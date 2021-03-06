#    Copyright (C) 2018-2021 by Bitonic B.V.
#
#    This file is part of the BL4P Server.
#
#    The BL4P Server is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The BL4P Server is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with the BL4P Server. If not, see <http://www.gnu.org/licenses/>.

import decimal
import hashlib
import logging
import os
import time

import secp256k1

from .api import selfreport

from .utils import Struct, Enum



sha256 = lambda preimage: hashlib.sha256(preimage).digest()



class User(Struct):
	id = None     #int: user ID
	balance = 0   #int: balance
	pubKey = None #secp256k1.PublicKey: public key for self-reporting



'''
(initial) -> waiting_for_selfreport -> waiting_for_sender -> waiting_for_receiver -> completed
waiting_for_sender -> sender_timeout
waiting_for_receiver -> receiver_timeout
waiting_for_selfreport -> canceled
waiting_for_sender -> canceled
waiting_for_receiver -> canceled
'''
TransactionStatus = Enum(['waiting_for_selfreport', 'waiting_for_sender', 'waiting_for_receiver', 'sender_timeout', 'receiver_timeout', 'completed', 'canceled'])

class Transaction(Struct):
	sender_userid = None   #int or None: sender user ID
	receiver_userid = None #int: receiver user id
	amountIncoming = 0     #int: amount to be taken from sender
	amountOutgoing = 0     #int: amount to be given to receiver
	preimage = None        #bytes: payment preimage
	senderTimeout = None   #float: sender time-out (seconds since UNIX epoch)
	receiverTimeout = None #float: receiver time-out (seconds since UNIX epoch)
	status = None          #TransactionStatus: status


