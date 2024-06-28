from .utils.PyBinaryReader.binary_reader import *


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
        br.seek(8, 1)

        self.colorCount = br.read_uint32()
        for i in range(self.colorCount):

            color = br.read_uint8(4)

            self.paletteData.append(((color[2], color[1], color[0], min(255, color[3] * 2))))
    
    def finalize(*args):
        pass