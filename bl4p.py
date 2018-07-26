#!/usr/bin/env python3

import storage

receiverID = 3
senderID = 6

s = storage.Storage()
s.users[receiverID] = storage.User(id=receiverID, balance=2000)
s.users[senderID] = storage.User(id=senderID, balance=5000)

print('Before:')
print(s.users[senderID].balance)
print(s.users[receiverID].balance)

#Receiver:
senderAmount, receiverAmount, paymentHash = s.startTransaction(
	receiverID, amount=1000, timeDelta=5, receiverPaysFee=True)

#Sender:
paymentPreimage = s.processSenderAck(
	senderID, amount=senderAmount, paymentHash=paymentHash)

#Receiver:
s.processReceiverClaim(paymentPreimage)

print('After:')
print(s.users[senderID].balance)
print(s.users[receiverID].balance)

