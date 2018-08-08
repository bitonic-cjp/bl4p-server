import binascii

from api import bl4p_proto_pb2



def start(storage, userID, request):
	print('start called by userid: ', userID)
	result = bl4p_proto_pb2.BL4P_StartResult()
	result.sender_amount.amount = request.amount.amount
	result.receiver_amount.amount = request.amount.amount
	result.payment_hash.data = b'\x00' * 32
	return result

	#TODO: rework function
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


def send(storage, userID, request):
	#TODO: rework function
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


def receive(storage, userID, request):
	#TODO: rework function
	try:
		storage.processReceiverClaim(paymentPreimage=paymentpreimage)
		return {
			}

	except storage.TransactionNotFound:
		raise Exception('Transaction not found (incorrect preimage)')


def getStatus(storage, userID, request):
	#TODO: rework function
	try:
		status = storage.getTransactionStatus(userid=userid, paymentHash=paymenthash)
		return {
			'status': status
			}

	except storage.UserNotFound:
		raise Exception('User not found')
	except storage.TransactionNotFound:
		raise Exception('Transaction not found (incorrect user id or payment hash)')



def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(server, storage):
	functionData = \
	{
	bl4p_proto_pb2.BL4P_Start    : start,
	bl4p_proto_pb2.BL4P_Send     : send,
	bl4p_proto_pb2.BL4P_Receive  : receive,
	bl4p_proto_pb2.BL4P_GetStatus: getStatus,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, storage))

	#TODO:
	#server.registerTimeoutFunction(storage.processTimeouts)

