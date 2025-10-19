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
            # uint32
            # float32[2]
            # byte[4]

        # BIN_filter
            # uint32
            # ??

        # BIN_env
            # uint32 == 0x103
            # float32[3]
            # byte[4]
            #  ??


        
    def finalize(self, chunks):
        pass