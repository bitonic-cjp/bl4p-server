import decimal
import sys
import unittest

sys.path.append('..')

import storage



class TestStorage(unittest.TestCase):
	def setUp(self):
		self.receiverID = 3
		self.senderID = 6
		self.storage = storage.Storage()
		self.storage.fee_base = 1
		self.storage.fee_rate = 0
		self.storage.users[self.senderID] = storage.User(id=self.senderID, balance=0)
		self.storage.users[self.receiverID] = storage.User(id=self.receiverID, balance=0)


	def setBalance(self, userID, balance):
		self.storage.users[userID].balance = balance

	def getBalance(self, userID):
		return self.storage.users[userID].balance


	def getTransactionStatus(self, paymentHash):
		return self.storage.transactions[paymentHash].status


	def test_goodFlow_receiverPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)

		#Sender:
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)

		#Receiver:
		self.storage.processReceiverClaim(paymentPreimage)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)


	def test_goodFlow_senderPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=False)
		self.assertEqual(senderAmount,   101) #fee added
		self.assertEqual(receiverAmount, 100) #not affected by fee
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)

		#Sender:
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)

		#Receiver:
		self.storage.processReceiverClaim(paymentPreimage)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)

	#TODO: time-out scenarios

	def test_startTransaction_invalidUser(self):
		with self.assertRaises(storage.Storage.UserNotFound):
			self.storage.startTransaction(1312, amount=100, timeDelta=5, receiverPaysFee=True)


	def test_startTransaction_insufficientAmount(self):
		self.storage.fee_base = 1
		self.storage.fee_rate = 0

		for amount in [-1, 0, 1]:
			with self.assertRaises(storage.Storage.InsufficientAmount):
				self.storage.startTransaction(self.receiverID, amount=amount, timeDelta=5, receiverPaysFee=True)

		self.storage.startTransaction(self.receiverID, amount=2, timeDelta=5, receiverPaysFee=True)

		for amount in [-1, 0]:
			with self.assertRaises(storage.Storage.InsufficientAmount):
				self.storage.startTransaction(self.receiverID, amount=amount, timeDelta=5, receiverPaysFee=False)

		self.storage.startTransaction(self.receiverID, amount=1, timeDelta=5, receiverPaysFee=False)


	def test_processTimeout_NOPs(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Test that it succeeds for non-existing transactions
		self.storage.processTimeout(b'x'*32)

		#Now test it in states where it should be a NOP too

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)

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
		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		with self.assertRaises(storage.Storage.UserNotFound):
			self.storage.processSenderAck(1312, amount=senderAmount, paymentHash=paymentHash)


	def test_processSenderAck_invalidPaymentHash(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=100, paymentHash=b'x'*32)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		self.storage.processTimeout(paymentHash)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.storage.processReceiverClaim(paymentPreimage)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)


	def test_processSenderAck_insufficientFunds(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=501, timeDelta=5, receiverPaysFee=True)
		self.assertEqual(senderAmount, 501)
		with self.assertRaises(storage.Storage.InsufficientFunds):
			self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
			self.assertEqual(self.getBalance(self.senderID), 500)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=500, timeDelta=5, receiverPaysFee=True)
		self.assertEqual(senderAmount, 500)
		self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 0)


	def test_processReceiverClaim_invalidPaymentHash(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(b'x'*32)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		paymentPreimage = self.storage.transactions[paymentHash].preimage
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		paymentPreimage = self.storage.transactions[paymentHash].preimage
		self.storage.processTimeout(paymentHash)
		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200)

		senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=100, timeDelta=5, receiverPaysFee=True)
		paymentPreimage = self.storage.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash)
		self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)

		with self.assertRaises(storage.Storage.TransactionNotFound):
			self.storage.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)


	def test_feeAmounts(self):
		self.storage.fee_base = 1
		self.storage.fee_rate = decimal.Decimal('0.0025')

		for amount in [2, 10, 1000, 10000]:
			expectedFee = 1 + (25*amount) // 10000

			senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=amount, timeDelta=5, receiverPaysFee=True)
			self.assertEqual(senderAmount,  amount)
			self.assertEqual(receiverAmount, amount - expectedFee)

			senderAmount, receiverAmount, paymentHash = self.storage.startTransaction(self.receiverID, amount=amount, timeDelta=5, receiverPaysFee=False)
			self.assertEqual(senderAmount,  amount + expectedFee)
			self.assertEqual(receiverAmount, amount)



if __name__ == '__main__':
	unittest.main()

