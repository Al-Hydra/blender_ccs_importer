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
    self.cameraControllers = []
    self.morphControllers = []
    self.materialControllers = []
    self.distantLightControllers = []
    #self.directLightControllers = []
    #self.spotLightControllers = []
    self.omniLightControllers = []
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
            obj_f.position, obj_f.rotation, obj_f.scale, obj_f.opacity, obj_f.objectIndex, obj_f.ctrlFlags, obj_f.has_model 
        )

    def read_camera_controller():
        self.cameraControllers.append(br.read_struct(cameraController, None, current_frame))
    
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

    def read_distant_light_Controller():
        self.distantLightControllers.append(br.read_struct(distantLightController, None, current_frame))

    def read_distant_light_frame():
        light_f = br.read_struct(distantLightFrame, None, current_frame, indexTable)
        self.lights[light_f.lightObject][current_frame] = (
            light_f.rotation, light_f.color, light_f.intensity, light_f.lightIndex, light_f.flags
        )

    def read_ambient_frame():
        ambient_f = br.read_struct(ambientFrame, None, current_frame)
        self.lights['Ambient'][current_frame] = ambient_f.color


    def read_direct_light_Controller():
        self.directLightControllers.append(br.read_struct(directLightController, None, current_frame))

    def read_spot_light_Controller():
        self.spotLightControllers.append(br.read_struct(spotLightController, None, current_frame))


    def read_omni_light_Controller():
        self.omniLightControllers.append(br.read_struct(omniLightController, None, current_frame))

    def read_omni_light_frame():
        light_f = br.read_struct(omniLightFrame, None, current_frame, indexTable)
        self.lights[light_f.lightObject][current_frame] = (
            light_f.position, light_f.color, light_f.floats, light_f.lightIndex, light_f.flags
        )

    def read_note_frame():
        note_f = br.read_struct(noteFrame, None, current_frame, indexTable)
        print(f"Read chunk_type noteFrame with unknown data: {note_f.name}, frame: {current_frame}")

    # Dispatch table
    chunk_handlers = {
        CCSTypes.Frame: read_frame,
        CCSTypes.ObjectController: read_object_controller,
        CCSTypes.ObjectFrame: read_object_frame,
        CCSTypes.CameraController: read_camera_controller,
        CCSTypes.CameraFrame: read_camera_frame,
        CCSTypes.MorphController: read_morph_controller,
        CCSTypes.MorphFrame: read_morph_frame,
        CCSTypes.MaterialController: read_material_controller,
        CCSTypes.MaterialFrame: read_material_frame,
        CCSTypes.PCMFrame: read_pcm_frame,
        CCSTypes.DistantLightController: read_distant_light_Controller,
        CCSTypes.DistantLightFrame: read_distant_light_frame,
        CCSTypes.AmbientFrame: read_ambient_frame,
        # Not fully understood, but seen in some files
        # Included for CCS file rewriting support
        #CCSTypes.DirectLightController: read_direct_light_Controller,
        #CCSTypes.SpotLightController: read_spot_light_Controller,
        CCSTypes.OmniLightController: read_omni_light_Controller,
        CCSTypes.OmniLightFrame: read_omni_light_frame,
        CCSTypes.NoteFrame: read_note_frame,
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


def anmChunkWriter(self, br: BinaryReader, version=0x120, sortedChunks=None):
    final_frame = self.frameCount -1 
    for current_frame in range(self.frameCount):
        if current_frame == 0:
            # write frame 0
            anmFrame = frame()
            frame_type = 'Frame'
            write_frameChunk(br, anmFrame, frame_type, current_frame)

            # Object controllers
            for objController in self.objectControllers:
                anmCtrl_type = 'ObjectController'
                write_anmCtrlChunk(br, objController, anmCtrl_type, current_frame)

            # Material Controllers
            for matController in self.materialControllers:
                anmCtrl_type = 'MaterialController'
                write_anmCtrlChunk(br, matController, anmCtrl_type, current_frame)

            # Distant Light Controllers
            for lgtController in self.distantLightControllers:
                anmCtrl_type = 'DistantLightController'
                write_anmCtrlChunk(br, lgtController, anmCtrl_type, current_frame)

            # Omni Light Controllers
            for lgtController in self.omniLightControllers:
                anmCtrl_type = 'OmniLightController'
                write_anmCtrlChunk(br, lgtController, anmCtrl_type, current_frame)

            # Morph Controllers
            for mphController in self.morphControllers:
                anmCtrl_type = 'MorphController'
                write_anmCtrlChunk(br, mphController, anmCtrl_type, current_frame)

        if current_frame < self.frameCount:
            # Write objectFrames
            for object_name, frames in self.objects.items():
                #print(f"object_Name: {object_name}, frames.items() {frames.items()}")
                for f, frame_data in frames.items():
                    if current_frame == f:

                        # Unpack Object frame_data
                        pos, rot, scale, opacity, index, flags, has_model = frame_data

                        obj_f = objectFrame()
                        obj_f.objectIndex = index
                        obj_f.ctrlFlags = flags
                        obj_f.position = pos
                        obj_f.rotation = rot
                        obj_f.scale = scale
                        obj_f.opacity = opacity
                        obj_f.has_model = has_model 

                        frame_type = 'ObjectFrame'
                        write_frameChunk(br, obj_f, frame_type, current_frame)

            # Write lightFrames
            lightChunks = {chunk.name: chunk for chunk in sortedChunks["Light"]}
            for light_Name, frames in self.lights.items():
                #print(f"self.lights.items(): {frames}")

                for f, frame_data in frames.items():
                    #print(f"light_Name: {light_Name}, frames.items() {frames.items()}")
                    if current_frame == f:

                        lightChunk = lightChunks.get(light_Name)

                        if lightChunk.lightType.name == 'DistantLight':
                            #print(f"lightChunk.type: {lightChunk.lightType} frame# {f}")

                            # Unpack DistantLight frame_data
                            rot, clr, en, index, flags = frame_data

                            light_f = distantLightFrame()
                            light_f.lightIndex = index
                            light_f.flags = flags
                            light_f.rotation = rot
                            light_f.color = clr
                            light_f.intensity = en
                            frame_type = 'DistantLightFrame'
                            write_frameChunk(br, light_f, frame_type, current_frame)

                        if lightChunk.lightType.name == 'OmniLight':
                            #print(f"lightChunk.type: {lightChunk.lightType} frame# {f}")

                            # Unpack OmniLight frame_data
                            pos, clr, unkf, index, flags = frame_data

                            light_f = omniLightFrame()
                            light_f.lightIndex = index
                            light_f.flags = flags
                            light_f.position = pos
                            light_f.color = clr
                            light_f.floats = unkf
                            frame_type = 'OmniLightFrame'
                            write_frameChunk(br, light_f, frame_type, current_frame)

            # Write frame
            anmFrame = frame()
            frame_type = 'Frame'
            if final_frame != current_frame:
                #write Normal Frame
                write_frameChunk(br, anmFrame, frame_type, current_frame)

            # Write last frame
            else:
                last_frame = -1
                if self.animationLoops:
                    last_frame = -2
                write_frameChunk(br, anmFrame, frame_type, last_frame)
            
    return


def write_anmCtrlChunk(br: BinaryReader, anmCtrl_data, anmCtrl_type, current_frame):
    br.write_uint16(CCSTypes[anmCtrl_type].value)
    br.write_uint16(0xCCCC) # Write 0xCCCC bytes
    # create temeperay buffer
    acChunk_buf = BinaryReader(encoding='cp932')
    acChunk_buf.write_struct(anmCtrl_data, current_frame)
    # write anmCtrlChunk size
    br.write_uint32(acChunk_buf.size() // 4)
     # write anmCtrlChunk to Chunk
    br.write_bytes(bytes(acChunk_buf.buffer()))


def write_frameChunk(br: BinaryReader, frame_data, frame_type, current_frame):
    br.write_uint16(CCSTypes[frame_type].value)
    br.write_uint16(0xCCCC) # Write 0xCCCC bytes
    # create temeperay buffer
    afChunk_buf = BinaryReader(encoding='cp932')
    afChunk_buf.write_struct(frame_data, current_frame)
    # write frameChunk size
    br.write_uint32(afChunk_buf.size() // 4)
     # write current_frame to Chunk
    br.write_bytes(bytes(afChunk_buf.buffer()))


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
        self.FOV = readFloat(br, self.FOV, self.ctrlFlags >> 6, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.cameraIndex)
        br.write_uint32(self.ctrlFlags)
        writeVector(br, self.positions, self.ctrlFlags, currentFrame)
        writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        writeFloat(br, self.FOV, self.ctrlFlags >> 6, currentFrame)

    def finalize(self, chunks):
        self.camera = chunks[self.cameraIndex]


class materialController(BrStruct):
    def __init__(self):
        self.material = None
        self.offsetX = {}
        self.offsetY = {}
        self.scaleX = {}
        self.scaleY = {}
        self.float_4 = {}
        self.float_5 = {}

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.ctrlFlags = br.read_uint32()
        self.offsetX = readFloat(br, self.offsetX, self.ctrlFlags, currentFrame)
        self.offsetY = readFloat(br, self.offsetY, self.ctrlFlags >> 3, currentFrame)
        self.scaleX = readFloat(br, self.scaleX, self.ctrlFlags >> 6, currentFrame)
        self.scaleY = readFloat(br, self.scaleY, self.ctrlFlags >> 9, currentFrame)
        self.float_4 = readFloat(br, self.float_4, self.ctrlFlags >> 0xc, currentFrame)
        self.float_5 = readFloat(br, self.float_5, self.ctrlFlags >> 0xf, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.index)
        br.write_uint32(self.ctrlFlags)
        writeFloat(br, self.offsetX, self.ctrlFlags, currentFrame)
        writeFloat(br, self.offsetY, self.ctrlFlags >> 3, currentFrame)
        writeFloat(br, self.scaleX, self.ctrlFlags >> 6, currentFrame)
        writeFloat(br, self.scaleY, self.ctrlFlags >> 9, currentFrame)
        writeFloat(br, self.float_4, self.ctrlFlags >> 0xc, currentFrame)
        writeFloat(br, self.float_5, self.ctrlFlags >> 0xf, currentFrame)

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

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.morphIndex)
        br.write_uint32(len(self.morphTargets))
        for morphTarget in self.morphTargets:
            br.write_struct(morphTarget, currentFrame)

    def finalize(self, chunks):
        self.morph = chunks.get(self.morphIndex)

class morphTarget(BrStruct):
    def __br_read__(self, br: BinaryReader, currentFrame):
        morphValues = {}
        self.index = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.values = readFloat(br, morphValues, self.ctrlFlags, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.index)
        br.write_uint32(self.ctrlFlags)
        writeFloat(br, self.values, self.ctrlFlags, currentFrame)

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

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_int32(currentFrame)

    def finalize(self, chunks):
        pass


class objectFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.objectIndex = 0
        self.object = None
        self.name = ""
        self.ctrlFlags = 0
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

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.objectIndex)
        br.write_uint32(self.ctrlFlags)

        if self.ctrlFlags & 2 == 0:
            br.write_float32(self.position[0])
        if self.ctrlFlags & 4 == 0:
            br.write_float32(self.position[1])
        if self.ctrlFlags & 8 == 0:
            br.write_float32(self.position[2])
        
        if self.ctrlFlags & 10 == 0:
            br.write_float32(self.rotation[0])
        if self.ctrlFlags & 20 == 0:
            br.write_float32(self.rotation[1])
        if self.ctrlFlags & 40 == 0:
            br.write_float32(self.rotation[2])

        if self.ctrlFlags & 80 == 0:
            br.write_float32(self.scale[0])
        if self.ctrlFlags & 100 == 0:
            br.write_float32(self.scale[1])
        if self.ctrlFlags & 200 == 0:
            br.write_float32(self.scale[2])

        if self.ctrlFlags & 400 == 0:
            br.write_float32(self.opacity)
        if self.ctrlFlags & 800 == 0:
            br.write_uint32(self.has_model)

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


class distantLightController(BrStruct):
    def __init__(self):
        self.lightObject = None
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.color = {}
        self.float = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.lightIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.color = readColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        self.float = readFloat(br, self.float, self.ctrlFlags >> 9, currentFrame)   # intensity?

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)
        br.write_uint32(self.ctrlFlags)
        writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        writeColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        writeFloat(br, self.float, self.ctrlFlags >> 9, currentFrame)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]
        print(f"distantLightController: {self.lightObject.name}, index: {self.lightIndex}")

