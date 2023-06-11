from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from typing import List, Tuple, Dict
import threading
import random
import concurrent.futures
import datetime
import logging
import threading
import time
import grpc

from google.protobuf import any_pb2
from google.rpc import code_pb2
from google.rpc import error_details_pb2
from google.rpc import status_pb2
from grpc_status import rpc_status

import mafia_pb2
import mafia_pb2_grpc

_ONE_DAY = datetime.timedelta(days=1)

_REACTION_TIME = datetime.timedelta(milliseconds=200)


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

    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.alive = True
        self.ended_day = False

    def __str__(self):
        return f"name: {self.name}, role: {self.role}"


class Game:
    def __init__(self, _id, players: Dict[str, Player]):
        self._id = _id
        self.players: Dict[str, Player] = players
        self.day_num = 1
        self.time = "day"
        self.status = "created"

    def kill(self, name) -> Tuple[bool, str]:
        if name not in self.players:
            return False, "invalid name"
        if not self.players[name].alive:
            return False, "player is already dead"
        self.players[name].alive = False
        return True, ""

    def check(self, name) -> Tuple[bool, str]:
        if name not in self.players:
            return False, "invalid name"
        if self.players[name].role == "mafia":
            Player.roles_actions["detective"]["day"].insert(0, "public")
            return True, name
        return False, name

    def check_status(self) -> int:
        mafia_alive = sum(1 for player in self.players.values() if player.role == "mafia" and player.alive is True)
        citizen_alive = sum(1 for player in self.players.values() if player.role != "mafia" and player.alive is True)
        if mafia_alive == 0:
            return 1
        if mafia_alive >= citizen_alive:
            return -1
        return 0


class Voting:
    def __init__(self, players):
        self.players_alive = sum(1 for player in players.values() if player.alive is True)
        self.votes = dict(
            zip([player.name for player in players.values() if player.alive is True], [0] * self.players_alive))
        self.sum = 0

    def vote(self, name) -> Tuple[bool, str]:
        if name not in self.votes:
            return False, "Player does not exist or is dead"
        self.votes[name] += 1
        return True, ""

    def check(self) -> Tuple[bool, str]:
        max_vote = -1
        cnt = 1
        loser = ""
        for name, votes in self.votes.items():
            if votes > max_vote:
                max_vote = votes
                cnt = 1
                loser = name
            elif votes == max_vote:
                cnt += 1
        if cnt == 1:
            return True, loser
        return False, ""


