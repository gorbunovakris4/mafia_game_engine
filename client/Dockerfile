FROM python:3.8

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 50051
EXPOSE 50051/udp


ENTRYPOINT ["python3", "-u", "client.py"]
