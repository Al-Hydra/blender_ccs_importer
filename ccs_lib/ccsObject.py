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
        self.clump = None

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


class ccsExternalObject(BrStruct):
    def __init__(self) -> None:
        super().__init__()
        self.index = 0
        self.name = ''
        self.path = ''
        self.type = "ExternalObject"
        self.parentIndex = 0
        self.objectIndex = 0
        self.model = None

    def __br_read__(self, br: BinaryReader, indexTable):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.referencedParentIndex = br.read_uint32()
        self.referencedParentName = indexTable.Names[self.referencedParentIndex]
        self.referencedObjectIndex = br.read_uint32()
        self.referencedObjectName = indexTable.Names[self.referencedObjectIndex]

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.index)
        br.write_uint32(self.referencedParentIndex)
        br.write_uint32(self.referencedObjectIndex)
    
    def finalize(self, chunks):
        self.parent = chunks[self.referencedParentIndex]
        self.object = chunks[self.referencedObjectIndex]


class ccsAnmObject(BrStruct):
    def __init__(self) -> None:
        super().__init__()
        self.index = 0
        self.name = ''
        self.path = ''
        self.type = "AnmObject"
        self.parentIndex = 0
        self.modelIndex = 0
        self.layerIndex = 0
        self.extraIndex = 0

    def __br_read__(self, br: BinaryReader, indexTable, version: int):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.parentIndex = br.read_uint32()
        self.layerIndex = br.read_uint32()
        self.shadowIndex = br.read_uint32()
        self.extraIndex = br.read_uint32()

    def finalize(self, chunks):
        self.parent = chunks[self.parentIndex]
        self.model = chunks[self.modelIndex]
        self.shadow = chunks[self.layerIndex]
        self.extra = chunks[self.extraIndex]