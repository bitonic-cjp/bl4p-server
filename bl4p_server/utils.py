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

from functools import reduce



class Struct:
	def __init__(self, **kwargs):
		self.__elementNames = [e for e in dir(self) if not e.startswith('__')]
		for k in kwargs:
			if k not in self.__elementNames:
				raise KeyError('Key %s not in Struct' % k)
			self.__dict__[k] = kwargs[k]


	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return '%s(%s)' % (
			self.__class__.__name__,
			', '.join([
				'%s=%s' % (k, repr(getattr(self, k)))
				for k in self.__elementNames
				])
			)


	def __eq__(self, obj):
		return obj.__class__ == self.__class__ and \
			reduce(lambda x,y: x and y,
				[
				getattr(self, k) == getattr(obj, k)
				for k in self.__elementNames
				])


class Enum(set):
	def __init__(self, elements, parentEnum=None):
		set.__init__(self, elements)
		if parentEnum is not None:
			self.update(parentEnum)


	def __getattr__(self, name):
		if name in self:
			return name
		raise AttributeError

