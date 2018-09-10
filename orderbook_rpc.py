from api import bl4p_proto_pb2
from api.client import Offer, Asset


div_mBTC = 1000
div_EUR  = 1
dummyOrderBook = \
{
1: Offer(
	bid = Asset(1, div_mBTC, 'btc', 'ln'),
	ask = Asset(6, div_EUR , 'eur', 'bl3p.eu'),
	address = 'foo',
	cltv_expiry_delta = (3, 4)
	),
2: Offer(
	bid = Asset(8, div_EUR , 'eur', 'bl3p.eu'),
	ask = Asset(2, div_mBTC, 'btc', 'ln'),
	address = 'foo',
	locked_timeout = (5, 6)
	),
}



def error(reason):
	result = bl4p_proto_pb2.Error()
	result.reason = reason
	return result



def addOffer(market, userID, request):
	#TODO

	result = bl4p_proto_pb2.BL4P_AddOfferResult()
	return result


def listOffers(market, userID, request):
	#TODO
	result = bl4p_proto_pb2.BL4P_ListOffersResult()
	for ID, offer in dummyOrderBook.items():
		item = result.offers.add()
		item.offerID = ID
		item.offer.CopyFrom(offer.toPB2())
	return result


def removeOffer(market, userID, request):
	#TODO

	result = bl4p_proto_pb2.BL4P_RemoveOfferResult()
	return result


def findOffers(market, userID, request):
	query = Offer.fromBP2(request.query)

	#TODO
	result = bl4p_proto_pb2.BL4P_FindOffersResult()
	for offer in dummyOrderBook.values():
		offer_pb2 = result.offers.add()
		offer_pb2.CopyFrom(offer.toPB2())
	return result



def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(server, market):
	functionData = \
	{
	bl4p_proto_pb2.BL4P_AddOffer    : addOffer,
	bl4p_proto_pb2.BL4P_ListOffers  : listOffers,
	bl4p_proto_pb2.BL4P_RemoveOffer : removeOffer,
	bl4p_proto_pb2.BL4P_FindOffers  : findOffers,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, market))

