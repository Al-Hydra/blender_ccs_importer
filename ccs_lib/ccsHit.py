from .utils.PyBinaryReader.binary_reader import *

class ccsHit(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Hit"
        self.path = ''
        self.hitMeshes = []
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.hitMeshCount = br.read_uint32()
        self.totalVertexCount = br.read_uint32()

        for i in range(self.hitMeshCount):
            self.hitMeshes.append(br.read_struct(hitMesh))


class hitMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.vertexCount = br.read_uint32()
        self.hitParams = br.read_uint32()
        self.verticesSet1 = [br.read_struct(hitVertex) for i in range(self.vertexCount)]
        self.verticesSet2 = [br.read_struct(hitVertex) for i in range(self.vertexCount)]


class hitVertex:
    def __init__(self):
        self.posX = 0
        self.posY = 0
        self.posZ = 0