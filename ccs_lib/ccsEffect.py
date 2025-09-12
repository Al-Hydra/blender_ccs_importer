from .utils.PyBinaryReader.binary_reader import *
from .Eff import makeEffect, makeMaterial


class ccsEffect(BrStruct):

    def __init__(self):
        self.name = ""
        self.type = "Effect"
        self.path = ""
        self.texture = None
        self.object = None
        self.AnmObject = None
        self.parent = None
        self.model = None
        self.material = None
        self.clump = None
        self.frameCount = 0

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.textureIndex = br.read_uint32()
        self.matFlags1 = br.read_uint8() | 0x40
        self.matFlags2 = br.read_uint8()
        if version < 0x122:
            self.unk0 = br.read_int16()  # f == i16
        else:
            self.unk0 = br.read_int16() * 0.00390625  # f == i16 * 0.00390625
            
        self.unk1 = br.read_int16()
        self.frameCount = br.read_int16()
        
        self.vOffset_Left = br.read_float32()   * 0.01  #verts 0, 2
        self.vOffset_Bottem = br.read_float32() * 0.01  #verts 0, 1
        self.vOffset_Right = br.read_float32()  * 0.01  #verts 1, 3
        self.vOffset_Top = br.read_float32()    * 0.01  #verts 2, 3
        
        self.scaledX = br.read_int16() / 4096
        self.scaledY = br.read_int16() / 4096
        
        self.frameInfo = [br.read_struct(EffectFrame) for f in range(self.frameCount)]
    
    def __br_write__(self, br: BinaryReader, version=0x120):
        br.write_uint32(self.index)
        br.write_uint32(self.textureIndex)
        br.write_uint8(self.matFlags1 & ~0x40)
        br.write_uint8(self.matFlags2)
        if version < 0x122:
            br.write_int16(int(self.unk0))       # unk0
        else:
            br.write_int16(int(self.unk0 * 256)) # unk0
        br.write_int16(self.unk1)   # unk1
        br.write_int16(self.frameCount)
        
        br.write_float32(self.vOffset_Left   * 100)    # verts 0, 2
        br.write_float32(self.vOffset_Bottem * 100)  # verts 0, 1
        br.write_float32(self.vOffset_Right  * 100)   # verts 1, 3
        br.write_float32(self.vOffset_Top    * 100)     # verts 2, 3
        
        br.write_int16(int(self.scaledX * 4096))
        br.write_int16(int(self.scaledY * 4096))
        
        for frameInfo in self.frameInfo:
            frameInfo: EffectFrame
            br.write_struct(frameInfo)
            
    def finalize(self, chunks, chunks2):
        self.texture = chunks.get(self.textureIndex)
        makeEffect(self)
        makeMaterial(self.model, self.texture)
        self.AnmObject = chunks2.get(self.index)
        if self.AnmObject:
            self.AnmObject.parent = chunks.get(self.AnmObject.parentIndex)

class EffectFrame(BrStruct):
    def __init__(self):
        self.offsetX = 0
        self.offsetY = 0
        self.opacity = 1
        
    def __br_read__(self, br: BinaryReader):
        self.offsetX = br.read_int16() / 4096
        self.offsetY = br.read_int16() / 4096
        self.opacity = float(br.read_int16())
        br.seek(2, 1)

    def __br_write__(self, br: BinaryReader):
        br.write_int16(int(self.offsetX * 4096))
        br.write_int16(int(self.offsetY * 4096))
        br.write_int16(int(self.opacity))
        br.write_int16(0) # padding