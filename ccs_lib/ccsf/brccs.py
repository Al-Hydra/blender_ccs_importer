import struct, array,time, json
from enum import Enum, IntFlag
from math import pi
from .utils.PyBinaryReader.binary_reader import *


class CCSFVersions(Enum):
    VER1 = 0x110
    VER2 = 0x120
    VER3 = 0x125


class CCSTypes(Enum):
    Header = 0x0001
    StringTable = 0x0002
    Null = 0x0003
    Stream = 0x0005
    Object = 0x0100
    Material = 0x0200
    Texture = 0x0300
    Color_Palette = 0x0400
    Camera = 0x0500
    Light = 0x0600
    Animation = 0x0700
    Model = 0x0800
    Clump = 0x0900
    External = 0x0a00
    HitModel = 0x0b00
    Bounding_Box = 0x0c00
    Particle = 0x0d00
    Effect = 0x0e00
    Blit_Group = 0x1000
    FrameBuffer_Page = 0x1100
    FrameBuffer_Rect = 0x1200
    Dummy_Position = 0x1300
    Dummy_Position_Rotation = 0x1400
    Layer = 0x1700
    Shadow = 0x1800
    Morpher = 0x1900
    DummyObject = 0x2000
    PCM_Audio = 0x2200
    Binary_Blob = 0x2400
    EOF = 0xff01


