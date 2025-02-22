from .utils.PyBinaryReader.binary_reader import *


class ccsPCM(BrStruct):

    def __init__(self):
        self.name = "PCM Audio"
        self.type = "PCM"
        self.path = ""
        self.data = b""

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()

        self.unknown1 = br.read_uint16()
        self.channelCount = br.read_uint16()
        self.chunkSize = br.read_uint32()
        self.count = br.read_uint32()
        self.data = br.read_bytes(self.chunkSize * self.count * 4)
        
        
    
    def finalize(self, chunks):
        pass
