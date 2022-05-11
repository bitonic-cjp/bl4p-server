#    Copyright (C) 2019-2021 by Bitonic B.V.
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

