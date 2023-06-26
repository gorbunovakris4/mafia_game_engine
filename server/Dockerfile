FROM python:3.8

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install grpcio
RUN pip install grpcio-tools
RUN pip install googleapis-common-protos
RUN pip install grpcio-status
RUN unset http_proxy
RUN unset https_proxy


EXPOSE 50051
EXPOSE 50051/udp


ENTRYPOINT ["python3", "-u", "server.py"]
