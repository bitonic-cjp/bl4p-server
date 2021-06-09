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



server = rpcserver.RPCServer()

bl4p = bl4p_backend.BL4P()

#Some dummy users:
key3 = secp256k1.PrivateKey(privkey=sha256(b'3'))
key6 = secp256k1.PrivateKey(privkey=sha256(b'6'))
bl4p.users[3] = bl4p_backend.User(id=3, balance=2000000000, pubKey=key3.pubkey) #20 000 eur
bl4p.users[6] = bl4p_backend.User(id=6, balance=5000000000, pubKey=key6.pubkey) #50 000 eur

offerBook = offerbook_backend.OfferBook()

bl4p_rpc.registerRPC(server, bl4p)
offerbook_rpc.registerRPC(server, offerBook)



def main():
	server.run()



if __name__ == '__main__':
	main() # pragma no cover

