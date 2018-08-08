import websocket

from . import bl4p_proto_pb2
from .serialization import serialize, deserialize



class Bl4pApi(websocket.WebSocket):
	def __init__(self, url, userid, password):
		websocket.WebSocket.__init__(self)

		header = \
		{
		'User-Agent': 'Python Bl4pApi',
		'Authorization': userid + ':' + password,
		}
		self.connect(url, header=header)
		self.userid = userid
		self.password = password

		self.lastRequestID = 0


	def apiCall(self, requestTypeID, requestObj):
		requestObj.request = self.lastRequestID
		self.send(serialize(requestObj), opcode=websocket.ABNF.OPCODE_BINARY)

		while True:
			result = deserialize(self.recv())
			if result.request != self.lastRequestID:
				#TODO: log a warning (we ignore a message)
				continue

			break

		self.lastRequestID += 1

		return result


	def start(self, amount, sender_timeout_delta_ms, receiver_pays_fee):
		requestObj = bl4p_proto_pb2.BL4P_Start()
		requestObj.amount.amount = amount
		requestObj.sender_timeout_delta_ms = sender_timeout_delta_ms
		requestObj.receiver_pays_fee = receiver_pays_fee
		return self.apiCall(bl4p_proto_pb2.Msg_BL4P_Start, requestObj)


api = Bl4pApi('ws://localhost:8000', '3', '3')

result = api.start(amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=True)
print(result)

api.close()

