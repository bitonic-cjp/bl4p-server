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
	def fromBP2(pb2):
		ret = Offer(pb2.bid, pb2.ask, pb2.address)

		Condition = offers_pb2.Offer.Condition
		for condition in pb2.conditions:
			if condition.key == Condition.MIN_CLTV_EXPIRY_DELTA:
				ret.min_cltv_expiry_delta = condition.value
			elif condition.key == Condition.MIN_LOCKED_TIMEOUT:
				ret.min_locked_timeout = condition.value
			elif condition.key == Condition.MAX_LOCKED_TIMEOUT:
				ret.max_locked_timeout = condition.value
			else:
				raise Exception('Unknown condition type')

		return ret


	def __init__(self,
			bid, ask,
			address,
			min_cltv_expiry_delta = None,
			min_locked_timeout = None,
			max_locked_timeout = None,
			):
		self.bid = bid
		self.ask = ask
		self.address = address
		self.min_cltv_expiry_delta = min_cltv_expiry_delta
		self.min_locked_timeout = min_locked_timeout
		self.max_locked_timeout = max_locked_timeout


	def toPB2(self):
		ret = offers_pb2.Offer()
		ret.bid.CopyFrom(self.bid)
		ret.ask.CopyFrom(self.ask)
		ret.address = self.address

		Condition = offers_pb2.Offer.Condition
		conditions = \
		{
		Condition.MIN_CLTV_EXPIRY_DELTA: self.min_cltv_expiry_delta,
		Condition.MIN_LOCKED_TIMEOUT   : self.min_locked_timeout,
		Condition.MAX_LOCKED_TIMEOUT   : self.max_locked_timeout,
		}
		for key, value in conditions.items():
			if value is not None:
				condition = ret.conditions.add()
				condition.key = key
				condition.value = value
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
		self.apiCall(request)


	def removeOffer(self, offer_hash):
		request = bl4p_proto_pb2.BL4P_RemoveOffer()
		self.apiCall(request)


	def findOffers(self, query):
		request = bl4p_proto_pb2.BL4P_FindOffers()
		result = self.apiCall(request)
		return \
		[
		Offer.fromBP2(offer_PB2)
		for offer_PB2 in result.offers
		]

