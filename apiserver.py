import asyncio

import websockets
import websockets.server

from api.serialization import serialize, deserialize



PORT=8000



class APIServer:
	def __init__(self):
		self.RPCFunctions = {}
		self.timeoutFunctions = []

		self.loop = asyncio.SelectorEventLoop()
		startServer = websockets.server.serve(
			self.handleMessages,
			'localhost', PORT
			)
		self.loop.run_until_complete(startServer)

		self.activeTimer = None


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


	@asyncio.coroutine
	def handleMessages(self, websocket, path):
		try:
			userID, password = websocket.request_headers['authorization'].split(':')
			if userID != password:
				raise Exception() #wrong password

			userID = int(userID)
		except:
			#Something went wrong, assume authentication failed
			#TODO: send error message
			userID = None

		while True:
			message = yield from websocket.recv()
			request = deserialize(message)

			try:
				function = self.RPCFunctions[request.__class__]
			except KeyError:
				print('Received unknown message type')
				#TODO: send back error


			#TODO: handle exceptions in function
			result = function(userID, request)

			#After a function call, time-outs may have changed:
			self.manageTimeouts()

			result.request = request.request
			yield from websocket.send(serialize(result))


	def run(self):
		#Initial time-outs set-up:
		self.manageTimeouts()
		self.loop.run_forever()


	def stop(self):
		self.loop.stop()


	def manageTimeouts(self):
		if self.activeTimer is not None:
			self.activeTimer.cancel()

		#Re-check at least once every 10 minutes
		nextTimeout = 600.0

		for f in self.timeoutFunctions:
			t = f()
			if t is None:
				continue
			if nextTimeout is None or t < nextTimeout:
				nextTimeout = t

		self.activeTimer = self.loop.call_later(
				nextTimeout, self.manageTimeouts
				)

