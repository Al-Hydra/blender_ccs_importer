from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes


class ccsStream(BrStruct):

    def __init__(self):
        self.frameCount = 0
        self.chunks = []

    def __br_read__(self, br: BinaryReader):
        self.frameCount = br.read_uint32()
        currentFrame = 0
        while currentFrame != -1:
            #read chunk type
            #print(hex(br.pos()))
            chunkType = CCSTypes(br.read_uint16())
            br.seek(2, 1)
            if chunkType == CCSTypes.Frame:
                size = br.read_uint32()
                currentFrame = br.read_int32()
                continue
            else:
                chunkSize = br.read_uint32() * 4
                chunkData = br.read_bytes(chunkSize)
                self.chunks.append((chunkType, chunkData))
        #print(f'frameCount = {self.frameCount}')


class ccsStreamOutlineParam(BrStruct):
    def __init__(self) -> None:
        self.name = ""
        self.type = "StreamOutlineParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable):
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
    def __init__(self) -> None:
        self.name = ""
        self.type = "StreamCelShadeParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable):
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
    def __init__(self) -> None:
        self.name = ""
        self.type = "StreamFBSBlurParam"
        self.path = ""
    def __br_read__(self, br: BinaryReader, indexTable):
        self.unk1 = br.read_uint16()
        self.unk2 = br.read_uint16()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
    
    def finalize(self, chunks):
        pass