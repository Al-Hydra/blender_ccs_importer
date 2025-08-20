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
            unk0 = br.read_int16()  # f == i16
        else:
            unk0 = br.read_int16() * 0.00390625  # f == i16 * 0.00390625
            
        unk1 = br.read_int16()
        self.frameCount = br.read_int16()
        
        self.vOffset_Left = br.read_float32()     * 0.01  #verts 0, 2
        self.vOffset_Bottem = br.read_float32()   * 0.01  #verts 0, 1
        self.vOffset_Right = br.read_float32()    * 0.01  #verts 1, 3
        self.vOffset_Top = br.read_float32()      * 0.01  #verts 2, 3
        
        self.scaledX = br.read_int16() * 0.0002441406
        self.scaledY = br.read_int16() * 0.0002441406
        
        self.frameInfo = [br.read_struct(EffectFrame) for f in range(self.frameCount)]
    
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
        self.Alpha = 1
        
    def __br_read__(self, br: BinaryReader):
        self.offsetX = br.read_int16() * 0.0002441406
        self.offsetY = br.read_int16() * 0.0002441406
        self.opacity = float(br.read_int16())
        br.seek(2, 1)
