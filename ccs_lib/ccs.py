from enum import Enum, IntFlag
from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes
from .ccsClump import ccsClump
from .ccsObject import ccsObject, ccsExternalObject, ccsAnmObject
from .ccsModel import ccsModel
from .ccsTexture import ccsTexture
from .ccsClut import ccsClut
from .ccsMaterial import ccsMaterial
from .ccsDummy import ccsDummyPos, ccsDummyPosRot
from .ccsHit import ccsHit
from .ccsStream import ccsStream
from  .ccsBox import ccsBox
from .ccsCamera import ccsCamera
from .ccsAnimation import ccsAnimation
from .ccsMorph import ccsMorph
from cProfile import Profile
import gzip


class ccsFile(BrStruct):
    def __init__(self):
        self.name = ""
        self.version = 0
        self.indexTable = None
        self.chunks = {}

    def __br_read__(self, br: BinaryReader):
        #read the header
        self.header = br.read_struct(ccsHeader)
        self.name = self.header.FileName
        self.version = self.header.Version
        self.indexTable = br.read_struct(ccsIndex)

        #fill the chunks dict with values from the index table
        self.chunks = {i: None for  i in range(self.indexTable.NamesCount)}

        #read setup section
        chunkType = CCSTypes(br.read_uint16())
        br.seek(2, 1) #skip 0xCCCC bytes
        chunkSize = br.read_uint32() * 4
        br.seek(chunkSize, 1)

        index = 0
        #read regular chunks
        while chunkType != CCSTypes.Stream:
            #print(hex(br.pos()))
            chunkType = CCSTypes(br.read_uint16())
            br.seek(2, 1) #skip 0xCCCC bytes
            chunkSize = br.read_uint32() * 4

            #print(f"Reading chunk {chunkType} at {hex(br.pos())} with size {chunkSize}, index {index}")
            
            if chunkType == CCSTypes.Stream:
                break
            elif chunkType == CCSTypes.Clump:
                chunkData = br.read_struct(ccsClump, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.Object:
                chunkData = br.read_struct(ccsObject, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.AnimationObject:
                chunkData = br.read_struct(ccsAnmObject, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.External:
                chunkData = br.read_struct(ccsExternalObject, None, self.indexTable)
            elif chunkType == CCSTypes.Model:
                chunkData = br.read_struct(ccsModel, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.Morpher:
                chunkData = br.read_struct(ccsMorph, None, self.indexTable)
            elif chunkType == CCSTypes.BoundingBox:
                chunkData = br.read_struct(ccsBox, None, self.indexTable)
            elif chunkType == CCSTypes.Texture:
                chunkData = br.read_struct(ccsTexture, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.Clut:
                chunkData = br.read_struct(ccsClut, None, self.indexTable)
            elif chunkType == CCSTypes.Material:
                chunkData = br.read_struct(ccsMaterial, None, self.indexTable, self.version)
            elif chunkType == CCSTypes.DummyPosition:
                chunkData = br.read_struct(ccsDummyPos, None, self.indexTable)
            elif chunkType == CCSTypes.DummyPositionRotation:
                chunkData = br.read_struct(ccsDummyPosRot, None, self.indexTable)
            elif chunkType == CCSTypes.HitModel:
                chunkData = br.read_struct(ccsHit, None, self.indexTable)
            elif chunkType == CCSTypes.Camera:
                chunkData = br.read_struct(ccsCamera, None, self.indexTable)
            elif chunkType == CCSTypes.Animation:
                chunkData = br.read_struct(ccsAnimation, None, self.indexTable, self.version)
            else:
                print(f"Unknown chunk type {chunkType} at {hex(br.pos())}")
                chunkData = br.read_struct(ccsChunk, None, self.indexTable, chunkSize)
            
            #add the chunk to the chunks dict
            self.chunks[chunkData.index] = chunkData

            index += 1
        
        #read stream section
        self.stream = br.read_struct(ccsStream)

        #finalize initialization
        for chunk in self.chunks.values():
            if chunk is not None:
                chunk.finalize(self.chunks)


class ccsHeader(BrStruct):
    def __init__(self):
        self.Type = None

    def __br_read__(self, br: BinaryReader):
        self.Type = br.read_uint32() & 0xFFFF
        assert self.Type == CCSTypes.Header.value
        self.Size = br.read_uint32() * 4
        self.Magic = br.read_str(4)
        self.FileName = br.read_str(32)
        self.Version = br.read_uint32()
        self.TotalChunkCount = br.read_uint32()
        br.seek(8, 1)

class ccsIndex(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.ccs_type = br.read_uint32() & 0xFFFF
        assert self.ccs_type == CCSTypes.IndexTable.value

        self.Size = br.read_uint32() * 4

        self.PathsCount = br.read_uint32()
        self.NamesCount = br.read_uint32()

        self.Paths = [br.read_str(32) for i in range(self.PathsCount)]
        self.Names = [(br.read_str(30), self.Paths[br.read_uint16()]) for i in range(self.NamesCount)]

class ccsChunk(BrStruct):
    def __init__(self):
        self.index = 0
        self.name = ""
        self.type = ""
        self.path = ""
    
    def __br_read__(self, br: BinaryReader, indexTable, size):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.data = br.read_bytes(size - 4)
    def finalize(self, chunks):
        pass


def readCCS(filePath):
    with open(filePath, "rb") as f:
        fileBytes = f.read()
        #check if the file is gzipped
        if fileBytes[:2] == b'\x1f\x8b':
            fileBytes = gzip.decompress(fileBytes)
            print("File is gzipped")

    br = BinaryReader(fileBytes, encoding='cp932')
    ccs = br.read_struct(ccsFile)
    return ccs


if __name__ == "__main__":
    ccs = readCCS("D:\CCS\Infection\cbu1body.ccs")

    print(ccs.header.FileName)