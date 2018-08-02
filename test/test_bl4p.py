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
		def assertStatus(userID, paymentHash, expectedStatus):
			ret = self.client.getStatus(userid=userID, paymenthash=paymentHash)
			self.assertEqual(ret['result'], 'success')
			ret = ret['data']
			self.assertEqual(ret['status'], expectedStatus)

		#Receiver:
		ret = self.client.start(userid=self.receiverID, amount=100, timedelta=5, receiverpaysfee=True)
		self.assertEqual(ret['result'], 'success')
		ret = ret['data']
		paymentHash = ret['paymenthash']
		senderAmount = ret['senderamount']
		self.assertEqual(ret['senderamount'],  100) #not affected by fee
		self.assertEqual(ret['receiveramount'], 99) #fee subtracted
		assertStatus(self.receiverID, paymentHash, 'waiting_for_sender')

		#Sender:
		ret = self.client.send(userid=self.senderID, amount=senderAmount, paymenthash=paymentHash)
		self.assertEqual(ret['result'], 'success')
		ret = ret['data']
		paymentPreimage = ret['paymentpreimage']
		assertStatus(self.receiverID, paymentHash, 'waiting_for_receiver')
		assertStatus(self.senderID, paymentHash, 'waiting_for_receiver')

		#Receiver:
		ret = self.client.receive(paymentpreimage=paymentPreimage)
		self.assertEqual(ret['result'], 'success')
		assertStatus(self.receiverID, paymentHash, 'completed')
		assertStatus(self.senderID, paymentHash, 'completed')



if __name__ == '__main__':
	unittest.main(verbosity=2)

