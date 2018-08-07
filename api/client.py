import struct

from websocket import WebSocket

import bl4p_proto_pb2



class Bl4pApi(WebSocket):
	def __init__(self, url, userid, password):
		WebSocket.__init__(self)
		self.connect(url)
		self.userid = userid
		self.password = password

		self.lastRequestID = 0


	def apiCall(self, requestTypeID, requestObj):
		requestObj.request = self.lastRequestID
		serialized = requestObj.SerializeToString()

		requestTypeID = struct.pack('<I', requestTypeID) #32-bit little endian

		self.send(requestTypeID + serialized)
		#TODO: receive reply

		self.lastRequestID += 1


	def start(self, amount, sender_timeout_delta_ms, receiver_pays_fee):
		requestObj = bl4p_proto_pb2.BL4P_Start()
		requestObj.amount.amount = amount
		requestObj.sender_timeout_delta_ms = sender_timeout_delta_ms
		requestObj.receiver_pays_fee = receiver_pays_fee
		return self.apiCall(bl4p_proto_pb2.Msg_BL4P_Start, requestObj)



api = Bl4pApi('ws://localhost:8000', '', '')
api.start(amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=True)
api.close()

