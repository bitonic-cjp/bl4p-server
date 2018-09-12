import copy



def offersMatch(o1, o2):
	#Must be matching currency and exchange:
	if \
		o1.bid.currency != o2.ask.currency or \
		o1.bid.exchange != o2.ask.exchange or \
		o1.ask.currency != o2.bid.currency or \
		o1.ask.exchange != o2.bid.exchange:
			return False

	#All condition ranges must overlap
	commonKeys = set(o1.conditions.keys()) & set(o2.conditions.keys())
	testOverlap = lambda r1, r2: r1[0] <= r2[1] and r2[0] <= r1[1]
	overlaps = \
	(
	testOverlap(o1.conditions[key], o2.conditions[key])
	for key in commonKeys
	)
	if False in overlaps:
		return False

	#Must have compatible limit rates
	#One should bid at least as much as the other asks.
	#    bid1 / ask1 >= ask2 / bid2
	#    bid1 * bid2 >= ask1 * ask2
	#    (bid1 / bid1_div) * (bid2 / bid2_div) >= (ask1 / ask1_div) * (ask2 / ask2_div)
	#    bid1 * bid2 * ask1_div * ask2_div >= ask1 * ask2 * bid1_div * bid2_div

	#Implementation note: multiplying all these numbers together may give quite large results.
	#The correctness may well depend on Python's unlimited-size integers.
	return \
		o1.bid.max_amount * o2.bid.max_amount * o1.ask.max_amount_divisor * o2.ask.max_amount_divisor \
			>= \
		o1.ask.max_amount * o2.ask.max_amount * o1.bid.max_amount_divisor * o2.bid.max_amount_divisor



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

