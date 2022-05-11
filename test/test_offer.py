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

import sys
import unittest

sys.path.append('..')

from bl4p_server.api import offer_pb2
from bl4p_server.api import offer



class TestOffer(unittest.TestCase):
	def test_Asset(self):
		asset = offer.Asset(max_amount=1, max_amount_divisor=10, currency='btc', exchange='ln')
		self.assertTrue(isinstance(asset, offer_pb2.Offer.Asset))
		self.assertEqual(asset.max_amount, 1)
		self.assertEqual(asset.max_amount_divisor, 10)
		self.assertEqual(asset.currency, 'btc')
		self.assertEqual(asset.exchange, 'ln')


	def test_constructor(self):
		o = offer.Offer(
			bid='foo', ask='bar',
			address='fubar',
			ID=42,
			)
		self.assertEqual(o.bid, 'foo')
		self.assertEqual(o.ask, 'bar')
		self.assertEqual(o.address, 'fubar')
		self.assertEqual(o.ID, 42)
		self.assertEqual(o.conditions, {})

		o = offer.Offer(
			bid='foo', ask='bar',
			address='fubar',
			ID=42,
			cltv_expiry_delta='cltv_range',
			sender_timeout = 'sender_timeout_range',
			locked_timeout='locked_timeout_range'
			)
		self.assertEqual(o.bid, 'foo')
		self.assertEqual(o.ask, 'bar')
		self.assertEqual(o.address, 'fubar')
		self.assertEqual(o.ID, 42)
		self.assertEqual(o.conditions,
			{
			offer_pb2.Offer.Condition.CLTV_EXPIRY_DELTA: 'cltv_range',
			offer_pb2.Offer.Condition.SENDER_TIMEOUT   : 'sender_timeout_range',
			offer_pb2.Offer.Condition.LOCKED_TIMEOUT   : 'locked_timeout_range',
			})


	def test_fromPB2(self):
		pb2 = offer_pb2.Offer()
		pb2.bid.max_amount = 1
		pb2.bid.max_amount_divisor = 10
		pb2.bid.currency = 'btc'
		pb2.bid.exchange = 'ln'
		pb2.ask.max_amount = 5000
		pb2.ask.max_amount_divisor = 100
		pb2.ask.currency = 'eur'
		pb2.ask.exchange = 'bl3p.eu'
		pb2.address = 'fubar'
		pb2.ID = 42
		c1 = pb2.conditions.add()
		c1.key = offer_pb2.Offer.Condition.CLTV_EXPIRY_DELTA
		c1.min_value = 2
		c1.max_value = 3
		c2 = pb2.conditions.add()
		c2.key = offer_pb2.Offer.Condition.SENDER_TIMEOUT
		c2.min_value = 4
		c2.max_value = 5
		c3 = pb2.conditions.add()
		c3.key = offer_pb2.Offer.Condition.LOCKED_TIMEOUT
		c3.min_value = 6
		c3.max_value = 7

		o = offer.Offer.fromPB2(pb2)
		self.assertEqual(o.bid.max_amount, 1)
		self.assertEqual(o.bid.max_amount_divisor, 10)
		self.assertEqual(o.bid.currency, 'btc')
		self.assertEqual(o.bid.exchange, 'ln')
		self.assertEqual(o.ask.max_amount, 5000)
		self.assertEqual(o.ask.max_amount_divisor, 100)
		self.assertEqual(o.ask.currency, 'eur')
		self.assertEqual(o.ask.exchange, 'bl3p.eu')
		self.assertEqual(o.address, 'fubar')
		self.assertEqual(o.ID, 42)
		self.assertEqual(o.conditions, {
			offer_pb2.Offer.Condition.CLTV_EXPIRY_DELTA: (2, 3),
			offer_pb2.Offer.Condition.SENDER_TIMEOUT: (4, 5),
			offer_pb2.Offer.Condition.LOCKED_TIMEOUT: (6, 7),
			})


	def test_toPB2(self):
		o = offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			)

		pb2 = o.toPB2()
		self.assertEqual(pb2.bid.max_amount, 1)
		self.assertEqual(pb2.bid.max_amount_divisor, 10)
		self.assertEqual(pb2.bid.currency, 'btc')
		self.assertEqual(pb2.bid.exchange, 'ln')
		self.assertEqual(pb2.ask.max_amount, 5000)
		self.assertEqual(pb2.ask.max_amount_divisor, 100)
		self.assertEqual(pb2.ask.currency, 'eur')
		self.assertEqual(pb2.ask.exchange, 'bl3p.eu')
		self.assertEqual(pb2.address, 'fubar')
		self.assertEqual(pb2.ID, 42)

		for c in pb2.conditions:
			self.assertEqual(
				o.conditions[c.key],
				(c.min_value, c.max_value)
				)
			del o.conditions[c.key]
		self.assertEqual(o.conditions, {})


	def test_equality(self):
		o = offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			)

		self.assertTrue(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=2   , max_amount_divisor=10 , currency='btc', exchange='ln'), #different
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=6000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'), #different
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='foobar', #different
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=41, #different
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 2), #different
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(3, 5), #different
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			locked_timeout=(5, 7), #different
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			#different
			sender_timeout=(4, 5),
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			#different
			locked_timeout=(6, 7),
			))

		self.assertFalse(o == offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3),
			sender_timeout=(4, 5),
			#different
			))


	def test_str(self):
		o = offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			)
		s = str(o)
		self.assertEqual(type(s), str)


	def test_getConditionMin(self):
		o = offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3)
			)
		self.assertEqual(o.getConditionMin(offer_pb2.Offer.Condition.CLTV_EXPIRY_DELTA), 2)
		self.assertEqual(o.getConditionMin(offer_pb2.Offer.Condition.SENDER_TIMEOUT), -(2**63))



	def test_getConditionMax(self):
		o = offer.Offer(
			bid=offer.Asset(max_amount=1   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(2, 3)
			)
		self.assertEqual(o.getConditionMax(offer_pb2.Offer.Condition.CLTV_EXPIRY_DELTA), 3)
		self.assertEqual(o.getConditionMax(offer_pb2.Offer.Condition.SENDER_TIMEOUT), 2**63 - 1)


	def test_matches(self):
		o1 = offer.Offer(
			bid=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			)

		matches = \
		[
		offer.Offer(
			#Exact match:
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Other address:
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='foobar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Other ID:
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=41,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Bids more:
			bid=offer.Asset(max_amount=6000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Other bid divisor:
			bid=offer.Asset(max_amount=500 , max_amount_divisor=10 , currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Asks less:
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=9   , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Other ask divisor:
			bid=offer.Asset(max_amount=5000 , max_amount_divisor=100 , currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=100  , max_amount_divisor=1000, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#No CLTV specification
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#No sender timeout specification
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#No locked timeout specification
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			),
		offer.Offer(
			#CLTV range shifted up
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(25, 35),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#CLTV range shifted down
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(15, 25),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		]
		nonMatches = \
		[
		offer.Offer(
			#Bid and ask swapped:
			bid=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			ask=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Wrong bid currency
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='usd', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Wrong ask currency
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='ltc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Wrong bid exchange
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl4p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Wrong ask exchange
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange=''),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Bids less
			bid=offer.Asset(max_amount=4000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Bids less, other bid divisor
			bid=offer.Asset(max_amount=40000, max_amount_divisor=1000, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10   , max_amount_divisor=100 , currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Asks more
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=20  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#Asks more, other ask divisor
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=2   , max_amount_divisor=10 , currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(20, 30),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#CLTV range shifted up
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(35, 45),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		offer.Offer(
			#CLTV range shifted down
			bid=offer.Asset(max_amount=5000, max_amount_divisor=100, currency='eur', exchange='bl3p.eu'),
			ask=offer.Asset(max_amount=10  , max_amount_divisor=100, currency='btc', exchange='ln'),
			address='fubar',
			ID=42,
			cltv_expiry_delta=(5, 15),
			sender_timeout=(40, 50),
			locked_timeout=(60, 70),
			),
		]

		for o2 in matches:
			self.assertTrue(o1.matches(o2))
			self.assertTrue(o2.matches(o1))
		for o2 in nonMatches:
			self.assertFalse(o1.matches(o2))
			self.assertFalse(o2.matches(o1))



if __name__ == '__main__':
	unittest.main(verbosity=2)

