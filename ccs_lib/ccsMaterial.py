from .ccsTexture import ccsTexture
from .utils.PyBinaryReader.binary_reader import *

class ccsMaterial(BrStruct):
    def __init__(self):
        self.name = ''
        self.textureName = ''
        self.alternativeName = ''
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
        self.useCharaShader = False
        self.forceOutputColor = [0, 0, 0, 0]
        #cullModes: 0=deafualt, 1=back, 2=front
        self.cullMode = 0       
        self.ambientColor = [0, 0, 0, 0]
        self.textureNormIndex = 0
        self.normalStrength = 0
        self.useSpecular = 0
        self.debugSpecular = 0
        self.textureSpecIndex = 0
        self.specularStrength = 0
        self.specularShininess = 0
        self.textureMultiIndex = 0
        self.mTex_blendMode = 0
        self.MultiTexParam_unk1 = 0
        # mTex_uvModes: 0=UVs, 1=UV from Reflection view, 2=UV from view pos, 3=UV from world normal, 4=UV from world pos
        self.mTex_uvMode = 0           
        self.MultiTexParam_unk3 = 0
        self.mTexUV_scaleX = 1
        self.mTexUV_scaleY = 1
        self.mTexUV_offsetX = 0
        self.mTexUV_offsetY = 0
        self.mTexUV_speed   = [0, 0]
        self.EmissionColor  = [0, 0, 0, 0]


    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.textureName = indexTable.Names[self.textureIndex][0]
        
        self.alpha = br.read_float32()
        if version >= 0x130:
            self.useCharaShader = True
            self.offsetX = br.read_int16() / 4096
            self.offsetY = br.read_int16() / 4096
            self.scaleX = br.read_int16() / 4096
            self.scaleY = br.read_int16() / 4096
            self.forceOutputColor = br.read_uint8(4)
            if self.forceOutputColor == [0, 0, 0, 0]:
                self.useCharaShader = False
            self.cullMode      = br.read_int32()
            self.ambientColor  = br.read_uint8(4)
            self.textureNormIndex = br.read_uint32()
            self.normalStrength = br.read_float32()
            self.useSpecular    = br.read_uint16()
            self.debugSpecular  = br.read_uint16()
            self.textureSpecIndex = br.read_uint32()
            self.specularStrength = br.read_float32()
            self.specularShininess = br.read_float32()
            if version > 0x130:
                self.textureMultiIndex = br.read_uint32()
                self.mTex_blendMode = br.read_uint16()
                self.mTex_uvMode    = br.read_uint16()
                self.mTexUV_scaleX  = br.read_float32()
                self.mTexUV_scaleY  = br.read_float32()
                self.mTexUV_offsetX = br.read_float32()
                self.mTexUV_offsetY = br.read_float32()
                self.mTexUV_speed   = br.read_float32(2)
                self.EmissionColor  = br.read_uint8(4)
        elif version < 0x130 and version >= 0x120:
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
        if version >= 0x130:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))
            br.write_uint16(int(self.scaleX * 4096))
            br.write_uint16(int(self.scaleY * 4096))
            br.write_uint8(self.forceOutputColor[0])
            br.write_uint8(self.forceOutputColor[1])
            br.write_uint8(self.forceOutputColor[2])
            br.write_uint8(self.forceOutputColor[3])
            br.write_int32(self.cullMode)
            br.write_uint8(self.ambientColor[0])
            br.write_uint8(self.ambientColor[1])
            br.write_uint8(self.ambientColor[2])
            br.write_uint8(self.ambientColor[3])
            br.write_uint32(self.textureNormIndex)
            br.write_float32(self.normalStrength)
            br.write_uint16(self.useSpecular)
            br.write_uint16(self.debugSpecular)
            br.write_uint32(self.textureSpecIndex)
            br.write_float32(self.specularStrength)
            br.write_float32(self.specularShininess)
            if version > 0x130:
                br.write_uint32(self.textureMultiIndex)
                br.write_uint16(self.mTex_blendMode)
                br.write_uint16(self.mTex_uvMode)
                br.write_float32(self.mTexUV_scaleX)
                br.write_float32(self.mTexUV_scaleY)
                br.write_float32(self.mTexUV_offsetX)
                br.write_float32(self.mTexUV_offsetY)
                br.write_float32(self.mTexUV_speed)
                br.write_uint8(self.EmissionColor)
        elif version < 0x130 and version >= 0x120:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))
            br.write_uint16(int(self.scaleX * 4096))
            br.write_uint16(int(self.scaleY * 4096))
        else:
            br.write_uint16(int(self.offsetX * 4096))
            br.write_uint16(int(self.offsetY * 4096))


    def finalize(self, chunks):
        self.texture = chunks.get(self.textureIndex)
        
        #we'll try to get the texture's clut chunk so we can use its name as an alt name for the material
        if self.texture and isinstance(self.texture, ccsTexture):
            # check for clut
            if self.texture.clutIndex:
                clut = chunks.get(self.texture.clutIndex)
                if clut and clut.name:
                    self.alternativeName = clut.name
        
        if self.useCharaShader:
            if self.textureNormIndex:
                self.textureN = chunks.get(self.textureNormIndex)
            if self.textureSpecIndex:
                self.textureS = chunks.get(self.textureSpecIndex)
            if self.textureMultiIndex:
                self.textureM = chunks.get(self.textureMultiIndex)
