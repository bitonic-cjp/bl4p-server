#    Copyright (C) 2018-2021 by Bitonic B.V.
#
#    This file is part of the BL4P Server.
#
#    The BL4P Server is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The BL4P Server is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with the BL4P Server. If not, see <http://www.gnu.org/licenses/>.

from .api import bl4p_pb2
from .api.offer import Offer



def error(reason):
	result = bl4p_pb2.Error()
	result.reason = reason
	return result



def addOffer(offerBook, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

	result = bl4p_pb2.BL4P_AddOfferResult()

	try:
		result.offerID = offerBook.addOffer(
			userID=userID,
			offer=Offer.fromPB2(request.offer)
			)
	except offerBook.InvalidOffer:
		return error(bl4p_pb2.Err_NoSuchOrder)

	return result


def listOffers(offerBook, userID, request):
	if userID is None:
		return error(bl4p_pb2.Err_Unauthorized)

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
		return error(bl4p_pb2.Err_Unauthorized)

	try:
		offerBook.removeOffer(
			userID=userID,
			offerID=request.offerID
			)
	except offerBook.OfferNotFound:
		return error(bl4p_pb2.Err_NoSuchOrder)

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

