# otbmlib version 0.2 (made by kanu)
# based on:
# https://otland.net/threads/a-comphrensive-description-of-the-otbm-format.258583/
LIB_VERSION = "0.2"


import math
import os

#----------------------constants----------------------#
OTBM_HEADER = b"\x00"
OTBM_MAPDATA = b"\x02"
OTBM_TILEAREA = b"\x04"
OTBM_TILE = b"\x05"
OTBM_ITEM = b"\x06"
NODE_OPEN = b"\xFE"
NODE_CLOSE = b"\xFF"
ESCAPE_BYTE = b"\xFD"

OTBM_ATTR_DESCRIPTION = b"\x01"
OTBM_ATTR_EXT_FILE = b"\x02"
OTBM_ATTR_TILE_FLAGS = b"\x03"
OTBM_ATTR_ACTION_ID = b"\x04"
OTBM_ATTR_UNIQUE_ID = b"\x05"
OTBM_ATTR_TEXT = b"\x06"
OTBM_ATTR_TILE_DEST = b"\x08"
OTBM_ATTR_ITEM = b"\x09"
OTBM_ATTR_DEPOT_ID = b"\x0a"
OTBM_ATTR_EXT_SPAWN_FILE = b"\x0b"
OTBM_ATTR_EXT_HOUSE_FILE = b"\x0d"
OTBM_ATTR_HOUSEDOORID = b"\x0e"
OTBM_ATTR_COUNT = b"\x0f"
OTBM_ATTR_RUNE_CHARGES = b"\x16"

TILESTATE_PROTECTIONZONE = 0x00000001
TILESTATE_NOPVP = 0x00000004
TILESTATE_NOLOGOUT = 0x00000008
TILESTATE_PVPZONE = 0x00000010

AREA_SIZE = 256

#----------------------classes and methods----------------------#

class Map:
    def __init__(self, sizeX = 256, sizeY = 256):
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.version = (0x02000000).to_bytes(4, byteorder="big")
        self.itemsMajorVersion = (0x03000000).to_bytes(4, byteorder="big")
        self.itemsMinorVersion = (0x13000000).to_bytes(4, byteorder="big")
        self.mapData = OTBMMapData()
        return

    def getTile(self, x, y, z): #x and y are absolute tile coordinates
        return self.mapData.getArea(x, y, z).getTile(x % AREA_SIZE, y % AREA_SIZE)

    def save(self, path):
        fileName = os.path.splitext(os.path.basename(path))[0] #base file name without extension

        file = open(path, "wb+")
        mapa_bytes = bytearray()
        file.write(b"\x00\x00\x00\x00")
        file.write(NODE_OPEN)
        file.write(OTBM_HEADER)
        file.write(mapa.version)
        file.write(mapa.sizeX.to_bytes(2, byteorder="little"))
        file.write(mapa.sizeY.to_bytes(2, byteorder="little"))
        file.write(mapa.itemsMajorVersion)
        file.write(mapa.itemsMinorVersion)
        file.write(NODE_OPEN)
        file.write(OTBM_MAPDATA)
        file.write(b"\x01")
        file.write(stringToBytes("Saved with otbmlib " + LIB_VERSION))
        file.write(b"\x01")
        file.write(stringToBytes("No map description available."))
        file.write(OTBM_ATTR_EXT_SPAWN_FILE)
        file.write(stringToBytes(fileName + "-spawn.xml"))
        file.write(OTBM_ATTR_EXT_HOUSE_FILE)
        file.write(stringToBytes(fileName + "-house.xml"))

        for area in mapa.mapData.areas.values():
            file.write(NODE_OPEN)
            file.write(OTBM_TILEAREA)
            file.write(area.x.to_bytes(2, byteorder="little"))
            file.write(area.y.to_bytes(2, byteorder="little"))
            file.write(area.z.to_bytes(1, byteorder="little"))

            for tile in area.tiles.values():
                file.write(NODE_OPEN)
                file.write(OTBM_TILE)
                file.write(tile.x.to_bytes(1, byteorder="little"))
                file.write(tile.y.to_bytes(1, byteorder="little"))
                
                for item in tile.items:
                    file.write(NODE_OPEN)
                    file.write(OTBM_ITEM)
                    file.write(item.id.to_bytes(2, byteorder="little").replace(b"\xfd", b"\xfd\xfd").replace(b"\xfe", b"\xfd\xfe").replace(b"\xff", b"\xfd\xff"))
                    if item.count > 0:
                        file.write(OTBM_ATTR_COUNT)
                        file.write(item.count.to_bytes(1, byteorder="little"))
                    file.write(NODE_CLOSE) #close item node
                
                file.write(NODE_CLOSE) #close tile node
            
            file.write(NODE_CLOSE) #close area node
        
        file.write(NODE_CLOSE) #close map data node
        file.write(NODE_CLOSE) #close otbm header node
        file.close()
        return



class OTBMMapData:
    def __init__(self):
        self.properties = [] #list of strings
        self.areas = {} #dict: tuple (x,y,z) -> OTBMTileArea
        return

    def getArea(self, x, y, z): #x and y are absolute tile coordinates
        ax = math.floor(x / 256) * 256
        ay = math.floor(y / 256) * 256
        if self.areas.get((ax,ay,z)) == None:
            tileArea = OTBMTileArea()
            tileArea.x = ax
            tileArea.y = ay
            tileArea.z = z
            self.areas[(ax,ay,z)] = tileArea
        return self.areas[(ax,ay,z)]



class OTBMTileArea: #a chunk of the map, contains tiles
    def __init__(self, x = 127, y = 127, z = 7):
        self.x = x #2 bytes
        self.y = y #2 bytes
        self.z = z #1 byte
        self.tiles = {} #dict: tuple (x relative, y relative) -> OTBMTile
        return

    def getTile(self, rx, ry): #rx and ry are relative tile coordinates (between 0 and 255 inclusive)
        if self.tiles.get((rx, ry)) == None:
            tile = OTBMTile()
            tile.x = rx
            tile.y = ry
            self.tiles[(rx,ry)] = tile
        return self.tiles[(rx,ry)]



class OTBMTile:
    def __init__(self, x = 0, y = 0):
        self.x = x #1 byte
        self.y = y #1 byte
        self.properties = []
        self.items = [] #list of OTBMItem
        return

    def addItem(self, id, count = 0):
        item = OTBMItem()
        item.id = id
        item.count = count
        self.items.append(item)
        return



class OTBMItem:
    def __init__(self):
        self.id = 414 #2 bytes
        self.count = 0
        self.properties = []
        return



#----------------------functions----------------------#


def stringToBytes(txt):
    data = txt.encode("ascii")
    size = len(data)
    return size.to_bytes(2, byteorder="little") + data



#----------------------debug----------------------#


#if __name__ == "__main__":
    #map = Map()
    #tile = map.getTile(5, 5, 7)
    #tile.addItem(4526)
    #map.save("testotbmlib.otbm")
