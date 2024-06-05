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