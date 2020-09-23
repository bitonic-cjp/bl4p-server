import asyncio
import logging
import traceback

import websockets

from api.serialization import serialize, deserialize
from api import bl4p_pb2



PORT=8000



class RPCServer:
	def __init__(self):
		self.RPCFunctions = {}
		self.timeoutFunctions = []

		self.loop = asyncio.SelectorEventLoop()

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

		try:
			while True:
				message = yield from websocket.recv()
				request = deserialize(message)

				try:
					function = self.RPCFunctions[request.__class__]
				except KeyError:
					logging.warning('Received unsupported request type')
					result = bl4p_pb2.Error()
					result.reason = bl4p_pb2.Err_MalformedRequest
				else:
					try:
						result = function(userID, request)
					except Exception as e:
						logging.error('Something unexpected went wrong: ' + str(e))
						logging.error(traceback.format_exc())
						result = bl4p_pb2.Error()
						result.reason = bl4p_pb2.Err_Unknown

					#After a function call, time-outs may have changed:
					self.manageTimeouts()

				result.request = request.request
				yield from websocket.send(serialize(result))
		except websockets.ConnectionClosed:
			#Accept a connection close at any time.
			#Our response is just to silently break the loop.
			pass



	def run(self):
		#Initial time-outs set-up:
		self.manageTimeouts()

		startServer = websockets.serve(
			self.handleMessages,
			'localhost', PORT,
			loop = self.loop,
			)
		self.server = self.loop.run_until_complete(startServer)
		self.stopFuture = self.loop.create_future()
		#self.loop.run_forever()
		self.loop.run_until_complete(self.stopFuture)
		self.server.close()
		self.loop.run_until_complete(self.server.wait_closed())
		self.loop.close()


	def close(self):
		#Only set the future if it hasn't been set yet:
		try:
			self.stopFuture.result()
		except asyncio.exceptions.InvalidStateError:
			self.stopFuture.set_result(True)


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

