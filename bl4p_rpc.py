import binascii

from api import bl4p_proto_pb2


def error(reason):
	result = bl4p_proto_pb2.Error()
	result.reason = reason
	return result


def start(storage, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		senderAmount, receiverAmount, paymentHash = \
			storage.startTransaction(
				receiver_userid=userID,
				amount=request.amount.amount,
				timeDelta=request.sender_timeout_delta_ms / 1000.0,
				receiverPaysFee=request.receiver_pays_fee
				)
	except storage.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except storage.InsufficientAmount:
		return error(bl4p_proto_pb2._InvalidAmount)
	except storage.InvalidTimeDelta:
		return error(bl4p_proto_pb2._InvalidAmount)

	result = bl4p_proto_pb2.BL4P_StartResult()
	result.sender_amount.amount = senderAmount
	result.receiver_amount.amount = receiverAmount
	result.payment_hash.data = paymentHash
	return result


def send(storage, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		paymentPreimage = \
			storage.processSenderAck(
				sender_userid=userID,
				amount=request.sender_amount.amount,
				paymentHash=request.payment_hash.data
				)

	except storage.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except storage.TransactionNotFound:
		return error(bl4p_proto_pb2._NoSuchOrder)
	except storage.InsufficientFunds:
		return error(bl4p_proto_pb2._BalanceInsufficient)

	result = bl4p_proto_pb2.BL4P_SendResult()
	result.payment_preimage.data = paymentPreimage
	return result


def receive(storage, userID, request):
	try:
		storage.processReceiverClaim(
			paymentPreimage=request.payment_preimage.data
			)
	except storage.TransactionNotFound:
		return error(bl4p_proto_pb2._NoSuchOrder)

	result = bl4p_proto_pb2.BL4P_ReceiveResult()
	return result


def getStatus(storage, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		status = storage.getTransactionStatus(
			userid=userID,
			paymentHash=request.payment_hash.data)
	except storage.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except storage.TransactionNotFound:
		return error(bl4p_proto_pb2._NoSuchOrder)

	result = bl4p_proto_pb2.BL4P_GetStatusResult()
	result.status = \
	{
	'waiting_for_sender'  : bl4p_proto_pb2._waiting_for_sender,
	'waiting_for_receiver': bl4p_proto_pb2._waiting_for_receiver,
	'sender_timeout'      : bl4p_proto_pb2._sender_timeout,
	'receiver_timeout'    : bl4p_proto_pb2._receiver_timeout,
	'completed'           : bl4p_proto_pb2._completed,
	}[status]
	return result



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

	server.registerTimeoutFunction(storage.processTimeouts)

