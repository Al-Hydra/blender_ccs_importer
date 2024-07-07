from .utils.PyBinaryReader.binary_reader import *
import struct
from .ccsTypes import CCSTypes, ccsDict


def anmChunkReader(self, br: BinaryReader, indexTable, version):
    currentFrame = 0
    self.cameras = {}
    self.objectControllers = []
    self.morphControllers = []
    self.materialControllers = []
    self.objects = {}
    self.materials = {}
    while not currentFrame < 0:
        #read chunk type
        #print(hex(br.pos()))
        #print(self.name)
        chunkType = CCSTypes(br.read_uint16())
        #print(chunkType)
        br.seek(2, 1)
        chunkSize = br.read_uint32()
        if chunkType == CCSTypes.Frame:
            currentFrame = br.read_int32()
            continue
        
        elif chunkType == CCSTypes.ObjectController:
            objectCtrl = br.read_struct(objectController, None, currentFrame)
            self.objectControllers.append(objectCtrl)
        
        elif chunkType == CCSTypes.ObjectFrame:
            objF = br.read_struct(objectFrame, None, currentFrame, indexTable)
            obj = self.objects.get(objF.name)
            if not obj:
                self.objects[objF.name] = {currentFrame: (objF.position, objF.rotation, objF.scale)}
            else:
                self.objects[objF.name][currentFrame] = (objF.position, objF.rotation, objF.scale)
        
        elif chunkType == CCSTypes.CameraFrame:
            camF = br.read_struct(cameraFrame, None, currentFrame, indexTable)
            cam = self.cameras.get(camF.name)
            if not cam:
                self.cameras[camF.name] = {currentFrame: (camF.position, camF.rotation, camF.fov)}
            else:
                self.cameras[camF.name][currentFrame] = (camF.position, camF.rotation, camF.fov)
        
        elif chunkType == CCSTypes.MorphController:
            morphCtrl = br.read_struct(morphController, None, currentFrame)
            self.morphControllers.append(morphCtrl)

        elif chunkType == CCSTypes.MaterialController:
            materialCtrl = br.read_struct(materialController, None, currentFrame, indexTable)
            self.materialControllers.append(materialCtrl)
        
        elif chunkType == CCSTypes.MaterialFrame:
            materialF = br.read_struct(materialFrame, None, currentFrame, indexTable, version)
            material = self.materials.get(materialF.name)
            if not material:
                self.materials[materialF.name] = {currentFrame: (materialF.offsetX, materialF.offsetY, materialF.scaleX, materialF.scaleY)}
            else:
                self.materials[materialF.name][currentFrame] = (materialF.offsetX, materialF.offsetY, materialF.scaleX, materialF.scaleY)

        else:
            chunkData = br.seek(chunkSize * 4, 1)
            #self.frames.append((chunkType, chunkData))


class objectController(BrStruct):
    def __init__(self):
        self.object = None
        self.positions = {}
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.scales = {}
        self.opacity = {}
        self.frameData = {}
    def __br_read__(self, br: BinaryReader, currentFrame):
        self.objectIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.positions = readVector(br, self.positions, self.ctrlFlags, currentFrame)
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.scales = readVector(br, self.scales, self.ctrlFlags >> 6, currentFrame)
        self.opacity = readFloat(br, self.opacity, self.ctrlFlags >> 9, currentFrame)
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]

class cameraController(BrStruct):
    def __init__(self):
        self.camera = None
        self.positions = {}
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.FOV = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.cameraIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.positions = readVector(br, self.positions, self.ctrlFlags, currentFrame)
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.FOV = readFloat(br, self.FOV, self.ctrlFlags, currentFrame)
    
    def finalize(self, chunks):
        self.camera = chunks[self.cameraIndex]


