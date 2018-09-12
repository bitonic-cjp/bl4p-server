from api import bl4p_proto_pb2
from api.offer import Offer



def error(reason):
	result = bl4p_proto_pb2.Error()
	result.reason = reason
	return result



def addOffer(offerBook, userID, request):
	#TODO: check userID not None
	result = bl4p_proto_pb2.BL4P_AddOfferResult()
	result.offerID = offerBook.addOffer(userID, Offer.fromPB2(request.offer))
	return result


def listOffers(offerBook, userID, request):
	#TODO: check userID not None
	result = bl4p_proto_pb2.BL4P_ListOffersResult()
	for offerID, offer in offerBook.listOffers(userID).items():
		item = result.offers.add()
		item.offerID = offerID
		item.offer.CopyFrom(offer.toPB2())
	return result


def removeOffer(offerBook, userID, request):
	#TODO: check userID not None
	#TODO: handle exception
	offerBook.removeOffer(userID, request.offerID)
	result = bl4p_proto_pb2.BL4P_RemoveOfferResult()
	return result


def findOffers(offerBook, userID, request):
	#TODO: check userID not None
	result = bl4p_proto_pb2.BL4P_FindOffersResult()
	for offer in offerBook.findOffers(Offer.fromPB2(request.query)):
		offer_pb2 = result.offers.add()
		offer_pb2.CopyFrom(offer.toPB2())
	return result



def makeClosure(function, firstArg):
	def closure(*args, **kwargs):
		return function(firstArg, *args, **kwargs)
	return closure


def registerRPC(server, offerBook):
	functionData = \
	{
	bl4p_proto_pb2.BL4P_AddOffer    : addOffer,
	bl4p_proto_pb2.BL4P_ListOffers  : listOffers,
	bl4p_proto_pb2.BL4P_RemoveOffer : removeOffer,
	bl4p_proto_pb2.BL4P_FindOffers  : findOffers,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, offerBook))

