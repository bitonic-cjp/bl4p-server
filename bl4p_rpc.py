import binascii



# RPC functions:

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
		storage.processReceiverClaim(paymentpreimage)
		return {
			}

	except storage.TransactionNotFound:
		raise Exception('Transaction not found (incorrect preimage)')


def getstatus(storage, userid, paymenthash):
	return {
		}


#Argument type constructors:

def hex2binary(s):
	try:
		return binascii.unhexlify(s.encode())
	except Exception as e:
		raise ValueError(str(e))


def str2bool(s):
	try:
		return {'true': True, 'false': False}[s.lower()]
	except Exception:
		raise ValueError()




def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(RPCServer, storage):
	functionData = \
	{
	'start':     (start    , (('userid', int), ('amount', int), ('timedelta', float), ('receiverpaysfee', str2bool))),
	'send':      (send     , (('userid', int), ('amount', int), ('paymenthash', hex2binary))),
	'receive':   (receive  , (('paymentpreimage', hex2binary), )),
	'getstatus': (getstatus, (('userid', int), ('paymenthash', hex2binary))),
	}

	for name, data in functionData.items():
		function, argsDef = data
		function = makeClosure(function, storage)
		RPCServer.registerRPCFunction(name, function, argsDef)

