from __future__ import print_function

import random
import threading
import mafia_pb2
import mafia_pb2_grpc
import time
import names
from typing import Tuple
import sys

import logging

from google.rpc import error_details_pb2
import grpc
from grpc_status import rpc_status

global name


class Player:
    roles_actions = {"detective": {
        "night": ["check"],
        "day": ["vote", "end"]
    },
        "citizen": {
            "night": [],
            "day": ["vote", "end"]
        },
        "mafia": {
            "night": ["kill"],
            "day": ["vote", "end"]
        }
    }

    def __init__(self, name, role, players):
        self.name = name
        self.role = role
        self.alive = True
        self.ended_day = False
        self.is_day = True
        self.day_num = 1
        self.voted = False
        self.published = False
        self.alive_players = players
        self.guessed_mafia = False
        self.guess = ""

    def make_action(self) -> Tuple[str, str, str]:
        if self.role == "mafia" and self.is_day is False:
            victim = self.alive_players[random.randint(0, len(self.alive_players) - 1)]
            return self.name, "kill", victim
        if self.role == "detective" and not self.guessed_mafia and not self.is_day:
            victim = self.alive_players[random.randint(0, len(self.alive_players) - 1)]
            return self.name, "check", victim
        if self.role == "detective" and self.guessed_mafia and self.is_day and not self.published:
            self.published = True
            return self.name, "publish", self.guess
        if self.is_day and not self.voted and self.day_num > 1:
            victim = self.alive_players[random.randint(0, len(self.alive_players) - 1)]
            self.voted = True
            return self.name, "vote", victim
        self.ended_day = True
        return self.name, "end", self.name

    def set_night(self):
        self.is_day = False
        self.voted = False

    def set_day(self):
        self.day_num += 1
        self.is_day = True
        self.voted = False
        self.ended_day = False

    def killed_player(self, name):
        self.alive_players.remove(name)


