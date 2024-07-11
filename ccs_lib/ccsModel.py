from enum import IntFlag
from .utils.PyBinaryReader.binary_reader import *
class ModelTypes(IntFlag):
    Rigid1 = 0
    Rigid2 = 1
    TrianglesList = 2
    Deformable = 4
    ShadowMesh = 8


class RigidMesh(BrStruct):
    def __init__(self):
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.parent = None
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=64, modelFlags=0, version = 0x110):
        self.parentIndex = br.read_uint32()
        self.materialIndex = br.read_uint32()
        self.vertexCount = br.read_uint32()

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        self.vertices = [Vertex(br.read_int16(3), scale= vertexScale) for i in range(self.vertexCount)]
        br.align_pos(4)

        for vertex in self.vertices:
            vertex.normal = tuple((map(lambda x: x/64, br.read_int8(3))))
            vertex.triangleFlag = br.read_int8()

        
        if ((modelFlags & 2) == 0):
            for i in range(self.vertexCount):
                vertex.color = br.read_uint8(4)


        if version > 0x125:
            for v in self.vertices:
                v.UV = (br.read_int32() / 65536, br.read_int32() / 65536)

        else:
            for v in self.vertices:
                v.UV = (br.read_int16() / 256, br.read_int16() / 256)

    
    def finalize(self, chunks):
        self.material = chunks[self.materialIndex]
        
        

class ShadowMesh(BrStruct):
    def __init__(self):
        self.vertexCount = 0
        self.trianglesCount = 0
        self.vertices = []
        self.triangles = []

    def __br_read__(self, br: BinaryReader, vertexScale=64):
        self.vertexCount = br.read_uint32()
        self.triangleVerticesCount = br.read_uint32()
        self.vertices = [Vertex((br.read_int16(), br.read_int16(), br.read_int16()), (0,0,0), (0,0,0,0), (0, 0), vertexScale) for i in range(self.vertexCount)]

        br.align_pos(4)
        self.triangles = [br.read_int32(3) for i in range((self.triangleVerticesCount // 3))]

    def finalize(self, chunks):
        pass

    

class DeformableMesh(BrStruct):
    def __init__(self):
        self.material = None
        self.vertexCount = 0
        self.deformableVerticesCount = 0
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=256, version = 0x100, tanBinFlag = 0):
        self.materialID = br.read_uint32()
        #print(f'MaterialID = {self.MaterialID}')
        self.vertexCount = br.read_uint32() #This is the number of vertices that are actually used
        #print(f'VertexCount = {self.VertexCount}')
        self.deformableVerticesCount = br.read_uint32() 
        #print(f'TotalVertexCount = {self.TotalVertexCount}')

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        #Single weight vertices
        if not self.deformableVerticesCount:
            boneID = br.read_uint32()
            vpBuffer = BinaryReader(br.read_bytes(self.vertexCount * 6), encoding='cp932')
            br.align_pos(4)
            vnBuffer = BinaryReader(br.read_bytes(self.vertexCount * 4), encoding='cp932')

            for i in range(self.vertexCount):
                vertex = DeformableVertex()
                vertex.positions[0] = ((vpBuffer.read_int16() * finalScale),
                                        (vpBuffer.read_int16() * finalScale),
                                        (vpBuffer.read_int16() * finalScale))
                
                vertex.boneIDs[0] = boneID
                vertex.weights[0] = 1
                vertex.normals[0] = (vnBuffer.read_int8() / 64,
                                     vnBuffer.read_int8() / 64,
                                     vnBuffer.read_int8() / 64)
                vertex.triangleFlag = vnBuffer.read_int8()

                self.vertices.append(vertex)

            if version > 0x125:
                for v in self.vertices:
                    v.UV = (br.read_int32() / 65536, br.read_int32() / 65536)

            else:
                for v in self.vertices:
                    v.UV = (br.read_int16() / 256, br.read_int16() / 256)
                

            if tanBinFlag:
                vtBuffer = BinaryReader(br.read_bytes(self.vertexCount * 4), encoding='cp932')
                vbnBuffer = BinaryReader(br.read_bytes(self.vertexCount * 4), encoding='cp932')
                


        else: #multiple weights vertices
            if version < 0x125:
                vpBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 8), encoding='cp932')
                vnBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 4), encoding='cp932')
                uvBuffer = BinaryReader(br.read_bytes(self.vertexCount * 4), encoding='cp932')


                for i in range(self.vertexCount):

                    vertex = DeformableVertex()
                    
                    vertex.positions[0] = ((vpBuffer.read_int16() * finalScale),
                                            (vpBuffer.read_int16() * finalScale),
                                            (vpBuffer.read_int16() * finalScale))

                    vertParams = vpBuffer.read_uint16()
                    vertex.boneIDs[0] = vertParams >> 10
                    vertex.weights[0] = (vertParams & 0x1ff) / 256

                    vertex.normals[0] = (vnBuffer.read_int8() / 64,
                                        vnBuffer.read_int8() / 64,
                                        vnBuffer.read_int8() / 64)
                    vertex.triangleFlag = vnBuffer.read_int8()
                    
                    if ((vertParams >> 9) & 0x1) == 0:
                        vertex.positions[1] = ((vpBuffer.read_int16()) * finalScale,
                                            (vpBuffer.read_int16()) * finalScale,
                                            (vpBuffer.read_int16()) * finalScale)
                        
                        secondParams = vpBuffer.read_uint16()
                        vertex.weights[1] = (secondParams & 0x1ff) / 256
                        vertex.boneIDs[1] = (secondParams >> 10)

                        vertex.normals[1] = (vnBuffer.read_int8() / 64,
                                            vnBuffer.read_int8() / 64,
                                            vnBuffer.read_int8() / 64)
                        vertex.triangleFlag = vnBuffer.read_int8()

                    vertex.UV = (uvBuffer.read_int16() / 256, uvBuffer.read_int16() / 256)
                    
                    self.vertices.append(vertex)
            
            else:
                vpBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 0x0c), encoding='cp932')
                vnBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 4), encoding='cp932')
                uvBuffer = BinaryReader(br.read_bytes(self.vertexCount * 8), encoding='cp932')

                if tanBinFlag:
                    vtBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 4), encoding='cp932')
                    vbnBuffer = BinaryReader(br.read_bytes(self.deformableVerticesCount * 4), encoding='cp932')

                for i in range(self.vertexCount):
                    vertex = DeformableVertex()

                    stopBit = 0
                    i = 0
                    while(stopBit == 0):
                        vertex.positions[i] = ((vpBuffer.read_int16() * finalScale),
                                                    (vpBuffer.read_int16() * finalScale),
                                                    (vpBuffer.read_int16() * finalScale))
                        
                        vertex.weights[i] = vpBuffer.read_int16() / 256
                        stopBit = vpBuffer.read_int16()
                        vertex.boneIDs[i] = vpBuffer.read_int16()

                        vertex.normals[i] =  (vnBuffer.read_int8() / 64,
                                            vnBuffer.read_int8() / 64,
                                            vnBuffer.read_int8() / 64)
                        
                        vertex.triangleFlag = vnBuffer.read_int8()

                        i += 1

                    vertex.UV = (uvBuffer.read_int32() / 65536, uvBuffer.read_int32() / 65536)

                    self.vertices.append(vertex)
                

    def finalize(self, chunks):
        self.material = chunks[self.materialID]


