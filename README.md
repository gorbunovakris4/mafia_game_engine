# mafia_game_engine

## Description

Server and bot-client for mafia based on grpc.

## Usage

### 0. Run from different terminals

```bash
pip install -r /server/requirements.txt
pip install grpcio
pip install grpcio-tools
pip install googleapis-common-protos
pip install grpcio-status
```
```bash
python3 server/server.py
```
And at least 4 times: 

```bash
python3 client/client.py
```

When there are 4 client, game will start. Moves are made automatically

### 1. CLient name and host

You can choose your name and host by running:
```bash
python3 client/client.py {host:port} {name}
```

Example:

```bash
 python3 client/client.py localhost:50051 Serge
```

### 2. Run server using docker

```bash
docker build -t mafia_server:1.0 ./server

docker compose up -d
```
