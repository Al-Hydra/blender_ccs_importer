from .utils.PyBinaryReader.binary_reader import *
from enum import Enum

class ccsLight(BrStruct):
    def __init__(self) -> None:
        super().__init__()
        self.index = 0
        self.name = ''
        self.path = ''
        self.type = "Light"

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        #self.lightType = lightType(br.read_uint32() & 0xFF)
        self.lightType = lightType(br.read_uint8())
        self.unk = br.read_uint8()
        br.seek(2, 1) # padding


    def __br_write__(self, br: BinaryReader, version):
        br.write_uint32(self.index)
        br.write_uint8(self.lightType.value)
        br.write_uint8(self.unk)   
        br.write_uint16(0)


    def finalize(self, chunks):
        pass


class lightType(Enum):
    DistantLight = 1
    DirectLight = 2
    SpotLight = 3
    OmniLight = 4