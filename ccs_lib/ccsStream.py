from .utils.PyBinaryReader.binary_reader import *
#from .ccsTypes import CCSTypes
from .Anms import anmChunkReader


class ccsStream(BrStruct):

    def __init__(self):
        self.name = "streamAnimation"
        self.type = "Stream"
        self.frameCount = 0
        self.chunks = []
        self.objectControllers = []
        self.objects = {}
        self.objectFrames = []

    def __br_read__(self, br: BinaryReader, name, ccsChunks, indexTable):
        self.name = name


        self.frameCount = br.read_uint32()
        currentFrame = 0
        anmChunkReader(self, br, indexTable)

        '''for objf in self.objectFrames:
            objf.finalize(ccsChunks)'''

class ccsStreamOutlineParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamOutlineParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.layer = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamCelShadeParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamCelShadeParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamToneShadeParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamToneShadeParam"
        self.path = ""
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamFBSBlurParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamFBSBlurParam"
        self.path = ""
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk1 = br.read_uint16()
        self.unk2 = br.read_uint16()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
    
    def finalize(self, chunks):
        pass