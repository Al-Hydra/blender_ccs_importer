from .utils.PyBinaryReader.binary_reader import *


class ccsCamera(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Camera"
        self.path = ''
        self.fov = 45
    
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
    

    def finalize(self, chunks):
        pass