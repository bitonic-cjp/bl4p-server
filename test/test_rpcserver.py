import sys
import threading
import unittest

sys.path.append('..')

import rpcserver
from api.bl4p import Bl4pApi



class ServerThread(threading.Thread):
	def __init__(self, server):
		threading.Thread.__init__(self)
		self.server = server
		self.server.timeout = 1.0


	def start(self):
		self.stopRequested = False
		threading.Thread.start(self)


	def stop(self):
		self.stopRequested = True
		self.join()


	def run(self):
		while not self.stopRequested:
			self.server.handle_request()



class TestRPCServer(unittest.TestCase):
	def setUp(self):
		self.server = rpcserver.RPCServer()
		self.serverThread = ServerThread(self.server)
		self.serverThread.start()

		self.client = Bl4pApi('http://localhost:8000/', '', '')


	def tearDown(self):
		self.serverThread.stop()
		self.server.server_close()


	def test_successfullCall(self):
		callLog = []
		def simpleFunc(arg):
			callLog.append(arg)
			return arg

		self.server.registerRPCFunction('simpleFunc', simpleFunc, [('arg', int)])

		ret = self.client.apiCall('simpleFunc', {'arg': 3})
		self.assertEqual(ret, {'result': 'success', 'data': 3})
		self.assertEqual(callLog, [3])



if __name__ == '__main__':
	unittest.main(verbosity=2)

