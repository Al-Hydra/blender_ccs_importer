from .utils.PyBinaryReader.binary_reader import *
import struct
from .ccsTypes import CCSTypes, ccsDict
from collections import defaultdict
import numpy as np
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
    self.animationLoops = False

    def read_frame():
        nonlocal current_frame
        current_frame = br.read_int32()

    def read_object_controller():
        self.objectControllers.append(br.read_struct(objectController, None, current_frame))

    def read_object_frame():
        obj_f = br.read_struct(objectFrame, None, current_frame, indexTable)
        self.objects[obj_f.name][current_frame] = (
            obj_f.position, obj_f.rotation, obj_f.scale, obj_f.opacity
        )

    def read_camera_frame():
        cam_f = br.read_struct(cameraFrame, None, current_frame, indexTable)
        self.cameras[cam_f.name][current_frame] = (
            cam_f.position, cam_f.rotation, cam_f.fov
        )

    def read_morph_controller():
        self.morphControllers.append(br.read_struct(morphController, None, current_frame))

    def read_morph_frame():
        morph_f = br.read_struct(morphFrame, None, current_frame, indexTable)
        morph_f_morph = self.morphs[morph_f.morph]
        for morph_t, value in morph_f.morphTargets.items():
            morph_f_morph[morph_t][morph_f.frame] = [1 - value]

    def read_material_controller():
        self.materialControllers.append(
            br.read_struct(materialController, None, current_frame, indexTable)
        )

    def read_material_frame():
        material_f = br.read_struct(materialFrame, None, current_frame, indexTable, version)
        self.materials[material_f.name][current_frame] = (
            material_f.offsetX, material_f.offsetY, material_f.scaleX, material_f.scaleY
        )

    def read_pcm_frame():
        self.pcmFrames[current_frame] = br.read_struct(PCMFrame, None, current_frame)

    def read_distant_light_frame():
        light_f = br.read_struct(distantLightFrame, None, current_frame, indexTable)
        self.lights[light_f.lightObject][current_frame] = (
            light_f.rotation, light_f.color, light_f.intensity
        )

    def read_ambient_frame():
        ambient_f = br.read_struct(ambientFrame, None, current_frame)
        self.lights['Ambient'][current_frame] = ambient_f.color

    # Dispatch table
    chunk_handlers = {
        CCSTypes.Frame: read_frame,
        CCSTypes.ObjectController: read_object_controller,
        CCSTypes.ObjectFrame: read_object_frame,
        CCSTypes.CameraFrame: read_camera_frame,
        CCSTypes.MorphController: read_morph_controller,
        CCSTypes.MorphFrame: read_morph_frame,
        CCSTypes.MaterialController: read_material_controller,
        CCSTypes.MaterialFrame: read_material_frame,
        CCSTypes.PCMFrame: read_pcm_frame,
        CCSTypes.DistantLightFrame: read_distant_light_frame,
        CCSTypes.AmbientFrame: read_ambient_frame,
    }

    # Main loop
    while current_frame > -1:
        chunk_type = CCSTypes(br.read_uint16())
        br.seek(2, 1)  # skip padding
        chunk_size = br.read_uint32()

        handler = chunk_handlers.get(chunk_type)
        if handler:
            handler()
        else:
            print(f"Skiped unknown chunk_type: {chunk_type}")
            # Unknown chunk; skip
            br.seek(chunk_size * 4, 1)


    if current_frame == -2:
        self.animationLoops = True

