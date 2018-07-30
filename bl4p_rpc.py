import binascii

def start(storage, userid, amount, timedelta, receiverpaysfee):
	try:
		senderAmount, receiverAmount, paymentHash = \
			storage.startTransaction(
				receiver_userid=userid,
				amount=amount,
				timeDelta=timedelta,
				receiverPaysFee=receiverpaysfee
				)
		paymentHash = binascii.hexlify(paymentHash).decode()
		return {
			'senderamount': senderAmount,
			'receiveramount': receiverAmount,
			'paymenthash': paymentHash
			}

	except storage.UserNotFound:
		raise Exception('User not found')
	except storage.InsufficientAmount:
		raise Exception('Insufficient amount (must be positive after subtraction of fees)')
	except storage.InvalidTimeDelta:
		raise Exception('Invalid (non-positive) timedelta')


def send(storage, userid, amount, paymenthash):
	try:
		paymenthash = binascii.unhexlify(paymenthash.encode())
	except Exception as e:
		print(e)
		raise Exception('Invalid payment hash (failed to decode as hex string)')

	try:
		paymentPreimage = \
			storage.processSenderAck(
				sender_userid=userid,
				amount=amount,
				paymentHash=paymenthash
				)
		paymentPreimage = binascii.hexlify(paymentPreimage).decode()
		return {
			'paymentpreimage': paymentPreimage
			}

	except storage.UserNotFound:
		raise Exception('User not found')
	except storage.TransactionNotFound:
		raise Exception('Transaction not found (incorrect amount or payment hash)')
	except storage.InsufficientFunds:
		raise Exception('Insufficient funds')


def receive(storage, paymentpreimage):
	try:
		paymentpreimage = binascii.unhexlify(paymentpreimage.encode())
	except Exception as e:
		print(e)
		raise Exception('Invalid payment preimage (failed to decode as hex string)')

	try:
		storage.processReceiverClaim(paymentpreimage)
		return {
			}

	except storage.TransactionNotFound:
		raise Exception('Transaction not found (incorrect preimage)')


def getstatus(storage, userid, paymenthash):
	try:
		paymenthash = binascii.unhexlify(paymenthash.encode())
	except Exception as e:
		print(e)
		raise Exception('Invalid payment hash (failed to decode as hex string)')

	return {
		}


def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(RPCServer, storage):
	functionData = \
	{
	'start':     (start    , (('userid', int), ('amount', int), ('timedelta', float), ('receiverpaysfee', bool))),
	'send':      (send     , (('userid', int), ('amount', int), ('paymenthash', str))),
	'receive':   (receive  , (('paymentpreimage', str), )),
	'getstatus': (getstatus, (('userid', int), ('paymenthash', str))),
	}

	for name, data in functionData.items():
		function, argsDef = data
		function = makeClosure(function, storage)
		RPCServer.registerRPCFunction(name, function, argsDef)

