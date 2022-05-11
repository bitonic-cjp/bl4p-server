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

import copy



class UserData:
	def __init__(self):
		self.nextOfferID = 0
		self.offers = {}


	def addOffer(self, offer):
		ret = self.nextOfferID
		self.offers[ret] = copy.deepcopy(offer)
		self.nextOfferID += 1
		return ret


	def listOffers(self):
		return self.offers


	def removeOffer(self, offerID):
		del self.offers[offerID]


	def findOffers(self, query):
		return filter(query.matches, self.offers.values())



class OfferBook:
	'''
	Offer book data storage and business logic back-end.
	This is a dummy class with only volatile (internal memory) storage.
	An actual implementation should use something like SQL with
	atomic database transactions.
	'''

	class InvalidOffer(Exception):
		pass

	class OfferNotFound(Exception):
		pass


	def __init__(self):
		self.data = {}


	def addOffer(self, userID, offer):
		#Sensibility check:
		#For all conditions, max >= min
		for k, v in offer.conditions.items():
			minimum, maximum = v
			if maximum < minimum:
				raise OfferBook.InvalidOffer()

		return self.getUserData(userID).addOffer(offer)


	def listOffers(self, userID):
		return self.getUserData(userID).listOffers()


	def removeOffer(self, userID, offerID):
		try:
			return self.getUserData(userID).removeOffer(offerID)
		except KeyError:
			raise OfferBook.OfferNotFound()


	def findOffers(self, query):
		return \
		[
		offer
		for userData in self.data.values()
		for offer in userData.findOffers(query)
		]


	def getUserData(self, userID):
		try:
			userData = self.data[userID]
		except KeyError:
			userData = UserData()
			self.data[userID] = userData
		return userData

