import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append('..')

from bl4p_server.api import bl4p_pb2, offer_pb2
from bl4p_server import offerbook_rpc



class MockServer:
	def __init__(self):
		self.RPCFunctions = {}


	def registerRPCFunction(self, requestType, function):
		self.RPCFunctions[requestType] = function



class MockOfferBook(Mock):
	class InvalidOffer(Exception):
		pass

	class OfferNotFound(Exception):
		pass



class MockOffer(Mock):
	def __init__(self):
		Mock.__init__(self)
		self.conditions = {}
		self.toPB2 = Mock(
			return_value=offer_pb2.Offer()
			)



class TestOfferBookRPC(unittest.TestCase):

	@patch('bl4p_server.offerbook_rpc.addOffer'   , return_value=100)
	@patch('bl4p_server.offerbook_rpc.listOffers' , return_value=101)
	@patch('bl4p_server.offerbook_rpc.removeOffer', return_value=102)
	@patch('bl4p_server.offerbook_rpc.findOffers' , return_value=103)
	def test_registerRPC(self, mock_findOffers, mock_removeOffer, mock_listOffers, mock_addOffer):
		mocks = \
		{
		bl4p_pb2.BL4P_AddOffer   : mock_addOffer,
		bl4p_pb2.BL4P_ListOffers : mock_listOffers,
		bl4p_pb2.BL4P_RemoveOffer: mock_removeOffer,
		bl4p_pb2.BL4P_FindOffers : mock_findOffers,
		}

		server = MockServer()
		offerBook = Mock()

		offerbook_rpc.registerRPC(server, offerBook)

		self.assertEqual(len(server.RPCFunctions.keys()), len(mocks))

		#Test the functions passed to registerRPCFunction
		for requestType in mocks.keys():
			registeredFunction = server.RPCFunctions[requestType]
			ret = registeredFunction(1,2,3)
			for mockType, mock in mocks.items():
				if mockType == requestType:
					mock.assert_called_once_with(offerBook, 1, 2, 3)
					self.assertEqual(ret, mock.return_value)
				else:
					mock.assert_not_called()
				mock.reset_mock()


	@patch('bl4p_server.offerbook_rpc.Offer')
	def test_addOffer(self, mock_Offer):
		mock_Offer.fromPB2 = Mock(
			return_value='fromPB2'
			)

		offerBook = MockOfferBook()

		request = Mock()

		#Successfull call
		offerBook.addOffer = Mock(
			return_value=42
			)
		result = offerbook_rpc.addOffer(offerBook, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_AddOfferResult))
		self.assertEqual(result.offerID, 42)
		offerBook.addOffer.assert_called_once_with(
			userID=4, offer='fromPB2'
			)
		mock_Offer.fromPB2.assert_called_once_with(
			request.offer
			)

		#Exceptions
		for xc in [offerBook.InvalidOffer()]:
			offerBook.addOffer.reset_mock()
			offerBook.addOffer.side_effect=xc
			result = offerbook_rpc.addOffer(offerBook, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		offerBook.addOffer.reset_mock()
		result = offerbook_rpc.addOffer(offerBook, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_listOffers(self):
		offerBook = MockOfferBook()

		request = Mock()

		#Successfull call
		o1 = MockOffer()
		o2 = MockOffer()
		offerBook.listOffers = Mock(
			return_value={42: o1, 43: o2}
			)
		result = offerbook_rpc.listOffers(offerBook, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_ListOffersResult))
		self.assertEqual(len(result.offers), 2)
		for item in result.offers:
			self.assertTrue(item.offerID in [42, 43])
		o1.toPB2.assert_called_once_with()
		o2.toPB2.assert_called_once_with()
		offerBook.listOffers.assert_called_once_with(
			userID=4
			)

		offerBook.listOffers.reset_mock()
		result = offerbook_rpc.listOffers(offerBook, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	def test_removeOffer(self):
		offerBook = MockOfferBook()

		request = Mock()
		request.offerID = 42

		#Successfull call
		offerBook.removeOffer = Mock()
		result = offerbook_rpc.removeOffer(offerBook, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_RemoveOfferResult))
		offerBook.removeOffer.assert_called_once_with(
			userID=4,
			offerID=42
			)

		#Exceptions
		for xc in [offerBook.OfferNotFound()]:
			offerBook.removeOffer.reset_mock()
			offerBook.removeOffer.side_effect=xc
			result = offerbook_rpc.removeOffer(offerBook, userID=4, request=request)
			self.assertTrue(isinstance(result, bl4p_pb2.Error))

		offerBook.removeOffer.reset_mock()
		result = offerbook_rpc.removeOffer(offerBook, userID=None, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.Error))


	@patch('bl4p_server.offerbook_rpc.Offer')
	def test_findOffers(self, mock_Offer):
		mock_Offer.fromPB2 = Mock(
			return_value='fromPB2'
			)

		offerBook = MockOfferBook()

		request = Mock()

		#Successfull call
		o1 = MockOffer()
		o2 = MockOffer()
		offerBook.findOffers = Mock(
			return_value=[o1, o2]
			)
		result = offerbook_rpc.findOffers(offerBook, userID=4, request=request)
		self.assertTrue(isinstance(result, bl4p_pb2.BL4P_FindOffersResult))
		self.assertEqual(len(result.offers), 2)
		offerBook.findOffers.assert_called_once_with(
			query='fromPB2'
			)



if __name__ == '__main__':
	unittest.main(verbosity=2)

