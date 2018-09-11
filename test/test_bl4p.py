import sys
import threading
import time
import unittest
import urllib.request

sys.path.append('..')

from api.client import Bl4pApi, Asset, Offer
import bl4p



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
				bl4p.server.close()

			return 0.1

		bl4p.server.registerTimeoutFunction(stopThread)
		bl4p.main()



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
		self.sender = Bl4pApi('ws://localhost:8000/', '3', '3')
		self.receiver = Bl4pApi('ws://localhost:8000/', '6', '6')


	def tearDown(self):
		self.sender.close()
		self.receiver.close()


	def test_goodFlow_receiverPaysFee(self):
		def assertStatus(interface, paymentHash, expectedStatus):
			status = interface.getStatus(payment_hash=paymentHash)
			self.assertEqual(status, expectedStatus)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.receiver.start(amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		assertStatus(self.receiver, paymentHash, 'waiting_for_sender')

		#Sender:
		paymentPreimage = self.sender.send(sender_amount=senderAmount, payment_hash=paymentHash)
		assertStatus(self.receiver, paymentHash, 'waiting_for_receiver')
		assertStatus(self.sender, paymentHash, 'waiting_for_receiver')

		#Receiver:
		self.receiver.receive(payment_preimage=paymentPreimage)
		assertStatus(self.receiver, paymentHash, 'completed')
		assertStatus(self.sender, paymentHash, 'completed')


	def test_offerbook_API(self):
		div_mBTC = 1000
		div_EUR  = 1
		addedOffer = Offer(
			bid = Asset(1, div_mBTC, 'btc', 'ln'),
			ask = Asset(5, div_EUR , 'eur', 'bl3p.eu'),
			address = 'foo',
			cltv_expiry_delta = (3, 4),
			)

		queryOffer = Offer(
			bid = Asset(5, div_EUR , 'eur', 'bl3p.eu'),
			ask = Asset(1, div_mBTC, 'btc', 'ln'),
			address = 'bar',
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

