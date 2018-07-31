# this code was written for BL3P by folkert@vanheusden.com
# it has been released under AGPL v3.0
# heavily modified for BL4P by CJP

# it requires 'pycurl'
# in debian this can be found in the 'python-pycurl' package

import base64
import hashlib
import hmac
import json
import pycurl
import urllib.parse

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

from datetime import datetime
from time import mktime

class Bl4pApi:
	url = None
	pubKey = None
	secKey = None
	verbose = False

	def __init__(self, u, pk, sk):
		self.url = u
		self.pubKey = pk
		self.secKey = sk

	def setVerbose(self, v):
		self.verbose = v

	def apiCall(self, path, params):
		dt = datetime.utcnow()
		us = mktime(dt.timetuple()) * 1000 * 1000 + dt.microsecond
		nonce = '%d' % us

		# generate the POST data string
		post_data = urllib.parse.urlencode(params)

		body = '%s%c%s' % (path, 0x00, post_data)

		privkey_bin = base64.b64decode(self.secKey)

		signature_bin = hmac.new(privkey_bin, body.encode(), hashlib.sha512).digest()

		signature = base64.b64encode(signature_bin)

		fullpath = '%s%s' % (self.url, path)

		headers = [ 'Rest-Key: %s' % self.pubKey, 'Rest-Sign: %s' % signature.decode() ]

		buffer = BytesIO()

		c = pycurl.Curl()
		c.setopt(c.USERAGENT, 'Mozilla/4.0 (compatible; BL3P Python 3 client written by folkert@vanheusden.com; 0.1)');
		c.setopt(c.WRITEFUNCTION, buffer.write)
		c.setopt(c.URL, fullpath);
		c.setopt(c.POST, 1);
		c.setopt(c.POSTFIELDS, post_data);
		c.setopt(c.HTTPHEADER, headers);
		c.setopt(c.SSLVERSION, 1);
		c.setopt(c.SSL_VERIFYPEER, True);
		c.setopt(c.SSL_VERIFYHOST, 2);
		c.setopt(c.CONNECTTIMEOUT, 5);
		c.setopt(c.TIMEOUT, 10);

		if self.verbose:
			c.setopt(c.VERBOSE, 1)
		else:
			c.setopt(c.VERBOSE, 0)

		c.perform()

		response_code = c.getinfo(c.RESPONSE_CODE)
		if response_code != 200:
			raise Exception('unexpected response code: %d' % response_code)

		c.close()

		return json.loads(buffer.getvalue().decode())


	def start(self, **params):
		'''
		Start a new transaction.

		:param userid: the user ID of the receiver
		:param amount: the amount to be transfered from sender to receiver
		:param timedelta: the maximum time for the sender to respond, in seconds
		:param receiverpaysfee: indicates whether receiver or sender pays the fee

		:returns: the result of the function call
		'''

		return self.apiCall('start', params)

