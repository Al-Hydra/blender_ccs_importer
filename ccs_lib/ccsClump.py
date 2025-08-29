from .utils.PyBinaryReader.binary_reader import *

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


    def __br_write__(self, br: BinaryReader, version):
        br.write_uint32(self.index)
        br.write_uint32(self.boneCount)

        
        for i in range(self.boneCount):
            br.write_uint32(self.boneIndices[i])

        if version > 0x110:
            #print(f'self.bones {self.bones.items()}')
            for i, bone in self.bones.items():
                bone: Bone
                #print(f'self.bones.Bbone: {bone}')
                br.write_struct(bone)
        else:
            print(f'TODO: Clump version lower then 0x110')



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
        self.clump = None

    def __br_read__(self, br: BinaryReader):
        self.pos = br.read_float32(3)
        self.rot = br.read_float32(3)
        self.scale = br.read_float32(3)


    def __br_write__(self, br: BinaryReader):
        br.write_float32(self.pos)
        br.write_float32(self.rot)
        br.write_float32(self.scale)
    

    def finalize(self, index, bones, chunks, clump):
        bone_obj = chunks[index]
        if bone_obj.type != "Effect":
            bone_obj.finalize(chunks)

        bone_obj.clump = clump
        
        self.name = bone_obj.name
        self.object = bone_obj
        if bone_obj.parent:
            self.parent = bones.get(bone_obj.parent.index)
            self.parentObject = bone_obj.parent
        
        '''if bone_obj.type != "":
            self.parent = bones.get(bone_obj.parent.index)'''
        if self.object.model:
            self.object.model.clump = clump
            self.object.model.parentBone = self
