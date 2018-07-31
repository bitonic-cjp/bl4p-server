import sys
import unittest
from unittest.mock import patch

sys.path.append('..')

import bl4p_rpc



class DummyRPCServer:
	def __init__(self):
		self.RPCFunctions = {}


	def registerRPCFunction(self, name, function, argsDef):
		self.RPCFunctions[name] = function, argsDef



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

		server = DummyRPCServer()
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



if __name__ == '__main__':
	unittest.main(verbosity=2)

