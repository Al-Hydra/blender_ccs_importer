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

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.alpha = br.read_float()
        if version > 0x130:
            self.version = version
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
            unk0 = br.read_int32()
            unk1 = br.read_int32()
            AmbientColor = br.read_uint8(4)
            self.textureNIndex = br.read_uint32()
            self.NormalMapParam = br.read_float()
            unk2 = br.read_int32()
            self.textureSIndex = br.read_uint32()
            self.SpecularParam1 = br.read_float()
            self.SpecularParam2 = br.read_float()
            self.textureMIndex = br.read_uint32()
            self.MultiTexParams = br.read_uint8(4)
            self.MultiTexUV = br.read_float(4)
            self.MultiTexSpeed = br.read_float(2)
            self.EmissionColor = br.read_uint8(4)
        elif version == 0x130:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
            values = br.read_int32(9)
        elif version < 0x130 and version > 0x120:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
        else:
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096


    def finalize(self, chunks):
        self.texture = chunks.get(self.textureIndex)
        if self.version > 0x130:
            if self.textureNIndex:
                self.textureN = chunks.get(self.textureNIndex)
            if self.textureSIndex:
                self.textureS = chunks.get(self.textureNIndex)
            if self.textureMIndex:
                self.textureM = chunks.get(self.textureMIndex)