class materialController(BrStruct):
    def __init__(self):
        self.material = None
        self.offsetX = {}
        self.offsetY = {}
        self.scaleX = {}
        self.scaleY = {}

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.ctrlFlags = br.read_uint32()

        self.offsetX = readFloat(br, self.offsetX, self.ctrlFlags, currentFrame)
        self.offsetY = readFloat(br, self.offsetY, self.ctrlFlags >> 3, currentFrame)
        self.scaleX = readFloat(br, self.scaleX, self.ctrlFlags >> 6, currentFrame)
        self.scaleY = readFloat(br, self.scaleY, self.ctrlFlags >> 9, currentFrame)
    
    def finalize(self, chunks):
        self.material = chunks[self.index]


class materialFrame(BrStruct):
    def __init__(self):
        self.material = None
        self.frame = 0
        self.offsetX = 0
        self.offsetY = 0
        self.scaleX = 0
        self.scaleY = 0

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.ctrlFlags = br.read_uint32()

        self.frame = currentFrame

        if version > 0x120:

            if self.ctrlFlags & 2 == 0:
                self.offsetX = br.read_float()
            if self.ctrlFlags & 4 == 0:
                self.offsetY = br.read_float()
            if self.ctrlFlags & 8 == 0:
                self.scaleX = br.read_float()
            if self.ctrlFlags & 10 == 0:
                self.scaleY = br.read_float()
            if self.ctrlFlags & 20 == 0:
                self.unk1 = br.read_float()
            if self.ctrlFlags & 40 == 0:
                self.unk2 = br.read_float()
        
        else:
            if self.ctrlFlags & 2 == 0:
                self.offsetX = br.read_float()
            if self.ctrlFlags & 4 == 0:
                self.offsetY = br.read_float()

    
    def finalize(self, chunks):
        self.material = chunks[self.index]


class morphController(BrStruct):
    def __init__(self):
        self.morph = None
        self.target = None
        self.morphValues = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.morphIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.targetIndex = br.read_uint32()
        self.unk = br.read_uint32()

        self.frameCount = br.read_uint32()

        self.morphValues = {br.read_int32() : br.read_float() for i in range(self.frameCount)}

        #self.morphValues = readFloat(br, self.morphValues, self.ctrlFlags, currentFrame)


    def finalize(self, chunks):
        self.morph = chunks[self.morphIndex]
        self.target = chunks[self.targetIndex]


class frame(BrStruct):
    def __init__(self):
        self.index = 0
    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_int32()
    def finalize(self, chunks):
        pass


class objectFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.object = None
        self.name = ""
        self.position = [0,0,0]
        self.rotation = [0,0,0]
        self.scale = [1,1,1]
        self.opacity = 1
        self.unk = 0

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.objectIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()

        self.name = indexTable.Names[self.objectIndex][0]
        
        self.frame = currentFrame

        if self.ctrlFlags & 2 == 0:
            self.position[0] = br.read_float()
        if self.ctrlFlags & 4 == 0:
            self.position[1] = br.read_float()
        if self.ctrlFlags & 8 == 0:
            self.position[2] = br.read_float()
        
        if self.ctrlFlags & 10 == 0:
            self.rotation[0] = br.read_float()
        if self.ctrlFlags & 20 == 0:
            self.rotation[1] = br.read_float()
        if self.ctrlFlags & 40 == 0:
            self.rotation[2] = br.read_float()

        if self.ctrlFlags & 80 == 0:
            self.scale[0] = br.read_float()
        if self.ctrlFlags & 100 == 0:
            self.scale[1] = br.read_float()
        if self.ctrlFlags & 200 == 0:
            self.scale[2] = br.read_float()

        if self.ctrlFlags & 400 == 0:
            self.unk = br.read_float()
        if self.ctrlFlags & 800 == 0:
            self.opacity = br.read_uint32()

    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]


class cameraFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.camera = None
        self.name = ""
        self.position = [0,0,0]
        self.rotation = [0,0,0]
        self.fov = 45

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.ctrlFlags = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        
        self.frame = currentFrame

        if self.ctrlFlags & 2 == 0:
            self.position[0] = br.read_float()
        if self.ctrlFlags & 4 == 0:
            self.position[1] = br.read_float()
        if self.ctrlFlags & 8 == 0:
            self.position[2] = br.read_float()
        
        if self.ctrlFlags & 10 == 0:
            self.rotation[0] = br.read_float()
        if self.ctrlFlags & 20 == 0:
            self.rotation[1] = br.read_float()
        if self.ctrlFlags & 40 == 0:
            self.rotation[2] = br.read_float()

        if self.ctrlFlags & 80 == 0:
            self.unk = br.read_float()
        if self.ctrlFlags & 100 == 0:
            self.fov = br.read_float()

    def finalize(self, chunks):
        self.camera = chunks[self.index]


