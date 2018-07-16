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


	def __init__(self):
		self.users = {}
		self.transactions = {}


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


	def startTransaction(self, receiver_userid, amount, timeDelta):
		'''
		Start a new transaction.

		:param receiver_userid: the user ID of the receiver
		:param amount: the amount to be transfered from sender to receiver
		:param timeDelta: the maximum time for the sender to respond, in seconds

		:returns: the payment hash

		:raises UserNotFound: No user was found with this ID
		'''

		#Just check that the user exists
		self.getUser(receiver_userid)

		fee = 0 #TODO

		assert amount > 0
		assert amount - fee > 0

		preimage = os.urandom(32) #TODO: HD wallet instead?
		paymentHash = sha256(preimage)
		timeoutTime = time.time() + timeDelta

		tx = Transaction(
			sender_userid = None,
			receiver_userid = receiver_userid,
			amountIncoming = amount,
			amountOutgoing = amount - fee, #receiver pays fee
			preimage = preimage,
			timeoutTime = timeoutTime,
			status = TransactionStatus.waiting_for_sender
			)
		self.transactions[paymentHash] = tx
		return paymentHash


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
		:raises TransactionNotFound: No transaction was found for this payment hash
		'''

		sender = self.getUser(sender_userid)

		tx = self.getTransaction(paymentHash,
			[
			TransactionStatus.waiting_for_sender,
			TransactionStatus.waiting_for_receiver
			])

		assert sender.balance >= amount
		assert tx.amountIncoming == amount

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

		paymentHash = sha256(preimage)
		tx = self.getTransaction(paymentHash, [TransactionStatus.waiting_for_receiver])
		receiver = self.getUser(tx.receiver_userid)

		receiver.balance += tx.amountOutgoing
		tx.status = TransactionStatus.completed

