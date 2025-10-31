from .utils.PyBinaryReader.binary_reader import *
from enum import Enum


class ccsBinary(BrStruct):

    def __init__(self):
        self.name = ''
        self.type = 'Binary'
        self.path = ''

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        # BIN_shade
            # uint32 == 0x100
            # float32
            # byte[4]
            # byte[4]

        # BIN_filter
            # uint32 == 0x100
            # uint8
            # uint8[3]  filterColor[R,G,B]   / 255
            # uint32
            # uint32

        # BIN_env  | BIN_stage_env  | BIN_power_env
            # uint32 == 0x103 | 0x102
            # float32[3] ambientPlayer[B,G,R] / 255.0f
            # uint32[3]  ambient[B,G,R]    / 255
            # uint32[3]  mainLightColor
            # uint32[3]  fogColor[B,G,R]
            # float32    fogNear
            # float32    fogFar
            # float32    fogMin
            # float32    fogMax
            # uint32[3]  BgColor[B,G,R]
            # uint32[4]
            # float32
            # uint32[4]
            # uint32[3]

        # BIN_power_color
        
    def finalize(self, chunks):
        pass