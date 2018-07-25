FROM python:3.6-alpine

RUN mkdir -p /output
VOLUME /output

RUN mkdir -p /jenkins_node_scanner
WORKDIR /jenkins_node_scanner

COPY requirements.txt /jenkins_node_scanner
RUN pip install --no-cache-dir -r requirements.txt

COPY jenkins_node_scanner.py /jenkins_node_scanner

EXPOSE 8000
ENTRYPOINT ["./jenkins_node_scanner.py"]
CMD ["--help"]
