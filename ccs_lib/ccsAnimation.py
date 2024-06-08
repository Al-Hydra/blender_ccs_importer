from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes

class ccsAnimation(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Animation"
        self.path = ''
        self.frames = []
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.frameCount = br.read_uint32()
        self.framesSectionSize = br.read_uint32()

        currentFrame = 0
        while currentFrame != -1:
            #read chunk type
            chunkType = CCSTypes(br.read_uint16())
            br.seek(2, 1)
            chunkSize = br.read_uint32()
            if chunkType == CCSTypes.Frame:
                currentFrame = br.read_int32()
                continue
            
            elif chunkType == CCSTypes.ObjectController:
                objectController = br.read_struct(objectController)
                self.frames.append((chunkType, objectController))

            else:
                chunkData = br.read_bytes(chunkSize * 4)
                self.frames.append((chunkType, chunkData))


class objectController(BrStruct):
    def __init__(self):
        self.objectIndex = 0
        self.keyframes = []
        self.positions = []
        self.rotations = []
        self.scales = []
        self.opacity = []
    def __br_read__(self, br: BinaryReader, currentFrame):
        self.objectIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()       



def readPosition(br: BinaryReader, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            position = br.read_struct(vector3)
    
    elif ctrlFlags & 7 == 1:
        position = br.read_struct(vector3)
    return position


class vector3(BrStruct):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
    def __br_read__(self, br: BinaryReader):
        self.x = br.read_float()
        self.y = br.read_float()
        self.z = br.read_float()


class rotationEuler(BrStruct):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
    def __br_read__(self, br: BinaryReader):
        self.x = br.read_float()
        self.y = br.read_float()
        self.z = br.read_float()


class rotationQuaternion(BrStruct):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.w = 0
    def __br_read__(self, br: BinaryReader):
        self.x = br.read_float()
        self.y = br.read_float()
        self.z = br.read_float()
        self.w = br.read_float()


class colorRGBA(BrStruct):
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0
        self.a = 0
    def __br_read__(self, br: BinaryReader):
        self.r = br.read_uint8()
        self.g = br.read_uint8()
        self.b = br.read_uint8()
        self.a = br.read_uint8()
