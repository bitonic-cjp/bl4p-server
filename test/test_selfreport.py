import sys
import unittest

sys.path.append('..')

from bl4p_server.api import bl4p_pb2
from bl4p_server.api import selfreport



class TestSelfReport(unittest.TestCase):
	def test_serialization(self):
		before = {'a': 'foo', 'b': 'bar'}

		b = selfreport.serialize(before)
		self.assertTrue(isinstance(b, bytes))

		after = selfreport.deserialize(b)
		self.assertTrue(isinstance(after, dict))
		self.assertEqual(before, after)



if __name__ == '__main__':
	unittest.main(verbosity=2)

