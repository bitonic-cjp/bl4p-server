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
			}, True

	except storage.UserNotFound:
		return 'User not found', False
	except storage.InsufficientAmount:
		return 'Insufficient amount (must be positive after subtraction of fees)', False
	except storage.InvalidTimeDelta:
		return 'Invalid (non-positive) timedelta', False


def send(storage, userid, amount, paymenthash):
	try:
		paymenthash = binascii.unhexlify(paymenthash.encode())
	except Exception as e:
		print(e)
		return 'Invalid payment hash (failed to decode as hex string)', False
		return

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
			}, True

	except storage.UserNotFound:
		return 'User not found', False
	except storage.TransactionNotFound:
		return 'Transaction not found (incorrect amount or payment hash)', False
	except storage.InsufficientFunds:
		return 'Insufficient funds', False


def receive(storage, paymentpreimage):
	try:
		paymentpreimage = binascii.unhexlify(paymentpreimage.encode())
	except Exception as e:
		print(e)
		return 'Invalid payment preimage (failed to decode as hex string)', False
		return

	try:
		storage.processReceiverClaim(paymentpreimage)
		return {
			}, True

	except storage.TransactionNotFound:
		return 'Transaction not found (incorrect preimage)', False


def getstatus(storage, userid, paymenthash):
	try:
		paymenthash = binascii.unhexlify(paymenthash.encode())
	except Exception as e:
		print(e)
		return 'Invalid payment hash (failed to decode as hex string)', False
		return

	return {
		}, True


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

