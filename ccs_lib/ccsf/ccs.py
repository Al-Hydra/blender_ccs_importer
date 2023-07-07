import struct, math
#from PIL import Image
from .brccs import *
from .utils.bmp import *
from concurrent.futures import ThreadPoolExecutor
from mathutils import Vector, Matrix, Euler, Quaternion
from math import radians, pi
from itertools import zip_longest


class CCSFile:
    def __init__(self, filename: str, version: int, paths: list[str], names: list[str], chunks = None):
        self.filename = filename
        self.version = version
        global ccsf_version  # I need to find a better way to do this
        ccsf_version = self.version
        self.ChunksDict = chunks
    

'''class CCSChunk:
    def __init__(self, chunk: BrChunk, Refs: ChunkRefs = None):
        self.Name = Refs.Names[chunk.Index][0]
        self.Path = Refs.Names[chunk.Index][1]
        self.Type = CCSTypes(chunk.Type).name
        self.Index = chunk.Index
        self.BrChunk = chunk
        self.Data = chunk.Data'''
    
    
class Clump(CCSChunk):
    def init_data(self, chunk: BrClump, Refs: ChunkRefs, chunks: ChunksDict):
        self.bone_names = []
        self.bones = {}
        #print(self.bones)
        
        for b, i in zip(chunk.bones, chunk.bone_indices):
            self.bones[Refs.Names[i][0]] = Bone(b, i, self, Refs, chunks)
            self.bone_names.append(Refs.Names[i][0])
                

class Bone:
    def __init__(self, bone: BrBone, index, clump, Refs: ChunkRefs, chunks: ChunksDict):
        self.name = Refs.Names[index][0]
        self.index = index
        self.clump = clump
        
        bone_obj = chunks.get_chunk_alt(self.index)
        bone_obj.__class__ = Object
        bone_obj.init_data(bone_obj.Data, Refs, chunks)

        self.parent = self.clump.bones.get(bone_obj.ParentObject)
        self.model = bone_obj.Model
        if self.model:
            self.modelchunk = chunks[self.model]
            self.modelchunk.__class__ = Model
            self.modelchunk.clump_references(clump, self)

            self.shadow = bone_obj.Shadow

        self.position = Vector(bone.pos) * 0.01
        self.scale = Vector(bone.scale)
        self.rotation = (radians(bone.rot[0]), radians(bone.rot[1]), radians(bone.rot[2]))
        self.matrix = Matrix() #We'll calculate the actual matrix in blender
        

