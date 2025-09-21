from .utils.PyBinaryReader.binary_reader import *

class ccsHit(BrStruct):
    def __init__(self):
        self.index = 0
        self.name = ''
        self.type = "HitModel"
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

    def __br_write__(self, br: BinaryReader, version):
        br.write_uint32(self.index)

        br.write_uint32(self.modelIndex)
        br.write_string_index(self.modelName)
        br.write_string_index(self.modelPath)

        br.write_uint32(self.hitMeshCount)
        br.write_uint32(self.totalVertexCount)

        for mesh in self.hitMeshes:
            br.write_struct(mesh)
    
    def finalize(self, chunks):
        self.model = chunks[self.modelIndex]


class hitMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.vertexCount = br.read_uint32()
        self.hitParams = br.read_uint32()
        self.verticesSet1 = [br.read_float32(3) for i in range(self.vertexCount)]
        self.verticesSet2 = [br.read_float32(3) for i in range(self.vertexCount)]

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.vertexCount)
        br.write_uint32(self.hitParams)

        for v in self.verticesSet1:
            br.write_float32(v)

        for v in self.verticesSet2:
            br.write_float32(v)


class hitVertex(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.X = br.read_float32()
        self.Y = br.read_float32()
        self.Z = br.read_float32()

    def __br_write__(self, br: BinaryReader):
        br.write_float32(self.X)
        br.write_float32(self.Y)
        br.write_float32(self.Z)