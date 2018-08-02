import sys
import threading
import time
import unittest
import urllib.request

sys.path.append('..')

from api.bl4p import Bl4pApi
import bl4p



class ServerThread(threading.Thread):
	class StopServerThread(Exception):
		pass


	def start(self):
		self.stopRequested = False
		threading.Thread.start(self)


	def stop(self):
		self.stopRequested = True
		self.join()


	def run(self):

		def stopThread():
			if self.stopRequested:
				raise ServerThread.StopServerThread()

			return 0.1

		bl4p.server.registerTimeoutFunction(stopThread)
		try:
			bl4p.main()
		except ServerThread.StopServerThread:
			bl4p.server.server_close()



class TestBL4P(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.serverThread = ServerThread()
		cls.serverThread.start()


	@classmethod
	def tearDownClass(cls):
		cls.serverThread.stop()


	def setUp(self):
		self.senderID = 3
		self.receiverID = 6
		self.client = Bl4pApi('http://localhost:8000/', '', '')


	def test_goodFlow_receiverPaysFee(self):
		#Receiver:
		ret = self.client.start(userid=self.receiverID, amount=100, timedelta=5, receiverpaysfee=True)
		self.assertEqual(ret['result'], 'success')
		ret = ret['data']
		self.assertEqual(ret['senderamount'],  100) #not affected by fee
		self.assertEqual(ret['receiveramount'], 99) #fee subtracted

		'''
		self.assertEqual(self.storage.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_sender')

		#Sender:
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.storage.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.storage.getTransactionStatus(self.senderID, paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.storage.processReceiverClaim(paymentPreimage)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)
		self.assertEqual(self.storage.getTransactionStatus(self.receiverID, paymentHash), 'completed')
		self.assertEqual(self.storage.getTransactionStatus(self.senderID, paymentHash), 'completed')
		'''



if __name__ == '__main__':
	unittest.main(verbosity=2)

