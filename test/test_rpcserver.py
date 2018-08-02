import sys
import threading
import time
import unittest
import urllib.request

sys.path.append('..')

import rpcserver
from api.bl4p import Bl4pApi



class ServerThread(threading.Thread):
	class StopServerThread(Exception):
		pass


	def __init__(self, server):
		threading.Thread.__init__(self)
		self.server = server

		def stopThread():
			if self.stopRequested:
				raise ServerThread.StopServerThread()

			return 0.1

		self.server.registerTimeoutFunction(stopThread)


	def start(self):
		self.stopRequested = False
		threading.Thread.start(self)


	def stop(self):
		self.stopRequested = True
		self.join()


	def run(self):
		try:
			self.server.run()
		except ServerThread.StopServerThread:
			pass



class TestRPCServer(unittest.TestCase):
	def setUp(self):
		self.server = rpcserver.RPCServer()
		self.serverThread = ServerThread(self.server)
		self.serverThread.start()

		self.callLog = []
		self.server.registerRPCFunction(
			'function',
			self.APIFunction,
			(('arg1', int), ('arg2', str))
			)

		self.client = Bl4pApi('http://localhost:8000/', '', '')


	def tearDown(self):
		self.serverThread.stop()
		self.server.server_close()


	def APIFunction(self, arg1, arg2):
		self.callLog.append((arg1, arg2))
		if arg2 == 'exception':
			raise Exception('Test exception')
		return {'ret1': arg1, 'ret2': arg2}


	def test_successfullCall(self):
		ret = self.client.apiCall('function', {'arg1': 3, 'arg2': 'foo'})
		self.assertEqual(ret, {'result': 'success', 'data': {'ret1': 3, 'ret2': 'foo'}})
		self.assertEqual(self.callLog, [(3, 'foo')])


	def test_exceptionCall(self):
		ret = self.client.apiCall('function', {'arg1': 3, 'arg2': 'exception'})
		self.assertEqual(ret, {'result': 'error', 'data': 'Test exception'})
		self.assertEqual(self.callLog, [(3, 'exception')])


	def test_nonExistingCall(self):
		with self.assertRaises(Exception, msg='unexpected response code: 404'):
			self.client.apiCall('doesNotExist', {})

		with self.assertRaises(Exception, msg='unexpected response code: 404'):
			self.client.apiCall('function/function', {})

		with self.assertRaises(Exception, msg='unexpected response code: 404'):
			self.client.apiCall('', {})


	def test_missingArgument(self):
		with self.assertRaises(Exception, msg='unexpected response code: 400'):
			self.client.apiCall('function', {})


	def test_argumentTypeError(self):
		with self.assertRaises(Exception, msg='unexpected response code: 400'):
			self.client.apiCall('function', {'arg1': 'bar', 'arg2': 'foo'})


	def test_timeouts(self):
		dt1 = None
		dt2 = None
		timesCalled = [0, 0]
		f2Called = 0
		def f1():
			timesCalled[0] += 1
			return dt1
		def f2():
			timesCalled[1] += 1
			return dt2

		#We want a clean server without a running thread:
		self.serverThread.stop()
		self.server.server_close()
		server = rpcserver.RPCServer()

		server.registerTimeoutFunction(f1)
		server.registerTimeoutFunction(f2)

		server.manageTimeouts()
		self.assertEqual(server.timeout, None)
		self.assertEqual(timesCalled, [1,1])

		dt1 = 1.0
		server.manageTimeouts()
		self.assertEqual(server.timeout, dt1)
		self.assertEqual(timesCalled, [2,2])

		dt2 = 2.0
		server.manageTimeouts()
		self.assertEqual(server.timeout, dt1)
		self.assertEqual(timesCalled, [3,3])

		dt1 = None
		server.manageTimeouts()
		self.assertEqual(server.timeout, dt2)
		self.assertEqual(timesCalled, [4,4])

		server.server_close()


	def test_landingPage(self):
		with urllib.request.urlopen('http://localhost:8000/') as f:
			page = f.read()
		self.assertTrue(b'function' in page)
		self.assertTrue(b'arg1' in page)
		self.assertTrue(b'arg2' in page)



if __name__ == '__main__':
	unittest.main(verbosity=2)

