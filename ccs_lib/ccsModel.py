from enum import IntFlag
from .utils.PyBinaryReader.binary_reader import *
import numpy as np

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

        # Positions: int16 xyz
        pos_i16 = np.frombuffer(br.read_bytes(self.vertexCount * 6), dtype='i2').reshape(self.vertexCount, 3)
        positions0 = pos_i16.astype(np.float32) * np.float32(finalScale)

        # Align to 4 bytes
        br.align_pos(4)

        # Normals + per-vertex flag: 3 * int8 + int8
        n_i8 = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)
        normals0      = n_i8[:, :3].astype(np.float32) / np.float32(64.0)
        triangleFlag  = n_i8[:, 3].astype(np.int8, copy=False)

        # Allocate 4-slot containers
        positions = np.zeros((self.vertexCount, 3), dtype=np.float32)
        normals   = np.zeros((self.vertexCount, 3), dtype=np.float32)
        boneIDs   = np.zeros((self.vertexCount, 4),    dtype=np.int32)
        weights   = np.zeros((self.vertexCount, 4),    dtype=np.float32)

        positions[:] = positions0
        normals[:] = normals0
        boneIDs[:,   0]    = self.parentIndex
        weights[:,   0]    = 1.0

        # Colors (present when (modelFlags & 2) == 0)
        color = None
        if (modelFlags & 2) == 0:
            # 4 * uint8 per vertex, doubled and clamped to 255
            col = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='u1').reshape(self.vertexCount, 4).astype(np.int16)
            col = np.minimum(255, col * 2).astype(np.uint8)
            color = col

        # UVs (present when (modelFlags & 4) == 0)
        UV = None
        if (modelFlags & 4) == 0:
            if version >= 0x125:
                # 16.16 fixed-point in int32
                uv_i32 = np.frombuffer(br.read_bytes(self.vertexCount * 8), dtype='i4').reshape(self.vertexCount, 2)
                UV = uv_i32.astype(np.float32) / np.float32(65536.0)
            else:
                # int16 / 256
                uv_i16 = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i2').reshape(self.vertexCount, 2)
                UV = uv_i16.astype(np.float32) / np.float32(256.0)

        # Optional tangents/binormals (each: 3 * int8 + sign byte)
        tangents = tangent_sign = bitangents = bitangent_sign = None
        if tanBinFlag:
            t_i8   = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)
            b_i8   = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)

            tangents       = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
            tangent_sign   = np.zeros((self.vertexCount, 4),    dtype=np.int8)
            bitangents     = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
            bitangent_sign = np.zeros((self.vertexCount, 4),    dtype=np.int8)

            tangents[:, 0, :]     = t_i8[:, :3].astype(np.float32) / np.float32(64.0)
            tangent_sign[:, 0]    = t_i8[:, 3].astype(np.int8)
            bitangents[:, 0, :]   = b_i8[:, :3].astype(np.float32) / np.float32(64.0)
            bitangent_sign[:, 0]  = b_i8[:, 3].astype(np.int8)

        self.vertices =  {
            "positions":     positions,      # (V,4,3) slot0 filled
            "normals":       normals,        # (V,4,3) slot0 filled
            "boneIDs":       boneIDs,        # (V,4)   slot0=parentIndex
            "weights":       weights,        # (V,4)   slot0=1
            "triangleFlag":  triangleFlag,   # (V,)
            "color":         color,          # (V,4) uint8 or None
            "UV":            UV,             # (V,2) float32 or None
            "tangents":        tangents,        # (V,4,3) or None
            "tangent_sign":    tangent_sign,    # (V,4)   or None
            "bitangents":      bitangents,      # (V,4,3) or None
            "bitangent_sign":  bitangent_sign,  # (V,4)   or None
        }


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
            vnBuffer.write_int8(self.vertices[v].triangleFlags)

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

        #self.vertices = np.frombuffer(br.read_bytes(self.vertexCount * 6), dtype=np.int16).reshape(-1, 3) / ((vertexScale / 256) / 16) * 0.01
        self.vertices = np.frombuffer(br.read_bytes(self.vertexCount * 6), dtype=np.int16).reshape(-1, 3) * ((vertexScale / 256) / 16) * 0.01

        #self.vertices = [Vertex((br.read_int16(), br.read_int16(), br.read_int16()), (0,0,0), (0,0,0,0), (0, 0), vertexScale) for i in range(self.vertexCount)]

        br.align_pos(4)
        #self.triangles = [br.read_int32(3) for i in range((self.triangleVerticesCount // 3))]
        self.triangles = np.frombuffer(br.read_bytes(self.triangleVerticesCount * 4), dtype=np.int32).reshape(-1, 3)


    def __br_write__(self, br: BinaryReader, vertexScale=64):
        br.write_uint32(self.vertexCount)
        br.write_uint32(self.triangleVerticesCount)

        finalScale = ((vertexScale / 256)  / 16) * 0.01

        for v in range(self.vertexCount):
            br.write_int16(round(self.vertices[v][0] / finalScale))
            br.write_int16(round(self.vertices[v][1] / finalScale))
            br.write_int16(round(self.vertices[v][2] / finalScale))

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
            #vpBuffer = BinaryReader(br.read_bytes(self.vertexCount * 6), encoding='cp932')

            # positions: int16 xyz, scaled
            pos_i16 = np.frombuffer(br.read_bytes(self.vertexCount * 6), dtype='i2').reshape(self.vertexCount, 3)
            positions0 = pos_i16.astype(np.float32) * np.float32(finalScale)

            # align to 4 bytes (reader maintains its own cursor)
            br.align_pos(4)

            # normals: int8 xyz, scaled
            n_i8 = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)
            normals0 = n_i8[:, :3].astype(np.float32) / np.float32(64.0)
            flags_i8 = n_i8[:, 3].astype(np.int8)  # triangle flags

            # 4-slot containers (SoA)
            positions = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
            normals   = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
            boneIDs   = np.zeros((self.vertexCount, 4),    dtype=np.uint32)
            weights   = np.zeros((self.vertexCount, 4),    dtype=np.float32)
            flags     = np.zeros((self.vertexCount),    dtype=np.int8)

            positions[:, 0, :] = positions0
            normals[:,   0, :] = normals0
            flags[:] = flags_i8

            # constant boneID in slot0, weight 1.0 in slot0
            boneIDs[:, 0] = boneID
            weights[:, 0] = 1.0

            # UVs
            if version > 0x125:
                # Your code used float32/65536; preserved here.
                # If these are actually fixed-point int16 UVs, switch dtype to e+'i2' and keep the /65536.
                uv = np.frombuffer(br.read_bytes(self.vertexCount * 8), dtype='i4').reshape(self.vertexCount, 2) / np.float32(65536.0)
            else:
                uv = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i2').reshape(self.vertexCount, 2) / np.float32(256.0)
            vertexUVs = uv.astype(np.float32, copy=False)

            # Tangents (optional)
            vertexTangents = None
            vertexBitangents = None
            if tanBinFlag:
                vertexTangents   = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)
                vertexBitangents = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i1').reshape(self.vertexCount, 4)

            self.vertices = {
                "positions": positions,            # (V,4,3) slot0 filled
                "normals":   normals,              # (V,4,3) slot0 filled
                "boneIDs":   boneIDs,              # (V,4)   slot0=bone_id
                "weights":   weights,              # (V,4)   slot0=1
                "UV":        vertexUVs,            # (V,2)
                "tangents":  vertexTangents,       # (V,4) or None
                "bitangents":vertexBitangents,     # (V,4) or None
                "triangleFlags":     flags                   # (V,4)    int8
            }

                

        else: #multiple weights vertices
            if version < 0x125:
                # --- raw reads ---
                vp = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 8), dtype='i2').reshape(-1, 4)
                vn = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 4), dtype='i1').reshape(-1, 4)
                uv = np.frombuffer(br.read_bytes(self.vertexCount * 4), dtype='i2').reshape(-1, 2)

                pos_i16  = vp[:, :3]                         # (Ndef,3) int16
                params   = vp[:,  3].view('u2')       # (Ndef,)  uint16
                norm_i8  = vn[:, :3]                         # (Ndef,3) int8
                flags_i8 = vn[:,  3]                         # (Ndef,)  int8

                # --- map deformable entries to vertices (1 or 2 per vertex) ---
                first_idx  = np.empty(self.vertexCount, dtype=np.int32)
                has_second = np.empty(self.vertexCount, dtype=bool)

                i = 0
                for v in range(self.vertexCount):
                    first_idx[v] = i
                    p = params[i]
                    hs = ((p >> 9) & 1) == 0  # 0 => has second
                    has_second[v] = hs
                    i += 1 + (1 if hs else 0)

                if i != self.deformableVerticesCount:
                    raise ValueError(f"Count mismatch: walked {i}, expected {self.deformableVerticesCount}")

                second_idx = first_idx + 1

                # --- allocate 4 slots per vertex ---
                positions = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
                normals   = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
                boneIDs   = np.zeros((self.vertexCount, 4),    dtype=np.uint16)
                weights   = np.zeros((self.vertexCount, 4),    dtype=np.float32)
                flags     = np.zeros((self.vertexCount),    dtype=np.int8)

                # slot 0
                s0 = first_idx
                positions[:, 0, :] = pos_i16[s0].astype(np.float32) * np.float32(finalScale)
                p0 = params[s0]
                boneIDs[:, 0] = (p0 >> 10).astype(np.uint16)
                weights[:, 0] = (p0 & 0x1FF).astype(np.float32) / np.float32(256.0)
                normals[:, 0, :] = norm_i8[s0].astype(np.float32) / np.float32(64.0)
                flags[:] = flags_i8[s0]
                # slot 1 (only where present)
                if has_second.any():
                    s1 = second_idx[has_second]
                    positions[has_second, 1, :] = pos_i16[s1].astype(np.float32) * np.float32(finalScale)
                    p1 = params[s1]
                    boneIDs[has_second, 1] = (p1 >> 10).astype(np.uint16)
                    weights[has_second, 1] = (p1 & 0x1FF).astype(np.float32) / np.float32(256.0)
                    normals[has_second, 1, :] = norm_i8[s1].astype(np.float32) / np.float32(64.0)

                # UVs
                if version > 0x125:
                    UV = uv.astype(np.float32) / np.float32(65536.0)  # (V,2)
                else:
                    UV = uv.astype(np.float32) / np.float32(256.0)  # (V,2)

                self.vertices = {
                    "positions": positions,  # (V,4,3)  float32
                    "normals":   normals,    # (V,4,3)  float32
                    "boneIDs":   boneIDs,    # (V,4)    uint16
                    "weights":   weights,    # (V,4)    float32
                    "UV":        UV,         # (V,2)    float32
                    "triangleFlags":     flags         # (V,4)    int8
                }

            else:
                # vp: x,y,z, weight, stopBit, boneID  (all int16)  -> 6 * i16 = 12 bytes
                vp_raw = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 0x0C), dtype='i2').reshape(-1, 6)

                # vn: nx, ny, nz, flag (all int8) -> 4 bytes
                vn_raw = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 4), dtype='i1').reshape(-1, 4)

                # optional: tangents / bitangents (assumed int8[4] same as normals)
                vt_raw = vbn_raw = None
                if tanBinFlag:
                    vt_raw = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 4), dtype='i1').reshape(-1, 4)
                    vbn_raw = np.frombuffer(br.read_bytes(self.deformableVerticesCount * 4), dtype='i1').reshape(-1, 4)

                # --- UVs: 16.16 fixed-point in int32 ---
                uv_raw = np.frombuffer(br.read_bytes(self.vertexCount * 8), dtype='i4').reshape(-1, 2)

                # --- outputs: 4 slots per vertex ---
                positions = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
                normals   = np.zeros((self.vertexCount, 4, 3), dtype=np.float32)
                boneIDs   = np.zeros((self.vertexCount, 4),    dtype=np.uint16)
                weights   = np.zeros((self.vertexCount, 4),    dtype=np.float32)
                flags     = np.zeros(self.vertexCount,         dtype=np.int8)
                UV        = np.zeros((self.vertexCount, 2),    dtype=np.float32)

                # Tangents/bitangents (optional)
                tangents        = np.zeros((self.vertexCount, 4, 3), dtype=np.float32) if tanBinFlag else None
                tangent_sign    = np.zeros((self.vertexCount, 4),    dtype=np.int8)    if tanBinFlag else None
                bitangents      = np.zeros((self.vertexCount, 4, 3), dtype=np.float32) if tanBinFlag else None
                bitangent_sign  = np.zeros((self.vertexCount, 4),    dtype=np.int8)    if tanBinFlag else None

                # --- walk deformable entries per vertex until stopBit ---
                idx = 0
                for v in range(self.vertexCount):
                    slot = 0
                    stopBit = 0
                    while stopBit == 0 and slot < 4:
                        x, y, z, w_i16, stop_i16, bone_i16 = vp_raw[idx]
                        nx, ny, nz, flag = vn_raw[idx]

                        # positions, weights, bone ids
                        positions[v, slot] = (x*finalScale, y*finalScale, z*finalScale)
                        weights[v, slot]   = w_i16 / 256.0
                        boneIDs[v, slot]   = np.uint16(bone_i16)

                        # normals + triangle flag (last seen wins)
                        normals[v, slot] = (nx/64.0, ny/64.0, nz/64.0)
                        flags[v] = flag

                        # tangents / bitangents (assumed int8 packing like normals)
                        if tanBinFlag:
                            tx, ty, tz, ts = vt_raw[idx]
                            bx, by, bz, bs = vbn_raw[idx]
                            tangents[v, slot]       = (tx/64.0, ty/64.0, tz/64.0)
                            tangent_sign[v, slot]   = ts   # keep raw sign/flag byte
                            bitangents[v, slot]     = (bx/64.0, by/64.0, bz/64.0)
                            bitangent_sign[v, slot] = bs

                        stopBit = stop_i16
                        idx += 1
                        slot += 1

                    # UVs: 16.16 fixed-point -> float
                    u_i32, v_i32 = uv_raw[v]
                    UV[v] = (u_i32/65536.0, v_i32/65536.0)

                # --- package ---
                self.vertices = {
                    "positions":     positions,     # (V,4,3)
                    "normals":       normals,       # (V,4,3)
                    "boneIDs":       boneIDs,       # (V,4)
                    "weights":       weights,       # (V,4)
                    "triangleFlags":  flags,         # (V,)
                    "UV":            UV,            # (V,2)
                }
                if tanBinFlag:
                    self.vertices.update({
                        "tangents":        tangents,        # (V,4,3)
                        "tangent_sign":    tangent_sign,    # (V,4)  int8
                        "bitangents":      bitangents,      # (V,4,3)
                        "bitangent_sign":  bitangent_sign,  # (V,4)  int8
                    })


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
                br.write_int8(self.vertices[v].triangleFlags)

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
                    vnBuffer.write_int8(self.vertices[v].triangleFlags)
                    
                    if self.vertices[v].multiWeight:
                        normCount += 1
                        #v_norm = self.vertices[v].normals[1]
                        v_norm = self.vertices[v].normals[0]
                        vnBuffer.write_int8(int(v_norm[0] * 64))
                        vnBuffer.write_int8(int(v_norm[1] * 64))
                        vnBuffer.write_int8(int(v_norm[2] * 64))
                        vnBuffer.write_int8(self.vertices[v].triangleFlags)
                    
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
                        vnBuffer.write_int8(self.vertices[v].triangleFlags)

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
            vertexScale = br.read_float32()
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
        self.vertexScale = br.read_float32()
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
            self.outlineWidth = br.read_float32()
        
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
        br.write_float32(self.vertexScale)
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
            br.write_float32(self.outlineWidth)

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
        if self.lookupList and self.clump:
            self.lookuplistnames = [chunks.get(self.clump.boneIndices[i]).name for i in self.lookupList]
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
        self.triangleFlags = 0
        self.multiWeight = False
