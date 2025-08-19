from .utils.PyBinaryReader.binary_reader import *
import numpy as np

class ccsClut(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Clut"
        self.path = ''
        self.blitGroup = 0
        self.colorCount = 0
        self.paletteData = []

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        self.blitGroup = br.read_uint32()
        #br.seek(7, 1)
        self.unk1 = br.read_uint32()
        self.unk2 = br.read_uint16()
        self.unk3 = br.read_uint8()
        self.alphaFlag = br.read_int8()
        
        self.colorCount = br.read_uint32()
        '''palette = np.frombuffer(br.read_bytes(self.colorCount * 4), dtype=(np.uint8, 4))
        #rearrange BGRA to RGBA
        palette = palette[:, [2, 1, 0, 3]]
        
        #multiply alpha by 2
        palette[:, 3] = np.clip(palette[:, 3] * 2, 0, 255)
        
        self.paletteData = palette'''

        for i in range(self.colorCount):

            color = br.read_uint8(4)

            self.paletteData.append(((color[2], color[1], color[0], min(255, color[3] * 2))))

    def __br_write__(self, br: BinaryReader, version: int):
        br.write_uint32(self.index)
        br.write_uint32(self.blitGroup)
        # Unknown 
        br.write_uint32(self.unk1)
        br.write_uint16(self.unk2)
        br.write_uint8(self.unk3)
        
        br.write_uint8(self.alphaFlag)

        br.write_uint32(self.colorCount)

        for i in range(self.colorCount):
            p_color = self.paletteData[i]
            br.write_uint8(p_color[2])
            br.write_uint8(p_color[1])
            br.write_uint8(p_color[0])
            #br.write_uint8(p_color[3] // 2)
            br.write_uint8(round(p_color[3] / 2))
    
    def finalize(*args):
        pass