class distantLightFrame(BrStruct):
    def __init__(self):
        self.lightIndex = 0
        self.lightObject = None
        self.rotation = (0, 0, 0)
        self.color = (0, 0, 0, 1)
        self.intensity = 1
        self.frame = 0

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.lightIndex = br.read_uint32()
        self.lightObject = indexTable.Names[self.lightIndex][0]
        self.name = indexTable.Names[self.lightIndex][0]
        
        self.flags = br.read_uint32()
        self.rotation = br.read_float32(3)
        self.color = br.read_uint8(4)
        self.frame = currentFrame

        if self.flags & 0x20:
            self.intensity = br.read_float32()

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)

        br.write_uint32(self.flags)
        br.write_float32(self.rotation)
        br.write_uint8(self.color)

        if self.flags & 0x20:
            br.write_float32(self.intensity)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]


class ambientFrame(BrStruct):
    def __init__(self):
        self.color = (128, 128, 128, 255)
        self.frame = 0

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.color = br.read_uint8(4)
        self.frame = currentFrame


class noteFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.object = None
        self.name = ""

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.objectIndex = br.read_uint32()
        self.name = indexTable.Names[self.objectIndex][0]
        self.unk1 = br.read_uint32()
        self.unk2 = br.read_uint32()

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.objectIndex)
        br.write_uint32(self.unk1)
        br.write_uint32(self.unk2)

    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]


