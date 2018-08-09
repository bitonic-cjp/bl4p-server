import sys
import threading
import time
import unittest
from unittest.mock import Mock

sys.path.append('..')

import apiserver
from api.client import Bl4pApi
from api import bl4p_proto_pb2



class ServerThread(threading.Thread):
	def __init__(self, server):
		threading.Thread.__init__(self)
		self.server = server

		def stopThread():
			if self.stopRequested:
				self.server.close()

			return 0.1

		self.server.registerTimeoutFunction(stopThread)


	def start(self):
		self.stopRequested = False
		threading.Thread.start(self)


	def stop(self):
		self.stopRequested = True
		self.join()


	def run(self):
		self.server.run()



class TestRPCServer(unittest.TestCase):
	def setUp(self):
		self.server = apiserver.APIServer()
		self.serverThread = ServerThread(self.server)
		self.serverThread.start()
		time.sleep(0.1)

		self.callLog = []
		self.server.registerRPCFunction(
			bl4p_proto_pb2.BL4P_Start,
			self.APIFunction
			)

		self.client = Bl4pApi('ws://localhost:8000/', '3', '3')


	def tearDown(self):
		self.client.close()
		self.serverThread.stop()


	def APIFunction(self, userID, request):
		self.callLog.append((userID, request))
		ret = bl4p_proto_pb2.BL4P_StartResult()
		ret.payment_hash.data = b'\x00\xff'
		return ret


	def test_successfullCall(self):
		senderAmount, receiverAmount, paymentHash = self.client.start(
			amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=False)

		self.assertEqual(paymentHash, b'\x00\xff')

		self.assertEqual(len(self.callLog), 1)
		userID, request = self.callLog[0]
		self.assertEqual(userID, 3)
		self.assertEqual(request.amount.amount, 100)


	def test_incorrectPassword(self):
		self.client.close()
		self.client = Bl4pApi('ws://localhost:8000/', '3', 'wrong')

		senderAmount, receiverAmount, paymentHash = self.client.start(
			amount=100, sender_timeout_delta_ms=5000, receiver_pays_fee=False)

		self.assertEqual(paymentHash, b'\x00\xff')

		self.assertEqual(len(self.callLog), 1)
		userID, request = self.callLog[0]
		self.assertEqual(userID, None)
		self.assertEqual(request.amount.amount, 100)


	def test_nonExistingCall(self):
		with self.assertRaises(Bl4pApi.Error):
			self.client.getStatus(payment_hash=b'foobar')


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
		server = apiserver.APIServer()

		server.loop = Mock()

		server.registerTimeoutFunction(f1)
		server.registerTimeoutFunction(f2)

		server.manageTimeouts()
		server.loop.call_later.assert_called_once_with(600.0, server.manageTimeouts)
		self.assertEqual(timesCalled, [1,1])
		server.loop.call_later.reset_mock()

		dt1 = 1.0
		server.manageTimeouts()
		server.loop.call_later.assert_called_once_with(dt1, server.manageTimeouts)
		self.assertEqual(timesCalled, [2,2])
		server.loop.call_later.reset_mock()

		dt2 = 2.0
		server.manageTimeouts()
		server.loop.call_later.assert_called_once_with(dt1, server.manageTimeouts)
		self.assertEqual(timesCalled, [3,3])
		server.loop.call_later.reset_mock()

		dt1 = None
		server.manageTimeouts()
		server.loop.call_later.assert_called_once_with(dt2, server.manageTimeouts)
		self.assertEqual(timesCalled, [4,4])



if __name__ == '__main__':
	unittest.main(verbosity=2)

