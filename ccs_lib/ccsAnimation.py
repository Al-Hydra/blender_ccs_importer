from .utils.PyBinaryReader.binary_reader import *
from .Anms import anmChunkReader


class ccsAnimation(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Animation"
        self.path = ''
        self.loop = False
        self.frameCount = 0
        self.objectControllers = []
        self.morphControllers = []
        self.materialControllers = []
        self.objects = {}
        
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.frameCount = br.read_uint32()
        self.framesSectionSize = br.read_uint32()

        anmChunkReader(self, br, indexTable)
    
    def finalize(self, chunks):
        for objectCtrl in self.objectControllers:
            objectCtrl.finalize(chunks)
        

