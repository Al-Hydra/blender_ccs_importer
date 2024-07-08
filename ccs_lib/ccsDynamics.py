from .utils.PyBinaryReader.binary_reader import *


class ccsDynamics(BrStruct):

    def __init__(self):
        self.name = ""
        self.type = "Dynamics"
        self.path = ""
        self.springBones = []
        self.collisions = []

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.clumpIndex = br.read_uint32()
        self.index = f"{self.clumpIndex}_Dynamics"
        self.name = f"{indexTable.Names[self.clumpIndex][0]}_Dynamics"
        self.path = indexTable.Names[self.clumpIndex][1]

        self.springBonesCount = br.read_uint16()
        self.collisionsCount = br.read_uint16()

        self.springBones = [br.read_struct(springBone) for i in range(self.springBonesCount)]
        self.collisions = [br.read_struct(collision) for i in range(self.collisionsCount)]

    def finalize(self, chunks):
        self.clump = chunks[self.clumpIndex]
        if self.clump:
            self.clump.dynamics = self


class springBone(BrStruct):

    def __init__(self):
        self.boneIndex = 0
        self.params = (0,0,0)

    def __br_read__(self, br: BinaryReader):
        self.boneIndex = br.read_uint32()
        self.params = br.read_float(3)


class collision(BrStruct):

    def __init__(self):
        self.boneIndex = 0
        self.position = (0,0,0)
        self.rotation = (0,0,0)
        self.scale = (1,1,1)
    

    def __br_read__(self, br: BinaryReader):
        self.boneIndex = br.read_uint32()
        self.position = br.read_float(3)
        self.rotation = br.read_float(3)
        self.scale = br.read_float(3)
