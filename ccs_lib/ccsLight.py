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

        self.lightType = lightType(br.read_uint32() & 0xFF)

    
    def finalize(self, chunks):
        pass


class lightType(Enum):
    DistantLight = 1
    DirectLight = 2
    SpotLight = 3
    OmniLight = 4