class BL4P:
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


	class InvalidTimeout(Exception):
		pass


	class InsufficientFunds(Exception):
		pass


	class SignatureFailure(Exception):
		pass


	class MissingData(Exception):
		pass


	def __init__(self):
		self.users = {}
		self.transactions = {}

		#1 + 0.25% fee:
		self.fee_rate = decimal.Decimal('0.0025')
		self.fee_base = 1

		self.maxLockedTimeout = 366 * 24 * 3600 #one year
		self.minTimeBetweenTimeouts = 1         #one second


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
			raise BL4P.UserNotFound()

		assert ret.id == userid
		return ret


	def getTransaction(self, paymentHash, acceptableStates=None):
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
			logging.warning(
				'getTransaction: payment hash not found'
				)
			raise BL4P.TransactionNotFound()

		if acceptableStates is not None and ret.status not in acceptableStates:
			logging.warning(
				'getTransaction: payment is not in an acceptable state: state %s; acceptable %s' % \
				(ret.status, str(acceptableStates))
				)
			raise BL4P.TransactionNotFound()

		return ret


	def startTransaction(self, receiver_userid, amount, senderTimeout, lockedTimeout, receiverPaysFee):
		'''
		Start a new transaction.

		:param receiver_userid: the user ID of the receiver
		:param amount: the amount to be transfered from sender to receiver
		:param senderTimeout: the maximum time for the sender to respond, in seconds
		:param lockedTimeout: the maximum time until a locked transaction goes back to sender, in seconds
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
			logging.warning(
				'startTransaction: insufficient amount (incoming: %d; outgoing: %d)' % \
				(amountIncoming, amountOutgoing))
			raise BL4P.InsufficientAmount()

		if lockedTimeout <= 0.0:
			logging.warning('startTransaction: invalid locked timeout (%f <= 0)' % \
				lockedTimeout
				)
			raise BL4P.InvalidTimeout()

		if lockedTimeout > self.maxLockedTimeout:
			logging.warning('startTransaction: invalid locked timeout (%f > %f)' % \
				(lockedTimeout, self.maxLockedTimeout)
				)
			raise BL4P.InvalidTimeout()

		if senderTimeout <= 0.0:
			logging.warning(
				'startTransaction: invalid sender timeout (%f <= 0)' % \
				senderTimeout
				)
			raise BL4P.InvalidTimeout()

		if senderTimeout > lockedTimeout - self.minTimeBetweenTimeouts:
			logging.warning(
				'startTransaction: invalid sender timeout (%f > %f)' % \
				(senderTimeout, lockedTimeout - self.minTimeBetweenTimeouts)
				)
			raise BL4P.InvalidTimeout()

		preimage = os.urandom(32) #TODO: HD wallet instead?
		paymentHash = sha256(preimage)

		currentTime = time.time()
		senderTimeout = currentTime + senderTimeout
		receiverTimeout = currentTime + lockedTimeout

		logging.info(
			'startTransaction: amountIncoming: %d; amountOutgoing: %d' % \
			(amountIncoming, amountOutgoing)
			)
		logging.info('  Current balance of receiving user %d: %d' % \
			(receiver_userid, self.getUser(receiver_userid).balance)
			)

		tx = Transaction(
			sender_userid = None,
			receiver_userid = receiver_userid,
			amountIncoming = amountIncoming,
			amountOutgoing = amountOutgoing,
			preimage = preimage,
			senderTimeout = senderTimeout,
			receiverTimeout = receiverTimeout,
			status = TransactionStatus.waiting_for_selfreport
			)
		self.transactions[paymentHash] = tx
		return amountIncoming, amountOutgoing, paymentHash


	def processSelfReport(self, receiver_userid, report, signature):
		'''
		Process self-reporting by the receiver.

		:param receiver_userid: the user ID of the receiver
		:param report: the serialized report
		:param signature: the user's signature over the report report

		:raises SignatureFailure: the signature is not correct
		:raises TransactionNotFound: No transaction was found for this user and hash
		:raises MissingData: The report is missing required data
		'''

		user = self.getUser(receiver_userid)
		try:
			sigObject = user.pubKey.ecdsa_deserialize(signature)
			assert user.pubKey.ecdsa_verify(report, sigObject)
		except:
			#On *anything* that goes wrong, including assertion failure:
			raise BL4P.SignatureFailure()

		#TODO: propagate correct exception type if this fails
		contents = selfreport.deserialize(report)

		#We require this data:
		try:
			paymentHash = bytes.fromhex(contents['paymentHash'])
			offerID = int(contents['offerID'])
			receiverCryptoAmount = decimal.Decimal(contents['receiverCryptoAmount'])
			cryptoCurrency = contents['cryptoCurrency']
		except KeyError:
			raise BL4P.MissingData()

		tx = self.getTransaction(paymentHash, [TransactionStatus.waiting_for_selfreport])

		if tx.receiver_userid != receiver_userid:
			#The transaction exists globally, but not in this user's transactions.
			raise BL4P.TransactionNotFound()

		logging.info('selfReport: ' + str(contents))

		#TODO: store report and signature data

		tx.status = TransactionStatus.waiting_for_sender


	def cancelTransaction(self, receiver_userid, paymentHash):
		'''
		Cancel transaction initiated by the receiver.

		:param receiver_userid: the user ID of the receiver
		:param paymentHash: the payment hash

		:raises TransactionNotFound: No transaction was found for this user and hash
		'''

		tx = self.getTransaction(paymentHash,
			[TransactionStatus.waiting_for_selfreport, TransactionStatus.waiting_for_sender, TransactionStatus.waiting_for_receiver]
			)

		if tx.receiver_userid != receiver_userid:
			#The transaction exists globally, but not in this user's transactions.
			raise BL4P.TransactionNotFound()

		if tx.status == TransactionStatus.waiting_for_receiver:
			#Funds are already sent - give back to sender
			sender = self.getUser(tx.sender_userid)
			sender.balance += tx.amountIncoming

		logging.info('cancelTransaction')

		tx.status = TransactionStatus.canceled


	def processSenderAck(self, sender_userid, amount, paymentHash, maxLockedTimeout, report, signature):
		'''
		Process acknowledgement by the sender.

		:param sender_userid: the user ID of the sender
		:param amount: the amount to be transfered from sender to receiver
		:param paymentHash: the payment hash
		:param maxLockedTimeout: the maximum time until a locked transaction goes back to sender, in seconds
		
		:param report: the serialized report
		:param signature: the user's signature over the report report

		:returns: the payment preimage

		:raises SignatureFailure: the signature is not correct
		:raises UserNotFound: No user was found with this ID
		:raises TransactionNotFound: No transaction was found for this payment hash and amount
		:raises InsufficientFunds: The sender has insufficient funds to pay the given amount
		:raises MissingData: The report is missing required data
		'''

		sender = self.getUser(sender_userid)

		try:
			sigObject = sender.pubKey.ecdsa_deserialize(signature)
			assert sender.pubKey.ecdsa_verify(report, sigObject)
		except:
			#On *anything* that goes wrong, including assertion failure:
			raise BL4P.SignatureFailure()

		#TODO: propagate correct exception type if this fails
		contents = selfreport.deserialize(report)

		#We require this data:
		try:
			paymentHash = bytes.fromhex(contents['paymentHash'])
			offerID = int(contents['offerID'])
			receiverCryptoAmount = decimal.Decimal(contents['receiverCryptoAmount'])
			cryptoCurrency = contents['cryptoCurrency']
		except KeyError:
			raise BL4P.MissingData()

		#TODO: compare against receiver reported data

		#TODO: store report and signature data

		tx = self.getTransaction(paymentHash,
			[
			TransactionStatus.waiting_for_sender,
			TransactionStatus.waiting_for_receiver
			])
		if tx.amountIncoming != amount:
			logging.warning(
				'processSenderAck: amount mismatch (is: %d; should be: %d)' % \
				(amount, tx.amountIncoming)
				)
			raise BL4P.TransactionNotFound()

		currentTime = time.time()
		lockedTimeout = tx.receiverTimeout - currentTime
		if lockedTimeout > maxLockedTimeout:
			logging.warning(
				'processSenderAck: locked timeout mismatch (actual: %d > max: %d)' % \
				(lockedTimeout, maxLockedTimeout)
				)
			raise BL4P.TransactionNotFound()

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
				logging.warning('processSenderAck: userID mismatch on later call')
				raise BL4P.TransactionNotFound()

			#We're clear:
			return tx.preimage

		#Otherwise (waiting_for_sender), take funds from the sender:
		#This is the 1st call
		if sender.balance < amount:
			logging.warning('processSenderAck: insufficient funds')
			raise BL4P.InsufficientFunds()

		logging.info('senderAck')
		logging.info('  Old balance of sending user %d: %d' % \
			(sender_userid, sender.balance)
			)

		sender.balance -= amount

		logging.info('  New balance of sending user %d: %d' % \
			(sender_userid, sender.balance)
			)

		tx.sender_userid = sender_userid
		tx.status = TransactionStatus.waiting_for_receiver
		return tx.preimage


	def processReceiverClaim(self, paymentPreimage):
		'''
		Process transaction claim by the receiver.

		:param paymentPreimage: the payment preimage

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

		paymentHash = sha256(paymentPreimage)
		tx = self.getTransaction(paymentHash, [TransactionStatus.waiting_for_receiver])
		receiver = self.getUser(tx.receiver_userid)

		logging.info('receiverAck')

		logging.info('  Old balance of receiving user %d: %d' % \
			(tx.receiver_userid, receiver.balance)
			)

		receiver.balance += tx.amountOutgoing

		logging.info('  New balance of receiving user %d: %d' % \
			(tx.receiver_userid, receiver.balance)
			)

		tx.status = TransactionStatus.completed


	def getTransactionStatus(self, userid, paymentHash):
		'''
		Return transaction status to either sender or receiver.

		:param userid: the user ID of the sender or receiver
		:param paymentHash: the payment hash

		:returns: the status

		:raises UserNotFound: No user was found with this ID
		:raises TransactionNotFound: No transaction was found for this payment hash and amount
		'''

		#Just check that the user exists
		self.getUser(userid)

		tx = self.getTransaction(paymentHash)
		if userid not in (tx.sender_userid, tx.receiver_userid):
			raise BL4P.TransactionNotFound()

		return str(tx.status)


	def processTimeouts(self):
		'''
		Process transaction time-out events.

		:returns: the time-delta to the next time-out, or None
		'''

		t = time.time()

		nextTimeout = None

		#TODO: cache a sorted time-out list, to make this scalable
		for tx in self.transactions.values():
			#We have two kinds of time-outs
			if tx.status == TransactionStatus.waiting_for_sender:
				timeout, handler = tx.senderTimeout, self.processSenderTimeout
			elif tx.status == TransactionStatus.waiting_for_receiver:
				timeout, handler = tx.receiverTimeout, self.processReceiverTimeout
			else:
				#python3-coverage doesn't detect coverage of
				#this case, due to a Python optimization.
				continue # pragma: no cover

			if timeout <= t:
				#This time-out has happened
				handler(tx)

			elif nextTimeout is None or timeout < nextTimeout:
				#This is the upcoming time-out
				nextTimeout = timeout

		return None if nextTimeout is None else nextTimeout - t


	def processSenderTimeout(self, tx):
		logging.info('Sender time-out happened')
		assert tx.status == TransactionStatus.waiting_for_sender
		tx.status = TransactionStatus.sender_timeout


	def processReceiverTimeout(self, tx):
		logging.info('Receiver time-out happened')
		assert tx.status == TransactionStatus.waiting_for_receiver

		tx.status = TransactionStatus.receiver_timeout
		sender = self.getUser(tx.sender_userid)
		sender.balance += tx.amountIncoming

