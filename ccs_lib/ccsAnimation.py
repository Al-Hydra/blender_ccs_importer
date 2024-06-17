from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes
import struct

class ccsAnimation(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Animation"
        self.path = ''
        self.objectControllers = []
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.frameCount = br.read_uint32()
        self.framesSectionSize = br.read_uint32()

        currentFrame = 0
        while not currentFrame < 0:
            #read chunk type
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

            else:
                chunkData = br.read_bytes(chunkSize * 4)
                #self.frames.append((chunkType, chunkData))
    
    def finalize(self, chunks):
        for objectCtrl in self.objectControllers:
            objectCtrl.finalize(chunks)


class objectController(BrStruct):
    def __init__(self):
        self.object = None
        self.positions = {}
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.scales = {}
        self.opacity = {}
    def __br_read__(self, br: BinaryReader, currentFrame):
        self.objectIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.positions = readPosition(br, self.positions, self.ctrlFlags, currentFrame)
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.scales = readScale(br, self.scales, self.ctrlFlags >> 6, currentFrame)
        self.opacity = readOpacity(br, self.opacity, self.ctrlFlags >> 9, currentFrame)
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]


'''def readPosition(br: BinaryReader, positions, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        frame = br.read_uint32()
        posX = br.read_float()
        posY = br.read_float()
        posZ = br.read_float()
        positions[frame] = (posX, posY, posZ)

        for i in range(1, frameCount):
            frame = br.read_uint32()
            newPosX = br.read_float()
            delta = newPosX - posX
            posX = posX + delta

            newPosY = br.read_float()
            delta = newPosY - posY
            posY = posY + delta
            
            newPosZ = br.read_float()
            delta = newPosZ - posZ
            posY = posZ + delta

            positions[frame] = (posX, posY, posZ)
    
    elif ctrlFlags & 7 == 1:
        position = br.read_float(3)
        positions[currentFrame] = position
    
    return positions'''


def readPosition(br: BinaryReader, positions, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        frame = br.read_uint32()
        posX = br.read_float()
        posY = br.read_float()
        posZ = br.read_float()
        positions[frame] = (posX, posY, posZ)

        for i in range(1, frameCount):
            frame = br.read_uint32()
            posX = br.read_float()
            posY = br.read_float()        
            posZ = br.read_float()

            positions[frame] = (posX, posY, posZ)
    
    elif ctrlFlags & 7 == 1:
        position = br.read_float(3)
        positions[currentFrame] = position
    
    return positions


def readRotationEuler(br: BinaryReader, rotations, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            rotations[frame] = br.read_float(3)
    
    elif ctrlFlags & 7 == 1:
        rotations[currentFrame] = br.read_float(3)
    
    return rotations


def readRotationQuat(br: BinaryReader, rotations, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 4:
        frameCount = br.read_uint32()
        for i in range(frameCount):
            frame = br.read_uint32()
            rotations[frame] = br.read_float(4)
    
    return rotations


def readScale(br: BinaryReader, scales, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            scale = br.read_float(3)
            scales[frame] = scale
    
    elif ctrlFlags & 7 == 1:
        scale = br.read_float(3)
        scales[currentFrame] = scale
    
    return scales


def readOpacity(br: BinaryReader, opacities, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            opacity = br.read_float()
            opacities[frame] = opacity
    
    elif ctrlFlags & 7 == 1:
        opacity = br.read_float()
        opacities[currentFrame] = opacity
    
    return opacities


def readColor(br: BinaryReader, colors, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()

        for i in range(frameCount):
            frame = br.read_uint32()
            color = br.read_struct(colorRGBA)
            colors[frame] = color
    
    elif ctrlFlags & 7 == 1:
        color = br.read_struct(colorRGBA)
        colors[currentFrame] = color
    return color


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
