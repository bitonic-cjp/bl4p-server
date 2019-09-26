import decimal
import sys
import time
import unittest

sys.path.append('..')

import bl4p_backend
from api import selfreport



class Dummy:
	pass



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


	def bl4p_startTransaction(self, amount=100, senderTimeout=5, lockedTimeout=5000, receiverPaysFee=True):
		data = Dummy()
		data.senderAmount, data.receiverAmount, data.paymentHash = \
			self.bl4p.startTransaction(
				self.receiverID, amount=amount, senderTimeout=senderTimeout, lockedTimeout=lockedTimeout, receiverPaysFee=receiverPaysFee)
		data.lockedTimeout = lockedTimeout
		return data


	def bl4p_processSelfReport(self, data):
		report = \
		{
		'paymentHash': data.paymentHash.hex(),
		'offerID': '42',
		'receiverCryptoAmount': '6',
		'cryptoCurrency': 'btc'
		}
		self.bl4p.processSelfReport(self.receiverID, selfreport.serialize(report), b'bar')


	def bl4p_cancelTransaction(self, data):
		self.bl4p.cancelTransaction(self.receiverID, data.paymentHash)


	def bl4p_processSenderAck(self, data):
		report = \
		{
		'paymentHash': data.paymentHash.hex(),
		'offerID': '42',
		'receiverCryptoAmount': '6',
		'cryptoCurrency': 'btc'
		}
		data.paymentPreimage = self.bl4p.processSenderAck(
			self.senderID, amount=data.senderAmount, paymentHash=data.paymentHash, maxLockedTimeout=data.lockedTimeout, report=selfreport.serialize(report), signature=b'bar')


	def bl4p_processReceiverClaim(self, data):
		self.bl4p.processReceiverClaim(data.paymentPreimage)


	def test_goodFlow_receiverPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		data = self.bl4p_startTransaction()
		self.assertEqual(data.senderAmount,  100) #not affected by fee
		self.assertEqual(data.receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_sender')

		self.bl4p_processSelfReport(data)

		#Sender:
		self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(self.senderID), 500 - data.senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, data.paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p_processReceiverClaim(data)
		self.assertEqual(self.getBalance(self.senderID), 500 - data.senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + data.receiverAmount)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'completed')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, data.paymentHash), 'completed')


	def test_goodFlow_senderPaysFee(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		data = self.bl4p_startTransaction(receiverPaysFee=False)
		self.assertEqual(data.senderAmount,   101) #fee added
		self.assertEqual(data.receiverAmount, 100) #not affected by fee
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_sender')

		self.bl4p_processSelfReport(data)

		#Sender:
		self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(self.senderID), 500 - data.senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, data.paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p_processReceiverClaim(data)
		self.assertEqual(self.getBalance(self.senderID), 500 - data.senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200 + data.receiverAmount)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'completed')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, data.paymentHash), 'completed')


	def test_badFlow_senderTimeout(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		data = self.bl4p_startTransaction(senderTimeout=0.1)
		self.bl4p_processSelfReport(data)

		#Sender:
		time.sleep(0.2)
		self.bl4p.processTimeouts()
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'sender_timeout')


	def test_badFlow_receiverTimeout(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)
		self.bl4p.minTimeBetweenTimeouts = 0.01

		#Receiver:
		data = self.bl4p_startTransaction(senderTimeout=0.05, lockedTimeout=0.1)
		self.bl4p_processSelfReport(data)

		#Sender:
		self.bl4p_processSenderAck(data)

		#Receiver:
		time.sleep(0.2)
		self.bl4p.processTimeouts()
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'receiver_timeout')


	def test_canceled_after_start(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		data = self.bl4p_startTransaction()
		self.assertEqual(data.senderAmount,  100) #not affected by fee
		self.assertEqual(data.receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_sender')
		self.bl4p_processSelfReport(data)

		#Receiver:
		self.bl4p_cancelTransaction(data)
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'canceled')


	def test_canceled_after_sent(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Receiver:
		data = self.bl4p_startTransaction()
		self.assertEqual(data.senderAmount,  100) #not affected by fee
		self.assertEqual(data.receiverAmount, 99) #fee subtracted
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_sender')
		self.bl4p_processSelfReport(data)

		#Sender:
		self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(self.senderID), 500 - data.senderAmount)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'waiting_for_receiver')
		self.assertEqual(self.bl4p.getTransactionStatus(self.senderID, data.paymentHash), 'waiting_for_receiver')

		#Receiver:
		self.bl4p_cancelTransaction(data)
		self.assertEqual(self.getBalance(self.senderID), 500)
		self.assertEqual(self.getBalance(self.receiverID), 200)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data.paymentHash), 'canceled')


	def test_startTransaction_UserNotFound(self):
		self.receiverID = 1312
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p_startTransaction()


	def test_startTransaction_InsufficientAmount(self):
		self.bl4p.fee_base = 1
		self.bl4p.fee_rate = 0

		for amount in [-1, 0, 1]:
			with self.assertRaises(self.bl4p.InsufficientAmount):
				self.bl4p_startTransaction(amount=amount)

		self.bl4p_startTransaction(amount=2)

		for amount in [-1, 0]:
			with self.assertRaises(self.bl4p.InsufficientAmount):
				self.bl4p_startTransaction(amount=amount, receiverPaysFee=False)

		self.bl4p_startTransaction(amount=1, receiverPaysFee=False)


	def test_startTransaction_InvalidSenderTimeout(self):
		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p_startTransaction(senderTimeout=-0.1)

		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p_startTransaction(senderTimeout=5000)


	def test_startTransaction_InvalidLockedTimeout(self):
		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p_startTransaction(lockedTimeout=-0.1)

		with self.assertRaises(self.bl4p.InvalidTimeout):
			self.bl4p_startTransaction(lockedTimeout=40000000)


	def test_cancelTransaction_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		data = Dummy()
		data.paymentHash = b'x'*32
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_cancelTransaction(data)

		data = self.bl4p_startTransaction()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.cancelTransaction(self.senderID, paymentHash=data.paymentHash)

		data = self.bl4p_startTransaction(senderTimeout=0.01)
		time.sleep(0.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_cancelTransaction(data)

		data = self.bl4p_startTransaction(senderTimeout=0.01, lockedTimeout=1.02)
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		time.sleep(1.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_cancelTransaction(data)

		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		self.bl4p_processReceiverClaim(data)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_cancelTransaction(data)


	def test_processSenderAck_UserNotFound(self):
		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		self.senderID = 1312
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p_processSenderAck(data)


	def test_processSenderAck_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		#Tx was never created:
		data = Dummy()
		data.senderAmount = 100
		data.paymentHash = b'x'*32
		data.lockedTimeout = 5000
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)

		#Tx was created, but timed out:
		data = self.bl4p_startTransaction(senderTimeout=0.01)
		self.bl4p_processSelfReport(data)
		time.sleep(0.1)
		self.assertEqual(self.bl4p.processTimeouts(), None)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)

		#Tx was created, but already finished by now:
		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		self.bl4p_processReceiverClaim(data)
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)

		#Tx was created, but has a different amount:
		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		data.senderAmount += 1
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)

		#Tx was created, but has an incompatible locked timeout:
		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		data.lockedTimeout -= 1
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)


	def test_processSenderAck_InsufficientFunds(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		data = self.bl4p_startTransaction(amount=501)
		self.assertEqual(data.senderAmount, 501)
		self.bl4p_processSelfReport(data)
		with self.assertRaises(self.bl4p.InsufficientFunds):
			self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(self.senderID), 500)

		data = self.bl4p_startTransaction(amount=500)
		self.assertEqual(data.senderAmount, 500)
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(self.senderID), 0)


	def test_processSenderAck_multipleCalls(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		paymentPreimage1 = data.paymentPreimage
		self.assertEqual(self.getBalance(self.senderID), 400)

		self.bl4p_processSenderAck(data)
		paymentPreimage2 = data.paymentPreimage
		self.assertEqual(paymentPreimage1, paymentPreimage2)
		self.assertEqual(self.getBalance(self.senderID), 400)

		realSenderID = self.senderID
		self.senderID = self.receiverID
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processSenderAck(data)
		self.assertEqual(self.getBalance(realSenderID), 400)


	def test_processReceiverClaim_TransactionNotFound(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)

		data = Dummy()
		data.paymentPreimage = b'x'*32
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processReceiverClaim(data)

		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		data.paymentPreimage = self.bl4p.transactions[data.paymentHash].preimage
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processReceiverClaim(data)

		data = self.bl4p_startTransaction(senderTimeout=0.01)
		self.bl4p_processSelfReport(data)
		data.paymentPreimage = self.bl4p.transactions[data.paymentHash].preimage
		time.sleep(0.1)
		self.bl4p.processTimeouts()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processReceiverClaim(data)

		self.assertEqual(self.getBalance(self.receiverID), 200)

		data = self.bl4p_startTransaction()
		self.bl4p_processSelfReport(data)
		self.bl4p_processSenderAck(data)
		self.bl4p_processReceiverClaim(data)

		self.assertEqual(self.getBalance(self.receiverID), 200 + data.receiverAmount)

		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p_processReceiverClaim(data)

		self.assertEqual(self.getBalance(self.receiverID), 200 + data.receiverAmount)


	def test_processSelfReport_MissingData(self):
		data = self.bl4p_startTransaction()
		for missing in ['paymentHash', 'offerID', 'receiverCryptoAmount', 'cryptoCurrency']:
			report = \
			{
			'paymentHash': data.paymentHash.hex(),
			'offerID': '42',
			'receiverCryptoAmount': '6',
			'cryptoCurrency': 'btc'
			}
			del report[missing]
			with self.assertRaises(self.bl4p.MissingData):
				self.bl4p.processSelfReport(self.receiverID, selfreport.serialize(report), b'bar')


	def test_getTransactionStatus_UserNotFound(self):
		data = self.bl4p_startTransaction()
		with self.assertRaises(self.bl4p.UserNotFound):
			self.bl4p.getTransactionStatus(1312, paymentHash=data.paymentHash)


	def test_getTransactionStatus_TransactionNotFound(self):
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.getTransactionStatus(self.receiverID, paymentHash='xxx')

		data = self.bl4p_startTransaction()
		with self.assertRaises(self.bl4p.TransactionNotFound):
			self.bl4p.getTransactionStatus(self.senderID, paymentHash=data.paymentHash)


	def test_processTimeouts(self):
		self.setBalance(self.senderID, 500)
		self.setBalance(self.receiverID, 200)
		self.bl4p.minTimeBetweenTimeouts = 0.01

		#Timeout sequence
		data1 = self.bl4p_startTransaction(senderTimeout=2)
		data2 = self.bl4p_startTransaction(senderTimeout=1)
		data3 = self.bl4p_startTransaction(senderTimeout=2)
		data4 = self.bl4p_startTransaction(senderTimeout=3)
		self.bl4p_processSelfReport(data1)
		self.bl4p_processSelfReport(data2)
		self.bl4p_processSelfReport(data3)
		self.bl4p_processSelfReport(data4)
		time.sleep(0.5)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data1.paymentHash), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data2.paymentHash), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data3.paymentHash), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data4.paymentHash), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data1.paymentHash), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data2.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data3.paymentHash), 'waiting_for_sender')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data4.paymentHash), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertAlmostEqual(ret, 0.5, places=2)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data1.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data2.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data3.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data4.paymentHash), 'waiting_for_sender')

		time.sleep(1)
		ret = self.bl4p.processTimeouts()
		self.assertEqual(ret, None)
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data1.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data2.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data3.paymentHash), 'sender_timeout')
		self.assertEqual(self.bl4p.getTransactionStatus(self.receiverID, data4.paymentHash), 'sender_timeout')

		ret = self.bl4p.processTimeouts()
		self.assertEqual(ret, None)


		#processTimeouts should be a NOP in these cases:

		data = self.bl4p_startTransaction(senderTimeout=0.1, lockedTimeout=0.2)
		self.bl4p_processSelfReport(data)
		time.sleep(0.05)

		statusBefore = self.getTransactionStatus(data.paymentHash)
		self.bl4p.processTimeouts()
		statusAfter = self.getTransactionStatus(data.paymentHash)
		self.assertEqual(statusBefore, statusAfter)

		self.bl4p_processSenderAck(data)

		statusBefore = self.getTransactionStatus(data.paymentHash)
		self.bl4p.processTimeouts()
		statusAfter = self.getTransactionStatus(data.paymentHash)
		self.assertEqual(statusBefore, statusAfter)

		self.bl4p_processReceiverClaim(data)

		statusBefore = self.getTransactionStatus(data.paymentHash)
		self.assertEqual(self.bl4p.processTimeouts(), None)
		statusAfter = self.getTransactionStatus(data.paymentHash)
		self.assertEqual(statusBefore, statusAfter)


	def test_feeAmounts(self):
		self.bl4p.fee_base = 1
		self.bl4p.fee_rate = decimal.Decimal('0.0025')

		for amount in [2, 10, 1000, 10000]:
			expectedFee = 1 + (25*amount) // 10000

			data = self.bl4p_startTransaction(amount=amount)
			self.assertEqual(data.senderAmount,  amount)
			self.assertEqual(data.receiverAmount, amount - expectedFee)

			data = self.bl4p_startTransaction(amount=amount, receiverPaysFee=False)
			self.assertEqual(data.senderAmount,  amount + expectedFee)
			self.assertEqual(data.receiverAmount, amount)


if __name__ == '__main__':
	unittest.main(verbosity=2)

