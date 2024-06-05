from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes

class ccsClump(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "Clump"
        self.path = ""
        self.bones = {}
        self.dynamics = None
    
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.boneCount = br.read_uint32()
        self.boneIndices = [br.read_uint32()
                              for i in range(self.boneCount)]
        
        if version > 0x110:
            self.bones = {i: br.read_struct(Bone) for i in self.boneIndices}
        else:
            #Early versions of CCS Clumps don't have loc, rot, scale data for bones
            self.bones = {i: Bone() for i in self.boneIndices}
    
    def finalize(self, chunks):
        for bone, index in zip(self.bones.values(), self.boneIndices):
            bone.finalize(index, self.bones, chunks, self)


class Bone(BrStruct):
    def __init__(self):
        self.name = ""
        self.object = None
        self.parent = None
        self.pos = (0,0,0)
        self.rot = (0,0,0)
        self.scale = (1,1,1)
        self.matrix = [(0,0,0,0), (0,0,0,0), (0,0,0,0), (0,0,0,0)]

    def __br_read__(self, br: BinaryReader):
        self.pos = br.read_float(3)
        self.rot = br.read_float(3)
        self.scale = br.read_float(3)
    
    def finalize(self, index, bones, chunks, clump):
        bone_obj = chunks[index]
        print(f"Bone: {bone_obj.name}")

        bone_obj.finalize(chunks)
        self.name = bone_obj.name
        self.object = bone_obj
        if bone_obj.type != "":
            self.parent = bones.get(bone_obj.parentIndex)
        
            if self.object.model:
                self.object.model.clump = clump
                self.object.model.parentBone = self
