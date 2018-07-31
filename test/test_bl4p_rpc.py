import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append('..')

import bl4p_rpc



class MockRPCServer:
	def __init__(self):
		self.RPCFunctions = {}


	def registerRPCFunction(self, name, function, argsDef):
		self.RPCFunctions[name] = function, argsDef


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
	@patch('bl4p_rpc.getstatus', return_value=103)
	def test_registerRPC(self, mock_getstatus, mock_receive, mock_send, mock_start):
		mocks = \
		{
		'start'    : mock_start,
		'send'     : mock_send,
		'receive'  : mock_receive,
		'getstatus': mock_getstatus,
		}

		server = MockRPCServer()
		storage = 'foo'

		bl4p_rpc.registerRPC(server, storage)

		self.assertEqual(len(server.RPCFunctions.keys()), len(mocks))

		#Test the functions passed to registerRPCFunction
		for name in mocks.keys():
			registeredFunction = server.RPCFunctions[name][0]
			ret = registeredFunction(1,2,3)
			for mockname, mock in mocks.items():
				if mockname == name:
					mock.assert_called_once_with(storage, 1, 2, 3)
					self.assertEqual(ret, mock.return_value)
				else:
					mock.assert_not_called()
				mock.reset_mock()

		#Test the argsDef passed to registerRPCFunction
		self.assertEqual(server.RPCFunctions['start'][1],
			(('userid', int), ('amount', int), ('timedelta', float), ('receiverpaysfee', bl4p_rpc.str2bool))
			)
		self.assertEqual(server.RPCFunctions['send'][1],
			(('userid', int), ('amount', int), ('paymenthash', bl4p_rpc.hex2binary))
			)
		self.assertEqual(server.RPCFunctions['receive'][1],
			(('paymentpreimage', bl4p_rpc.hex2binary), )
			)
		self.assertEqual(server.RPCFunctions['getstatus'][1],
			(('userid', int), ('paymenthash', bl4p_rpc.hex2binary))
			)


	def test_str2bool(self):
		self.assertEqual(bl4p_rpc.str2bool('True'), True)
		self.assertEqual(bl4p_rpc.str2bool('TRUE'), True)
		self.assertEqual(bl4p_rpc.str2bool('true'), True)

		self.assertEqual(bl4p_rpc.str2bool('False'), False)
		self.assertEqual(bl4p_rpc.str2bool('FALSE'), False)
		self.assertEqual(bl4p_rpc.str2bool('false'), False)

		for s in ['', '0', '1', 'foo']:
			with self.assertRaises(ValueError):
				bl4p_rpc.str2bool(s)


	def test_hex2binary(self):
		self.assertEqual(bl4p_rpc.hex2binary(''), b'')
		self.assertEqual(bl4p_rpc.hex2binary('00'), b'\x00')
		self.assertEqual(bl4p_rpc.hex2binary('01'), b'\x01')
		self.assertEqual(bl4p_rpc.hex2binary('ff'), b'\xff')
		self.assertEqual(bl4p_rpc.hex2binary('1234'), b'\x12\x34')
		self.assertEqual(bl4p_rpc.hex2binary('0123456789abcdef'), b'\x01\x23\x45\x67\x89\xab\xcd\xef')

		for s in ['0', 'aaa', 'x0', '00x']:
			with self.assertRaises(ValueError):
				bl4p_rpc.hex2binary(s)


	def test_start(self):
		storage = MockStorage()

		#Successfull call
		storage.startTransaction = Mock(
			return_value=(100, 99, b'\x00\xff')
			)
		ret = bl4p_rpc.start(storage, userid=4, amount=5, timedelta=6, receiverpaysfee=7)
		self.assertEqual(ret,
			{'senderamount': 100, 'receiveramount': 99, 'paymenthash': '00ff'}
			)
		storage.startTransaction.assert_called_once_with(
			receiver_userid=4, amount=5, timeDelta=6, receiverPaysFee=7
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.InsufficientAmount(), storage.InvalidTimeDelta()]:
			storage.startTransaction.reset_mock()
			storage.startTransaction.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.start(storage, userid=4, amount=5, timedelta=6, receiverpaysfee=7)


	def test_send(self):
		storage = MockStorage()

		#Successfull call
		storage.processSenderAck = Mock(
			return_value=b'\x00\xff'
			)
		ret = bl4p_rpc.send(storage, userid=4, amount=5, paymenthash=6)
		self.assertEqual(ret,
			{'paymentpreimage': '00ff'}
			)
		storage.processSenderAck.assert_called_once_with(
			sender_userid=4, amount=5, paymentHash=6
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound(), storage.InsufficientFunds()]:
			storage.processSenderAck.reset_mock()
			storage.processSenderAck.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.send(storage, userid=4, amount=5, paymenthash=6)


	def test_receive(self):
		storage = MockStorage()

		#Successfull call
		storage.processReceiverClaim = Mock()
		ret = bl4p_rpc.receive(storage, paymentpreimage=4)
		self.assertEqual(ret,
			{}
			)
		storage.processReceiverClaim.assert_called_once_with(
			paymentPreimage=4
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound()]:
			storage.processReceiverClaim.reset_mock()
			storage.processReceiverClaim.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.receive(storage, paymentpreimage=4)


	def test_getstatus(self):
		storage = MockStorage()

		#Successfull call
		storage.getTransactionStatus = Mock(
			return_value='fubar'
			)
		ret = bl4p_rpc.getstatus(storage, userid=4, paymenthash=5)
		self.assertEqual(ret,
			{'status': 'fubar'}
			)
		storage.getTransactionStatus.assert_called_once_with(
			userid=4, paymentHash=5
			)

		#Exceptions
		for xc in [storage.UserNotFound(), storage.TransactionNotFound()]:
			storage.getTransactionStatus.reset_mock()
			storage.getTransactionStatus.side_effect=xc
			with self.assertRaises(Exception):
				bl4p_rpc.getstatus(storage, userid=4, paymenthash=5)



if __name__ == '__main__':
	unittest.main(verbosity=2)

