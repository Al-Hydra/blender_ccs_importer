from .utils.PyBinaryReader.binary_reader import *

class ccsMaterial(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Material"
        self.path = ''
        self.alpha = 1
        self.offsetX = 0
        self.offsetY = 0
        self.scaleX = 1
        self.scaleY = 1
        self.texture = None
        self.textureN = None
        self.textureS = None
        self.textureM = None
        self.version = 0

        self.unk0 = 0
        self.unk1 = 0
        self.ambientColor = [0, 0, 0, 0]
        self.textureNormIndex = 0
        self.normalMapParam = 0
        self.unk2 = 0
        self.textureSpecIndex = 0
        self.SpecularParam1 = 0
        self.SpecularParam2 = 0
        self.textureMultiIndex = 0
        self.MultiTexParams = [0, 0, 0, 0]
        self.MultiTexUV = [0, 0, 0, 0]
        self.MultiTexSpeed = [0, 0]
        self.EmissionColor = [0, 0, 0, 0]


    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.alpha = br.read_float32()
        if version > 0x130:
            self.version = version
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
            self.unk0 = br.read_int32()
            self.unk1 = br.read_int32()
            self.ambientColor = br.read_uint8(4)
            self.textureNormIndex = br.read_uint32()
            self.normalMapParam = br.read_float32()
            self.unk2 = br.read_int32()
            self.textureSpecIndex = br.read_uint32()
            self.SpecularParam1 = br.read_float32()
            self.SpecularParam2 = br.read_float32()
            self.textureMultiIndex = br.read_uint32()
            self.MultiTexParams = br.read_uint8(4)
            self.MultiTexUV = br.read_float32(4)
            self.MultiTexSpeed = br.read_float32(2)
            self.EmissionColor = br.read_uint8(4)
        elif version == 0x130:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
            self.values = br.read_int32(9)
        elif version < 0x130 and version > 0x120:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
        else:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096

    def __br_write__(self, br: BinaryReader, version):
        br.write_uint32(self.index)
        br.write_uint32(self.textureIndex)
        br.write_float32(self.alpha)
        if version > 0x130:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))
            br.write_uint16(int(self.scaleX * 4096))
            br.write_uint16(int(self.scaleY * 4096))
            br.write_uint32(self.unk0)
            br.write_uint32(self.unk1)
            br.write_uint8(self.ambientColor[0])
            br.write_uint8(self.ambientColor[1])
            br.write_uint8(self.ambientColor[2])
            br.write_uint8(self.ambientColor[3])
            br.write_uint32(self.textureNormIndex)
            br.write_float32(self.normalMapParam)
            br.write_uint32(self.unk2)
            br.write_uint32(self.textureSpecIndex)
            br.write_float32(self.SpecularParam1)
            br.write_float32(self.SpecularParam2)
            br.write_uint32(self.textureMultiIndex)
            br.write_uint8(self.MultiTexParams)
            br.write_float32(self.MultiTexUV)
            br.write_float32(self.MultiTexSpeed)
            br.write_uint8(self.EmissionColor)
        elif version == 0x130:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))
            br.write_uint16(int(self.scaleX * 4096))
            br.write_uint16(int(self.scaleY * 4096))
            br.write_bytes(bytes(self.values))
        elif version < 0x130 and version > 0x120:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))
            br.write_uint16(int(self.scaleX * 4096))
            br.write_uint16(int(self.scaleY * 4096))
        else:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))


    def finalize(self, chunks):
        self.texture = chunks.get(self.textureIndex)
        if self.version > 0x130:
            if self.textureNormIndex:
                self.textureN = chunks.get(self.textureNormIndex)
            if self.textureSpecIndex:
                self.textureS = chunks.get(self.textureSpecIndex)
            if self.textureMultiIndex:
                self.textureM = chunks.get(self.textureMultiIndex)
