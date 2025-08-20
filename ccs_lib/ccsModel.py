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
        self.parentIndex = 0
        self.materialIndex = 0
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.parent = None
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=64, modelFlags=0, version = 0x110, tanBinFlag = 0):
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
            for vertex in self.vertices:
                vertex.color = [min(255, br.read_uint8() * 2) for i in range(4)]
        if ((modelFlags & 4) == 0):
            if version >= 0x125:
                for v in self.vertices:
                    v.UV = (br.read_int32() / 65536, br.read_int32() / 65536)

            else:
                for v in self.vertices:
                    v.UV = (br.read_int16() / 256, br.read_int16() / 256)

        if tanBinFlag:
            for vertex in self.vertices:
                vertex.Tangent = tuple((map(lambda x: x/64, br.read_int8(3))))
                vertex.Tangent_triangleFlag = br.read_int8()
                vertex.Binormal = tuple((map(lambda x: x/64, br.read_int8(3))))
                vertex.Binormal_triangleFlag = br.read_int8()


    def __br_write__(self, br: BinaryReader, vertexScale=64, modelFlags=0, version = 0x110, tanBinFlag = 0):
        br.write_uint32(self.parentIndex)
        br.write_uint32(self.materialIndex)
        br.write_uint32(self.vertexCount)

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        posCount = 0
        normCount = 0
        colCount = 0
        uvCount = 0
        vpBuffer = BinaryReader(encoding='cp932')
        vnBuffer = BinaryReader(encoding='cp932')
        vcBuffer = BinaryReader(encoding='cp932')
        uvBuffer = BinaryReader(encoding='cp932')
        vtBuffer = BinaryReader(encoding='cp932')
        vbnBuffer = BinaryReader(encoding='cp932')
        
        for v in range(self.vertexCount):
            posCount += 1
            v_pos = self.vertices[v].position
            vpBuffer.write_int16(round(v_pos[0] / finalScale))
            vpBuffer.write_int16(round(v_pos[1] / finalScale))
            vpBuffer.write_int16(round(v_pos[2] / finalScale))

            normCount += 1
            v_norm = self.vertices[v].normal
            vnBuffer.write_int8(int(v_norm[0] * 64))
            vnBuffer.write_int8(int(v_norm[1] * 64))
            vnBuffer.write_int8(int(v_norm[2] * 64))
            vnBuffer.write_int8(self.vertices[v].triangleFlag)

            if ((modelFlags & 2) == 0):
                colCount += 1
                v_col = self.vertices[v].color
                vcBuffer.write_uint8(round(v_col[0] / 2))
                vcBuffer.write_uint8(round(v_col[1] / 2))
                vcBuffer.write_uint8(round(v_col[2] / 2))
                vcBuffer.write_uint8(round(v_col[3] / 2))

            if ((modelFlags & 4) == 0):
                uvCount += 1
                if version >= 0x125:
                    print(f'UV VERSION: >= 0x125 UV: {self.vertices[v].UV[0]}, {self.vertices[v].UV[1]}')
                    uvBuffer.write_int32(int(self.vertices[v].UV[0] * 65536))
                    uvBuffer.write_int32(int(self.vertices[v].UV[1] * 65536))
                else:
                    uvBuffer.write_int16(int(self.vertices[v].UV[0] * 256))
                    uvBuffer.write_int16(int(self.vertices[v].UV[1] * 256))

            if tanBinFlag:
                print(f'TODO: Export meshes mesh tan & Bin')

        print(f'RigidMesh version {version} posCount {posCount} normCount {normCount} colCount {colCount} uvCount {uvCount}')

        br.write_bytes(bytes(vpBuffer.buffer()))
        # br.align_pos(4)
        br.align(4)
        br.write_bytes(bytes(vnBuffer.buffer()))
        br.write_bytes(bytes(vcBuffer.buffer()))
        br.write_bytes(bytes(uvBuffer.buffer()))
        if tanBinFlag:
            br.write_bytes(bytes(vtBuffer.buffer()))
            br.write_bytes(bytes(vbnBuffer.buffer()))

    
    def finalize(self, chunks):
        self.material = chunks.get(self.materialIndex)
        
        

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


    def __br_write__(self, br: BinaryReader, vertexScale=64):
        #br.write_uint32(0)
        #br.write_uint32(0)
        br.write_uint32(self.vertexCount)
        br.write_uint32(self.triangleVerticesCount)

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        for v in range(self.vertexCount):
            br.write_int16(round(self.vertices[v].position[0] / finalScale))
            br.write_int16(round(self.vertices[v].position[1] / finalScale))
            br.write_int16(round(self.vertices[v].position[2] / finalScale))

        # br.align_pos(4)
        br.align(4)
        for v in range((self.triangleVerticesCount // 3)):
            br.write_int32(self.triangles[v][0])
            br.write_int32(self.triangles[v][1])
            br.write_int32(self.triangles[v][2])


    def finalize(self, chunks):
        pass

    

class DeformableMesh(BrStruct):
    def __init__(self):
        self.materialIndex = 0
        self.material = None
        self.vertexCount = 0
        self.deformableVerticesCount = 0
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=256, version = 0x100, tanBinFlag = 0):
        self.materialIndex = br.read_uint32()
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


    def __br_write__(self, br: BinaryReader, vertexScale=256, version = 0x120, tanBinFlag = 0):
        br.write_uint32(self.materialIndex)
        br.write_uint32(self.vertexCount)
        br.write_uint32(self.deformableVerticesCount)
        #print(f'Write DeformableMesh vertexCount: {self.vertexCount}, deformableVerticesCount: {self.deformableVerticesCount}')

        finalScale = ((vertexScale / 256)  / 16) * 0.01
        #print(f'exportScale: {finalScale}')

        #Single weight vertices
        if not self.deformableVerticesCount:
            br.write_uint32(self.vertices[0].boneIDs[0])

            for v in range(self.vertexCount):
                v_pos = self.vertices[v].positions[0]
                br.write_int16(int(v_pos[0] / finalScale))
                br.write_int16(int(v_pos[1] / finalScale))
                br.write_int16(int(v_pos[2] / finalScale))

            # br.align_pos(4)
            br.align(4)

            for v in range(self.vertexCount):
                v_norm = self.vertices[v].normals[0]
                br.write_int8(int(v_norm[0] * 64))
                br.write_int8(int(v_norm[1] * 64))
                br.write_int8(int(v_norm[2] * 64))
                br.write_int8(self.vertices[v].triangleFlag)

            if version > 0x125:
                for v in self.vertices:
                    br.write_int32(int(v.UV[0] * 65536))
                    br.write_int32(int(v.UV[1] * 65536))

            else:
                for v in self.vertices:
                    br.write_int16(int(v.UV[0] * 256))
                    br.write_int16(int(v.UV[1] * 256))
            
            if tanBinFlag:
                print(f'TODO: Export meshes mesh tan & Bin')


        else: #multiple weights vertices
            posCount = 0
            normCount = 0
            uvCount = 0
            vpBuffer = BinaryReader(encoding='cp932')
            vnBuffer = BinaryReader(encoding='cp932')
            uvBuffer = BinaryReader(encoding='cp932')
            vtBuffer = BinaryReader(encoding='cp932')
            vbnBuffer = BinaryReader(encoding='cp932')

            if version < 0x125:
                #print(f'self.vertices: {len(self.vertices)}')
                for v in range(self.vertexCount):
                    posCount += 1
                    v_pos = self.vertices[v].positions[0]
                    vpBuffer.write_int16(int(v_pos[0] / finalScale))
                    vpBuffer.write_int16(int(v_pos[1] / finalScale))
                    vpBuffer.write_int16(int(v_pos[2] / finalScale))
                    boneID = self.vertices[v].boneIDs[0]
                    weight = self.vertices[v].weights[0]
                    #vertParams = (boneID << 10) | int(weight * 256) | (1 << 9)
                    vertParams = (boneID << 10) | int(weight * 256)
                    #print(f'vertParams: {vertParams}')
                    if self.vertices[v].multiWeight:
                        vertParams &= ~(1 << 9)
                    else:
                        vertParams |= (1 << 9)

                    #print(f'vertParams: {vertParams}')
                    vpBuffer.write_uint16(vertParams)

                    if self.vertices[v].multiWeight:
                        v_pos = self.vertices[v].positions[1]
                        vpBuffer.write_int16(int(v_pos[0] / finalScale))
                        vpBuffer.write_int16(int(v_pos[1] / finalScale))
                        vpBuffer.write_int16(int(v_pos[2] / finalScale))
                        boneID = self.vertices[v].boneIDs[1]
                        weight = self.vertices[v].weights[1]
                        secondParams = (boneID << 10) | int(weight * 256)
                        #print(f'vertParams: {secondParams}')
                        secondParams |= (1 << 9)
                        vpBuffer.write_uint16(secondParams)
                    #print(f"v.position: {posCount} weights {len(self.vertices[v].positions)} {len(bytes(vpBuffer.buffer()))}")
                    
                    v_norm = self.vertices[v].normals[0]
                    normCount += 1
                    vnBuffer.write_int8(int(v_norm[0] * 64))
                    vnBuffer.write_int8(int(v_norm[1] * 64))
                    vnBuffer.write_int8(int(v_norm[2] * 64))
                    vnBuffer.write_int8(self.vertices[v].triangleFlag)
                    
                    if self.vertices[v].multiWeight:
                        normCount += 1
                        #v_norm = self.vertices[v].normals[1]
                        v_norm = self.vertices[v].normals[0]
                        vnBuffer.write_int8(int(v_norm[0] * 64))
                        vnBuffer.write_int8(int(v_norm[1] * 64))
                        vnBuffer.write_int8(int(v_norm[2] * 64))
                        vnBuffer.write_int8(self.vertices[v].triangleFlag)
                    
                    uvBuffer.write_int16(int(self.vertices[v].UV[0] * 256))
                    uvBuffer.write_int16(int(self.vertices[v].UV[1] * 256))
                    uvCount += 1

            else:
                for v in range(self.vertexCount):
                    posCount += 1
                    for i in range(len(self.vertices[v].positions)):
                        v_pos = self.vertices[v].positions[i]
                        #print(f'self.vertex: {v} posCount {len(self.vertices[v].positions)}')
                        vpBuffer.write_int16(int(v_pos[0] / finalScale))
                        vpBuffer.write_int16(int(v_pos[1] / finalScale))
                        vpBuffer.write_int16(int(v_pos[2] / finalScale))
                        vpBuffer.write_int16(int(self.vertices[v].weights[i] * 256))

                        if i != len(self.vertices[v].positions) - 1:
                            vpBuffer.write_int16(0)
                        else:
                            vpBuffer.write_int16(1)

                        vpBuffer.write_int16(self.vertices[v].boneIDs[i])

                        normCount += 1
                        v_norm = self.vertices[v].normals[i]
                        vnBuffer.write_int8(int(v_norm[0] * 64))
                        vnBuffer.write_int8(int(v_norm[1] * 64))
                        vnBuffer.write_int8(int(v_norm[2] * 64))
                        vnBuffer.write_int8(self.vertices[v].triangleFlag)

                        if tanBinFlag:
                            v_tan = self.vertices[v].tangents[i]
                            vnBuffer.write_int8(int(v_tan[0] * 64))
                            vnBuffer.write_int8(int(v_tan[1] * 64))
                            vnBuffer.write_int8(int(v_tan[2] * 64))
                            vnBuffer.write_int8(0)

                            v_bin = self.vertices[v].tangents[i]
                            vnBuffer.write_int8(int(v_bin[0] * 64))
                            vnBuffer.write_int8(int(v_bin[1] * 64))
                            vnBuffer.write_int8(int(v_bin[2] * 64))
                            vnBuffer.write_int8(0)

                    
                    uvBuffer.write_int32(int(self.vertices[v].UV[0] * 65536))
                    uvBuffer.write_int32(int(self.vertices[v].UV[1] * 65536))
                    uvCount += 1

            br.write_bytes(bytes(vpBuffer.buffer()))
            br.write_bytes(bytes(vnBuffer.buffer()))
            br.write_bytes(bytes(uvBuffer.buffer()))
            if tanBinFlag:
                br.write_bytes(bytes(vtBuffer.buffer()))
                br.write_bytes(bytes(vbnBuffer.buffer()))


    def finalize(self, chunks):
        self.material = chunks.get(self.materialIndex)


class unkMesh(BrStruct):
    def __init__(self):
        self.materialIndex = 0
        self.material = None
        self.vertexCount = 0
        self.unk = 0
        self.vertices = []
    def __br_read__(self, br: BinaryReader, vertexScale=64):
        self.materialIndex = br.read_uint32()
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
        self.material = chunks.get(self.materialIndex)
        self.clump = chunks.get(self.clumpIndex)
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
        self.matFlags1 = br.read_uint8()
        self.matFlags2 = br.read_uint8()
        self.unkFlags = br.read_int16()
        self.lookupListCount = br.read_uint8()
        self.extraFlags = br.read_uint8()
        self.tangentBinormalsFlag = br.read_uint16()

        #print(self.ModelType)

        if version > 0x110:
            self.outlineColor = br.read_uint8(4)
            self.outlineWidth = br.read_float()
        
        #print(f'LookupListCount = {self.LookupListCount}')
        # Replaced 'and' with 'or' to import some models needs to be looked into
        # Example from UN3 d18_101e.ccs
        if (self.modelType & 1 == 0) and (self.modelType & 4) and version > 0x111:
        #if (self.modelType & 1 == 0) or (self.modelType & 4) and version > 0x111:
            self.lookupList = [br.read_uint8() for i in range(self.lookupListCount)]
            br.align_pos(4)
            #print(f'lookupList = {self.lookupList}')
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
                    rigidmesh = br.read_struct(RigidMesh, None, self.vertexScale, self.modelFlags, version, self.tangentBinormalsFlag)
                    self.meshes.append(rigidmesh)
    

    def __br_write__(self, br: BinaryReader, version=0x120):
        #print(f'Write chunk index: {self.index} name: {self.name}')
        br.write_uint32(self.index)
        br.write_float(self.vertexScale)
        br.write_uint8(self.modelType)
        br.write_uint8(self.modelFlags)
        br.write_uint16(self.meshCount)
        br.write_uint8(self.matFlags1)
        br.write_uint8(self.matFlags2)
        br.write_uint16(self.unkFlags)
        br.write_uint8(self.lookupListCount)
        br.write_uint8(self.extraFlags)
        br.write_uint16(self.tangentBinormalsFlag)

        if version > 0x110:
            br.write_uint8(self.outlineColor)
            br.write_float(self.outlineWidth)

        if ((self.modelType & 1) == 0) and (self.modelType & 4) and version > 0x111:
            for i in range(self.lookupListCount):
                br.write_uint8(self.lookupList[i])
                
            # br.align_pos(4)
            br.align(4)

        if self.meshCount > 0:

            if self.modelType & ModelTypes.Deformable and not self.modelType & ModelTypes.TrianglesList:
                print(f'Write chunk index: {self.index} name: {self.name}')
                for mesh in self.meshes:
                    mesh: DeformableMesh
                    br.write_struct(mesh, self.vertexScale, version, self.tangentBinormalsFlag)
            
            elif self.modelType == ModelTypes.ShadowMesh:
                for mesh in self.meshes:
                    mesh: ShadowMesh
                    br.write_struct(mesh)
            
            elif self.modelType & ModelTypes.TrianglesList:
                print(f'TODO: Export meshes model type TrianglesList')

            else:
                self.meshes: RigidMesh
                br.write_struct(self.meshes, self.vertexScale, self.modelFlags, version, self.tangentBinormalsFlag)


    def finalize(self, chunks):
        if self.lookupList:
            self.lookuplistnames = [chunks.get(i).name for i in self.lookupList]
            #print(f'lookuplistnames = {self.lookuplistnames}')

        for mesh in self.meshes:
            mesh.finalize(chunks)


class Vertex(BrStruct):
    def __init__(self, p=(0,0,0), n=(0,0,0), c=(255,255,255,255), uv=(0,0), scale = 256, flag=0):
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
        self.tangents = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        self.weights = [0, 0, 0, 0]
        self.UV = [0, 0]
        self.boneIDs = [0, 0, 0, 0]
        self.triangleFlag = 0
        self.multiWeight = False
