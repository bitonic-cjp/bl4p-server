#!/usr/bin/env python3

import rpcserver
import storage

receiverID = 3
senderID = 6

s = storage.Storage()
s.users[receiverID] = storage.User(id=receiverID, balance=2000)
s.users[senderID] = storage.User(id=senderID, balance=5000)

rpc = rpcserver.RPCServer(s)
rpc.serve_forever()

