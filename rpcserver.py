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
		(name, [a[0] for a in functionData[1]])
		for name, functionData in self.server.RPCFunctions.items()
		]

		for name, args in methods:
			args.sort()
		methods.sort(key=lambda m: m[0])

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
			name = path[-1]

			try:
				function, argsDef = self.server.RPCFunctions[name]
			except KeyError:
				raise RPCException(404, 'Not found: ' + self.path)

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

			args = {}
			for name, type in argsDef:
				try:
					args[name] = type(postvars[name])
				except KeyError:
					raise RPCException(400, 'Missing parameter %s' % name)
				except ValueError:
					raise RPCException(400, 'Invalid value for parameter %s: %s' % (name, postvars[name]))

			try:
				data, success = function(**args), True
			except Exception as e:
				data, success = str(e), False

			self.do_HEAD(mime='application/json')
			self.wfile.write(json.dumps({
				'result': 'success' if success else 'error',
				'data': data
				}).encode())

		except RPCException as e:
			self.do_HEAD(response=e.code)
			self.wfile.write(str(e).encode())


	def readArgs(self, args, argsDef):

		return ret



class RPCServer(socketserver.TCPServer):
	def __init__(self):
		socketserver.TCPServer.__init__(self, ('', PORT), RPCHandler)
		self.RPCFunctions = {}


	def registerRPCFunction(self, name, function, argsDef):
		'''
		Registers an RPC function.

		:param name: the RPC name of the function.
		:param function: the function. May raise Exception.
		:param argsDef: definition of the arguments. Each element must be (name, type).
		'''

		self.RPCFunctions[name] = function, argsDef