#def anmChunkWriter(self, br: BinaryReader, indexTable, version):
def anmChunkWriter(self, br: BinaryReader, version):
    current_frame = 0

    for f in range(self.frameCount):
        if f == 0:
            # write frame 0
            br.write_uint16(CCSTypes.Frame.value)
            br.write_uint16(0xCCCC)
            br.write_uint32(1)
            br.write_int32(0) # first frame

            # Object controllers
            for objController in self.objectControllers:
                objController: objectController
                #br.write_uint16(0x0102)
                br.write_uint16(CCSTypes.ObjectController.value)
                br.write_uint16(0xCCCC)
                # create temeperay buffer
                ocBuffer = BinaryReader(encoding='cp932')
                ocBuffer.write_struct(objController, current_frame)
                # write chunk size
                br.write_uint32(ocBuffer.size() // 4)
                # write buffer to chunk
                br.write_bytes(bytes(ocBuffer.buffer()))
                print(f"objController: objectController: {objController}")

            # material Controllers
            for matController in self.materialControllers:
                matController: materialController
                #br.write_uint16(0x0202)
                br.write_uint16(CCSTypes.MaterialController.value)
                br.write_uint16(0xCCCC)
                # create temeperay buffer
                mcBuffer = BinaryReader(encoding='cp932')
                mcBuffer.write_struct(matController, current_frame)
                # write chunk size
                br.write_uint32(mcBuffer.size() // 4)
                # write buffer to chunk
                br.write_bytes(bytes(mcBuffer.buffer()))
                print(f"materialController: materialController: {matController}")

        elif f < self.frameCount:
            # write final frame as (-1) or (-2)for looping?
            br.write_uint16(CCSTypes.Frame.value)
            br.write_uint16(0xCCCC)
            br.write_uint32(1)
            br.write_int32(f) # frame
            if f == self.frameCount -1:
                # write final frame as -1 or -2
                br.write_uint16(CCSTypes.Frame.value)
                br.write_uint16(0xCCCC)
                br.write_uint32(1)
                if self.animationLoops == False:
                    br.write_int32(-1) # last frame
                else:
                    br.write_int32(-2) # last frame
                break
        else:
            # write final frame as -1 or -2
            br.write_uint16(CCSTypes.Frame.value)
            br.write_uint16(0xCCCC)
            br.write_uint32(1)
            if self.animationLoops == False:
                br.write_int32(-1) # last frame
            else:
                br.write_int32(-2) # last frame
            break
    
    return



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

    def __br_write__(self, br: BinaryReader, currentFrame):
            br.write_uint32(self.objectIndex)
            br.write_uint32(self.ctrlFlags)
            writeVector(br, self.positions, self.ctrlFlags, currentFrame)
            writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
            writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
            writeVector(br, self.scales, self.ctrlFlags >> 6, currentFrame)
            writeFloat(br, self.opacity, self.ctrlFlags >> 9, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
            br.write_uint32(self.objectIndex)
            br.write_uint32(self.ctrlFlags)
            writeVector(br, self.positions, self.ctrlFlags, currentFrame)
            writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
            writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
            writeVector(br, self.scales, self.ctrlFlags >> 6, currentFrame)
            writeFloat(br, self.opacity, self.ctrlFlags >> 9, currentFrame)

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

    def __br_write__(self, br: BinaryReader, currentFrame):
            br.write_uint32(self.index)
            br.write_uint32(self.ctrlFlags)
            writeFloat(br, self.offsetX, self.ctrlFlags, currentFrame)
            writeFloat(br, self.offsetY, self.ctrlFlags >> 3, currentFrame)
            writeFloat(br, self.scaleX, self.ctrlFlags >> 6, currentFrame)
            writeFloat(br, self.scaleY, self.ctrlFlags >> 9, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
            br.write_uint32(self.index)
            br.write_uint32(self.ctrlFlags)
            writeFloat(br, self.offsetX, self.ctrlFlags, currentFrame)
            writeFloat(br, self.offsetY, self.ctrlFlags >> 3, currentFrame)
            writeFloat(br, self.scaleX, self.ctrlFlags >> 6, currentFrame)
            writeFloat(br, self.scaleY, self.ctrlFlags >> 9, currentFrame)

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
                self.offsetX = br.read_float32()
            if not self.ctrlFlags & 2:
                self.offsetY = br.read_float32()
        
        else:
            if not self.ctrlFlags & 1:
                self.offsetX = br.read_float32()
                self.offsetY = br.read_float32()
            if not self.ctrlFlags & 2:
                self.scaleX = br.read_float32()
                self.scaleY = br.read_float32()
                self.unk1 = br.read_float32()
                self.unk2 = br.read_float32()

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
        self.morphTargets = {indexTable.Names[br.read_uint32()][0]: br.read_float32() for _ in range(self.targetsCount)}
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

        flags = self.ctrlFlags

        # Table of (bitmask, destination list, index, read_func)
        read_map = [
            (0x2, self.position, 0, br.read_float32),
            (0x4, self.position, 1, br.read_float32),
            (0x8, self.position, 2, br.read_float32),
            (0x10, self.rotation, 0, br.read_float32),
            (0x20, self.rotation, 1, br.read_float32),
            (0x40, self.rotation, 2, br.read_float32),
            (0x80, self.scale,    0, br.read_float32),
            (0x100, self.scale,   1, br.read_float32),
            (0x200, self.scale,   2, br.read_float32),
        ]

        for bit, target, i, reader in read_map:
            if not flags & bit:
                target[i] = reader()

        if not flags & 0x400:
            self.opacity = br.read_float32()
        if not flags & 0x800:
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
            self.position[0] = br.read_float32()
        if not self.ctrlFlags & 4:
            self.position[1] = br.read_float32()
        if not self.ctrlFlags & 8:
            self.position[2] = br.read_float32()
        if not self.ctrlFlags & 10:
            self.rotation[0] = br.read_float32()
        if not self.ctrlFlags & 20:
            self.rotation[1] = br.read_float32()
        if not self.ctrlFlags & 40:
            self.rotation[2] = br.read_float32()
        if not self.ctrlFlags & 80:
            self.unk = br.read_float32()
        if not self.ctrlFlags & 100:
            self.fov = br.read_float32()

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
        self.position = br.read_float32(3)
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
        self.rotation = br.read_float32(3)
        self.color = br.read_uint8(4)
        self.frame = currentFrame

        if self.flags & 0x20:
            self.intensity = br.read_float32()

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
        #vectorFrames = {br.read_int32(): br.read_float32(3) for _ in range(frameCount)}
        vectorFrames = np.frombuffer(br.read_bytes(frameCount * 16), dtype=[('frame', 'i4'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        vectorFrames = {frame['frame']: (frame['x'], frame['y'], frame['z']) for frame in vectorFrames}
        
    elif ctrlFlags & 7 == 1:
        vectorFrames[currentFrame] = br.read_float32(3)
    return vectorFrames

def writeVector(br: BinaryReader, vectorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        br.write_uint32(len(vectorFrames))
        for f in vectorFrames:
            br.write_uint32(f)
            br.write_float32(vectorFrames[f])
    elif ctrlFlags & 7 == 1:
        for f in vectorFrames:
            br.write_float32(vectorFrames[f])
    return


def readRotationEuler(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        rotationFrames = np.frombuffer(br.read_bytes(frameCount * 16), dtype=[('frame', 'i4'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        rotationFrames = {frame['frame']: (frame['x'], frame['y'], frame['z']) for frame in rotationFrames}
    elif ctrlFlags & 7 == 1:
        rotationFrames[currentFrame] = br.read_float32(3)
    return rotationFrames

def writeRotationEuler(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        br.write_uint32(len(rotationFrames))
        for f in rotationFrames:
            br.write_uint32(f)
            br.write_float32(rotationFrames[f])
    elif ctrlFlags & 7 == 1:
        for f in rotationFrames:
            br.write_float32(rotationFrames[f])
    return


def readRotationQuat(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 4:
        frameCount = br.read_uint32()
        rotationFrames = np.frombuffer(br.read_bytes(frameCount * 20), dtype=[('frame', 'i4'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('w', 'f4')])
        rotationFrames = {frame['frame']: (frame['x'], frame['y'], frame['z'], frame['w']) for frame in rotationFrames}
    return rotationFrames

def writeRotationQuat(br: BinaryReader, rotationFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 4:
        br.write_uint32(len(rotationFrames))
        for f in rotationFrames:
            br.write_uint32(f)
            br.write_float32(rotationFrames[f])
    return


def readFloat(br: BinaryReader, floatFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        floatFrames = np.frombuffer(br.read_bytes(frameCount * 8), dtype=[('frame', 'i4'), ('value', 'f4')])
        floatFrames = {frame['frame']: frame['value'] for frame in floatFrames}
    elif ctrlFlags & 7 == 1:
        floatFrames[currentFrame] = br.read_float32()
    return floatFrames

def writeFloat(br: BinaryReader, floatFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        br.write_uint32(len(floatFrames))
        for f in floatFrames:
            br.write_uint32(f)
            br.write_float32(floatFrames[f])
    elif ctrlFlags & 7 == 1:
        for f in floatFrames:
            br.write_float32(floatFrames[f])
    return


def readColor(br: BinaryReader, colorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        frameCount = br.read_uint32()
        colorFrames = np.frombuffer(br.read_bytes(frameCount * 8), dtype=[('frame', 'i4'), ('r', 'u1'), ('g', 'u1'), ('b', 'u1'), ('a', 'u1')])
        colorFrames = {frame['frame']: (frame['r'], frame['g'], frame['b'], frame['a']) for frame in colorFrames}
    elif ctrlFlags & 7 == 1:
        colorFrames[currentFrame] = br.read_uint8(4)
    return colorFrames


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