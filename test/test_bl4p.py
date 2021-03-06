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

import hashlib
import sys
import threading
import time
import unittest
import urllib.request

import secp256k1

sys.path.append('..')

testHost = '127.0.0.1'
testPort = 8000
testURL = 'ws://%s:%d/' % (testHost, testPort)

from bl4p_server import rpcserver

from bl4p_server.api.client import Bl4pApi
from bl4p_server.api.offer import Asset, Offer
from bl4p_server.api import selfreport
import bl4p_server.__main__ as bl4p



sha256 = lambda preimage: hashlib.sha256(preimage).digest()



class ServerThread(threading.Thread):
	def start(self):
		self.stopRequested = False
		threading.Thread.start(self)


	def stop(self):
		self.stopRequested = True
		self.join()


	def run(self):

		def stopThread():
			if self.stopRequested:
				bl4p.stopServer()

			return 0.1

		bl4p.main(timeoutFunctions=[stopThread])



class TestBL4P(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.serverThread = ServerThread()
		cls.serverThread.start()
		time.sleep(0.5)


	@classmethod
	def tearDownClass(cls):
		cls.serverThread.stop()


	def setUp(self):
		self.sender = Bl4pApi(testURL, '3', '3')
		self.receiver = Bl4pApi(testURL, '6', '6')
		self.senderKey = secp256k1.PrivateKey(privkey=sha256(b'3'))
		self.receiverKey = secp256k1.PrivateKey(privkey=sha256(b'6'))


	def tearDown(self):
		self.sender.close()
		self.receiver.close()


	def assertStatus(self, interface, paymentHash, expectedStatus):
		status = interface.getStatus(payment_hash=paymentHash)
		self.assertEqual(status, expectedStatus)


	def test_goodFlow_receiverPaysFee(self):
		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.receiver.start(amount=100, sender_timeout_delta_ms=5000, locked_timeout_delta_s=5000, receiver_pays_fee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertStatus(self.receiver, paymentHash, 'waiting_for_selfreport')

		report = selfreport.serialize(
			{
			'paymentHash': paymentHash.hex(),
			'offerID': '6',
			'receiverCryptoAmount': '42',
			'cryptoCurrency': 'btc',
			})
		sigObject = self.receiverKey.ecdsa_sign(report)
		serializedSig = self.receiverKey.ecdsa_serialize(sigObject)
		self.receiver.selfReport(report=report, signature=serializedSig)
		self.assertStatus(self.receiver, paymentHash, 'waiting_for_sender')

		#Sender:
		sigObject = self.senderKey.ecdsa_sign(report)
		serializedSig = self.senderKey.ecdsa_serialize(sigObject)
		paymentPreimage = self.sender.send(sender_amount=senderAmount, payment_hash=paymentHash, max_locked_timeout_delta_s=5000, report=report, signature=serializedSig)
		self.assertStatus(self.receiver, paymentHash, 'waiting_for_receiver')
		self.assertStatus(self.sender, paymentHash, 'waiting_for_receiver')

		#Receiver:
		self.receiver.receive(payment_preimage=paymentPreimage)
		self.assertStatus(self.receiver, paymentHash, 'completed')
		self.assertStatus(self.sender, paymentHash, 'completed')


	def test_canceled(self):
		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.receiver.start(amount=100, sender_timeout_delta_ms=5000, locked_timeout_delta_s=5000, receiver_pays_fee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertStatus(self.receiver, paymentHash, 'waiting_for_selfreport')

		report = selfreport.serialize(
			{
			'paymentHash': paymentHash.hex(),
			'offerID': '6',
			'receiverCryptoAmount': '42',
			'cryptoCurrency': 'btc',
			})
		sigObject = self.receiverKey.ecdsa_sign(report)
		serializedSig = self.receiverKey.ecdsa_serialize(sigObject)
		self.receiver.selfReport(report=report, signature=serializedSig)
		self.assertStatus(self.receiver, paymentHash, 'waiting_for_sender')

		self.receiver.cancelStart(paymentHash)
		self.assertStatus(self.receiver, paymentHash, 'canceled')


	def test_offerbook_API(self):
		div_mBTC = 1000
		div_EUR  = 1
		addedOffer = Offer(
			bid = Asset(1, div_mBTC, 'btc', 'ln'),
			ask = Asset(5, div_EUR , 'eur', 'bl3p.eu'),
			address = 'foo',
			ID = 42,
			cltv_expiry_delta = (3, 4),
			)

		queryOffer = Offer(
			bid = Asset(5, div_EUR , 'eur', 'bl3p.eu'),
			ask = Asset(1, div_mBTC, 'btc', 'ln'),
			address = 'bar',
			ID = 41,
			locked_timeout = (5, 6),
			)

		addedOfferID = self.sender.addOffer(addedOffer)

		listedOffers = self.sender.listOffers()
		self.assertEqual(listedOffers, {addedOfferID: addedOffer})

		foundOffers = self.receiver.findOffers(queryOffer)
		self.assertEqual(foundOffers, [addedOffer])

		self.sender.removeOffer(addedOfferID)

		listedOffers = self.sender.listOffers()
		self.assertEqual(listedOffers, {})

		foundOffers = self.receiver.findOffers(queryOffer)
		self.assertEqual(foundOffers, [])



if __name__ == '__main__':
	unittest.main(verbosity=2)

