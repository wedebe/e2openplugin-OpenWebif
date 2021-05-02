# -*- coding: utf-8 -*-

##########################################################################
# OpenWebif: wsController
##########################################################################
# Copyright (C) 2021 E2OpenPlugins
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
##########################################################################

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource

import json

class OWFServerProtocol(WebSocketServerProtocol):

	TYPE_RESULT = "result"
	TYPE_PING = "ping"

	server = None

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(code))

	# def _disconnect(self, code=3401, reason=u'Authentication failed'):
	# 	self.sendClose(code=code, reason=reason)

	def onConnecting(self, request):
		print("Client connectinging: {0}".format(request.peer))
		return None

	def onConnect(self, request):
		print("Client connecting: {0}".format(request.peer))
		return None

	def onOpen(self):
		print("open")

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			# msg = json.loads(payload, 'utf8')
			msg = payload
			print("> %s" % (msg))
			self.sendMessage(msg)
			# self.onJSONMessage(msg)

	# def onJSONMessage(self, msg):
	# 	if not msg:
	# 		return
	# 	print("> (JSON) %s" % (msg))
		# self._requestID = msg["id"]
		# do = 'do_{}'.format(msg['type'])
		# getattr(self, do)(msg)

	# def sendJSON(self, msg):
	# 	if "id" in msg:
	# 		self._requestID += 1
	# 		msg['id'] = self._requestID
	# 	msg = json.dumps(msg).encode('utf8')
	# 	print("< %s" % (msg))
	# 	self.sendMessage(msg)

	# def sendResult(self, id, result=None):
	# 	msg = {
	# 		"id": id,
	# 		"type": self.TYPE_RESULT,
	# 		"success": True,
	# 		"result": result,
	# 	}
	# 	self.sendJSON(msg)

	# def sendError(self, id, code, message=None):
	# 	data = {
	# 		"id": id,
	# 		"type": self.TYPE_RESULT,
	# 		"success": False,
	# 		"error": {
	# 			"code": code,
	# 			"message": message,
	# 		}
	# 	}
	# 	self.sendJSON(data)

	# def do_ping(self, msg):
	# 	self.sendJSON({"type": self.TYPE_PING})


class BroadcastServerProtocol(WebSocketServerProtocol):

	def onOpen(self):
		self.factory.register(self)

	def onMessage(self, payload, isBinary):
		if not isBinary:
			msg = "{} from {}".format(payload.decode('utf8'), self.peer)
			self.factory.broadcast(msg)

	def connectionLost(self, reason):
		WebSocketServerProtocol.connectionLost(self, reason)
		self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):

	"""
	Simple broadcast server broadcasting any message it receives to all
	currently connected clients.
	"""

	def __init__(self, url):
		WebSocketServerFactory.__init__(self, url)
		self.clients = []
		self.tickcount = 0
		self.tick()

	def tick(self):
		self.tickcount += 1
		self.broadcast("tick %d from server" % self.tickcount)
		reactor.callLater(1, self.tick)

	def register(self, client):
		if client not in self.clients:
			print("registered client {}".format(client.peer))
			self.clients.append(client)

	def unregister(self, client):
		if client in self.clients:
			print("unregistered client {}".format(client.peer))
			self.clients.remove(client)

	def broadcast(self, msg):
		print("broadcasting message '{}' ..".format(msg))
		for c in self.clients:
			c.sendMessage(msg.encode('utf8'))
			print("message sent to {}".format(c.peer))


class BroadcastPreparedServerFactory(BroadcastServerFactory):

	"""
	Functionally same as above, but optimized broadcast using
	prepareMessage and sendPreparedMessage.
	"""

	def broadcast(self, msg):
		print("broadcasting prepared message '{}' ..".format(msg))
		preparedMsg = self.prepareMessage(msg)
		for c in self.clients:
			c.sendPreparedMessage(preparedMsg)
			print("prepared message sent to {}".format(c.peer))


class OWFWebSocketServer():
	def __init__(self):
		self.factory = WebSocketServerFactory(url=None)
		self.factory.setProtocolOptions(autoPingInterval=15, autoPingTimeout=3)
		self.factory.protocol = OWFServerProtocol #(self.topics)
		self.root = WebSocketResource(self.factory)
		OWFServerProtocol.server = None

	def start(self):
		OWFServerProtocol.server = self


webSocketServer = OWFWebSocketServer()
