import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append('..')

from api import bl4p_pb2
import bl4p_rpc



class MockServer:
	def __init__(self):
		self.RPCFunctions = {}
		self.timeoutFunctions = []


	def registerRPCFunction(self, requestType, function):
		self.RPCFunctions[requestType] = function


	def registerTimeoutFunction(self, function):
		self.timeoutFunctions.append(function)



class MockBL4P(Mock):
	class UserNotFound(Exception):
		pass

	class TransactionNotFound(Exception):
		pass


	class InsufficientAmount(Exception):
		pass


	class InvalidTimeout(Exception):
		pass


	class InsufficientFunds(Exception):
		pass


	class SignatureFailure(Exception):
		pass


	class MissingData(Exception):
		pass



class TestBL4PRPC(unittest.TestCase):

	@patch('bl4p_rpc.start'      , return_value=100)
	@patch('bl4p_rpc.cancelStart', return_value=101)
	@patch('bl4p_rpc.send'       , return_value=102)
	@patch('bl4p_rpc.receive'    , return_value=103)
	@patch('bl4p_rpc.getStatus'  , return_value=104)
	@patch('bl4p_rpc.selfReport' , return_value=105)
	def test_registerRPC(self, mock_selfReport, mock_getStatus, mock_receive, mock_send, mock_cancelStart, mock_start):
		mocks = \
		{
		bl4p_pb2.BL4P_Start      : mock_start,
		bl4p_pb2.BL4P_CancelStart: mock_cancelStart,
		bl4p_pb2.BL4P_Send       : mock_send,
		bl4p_pb2.BL4P_Receive    : mock_receive,
		bl4p_pb2.BL4P_GetStatus  : mock_getStatus,
		bl4p_pb2.BL4P_SelfReport : mock_selfReport,
		}

		server = MockServer()
		bl4p = Mock()

		bl4p_rpc.registerRPC(server, bl4p)

		self.assertEqual(len(server.RPCFunctions.keys()), len(mocks))

		#Test the functions passed to registerRPCFunction
		for requestType in mocks.keys():
			registeredFunction = server.RPCFunctions[requestType]
			ret = registeredFunction(1,2,3)
			for mockType, mock in mocks.items():
				if mockType == requestType:
					mock.assert_called_once_with(bl4p, 1, 2, 3)
					self.assertEqual(ret, mock.return_value)
				else:
					mock.assert_not_called()
				mock.reset_mock()

		self.assertEqual(server.timeoutFunctions, [bl4p.processTimeouts])


	def test_start(self):
		bl4p = MockBL4P()

		request = Mock()
		request.amount.amount = 5
		request.sender_timeout_delta_ms = 6
		request.locked_timeout_delta_s = 7
		request.receiver_pays_fee = 8

		#Successfull call
		bl4p.startTransaction = Mock(
			return_value=(100, 99, b'\x00\xff')
			)
		result = bl4p_rpc.start(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_StartResult))
		self.assertEqual(result.sender_amount.amount, 100)
		self.assertEqual(result.receiver_amount.amount, 99)
		self.assertEqual(result.payment_hash.data, b'\x00\xff')
		bl4p.startTransaction.assert_called_once_with(
			receiver_userid=4, amount=5, senderTimeout=6/1000.0, lockedTimeout=7, receiverPaysFee=8
			)

		#Exceptions
		for xc in [bl4p.UserNotFound(), bl4p.InsufficientAmount(), bl4p.InvalidTimeout()]:
			bl4p.startTransaction.reset_mock()
			bl4p.startTransaction.side_effect=xc
			result = bl4p_rpc.start(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		bl4p.startTransaction.reset_mock()
		result = bl4p_rpc.start(bl4p, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_cancelStart(self):
		bl4p = MockBL4P()

		request = Mock()
		request.payment_hash.data = 5

		#Successfull call
		bl4p.cancelTransaction = Mock()
		result = bl4p_rpc.cancelStart(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_CancelStartResult))
		bl4p.cancelTransaction.assert_called_once_with(
			receiver_userid=4,
			paymentHash=5
			)

		#Exceptions
		for xc in [bl4p.TransactionNotFound()]:
			bl4p.cancelTransaction.reset_mock()
			bl4p.cancelTransaction.side_effect=xc
			result = bl4p_rpc.cancelStart(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		bl4p.cancelTransaction.reset_mock()
		result = bl4p_rpc.cancelStart(bl4p, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_send(self):
		bl4p = MockBL4P()

		request = Mock()
		request.sender_amount.amount = 5
		request.payment_hash.data = 6
		request.max_locked_timeout_delta_s = 7
		request.report = 8
		request.signature = 9

		#Successfull call
		bl4p.processSenderAck = Mock(
			return_value=b'\x00\xff'
			)
		result = bl4p_rpc.send(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_SendResult))
		self.assertEqual(result.payment_preimage.data, b'\x00\xff')
		bl4p.processSenderAck.assert_called_once_with(
			sender_userid=4, amount=5, paymentHash=6, maxLockedTimeout=7,
			report=8, signature=9,
			)

		#Exceptions
		for xc in [bl4p.UserNotFound(), bl4p.TransactionNotFound(), bl4p.InsufficientFunds()]:
			bl4p.processSenderAck.reset_mock()
			bl4p.processSenderAck.side_effect=xc
			result = bl4p_rpc.send(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		bl4p.processSenderAck.reset_mock()
		result = bl4p_rpc.send(bl4p, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_receive(self):
		bl4p = MockBL4P()

		request = Mock()
		request.payment_preimage.data = 5

		#Successfull call
		bl4p.processReceiverClaim = Mock()
		result = bl4p_rpc.receive(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_ReceiveResult))
		bl4p.processReceiverClaim.assert_called_once_with(
			paymentPreimage=5
			)

		#Exceptions
		for xc in [bl4p.TransactionNotFound()]:
			bl4p.processReceiverClaim.reset_mock()
			bl4p.processReceiverClaim.side_effect=xc
			result = bl4p_rpc.receive(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_getStatus(self):
		bl4p = MockBL4P()

		request = Mock()
		request.payment_hash.data = 5

		#Successfull call
		bl4p.getTransactionStatus = Mock(
			return_value='completed'
			)
		result = bl4p_rpc.getStatus(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_GetStatusResult))
		self.assertEqual(result.status, bl4p_pb2._completed)
		bl4p.getTransactionStatus.assert_called_once_with(
			userid=4, paymentHash=5
			)

		#Exceptions
		for xc in [bl4p.UserNotFound(), bl4p.TransactionNotFound()]:
			bl4p.getTransactionStatus.reset_mock()
			bl4p.getTransactionStatus.side_effect=xc
			result = bl4p_rpc.getStatus(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		bl4p.getTransactionStatus.reset_mock()
		result = bl4p_rpc.getStatus(bl4p, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_selfReport(self):
		bl4p = MockBL4P()

		request = Mock()
		request.report = b'foo'
		request.signature = b'bar'

		#Successfull call
		bl4p.processSelfReport = Mock()
		result = bl4p_rpc.selfReport(bl4p, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_SelfReportResult))
		bl4p.processSelfReport.assert_called_once_with(
			receiver_userid=4, report=b'foo', signature=b'bar'
			)

		#Exceptions
		for xc in [bl4p.TransactionNotFound(), bl4p.SignatureFailure(), bl4p.MissingData()]:
			bl4p.processSelfReport.reset_mock()
			bl4p.processSelfReport.side_effect=xc
			result = bl4p_rpc.selfReport(bl4p, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		bl4p.getTransactionStatus.reset_mock()
		result = bl4p_rpc.selfReport(bl4p, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))



if __name__ == '__main__':
	unittest.main(verbosity=2)

