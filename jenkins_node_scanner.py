#!/usr/bin/env python3

"""Continually scan a Jenkins master and write the nodes to a file."""

from contextlib import contextmanager
from xml.etree import ElementTree
import argparse
import json
import logging
import os
import re
import shutil
import socket
import sys
import tempfile
import time

import jenkins
from prometheus_client import start_http_server, Counter, Gauge, Histogram


JENKINS_API_LATENCY = Histogram(
    'jenkins_api_latency_seconds',
    'Response latency of Jenkins API (seconds)',
    ['api_method'],
)

JENKINS_API_EXCEPTIONS = Counter(
    'jenkins_api_exceptions',
    'Exceptions encountered accessing the Jenkins API.',
    ['api_method'],
)

GLOBAL_EXCEPTIONS = Counter(
    'node_scanner_exceptions',
    'Unhandled top-level exceptions.',
    [],
)

NODES_FOUND = Gauge(
    'nodes_found',
    'Nodes found in a scan.',
    ['jenkins_master'],
)

UNPARSEABLE_NODES_FOUND = Gauge(
    'unparseable_nodes_found',
    'Nodes found in a scan whose IP addresses could not be parsed.',
    ['jenkins_master'],
)


@contextmanager
def ignore_exceptions_except_exit():
    """Ignores all exceptions except KeyboardInterrupt and SystemExit."""
    try:
        yield
    except (KeyboardInterrupt, SystemExit):  # noqa pylint: disable=try-except-raise
        raise
    except:  # noqa pylint: disable=bare-except
        logging.exception('Unexpected error, continuing anyway.')


def get_args():
    """Configure arguments and parse them."""
    parser = argparse.ArgumentParser(
        description='Write Jenkins nodes to a file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'url',
        help='Full URL to the Jenkins master, such as http://jenkins:80.',
    )
    parser.add_argument(
        'output_file',
        help='Filename to write the node list.',
    )

    parser.add_argument(
        '--exclude-regex',
        default='^master$',
        help='Exclude any nodes matching this regex.',
    )
    parser.add_argument(
        '--password',
        help='Jenkins password.',
    )
    parser.add_argument(
        '--period',
        default=60,
        type=int,
        help='How many seconds to wait between scans. If 0, then the script will exit '
             'after performing a single scan.',
    )
    parser.add_argument(
        '--prometheus-port',
        default=8000,
        type=int,
        help='Port on which to expose Prometheus metrics.',
    )
    parser.add_argument(
        '--target-port',
        action='append',
        default=[],
        dest='target_ports',
        required=True,
        type=int,
        help='Target port to be scraped (e.g. 9100 for node_exporter). May be given '
             'multiple times for multiple ports.',
    )
    parser.add_argument(
        '--timeout',
        default=60,
        type=int,
        help='Timeout in seconds for the Jenkins call.',
    )
    parser.add_argument(
        '--username',
        help='Jenkins username.',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable more detailed logging.',
    )

    return parser.parse_args()


def get_node_ip(master, node):
    """Return the IP address of a node.

    Returns None if the node's IP address can not be determined.
    """
    # pylint: disable=no-member
    try:
        with JENKINS_API_EXCEPTIONS.labels('get_node_config').count_exceptions():
            # pylint: disable=no-member
            with JENKINS_API_LATENCY.labels('get_node_config').time():
                node_config = master.get_node_config(node['name'])
    except jenkins.NotFoundException:
        # If we hit a 404 for some reason, we still want to process other nodes so we
        # capture and log the exception here instead of letting it rise to the top-level
        # loop. It will still be counted by the count_exceptions() context manager
        # and reported to Prometheus, so capturing it here won't hide it from monitoring.
        logging.exception('404 when contacting %s', node)
        return None

    if 'hudson.plugins.swarm.SwarmSlave' not in node_config:
        logging.warning('Unrecognized node type: %s', node['name'])
        return None

    tree = ElementTree.fromstring(node_config)
    description = tree.find('description').text
    # Parses "Swarm slave from 10.1.1.1 : null" (after : can be arbitrary text)
    return description.split('from ')[1].split(' :')[0]


def get_nodes(master):
    """Get a list of nodes from a Jenkins master."""
    logging.debug('Connecting to master')
    try:
        # pylint: disable=no-member
        with JENKINS_API_EXCEPTIONS.labels('get_nodes').count_exceptions():
            # pylint: disable=no-member
            with JENKINS_API_LATENCY.labels('get_nodes').time():
                return master.get_nodes()
    except jenkins.JenkinsException as error:
        logging.warning('Could not connect to master: %s', error)
        return []


def is_port_open(ip_addr, port):
    """Return whether a TCP port is open on the given IP address."""
    try:
        logging.debug('Testing port %d on %s', port, ip_addr)
        sock = socket.create_connection((ip_addr, int(port)), timeout=1)
        sock.shutdown(socket.SHUT_RDWR)
        return True
    except (ConnectionRefusedError, socket.timeout):
        return False


def write_output(output_file, node_info):
    """Attempt to atomically write data as json to the output file.

    This is done by writing to a tempfile and moving it over the output file. This is an
    attempt to prevent race conditions between Prometheus and jenkins_node_scanner, but
    Prometheus still shows "unexpected end of JSON input" occasionally.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, output_file)
        with open(tmpfile, 'w') as filehandle:
            json.dump(node_info, filehandle, sort_keys=True, indent=2)
            filehandle.flush()
            os.fsync(filehandle.fileno())
        # Overwrite output by renaming the tempfile to the output file.
        shutil.move(tmpfile, output_file)


def main():
    """Run the main scanning loop."""
    args = get_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    start_http_server(args.prometheus_port)
    logging.info('Serving metrics on port %d', args.prometheus_port)

    exclude_regex = re.compile(args.exclude_regex)

    while True:
        with ignore_exceptions_except_exit():
            with GLOBAL_EXCEPTIONS.count_exceptions():
                logging.debug('Connecting to Jenkins master at %s', args.url)
                master = jenkins.Jenkins(
                    args.url,
                    username=args.username,
                    password=args.password,
                    timeout=args.timeout,
                )

                logging.debug('Fetching node list')
                nodes = [x for x in get_nodes(master)
                         if not exclude_regex.match(x['name'])]
                logging.debug('Found %d nodes', len(nodes))

                raw_node_ips = [(node, get_node_ip(master, node)) for node in nodes]
                node_ips = [(node, ip) for node, ip in raw_node_ips if ip is not None]

                # pylint: disable=no-member
                NODES_FOUND.labels(args.url).set(len(node_ips))
                # pylint: disable=no-member
                UNPARSEABLE_NODES_FOUND.labels(args.url).set(
                    len(raw_node_ips) - len(node_ips))

                node_info = [{
                    'labels': {
                        'jenkins_master': args.url,
                        'node': node['name'],
                    },
                    'targets': ['%s:%d' % (ip_addr, port) for port in args.target_ports
                                if is_port_open(ip_addr, port)],
                } for node, ip_addr in node_ips]

                write_output(args.output_file, node_info)

        if args.period == 0:
            break

        logging.debug('Waiting %d seconds', args.period)
        time.sleep(args.period)


if __name__ == '__main__':
    sys.exit(main())
