from websocket_server.websocket_server import WebsocketServer



PORT=8000



class APIServer:
	def __init__(self):
		self.server = WebsocketServer(PORT)
		self.server.set_fn_new_client(self.new_client)
		self.server.set_fn_client_left(self.client_left)
		self.server.set_fn_message_received(self.message_received)


	# Called for every client connecting (after handshake)
	def new_client(self, client, server):
		print("New client connected and was given id %d" % client['id'])
		self.server.send_message_to_all("Hey all, a new client has joined us")


	# Called for every client disconnecting
	def client_left(self, client, server):
		print("Client(%d) disconnected" % client['id'])


	# Called when a client sends a message
	def message_received(self, client, server, message):
		if len(message) > 200:
			message = message[:200]+'..'
		print("Client(%d) said: %s" % (client['id'], message))


	def run(self):
		self.server.run_forever()


api = APIServer()
api.run()

