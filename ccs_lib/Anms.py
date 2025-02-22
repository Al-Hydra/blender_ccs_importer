from .utils.PyBinaryReader.binary_reader import *
import struct
from .ccsTypes import CCSTypes, ccsDict
from collections import defaultdict

def anmChunkReader(self, br: BinaryReader, indexTable, version):
    current_frame = 0
    self.cameras = defaultdict(dict)
    self.objects = defaultdict(dict)
    self.materials = defaultdict(dict)
    self.morphs = defaultdict(lambda: defaultdict(dict))
    self.objectControllers = []
    self.morphControllers = []
    self.materialControllers = []
    self.pcmFrames = {}
    self.lights = defaultdict(dict)

    while current_frame > -1:
        # Read chunk type and size
        #print(f"reading anm chunk at {hex(br.pos())}")
        chunk_type = CCSTypes(br.read_uint16())
        br.seek(2, 1)  # Skip padding
        chunk_size = br.read_uint32()

        if chunk_type == CCSTypes.Frame:
            # Directly update current frame
            current_frame = br.read_int32()

        elif chunk_type == CCSTypes.ObjectController:
            # Read and append object controller
            self.objectControllers.append(br.read_struct(objectController, None, current_frame))

        elif chunk_type == CCSTypes.ObjectFrame:
            # Process object frame data
            obj_f = br.read_struct(objectFrame, None, current_frame, indexTable)
            self.objects[obj_f.name][current_frame] = (
                obj_f.position, obj_f.rotation, obj_f.scale, obj_f.opacity
            )

        elif chunk_type == CCSTypes.CameraFrame:
            # Process camera frame data
            cam_f = br.read_struct(cameraFrame, None, current_frame, indexTable)
            self.cameras[cam_f.name][current_frame] = (
                cam_f.position, cam_f.rotation, cam_f.fov
            )

        elif chunk_type == CCSTypes.MorphController:
            # Read and append morph controller
            self.morphControllers.append(br.read_struct(morphController, None, current_frame))

        elif chunk_type == CCSTypes.MorphFrame:
            # Process morph frame data
            morph_f = br.read_struct(morphFrame, None, current_frame, indexTable)
            morph_f_morph = self.morphs[morph_f.morph]
            for morph_t, value in morph_f.morphTargets.items():
                morph_f_morph[morph_t][morph_f.frame] = [1 - value]

        elif chunk_type == CCSTypes.MaterialController:
            # Read and append material controller
            self.materialControllers.append(
                br.read_struct(materialController, None, current_frame, indexTable)
            )

        elif chunk_type == CCSTypes.MaterialFrame:
            # Process material frame data
            material_f = br.read_struct(materialFrame, None, current_frame, indexTable, version)
            self.materials[material_f.name][current_frame] = (
                material_f.offsetX, material_f.offsetY, material_f.scaleX, material_f.scaleY
            )

        elif chunk_type == CCSTypes.PCMFrame:
            # Process PCM frame data
            self.pcmFrames[current_frame] = br.read_struct(PCMFrame, None, current_frame)
        
        elif chunk_type == CCSTypes.DistantLightFrame:
            # Process distant light frame data
            light_f = br.read_struct(distantLightFrame, None, current_frame, indexTable)
            self.lights[light_f.lightObject][current_frame] = (
                light_f.rotation, light_f.color, light_f.intensity
            )
            
        elif chunk_type == CCSTypes.AmbientFrame:
            # Process ambient light frame data
            ambient_f = br.read_struct(ambientFrame, None, current_frame)
            self.lights['Ambient'][current_frame] = ambient_f.color

        else:
            # Skip unknown chunk
            br.seek(chunk_size * 4, 1)

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

        if version < 0x120:
            if not self.ctrlFlags & 1:
                self.offsetX = br.read_float()
            if not self.ctrlFlags & 2:
                self.offsetY = br.read_float()
        
        else:
            if not self.ctrlFlags & 1:
                self.offsetX = br.read_float()
                self.offsetY = br.read_float()
            if not self.ctrlFlags & 2:
                self.scaleX = br.read_float()
                self.scaleY = br.read_float()
                self.unk1 = br.read_float()
                self.unk2 = br.read_float()

    def finalize(self, chunks):
        self.material = chunks[self.index]

class morphController(BrStruct):
    def __init__(self):
        self.morph = None
        self.target = None
        self.morphTargets = []

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.morphIndex = br.read_uint32()
        self.targetsCount = br.read_uint32()
        self.morphTargets = br.read_struct(morphTarget, self.targetsCount, currentFrame)

    def finalize(self, chunks):
        self.morph = chunks.get(self.morphIndex)

class morphTarget(BrStruct):
    def __br_read__(self, br: BinaryReader, currentFrame):
        morphValues = {}
        self.index = br.read_uint32()
        ctrlFlags = br.read_uint32()
        self.values = readFloat(br, morphValues, ctrlFlags, currentFrame)

