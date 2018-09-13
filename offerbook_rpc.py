from api import bl4p_pb2
from api.offer import Offer



def error(reason):
	result = bl4p_pb2.Error()
	result.reason = reason
	return result



def addOffer(offerBook, userID, request):
	if userID is None:
		return error(bl4p_pb2._Unauthorized)

	result = bl4p_pb2.BL4P_AddOfferResult()
	result.offerID = offerBook.addOffer(
		userID=userID,
		offer=Offer.fromPB2(request.offer)
		)
	return result


def listOffers(offerBook, userID, request):
	if userID is None:
		return error(bl4p_pb2._Unauthorized)

	result = bl4p_pb2.BL4P_ListOffersResult()
	data = offerBook.listOffers(
		userID=userID
		)
	for offerID, offer in data.items():
		item = result.offers.add()
		item.offerID = offerID
		item.offer.CopyFrom(offer.toPB2())
	return result


def removeOffer(offerBook, userID, request):
	if userID is None:
		return error(bl4p_pb2._Unauthorized)

	try:
		offerBook.removeOffer(
			userID=userID,
			offerID=request.offerID
			)
	except offerBook.OfferNotFound:
		return error(bl4p_pb2._NoSuchOrder)

	result = bl4p_pb2.BL4P_RemoveOfferResult()
	return result


def findOffers(offerBook, userID, request):
	result = bl4p_pb2.BL4P_FindOffersResult()
	data = offerBook.findOffers(
		query=Offer.fromPB2(request.query)
		)
	for offer in data:
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
	bl4p_pb2.BL4P_AddOffer    : addOffer,
	bl4p_pb2.BL4P_ListOffers  : listOffers,
	bl4p_pb2.BL4P_RemoveOffer : removeOffer,
	bl4p_pb2.BL4P_FindOffers  : findOffers,
	}

	for requestType, function in functionData.items():
		server.registerRPCFunction(requestType,
			makeClosure(function, offerBook))

