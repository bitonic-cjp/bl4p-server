import cgi
import http.server
import json
import socketserver
import urllib.parse



socketserver.TCPServer.allow_reuse_address = True
PORT = 8000


class RPCException(Exception):
	def __init__(self, code, text):
		Exception.__init__(self, text)
		self.code = code



class RPCHandler(http.server.BaseHTTPRequestHandler):
	def do_HEAD(self, response=200, mime='text/html'):
		self.send_response(response)
		self.send_header('Content-Type', mime)
		self.end_headers()


	def do_GET(self):
		methods = \
		[
		('start', ['userid', 'amount', 'timedelta', 'receiverpaysfee']),
		('send', ['userid'])
		]

		forms = \
		[
		'<h3>%s</h3>' % name + \
		'<form name="post" action="%s" method="post"><table>\n<tr>' % name + \
		'</tr>\n<tr>'.join([
			'<td>%s</td><td><input name="%s" size="64"></td>' % (a,a)
			for a in args
			]) + \
		'</tr>\n</table>\n'
		'<input type="submit">'
		'</form>'
		for name, args in methods
		]

		s = '<html><body>\n' + '<hr>\n'.join(forms) + '\n</body></html>'
		
		self.do_HEAD(mime='text/html')
		self.wfile.write(s.encode())


	def do_POST(self):
		try:
			path = self.path.split('/')[1:]
			if len(path) != 1:
				raise RPCException(404, 'Not found: ' + self.path)
			methodName = path[-1]

			ctype, pdict = cgi.parse_header(self.headers['content-type'])
			if ctype == 'multipart/form-data':
				postvars = cgi.parse_multipart(self.rfile, pdict)
			elif ctype == 'application/x-www-form-urlencoded':
				length = int(self.headers['content-length'])
				postvars = urllib.parse.parse_qs(
					self.rfile.read(length),
					keep_blank_values=1)
			else:
				postvars = {}

			postvars = \
			{
			k.decode(): v[0].decode()
			for k, v in postvars.items()
			}

			try:
				ret = \
				{
				'start':     self.rpc_start,
				'send':      self.rpc_send,
				'receive':   self.rpc_receive,
				'getstatus': self.rpc_getstatus,
				}[methodName](postvars)
			except KeyError:
				raise RPCException(404, 'Not found: ' + self.path)
		except RPCException as e:
			self.do_HEAD(response=e.code)
			self.wfile.write(str(e).encode())


	def rpc_start(self, args):
		argsDef = (('userid', int), ('amount', int), ('timedelta', float), ('receiverpaysfee', bool))
		userid, amount, timeDelta, receiverPaysFee = self.readArgs(args, argsDef)

		storage = self.server.storage

		try:
			senderAmount, receiverAmount, paymentHash = \
				storage.startTransaction(
					receiver_userid=userid,
					amount=amount,
					timeDelta=timeDelta,
					receiverPaysFee=receiverPaysFee
					)

			self.writeResult(args)
		except storage.UserNotFound:
			self.writeResult('User not found', success=False)
		except storage.InsufficientAmount:
			self.writeResult('Insufficient amount (must be positive after subtraction of fees)', success=False)
		except storage.InvalidTimeDelta:
			self.writeResult('Invalid (non-positive) timedelta', success=False)


	def rpc_send(self, args):
		self.writeResult(args)


	def rpc_receive(self, args):
		self.writeResult(args)


	def rpc_getstatus(self, args):
		self.writeResult(args)


	def readArgs(self, args, argsDef):
		ret = []

		for name, type in argsDef:
			try:
				ret.append(type(args[name]))
			except KeyError:
				raise RPCException(400, 'Missing parameter %s' % name)
			except ValueError:
				raise RPCException(400, 'Invalid value for parameter %s: %s' % (name, args[name]))

		return ret


	def writeResult(self, data, success=True):
		self.do_HEAD(mime='application/json')
		self.wfile.write(json.dumps({
			'result': 'success' if success else 'error',
			'data': data
			}).encode())



class RPCServer(socketserver.TCPServer):
	def __init__(self, storage):
		socketserver.TCPServer.__init__(self, ('', PORT), RPCHandler)
		self.storage = storage

