from websocket_server.websocket_server import WebsocketServer



PORT=8000



class APIServer(WebsocketServer):
	def __init__(self):
		WebsocketServer.__init__(self, PORT)


	# Called for every client connecting (after handshake)
	def handle_new_client(self, client, server):
		print("New client connected and was given id %d" % client['id'])
		self.send_message_to_all("Hey all, a new client has joined us")


	# Called for every client disconnecting
	def handle_client_left(self, client, server):
		print("Client(%d) disconnected" % client['id'])


	# Called when a client sends a message
	def handle_message_received(self, client, server, message):
		if len(message) > 200:
			message = message[:200]+'..'
		print("Client(%d) said: %s" % (client['id'], message))


	def run(self):
		self.run_forever()


api = APIServer()
api.run()

