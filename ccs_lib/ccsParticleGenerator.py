from .utils.PyBinaryReader.binary_reader import *
from enum import Enum


class ccsParticleGenerator(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "ParticleGenerator"
        self.path = ""
        self.resourceCount = 0
        self.forceFieldCount = 0
        self.generatorParam = None
        self.forceFieldParam = []
        self.resource = []

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        print(f'PartGen | Name {self.name}')

        self.unkIndex = br.read_uint32() # May  be unused

        flags = br.read_uint32()
        print(f'PartGen | HEX flags {flags:#010x}')
        self.pgcflags = setPGCflags(flags)
        print(f'PartGen | HEX pgcFlags {self.pgcflags:#04x}')
        pgpFlags = setPGPFlags(flags)
        print(f'PartGen | HEX pgpFlags {pgpFlags:#06x}')

        self.generatorParam = br.read_struct(ccParticleGeneratorParam, None, pgpFlags)

        # Get number of resources and forcefields
        self.resourceCount = ((flags >> 0x0c) & 0x0f)
        print(f'PartGen | {self.name} resourceCount = {self.resourceCount}')
        self.forceFieldCount = ((flags >> 0x10) & 0x0f)
        print(f'PartGen | {self.name} forceFieldCount = {self.forceFieldCount}')

        self.fade_400 = br.read_float()
        self.clip_50 = br.read_float()
        self.fade_4000 = br.read_float()
        self.clip_5000 = br.read_float()
        self.unk1 = br.read_float()
        self.unk2 = br.read_float()
        self.unk3 = br.read_float()

        # Read and append forceFieldParam
        for i in range(self.forceFieldCount):
            #self.forceField.append(br.read_struct(ForceField, None))
            self.forceFieldParam.append(br.read_struct(ccParticleForceFieldParam, None))
            print(f'PartGen | forceField# {i} Type ({self.forceFieldParam[i].type.value:#04x}) {self.forceFieldParam[i].type.name}')

        # Read and append forceFieldParam
        for i in range(self.resourceCount):
            self.resource.append(br.read_struct(PartResource, None, version))
            print(f'PartGen | resource# {i} index {self.resource[i].resourceIndex}')
    

    def finalize(self, chunks):
        #print("PartGen | finalize() called")  # Debug line
        for partResource in self.resource:
            partResource.finalize(chunks)

        for i in range(self.resourceCount):
            print(f'PartGen finalize | {self.name} resource # {i} index {self.resource[i].resourceIndex}')
    
        # Check for use of unkIndex
        if self.unkIndex:
            print(f'PartGen | {self.name} unkIndex = {self.unkIndex}')
            raise ValueError(f'PartGen | {self.name} unkIndex = {self.unkIndex}')  # Catch use of unkIndex


def setPGCflags(flags):
    pgcFlags = 0
    shiftFlag = (flags >> 0x0f) & 0xff  # Shift bits 22-15
    shiftFlag  = shiftFlag & 0x1e | shiftFlag & 0x60    # Mask bits 4 1 (0x1E) | bits 6 5 (0x60)
    bit0 = (flags >> 0x16) & 1      # Shidt bit 22 to bit 0
    pgcFlags = pgcFlags & 0x80 | shiftFlag | bit0

    return pgcFlags


def setPGPFlags(flags):
    pgpFlags = 0
    pgpFlags = (flags >> 0xb) & 0x6000 | ((flags >> 8) & 0xf) << 8 | pgpFlags & 0x8000

    return pgpFlags


class ccParticleGeneratorParam(BrStruct):
    def __init__(self):
        self.flags = 0

    def __br_read__(self, br: BinaryReader, pgpFlags):
        self.flags = pgpFlags
        self.unk01 = br.read_int16()
        print(f'PartGen  | GenParam unk01 -1 = {self.unk01}')
        br.seek(2, 1)  # Skip CCCC
        self.unk02 = br.read_float()
        self.unk03 = br.read_uint16()
        self.unk04 = br.read_uint16()
        self.unk05 = br.read_uint16()
        self.unk06 = br.read_uint16()
        self.unk07 = br.read_float()
        self.unk08 = br.read_float()
        self.unk09 = br.read_float()
        self.unk10 = br.read_float()
        self.unk11 = br.read_float()
        self.unk12 = br.read_int16()
        self.unk13 = br.read_int16()
        self.FadeInRate = br.read_int16() * 0.0004882813
        self.FadeOutRate = br.read_int16() * 0.0004882813
        #print(f'PartGen  | GenParam FadeInRate {self.FadeInRate}')
        #print(f'PartGen  | GenParam FadeOutRate {self.FadeOutRate}')
        print(f'PartGen  | GenParam pgpFlags >> 2 {pgpFlags >> 2:06x}, pgpFlags >> 4 {pgpFlags >> 4:06x}, pgpFlags >> 0xd {pgpFlags >> 0xd:06x}')


class PartResource(BrStruct):
    def __init__(self):
        self.partResource = None
        self.unk1 = 0   # Plays a role in changing Clut & Texture
        self.unk2 = 0   # Plays a role in changing Clut & Texture
        self.unk3 = 0   # Mask to 2 bits

    def __br_read__(self, br: BinaryReader, version):
        self.resourceIndex = br.read_uint32()   # CMP ANM EFF
        if version > 0x122:
            self.unk0 = br.read_int8()      # Plays a role in changing Clut & Texture
            self.unk1 = br.read_int8()      # Plays a role in changing Texture
            self.unk2 = br.read_int8()
            self.unk3 = br.read_int8() & 3  # Mask to 2 bits  # Skip CC

    def finalize(self, chunks):
        self.partResource = chunks.get(self.resourceIndex)
        print(f'PartGen finalize | partResource index {self.resourceIndex}')

        # check that partResource hase values resourceIndex may point to external chunk
        if self.partResource:
            print(f'PartGen finalize | partResource type {self.partResource.type}')
            print(f'PartGen finalize | partResource name {self.partResource.name}')


class ccParticleForceFieldParam(BrStruct):
    def __init__(self):
        self.type = None
        #self.Param = None

    def __br_read__(self, br: BinaryReader):
        br.seek(4, 1)  # Skip padding
        unk = br.read_uint8()
        self.unk0 = unk & 1
        self.unk1 = unk >> 1
        br.seek(1, 1)  # Skip CC
        self.type = ForceFieldTypes(br.read_uint8())
        br.seek(1, 1)
        self.unk2 = br.read_uint16()
        br.seek(2, 1)  # Skip CCCC
        #self.Param = br.read_struct(ForceFieldParam, None, self.type)
        self.value0 = br.read_float()
        self.value1 = br.read_float()
        self.value2 = br.read_float()
        self.value3 = br.read_float()
        self.value4 = br.read_float()


class ForceFieldTypes(Enum):
    ADDITION        = 0x00
    ACCELERATE      = 0x01
    REVOLUTION      = 0x02
    ROTATE          = 0x03
    ATTRACTIVE      = 0x04
    SCALE           = 0x05
    SCALE_X         = 0x06
    SCALE_Y         = 0x07
    SCALE_FIX       = 0x08
    SCALE_CHANGE    = 0x09
    ROTATE_2D       = 0x0a
    ROTATE_2D_FIX   = 0x0b
    ROTATE_3D_FIX   = 0x0c
    TRACE_POS       = 0x0d
    FADE_IN_OUT     = 0x0e
    ROTATE_AXIS     = 0x0f
    DIST_STOP       = 0x10

    NEW_ADDITION        = 0x11
    NEW_ACCELERATE      = 0x12
    NEW_REVOLUTION      = 0x13
    NEW_ROTATE          = 0x14
    NEW_ATTRACTIVE      = 0x15
    NEW_SCALE           = 0x16
    NEW_SCALE_X         = 0x17
    NEW_SCALE_Y         = 0x18
    NEW_SCALE_FIX       = 0x19
    NEW_SCALE_CHANGE    = 0x1a
    NEW_ROTATE_2D       = 0x1b
    NEW_ROTATE_2D_FIX   = 0x1c
    NEW_ROTATE_3D_FIX   = 0x1d
    NEW_TRACE_POS       = 0x1e
    NEW_FADE_IN_OUT     = 0x1f
    NEW_ROTATE_AXIS     = 0x20
    NEW_DIST_STOP       = 0x21

