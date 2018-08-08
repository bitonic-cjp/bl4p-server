import struct

from websocket_server.websocket_server import WebsocketServer

from api.serialization import serialize, deserialize


PORT=8000



class APIServer(WebsocketServer):
	def __init__(self):
		WebsocketServer.__init__(self, PORT)
		self.RPCFunctions = {}
		self.timeoutFunctions = []


	def registerRPCFunction(self, messageType, function):
		'''
		Registers an RPC function.

		:param messageType: the input message type.
		:param function: the function. May raise Exception.
		'''
		self.RPCFunctions[messageType] = function


	def registerTimeoutFunction(self, function):
		'''
		Registers a timeout function.

		Each time after a request is handled OR a time-out happens,
		every registered timeout function is called.
		The registered timeout functions must determine for themselves
		whether they need to do anything.
		Each returns either the time-delta to the next moment when it
		needs a time-out, or None if no such moment exists.
		The next time-out event corresponds with the lowest of the
		non-None values returned by the timeout functions.

		:param function: the function. Must return a timeout time-delta in seconds, or None.
		'''
		self.timeoutFunctions.append(function)


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

		try:
			function = self.RPCFunctions[request.__class__]
		except KeyError:
			print('Received unknown message type')
			#TODO: send back error

		#TODO: handle exceptions in function
		result = function(client['userid'], request)

		result.request = request.request
		client['handler'].send_binary(serialize(result))
		

	def run(self):
		while True:
			self.manageTimeouts()
			self.handle_request()


	def manageTimeouts(self):
		self.timeout = None
		for f in self.timeoutFunctions:
			t = f()
			if t is None:
				continue
			if self.timeout is None or t < self.timeout:
				self.timeout = t

