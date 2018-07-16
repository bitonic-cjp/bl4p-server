#!/usr/bin/env python3

import storage

receiverID = 3
senderID = 6

s = storage.Storage()
s.users[receiverID] = storage.User(id=receiverID, balance=200)
s.users[senderID] = storage.User(id=senderID, balance=500)

print('Before:')
print(s.users[senderID].balance)
print(s.users[receiverID].balance)

#Receiver:
paymentHash = s.startTransaction(receiverID, amount=100, timeDelta=5)

#Sender:
paymentPreimage = s.processSenderAck(senderID, amount=100, paymentHash=paymentHash)

#Receiver:
s.processReceiverClaim(paymentPreimage)

print('After:')
print(s.users[senderID].balance)
print(s.users[receiverID].balance)

