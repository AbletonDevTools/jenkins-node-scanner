FROM python:3.6-slim

RUN mkdir -p /output
VOLUME /output

RUN mkdir -p /jenkins_node_scanner
WORKDIR /jenkins_node_scanner

RUN apt-get update \
    && apt-get install -y wget=1.20.1-1.1 --no-install-recommends \
    && wget -q -O - https://github.com/papertrail/remote_syslog2/releases/download/v0.17/remote_syslog_linux_amd64.tar.gz \
       | tar -zxf -

COPY Pipfile /jenkins_node_scanner
COPY Pipfile.lock /jenkins_node_scanner
RUN pip install --no-cache-dir pipenv==2018.11.26
RUN pipenv install --system --ignore-pipfile

# Copy the supervisor config file
COPY supervisord.conf /etc/supervisord.conf

COPY jenkins_node_scanner.py /jenkins_node_scanner

EXPOSE 8000
ENTRYPOINT ["./jenkins_node_scanner.py"]
#CMD ["--help"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
