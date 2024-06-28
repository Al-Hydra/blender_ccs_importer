from .utils.PyBinaryReader.binary_reader import *

class ccsDummyPos(BrStruct):
    def __init__(self):
        self.name = ''
        self.path = ''
        self.type = "DummyPos"
        self.position = (0,0,0)
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.position = br.read_float(3)
    
    def finalize(*args):
        pass

class ccsDummyPosRot(BrStruct):
    def __init__(self):
        self.name = ''
        self.path = ''
        self.type = "DummyPosRot"
        self.position = (0,0,0)
        self.rotation = (0,0,0)
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.position = br.read_float(3)
        self.rotation = br.read_float(3)
    
    def finalize(*args):
        pass

    
