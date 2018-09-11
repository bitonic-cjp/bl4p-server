import copy



def offersMatch(o1, o2):
	return True #TODO



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
		return filter(
			lambda offer: offersMatch(query, offer),
			self.offers.values()
			)



class OfferBook:
	'''
	Offer book data storage and business logic back-end.
	This is a dummy class with only volatile (internal memory) storage.
	An actual implementation should use something like SQL with
	atomic database transactions.
	'''

	def __init__(self):
		self.data = {}


	def addOffer(self, userID, offer):
		return self.getUserData(userID).addOffer(offer)


	def listOffers(self, userID):
		return self.getUserData(userID).listOffers()


	def removeOffer(self, userID, offerID):
		return self.getUserData(userID).removeOffer(offerID)


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
