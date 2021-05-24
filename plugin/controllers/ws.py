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


from __future__ import print_function
from twisted.internet import reactor, task
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource
from .models.info import getStatusInfo

import json

class OWFServerProtocol(WebSocketServerProtocol):

	TYPE_RESULT = "result"
	TYPE_PING = "ping"
	server = None

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(code))


class BroadcastServerProtocol(WebSocketServerProtocol):

	def onConnect(self, request):
		debugLog("BSP: onConnect: {0}".format(request.peer))

	def onOpen(self):
		debugLog("BSP: onOpen")
		self.factory.registerClient(self)

	def onMessage(self, payload, isBinary):
		if not isBinary:
			msg = "{} from {}".format(payload.decode('utf8'), self.peer)
			debugLog("BSP: onMessage: (!isBinary) %s" % (msg))
			self.factory.broadcast(msg)

	def connectionLost(self, reason):
		debugLog("BSP: connectionLost")
		WebSocketServerProtocol.connectionLost(self, reason)
		self.factory.deregisterClient(self)

	def onClose(self, wasClean, code, reason):
		debugLog("BSP: onClose: {0}".format(reason))


class BroadcastServerFactory(WebSocketServerFactory):

	"""
	Simple broadcast server broadcasting any message it receives to all
	currently connected clients.
	"""

	def __init__(self, url):
		debugLog("BSF: __init__")
		WebSocketServerFactory.__init__(self, url)
		self.clients = []
		self.tickcount = 0
		self.tick()

		l = task.LoopingCall(self.tick)
		l.start(1.0) # call every second
		# l.stop() will stop the looping calls

	def tick(self):
		debugLog("BSF: tick")
		# self.tickcount += 1
		# self.broadcast("tick %d from server" % self.tickcount)
		msg = json.dumps(getStatusInfo(self))
		self.broadcast(msg)
		# https://twistedmatrix.com/documents/12.3.0/core/howto/time.html
		# reactor.callLater(1, self.tick)

	def registerClient(self, client):
		if client not in self.clients:
			debugLog("BSF: registerClient {}".format(client.peer))
			self.clients.append(client)

	def deregisterClient(self, client):
		if client in self.clients:
			debugLog("BSF: deregisterClient: {}".format(client.peer))
			self.clients.remove(client)

	def broadcast(self, msg):
		for client in self.clients:
			client.sendMessage(msg.encode('utf8'))
			debugLog("BSF: broadcast (to {}): {}".format(client.peer, msg))
		# debugLog("BSF: broadcast (to {} clients): {}".format(len(self.clients), msg))


# for futute use
class BroadcastPreparedServerFactory(BroadcastServerFactory):

	"""
	Functionally same as above, but optimized broadcast using
	prepareMessage and sendPreparedMessage.
	"""

	def broadcast(self, msg):
		print("broadcasting prepared message '{}' ..".format(msg))
		preparedMsg = self.prepareMessage(msg)
		for client in self.clients:
			client.sendPreparedMessage(preparedMsg)
			print("prepared message sent to {}".format(client.peer))
			debugLog("BSF: broadcast (to {}): {}".format(client, msg))
		# debugLog("BPSF: broadcast (to {} clients): {}".format(len(self.clients), msg))


class OWIFWebSocketServer():
	def __init__(self):
		debugLog("OSS: __init__")
		ServerFactory = BroadcastServerFactory
		# ServerFactory = BroadcastPreparedServerFactory

		factory = ServerFactory(url=None)
		factory.setProtocolOptions(autoPingInterval=15, autoPingTimeout=3)
		factory.protocol = BroadcastServerProtocol #(self.topics)
		self.resource = WebSocketResource(factory)
		# BroadcastServerProtocol.server = None
		# start
		BroadcastServerProtocol.server = self

	def start(self):
		debugLog("OSS: start")


webSocketServer = OWIFWebSocketServer()
