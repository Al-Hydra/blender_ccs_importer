from .utils.PyBinaryReader.binary_reader import *


class ccsDynamics(BrStruct):

    def __init__(self):
        self.springBones = []
        self.collisions = []

    def __br_read__(self, br: BinaryReader, version):
        self.clumpIndex = br.read_uint32()
        self.springBonesCount = br.read_uint16()
        self.collisionsCount = br.read_uint16()

        self.springBones = [br.read_struct(springBone) for i in range(self.springBonesCount)]
        self.collisions = [br.read_struct(Collision) for i in range(self.collisionsCount)]

    def finalize(self, chunks):
        self.clump = chunks[self.clumpIndex]


class springBone(BrStruct):

    def __init__(self):
        self.boneIndex = 0
        self.params = (0,0,0)

    def __br_read__(self, br: BinaryReader):
        self.boneIndex = br.read_uint32()
        self.params = br.read_float(3)


class Collision(BrStruct):

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