def start_game(players, game_id, connection_string):
    print("Entering session...")
    print("Connected players are:\n\t", "\n\t".join(players), sep="")
    connected = True
    with grpc.insecure_channel(connection_string) as channel:
        stub = mafia_pb2_grpc.MafiaStub(channel)
        response = stub.GetRole(mafia_pb2.RoleRequest(name=name, game_id=game_id))
    print(f"you are {response.role}")
    players.remove(name)
    player = Player(name, response.role, players)
    try:
        while True:
            print(f"day {player.day_num} starts")
            if player.alive:
                action = ""
                while action != "end" and player.alive:
                    from_player, action, to_player = player.make_action()
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.CreateAction(
                            mafia_pb2.ActionRequest(from_name=from_player, action=action, to_name=to_player,
                                                    game_id=game_id))
                    if response.is_legal:
                        print("YOUR MOVE:\t", response.result, sep="")
                    time.sleep(5)
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.GetHistory(mafia_pb2.HistoryRequest(name=name, game_id=game_id))
                    for move in response.moves:
                        initiator = move.split()[0]
                        if initiator == name:
                            continue
                        elif initiator == "mafia":
                            victim = move.split()[2]
                            if victim == name:
                                player.alive = False
                            else:
                                player.alive_players.remove(victim)
                        print(initiator.capitalize(), " MOVE:\t", move, sep="")
                    time.sleep(5)
            else:
                print("you are dead :( can only observe the game")
                time.sleep(5)
                with grpc.insecure_channel(connection_string) as channel:
                    stub = mafia_pb2_grpc.MafiaStub(channel)
                    response = stub.GetHistory(mafia_pb2.HistoryRequest(name=name, game_id=game_id))
                for move in response.moves:
                    initiator = move.split()[0]
                    if initiator == name:
                        continue
                    elif initiator == "mafia":
                        victim = move.split()[2]
                        if victim == name:
                            player.alive = False
                        else:
                            player.alive_players.remove(victim)
                    print(initiator.capitalize(), " MOVE:\t", move, sep="")
                time.sleep(5)

            day_time = "day"
            while day_time == "day":
                with grpc.insecure_channel(connection_string) as channel:
                    stub = mafia_pb2_grpc.MafiaStub(channel)
                    response = stub.GetGameInfo(mafia_pb2.GameInfoRequest(name=name, game_id=game_id))
                    day_time = response.time
                    game_is_on = response.game_is_on
                    status = response.status
                    if not game_is_on:
                        print("sorry, game is interrupted")
                        print("Reconnect...")
                        with grpc.insecure_channel(connection_string) as channel:
                            stub = mafia_pb2_grpc.MafiaStub(channel)
                            response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                        connected = False
                        time.sleep(10)
                        run(connection_string)
                    elif status == 1:
                        print("citizens won! mafia is killed by voting")
                        time.sleep(10)
                        print("you can continue playing")
                        with grpc.insecure_channel(connection_string) as channel:
                            stub = mafia_pb2_grpc.MafiaStub(channel)
                            response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                        connected = False
                        time.sleep(100)
                        run(connection_string)
                    elif status == -1:
                        print("mafia won! only 1 citizen is still alive")
                        time.sleep(10)
                        print("you can continue playing")
                        with grpc.insecure_channel(connection_string) as channel:
                            stub = mafia_pb2_grpc.MafiaStub(channel)
                            response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                        connected = False
                        time.sleep(100)
                        run(connection_string)
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.GetHistory(mafia_pb2.HistoryRequest(name=name, game_id=game_id))
            for move in response.moves:
                initiator = move.split()[0]
                if initiator == name:
                    continue
                elif initiator == "mafia":
                    victim = move.split()[2]
                    if victim == name:
                        player.alive = False
                    else:
                        player.alive_players.remove(victim)
                elif initiator == "voting":
                    victim = move.split()[1]
                    if victim == name:
                        player.alive = False
                print(initiator.capitalize(), " MOVE:\t", move, sep="")
            print(f"day {player.day_num} ends")
            time.sleep(8)
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.GetGameInfo(mafia_pb2.GameInfoRequest(name=name, game_id=game_id))
                day_time = response.time
                game_is_on = response.game_is_on
                status = response.status
                if not game_is_on:
                    print("sorry, game is interrupted")
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
                elif status == 1:
                    print("citizens won! mafia is killed by voting")
                    time.sleep(10)
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
                elif status == -1:
                    print("mafia won! only 1 citizen is still alive")
                    time.sleep(10)
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
            print("night has fallen")
            player.set_night()
            time.sleep(5)
            if player.role == "mafia" and player.alive:
                from_player, action, to_player = player.make_action()
                with grpc.insecure_channel(connection_string) as channel:
                    stub = mafia_pb2_grpc.MafiaStub(channel)
                    response = stub.CreateAction(
                        mafia_pb2.ActionRequest(from_name=from_player, action=action, to_name=to_player,
                                                game_id=game_id))
                if response.is_legal:
                    print("YOUR MOVE:\t", response.result, sep="")
                time.sleep(8)
            elif player.role == "detective" and player.alive and not player.guessed_mafia:
                from_player, action, to_player = player.make_action()
                with grpc.insecure_channel(connection_string) as channel:
                    stub = mafia_pb2_grpc.MafiaStub(channel)
                    try:
                        response = stub.CreateAction(
                            mafia_pb2.ActionRequest(from_name=from_player, action=action, to_name=to_player,
                                                    game_id=game_id))
                        print("YOUR MOVE:\t", response.result, sep="")
                        if response.result.split()[1] == "found":
                            print(f"It is {to_player}")
                            player.guessed_mafia = True
                            player.guess = to_player
                            time.sleep(8)
                        else:
                            print(f"{to_player} is not mafia")
                            time.sleep(8)
                    except grpc.RpcError as rpc_error:
                        status = rpc_status.from_call(rpc_error)
                        if status.message == "player is dead":
                            player.alive = False
                            print("you are dead :( Can only observe the game")
                            time.sleep(3)
            day_time = "night"
            while day_time == "night":
                with grpc.insecure_channel(connection_string) as channel:
                    stub = mafia_pb2_grpc.MafiaStub(channel)
                    response = stub.GetTime(mafia_pb2.TimeRequest(name=name, game_id=game_id))
                    day_time = response.time
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.GetHistory(mafia_pb2.HistoryRequest(name=name, game_id=game_id))
            for move in response.moves:
                initiator = move.split()[0]
                if initiator == name:
                    continue
                elif initiator == "mafia":
                    victim = move.split()[2]
                    if victim == name:
                        player.alive = False
                    else:
                        player.alive_players.remove(victim)
                elif initiator == "voting":
                    victim = move.split()[1]
                    if victim == name:
                        player.alive = False
                    else:
                        player.alive_players.remove(victim)
                print(initiator.capitalize(), " MOVE:\t", move, sep="")
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.GetGameInfo(mafia_pb2.GameInfoRequest(name=name, game_id=game_id))
                day_time = response.time
                game_is_on = response.game_is_on
                status = response.status
                if not game_is_on:
                    print("sorry, game is interrupted")
                    print("Reconnect...")
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
                elif status == 1:
                    print("citizens won! mafia is killed by voting")
                    time.sleep(10)
                    print("you can continue playing")
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
                elif status == -1:
                    print("mafia won! only 1 citizen is still alive")
                    time.sleep(10)
                    print("you can continue playing")
                    with grpc.insecure_channel(connection_string) as channel:
                        stub = mafia_pb2_grpc.MafiaStub(channel)
                        response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
                    connected = False
                    time.sleep(100)
                    run(connection_string)
            player.set_day()
            time.sleep(5)
    except KeyboardInterrupt:
        if connected:
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
        logging.info("Terminating client.")
        exit(0)


def run(connection_string):
    global name
    in_game = False
    game_id = None
    while not in_game:
        print("Connecting...")
        with grpc.insecure_channel(connection_string) as channel:
            stub = mafia_pb2_grpc.MafiaStub(channel)
            try:
                response = stub.Connect(mafia_pb2.ConnectRequest(name=name))
                in_game = True
                game_id = response.game_id
            except grpc.RpcError as rpc_error:
                status = rpc_status.from_call(rpc_error)
                print(status.message)
                name = names.get_first_name()
                print(f"Ok, then. I am {name}")
    try:
        while True:
            time.sleep(10)
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.GetStatus(mafia_pb2.StatusRequest(name=name, game_id=game_id))

            print(response.status)
            if response.status == "game can be started!":
                start_game(response.players, game_id, connection_string)
            else:
                print("Connected players are:\n\t", "\n\t".join(response.players), sep="")
    except KeyboardInterrupt:
        if in_game:
            with grpc.insecure_channel(connection_string) as channel:
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.Disconnect(mafia_pb2.DisconnectRequest(name=name, game_id=game_id))
        logging.info("Terminating client.")
        exit(0)


if __name__ == '__main__':
    logging.basicConfig()
    connection_string = "localhost:50051"
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    name = ""
    if len(sys.argv) > 2:
        name = sys.argv[2]
    else:
        print("Selecting name...")
        name = names.get_first_name()
    print(f"I am {name}")
    run(connection_string)