class GameEngine:
    def __init__(self, min_player_cnt=4):
        self.players: Dict[str, Player] = {}
        self.free_roles = ["mafia", "detective", "citizen", "citizen"]
        self.min_player_cnt = min_player_cnt
        self.Game = None
        self.voting = None
        self.history = []
        self.notified = {}
        self.wait_players = True

    def add_player(self, name):
        lock = threading.Lock()
        with lock:
            self.players[name] = Player(name, "")

    def remove_player(self, name):
        lock = threading.Lock()
        with lock:
            del self.players[name]

    def assign_roles(self):
        self.wait_players = False
        random.shuffle(self.free_roles)
        lock = threading.Lock()
        with lock:
            for i, name in enumerate(self.players):
                self.players[name].role = self.free_roles[i]
        return self.players

    def start_game(self):
        lock = threading.Lock()
        with lock:
            self.Game = Game(1, self.players)
            self.Game.status = "started"
            self.notified = {player: 0 for player in self.players.keys()}

    def restart(self, outer_player):
        lock = threading.Lock()
        with lock:
            del self.players[outer_player]
            self.Game = None
            self.voting = None
            self.history = []
            self.notified = {}

    def new_day(self):
        lock = threading.Lock()
        with lock:
            self.Game.time = "day"
            self.Game.day_num += 1
            self.voting = Voting(self.Game.players)
            for player in self.Game.players:
                self.players[player].ended_day = False

    def end_day(self):
        lock = threading.Lock()
        with lock:
            self.Game.time = "night"

    def players_ended_day(self) -> int:
        lock = threading.Lock()
        with lock:
            return sum(1 for player in self.Game.players.values() if player.ended_day) - \
                sum(1 for player in self.Game.players.values() if player.alive)

    def refresh_time(self) -> str:
        lock = threading.Lock()
        with lock:
            if self.Game.time == "day":
                if self.players_ended_day() == 0:
                    if self.Game.day_num > 1:
                        is_killed, loser = self.voting.check()
                        if is_killed:
                            self.Game.kill(loser)
                            self.history.append(f"voting {loser} is killed")
                    self.end_day()
                    return "night"
                else:
                    return "day"
            else:
                mafia_move = False
                commissar_move = False
                if self.history[-1].split()[0] == "mafia":
                    mafia_move = True
                if self.history[-1].split()[0] == "detective":
                    commissar_move = True
                if self.history[-2].split()[0] == "mafia":
                    mafia_move = True
                if self.history[-2].split()[0] == "detective":
                    commissar_move = True
                if sum(1 for player in self.Game.players.values() if
                       player.alive is True and player.role == "detective") == 0:
                    commissar_move = True
                if sum(1 for player in self.Game.players.values() if
                       player.alive is True and player.role == "mafia") == 0:
                    mafia_move = True
                if mafia_move and commissar_move:
                    self.new_day()
                    return "day"
                return "night"

    def make_action(self, from_player, to_player, action) -> Tuple[bool, str]:
        if not self.Game.players[from_player].alive:
            return False, "player is dead"
        from_player_role = self.Game.players[from_player].role
        if action == "vote":
            if self.Game.time == "day":
                lock = threading.Lock()
                with lock:
                    self.voting.vote(to_player)
                    self.history.append(f"{from_player} vote for {to_player}")
                return True, f"{from_player} vote for {to_player}"
            else:
                return False, f"cannot vote at night"
        elif action == "end":
            if self.Game.time == "day":
                lock = threading.Lock()
                with lock:
                    self.Game.players[from_player].ended_day = True
                    self.history.append(f"{from_player} end this day")
                return True, f"{from_player} end this day"
            else:
                return False, f"it is night"
        elif action == "publish":
            if self.Game.time == "day":
                lock = threading.Lock()
                with lock:
                    self.history.append(f"detective found mafia. It is {to_player}")
                return True, f"detective found mafia. It is {to_player}"
            else:
                return False, "it is night"
        elif action == "kill":
            if self.Game.time == "night" and from_player_role == "mafia":
                lock = threading.Lock()
                with lock:
                    self.Game.kill(to_player)
                    self.history.append(f"mafia kill {to_player} this night")
                return True, f"mafia kill {to_player} this night"
            elif from_player_role != "mafia":
                return False, "you cannot kill"
            else:
                return False, "it is day"
        elif action == "check":
            if self.Game.time == "night" and from_player_role == "detective":
                lock = threading.Lock()
                with lock:
                    is_mafia, name = self.Game.check(to_player)
                    if is_mafia:
                        self.history.append(f"detective found mafia this night")
                        return True, f"detective found mafia this night"
                    else:
                        self.history.append(f"detective missed this night")
                        return False, f"detective missed this night"
            elif from_player_role != "detective":
                return False, "you cannot check"
            else:
                return False, "it is day"

        return False, "unknown action"


def create_duplicate_name_error_status(name):
    detail = any_pb2.Any()
    detail.Pack(
        error_details_pb2.QuotaFailure(violations=[
            error_details_pb2.QuotaFailure.Violation(
                subject="name: %s" % name,
                description="Duplicate name",
            )
        ], ))
    return status_pb2.Status(
        code=code_pb2.ALREADY_EXISTS,
        message='Name already exists.',
        details=[detail],
    )


def create_unknown_name_error_status(name):
    detail = any_pb2.Any()
    detail.Pack(
        error_details_pb2.QuotaFailure(violations=[
            error_details_pb2.QuotaFailure.Violation(
                subject="name: %s" % name,
                description="Unknown name",
            )
        ], ))
    return status_pb2.Status(
        code=code_pb2.ALREADY_EXISTS,
        message='There is no player with that name in the game.',
        details=[detail],
    )


def create_wrong_action_condition_status(reason, action):
    detail = any_pb2.Any()
    detail.Pack(
        error_details_pb2.QuotaFailure(violations=[
            error_details_pb2.QuotaFailure.Violation(
                subject="action: %s" % action,
                description=f"Action cannot be done due to {reason}",
            )
        ], ))
    return status_pb2.Status(
        code=code_pb2.PERMISSION_DENIED,
        message=reason,
        details=[detail],
    )


def create_game_ended_status(status):
    detail = any_pb2.Any()
    detail.Pack(
        error_details_pb2.QuotaFailure(violations=[
            error_details_pb2.QuotaFailure.Violation(
                subject="status: %s" % status,
                description=f"Game is ended",
            )
        ], ))
    return status_pb2.Status(
        code=code_pb2.PERMISSION_DENIED,
        message=status,
        details=[detail],
    )


