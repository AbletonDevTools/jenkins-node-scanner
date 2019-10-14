# jenkins-node-scanner

A service to list Jenkins nodes for further Prometheus scraping. The output is intended to
be read by Prometheus' `file_sd_config` section.

Basic usage:

1. `make sync`
1. `python jenkins_node_scanner.py http://jenkins:8080 output.json --period 5`
1. `cat output.json`

Note that the service exposes prometheus metrics about itself on port 8000 (by default).