class Object(CCSChunk):
    def init_data(self, chunk: BrObject, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.ParentObject = Refs.Names[chunk.ParentObjectID][0]
        self.Model = Refs.Names[chunk.ModelID][0]
        self.Shadow = Refs.Names[chunk.ShadowID][0]
        if ccsf_version > 0x120:
            self.unk = chunk.unk #could be footsteps chunk


class DummyObject(CCSChunk):
    def init_data(self, chunk: BrObject, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.ParentObject = Refs.Names[chunk.ParentObjectID][0]
        self.Model = Refs.Names[chunk.ModelID][0]
        self.Shadow = Refs.Names[chunk.ShadowID][0]
        

class External(CCSChunk):
    def init_data(self, chunk: BrExternal, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.ParentObject = chunks.get(chunk.ParentID, None)
        self.ParentIndex = chunk.ParentID
        self.Object = chunks.get(chunk.ParentID, None)
        self.ObjectIndex = chunk.ObjectID


class Color_Palette(CCSChunk):
    def init_data(self, chunk: BrColor_Palette, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.BlitGroup = chunk.BlitGroup
        self.ColorCount = chunk.ColorCount
        #self.Palette = chunk.Palette
        self.PaletteData = chunk.PaletteData
        

class Material(CCSChunk):
    def init_data(self, chunk: BrMaterial, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.Texture = chunks.get(chunk.TextureID, None)
        self.Alpha = chunk.Alpha


class Texture(CCSChunk):
    def init_data(self, chunk: BrTexture, Refs: ChunkRefs = None, chunks: ChunksDict = None):
        self.ColorTable: Color_Palette = chunks[chunk.ClutID]
        self.BlitGroup = chunk.BlitGroup
        self.TextureFlags = chunk.TextureFlags
        self.TextureType = TextureTypes(chunk.TextureType).name
        self.MipmapsCount = chunk.MipmapsCount
        self.Width = chunk.ActualWidth
        self.Height = chunk.ActualHeight

        self.TextureData = chunk.TextureData

        if self.TextureType == 'Indexed8':
            self.Image = I8toBMP(self.Width, self.Height, self.TextureData, self.ColorTable.PaletteData)
        elif self.TextureType == 'Indexed4':
            self.Image = I4toBMP(self.Width, self.Height, self.TextureData, self.ColorTable.PaletteData)


class Model(CCSChunk):
    def clump_references(self, clump, bone):
        self.clump = clump
        self.ParentBone = bone

    def init_data(self, chunk: BrModel, Refs: ChunkRefs, chunks: ChunksDict):
        start = time.perf_counter()
        self.VertexScale = chunk.VertexScale
        self.ModelType = ModelTypes(chunk.ModelType).name
        #print(self.ModelType)
        self.MeshFlags = chunk.MeshFlags
        self.MeshCount = chunk.MeshCount
        self.SourceFactor = chunk.SourceFactor
        self.DestinationFactor = chunk.DestinationFactor
        self.UnkFlags = chunk.UnkFlags
        #if self.MeshCount:

        if ccsf_version > 0x110:
            self.OutlineColor = chunk.OutlineColor
            self.OutlineWidth = chunk.OutlineWidth

            self.LookupList = list()

        #get clump chunk if it exists
        if hasattr(self, 'clump') and chunk.LookupListCount > 0 and ccsf_version > 0x110:
            self.LookupList = [self.clump.bone_names[i] for i in chunk.LookupList]      
        else:
            self.LookupList = Refs.Names
        
        def _process_mesh(self, mesh):
            if self.ModelType == "Rigid1" or self.ModelType == "Rigid2":
                return RigidMesh(mesh,self.VertexScale, Refs, chunks)

            elif self.ModelType == "ShadowMesh":
                return ShadowMesh(mesh, Refs)

            elif self.ModelType == "Deformable":
                if isinstance(mesh, BrRigidMesh):
                    return RigidMeshDeformable(mesh, Refs, self.LookupList, self.VertexScale, chunks)
                    
                else:
                    if isinstance(mesh, BrDeformableMesh):
                        return DeformableMesh(mesh, Refs, self.LookupList, self.VertexScale, chunks)
        
        
        if self.MeshCount > 0:
            self.meshes = [_process_mesh(self,mesh) for mesh in chunk.Meshes]

        else:
            self.meshes = None


class RigidMesh:
    def __init__(self, mesh: BrRigidMesh, vertex_scale, Refs: ChunkRefs = None, chunks = None):
        #some references are only exist in the string table
        #TODO Make it so the chunks dict returns the name if the chunk is not found
        self.Parent = Refs.Names[mesh.ParentID][0]
        self.Material = chunks[mesh.MaterialID]
        self.VertexCount = mesh.VertexCount
        self.Vertices = list()
        self.Triangles = list()

        Direction = 1
        for i in range(mesh.VertexCount):
            V = Vertex(p = mesh.Vertices[i].Position,
                        n = mesh.Vertices[i].Normal,
                        c = mesh.Vertices[i].Color,
                        uv = mesh.Vertices[i].UV,
                        scale= vertex_scale,
                        triangleflag=mesh.Vertices[i].TriangleFlag)
            
            #Triangles
            Flag = V.TriangleFlag
            
            if Flag == 1:
                Direction = 1
            elif Flag == 2:
                Direction = -1
            
            if Flag == 0:
                if Direction == 1:
                    self.Triangles.append((i-2, i-1, i))
                elif Direction == -1:
                    self.Triangles.append((i, i-1, i-2))

                #we need to flip the direction for the next face
                Direction *= -1
            self.Vertices.append(V)


class RigidMeshDeformable:
    def __init__(self, mesh: BrRigidMesh, Refs, lookup_list: list[int], vertex_scale: float, chunks):
        if lookup_list:
            self.Parent = lookup_list[mesh.ParentID]    
        else:
            self.Parent = Refs.Names[mesh.ParentID][0]
            
        self.Material = chunks[mesh.MaterialID]
        self.VertexCount = mesh.VertexCount
        self.Vertices = list()
        self.Triangles = list()

        Direction = 1
        for i in range(mesh.VertexCount):
            self.Vertices.append(Vertex(p = mesh.Vertices[i].Position,
                                        n = mesh.Vertices[i].Normal,
                                        uv = mesh.Vertices[i].UV,
                                        scale = vertex_scale,
                                        triangleflag = mesh.Vertices[i].TriangleFlag))
            #Triangles
            Flag = self.Vertices[i].TriangleFlag

            if Flag == 1:
                Direction = 1
            elif Flag == 2:
                Direction = -1
            
            if Flag == 0:
                if Direction == 1:
                    self.Triangles.append((i-2, i-1, i))
                elif Direction == -1:
                    self.Triangles.append((i, i-1, i-2))
                
                #we need to flip the direction for the next face
                Direction *= -1

class DeformableMesh:
    def __init__(self, mesh: BrDeformableMesh, Refs: ChunkRefs = None, lookup_list: list[int] = None, vertex_scale: float = 1.0, chunks = None):
        self.Material = chunks[mesh.MaterialID]
        self.VertexCount = mesh.VertexCount
        self.Vertices = list()
        self.Triangles = list()
       
        Direction = 1
        for i in range(mesh.VertexCount):
            self.Vertices.append(DeformableVertex(mesh.Vertices[i].Positions,
                                                mesh.Vertices[i].Normals,
                                                mesh.Vertices[i].Weights,
                                                mesh.Vertices[i].UV,
                                                mesh.Vertices[i].BoneIDs,
                                                mesh.Vertices[i].TriangleFlag,
                                                vertex_scale,
                                                lookup_list))
        
        #Triangles
            Flag = self.Vertices[i].TriangleFlag
            
            if Flag == 1:
                Direction = 1
            elif Flag == 2:
                Direction = -1
            
            if Flag == 0:
                if Direction == 1:
                    self.Triangles.append((i, i-1, i-2))
                elif Direction == -1:
                    self.Triangles.append((i-2, i-1, i))
                
                #we need to flip the direction for the next face
                Direction *= -1

        #dump vertex data
        '''vertex_dict = dict()
        for i, v in enumerate(self.Vertices):
            temp_dict = dict()
            temp_dict['Position1'] = v.Positions[0]
            temp_dict['Position2'] = v.Positions[1]
            temp_dict['Normal1'] = v.Normals[0]
            temp_dict['Normal2'] = v.Normals[1]
            temp_dict['Weight1'] = v.Weights[0]
            temp_dict['Weight2'] = v.Weights[1]
            temp_dict['UV'] = v.UV
            temp_dict['BoneID1'] = v.Bones[0]
            temp_dict['BoneID2'] = v.Bones[1]
            temp_dict['TriangleFlag'] = v.TriangleFlag
            vertex_dict[i] = temp_dict
        
        with open('vertex_converted.json', 'w') as f:
            json.dump(vertex_dict, f, indent=4)'''
            



class ShadowMesh:
    def __init__(self, mesh: BrShadowMesh, Refs: ChunkRefs = None):
        self.Vertices = [Vertex(mesh.VertexPositions[0])]
        self.Triangles = mesh.Triangles


class Vertex:
    def __init__(self, p=(0,0,0), n=(0,0,0), c=(0,0,0,0), uv=(0,0), scale = 256, triangleflag=0):
        #scale = scale * 0.00000225
        scale = ((scale / 256) * (0.0625 * 0.01))
        self.Position = (p[0] * scale,
                        p[1] * scale,
                        p[2] * scale)
        
        self.Normal = (n[0] / 64, n[1] / 64,
                       n[2] / 64)

        self.Color = (0, 0, 0, 0)
        self.UV = (uv[0] / 256, (uv[1] / 256))
        self.TriangleFlag = triangleflag

class DeformableVertex:
    def __init__(self, p, n, w, uv, b, triangleflag, scale, lookup= None):
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
        #print(self.Bones)
        self.TriangleFlag = triangleflag
        

class MeshFlags(IntFlag):
    NoColor = 0x2
    Morphable = 0x4
    Outline = 0x8
    Color = 0x10
    Unk = 0x20 #Vertex Colors?
