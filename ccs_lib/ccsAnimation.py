from .utils.PyBinaryReader.binary_reader import *
from .Anms import anmChunkReader, anmChunkWriter


class ccsAnimation(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Animation"
        self.path = ''
        self.loop = False
        self.frameCount = 0
        
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.frameCount = br.read_uint32()
        self.framesSectionSize = br.read_uint32()

        anmChunkReader(self, br, indexTable, version)
    
    
    def __br_write__(self, br: BinaryReader, version, sortedChunks):
        br.write_uint32(self.index)
        br.write_uint32(self.frameCount)
        br.write_uint32(self.framesSectionSize)

        #anmChunkWriter(self, br, indexTable, version)
        anmChunkWriter(self, br, version, sortedChunks)


    def finalize(self, chunks):
        for objectCtrl in self.objectControllers:
            objectCtrl.finalize(chunks)
        

