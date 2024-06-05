from enum import Enum
from .utils.PyBinaryReader.binary_reader import *
from .utils.bmp import I8toBMP, I4toBMP
from .utils.tga import *

class textureTypes(Enum):
    RGBA32 = 0
    Indexed8 = 0x13
    Indexed4 = 0x14
    DXT1 = 0x87
    DXT5 = 0x89

'''
class Texture(CCSChunk):
    def init_data(self, chunk: BrTexture, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.ColorTable: Color_Palette = chunks[chunk.ClutID]
        self.BlitGroup = chunk.BlitGroup
        self.TextureFlags = chunk.TextureFlags
        self.textureType = textureTypes(chunk.textureType).name
        self.MipmapsCount = chunk.MipmapsCount
        self.width = chunk.Actualwidth
        self.height = chunk.Actualheight

        self.textureData = chunk.textureData

        if self.textureType == 'Indexed8':
            self.Image = I8toBMP(self.width, self.height, self.textureData, self.ColorTable.PaletteData)
        elif self.textureType == 'Indexed4':
            self.Image = I4toBMP(self.width, self.height, self.textureData, self.ColorTable.PaletteData)
'''

class ccsTexture(BrStruct):

    def __init__(self):
        self.name = ''
        self.type = 'Texture'
        self.path = ''
        self.textureName = ''
        self.textureType = 0
        self.textureFlags = 0
        self.colorTable = 0
        self.mipmapsCount = 0
        self.width = 0
        self.height = 0
        self.textureData = b''

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.clutIndex = br.read_uint32()
        self.blitGroup = br.read_uint32()
        self.textureFlags = br.read_uint8()
        self.textureType = br.read_uint8()
        self.mipmapsCount = br.read_uint8()
        self.unk1 = br.read_uint8()
        self.width = br.read_uint8()
        self.height = br.read_uint8()
        self.unk2 = br.read_uint16()
        if version < 0x120:
            self.width = 1 << self.width
            self.height = 1 << self.height
            self.unk3 = br.read_uint32()
        elif self.width == 0xff or self.height == 0xff:
            self.width = br.read_uint16()
            self.height = br.read_uint16()
            self.unk3 = br.read_uint16()
        elif self.textureType == 0x87 or self.textureType == 0x89:
            br.seek(0x10, 1)
            self.width = br.read_uint16()
            self.height = br.read_uint16()
            br.seek(0x14, 1)
        else:
            self.width = 1 << self.width
            self.height = 1 <<self.height
            self.unk4 = br.read_uint32()

        self.textureDataSize = br.read_uint32()

        if self.textureType == 0x87 or self.textureType == 0x89:
            br.seek(0xC, 1)
            self.textureName = br.read_str(16)
            self.textureData = br.read_bytes(self.textureDataSize - 0x40)
        else:
            self.textureData = br.read_uint8(self.textureDataSize << 2)

    
    def convertToBMP(self):
        if self.textureType == 0x13:
            return I8toBMP(self.width, self.height, self.textureData, self.colorTable.paletteData)
        elif self.textureType == 0x14:
            return I4toBMP(self.width, self.height, self.textureData, self.colorTable.paletteData)
        else:
            return None
    
    def convertToTGA(self):
        if self.textureType == 0x13:
            return indexed8ToTGA(self.width, self.height, self.textureData, self.colorTable.paletteData)
        elif self.textureType == 0x14:
            return indexed4ToTGA(self.width, self.height, self.textureData, self.colorTable.paletteData)
    

    def finalize(self, chunks):
        self.colorTable = chunks[self.clutIndex]