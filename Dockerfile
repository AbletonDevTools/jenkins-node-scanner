FROM python:3.6-alpine

RUN mkdir -p /output
VOLUME /output

RUN mkdir -p /jenkins_node_scanner
WORKDIR /jenkins_node_scanner

COPY Pipfile /jenkins_node_scanner
COPY Pipfile.lock /jenkins_node_scanner
RUN pip install --no-cache-dir pipenv
RUN pipenv install --system --ignore-pipfile

COPY jenkins_node_scanner.py /jenkins_node_scanner

EXPOSE 8000
ENTRYPOINT ["./jenkins_node_scanner.py"]
CMD ["--help"]
