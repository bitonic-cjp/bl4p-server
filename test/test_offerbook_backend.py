import sys
import unittest

sys.path.append('..')

import offerbook_backend



class DummyQuery:
	def matches(self, offer):
		return offer.startswith('foo')



class TestOfferBook(unittest.TestCase):
	def setUp(self):
		self.offerBook = offerbook_backend.OfferBook()


	def test_offerManagement(self):
		userID = 3

		self.assertEqual(self.offerBook.listOffers(userID),
			{})

		foo = self.offerBook.addOffer(userID, 'foo')
		self.assertEqual(self.offerBook.listOffers(userID),
			{foo: 'foo'})

		bar = self.offerBook.addOffer(userID, 'bar')
		self.assertNotEqual(bar, foo)
		self.assertEqual(self.offerBook.listOffers(userID),
			{foo: 'foo', bar: 'bar'})

		self.offerBook.removeOffer(userID, foo)
		self.assertEqual(self.offerBook.listOffers(userID),
			{bar: 'bar'})

		baz = self.offerBook.addOffer(userID, 'baz')
		self.assertNotEqual(baz, foo)
		self.assertNotEqual(baz, bar)
		self.assertEqual(self.offerBook.listOffers(userID),
			{bar: 'bar', baz: 'baz'})

		with self.assertRaises(self.offerBook.OfferNotFound):
			self.offerBook.removeOffer(userID, foo)


	def test_findOffers(self):
		self.offerBook.addOffer(3, 'foobar')
		self.offerBook.addOffer(3, 'bar')
		self.offerBook.addOffer(4, 'foobaz')
		self.offerBook.addOffer(4, 'baz')
		found = self.offerBook.findOffers(DummyQuery())
		self.assertEqual(len(found), 2)
		self.assertTrue('foobar' in found)
		self.assertTrue('foobaz' in found)



if __name__ == '__main__':
	unittest.main(verbosity=2)

