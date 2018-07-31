import sys
import threading
import unittest
import urllib.request

sys.path.append('..')

import rpcserver
from api.bl4p import Bl4pApi



class ServerThread(threading.Thread):
	def __init__(self, server):
		threading.Thread.__init__(self)
		self.server = server
		self.server.timeout = 0.1


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


	def test_landingPage(self):
		with urllib.request.urlopen('http://localhost:8000/') as f:
			page = f.read()
		self.assertTrue(b'function' in page)
		self.assertTrue(b'arg1' in page)
		self.assertTrue(b'arg2' in page)



if __name__ == '__main__':
	unittest.main(verbosity=2)

