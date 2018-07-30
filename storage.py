import decimal
import hashlib
import os
import time

from utils import Struct, Enum



sha256 = lambda preimage: hashlib.sha256(preimage).digest()



class User(Struct):
	id = None   #int: user ID
	balance = 0 #int: balance


TransactionStatus = Enum(['waiting_for_sender', 'waiting_for_receiver', 'timeout', 'completed'])

class Transaction(Struct):
	sender_userid = None   #int or None: sender user ID
	receiver_userid = None #int: receiver user id
	amountIncoming = 0     #int: amount to be taken from sender
	amountOutgoing = 0     #int: amount to be given to receiver
	preimage = None        #bytes: payment preimage
	timeoutTime = None     #float: payment time-out (seconds since UNIX epoch)
	status = None          #TransactionStatus: status


class Storage:
	'''
	BL4P data storage and business logic back-end.
	This is a dummy class with only volatile (internal memory) storage.
	An actual implementation should use something like SQL with
	atomic database transactions.
	'''

	class UserNotFound(Exception):
		pass

	class TransactionNotFound(Exception):
		pass


	class InsufficientAmount(Exception):
		pass


	class InvalidTimeDelta(Exception):
		pass


	class InsufficientFunds(Exception):
		pass


	def __init__(self):
		self.users = {}
		self.transactions = {}

		self.fee_rate = decimal.Decimal('0.0025')
		self.fee_base = 1


	def getUser(self, userid):
		'''
		Get the user data structure for a user.

		:param userid: the user ID

		:returns: the user data structure

		:raises UserNotFound: No user was found with this ID
		'''

		try:
			ret = self.users[userid]
		except KeyError:
			raise Storage.UserNotFound()

		assert ret.id == userid
		return ret


	def getTransaction(self, paymentHash, acceptableStates):
		'''
		Get the user data structure for a transaction.

		:param paymentHash: the payment hash
		:param acceptableStates: iterable containing acceptable states

		:returns: the transaction data structure

		:raises TransactionNotFound: No transaction was found for this payment hash and acceptable states
		'''
		try:
			ret = self.transactions[paymentHash]
		except KeyError:
			raise Storage.TransactionNotFound()

		if ret.status not in acceptableStates:
			raise Storage.TransactionNotFound()

		return ret


	def startTransaction(self, receiver_userid, amount, timeDelta, receiverPaysFee):
		'''
		Start a new transaction.

		:param receiver_userid: the user ID of the receiver
		:param amount: the amount to be transfered from sender to receiver
		:param timeDelta: the maximum time for the sender to respond, in seconds
		:param receiverPaysFee: indicates whether receiver or sender pays the fee

		:returns: tuple (sender amount, receiver amount, payment hash)

		:raises UserNotFound: No user was found with this ID
		:raises InsufficientAmount: The amount is non-positive (maybe after subtraction of fees)
		:raises InvalidTimeDelta: The time-delta is non-positive
		'''

		#Just check that the user exists
		self.getUser(receiver_userid)

		fee = int(self.fee_base + self.fee_rate * amount)

		if receiverPaysFee:
			amountIncoming = amount
			amountOutgoing = amount - fee
		else:
			amountIncoming = amount + fee
			amountOutgoing = amount

		if amountOutgoing <= 0:
			raise Storage.InsufficientAmount()

		if timeDelta <= 0.0:
			raise Storage.InvalidTimeDelta()

		preimage = os.urandom(32) #TODO: HD wallet instead?
		paymentHash = sha256(preimage)
		timeoutTime = time.time() + timeDelta

		tx = Transaction(
			sender_userid = None,
			receiver_userid = receiver_userid,
			amountIncoming = amountIncoming,
			amountOutgoing = amountOutgoing,
			preimage = preimage,
			timeoutTime = timeoutTime,
			status = TransactionStatus.waiting_for_sender
			)
		self.transactions[paymentHash] = tx
		return amountIncoming, amountOutgoing, paymentHash


	def processTimeout(self, paymentHash):
		'''
		Process a transaction time-out event.

		:param paymentHash: the payment hash of the transaction
		'''

		try:
			tx = self.getTransaction(paymentHash, [TransactionStatus.waiting_for_sender])
			tx.status = TransactionStatus.timeout
		except Storage.TransactionNotFound:
			#It's OK to NOP if that transaction does not exist,
			#or if it no longer has the required state.
			pass


	def processSenderAck(self, sender_userid, amount, paymentHash):
		'''
		Process acknowledgement by the sender.

		:param sender_userid: the user ID of the sender
		:param amount: the amount to be transfered from sender to receiver
		:param paymentHash: the payment hash

		:returns: the payment preimage

		:raises UserNotFound: No user was found with this ID
		:raises TransactionNotFound: No transaction was found for this payment hash and amount
		:raises InsufficientFunds: The sender has insufficient funds to pay the given amount
		'''

		sender = self.getUser(sender_userid)

		tx = self.getTransaction(paymentHash,
			[
			TransactionStatus.waiting_for_sender,
			TransactionStatus.waiting_for_receiver
			])
		if tx.amountIncoming != amount:
			raise Storage.TransactionNotFound()

		#In case of waiting_for_receiver, only send back data:
		#This is the 2nd, 3d etc. call
		if tx.status == TransactionStatus.waiting_for_receiver:
			#First check if it's really the correct user:
			#This is important:
			#in case the sender manages to call this function a
			#first time but fails to get the preimage back,
			#and his incoming transaction times out,
			#the transaction must stay in limbo to give the sender
			#a chance to negotiate another payment for the funds.
			#For this, it is necessary the preimage stays a secret
			#between us and the sender.
			if tx.sender_userid != sender_userid:
				raise Storage.TransactionNotFound()

			#We're clear:
			return tx.preimage

		#Otherwise (waiting_for_sender), take funds from the sender:
		#This is the 1st call
		if sender.balance < amount:
			raise Storage.InsufficientFunds()

		sender.balance -= amount
		tx.sender_userid = sender_userid
		tx.status = TransactionStatus.waiting_for_receiver
		return tx.preimage


	def processReceiverClaim(self, preimage):
		'''
		Process transaction claim by the receiver.

		:param preimage: the payment preimage

		:raises TransactionNotFound: No transaction was found for this preimage
		'''

		#It's actually not that important who hands over the
		#receiver claim. The fact that *someone* hands it over to us
		#is proof that someone received the preimage and wants the
		#transaction to get out of limbo.
		#Since we only send the preimage to the sender, 
		#and the sender has an interest to keep the transaction in limbo
		#until its incoming funds are guaranteed,
		#this proves that the sender has its incoming funds guaranteed.
		#it's up to the sender to keep the preimage secret in other cases.
		#That's all we need to know.

		paymentHash = sha256(preimage)
		tx = self.getTransaction(paymentHash, [TransactionStatus.waiting_for_receiver])
		receiver = self.getUser(tx.receiver_userid)

		receiver.balance += tx.amountOutgoing
		tx.status = TransactionStatus.completed

