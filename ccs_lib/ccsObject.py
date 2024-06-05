from .utils.PyBinaryReader.binary_reader import *


class ccsObject(BrStruct):
    def __init__(self):
        self.index = 0
        self.name = ''
        self.path = ''
        self.type = "Object"
        self.parent = None
        self.model = None
        self.shadow = None
        self.extra = None

    def __br_read__(self, br: BinaryReader, indexTable, version: int):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.parentIndex = br.read_uint32()
        self.modelIndex = br.read_uint32()
        self.shadowIndex = br.read_uint32()
        if version > 0x120:
            self.extraIndex = br.read_uint32()

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.index)
        br.write_uint32(self.parentIndex)
        br.write_uint32(self.modelIndex)
        br.write_uint32(self.shadowIndex)
        br.write_uint32(self.extraIndex)
    
    def finalize(self, chunks):
        self.parent = chunks[self.parentIndex]
        self.model = chunks[self.modelIndex]
        self.shadow = chunks[self.shadowIndex]
        if self.extraIndex:
            self.extra = chunks[self.extraIndex]


class ccsExternalObject(BrStruct):
    def __init__(self) -> None:
        super().__init__()
        self.index = 0
        self.referencedParentIndex = 0
        self.referencedObjectIndex = 0

    def __br_read__(self, br: BinaryReader, indexTable, version: int):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.referencedParentIndex = br.read_uint32()
        self.referencedObjectIndex = br.read_uint32()

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.index)
        br.write_uint32(self.referencedParentIndex)
        br.write_uint32(self.referencedObjectIndex)
