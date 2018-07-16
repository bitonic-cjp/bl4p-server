import sys
import unittest

sys.path.append('..')

import storage



class TestStorage(unittest.TestCase):
	def setUp(self):
		self.receiverID = 3
		self.senderID = 6
		self.storage = storage.Storage()
		self.storage.users[self.senderID] = storage.User(id=self.senderID, balance=0)
		self.storage.users[self.receiverID] = storage.User(id=self.receiverID, balance=0)


	def setBalance(self, userID, balance):
		self.storage.users[userID].balance = balance

	def getBalance(self, userID):
		return self.storage.users[userID].balance


	def test_goodFlow(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)

		#Sender:
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)

		#Receiver:
		self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.senderID), 400)
		self.assertEqual(self.getBalance(self.receiverID), 300)



if __name__ == '__main__':
	unittest.main()

