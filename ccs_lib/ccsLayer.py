from .utils.PyBinaryReader.binary_reader import *

class ccsLayer(BrStruct):

    def __init__(self):
        self.name = ''
        self.type = 'Layer'
        self.path = ''

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = 99999999
        self.name = 'Layer'
        
        self.entryCount = br.read_uint32()
        layers = []
        for i in range(self.entryCount):
            flag = br.read_uint32()
            layerIndex = br.read_uint32()
            layers.append( (flag, layerIndex) )
        
    def finalize(self, chunks):
        pass