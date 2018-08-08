import websocket

from . import bl4p_proto_pb2
from .serialization import serialize, deserialize



class Bl4pApi:
	def __init__(self, url, userid, password):
		self.websocket = websocket.WebSocket()

		header = \
		{
		'User-Agent': 'Python Bl4pApi',
		'Authorization': userid + ':' + password,
		}
		self.websocket.connect(url, header=header)
		self.lastRequestID = 0


	def close(self):
		self.websocket.close()


	def apiCall(self, request):
		request.request = self.lastRequestID
		self.websocket.send(serialize(request), opcode=websocket.ABNF.OPCODE_BINARY)

		while True:
			result = deserialize(self.websocket.recv())
			if result.request != self.lastRequestID:
				#TODO: log a warning (we ignore a message)
				continue

			break

		self.lastRequestID += 1

		return result


	def start(self, amount, sender_timeout_delta_ms, receiver_pays_fee):
		request = bl4p_proto_pb2.BL4P_Start()
		request.amount.amount = amount
		request.sender_timeout_delta_ms = sender_timeout_delta_ms
		request.receiver_pays_fee = receiver_pays_fee
		result = self.apiCall(request)
		return result.sender_amount.amount, result.receiver_amount.amount, result.payment_hash.data


	def send(self, amount, payment_hash):
		request = bl4p_proto_pb2.BL4P_Send()
		request.sender_amount.amount = amount
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return result.payment_preimage.data


	def receive(self, payment_preimage):
		request = bl4p_proto_pb2.BL4P_Receive()
		request.payment_preimage.data = payment_preimage
		self.apiCall(request)


	def getStatus(self, payment_hash):
		request = bl4p_proto_pb2.BL4P_GetStatus()
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return \
		{
		bl4p_proto_pb2._waiting_for_sender  : 'waiting_for_sender',
		bl4p_proto_pb2._waiting_for_receiver: 'waiting_for_receiver',
		bl4p_proto_pb2._sender_timeout      : 'sender_timeout',
		bl4p_proto_pb2._receiver_timeout    : 'receiver_timeout',
		bl4p_proto_pb2._completed           : 'completed',
		}[result.status]



api = Bl4pApi('ws://localhost:8000', '3', '3')

senderAmount, receiverAmount, paymentHash = api.start(amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=True)
print(senderAmount, receiverAmount, paymentHash)

paymentPreimage = api.send(amount=senderAmount, payment_hash=paymentHash)
print(paymentPreimage)

api.receive(payment_preimage=paymentPreimage)

status = api.getStatus(payment_hash=paymentHash)
print(status)

api.close()

