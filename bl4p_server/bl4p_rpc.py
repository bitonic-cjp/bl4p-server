import binascii

from .api import bl4p_pb2


def error(reason):
	result = bl4p_pb2.Error()
	result.reason = reason
	return result


def start(bl4p, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		senderAmount, receiverAmount, paymentHash = \
			bl4p.startTransaction(
				receiver_userid=userID,
				amount=request.amount.amount,
				senderTimeout=request.sender_timeout_delta_ms / 1000.0,
				lockedTimeout=request.locked_timeout_delta_s,
				receiverPaysFee=request.receiver_pays_fee
				)
	except bl4p.UserNotFound:
		return error(bl4p_pb2.Err_InvalidAccount)
	except bl4p.InsufficientAmount:
		return error(bl4p_pb2.Err_InvalidAmount)
	except bl4p.InvalidTimeout:
		return error(bl4p_pb2.Err_InvalidAmount)

	result = bl4p_pb2.BL4P_StartResult()
	result.sender_amount.amount = senderAmount
	result.receiver_amount.amount = receiverAmount
	result.payment_hash.data = paymentHash
	return result


def selfReport(bl4p, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		bl4p.processSelfReport(
			receiver_userid=userID,
			report=request.report,
			signature=request.signature)
	except bl4p.UserNotFound:
		return error(bl4p_pb2.Err_InvalidAccount)
	except bl4p.SignatureFailure:
		return error(bl4p_pb2.Err_Unauthorized)
	except bl4p.TransactionNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)
	except bl4p.MissingData:
		return error(bl4p_pb2.Err_MalformedRequest)

	result = bl4p_pb2.BL4P_SelfReportResult()
	return result


def cancelStart(bl4p, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		bl4p.cancelTransaction(
			receiver_userid=userID,
			paymentHash=request.payment_hash.data
			)
	except bl4p.TransactionNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)

	result = bl4p_pb2.BL4P_CancelStartResult()
	return result


def send(bl4p, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		paymentPreimage = \
			bl4p.processSenderAck(
				sender_userid=userID,
				amount=request.sender_amount.amount,
				paymentHash=request.payment_hash.data,
				maxLockedTimeout=request.max_locked_timeout_delta_s,

				report=request.report,
				signature=request.signature,
				)

	except bl4p.UserNotFound:
		return error(bl4p_pb2.Err_InvalidAccount)
	except bl4p.SignatureFailure:
		return error(bl4p_pb2.Err_Unauthorized)
	except bl4p.TransactionNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)
	except bl4p.InsufficientFunds:
		return error(bl4p_pb2.Err_BalanceInsufficient)
	except bl4p.MissingData:
		return error(bl4p_pb2.Err_MalformedRequest)

	result = bl4p_pb2.BL4P_SendResult()
	result.payment_preimage.data = paymentPreimage
	return result


def receive(bl4p, userID, request):
	try:
		bl4p.processReceiverClaim(
			paymentPreimage=request.payment_preimage.data
			)
	except bl4p.TransactionNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)

	result = bl4p_pb2.BL4P_ReceiveResult()
	return result


def getStatus(bl4p, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		status = bl4p.getTransactionStatus(
			userid=userID,
			paymentHash=request.payment_hash.data)
	except bl4p.UserNotFound:
		return error(bl4p_pb2.Err_InvalidAccount)
	except bl4p.TransactionNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)

	result = bl4p_pb2.BL4P_GetStatusResult()
	result.status = \
	{
	'waiting_for_selfreport': bl4p_pb2._waiting_for_selfreport,
	'waiting_for_sender'    : bl4p_pb2._waiting_for_sender,
	'waiting_for_receiver'  : bl4p_pb2._waiting_for_receiver,
	'sender_timeout'        : bl4p_pb2._sender_timeout,
	'receiver_timeout'      : bl4p_pb2._receiver_timeout,
	'completed'             : bl4p_pb2._completed,
	'canceled'              : bl4p_pb2._canceled,
	}[status]
	return result


def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(server, bl4p):
	functionData = \
	{
	bl4p_pb2.BL4P_Start      : start,
	bl4p_pb2.BL4P_CancelStart: cancelStart,
	bl4p_pb2.BL4P_Send       : send,
	bl4p_pb2.BL4P_Receive    : receive,
	bl4p_pb2.BL4P_GetStatus  : getStatus,
	bl4p_pb2.BL4P_SelfReport : selfReport,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, bl4p))

	server.registerTimeoutFunction(bl4p.processTimeouts)

