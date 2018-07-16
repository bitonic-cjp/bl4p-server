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


	def getTransactionStatus(self, paymentHash):
		return self.storage.transactions[paymentHash].status


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


	def test_startTransaction_invalidUser(self):
		with self.assertRaises(storage.Storage.UserNotFound):
			self.storage.startTransaction(1312, amount=100, timeDelta=5)


	def test_processTimeout_NOPs(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Test that it succeeds for non-existing transactions
		self.storage.processTimeout(b'x'*32)

		#Now test it in states where it should be a NOP too

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)

		statusBefore = self.getTransactionStatus(paymentHash)
		self.storage.processTimeout(paymentHash)
		statusAfter = self.getTransactionStatus(paymentHash)
		self.assertEqual(statusBefore, statusAfter)

		self.storage.processReceiverClaim(paymentPreimage)

		statusBefore = self.getTransactionStatus(paymentHash)
		self.storage.processTimeout(paymentHash)
		statusAfter = self.getTransactionStatus(paymentHash)
		self.assertEqual(statusBefore, statusAfter)


	def test_processSenderAck_invalidUser(self):
		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		with self.assertRaises(storage.Storage.UserNotFound):
			self.storage.processSenderAck(1312, amount=100, paymentHash=paymentHash)


	def test_processSenderAck_invalidPaymentHash(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=100, paymentHash=b'x'*32)

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		self.storage.processTimeout(paymentHash)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)
		self.storage.processReceiverClaim(paymentPreimage)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)


	def test_processReceiverClaim_invalidPaymentHash(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(b'x'*32)

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		paymentPreimage = self.storage.transactions[paymentHash].preimage
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		paymentPreimage = self.storage.transactions[paymentHash].preimage
		self.storage.processTimeout(paymentHash)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200)

		paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=100, paymentHash=paymentHash)
		self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 300)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 300)



if __name__ == '__main__':
	unittest.main()

