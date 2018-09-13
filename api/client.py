import websocket

from . import bl4p_pb2
from .offer import Offer
from .serialization import serialize, deserialize



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


		if isinstance(result, bl4p_pb2.Error):
			#TODO: include error code
			raise Bl4pApi.Error('An error was received')

		return result


	def start(self, amount, sender_timeout_delta_ms, receiver_pays_fee):
		request = bl4p_pb2.BL4P_Start()
		request.amount.amount = amount
		request.sender_timeout_delta_ms = sender_timeout_delta_ms
		request.receiver_pays_fee = receiver_pays_fee
		result = self.apiCall(request)
		return result.sender_amount.amount, result.receiver_amount.amount, result.payment_hash.data


	def send(self, sender_amount, payment_hash):
		request = bl4p_pb2.BL4P_Send()
		request.sender_amount.amount = sender_amount
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return result.payment_preimage.data


	def receive(self, payment_preimage):
		request = bl4p_pb2.BL4P_Receive()
		request.payment_preimage.data = payment_preimage
		self.apiCall(request)


	def getStatus(self, payment_hash):
		request = bl4p_pb2.BL4P_GetStatus()
		request.payment_hash.data = payment_hash
		result = self.apiCall(request)
		return \
		{
		bl4p_pb2._waiting_for_sender  : 'waiting_for_sender',
		bl4p_pb2._waiting_for_receiver: 'waiting_for_receiver',
		bl4p_pb2._sender_timeout      : 'sender_timeout',
		bl4p_pb2._receiver_timeout    : 'receiver_timeout',
		bl4p_pb2._completed           : 'completed',
		}[result.status]


	def addOffer(self, offer):
		request = bl4p_pb2.BL4P_AddOffer()
		request.offer.CopyFrom(offer.toPB2())
		return self.apiCall(request).offerID


	def listOffers(self):
		request = bl4p_pb2.BL4P_ListOffers()
		result = self.apiCall(request)
		return \
		{
		item.offerID: Offer.fromPB2(item.offer)
		for item in result.offers
		}


	def removeOffer(self, offerID):
		request = bl4p_pb2.BL4P_RemoveOffer()
		request.offerID = offerID
		self.apiCall(request)


	def findOffers(self, query):
		request = bl4p_pb2.BL4P_FindOffers()
		request.query.CopyFrom(query.toPB2())
		result = self.apiCall(request)
		return \
		[
		Offer.fromPB2(offer_PB2)
		for offer_PB2 in result.offers
		]

