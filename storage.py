import time
import os

from utils import Struct, Enum



class User(Struct):
	id = None
	balance = 0


TransactionStatus = Enum(['waiting_for_sender', 'waiting_for_receiver', 'timeout', 'completed'])

class Transaction(Struct):
	sender_userid = None
	received_userid = None
	amount = 0
	preimage = None
	timeoutTime = None
	status = None


class Storage:
	def __init__(self):
		self.users = {}
		self.transactions = {}


	def startTransaction(self, receiver_userid, amount, timeDelta):
		#Just check that the user exists
		receiver = self.users[receiver_userid]
		assert receiver.id == receiver_userid

		preimage = os.urandom(32) #TODO: HD wallet instead?
		paymentHash = preimage #TODO: hash function
		timeoutTime = time.time() + timeDelta

		tx = Transaction(
			sender_userid = None,
			receiver_userid = receiver_userid,
			amount = amount,
			preimage = preimage,
			timeoutTime = timeoutTime,
			status = TransactionStatus.waiting_for_sender
			)
		self.transactions[paymentHash] = tx
		return paymentHash


	def processTimeout(self, paymentHash):
		tx = self.transactions[paymentHash]
		if tx.status == TransactionStatus.waiting_for_sender:
			tx.status = TransactionStatus.timeout


	def processSenderAck(self, sender_userid, amount, paymentHash):
		sender = self.users[sender_userid]
		assert sender.id == sender_userid

		tx = self.transactions[paymentHash]

		#TODO: take fees
		assert sender.balance >= amount
		assert tx.amount == amount

		sender.balance -= amount
		tx.sender_userid = sender_userid
		tx.status = TransactionStatus.waiting_for_receiver
		return tx.preimage


	def processReceiverClaim(self, preimage):
		paymentHash = preimage #TODO: hash function
		tx = self.transactions[paymentHash]
		receiver = self.users[tx.receiver_userid]

		assert tx.status == TransactionStatus.waiting_for_receiver

		#TODO: take fees
		receiver.balance += tx.amount
		tx.status = TransactionStatus.completed

