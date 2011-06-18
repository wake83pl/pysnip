# Copyright (c) Mathias Kaerlev 2011.# This file is part of pyspades.# pyspades program is free software: you can redistribute it and/or modify# it under the terms of the GNU General Public License as published by# the Free Software Foundation, either version 3 of the License, or# (at your option) any later version.# pyspades is distributed in the hope that it will be useful,# but WITHOUT ANY WARRANTY; without even the implied warranty of# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the# GNU General Public License for more details.# You should have received a copy of the GNU General Public License# along with pyspades.  If not, see <http://www.gnu.org/licenses/>.from pyspades.compression import decompressfrom pyspades.bytes import ByteReader, ByteWriterfrom pyspades.common import *from pyspades.loaders import *from pyspades import debug# for reference onlySIZES = {    1 : 8,     2 : 48,     3 : 44,     4 : 8,     5 : 4,     6 : 6,     7 : 8,     8 : 24,     9 : 8,     10 : 12,     11 : 16}LOADERS = {    0 : Packet0,    1 : Ack,    2 : ConnectionRequest,    3 : ConnectionResponse,    4 : Disconnect,    5 : Ping,    # packet 6, 7, 8 and 9 are variabled-sized packets    6 : SizedData,    7 : Packet7,    8 : MapData,    9 : SizedSequenceData,    10 : Packet10,    11 : Packet11}for id, loader in LOADERS.iteritems():    loader.id = iddef generate_loader_data(loader):    reader = ByteWriter()    write_loader_data(reader, loader)    return reader    def write_loader_data(reader, loader):    packet_id = loader.id    if loader.ack:        packet_id |= 0x80    reader.writeByte(packet_id, True)    reader.writeByte(loader.byte or 0, True)    reader.writeShort(loader.sequence or 0, True)    loader.write(reader)class Packet(object):    timer = None    connection_id = None    packet_id = None    unique = None    items = None    data = None    def __init__(self):        pass        def read(self, data):        reader = ByteReader(data)        value = reader.readShort(True)        flags = value & 0xC000        compressed = flags & 0x4000        timer = int(flags & 0x8000 != 0) # has timer?        self.unique = (value >> 12) & 3        self.connection_id = value & 0xFFF # if == 0xFFF CONNECTIONLESS        offset = 2 * timer + 2                if timer:            self.timer = reader.readShort(True)        else:            self.timer = None                if compressed:            decompressed_data = decompress(data[offset:])            reader = ByteReader(decompressed_data)                self.items = []                while reader.dataLeft():            value = reader.readByte(True)            packet_id = value & 0xF # a should be under 12            byte = reader.readByte(True)            sequence = reader.readShort(True)            loader = LOADERS[packet_id]()            loader.ack = (value & 0x80) != 0            loader.sequence = sequence            loader.byte = byte            loader.read(reader)            self.items.append(loader)        def generate(self):        reader = ByteWriter()        flags = 0        if self.timer is not None:            flags |= 0x8000        connection_id = self.connection_id        if connection_id is None:            connection_id = 0xFFF        unique = self.unique        if unique is None:            unique = 0        value = flags | ((unique & 3) << 12) | (connection_id & 0xFFF)        reader.writeShort(value, True)        if self.timer is not None:            reader.writeShort(self.timer, True)        if self.data is None:            for item in self.items:                write_loader_data(reader, item)        else:            reader.write(str(self.data))        return readerfrom pyspades import clientloaders, serverloadersCLIENT_LOADERS = {    0 : clientloaders.PositionData,    1 : clientloaders.OrientationData,    2 : clientloaders.MovementData,    3 : clientloaders.AnimationData,    4 : clientloaders.HitPacket,    5 : clientloaders.GrenadePacket,    6 : clientloaders.SetWeapon,    7 : clientloaders.SetColor,    8 : clientloaders.JoinTeam,    11 : clientloaders.BlockAction,    13 : clientloaders.KillAction,    14 : clientloaders.ChatMessage}SERVER_LOADERS = {    0 : serverloaders.PositionData,    1 : serverloaders.OrientationData,    2 : serverloaders.MovementData,    3 : serverloaders.AnimationData,    4 : serverloaders.HitPacket,    5 : serverloaders.GrenadePacket,    6 : serverloaders.SetWeapon,    7 : serverloaders.SetColor,    8 : serverloaders.ExistingPlayer,    9 : serverloaders.IntelAction,    10 : serverloaders.CreatePlayer,    11 : serverloaders.BlockAction,    12 : serverloaders.PlayerData,    13 : serverloaders.KillAction,    14 : serverloaders.ChatMessage}for table in (CLIENT_LOADERS, SERVER_LOADERS):    for id, item in table.iteritems():        item.id = iddef load_server_packet(data):    return load_contained_packet(data, SERVER_LOADERS)def load_client_packet(data):    return load_contained_packet(data, CLIENT_LOADERS)    def load_contained_packet(data, table):    firstByte = data.readByte(True)    data.rewind(1)    type = firstByte & 0xF    return table[type](data)    