class shadowFrame(BrStruct):
    def __init__(self):
        self.shadowObject = None
        self.position = (0,0,0)
        self.color = (0,0,0,1)
        self.frame = 0
    
    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.position = br.read_float(3)
        self.color = br.read_uint8(4)

        self.frame = currentFrame
    def finalize(self, chunks):
        self.shadowObject = chunks[self.index]


class distantLightFrame(BrStruct):
    def __init__(self):
        self.lightObject = None
        self.position = (0,0,0)
        self.color = (0,0,0,1)
        self.frame = 0
    
    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.flags = br.read_uint32()
        self.position = br.read_float(3)
        self.color = br.read_uint8(4)

        self.frame = currentFrame

        if (self.flags & 0x20) == 0:
            self.intensity = br.read_float()
    
    def finalize(self, chunks):
        self.lightObject = chunks[self.index] 

def readVector(br: BinaryReader, vectorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        vectorFrames = {br.read_int32(): br.read_float(3) for i in range(frameCount)}
    
    elif ctrlFlags & 7 == 1:
        position = br.read_float(3)
        vectorFrames[currentFrame] = position
    
    return vectorFrames


def readRotationEuler(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        rotationFrames = {br.read_int32(): br.read_float(3) for i in range(frameCount)}
    
    elif ctrlFlags & 7 == 1:
        rotationFrames[currentFrame] = br.read_float(3)
    
    return rotationFrames


def readRotationQuat(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 4:
        frameCount = br.read_uint32()
        rotationFrames = {br.read_int32(): br.read_float(4) for i in range(frameCount)}
    
    return rotationFrames


def readFloat(br: BinaryReader, floatFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        floatFrames = {br.read_int32(): br.read_float() for i in range(frameCount)}
    
    elif ctrlFlags & 7 == 1:
        floatFrames[currentFrame] =  br.read_float()
    
    return floatFrames


def readColor(br: BinaryReader, colorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            colorFrames[frame] = br.read_uint8(4)
    
    elif ctrlFlags & 7 == 1:
        colorFrames[currentFrame] = br.read_uint8(4)
    return colorFrames


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



def float_to_bits(f):
    # Convert a float to its binary representation (IEEE 754) as a 32-bit unsigned integer
    return struct.unpack('>I', struct.pack('>f', f))[0]

def unpack_f(param_1):
    # Convert the integer to a float using struct
    uVar1 = param_1
    uVar2 = (uVar1 >> 23) & 0xff
    
    param_2 = [0] * 4
    param_2[1] = uVar1 >> 31
    
    if uVar2 == 0:
        param_2[0] = 2
        return param_2
    
    param_2[2] = uVar2 - 0x7f
    param_2[0] = 3
    param_2[3] = (uVar1 & 0x7fffff) << 7 | 0x40000000
    return param_2

def fptosi(float_value):
    # Convert the float to its binary representation as a 32-bit unsigned integer
    param_1 = float_to_bits(float_value)
    
    # Unpack the float
    local_30, local_2c, local_28, local_24 = unpack_f(param_1)
    
    uVar1 = 0
    if local_30 != 2 and local_28 >= 0:
        if local_28 < 0x1f:
            uVar1 = local_24 >> (0x1e - local_28 & 0x1f)
            if local_2c != 0:
                uVar1 = -uVar1
        else:
            uVar1 = 0x7fffffff
            if local_2c != 0:
                uVar1 = 0x80000000
    
    return uVar1

def toRadians(values):
    return (((fptosi(x * 182.0444) * 9.58738e-05) for x in values))