class directLightController(BrStruct):
    def __init__(self):
        self.lightObject = None
        self.position = {}         # positions ?
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.color = {}
        self.float_0 = {}
        self.float_1 = {}
        self.float_2 = {}
        self.float_3 = {}
        self.float_4 = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.lightIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.position = readVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.color = readColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        self.float_0 = readFloat(br, self.float_0, self.ctrlFlags >> 0x9, currentFrame)
        self.float_1 = readFloat(br, self.float_1, self.ctrlFlags >> 0xc, currentFrame)
        self.float_2 = readFloat(br, self.float_2, self.ctrlFlags >> 0xf, currentFrame)
        self.float_3 = readFloat(br, self.float_3, self.ctrlFlags >> 0x12, currentFrame)
        self.float_4 = readFloat(br, self.float_4, self.ctrlFlags >> 0x15, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)
        br.write_uint32(self.ctrlFlags)
        writeVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        writeColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        writeFloat(br, self.float_0, self.ctrlFlags >> 0x9, currentFrame)
        writeFloat(br, self.float_1, self.ctrlFlags >> 0xc, currentFrame)
        writeFloat(br, self.float_2, self.ctrlFlags >> 0xf, currentFrame)
        writeFloat(br, self.float_3, self.ctrlFlags >> 0x12, currentFrame)
        writeFloat(br, self.float_4, self.ctrlFlags >> 0x15, currentFrame)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]
        print(f"directLightController: {self.lightObject.name}, index: {self.lightIndex}")

class directLightFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.lightIndex = 0
        self.lightObject = None
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.color = (0, 0, 0, 1)

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.lightIndex = br.read_uint32()
        self.lightObject = indexTable.Names[self.lightIndex][0]
        self.name = indexTable.Names[self.lightIndex][0]
        self.frame = currentFrame

        self.flags = br.read_uint32()
        self.position = br.read_float32(3)
        self.rotation = br.read_float32(3)
        self.color = br.read_uint8(4)
        self.floats = br.read_float32(5)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]


class spotLightController(BrStruct):
    def __init__(self):
        self.lightObject = None
        self.position = {}
        self.rotationsEuler = {}
        self.rotationsQuat = {}
        self.color = {}
        self.float_0 = {}
        self.float_1 = {}
        self.float_2 = {}
        self.float_3 = {}
        self.float_4 = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.lightIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.position = readVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        self.rotationsEuler = readRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        self.rotationsQuat = readRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        self.color = readColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        self.float_0 = readFloat(br, self.float_0, self.ctrlFlags >> 0x9, currentFrame)
        self.float_1 = readFloat(br, self.float_1, self.ctrlFlags >> 0xc, currentFrame)
        self.float_2 = readFloat(br, self.float_2, self.ctrlFlags >> 0xf, currentFrame)
        self.float_3 = readFloat(br, self.float_3, self.ctrlFlags >> 0x12, currentFrame)
        self.float_4 = readFloat(br, self.float_4, self.ctrlFlags >> 0x15, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)
        br.write_uint32(self.ctrlFlags)
        writeVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        writeRotationEuler(br, self.rotationsEuler, self.ctrlFlags >> 3, currentFrame)
        writeRotationQuat(br, self.rotationsQuat, self.ctrlFlags >> 3, currentFrame)
        writeColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        writeFloat(br, self.float_0, self.ctrlFlags >> 0xc, currentFrame)
        writeFloat(br, self.float_1, self.ctrlFlags >> 0xf, currentFrame)
        writeFloat(br, self.float_2, self.ctrlFlags >> 0x12, currentFrame)
        writeFloat(br, self.float_3, self.ctrlFlags >> 0x15, currentFrame)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]
        print(f"spotLightController: {self.lightObject.name}, index: {self.lightIndex}")


