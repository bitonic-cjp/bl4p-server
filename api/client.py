import struct

import websocket

import bl4p_proto_pb2



class Bl4pApi(websocket.WebSocket):
	def __init__(self, url, userid, password):
		websocket.WebSocket.__init__(self)
		self.connect(url)
		self.userid = userid
		self.password = password

		self.lastRequestID = 0


	def apiCall(self, requestTypeID, requestObj):
		requestObj.request = self.lastRequestID
		serialized = requestObj.SerializeToString()

		requestTypeID = struct.pack('<I', requestTypeID) #32-bit little endian

		self.send(requestTypeID + serialized, opcode=websocket.ABNF.OPCODE_BINARY)

		while True:
			message = self.recv()
			resultTypeID = struct.unpack('<I', message[:4])[0] #32-bit little endian
			if resultTypeID == bl4p_proto_pb2.Msg_BL4P_StartResult:
				result = bl4p_proto_pb2.BL4P_StartResult()
				result.ParseFromString(message[4:])
			else:
				print('Received unknown message type ', requestTypeID)
				#TODO: send back error
				break
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



api = Bl4pApi('ws://localhost:8000', '', '')

result = api.start(amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=True)
print(result)

api.close()

