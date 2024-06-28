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

        self.modelIndex = br.read_uint32()
        self.modelName = indexTable.Names[self.modelIndex][0]
        self.modelPath = indexTable.Names[self.modelIndex][1]
        
        self.hitMeshCount = br.read_uint32()
        self.totalVertexCount = br.read_uint32()

        for i in range(self.hitMeshCount):
            self.hitMeshes.append(br.read_struct(hitMesh))
    
    def finalize(self, chunks):
        self.model = chunks[self.modelIndex]


class hitMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.vertexCount = br.read_uint32()
        self.hitParams = br.read_uint32()
        self.verticesSet1 = [br.read_float(3) for i in range(self.vertexCount)]
        self.verticesSet2 = [br.read_float(3) for i in range(self.vertexCount)]


class hitVertex(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.X = br.read_float()
        self.Y = br.read_float()
        self.Z = br.read_float()