# Copyright (c) Mathias Kaerlev 2011.

# This file is part of pyspades.

# pyspades is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pyspades is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pyspades.  If not, see <http://www.gnu.org/licenses/>.

"""
Client implementation - WIP
"""

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from pyspades.protocol import BaseConnection
from pyspades.bytes import ByteReader, ByteWriter
from pyspades.packet import Packet, load_server_packet
from pyspades.loaders import *
from pyspades.common import *
from pyspades import clientloaders, serverloaders
from pyspades.multidict import MultikeyDict

import random

class OtherClient(object):
    def __init__(self, protocol, name, player_id):
        self.name = name
        self.protocol = protocol
        self.player_id = player_id

class ClientConnection(BaseConnection):
    protocol = None
    def __init__(self, protocol):
        BaseConnection.__init__(self)
        self.protocol = protocol
        self.auth_val = random.randint(0, 0xFFFF)
        self.map = ByteWriter()
        self.connections = MultikeyDict()
        self.spammy = {Ping : 0, MapData : 0, serverloaders.OrientationData : 0,
            serverloaders.PositionData : 0, serverloaders.AnimationData : 0,
            serverloaders.MovementData : 0}
        
        connect_request = ConnectionRequest()
        connect_request.auth_val = self.auth_val
        connect_request.client = True
        connect_request.version = crc32(open('../data/client.exe', 'rb').read())
        self.send_loader(connect_request, False, 255)
    
    def send_join(self, team = -1, weapon = -1):
        print 'joining team %s' % team
        loader = SizedData()
        data = ByteWriter()
        join = clientloaders.JoinTeam()
        join.name = 'flotothelo'
        join.team = team
        join.weapon = weapon
        join.write(data)
        loader.data = data
        self.send_loader(loader, True)
    
    def loader_received(self, packet):
        is_contained = hasattr(packet, 'data') and packet.id != MapData.id
        if is_contained:
            data = packet.data
            contained = load_server_packet(data)
        spam_class = contained.__class__ if is_contained else packet.__class__
        is_spammy = spam_class in self.spammy
        if is_spammy:
            self.spammy[spam_class] += 1
        else:
            message = None
            spammed = [spam.__name__ + (' x%s' % recv if recv > 1 else '')
                for spam, recv in self.spammy.items() if recv]
            if len(spammed):
                message = 'received ' + ', '.join(spammed)
                print message
                for spam in self.spammy:
                    self.spammy[spam] = 0            
            if is_contained:
                print contained
                print '    ', hexify(data)
        if packet.id == ConnectionResponse.id:
            self.connection_id = packet.connection_id
            self.unique = packet.unique
            self.connected = True
            print 'connected'
        elif is_contained:
            if packet.id == SizedData.id and self.map is not None:
                print 'finished!'
                reactor.callLater(1.0, self.send_join, team = 0, weapon = 0)
                #reactor.callLater(4.0, self.send_join, 1, 1)
                # open('testy.vxl', 'wb').write(str(self.map))
                self.map = None
            # data = packet.data
            # if data.dataLeft():
                # raw_input('not completely parsed')
            # print contained
            # newdata = ByteWriter()
            # contained.write(newdata)
            # if contained.id != serverloaders.PlayerData.id:
                # if str(data) != str(newdata):
                    # print hexify(data)
                    # print hexify(newdata)
                    # raw_input('incorrect save func')
        elif packet.id == MapData.id:
            data = packet.data
            if packet.num == 0:
                byte = data.readByte(True)
            self.map.write(data.read())
        elif packet.id == Ack.id:
            pass
        elif packet.id == Ping.id:
            pass
        elif packet.id == Packet10.id:
            print 'received packet10'
        else:
            print 'received:', packet
            raw_input('unknown packet')
    
    def send_data(self, data):
        self.protocol.transport.write(data)

class ClientProtocol(DatagramProtocol):
    connection_class = ClientConnection
    def __init__(self, host, port):
        self.host, self.port = host, port
    
    def startProtocol(self):
        self.transport.connect(self.host, self.port)
        self.connection = self.connection_class(self)
    
    def datagramReceived(self, data, address):
        self.connection.data_received(data)