import struct

from websocket_server.websocket_server import WebsocketServer

from api import bl4p_proto_pb2
from api.serialization import serialize, deserialize


PORT=8000



class APIServer(WebsocketServer):
	def __init__(self):
		WebsocketServer.__init__(self, PORT)


	# Called for every client connecting (after handshake)
	def handle_new_client(self, client, server):
		try:
			userid, password = client['headers']['authorization'].split(':')
			if userid != password:
				raise Exception() #wrong password
			client['userid'] = int(userid)
		except:
			#Something went wrong, assume authentication failed
			#TODO: send error message
			client['userid'] = None
		print("Client connected: userid ", client['userid'])


	# Called for every client disconnecting
	def handle_client_left(self, client, server):
		print("Client disconnected: userid ", client['userid'])


	# Called when a client sends a message
	def handle_message_received(self, client, server, message):
		request = deserialize(message)

		if isinstance(request, bl4p_proto_pb2.BL4P_Start):
			result = bl4p_proto_pb2.BL4P_StartResult()
			result.sender_amount.amount = request.amount.amount
			result.receiver_amount.amount = request.amount.amount
			result.payment_hash.data = b'\x00' * 32
		else:
			print('Received unknown message type')
			#TODO: send back error

		result.request = request.request
		client['handler'].send_binary(serialize(result))
		

	def run(self):
		self.run_forever()



api = APIServer()
api.run()

