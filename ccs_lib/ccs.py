from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes
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
from cProfile import Profile
import gzip


ccsDict = {
    0x0005: ccsStream,
    0x0100: ccsObject,
    0x0101: objectFrame,
    0x0102: objectController,
    0x0200: ccsMaterial,
    0x0202: materialController,
    0x0300: ccsTexture,
    0x0400: ccsClut,
    0x0500: ccsCamera,
    0x0503: cameraController,
    0x0600: ccsLight,
    0x0700: ccsAnimation,
    0x0800: ccsModel,
    0x0900: ccsClump,
    0x0a00: ccsExternalObject,
    0x0b00: ccsHit,
    0x0c00: ccsBox,
    0x1300: ccsDummyPos,
    0x1400: ccsDummyPosRot,
    0x1900: ccsMorph,
    0x1902: morphController,
    0x1a00: ccsStreamOutlineParam,
    0x1b00: ccsStreamCelShadeParam,
    0x1d00: ccsStreamFBSBlurParam,
    0x2000: ccsAnmObject,
    0x2300: ccsDynamics,
    0xff01: frame,
}

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
            
            chunk = ccsDict.get(chunkType.value)
            
            if chunk:
                chunkData = br.read_struct(chunk, None, self.indexTable, self.version)
            else:
                print(f"Unknown chunk type {chunkType} at {hex(br.pos())}")
                chunkData = br.read_struct(ccsChunk, None, self.indexTable, chunkSize, self.version)
            
            #add the chunk to the chunks dict
            self.chunks[chunkData.index] = chunkData
            
            #asset = self.indexTable.Names[chunkData.index][1]
            #self.assets[asset].append(chunkData)

            index += 1
        
        #read stream section
        self.stream = br.read_struct(ccsStream, None, self.name, self.chunks, self.indexTable)

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
    def __init__(self, index = 0, name = "", type = "", path = ""):
        self.index = index
        self.name = name
        self.type = type
        self.path = path
        self.object = None
        self.clump = None
    
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
    ccs = br.read_struct(ccsFile)
    return ccs


if __name__ == "__main__":
    ccs = readCCS("D:\CCS\Infection\cbu1body.ccs")

    print(ccs.header.FileName)