class morphFrame(BrStruct):
    def __init__(self):
        self.morph = None
        self.target = None
        self.frame = 0
        self.morphTargets = {}

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.morphIndex = br.read_uint32()
        self.morph = indexTable.Names[self.morphIndex][0]
        self.targetsCount = br.read_uint32()
        self.morphTargets = {indexTable.Names[br.read_uint32()][0]: br.read_float() for _ in range(self.targetsCount)}
        self.frame = currentFrame

    def finalize(self, chunks):
        pass

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
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1, 1, 1]
        self.has_model = 0
        self.opacity = 1

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.objectIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.name = indexTable.Names[self.objectIndex][0]
        self.frame = currentFrame

        if not self.ctrlFlags & 2:
            self.position[0] = br.read_float()
        if not self.ctrlFlags & 4:
            self.position[1] = br.read_float()
        if not self.ctrlFlags & 8:
            self.position[2] = br.read_float()
        if not self.ctrlFlags & 10:
            self.rotation[0] = br.read_float()
        if not self.ctrlFlags & 20:
            self.rotation[1] = br.read_float()
        if not self.ctrlFlags & 40:
            self.rotation[2] = br.read_float()
        if not self.ctrlFlags & 80:
            self.scale[0] = br.read_float()
        if not self.ctrlFlags & 100:
            self.scale[1] = br.read_float()
        if not self.ctrlFlags & 200:
            self.scale[2] = br.read_float()
        if not self.ctrlFlags & 400:
            self.opacity = br.read_float()
        if not self.ctrlFlags & 800:
            self.has_model = br.read_uint32()

    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]

class cameraFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.camera = None
        self.name = ""
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.fov = 45

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.frame = currentFrame

        if not self.ctrlFlags & 2:
            self.position[0] = br.read_float()
        if not self.ctrlFlags & 4:
            self.position[1] = br.read_float()
        if not self.ctrlFlags & 8:
            self.position[2] = br.read_float()
        if not self.ctrlFlags & 10:
            self.rotation[0] = br.read_float()
        if not self.ctrlFlags & 20:
            self.rotation[1] = br.read_float()
        if not self.ctrlFlags & 40:
            self.rotation[2] = br.read_float()
        if not self.ctrlFlags & 80:
            self.unk = br.read_float()
        if not self.ctrlFlags & 100:
            self.fov = br.read_float()

    def finalize(self, chunks):
        self.camera = chunks[self.index]

class shadowFrame(BrStruct):
    def __init__(self):
        self.shadowObject = None
        self.position = (0, 0, 0)
        self.color = (0, 0, 0, 1)
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
        self.rotation = (0, 0, 0)
        self.color = (0, 0, 0, 1)
        self.intensity = 1
        self.frame = 0

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.lightObject = indexTable.Names[self.index][0]
        self.name = indexTable.Names[self.index][1]
        
        self.flags = br.read_uint32()
        self.rotation = br.read_float(3)
        self.color = br.read_uint8(4)
        self.frame = currentFrame

        if self.flags & 0x20:
            self.intensity = br.read_float()

    def finalize(self, chunks):
        self.lightObject = chunks[self.index]


class ambientFrame(BrStruct):
    def __init__(self):
        self.color = (128, 128, 128, 255)
        self.frame = 0

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.color = br.read_uint8(4)
        self.frame = currentFrame

def readVector(br: BinaryReader, vectorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        vectorFrames = {br.read_int32(): br.read_float(3) for _ in range(frameCount)}
    elif ctrlFlags & 7 == 1:
        vectorFrames[currentFrame] = br.read_float(3)
    return vectorFrames

def readRotationEuler(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        rotationFrames = {br.read_int32(): br.read_float(3) for _ in range(frameCount)}
    elif ctrlFlags & 7 == 1:
        rotationFrames[currentFrame] = br.read_float(3)
    return rotationFrames

def readRotationQuat(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 4:
        frameCount = br.read_uint32()
        rotationFrames = {br.read_int32(): br.read_float(4) for _ in range(frameCount)}
    return rotationFrames

def readFloat(br: BinaryReader, floatFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        floatFrames = {br.read_int32(): br.read_float() for _ in range(frameCount)}
    elif ctrlFlags & 7 == 1:
        floatFrames[currentFrame] = br.read_float()
    return floatFrames

def readColor(br: BinaryReader, colorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        for _ in range(frameCount):
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

class PCMFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.data = b""

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.frame = currentFrame
        self.index = br.read_uint32()
        self.count = br.read_uint16()
        self.unknown = br.read_uint16()
        self.chunkSize = br.read_uint32()
        self.data = br.read_bytes(self.chunkSize * self.count * 4)