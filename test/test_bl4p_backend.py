import decimal
import sys
import time
import unittest

sys.path.append('..')

import bl4p_backend



class TestBL4P(unittest.TestCase):
	def setUp(self):
		self.receiverID = 3
		self.senderID = 6
		self.bl4p = bl4p_backend.BL4P()
		self.bl4p.fee_base = 1
		self.bl4p.fee_rate = 0
		self.bl4p.users[self.senderID] = bl4p_backend.User(id=self.senderID, balance=0)
		self.bl4p.users[self.receiverID] = bl4p_backend.User(id=self.receiverID, balance=0)


	def setBalance(self, userID, balance):
		self.bl4p.users[userID].balance = balance

	def getBalance(self, userID):
		return self.bl4p.users[userID].balance


	def getTransactionStatus(self, paymentHash):
		return self.bl4p.transactions[paymentHash].status


	def test_goodFlow_receiverPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_sender')

		#Sender:
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p.processReceiverClaim(paymentPreimage)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'completed')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, paymentHash), 'completed')


	def test_goodFlow_senderPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=False)
		self.assertEqual(senderAmount,   101) #fee added
		self.assertEqual(receiverAmount, 100) #not affected by fee
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_sender')

		#Sender:
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p.processReceiverClaim(paymentPreimage)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'completed')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, paymentHash), 'completed')


	def test_badFlow_senderTimeout(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.1, lockedTimeout=5000, receiverPaysFee=True)

		#Sender:
		time.sleep(0.2)
		self.bl4p.processTimeouts()
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'sender_timeout')


	def test_badFlow_receiverTimeout(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)
		self.bl4p.minTimeBetweenTimeouts = 0.01

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.05, lockedTimeout=0.1, receiverPaysFee=True)

		#Sender:
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)

		#Receiver:
		time.sleep(0.2)
		self.bl4p.processTimeouts()
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'receiver_timeout')


	def test_canceled_after_start(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_sender')

		#Receiver:
		self.bl4p.cancelTransaction(self.receiverID, paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'canceled')


	def test_canceled_after_sent(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		self.assertEqual(senderAmount,  100) #not affected by fee
		self.assertEqual(receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_sender')

		#Sender:
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(self.getBalance(self.senderID), 500 - senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p.cancelTransaction(self.receiverID, paymentHash)
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash), 'canceled')


	def test_startTransaction_UserNotFound(self):
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p.startTransaction(1312, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)


	def test_startTransaction_InsufficientAmount(self):
		self.bl4p.fee_base = 1
		self.bl4p.fee_rate = 0

		for amount in [-1, 0, 1]:
			with self.assertRaises(self.bl4p.InsufficientAmount):
				self.bl4p.startTransaction(self.receiverID, amount=amount, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)

		self.bl4p.startTransaction(self.receiverID, amount=2, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)

		for amount in [-1, 0]:
			with self.assertRaises(self.bl4p.InsufficientAmount):
				self.bl4p.startTransaction(self.receiverID, amount=amount, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=False)

		self.bl4p.startTransaction(self.receiverID, amount=1, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=False)


	def test_startTransaction_InvalidSenderTimeout(self):
		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=-0.1, lockedTimeout=5000, receiverPaysFee=True)

		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5000, lockedTimeout=5000, receiverPaysFee=True)


	def test_startTransaction_InvalidLockedTimeout(self):
		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=-0.1, receiverPaysFee=True)

		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=40000000, receiverPaysFee=True)


	def test_cancelTransaction_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.receiverID, paymentHash=b'x'*32)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.senderID, paymentHash=paymentHash)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.01, lockedTimeout=5000, receiverPaysFee=True)
		time.sleep(0.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.receiverID, paymentHash=paymentHash)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.01, lockedTimeout=1.02, receiverPaysFee=True)
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		time.sleep(1.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.receiverID, paymentHash=paymentHash)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.bl4p.processReceiverClaim(paymentPreimage)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.receiverID, paymentHash=paymentHash)


	def test_processSenderAck_UserNotFound(self):
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p.processSenderAck(1312, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)


	def test_processSenderAck_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Tx was never created:
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.senderID, amount=100, paymentHash=b'x'*32, maxLockedTimeout=5000)

		#Tx was created, but timed out:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.01, lockedTimeout=5000, receiverPaysFee=True)
		time.sleep(0.1)
		self.assertEqual(self.bl4p.processTimeouts(), None)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)

		#Tx was created, but already finished by now:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.bl4p.processReceiverClaim(paymentPreimage)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)

		#Tx was created, but has a different amount:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.senderID, amount=senderAmount+1, paymentHash=paymentHash, maxLockedTimeout=5000)

		#Tx was created, but has an incompatible locked timeout:
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=4999)


	def test_processSenderAck_InsufficientFunds(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=501, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		self.assertEqual(senderAmount, 501)
		with self.assertRaises(self.bl4p.InsufficientFunds):
			self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
			self.assertEqual(self.getBalance(self.senderID), 500)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=500, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		self.assertEqual(senderAmount, 500)
		self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(self.getBalance(self.senderID), 0)


	def test_processSenderAck_multipleCalls(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage1 = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(self.getBalance(self.senderID), 400)

		paymentPreimage2 = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.assertEqual(paymentPreimage1, paymentPreimage2)
		self.assertEqual(self.getBalance(self.senderID), 400)

		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processSenderAck(self.receiverID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
			self.assertEqual(self.getBalance(self.senderID), 400)


	def test_processReceiverClaim_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processReceiverClaim(b'x'*32)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage = self.bl4p.transactions[paymentHash].preimage
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processReceiverClaim(paymentPreimage)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.01, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage = self.bl4p.transactions[paymentHash].preimage
		time.sleep(0.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200)

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=5000)
		self.bl4p.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)

		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.processReceiverClaim(paymentPreimage)

		self.assertEqual(self.getBalance(self.receiverID), 200 + receiverAmount)


	def test_getTransactionStatus_UserNotFound(self):
		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p.getTransactionStatus(1312, paymentHash=paymentHash)


	def test_getTransactionStatus_TransactionNotFound(self):
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.getTransactionStatus(self.receiverID, paymentHash='xxx')

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.getTransactionStatus(self.senderID, paymentHash=paymentHash)


	def test_processTimeouts(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)
		self.bl4p.minTimeBetweenTimeouts = 0.01

		#Timeout sequence

		senderAmount, receiverAmount, paymentHash1 = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=2, lockedTimeout=5000, receiverPaysFee=True)
		senderAmount, receiverAmount, paymentHash2 = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=1, lockedTimeout=5000, receiverPaysFee=True)
		senderAmount, receiverAmount, paymentHash3 = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=2, lockedTimeout=5000, receiverPaysFee=True)
		senderAmount, receiverAmount, paymentHash4 = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=3, lockedTimeout=5000, receiverPaysFee=True)

		time.sleep(0.5)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash1), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash2), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash3), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash4), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash1), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash2), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash3), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash4), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash1), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash2), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash3), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash4), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertEqual(ret, None)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash1), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash2), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash3), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, paymentHash4), 'sender_timeout')

		ret = self.bl4p.processTimeouts()
		self.assertEqual(ret, None)


		#processTimeouts should be a NOP in these cases:

		senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=100, senderTimeout=0.1, lockedTimeout=0.2, receiverPaysFee=True)
		time.sleep(0.05)

		statusBefore = self.getTransactionStatus(paymentHash)
		self.bl4p.processTimeouts()
		statusAfter = self.getTransactionStatus(paymentHash)
		self.assertEqual(statusBefore, statusAfter)

		paymentPreimage = self.bl4p.processSenderAck(self.senderID, amount=senderAmount, paymentHash=paymentHash, maxLockedTimeout=0.2)

		statusBefore = self.getTransactionStatus(paymentHash)
		self.bl4p.processTimeouts()
		statusAfter = self.getTransactionStatus(paymentHash)
		self.assertEqual(statusBefore, statusAfter)

		self.bl4p.processReceiverClaim(paymentPreimage)

		statusBefore = self.getTransactionStatus(paymentHash)
		self.assertEqual(self.bl4p.processTimeouts(), None)
		statusAfter = self.getTransactionStatus(paymentHash)
		self.assertEqual(statusBefore, statusAfter)


	def test_feeAmounts(self):
		self.bl4p.fee_base = 1
		self.bl4p.fee_rate = decimal.Decimal('0.0025')

		for amount in [2, 10, 1000, 10000]:
			expectedFee = 1 + (25*amount) // 10000

			senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=amount, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True)
			self.assertEqual(senderAmount,  amount)
			self.assertEqual(receiverAmount, amount - expectedFee)

			senderAmount, receiverAmount, paymentHash = self.bl4p.startTransaction(self.receiverID, amount=amount, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=False)
			self.assertEqual(senderAmount,  amount + expectedFee)
			self.assertEqual(receiverAmount, amount)



if __name__ == '__main__':
	unittest.main(verbosity=2)