class omniLightController(BrStruct):
    def __init__(self):
        self.lightIndex = 0
        self.ctrlFlags = 0
        self.lightObject = None
        self.vec3f = {}        # positions ?
        self.color = {}
        self.float_0 = {}
        self.float_1 = {}
        self.float_2 = {}

    def __br_read__(self, br: BinaryReader, currentFrame):
        self.lightIndex = br.read_uint32()
        self.ctrlFlags = br.read_uint32()
        self.vec3f = readVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        self.color = readColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        self.float_0 = readFloat(br, self.float_0, self.ctrlFlags >> 9, currentFrame)
        self.float_1 = readFloat(br, self.float_1, self.ctrlFlags >> 0xc, currentFrame)
        self.float_2 = readFloat(br, self.float_2, self.ctrlFlags >> 0xf, currentFrame)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)
        br.write_uint32(self.ctrlFlags)
        writeVector(br, self.vec3f, self.ctrlFlags, currentFrame)
        writeColor(br, self.color, self.ctrlFlags >> 6, currentFrame)
        writeFloat(br, self.float_0, self.ctrlFlags >> 9, currentFrame)
        writeFloat(br, self.float_1, self.ctrlFlags >> 0xc, currentFrame)
        writeFloat(br, self.float_2, self.ctrlFlags >> 0xf, currentFrame)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]
        print(f"omniLightController: {self.lightObject.name}, index: {self.lightIndex}")

class omniLightFrame(BrStruct):
    def __init__(self):
        self.frame = 0
        self.lightIndex = 0
        self.flags = 0
        self.lightObject = None
        self.position = (0, 0, 0)
        self.color = (0, 0, 0, 255)
        self.floats = (0, 0, 0)

    def __br_read__(self, br: BinaryReader, currentFrame, indexTable):
        self.lightIndex = br.read_uint32()
        self.lightObject = indexTable.Names[self.lightIndex][0]
        self.name = indexTable.Names[self.lightIndex][0]
        self.frame = currentFrame

        self.flags = br.read_uint32()
        self.position = br.read_float32(3)
        self.color = br.read_uint8(4)
        self.floats = br.read_float32(3)

    def __br_write__(self, br: BinaryReader, currentFrame):
        br.write_uint32(self.lightIndex)
        br.write_uint32(self.flags)
        br.write_float32(self.position)
        br.write_uint8(self.color)
        br.write_float32(self.floats)

    def finalize(self, chunks):
        self.lightObject = chunks[self.lightIndex]


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

def writeColor(br: BinaryReader, colorFrames, ctrlFlags, currentFrame):
    if ctrlFlags & 7 == 2:
        br.write_uint32(len(colorFrames))
        for f in colorFrames:
            br.write_uint32(f)
            br.write_uint8(colorFrames[f])
    elif ctrlFlags & 7 == 1:
        for f in colorFrames:
            br.write_uint8(colorFrames[f])
    return


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