class BrCCSFile(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.Header = br.read_struct(BrHeader)
        self.ChunkRefs = br.read_struct(ChunkRefs)
        self.BrChunks = [br.read_struct(Null)]
        
        while not br.eof():
            self.BrChunks.append(br.read_struct(CCSChunk, None, self.ChunkRefs))
    
    def __br_write__(self, br: BinaryReader, ccs: 'CCSFile'):
        #write the chunks
        chunks_buf = BinaryReader(bytearray(), Endian.LITTLE, 'cp932')
        chunk_dict = ChunksDict()
        chunk_refs: ChunkRefs = ChunkRefs()
        index = 0
        for chunk in ccs.ChunksDict._dict.values():
            if chunk.Type == 'Clump':
                chunk.Index = index
                chunk_dict.add_chunk(chunk)
                chunk_refs.Paths = []
                chunk_refs.Names = []
                if chunk.Path not in chunk_refs.Paths:
                    chunk_refs.Paths.append(chunk.Path)
                chunk_refs.Names.append((chunk.Name, chunk_refs.Paths.index(chunk.Path)))
                chunks_buf.write_struct(chunk)
                index += 1
        
        ref_buf = BinaryReader(bytearray(), Endian.LITTLE, 'cp932')
        ref_buf.write_struct(chunk_refs)

        #write the header
        brheader = BrHeader()
        brheader.filename = ccs.filename
        brheader.version = ccs.version
        brheader.total_chunk_count = 0


        br.write_struct(brheader)
        br.extend(ref_buf.buffer())
        br.seek(len(ref_buf.buffer()), 1)
        #write the null chunk
        br.write_struct(Null())
        br.extend(chunks_buf.buffer())
        br.seek(len(chunks_buf.buffer()), 1)
        




class BrHeader(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.Type = br.read_uint32() & 0xFFFF
        assert self.Type == CCSTypes.Header.value
        self.Size = br.read_uint32() * 4
        self.Magic = br.read_str(4)
        self.FileName = br.read_str(32)
        self.Version = br.read_uint32()
        global ccsf_version
        ccsf_version = self.Version
        self.TotalChunkCount = br.read_uint32()
        br.seek(8, 1)


    def __br_write__(self, br: BinaryReader):
        br.write_uint16(CCSTypes.Header.value)
        br.write_uint16(0xCCCC)
        br.write_uint32(0x0D)
        br.write_str("CCSF")
        br.write_str_fixed(self.filename, 32)
        br.write_uint32(self.version)
        '''br.write_uint64(0)
        br.write_uint32(0)'''
        br.write_str_fixed('HydraBladeZ', 16)


class ChunkRefs(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.ccs_type = br.read_uint32() & 0xFFFF
        assert self.ccs_type == CCSTypes.StringTable.value

        self.Size = br.read_uint32() * 4

        ##start = time.perf_counter()

        self.PathsCount = br.read_uint32()
        self.NamesCount = br.read_uint32()

        self.Paths = [br.read_str(32) for i in range(self.PathsCount)]
        self.Names = [(br.read_str(30), self.Paths[br.read_uint16()]) for i in range(self.NamesCount)]


        #print(time.perf_counter() - start)
    

    def __br_write__(self, br: BinaryReader):
        with BinaryReader(bytearray(), Endian.LITTLE) as br_buf:
            for path in self.Paths:
                br_buf.write_str_fixed(path, 32)
            for ref in self.ChunkRefs:
                br_buf.write_str_fixed(ref, 30)
                br_buf.write_uint16(self.Paths.index(self.ChunkRefs[ref]))
            
            br.write_uint16(CCSTypes.StringTable.value)
            br.write_uint16(0xCCCC)
            br.write_uint32((br_buf.size() + 8) // 4)
            br.write_uint32(len(self.paths))
            br.write_uint32(len(self.names))
            br.extend(br_buf.buffer())
            br.seek(br_buf.size(), Whence.CUR)


class Null(BrStruct):
    def __init__(self):
        self.Name = ''
        self.Path = ''
        self.Type = 'Null'
        self.Index = 0
        self.Data = None
    
    def init_data(self, data, string_table: ChunkRefs, chunks: 'ChunksDict'):
        pass

    def __br_read__(self, br: BinaryReader):
        self.Type = br.read_uint32() & 0xFFFF
        assert self.Type == CCSTypes.Null.value
        self.Size = br.read_uint32()
    
    def __br_write__(self, br: BinaryReader):
        br.write_uint16(CCSTypes.Null.value)
        br.write_uint16(0)
        br.write_uint32(0)


class CCSChunk(BrStruct):
    def __init__(self):
        self.Name = ''
        self.Path = ''
        self.Type = 0
        self.Size = 0
        self.Index = 0
        self.Data = None
        self.CCS_Chunk = None #This will be set when writing

    def __br_read__(self, br: BinaryReader, Refs: ChunkRefs):
        self.Type = CCSTypes(br.read_uint32() & 0xFFFF).name
        self.Size = br.read_uint32()
        self.Index = br.read_int32()
        self.Name = Refs.Names[self.Index][0]
        self.Path = Refs.Names[self.Index][1]

        DataPos = br.pos() 

        #print(f'position = {hex(br.pos())}')
        if f'Br{self.Type}' in globals():
            chunktype = f'Br{self.Type}'
            self.BrChunk = br.read_struct(globals()[chunktype])
            self.Data = br.buffer()[DataPos:br.pos()]
        else:
            self.BrChunk = None
            self.Data = br.read_bytes((self.Size * 4) - 4)
        
    
    def __br_write__(self, br: BinaryReader):
        br.write_uint16(CCSTypes)
        br.write_uint16(0xCCCC)
        br.write_uint32(self.Size // 4)
        br.write_int32(self.Index)
        br.write_struct(CCSTypes(self.Type).name, self.CCS_Chunk)


class ChunksDict:
    def __init__(self, BrChunks: list = [], Refs: ChunkRefs = []):
        #start = time.perf_counter()
        #Some chunks have the same name and index, so we're gonna hash the index and type together
        self._dict = {}
        self.Indices = {}
        self.Names = {}
        self.Paths = {}

        for chunk in BrChunks:
            self._dict[hash((chunk.Index, chunk.Type))] = chunk
            self.Names[chunk.Name] = chunk
            self.Paths[chunk.Path] = chunk
            #print(globals())
            #init each chunk as the correct type
            if chunk.Type in globals().items():
                chunk.__class__ = globals()[chunk.Type]
                chunk.init_data(chunk.BrChunk, Refs, self)
                chunk.CCS_Chunk = chunk
        
        #print(f'ChunksDict init time: {time.perf_counter() - start}')

    def update_chunk(self, chunk: CCSChunk):
        self._dict[hash((chunk.Index, chunk.Type))] = chunk
        self.Names[chunk.Name] = chunk
        self.Paths[chunk.Path] = chunk
        self.Indices[chunk.Index] = chunk

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.Indices[key]
        elif isinstance(key, str):
            return self.Names[key]
        elif isinstance(key, tuple):
            return self._dict[hash(key)]
        else:
            raise TypeError(f'ChunksDict key must be int, str, or tuple, not {type(key)}')
        
    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.Indices[key] = value
        elif isinstance(key, str):
            self.Names[key] = value
        elif isinstance(key, tuple):
            self._dict[hash(key)] = value
        else:
            raise TypeError(f'ChunksDict key must be int, str, or tuple, not {type(key)}')
        
    def __delitem__(self, key):
        if isinstance(key, int):
            del self.Indices[key]
        elif isinstance(key, str):
            del self.Names[key]
        elif isinstance(key, tuple):
            del self._dict[hash(key)]
        else:
            raise TypeError(f'ChunksDict key must be int, str, or tuple, not {type(key)}')
        
        #Update chunks with new indices
        for chunk in self._dict.values():
            if chunk.Index > key:
                chunk.Index -= 1

                #Update the hash
                self._dict[hash((chunk.Index, chunk.Type))] = chunk
                del self._dict[hash((chunk.Index + 1, chunk.Type))]

                del self.Indices[chunk.Index + 1]
                self.Indices[chunk.Index] = chunk

    def __iter__(self):
        return iter(self._dict.values())

    def __len__(self):
        return len(self._dict)
    
    def __contains__(self, key):
        if isinstance(key, int):
            return key in self.Indices
        elif isinstance(key, str):
            return key in self.Names
        elif isinstance(key, tuple):
            return hash(key) in self._dict
        else:
            raise TypeError(f'ChunksDict key must be int, str, or tuple, not {type(key)}')
    
    def get(self, key, default=None):
        if isinstance(key, int):
            return self.Indices.get(key, default)
        elif isinstance(key, str):
            return self.Names.get(key, default)
        elif isinstance(key, tuple):
            return self._dict.get(hash(key), default)
        else:
            raise TypeError(f'ChunksDict key must be int, str, or tuple, not {type(key)}')
        
    def get_chunk_alt(self, Index):
        return self.Chunks[Index]
    
    def add_chunk(self, chunk: CCSChunk):
        self._dict[hash((chunk.Index, chunk.Type))] = chunk
        self.Names[chunk.Name] = chunk
        self.Paths[chunk.Path] = chunk
        self.Indices[chunk.Index] = chunk
    
    def remove_chunk(self, chunk: CCSChunk):
        del self._dict[hash((chunk.Index, chunk.Type))]
        del self.Names[chunk.Name]
        del self.Paths[chunk.Path]
        del self.Indices[chunk.Index]
    



class BrClump(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.bone_count = br.read_uint32()
        self.bone_indices = [br.read_uint32()
                              for i in range(self.bone_count)]
        
        if ccsf_version > 0x110:
            self.bones = [br.read_struct(BrBone) for i in range(self.bone_count)]
        else:
            #Early versions of CCS Clumps don't have loc, rot, scale data for bones
            self.bones = [DummyBone() for i in range(self.bone_count)]
    
    def __br_write__(self, br: BinaryReader, chunks: 'ChunksDict'):
        '''br.write_uint16(CCSTypes.Clump.value)
        br.write_uint16(0xCCCC)'''

        indices_buf = BinaryReader(bytearray(), Endian.LITTLE)
        bones_buf = BinaryReader(bytearray(), Endian.LITTLE)

        for bone in self.ccs_chunk.bones:
            indices_buf.write_uint32(chunks.get_chunk_index(bone))
            bones_buf.write_struct(bone)
        
        br.write_uint32((indices_buf.size() + bones_buf.size()) // 4)
        br.write_int32(chunks.get_chunk_index(self.ccs_chunk))

        #write indices
        br.extend(indices_buf.buffer())
        br.seek(indices_buf.size(), Whence.CUR)

        #write bones
        br.extend(bones_buf.buffer())
        br.seek(bones_buf.size(), Whence.CUR)


class BrBone(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.pos = br.read_float(3)
        self.rot = br.read_float(3)
        self.scale = br.read_float(3)
    def __br_write__(self, br: BinaryReader):
        br.write_float(pos * 100 for pos in self.pos)
        br.write_float(rot * 180 / pi for rot in self.rot)
        br.write_float(self.scale)

class DummyBone:
    def __init__(self):
        self.pos = (0,0,0)
        self.rot = (0,0,0)
        self.scale = (1,1,1)

class BrObject(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.ParentObjectID = br.read_uint32()
        #print(self.ParentObjectID)
        self.ModelID = br.read_uint32()
        #print(self.ModelID)
        self.ShadowID = br.read_uint32()
        #print(self.ShadowID)
        if ccsf_version > 0x120:
            self.unk = br.read_uint32()
    
    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.ParentObjectID)
        br.write_uint32(self.ModelID)
        br.write_uint32(self.ShadowID)
        if ccsf_version > 0x120:
            br.write_uint32(self.unk)


class BrDummyObject(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.ParentObjectID = br.read_uint32()
        self.ModelID = br.read_uint32()
        self.ShadowID = br.read_uint32()
        self.ExtraID = br.read_uint32()
    
    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.ParentObjectID)
        br.write_uint32(self.ModelID)
        br.write_uint32(self.ShadowID)
        br.write_uint32(self.ExtraID)


class BrExternal(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.ParentID = br.read_uint32()
        self.ObjectID = br.read_uint32()


class BrColor_Palette(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.BlitGroup = br.read_uint32()
        br.seek(8, 1)

        self.ColorCount = br.read_uint32()
        self.PaletteData = []
        for i in range(self.ColorCount):
            B = br.read_uint8()
            G = br.read_uint8()
            R = br.read_uint8()
            A = br.read_uint8()

            self.PaletteData.append(((R, G, B, min(255, A * 2))))


class BrMaterial(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.TextureID = br.read_uint32()
        self.Alpha = br.read_float()
        if ccsf_version > 0x120:
            self.X = br.read_float()
            self.Y = br.read_float()
        else:
            self.Offset1 = br.read_uint16()
            self.Offset2 = br.read_uint16()


class BrTexture(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        self.ClutID = br.read_uint32()
        self.BlitGroup = br.read_uint32()
        self.TextureFlags = br.read_uint8()
        self.TextureType = br.read_uint8()
        self.MipmapsCount = br.read_uint8()
        self.unk1 = br.read_uint8()
        self.Width = br.read_uint8()
        self.Height = br.read_uint8()
        self.unk2 = br.read_uint16()
        if ccsf_version < 0x120:
            self.ActualWidth = 1 << self.Width
            self.ActualHeight = 1 << self.Height
            self.unk3 = br.read_uint32()
        elif self.Width == 0xff or self.Height == 0xff:
            self.ActualWidth = br.read_uint16()
            self.ActualHeight = br.read_uint16()
            self.unk3 = br.read_uint16()
        elif self.TextureType == 0x87 or self.TextureType == 0x89:
            br.seek(0x10, 1)
            self.ActualHeight = br.read_uint16()
            self.ActualWidth = br.read_uint16()
            br.seek(0x14, 1)
        else:
            self.ActualWidth = 1 << self.Width
            self.ActualHeight = 1 <<self.Height
            self.unk4 = br.read_uint32()

        self.TextureDataSize = br.read_uint32()

        if self.TextureType == 0x87 or self.TextureType == 0x89:
            br.seek(0xC, 1)
            self.TextureName = br.read_str(16)
            self.TextureData = br.read_bytes(self.TextureDataSize - 0x40)
        else:
            self.TextureData = br.read_uint8(self.TextureDataSize << 2)



class TextureTypes(Enum):
    RGBA32 = 0
    Indexed8 = 0x13
    Indexed4 = 0x14
    DXT1 = 0x87
    DXT5 = 0x89


class ModelTypes(IntFlag):
    Rigid1 = 0
    Rigid2   = 1
    Morphable = 2
    Deformable = 4
    ShadowMesh = 8


class BrRigidMesh(BrStruct):
    def __br_read__(self, br: BinaryReader, deformable=False, MeshFlags=0):
        #print(f"reading rigid mesh at {hex(br.pos())}")
        if deformable:
            self.MaterialID = br.read_uint32()
            self.VertexCount = br.read_uint32()
            self.unk = br.read_uint32() #this could be the count of deformable vertices
            self.ParentID = br.read_uint32()
        else:
            self.ParentID = br.read_uint32()
            self.MaterialID = br.read_uint32()
            self.VertexCount = br.read_uint32()
        
        #create a list of BrVertex objects
        self.Vertices = [BrVertex() for i in range(self.VertexCount)]

        for i in range(self.VertexCount):
            self.Vertices[i].Position = br.read_int16(3)

        br.align_pos(4)

        for i in range(self.VertexCount):
            self.Vertices[i].Normal = br.read_int8(3)
            self.Vertices[i].TriangleFlag = br.read_uint8()

        if not deformable and not MeshFlags & 2:
            for i in range(self.VertexCount):
                self.Vertices[i].Color = br.read_uint8(4)
        
        if ccsf_version > 0x125:
            for i in range(self.VertexCount):
                self.Vertices[i].UV = br.read_uint32(2)
        else:
            for i in range(self.VertexCount):
                self.Vertices[i].UV = br.read_uint16(2)
        
        

class BrShadowMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.VertexCount = br.read_uint32()
        #print(f'VertexCount = {self.VertexCount}')
        self.TriangleVerticesCount = br.read_uint32()
        self.VertexPositions = [br.read_int16(3) for i in range(self.VertexCount)]
        #print(f'VertexPositions = {self.VertexPositions}')
        br.align_pos(4)
        self.Triangles = [br.read_int32(3) for i in range((self.TriangleVerticesCount // 3))]
        #print(f'Triangles = {self.Triangles}')


class BrDeformableMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.MaterialID = br.read_uint32()
        #print(f'MaterialID = {self.MaterialID}')
        self.VertexCount = br.read_uint32() #This is the number of vertices that are actually used
        #print(f'VertexCount = {self.VertexCount}')

        self.TotalVertexCount = br.read_uint32() #This is the total count of all vertices
                                                 #there are some duplicates because they store 1 vertex weight per position
                                                 #so if a vertex has 2 weights, it will be stored twice
        #print(f'TotalVertexCount = {self.TotalVertexCount}')
        self.Vertices = list()

        for i in range(self.VertexCount):

            Vertex = BrDeformableVertex()

            Vertex.Positions[0] = br.read_int16(3)

            vertParams = br.read_uint16()

            Vertex.BoneIDs[0] = vertParams >> 10
            Vertex.Weights[0] = (vertParams & 0x1ff)

            dualFlag = ((vertParams >> 9) & 0x1) == 0
            
            if dualFlag:
                Vertex.MultiWeight = True
                Vertex.Positions[1] = br.read_int16(3)
                secondParams = br.read_uint16()
                Vertex.Weights[1] = (secondParams & 0x1ff)
                Vertex.BoneIDs[1] = (secondParams >> 10)
            
            self.Vertices.append(Vertex)
                    
        for i in range(self.VertexCount):
            self.Vertices[i].Normals[0] = br.read_int8(3)

            self.Vertices[i].TriangleFlag = br.read_int8()
            if self.Vertices[i].MultiWeight:
                self.Vertices[i].Normals[1] = br.read_int8(3)
                br.read_int8()
        
        for i in range(self.VertexCount):
            self.Vertices[i].UV = br.read_int16(2)
        
        vertex_list = dict()
        
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
    


class BrModel(CCSChunk):
    def __br_read__(self, br: BinaryReader):
        #print(f'BrModel')
        self.VertexScale = br.read_float()
        #print(f'VertexScale = {self.VertexScale}')
        self.ModelType = br.read_uint8()
        self.MeshFlags = br.read_uint8()
        self.MeshCount = br.read_uint16()
        #print(f'MeshCount = {self.MeshCount}')
        self.SourceFactor = br.read_uint8() #this is a guess
        self.DestinationFactor = br.read_uint8() #this is a guess
        self.UnkFlags = br.read_uint16()
        self.LookupListCount = br.read_uint32()
        #print(self.ModelType)

        if ccsf_version > 0x110:
            self.OutlineColor = br.read_uint8(4)
            self.OutlineWidth = br.read_float()
        
        #print(f'LookupListCount = {self.LookupListCount}')
        if self.ModelType == ModelTypes.Deformable and ccsf_version > 0x111:
            self.LookupList = [br.read_uint8() for i in range(self.LookupListCount)]
            br.align_pos(4)
            #print(f'lookupTable = {self.LookupList}')
        else:
            self.LookupList = None

        self.Meshes = list()
        if self.MeshCount > 0:
            
            if self.ModelType == ModelTypes.Rigid1 or self.ModelType == ModelTypes.Rigid2:
                for i in range(self.MeshCount):
                    rigidmesh = br.read_struct(BrRigidMesh, None, False, self.MeshFlags)
                    self.Meshes.append(rigidmesh)

            elif self.ModelType & ModelTypes.Deformable:
                for i in range(self.MeshCount-1):
                    self.Meshes.append(br.read_struct(BrRigidMesh, None, True, self.MeshFlags))
                
                self.Meshes.append(br.read_struct(BrDeformableMesh))

            elif self.ModelType == ModelTypes.ShadowMesh:
                self.Meshes.append(br.read_struct(BrShadowMesh))
            


class BrVertex(BrStruct):
    def __init__(self, Position = (0, 0, 0), Normal = (0, 0, 0), TriangleFlag = 0, UV = (0, 0), Color = (0, 0, 0, 0)):
        self.Position = (0, 0, 0)
        self.Normal = (0, 0, 0)
        self.TriangleFlag = 0
        self.UV = (0, 0)
        self.Color = (0, 0, 0, 0)


class BrDeformableVertex:
    def __init__(self):
        self.Positions = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        self.MultiWeight = False
        self.Normals = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        self.UV = (0, 0)
        self.BoneIDs = [0, 0, 0, 0]
        self.Weights = [0, 0, 0, 0]
        self.VertexColor = (0, 0, 0, 0)
        self.TriangleFlag = 0
        