FROM python:3.7.4-slim

RUN mkdir -p /output
VOLUME /output

RUN mkdir -p /jenkins_node_scanner
WORKDIR /jenkins_node_scanner

RUN apt-get update \
    && apt-get install -y supervisor=3.3.5-1 wget=1.20.1-1.1 --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN wget -q -O - https://github.com/papertrail/remote_syslog2/releases/download/v0.17/remote_syslog_linux_amd64.tar.gz \
    | tar -zxf -


COPY Pipfile /jenkins_node_scanner
COPY Pipfile.lock /jenkins_node_scanner
RUN pip install --no-cache-dir pipenv==2018.11.26
RUN pipenv install --system --ignore-pipfile

RUN mkdir /logs/ && touch /logs/server

COPY jenkins_node_scanner.py /jenkins_node_scanner
COPY supervisord.conf /etc/supervisord.conf
COPY papertrail_config.yml /etc/log_files.yml

EXPOSE 8000
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
