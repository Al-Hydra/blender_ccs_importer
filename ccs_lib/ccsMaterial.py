from .utils.PyBinaryReader.binary_reader import *

class ccsMaterial(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Material"
        self.path = ''
        self.alpha = 0
        self.offsetX = 0
        self.offsetY = 0
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.alpha = br.read_float()
        if version > 0x120:
            self.offsetX = br.read_float()
            self.offsetY = br.read_float()
        else:
            self.offsetX = br.read_uint16()
            self.offsetY = br.read_uint16()
        
        if version >= 0x125:
            values = br.read_float(18)
    

    def finalize(self, chunks):
        self.texture = chunks[self.textureIndex]
