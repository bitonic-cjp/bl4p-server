from . import offers_pb2



def Asset(max_amount, max_amount_divisor, currency, exchange):
	ret = offers_pb2.Offer.Asset()
	ret.max_amount = max_amount
	ret.max_amount_divisor = max_amount_divisor
	ret.currency = currency
	ret.exchange = exchange
	return ret



class Offer:
	@staticmethod
	def fromPB2(pb2):
		ret = Offer(pb2.bid, pb2.ask, pb2.address)

		for condition in pb2.conditions:
			ret.conditions[condition.key] = \
				(condition.min_value, condition.max_value)

		return ret


	def __init__(self,
			bid, ask,
			address,
			cltv_expiry_delta = None, #None or (min, max)
			locked_timeout = None,    #None or (min, max)
			):
		self.bid = bid
		self.ask = ask
		self.address = address
		self.conditions = {}
		Condition = offers_pb2.Offer.Condition
		if cltv_expiry_delta is not None:
			self.conditions[Condition.CLTV_EXPIRY_DELTA] = cltv_expiry_delta
		if locked_timeout is not None:
			self.conditions[Condition.LOCKED_TIMEOUT] = locked_timeout


	def __eq__(self, other):
		return self.__dict__ == other.__dict__


	def toPB2(self):
		ret = offers_pb2.Offer()
		ret.bid.CopyFrom(self.bid)
		ret.ask.CopyFrom(self.ask)
		ret.address = self.address

		Condition = offers_pb2.Offer.Condition
		for key, minmax in self.conditions.items():
			condition = ret.conditions.add()
			condition.key = key
			condition.min_value, condition.max_value = minmax
		return ret
