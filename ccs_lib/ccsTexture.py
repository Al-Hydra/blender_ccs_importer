from enum import Enum
from .utils.PyBinaryReader.binary_reader import *
from .utils.bmp import I8toBMP, I4toBMP
from .utils.dds import *
from .utils.tga import *
import math

class textureTypes(Enum):
    RGBA32 = 0
    Indexed8 = 0x13
    Indexed4 = 0x14
    DXT1 = 0x87
    DXT3 = 0x88
    DXT5 = 0x89

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
        self.btx = False

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
        if self.width == 0xff or self.height == 0xff:
            self.width = br.read_uint16()
            self.height = br.read_uint16()
            self.unk3 = br.read_uint16()
        elif self.textureType == 0x87 or self.textureType == 0x88 or self.textureType == 0x89:
            br.seek(4,1)
            self.btx = br.read_struct(btxTexture)
            self.width = self.btx.width
            self.height = self.btx.height
            self.textureData = self.btx.textureData
        else:
            self.width = 1 << self.width
            self.height = 1 <<self.height
            self.unk4 = br.read_uint32()
            self.textureDataSize = br.read_uint32()
            self.textureData = br.read_uint8(self.textureDataSize << 2)

            #Skip mip levels
            for i in range(self.mipmapsCount):
                
                br.read_uint32()
                mipSize = br.read_uint32() << 2
                br.seek(mipSize, Whence.CUR)
    

    def __br_write__(self, br: BinaryReader, version):
        br.write_uint32(self.index)
        br.write_uint32(self.clutIndex)
        br.write_uint32(self.blitGroup)
        br.write_uint8(self.textureFlags)
        br.write_uint8(self.textureType)
        br.write_uint8(self.mipmapsCount)
        br.write_uint8(self.unk1)
        if int(math.log2(self.width)) >= 0xff or int(math.log2(self.height)) >= 0xff:
            br.write_uint8(0xff)
            br.write_uint8(0xff)
            br.write_uint16(self.unk2)
            br.write_uint16(self.width)
            br.write_uint16(self.height)
            br.write_uint16(self.unk3)
        elif self.textureType == 0x87 or self.textureType == 0x88 or self.textureType == 0x89:
            br.write_uint8(int(math.log2(self.width)))
            br.write_uint8(int(math.log2(self.height)))
            br.write_uint16(self.unk2)
            br.write_uint32(0xffffffff)
            self.btx: btxTexture
            #need to finish btx texture for export
            br.write_struct(self.btx)
        else:
            br.write_uint8(int(math.log2(self.width)))
            br.write_uint8(int(math.log2(self.height)))
            br.write_uint16(self.unk2)
            br.write_uint32(self.unk4)
            br.write_uint32(self.textureDataSize)
            br.write_uint8(self.textureData)
    

    def convertTexture(self, rawPixels = False):
        if self.btx:
            return bmxToDDS(self.btx)
        elif self.textureType == 0:
            return rgbaToTGA(self.width, self.height, self.textureData)
        elif self.textureType == 0x13:
            return indexed8ToTGA(self.width, self.height, self.textureData, self.colorTable.paletteData)
        elif self.textureType == 0x14:
            return indexed4ToTGA(self.width, self.height, self.textureData, self.colorTable.paletteData)
        else:
            return None


    def finalize(self, chunks):
        #self.colorTable = chunks[self.clutIndex]
        self.colorTable = chunks.get(self.clutIndex)


btxFourCC = {
    7 : 'DXT1',
    8 : 'DXT3',
    9 : 'DXT5'
}


class btxTexture(BrStruct):
    def __init__(self):
        self.name = ''
        self.pixelFormat = 0
        self.width = 0
        self.height = 0
        self.mipmaps = []
        self.textureData = b''

    def __br_read__(self, br: BinaryReader):
        self.totalSizeBTX = br.read_uint32()
        self.magic = br.read_str(4)
        try:
            self.magic == "btx"
        except ValueError:
            print()
        self.version = br.read_uint32()
        self.width = br.read_uint16()
        self.height = br.read_uint16()
        br.seek(2,1)
        self.mipmapsCount = br.read_uint16()
        self.pixelFormat = br.read_uint16()
        br.seek(6,1)
        self.headerSize = br.read_uint32()
        br.seek(4,1)
        self.totalSize = br.read_uint32()
        br.seek(12,1)
        self.name = br.read_str(16)
        #self.textureData = br.read_bytes((totalSize - headerSize))
        self.textureData = br.read_bytes((self.totalSizeBTX - 0x40))


    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.totalSizeBTX)
        br.write_str_fixed(self.magic, 4)
        br.write_uint32(self.version)
        br.write_uint16(self.width)
        br.write_uint16(self.height)
        br.write_uint16(0x0200) # Unknown
        br.write_uint16(self.mipmapsCount)
        br.write_uint16(self.pixelFormat)
        br.write_uint16(0x0100) # Unknown
        br.write_uint32(0x00000501) # Unknown
        br.write_uint32(self.headerSize)
        br.write_uint32(0x000000ff)
        br.write_uint32(self.totalSize)
        br.write_uint32(0x00000030)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_str_fixed(self.name, 16)
        br.write_bytes(self.textureData)


def bmxToDDS(bmx:btxTexture):
    dds = DDS()
    dds.magic = 'DDS '
    header = dds.header = DDS_Header()
    header.pixel_format = DDS_PixelFormat()
    header.size = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    header.flags = 0x1 | 0x2 | 0x4 | 0x1000

    header.width = bmx.width
    header.height = bmx.height
    header.mipMapCount = bmx.mipmapsCount

    # check if bmx.pixel_format is in nut_pf_fourcc
    if bmx.pixelFormat in btxFourCC.keys():

        header.pixel_format.fourCC = btxFourCC[bmx.pixelFormat]
        header.flags |= 0x80000  # LINEAR_SIZE
        header.pixel_format.flags = 0x4  # DDPF_FOURCC

        if header.pixel_format.fourCC == 'DXT1':
            header.pitchOrLinearSize = bmx.width * bmx.height // 2
        else:
            header.pitchOrLinearSize = bmx.width * bmx.height

        header.pixel_format.rgbBitCount = 0
        header.pixel_format.bitmasks = (0, 0, 0, 0)

        dds.mipmaps = bmx.mipmaps
        dds.texture_data = bmx.textureData

    header.pixel_format.size = 32
    if header.mipMapCount > 1:
        header.flags |= 0x20000  # DDSD_MIPMAPCOUNT
        header.caps1 = 0x8 | 0x1000 | 0x400000
    else:
        header.caps1 = 0x1000
    header.depth = 1
    header.reserved = [0] * 11
    header.caps2 = 0
    header.caps3 = 0
    header.caps4 = 0
    header.reserved2 = 0

    br = BinaryReader(endianness=Endian.LITTLE)
    br.write_struct(DDS(), dds)
    return br.buffer()