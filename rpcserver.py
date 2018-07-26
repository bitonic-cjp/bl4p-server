import http.server
import json
import socketserver



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
		try:
			path = self.path.split('/')[1:]
			if len(path) != 1:
				raise RPCException(404, 'Not found: ' + self.path)
			methodName = path[-1]
			try:
				ret = \
				{
				'start':     self.rpc_start,
				'send':      self.rpc_send,
				'receive':   self.rpc_receive,
				'getstatus': self.rpc_getstatus,
				}[methodName]()
			except KeyError:
				raise RPCException(404, 'Not found: ' + self.path)
		except RPCException as e:
			self.do_HEAD(response=e.code)
			self.wfile.write(str(e).encode())


	def rpc_start(self):
		self.writeResult(0)


	def rpc_send(self):
		self.writeResult(1)


	def rpc_receive(self):
		self.writeResult(2)


	def rpc_getstatus(self):
		self.writeResult(3)


	def writeResult(self, data, success=True):
		self.do_HEAD(mime='application/json')
		self.wfile.write(json.dumps({
			'result': 'success' if success else 'error',
			'data': data
			}).encode())



class RPCServer(socketserver.TCPServer):
	def __init__(self, storage):
		socketserver.TCPServer.__init__(self, ('', PORT), RPCHandler)

