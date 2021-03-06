#    Copyright (C) 2018-2021 by Bitonic B.V.
#
#    This file is part of the BL4P Server.
#
#    The BL4P Server is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The BL4P Server is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with the BL4P Server. If not, see <http://www.gnu.org/licenses/>.

import argparse
import hashlib
import logging

import secp256k1

from . import bl4p_backend
from . import bl4p_rpc
from . import offerbook_backend
from . import offerbook_rpc
from . import rpcserver

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

sha256 = lambda preimage: hashlib.sha256(preimage).digest()



def parseArgs():
	parser = argparse.ArgumentParser()
	parser.add_argument('--host', default='0.0.0.0', type=str,
		help='Address to bind service to')
	parser.add_argument('--port', default=8000, type=int,
		help='Port to bind service to')

	return parser.parse_args()


server = None #Make it a global variable


def stopServer():
	'This is only used in the unit test code'
	server.close()


def main(timeoutFunctions=[]):
	'''
	:param timeoutFunctions: list of functions that will be registered as
	                  timeout functions in the RPC server (default: empty list).
	                  This is only used in the unit test code.
	'''
	global server

	print('Starting BL4P server')
	args = parseArgs()

	server = rpcserver.RPCServer(args.host, args.port)
	for f in timeoutFunctions:
		server.registerTimeoutFunction(f)

	bl4p = bl4p_backend.BL4P()

	#Some dummy users:
	key3 = secp256k1.PrivateKey(privkey=sha256(b'3'))
	key6 = secp256k1.PrivateKey(privkey=sha256(b'6'))
	bl4p.users[3] = bl4p_backend.User(id=3, balance=2000000000, pubKey=key3.pubkey) #20 000 eur
	bl4p.users[6] = bl4p_backend.User(id=6, balance=5000000000, pubKey=key6.pubkey) #50 000 eur

	offerBook = offerbook_backend.OfferBook()

	bl4p_rpc.registerRPC(server, bl4p)
	offerbook_rpc.registerRPC(server, offerBook)

	server.run()



if __name__ == '__main__':
	main() # pragma no cover

