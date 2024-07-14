from .utils.PyBinaryReader.binary_reader import *


class ccsMorph(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Morph"
        self.path = ''
        self.target = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.targetIndex = br.read_uint32()
        self.targetName = indexTable.Names[self.targetIndex][0]
        self.targetPath = indexTable.Names[self.targetIndex][1]

    
    def finalize(self, chunks):
        self.target = chunks.get(self.targetIndex)