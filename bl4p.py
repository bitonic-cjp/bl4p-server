#!/usr/bin/env python3

import logging

import bl4p_backend
import bl4p_rpc
import offerbook_backend
import offerbook_rpc
import rpcserver

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

server = rpcserver.RPCServer()



bl4p = bl4p_backend.BL4P()
bl4p.users[3] = bl4p_backend.User(id=3, balance=20000000)
bl4p.users[6] = bl4p_backend.User(id=6, balance=50000000)

offerBook = offerbook_backend.OfferBook()

bl4p_rpc.registerRPC(server, bl4p)
offerbook_rpc.registerRPC(server, offerBook)



def main():
	server.run()



if __name__ == '__main__':
	main() # pragma no cover

