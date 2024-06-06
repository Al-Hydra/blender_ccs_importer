from enum import IntFlag
from .utils.PyBinaryReader.binary_reader import *
class ModelTypes(IntFlag):
    Rigid1 = 0
    Rigid2   = 1
    Unk = 2
    Deformable = 4
    ShadowMesh = 8


class RigidMesh(BrStruct):
    def __init__(self):
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.parent = None
        self.vertices = []
    def __br_read__(self, br: BinaryReader, deformable=False, vertexScale=64, modelFlags=0, version = 0x110):
        if deformable:
            self.materialIndex = br.read_uint32()
            self.vertexCount = br.read_uint32()
            self.unk = br.read_uint32() #this could be the count of deformable vertices
            self.parentIndex = br.read_uint32()
        else:
            self.parentIndex = br.read_uint32()
            self.materialIndex = br.read_uint32()
            self.vertexCount = br.read_uint32()
        
        if self.vertexCount > 0x10000:
            exception = ValueError(f'VertexCount is greater than 0x10000: {self.vertexCount}, offset = {hex(br.pos())}')
            raise exception

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        self.vertices = [Vertex() for i in range(self.vertexCount)]

        #if modelFlags & 2 == 0: #useless check, causes issues with models that have a deformable mesh
        for i in range(self.vertexCount):
            self.vertices[i].position = ((br.read_int16() * finalScale),
                                        (br.read_int16() * finalScale),
                                        (br.read_int16() * finalScale))        
        br.align_pos(4)

        for i in range(self.vertexCount):
            self.vertices[i].normal = (br.read_int8() / 64,
                                        br.read_int8() / 64,
                                        br.read_int8() / 64)
            self.vertices[i].triangleFlag = br.read_uint8()

        if modelFlags & 2 == 0 and not deformable:
            for i in range(self.vertexCount):
                self.vertices[i].color = br.read_uint8(4)
        
        if modelFlags & 4 == 0:
            if version > 0x125:
                for i in range(self.vertexCount):
                    self.vertices[i].UV = br.read_uint32(2)
            else:
                for i in range(self.vertexCount):
                    self.vertices[i].UV = (br.read_int16() / 256, br.read_int16() / 256)
    
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
        #self.vertexPositions = [br.read_int16(3) for i in range(self.vertexCount)]
        for i in range(self.vertexCount):

            pos = (br.read_int16() / 16, br.read_int16() / 16, br.read_int16() / 16)

            self.vertices.append(Vertex(pos, (0, 0, 0), (0, 0, 0, 0), (0, 0), vertexScale))
        br.align_pos(4)
        self.triangles = [br.read_int32(3) for i in range((self.triangleVerticesCount // 3))]

    def finalize(self, chunks):
        pass

    

class DeformableMesh(BrStruct):
    def __init__(self):
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=256):
        self.materialID = br.read_uint32()
        #print(f'MaterialID = {self.MaterialID}')
        self.vertexCount = br.read_uint32() #This is the number of vertices that are actually used
        #print(f'VertexCount = {self.VertexCount}')

        self.totalVertexCount = br.read_uint32() #This is the total count of all vertices
                                                 #there are some duplicates because they store 1 vertex weight per position
                                                 #so if a vertex has 2 weights, it will be stored twice
        #print(f'TotalVertexCount = {self.TotalVertexCount}')
        self.vertices = list()

        finalScale = ((vertexScale / 256) * (0.0625 * 0.01))

        for i in range(self.vertexCount):

            vertex = DeformableVertex()

            vertex.positions[0] = ((br.read_int16() * finalScale),
                                        (br.read_int16() * finalScale),
                                        (br.read_int16() * finalScale))     

            vertParams = br.read_uint16()
            if vertParams == 0xFFFF:
                raise ValueError(f'Vertex {i} has a weight of 0xFFFF')
            elif vertParams == 0:
                raise ValueError(f'Vertex {i} has a weight of 0')
            
            #print(vertParams)

            vertex.boneIDs[0] = vertParams >> 10
            vertex.weights[0] = (vertParams & 0x1ff) / 256
            if vertex.weights[0] == 0:
                raise ValueError(f'Vertex {i} has a weight of 0')
            elif vertex.weights[0] > 1 or  vertex.weights[0] < 0:
                raise ValueError(f'Vertex {i} has a weight greater than 1 or less than 0')
            
            if ((vertParams >> 9) & 0x1) == 0:
                vertex.multiWeight = True
                vertex.positions[1] = ((br.read_int16()) * finalScale,
                                        (br.read_int16()) * finalScale,
                                        (br.read_int16()) * finalScale)
                secondParams = br.read_uint16()
                vertex.weights[1] = (secondParams & 0x1ff) / 256
                vertex.boneIDs[1] = (secondParams >> 10)
                if vertex.weights[1] > 1 or vertex.weights[1] < 0:
                    raise ValueError(f'Vertex {i} has a weight greater than 1 or less than 0')
            
            self.vertices.append(vertex)
                    
        for i in range(self.vertexCount):
            self.vertices[i].normals[0] = (br.read_int8() / 64,
                                             br.read_int8() / 64,
                                             br.read_int8() / 64)

            self.vertices[i].triangleFlag = br.read_int8()
            if self.vertices[i].multiWeight:
                self.vertices[i].normals[1] = (br.read_int8() / 64,
                                                br.read_int8() / 64,
                                                br.read_int8() / 64)
                br.read_int8()
        
        for i in range(self.vertexCount):
            self.vertices[i].UV = (br.read_int16() / 256, br.read_int16() / 256)
        
        
        '''for i, v in enumerate(self.Vertices):
            v_dict = dict()
            v_dict['Position1'] = v.Positions[0]
            v_dict['Position2'] = v.Positions[1]
            v_dict['Normal1'] = v.Normals[0]
            v_dict['Normal2'] = v.Normals[1]
            v_dict['UV'] = v.UV
            v_dict['BoneID1'] = v.BoneIDs[0]
            v_dict['BoneID2'] = v.BoneIDs[1]
            v_dict['Weight1'] = v.Weights[0]
            v_dict['Weight2'] = v.Weights[1]
            v_dict['TriangleFlag'] = v.TriangleFlag
            v_dict['MultiWeight'] = v.MultiWeight
            vertex_list[i] = v_dict
        
        with open('vertex_list.json', 'w') as f:
            json.dump(vertex_list, f, indent=4)
    '''
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
            br.read_uint8()
            sectionType = br.read_uint8()
            br.seek(2, 1)
            count = br.read_uint32()
            vertexScale = br.read_float()
            finalScale = ((vertexScale / 256)  / 16) * 0.01
            if sectionType == 0:
                for i in range(count):
                    #vertex normals
                    self.normals.append((br.read_int8() / 64, br.read_int8() / 64, br.read_int8() / 64))

                '''align_amount = 4 - ((3 * count) % 4)
                br.seek(align_amount, 1)'''
                br.align_pos(4)
            
            elif sectionType == 1:
                #uvs
                for i in range(count):
                    self.uvs.append((br.read_int16() / 256, br.read_int16() / 256))

                '''align_amount = 4 - ((4 * count) % 4)
                br.seek(align_amount, 1)'''
                br.align_pos(4)
            
            elif sectionType == 7:
                #triangle flags
                for i in range(count):
                    self.triangleFlags.append(br.read_uint8())

                br.align_pos(4)
            
            elif sectionType == 8:
                #triangle indices
                for i in range(count):
                    self.triangleIndices.append(br.read_uint16())

                br.align_pos(4)

            elif sectionType == 32:
                #vertex positions and weights
                for i in range(count):
                    self.vertices.append((br.read_int16() * finalScale, br.read_int16() * finalScale, br.read_int16() * finalScale))
                    vertParams = br.read_uint16()
                    self.boneIDs.append(vertParams >> 10)
                    self.vertexWeights.append((vertParams & 0x1ff) / 256)

                '''align_amount = 4 - ((8 * count) % 4)
                br.seek(align_amount, 1)'''
                br.align_pos(4)
            
            elif sectionType == 33:
                #unk
                br.read_uint16(count)
                br.align_pos(4)

    
    def finalize(self, chunks):
        self.material = chunks[self.materialID]


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
        self.lookupListCount = br.read_uint32()
        #print(self.ModelType)

        if version > 0x110:
            self.outlineColor = br.read_uint8(4)
            self.outlineWidth = br.read_float()
        
        #print(f'LookupListCount = {self.LookupListCount}')
        if self.modelType & ModelTypes.Deformable and version > 0x111:
            self.lookupList = [br.read_uint8() for i in range(self.lookupListCount)]
            br.align_pos(4)
            #print(f'lookupTable = {self.LookupList}')
        else:
            self.lookupList = None

        self.meshes = list()
        if self.meshCount > 0:
            
            if self.modelType & ModelTypes.Deformable and not self.modelType & ModelTypes.Unk:
                for i in range(self.meshCount-1):
                    self.meshes.append(br.read_struct(RigidMesh, None, True, self.vertexScale, self.modelFlags, version))
                
                self.meshes.append(br.read_struct(DeformableMesh, None, self.vertexScale))

            elif self.modelType == ModelTypes.ShadowMesh:
                self.meshes.append(br.read_struct(ShadowMesh))
            
            elif self.modelType & ModelTypes.Unk:
                for i in range(self.meshCount):
                    self.meshes.append(br.read_struct(unkMesh, None, self.vertexScale))

            else:
                for i in range(self.meshCount):
                    rigidmesh = br.read_struct(RigidMesh, None, False, self.vertexScale, self.modelFlags, version)
                    self.meshes.append(rigidmesh)
    
    def finalize(self, chunks):
        if self.modelType == ModelTypes.ShadowMesh:
            self.meshes[0].finalize(chunks)
        
        if self.modelType == ModelTypes.Deformable:
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
        scale = (scale / 256) * 0.01

        self.position = (p[0] * scale,
                        p[1] * scale,
                        p[2] * scale)
        
        self.normal = (n[0] / 64, n[1] / 64,
                       n[2] / 64)

        self.color = c
        self.UV = (uv[0] / 256, (uv[1] / 256))
        self.triangleFlag = flag

class DeformableVertex:
    '''def __init__(self, p=(0,0,0), n=(0,0,0), w=(0,0,0,0), uv=(0,0), b=(0,0,0,0), triangleflag = 0, scale = 256, lookup= None):
        scale = ((scale / 256) * (0.0625 * 0.01))
        #scale = scale * 0.00000225
        self.Positions = [(p[0][0] * scale, p[0][1] * scale, p[0][2] * scale),
                            (p[1][0] * scale, p[1][1] * scale, p[1][2] * scale),
                            (p[2][0] * scale, p[2][1] * scale, p[2][2] * scale),
                            (p[3][0] * scale, p[3][1] * scale, p[3][2] * scale)]
        
        self.Normals = ((n[0][0] / 127, n[0][1] / 127, n[0][2] / 127),
                        (n[1][0] / 127, n[1][1] / 127, n[1][2] / 127),
                        (n[2][0] / 127, n[2][1] / 127, n[2][2] / 127),
                        (n[3][0] / 127, n[3][1] / 127, n[3][2] / 127))
        
        self.Weights = [w[0] / 256, w[1] / 256, w[2] / 256, w[3] / 256]
        self.UV = [uv[0] / 256, uv[1] / 256]
        self.Bones = (lookup[b[0]], lookup[b[1]], lookup[b[2]], lookup[b[3]])
        self.TriangleFlag = triangleflag'''
    
    def __init__(self):
        self.positions = [(0, 0, 0), (0, 0, 0)]
        self.normals = [(0, 0, 0), (0, 0, 0)]
        self.weights = [0, 0]
        self.UV = [0, 0]
        self.boneIDs = [0, 0]
        self.triangleFlag = 0
        self.multiWeight = False