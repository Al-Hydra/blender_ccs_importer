from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes, ccsDict
from .ccsClump import ccsClump
from .ccsDynamics import ccsDynamics
from .ccsObject import ccsObject, ccsExternalObject, ccsAnmObject
from .ccsModel import ccsModel
from .ccsTexture import ccsTexture
from .ccsClut import ccsClut
from .ccsMaterial import ccsMaterial
from .ccsDummy import ccsDummyPos, ccsDummyPosRot
from .ccsHit import ccsHit
from .ccsStream import *
from .ccsBox import ccsBox
from .ccsCamera import ccsCamera
from .ccsAnimation import ccsAnimation
from .ccsMorph import ccsMorph
from .ccsLight import ccsLight
from time import perf_counter
from .Anms import *
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
        self.indexTable: ccsIndex = br.read_struct(ccsIndex)
        self.assets = {self.indexTable.Paths[i]: [] for i in range(self.indexTable.PathsCount)}

        #fill the chunks dict with values from the index table
        self.chunks = {i: ccsChunk(i, self.indexTable.Names[i][0], "", self.indexTable.Names[i][1]) for  i in range(self.indexTable.NamesCount)}

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
            
            chunkClass = globals().get(ccsDict.get(chunkType.value), None)
            
            if chunkClass:
                chunkData = br.read_struct(chunkClass, None, self.indexTable, self.version)
            else:
                print(f"Unknown chunk type {chunkType} at {hex(br.pos())}")
                chunkData = br.read_struct(ccsChunk, None, self.indexTable, chunkSize, self.version)
            
            #add the chunk to the chunks dict
            self.chunks[chunkData.index] = chunkData
            asset = chunkData.path
            self.assets[asset].append(chunkData)

            index += 1
        
        #read stream section
        self.stream = br.read_struct(ccsStream, None, self.name, self.chunks, self.indexTable, self.version)

        #finalize initialization
        for chunk in self.chunks.values():
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
    def __init__(self, index = 0, name = "", type = "", path = ""):
        self.index = index
        self.name = name
        self.type = type
        self.path = path
        self.object = None
        self.clump = None
        self.parent = self
    
    def __br_read__(self, br: BinaryReader, indexTable, size, version):
        self.index = br.read_uint32()
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
    start = perf_counter()
    
    ccs = br.read_struct(ccsFile)

    print(f"read in {perf_counter() - start}")
    return ccs


if __name__ == "__main__":
    ccs = readCCS("D:\CCS\Infection\cbu1body.ccs")

    print(ccs.header.FileName)