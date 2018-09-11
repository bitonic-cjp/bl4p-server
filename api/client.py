import websocket

from . import bl4p_proto_pb2, offers_pb2
from .serialization import serialize, deserialize


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

		Condition = offers_pb2.Offer.Condition
		for condition in pb2.conditions:
			minmax = (condition.min_value, condition.max_value)
			if condition.key == Condition.CLTV_EXPIRY_DELTA:
				ret.cltv_expiry_delta = minmax
			elif condition.key == Condition.LOCKED_TIMEOUT:
				ret.locked_timeout = minmax
			else:
				raise Exception('Unknown condition type')

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
		self.cltv_expiry_delta = cltv_expiry_delta
		self.locked_timeout = locked_timeout


	def toPB2(self):
		ret = offers_pb2.Offer()
		ret.bid.CopyFrom(self.bid)
		ret.ask.CopyFrom(self.ask)
		ret.address = self.address

		Condition = offers_pb2.Offer.Condition
		conditions = \
		{
		Condition.CLTV_EXPIRY_DELTA: self.cltv_expiry_delta,
		Condition.LOCKED_TIMEOUT   : self.locked_timeout,
		}
		for key, minmax in conditions.items():
			if minmax is not None:
				condition = ret.conditions.add()
				condition.key = key
				condition.min_value, condition.max_value = minmax
		return ret



class Bl4pApi:
	class Error(Exception):
		pass


	def __init__(self, url, userid, password):
		self.websocket = websocket.WebSocket()

		header = \
		{
		'User-Agent': 'Python Bl4pApi',
		'Authorization': userid + ':' + password,
		}
		self.websocket.connect(url, header=header)
		self.lastRequestID = 0


	def close(self):
		self.websocket.close()


	def apiCall(self, request):
		request.request = self.lastRequestID
		self.websocket.send(serialize(request), opcode=websocket.ABNF.OPCODE_BINARY)

		while True:
			result = self.websocket.recv()
			result = deserialize(result)
			if result.request != self.lastRequestID:
				#TODO: log a warning (we ignore a message)
				continue

			break

		self.lastRequestID += 1


		if isinstance(result, bl4p_proto_pb2.Error):
			#TODO: include error code
			raise Bl4pApi.Error('An error was received')

		return result


	def start(self, amount, sender_timeout_delta_ms, receiver_pays_fee):
		request = bl4p_proto_pb2.BL4P_Start()
		request.amount.amount = amount
		request.sender_timeout_delta_ms = sender_timeout_delta_ms
		request.receiver_pays_fee = receiver_pays_fee
		result = self.apiCall(request)
		return result.sender_amount.amount, result.receiver_amount.amount, result.payment_hash.data


	def send(self, sender_amount, payment_hash):
		request = bl4p_proto_pb2.BL4P_Send()
		request.sender_amount.amount = sender_amount
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return result.payment_preimage.data


	def receive(self, payment_preimage):
		request = bl4p_proto_pb2.BL4P_Receive()
		request.payment_preimage.data = payment_preimage
		self.apiCall(request)


	def getStatus(self, payment_hash):
		request = bl4p_proto_pb2.BL4P_GetStatus()
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return \
		{
		bl4p_proto_pb2._waiting_for_sender  : 'waiting_for_sender',
		bl4p_proto_pb2._waiting_for_receiver: 'waiting_for_receiver',
		bl4p_proto_pb2._sender_timeout      : 'sender_timeout',
		bl4p_proto_pb2._receiver_timeout    : 'receiver_timeout',
		bl4p_proto_pb2._completed           : 'completed',
		}[result.status]


	def addOffer(self, offer):
		request = bl4p_proto_pb2.BL4P_AddOffer()
		request.offer.CopyFrom(offer.toPB2())
		return self.apiCall(request).offerID


	def listOffers(self):
		request = bl4p_proto_pb2.BL4P_ListOffers()
		result = self.apiCall(request)
		return \
		{
		item.offerID: item.offer
		for item in result.offers
		}


	def removeOffer(self, offerID):
		request = bl4p_proto_pb2.BL4P_RemoveOffer()
		request.offerID = offerID
		self.apiCall(request)


	def findOffers(self, query):
		request = bl4p_proto_pb2.BL4P_FindOffers()
		request.query.CopyFrom(query.toPB2())
		result = self.apiCall(request)
		return \
		[
		Offer.fromPB2(offer_PB2)
		for offer_PB2 in result.offers
		]

