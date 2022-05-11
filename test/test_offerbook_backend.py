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

from bl4p_server import offerbook_backend



class DummyOffer:
	def __init__(self, name):
		self.name = name
		self.conditions = {}


	def __eq__(self, o):
		return o.name == self.name



class DummyQuery:
	def matches(self, offer):
		return offer.name.startswith('foo')



class TestOfferBook(unittest.TestCase):
	def setUp(self):
		self.offerBook = offerbook_backend.OfferBook()


	def test_offerManagement(self):
		userID = 3

		offers = DummyOffer('foo'), DummyOffer('bar'), DummyOffer('baz')

		self.assertEqual(self.offerBook.listOffers(userID),
			{})

		foo = self.offerBook.addOffer(userID, offers[0])
		self.assertEqual(self.offerBook.listOffers(userID),
			{foo: offers[0]})

		bar = self.offerBook.addOffer(userID, offers[1])
		self.assertNotEqual(bar, foo)
		self.assertEqual(self.offerBook.listOffers(userID),
			{foo: offers[0], bar: offers[1]})

		self.offerBook.removeOffer(userID, foo)
		self.assertEqual(self.offerBook.listOffers(userID),
			{bar: offers[1]})

		baz = self.offerBook.addOffer(userID, offers[2])
		self.assertNotEqual(baz, foo)
		self.assertNotEqual(baz, bar)
		self.assertEqual(self.offerBook.listOffers(userID),
			{bar: offers[1], baz: offers[2]})

		with self.assertRaises(self.offerBook.OfferNotFound):
			self.offerBook.removeOffer(userID, foo)


	def test_invalidOffer(self):
		userID = 3

		offer = DummyOffer('foo')
		offer.conditions[0] = (3, 2) #min > max

		with self.assertRaises(self.offerBook.InvalidOffer):
			self.offerBook.addOffer(userID, offer)

		self.assertEqual(self.offerBook.listOffers(userID),
			{})


	def test_findOffers(self):
		offers = DummyOffer('foobar'), DummyOffer('bar'), DummyOffer('foobaz'), DummyOffer('baz')

		self.offerBook.addOffer(3, offers[0])
		self.offerBook.addOffer(3, offers[1])
		self.offerBook.addOffer(4, offers[2])
		self.offerBook.addOffer(4, offers[3])
		found = self.offerBook.findOffers(DummyQuery())
		self.assertEqual(len(found), 2)
		self.assertTrue(offers[0] in found)
		self.assertTrue(offers[2] in found)



if __name__ == '__main__':
	unittest.main(verbosity=2)

