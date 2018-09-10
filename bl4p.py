#!/usr/bin/env python3

import apiserver
import bl4p_rpc
import offerbook_rpc
import storage

server = apiserver.APIServer()



s = storage.Storage()
s.users[3] = storage.User(id=3, balance=2000)
s.users[6] = storage.User(id=6, balance=5000)

bl4p_rpc.registerRPC(server, s)
offerbook_rpc.registerRPC(server, None)



def main():
	server.run()



if __name__ == '__main__':
	main() # pragma no cover

