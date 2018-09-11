import binascii

from api import bl4p_proto_pb2


def error(reason):
	result = bl4p_proto_pb2.Error()
	result.reason = reason
	return result


def start(bl4p, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		senderAmount, receiverAmount, paymentHash = \
			bl4p.startTransaction(
				receiver_userid=userID,
				amount=request.amount.amount,
				timeDelta=request.sender_timeout_delta_ms / 1000.0,
				receiverPaysFee=request.receiver_pays_fee
				)
	except bl4p.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except bl4p.InsufficientAmount:
		return error(bl4p_proto_pb2._InvalidAmount)
	except bl4p.InvalidTimeDelta:
		return error(bl4p_proto_pb2._InvalidAmount)

	result = bl4p_proto_pb2.BL4P_StartResult()
	result.sender_amount.amount = senderAmount
	result.receiver_amount.amount = receiverAmount
	result.payment_hash.data = paymentHash
	return result


def send(bl4p, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		paymentPreimage = \
			bl4p.processSenderAck(
				sender_userid=userID,
				amount=request.sender_amount.amount,
				paymentHash=request.payment_hash.data
				)

	except bl4p.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except bl4p.TransactionNotFound:
		return error(bl4p_proto_pb2._NoSuchOrder)
	except bl4p.InsufficientFunds:
		return error(bl4p_proto_pb2._BalanceInsufficient)

	result = bl4p_proto_pb2.BL4P_SendResult()
	result.payment_preimage.data = paymentPreimage
	return result


def receive(bl4p, userID, request):
	try:
		bl4p.processReceiverClaim(
			paymentPreimage=request.payment_preimage.data
			)
	except bl4p.TransactionNotFound:
		return error(bl4p_proto_pb2._NoSuchOrder)

	result = bl4p_proto_pb2.BL4P_ReceiveResult()
	return result


def getStatus(bl4p, userID, request):
	if userID is None:
		return error(bl4p_proto_pb2._Unauthorized)

	try:
		status = bl4p.getTransactionStatus(
			userid=userID,
			paymentHash=request.payment_hash.data)
	except bl4p.UserNotFound:
		return error(bl4p_proto_pb2._InvalidAccount)
	except bl4p.TransactionNotFound:
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


def registerRPC(server, bl4p):
	functionData = \
	{
	bl4p_proto_pb2.BL4P_Start    : start,
	bl4p_proto_pb2.BL4P_Send     : send,
	bl4p_proto_pb2.BL4P_Receive  : receive,
	bl4p_proto_pb2.BL4P_GetStatus: getStatus,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, bl4p))

	server.registerTimeoutFunction(bl4p.processTimeouts)

