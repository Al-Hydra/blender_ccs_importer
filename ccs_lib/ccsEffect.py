from .utils.PyBinaryReader.binary_reader import *


class ccsEffect(BrStruct):

    def __init__(self):
        self.name = ""
        self.type = "Effect"
        self.path = ""
        self.texture = None
        self.object = None
        self.parent = None
        self.model = None

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.objectIndex = br.read_uint32()
        unk1 = br.read_int16()
        count = br.read_int16()
        minSomething = br.read_float(2)
        maxSomething = br.read_float(2)
        
        effectInfo = br.read_bytes(8 * count + 4)
        
        
    
    def finalize(self, chunks):
        self.object = chunks.get(self.objectIndex)

        