#!/usr/bin/env python3

import rpcserver
import bl4p_rpc
import storage

server = rpcserver.RPCServer()



s = storage.Storage()
s.users[3] = storage.User(id=3, balance=2000)
s.users[6] = storage.User(id=6, balance=5000)

bl4p_rpc.registerRPC(server, s)



server.serve_forever()