class MafiaServer(mafia_pb2_grpc.MafiaServicer):
    def __init__(self):
        self._game_engines = [GameEngine()]

    def Connect(self, request, context):
        logging.info("Received Connection from {}".format(context.peer()))
        lock = threading.Lock()
        with lock:
            if not self._game_engines[-1].wait_players or len(self._game_engines[-1].players.keys()) >= \
                    self._game_engines[-1].min_player_cnt:
                self._game_engines.append(GameEngine())
            if request.name in self._game_engines[-1].players:
                rich_status = create_duplicate_name_error_status(request.name)
                context.abort_with_status(rpc_status.to_status(rich_status))
            self._game_engines[-1].add_player(request.name)
            return mafia_pb2.ConnectResult(game_id=len(self._game_engines) - 1)

    def GetStatus(self, request, context):
        logging.info("Received Connection from {}".format(context.peer()))
        game_id = request.game_id
        if len(self._game_engines[game_id].players.keys()) < 4:
            status = "waiting for players"
        else:
            status = "game can be started!"
            if self._game_engines[game_id].Game is None:
                self._game_engines[game_id].assign_roles()
                self._game_engines[game_id].start_game()
        return mafia_pb2.Status(status=status, players=self._game_engines[game_id].players.keys())

    def Disconnect(self, request, context):
        logging.info("Received Disconnection from {}".format(context.peer()))
        game_id = request.game_id
        if request.name not in self._game_engines[game_id].players:
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS,
                "Name '{}' does not exist.".format(
                    request.name))
        lock = threading.Lock()
        with lock:
            if self._game_engines[game_id].Game is not None:
                self._game_engines[game_id].restart(request.name)
            else:
                self._game_engines[game_id].remove_player(request.name)
        return mafia_pb2.DisconnectRequest(name=request.name, game_id=game_id)

    def GetRole(self, request, context):
        logging.info("Received Disconnection from {}".format(context.peer()))
        game_id = request.game_id
        if request.name not in self._game_engines[game_id].players:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                "Name '{}' does not exist.".format(
                    request.name))
        role = self._game_engines[game_id].players[request.name].role
        return mafia_pb2.Role(role=role)

    def GetTime(self, request, context):
        logging.info("Received Disconnection from {}".format(context.peer()))
        game_id = request.game_id
        if request.name not in self._game_engines[game_id].players:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                "Name '{}' does not exist.".format(
                    request.name))
        lock = threading.Lock()
        with lock:
            time = self._game_engines[game_id].refresh_time()
            return mafia_pb2.Time(time=time)

    def GetGameInfo(self, request, context):
        game_id = request.game_id
        lock = threading.Lock()
        with lock:
            game_is_on = self._game_engines[game_id].Game is not None
            if game_is_on:
                status = self._game_engines[game_id].Game.check_status()
                time = self._game_engines[game_id].refresh_time()
            else:
                status = 0
                time = "day"
            return mafia_pb2.GameInfo(game_is_on=game_is_on, status=status, time=time)

    def CreateAction(self, request, context):
        logging.info("Received Disconnection from {}".format(context.peer()))
        game_id = request.game_id
        if request.from_name not in self._game_engines[game_id].players:
            rich_status = create_unknown_name_error_status(request.name)
            context.abort_with_status(rpc_status.to_status(rich_status))
        lock = threading.Lock()
        with lock:
            is_ok, res = self._game_engines[game_id].make_action(request.from_name, request.to_name, request.action)
            if not is_ok:
                rich_status = create_wrong_action_condition_status(res, request.action)
                context.abort_with_status(rpc_status.to_status(rich_status))
            return mafia_pb2.ActionResult(is_legal=is_ok, result=res)

    def GetHistory(self, request, context):
        logging.info("Received Disconnection from {}".format(context.peer()))
        game_id = request.game_id
        if request.name not in self._game_engines[game_id].players:
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS,
                "Name '{}' does not exist.".format(
                    request.name))
        lock = threading.Lock()
        with lock:
            if self._game_engines[game_id].Game is None:
                context.abort(
                    grpc.StatusCode.CANCELLED,
                    "Game is interrupted.".format(
                        request.name))
            history = self._game_engines[game_id].history[self._game_engines[game_id].notified[request.name]:]
            self._game_engines[game_id].notified[request.name] += len(history)
            return mafia_pb2.History(moves=history)


def _await_termination(server):
    try:
        while True:
            time.sleep(_ONE_DAY.total_seconds())
    except KeyboardInterrupt:
        logging.info("Terminating server.")
        server.stop(0)


def _run_server_non_blocking(host, port):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor())
    mafia_pb2_grpc.add_MafiaServicer_to_server(MafiaServer(), server)
    actual_port = server.add_insecure_port('{}:{}'.format(host, port))
    logging.info("Server listening at {}:{}".format(host, actual_port))
    server.start()
    return server, actual_port


def run_server(host='localhost', port=50051):
    print(f"listening on {host}:{port}")
    server, _ = _run_server_non_blocking(host, port)
    _await_termination(server)


if __name__ == '__main__':
    logging.basicConfig()
    run_server()
