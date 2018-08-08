import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append('..')

from api import bl4p_proto_pb2
import bl4p_rpc



class MockServer:
	def __init__(self):
		self.RPCFunctions = {}
		self.timeoutFunctions = []


	def registerRPCFunction(self, requestType, function):
		self.RPCFunctions[requestType] = function


	def registerTimeoutFunction(self, function):
		self.timeoutFunctions.append(function)



class MockStorage(Mock):
	class UserNotFound(Exception):
		pass

	class TransactionNotFound(Exception):
		pass


	class InsufficientAmount(Exception):
		pass


	class InvalidTimeDelta(Exception):
		pass


	class InsufficientFunds(Exception):
		pass



class TestBL4PRPC(unittest.TestCase):

	@patch('bl4p_rpc.start'    , return_value=100)
	@patch('bl4p_rpc.send'     , return_value=101)
	@patch('bl4p_rpc.receive'  , return_value=102)
	@patch('bl4p_rpc.getStatus', return_value=103)
	def test_registerRPC(self, mock_getStatus, mock_receive, mock_send, mock_start):
		mocks = \
		{
		bl4p_proto_pb2.BL4P_Start    : mock_start,
		bl4p_proto_pb2.BL4P_Send     : mock_send,
		bl4p_proto_pb2.BL4P_Receive  : mock_receive,
		bl4p_proto_pb2.BL4P_GetStatus: mock_getStatus,
		}

		server = MockServer()
		storage = Mock()

		bl4p_rpc.registerRPC(server, storage)

		self.assertEqual(len(server.RPCFunctions.keys()), len(mocks))

		#Test the functions passed to registerRPCFunction
		for requestType in mocks.keys():
			registeredFunction = server.RPCFunctions[requestType]
			ret = registeredFunction(1,2,3)
			for mockType, mock in mocks.items():
				if mockType == requestType:
					mock.assert_called_once_with(storage, 1, 2, 3)
					self.assertEqual(ret, mock.return_value)
				else:
					mock.assert_not_called()
				mock.reset_mock()

		#TODO
		#self.assertEqual(server.timeoutFunctions, [storage.processTimeouts])


	def test_start(self):
		storage = MockStorage()

		request = Mock()
		request.amount.amount = 5
		request.sender_timeout_delta_ms = 6
		request.receiver_pays_fee = 7

		#Successfull call
		storage.startTransaction = Mock(
			return_value=(100, 99, b'\x00\xff')
			)
		result = bl4p_rpc.start(storage, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_proto_pb2.BL4P_StartResult))
		self.assertEqual(result.sender_amount.amount, 100)
		self.assertEqual(result.receiver_amount.amount, 99)
		self.assertEqual(result.payment_hash.data, b'\x00\xff')
		storage.startTransaction.assert_called_once_with(
			receiver_userid=4, amount=5, timeDelta=6/1000.0, receiverPaysFee=7
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.InsufficientAmount(), storage.InvalidTimeDelta()]:
			storage.startTransaction.reset_mock()
			storage.startTransaction.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.start(storage, userID=4, request=request)


	def test_send(self):
		storage = MockStorage()

		request = Mock()
		request.sender_amount.amount = 5
		request.payment_hash.data = 6

		#Successfull call
		storage.processSenderAck = Mock(
			return_value=b'\x00\xff'
			)
		result = bl4p_rpc.send(storage, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_proto_pb2.BL4P_SendResult))
		self.assertEqual(result.payment_preimage.data, b'\x00\xff')
		storage.processSenderAck.assert_called_once_with(
			sender_userid=4, amount=5, paymentHash=6
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound(), storage.InsufficientFunds()]:
			storage.processSenderAck.reset_mock()
			storage.processSenderAck.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.send(storage, userID=4, request=request)


	def test_receive(self):
		storage = MockStorage()

		request = Mock()
		request.payment_preimage.data = 5

		#Successfull call
		storage.processReceiverClaim = Mock()
		result = bl4p_rpc.receive(storage, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_proto_pb2.BL4P_ReceiveResult))
		storage.processReceiverClaim.assert_called_once_with(
			paymentPreimage=5
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound()]:
			storage.processReceiverClaim.reset_mock()
			storage.processReceiverClaim.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.receive(storage, request=request)


	def test_getStatus(self):
		storage = MockStorage()

		request = Mock()
		request.payment_hash.data = 5

		#Successfull call
		storage.getTransactionStatus = Mock(
			return_value='completed'
			)
		result = bl4p_rpc.getStatus(storage, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_proto_pb2.BL4P_GetStatusResult))
		self.assertEqual(result.status, bl4p_proto_pb2._completed)
		storage.getTransactionStatus.assert_called_once_with(
			userid=4, paymentHash=5
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound()]:
			storage.getTransactionStatus.reset_mock()
			storage.getTransactionStatus.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.getstatus(storage, userid=4, request=request)



if __name__ == '__main__':
	unittest.main(verbosity=2)

