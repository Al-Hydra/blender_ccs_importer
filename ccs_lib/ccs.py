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
from .ccsEffect import ccsEffect
from .ccsPCM import ccsPCM
from time import perf_counter
from .Anms import *
import gzip, zlib
from cProfile import Profile



class ccsFile(BrStruct):
    def __init__(self):
        self.name = ""
        self.version = 0
        self.indexTable = None
        self.chunks = {}
        self.chunks2 = {}

    def __br_read__(self, br: BinaryReader):
        #read the header
        self.header = br.read_struct(ccsHeader)
        self.name = self.header.FileName
        self.version = self.header.Version
        self.indexTable: ccsIndex = br.read_struct(ccsIndex)
        self.assets = {self.indexTable.Paths[i]: [] for i in range(self.indexTable.PathsCount)}

        #fill the chunks dict with values from the index table
        #self.chunks = {self.indexTable.Names[i][0]: ccsChunk(i, self.indexTable.Names[i][0], "", self.indexTable.Names[i][1]) for i in range(self.indexTable.NamesCount)}
        self.sortedChunks = {name: [] for name in CCSTypes.__members__.keys()}
        self.sortedChunks[""] = []
        #read setup section
        chunkType = CCSTypes(br.read_uint16())
        br.seek(2, 1) #skip 0xCCCC bytes
        chunkSize = br.read_uint32() * 4
        br.seek(chunkSize, 1)

        index = 0
        #read regular chunks
        while chunkType != CCSTypes.Stream:
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
                print(f"Unknown chunk type {chunkType} at {hex(br.pos())}, index {index}")
                chunkData = br.read_struct(ccsChunk, None, self.indexTable, chunkSize, self.version)

            self.sortedChunks[chunkData.type].append(chunkData)
            #sort obj2 chunks separetly as there index overlaps with companion chunks
            if chunkData.type == "AnimationObject":
                self.chunks2[chunkData.index] = chunkData
            else:
                self.chunks[chunkData.index] = chunkData

            index += 1
        
        #read stream section
        self.stream = br.read_struct(ccsStream, None, self.name, self.chunks, self.indexTable, self.version)

        #finalize initialization
        for chunk in self.chunks.values():
            #make obj2/chunks2 data avalible to effect chunks with out effecting other chunks finalize
            if chunk.type == "Effect":
                chunk.finalize(self.chunks, self.chunks2)
            else:
                chunk.finalize(self.chunks)
                
            asset = chunk.path
            self.assets[asset].append(chunk)
    
    def combinePCM(self):
        parentPCM = None
        
        if self.sortedChunks.get("PCM"):
            for chunk in self.sortedChunks["PCM"]:
                if chunk.type == "PCM":
                    parentPCM = chunk
                    break

        #get pcmframes
        if self.stream:
            if self.stream.pcmFrames:
                for frame, pcm in self.stream.pcmFrames.items():
                    if frame == 0:
                        continue
                    parentPCM.data += pcm.data
        
        return parentPCM


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
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.data = br.read_bytes(size - 4)
    #def finalize(self, chunks):
    def finalize(self, chunks, chunks2=None):
        pass


def readCCS(filePath):
    time = perf_counter()
    with open(filePath, "rb") as f:
        fileBytes = f.read()
        #check if the file is gzipped
        if fileBytes[:2] == b'\x1f\x8b':
            fileBytes = gzip.decompress(fileBytes)
            print("File is gzipped")

    br = BinaryReader(fileBytes, encoding='cp932')        
    ccs = br.read_struct(ccsFile)
    
    print(f"CCS read in {perf_counter() - time} seconds")
    return ccs

if __name__ == "__main__":
    ccs = readCCS("D:\CCS\Infection\cbu1body.ccs")

    print(ccs.header.FileName)