class unkMesh(BrStruct):
    def __init__(self):
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=64):
        self.materialID = br.read_uint32()
        self.sectionCount = br.read_uint32()
        self.vertices = list()
        self.normals = list()
        self.uvs = list()
        self.colors = list()
        self.triangleFlags = list()
        self.vertexWeights = list()
        self.boneIDs = list()
        self.triangleIndices = list()

        for i in range(self.sectionCount):
            sectionFlags = br.read_uint8()
            sectionType = br.read_uint8()
            br.seek(2, 1)
            count = br.read_uint32()
            vertexScale = br.read_float()
            finalScale = ((vertexScale / 256)  / 16) * 0.01
            if sectionType == 0:
                for i in range(count):
                    #vertex normals
                    self.normals.append((br.read_int8() / 64, br.read_int8() / 64, br.read_int8() / 64))
            
            elif sectionType == 1:
                #uvs
                for i in range(count):
                    self.uvs.append((br.read_int16() / 256, br.read_int16() / 256))
            
            elif sectionType == 7:
                #triangle flags
                for i in range(count):
                    self.triangleFlags.append(br.read_uint8())

            
            elif sectionType == 8:
                #triangle indices
                for i in range(count):
                    self.triangleIndices.append(br.read_uint16())


            elif sectionType == 32:
                #vertex positions and weights
                if sectionFlags == 33:
                    for i in range(count):
                        vertex = DeformableVertex()
                        vertex.positions[0] = ((br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale))
                        
                        vertParams = br.read_uint16()
                        vertex.boneIDs[0] = vertParams >> 10
                        vertex.weights[0] = (vertParams & 0x1ff) / 256
                        #print((vertParams & 0x1ff) / 256)

                        self.vertices.append(vertex)
                
                elif sectionFlags == 34:
                    for i in range(count//2):
                        vertex = DeformableVertex()

                        vertex.positions[0] = ((br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale))
                        vertParams = br.read_uint16()
                        vertex.boneIDs[0] = vertParams >> 10
                        vertex.weights[0] = (vertParams & 0x1ff) / 256

                        vertex.positions[1] = ((br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale),
                                            (br.read_int16() * finalScale))
                        vertParams = br.read_uint16()
                        vertex.boneIDs[1] = vertParams >> 10
                        vertex.weights[1] = (vertParams & 0x1ff) / 256

                        self.vertices.append(vertex)

            
            elif sectionType == 33:
                self.clumpIndex = br.read_uint32()
            
            br.align_pos(4)

    
    def finalize(self, chunks):
        self.material = chunks[self.materialID]
        self.clump = chunks[self.clumpIndex]
        self.lookupList = self.clump.boneIndices


class ccsModel(BrStruct):
    def __init__(self):
        self.index = 0
        self.name = ""
        self.path = ""
        self.type = "Model"
        self.clump = None
        self.parentBone = None
        self.vertexScale = 0
        self.modelType = 0
        self.modelFlags = 0
        self.meshCount = 0
        self.sourceFactor = 0
        self.boundingBox = None


    def __br_read__(self, br: BinaryReader, indexTable, version=0x110):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.vertexScale = br.read_float()
        self.modelType = br.read_uint8()
        self.modelFlags = br.read_uint8()
        self.meshCount = br.read_uint16()
        self.matFlags = br.read_uint16()
        self.unkFlags = br.read_int16()
        self.lookupListCount = br.read_uint8()
        self.extraFlags = br.read_uint8()
        self.tangentBinormalsFlag = br.read_uint16()

        #print(self.ModelType)

        if version > 0x110:
            self.outlineColor = br.read_uint8(4)
            self.outlineWidth = br.read_float()
        
        #print(f'LookupListCount = {self.LookupListCount}')
        if (self.modelType & 1 == 0) and (self.modelType & 4) and version > 0x111:
            self.lookupList = [br.read_uint8() for i in range(self.lookupListCount)]
            br.align_pos(4)
            #print(f'lookupTable = {self.LookupList}')
        else:
            self.lookupList = None

        self.meshes = list()
        if self.meshCount > 0:
            
            if self.modelType & ModelTypes.Deformable and not self.modelType & ModelTypes.TrianglesList:

                self.meshes = br.read_struct(DeformableMesh, self.meshCount, self.vertexScale, version, self.tangentBinormalsFlag)

            elif self.modelType == ModelTypes.ShadowMesh:
                self.meshes.append(br.read_struct(ShadowMesh))
            
            elif self.modelType & ModelTypes.TrianglesList:
                for i in range(self.meshCount):
                    self.meshes.append(br.read_struct(unkMesh, None, self.vertexScale))

            else:
                for i in range(self.meshCount):
                    rigidmesh = br.read_struct(RigidMesh, None, self.vertexScale, self.modelFlags, version)
                    self.meshes.append(rigidmesh)
    
    def finalize(self, chunks):
        if self.modelType & ModelTypes.TrianglesList:
                self.lookupList = self.clump.boneIndices
                self.lookupNames = [chunks[i].name for i in self.lookupList]
        
        elif self.modelType & ModelTypes.Deformable:
            if self.clump and self.lookupList:
                self.lookupList = [self.clump.boneIndices[i] for i in self.lookupList]
                self.lookupNames = [chunks[i].name for i in self.lookupList]
            else:
                self.lookupList = self.clump.boneIndices
                self.lookupNames = [chunks[i].name for i in self.lookupList]
        
        for mesh in self.meshes:
            if mesh:
                mesh.finalize(chunks)


class Vertex(BrStruct):
    def __init__(self, p=(0,0,0), n=(0,0,0), c=(1,1,1,1), uv=(0,0), scale = 256, flag=0):
        scale = ((scale / 256)  / 16) * 0.01

        self.position = (p[0] * scale,
                        p[1] * scale,
                        p[2] * scale)
        
        self.normal = (n[0] / 64, n[1] / 64,
                       n[2] / 64)

        self.color = c
        self.UV = (uv[0] / 256, (uv[1] / 256))
        self.triangleFlag = flag

class DeformableVertex:    
    def __init__(self):
        self.positions = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        self.normals = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        self.weights = [0, 0, 0, 0]
        self.UV = [0, 0]
        self.boneIDs = [0, 0, 0, 0]
        self.triangleFlag = 0
        self.multiWeight = False