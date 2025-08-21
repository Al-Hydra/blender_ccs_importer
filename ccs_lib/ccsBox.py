from .utils.PyBinaryReader.binary_reader import *


class ccsBox(BrStruct):
    def  __init__(self):
        self.name = ''
        self.type = "BoundingBox"
        self.path = ''
        self.min = [0,0,0]
        self.max = [0,0,0]

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()  
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.modelIndex = br.read_uint32()
        self.min = br.read_float32(3)
        self.max = br.read_float32(3)
        
    def __br_write__(self, br: BinaryReader, version=0x120):
        br.write_uint32(self.index)
        br.write_uint32(self.modelIndex)
        br.write_float32(self.min)
        br.write_float32(self.max)
        
    
    def finalize(self, chunks):
        self.model = chunks[self.modelIndex]
        self.model.boundingBox = self
