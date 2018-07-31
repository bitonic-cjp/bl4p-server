import sys
import unittest

sys.path.append('..')

import utils



class TestUtils(unittest.TestCase):

	def test_Struct(self):
		class TestStruct(utils.Struct):
			attr1 = None
			attr2 = 'default'

		s = TestStruct(attr1=1, attr2=2)
		self.assertEqual(s.attr1, 1)
		self.assertEqual(s.attr2, 2)
		s = str(s)
		self.assertTrue('attr1' in s)
		self.assertTrue('attr2' in s)
		self.assertTrue('TestStruct' in s)

		s = TestStruct()
		self.assertEqual(s.attr1, None)
		self.assertEqual(s.attr2, 'default')

		with self.assertRaises(KeyError):
			s = TestStruct(attr3=1)

		self.assertEqual(
			TestStruct(attr1=1, attr2=2),
			TestStruct(attr1=1, attr2=2)
			)

		self.assertNotEqual(
			TestStruct(attr1=1, attr2=2),
			TestStruct(attr1=2, attr2=1)
			)


	def test_Enum(self):
		testEnum = utils.Enum(['foo', 'bar'])

		self.assertEqual(str(testEnum.foo), 'foo')
		self.assertEqual(str(testEnum.bar), 'bar')
		with self.assertRaises(AttributeError):
			x = str(testEnum.foobar)

		testEnum = utils.Enum(['bar', 'baz'], parentEnum=testEnum)
		self.assertEqual(str(testEnum.foo), 'foo')
		self.assertEqual(str(testEnum.bar), 'bar')
		self.assertEqual(str(testEnum.baz), 'baz')



if __name__ == '__main__':
	unittest.main(verbosity=2)

