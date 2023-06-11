# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mafia.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bmafia.proto\"\x1e\n\x0e\x43onnectRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\" \n\rConnectResult\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\"2\n\x11\x44isconnectRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\")\n\x06Status\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07players\x18\x02 \x03(\t\".\n\rStatusRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\",\n\x0bRoleRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\"\x14\n\x04Role\x12\x0c\n\x04role\x18\x01 \x01(\t\",\n\x0bTimeRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\"\x14\n\x04Time\x12\x0c\n\x04time\x18\x01 \x01(\t\"0\n\x0fGameInfoRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\"<\n\x08GameInfo\x12\x12\n\ngame_is_on\x18\x01 \x01(\x08\x12\x0e\n\x06status\x18\x02 \x01(\x05\x12\x0c\n\x04time\x18\x03 \x01(\t\"T\n\rActionRequest\x12\x11\n\tfrom_name\x18\x01 \x01(\t\x12\x0e\n\x06\x61\x63tion\x18\x02 \x01(\t\x12\x0f\n\x07to_name\x18\x03 \x01(\t\x12\x0f\n\x07game_id\x18\x04 \x01(\x05\"0\n\x0c\x41\x63tionResult\x12\x10\n\x08is_legal\x18\x01 \x01(\x08\x12\x0e\n\x06result\x18\x02 \x01(\t\"/\n\x0eHistoryRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07game_id\x18\x02 \x01(\x05\"\x18\n\x07History\x12\r\n\x05moves\x18\x01 \x03(\t2\xe3\x02\n\x05Mafia\x12,\n\x07\x43onnect\x12\x0f.ConnectRequest\x1a\x0e.ConnectResult\"\x00\x12\x36\n\nDisconnect\x12\x12.DisconnectRequest\x1a\x12.DisconnectRequest\"\x00\x12&\n\tGetStatus\x12\x0e.StatusRequest\x1a\x07.Status\"\x00\x12 \n\x07GetRole\x12\x0c.RoleRequest\x1a\x05.Role\"\x00\x12 \n\x07GetTime\x12\x0c.TimeRequest\x1a\x05.Time\"\x00\x12,\n\x0bGetGameInfo\x12\x10.GameInfoRequest\x1a\t.GameInfo\"\x00\x12/\n\x0c\x43reateAction\x12\x0e.ActionRequest\x1a\r.ActionResult\"\x00\x12)\n\nGetHistory\x12\x0f.HistoryRequest\x1a\x08.History\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'mafia_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CONNECTREQUEST._serialized_start=15
  _CONNECTREQUEST._serialized_end=45
  _CONNECTRESULT._serialized_start=47
  _CONNECTRESULT._serialized_end=79
  _DISCONNECTREQUEST._serialized_start=81
  _DISCONNECTREQUEST._serialized_end=131
  _STATUS._serialized_start=133
  _STATUS._serialized_end=174
  _STATUSREQUEST._serialized_start=176
  _STATUSREQUEST._serialized_end=222
  _ROLEREQUEST._serialized_start=224
  _ROLEREQUEST._serialized_end=268
  _ROLE._serialized_start=270
  _ROLE._serialized_end=290
  _TIMEREQUEST._serialized_start=292
  _TIMEREQUEST._serialized_end=336
  _TIME._serialized_start=338
  _TIME._serialized_end=358
  _GAMEINFOREQUEST._serialized_start=360
  _GAMEINFOREQUEST._serialized_end=408
  _GAMEINFO._serialized_start=410
  _GAMEINFO._serialized_end=470
  _ACTIONREQUEST._serialized_start=472
  _ACTIONREQUEST._serialized_end=556
  _ACTIONRESULT._serialized_start=558
  _ACTIONRESULT._serialized_end=606
  _HISTORYREQUEST._serialized_start=608
  _HISTORYREQUEST._serialized_end=655
  _HISTORY._serialized_start=657
  _HISTORY._serialized_end=681
  _MAFIA._serialized_start=684
  _MAFIA._serialized_end=1039
# @@protoc_insertion_point(module_scope)
