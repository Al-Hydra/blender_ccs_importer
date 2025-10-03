from .utils.PyBinaryReader.binary_reader import *
from collections import defaultdict


class ccsParticleAnmCtrl(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "ParticleAnmCtrl"
        self.path = ""
        self.animation = None
        self.ctrlCount = 0
        self.partGeneratorCtrl = []

    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        print(f'PartAnmCtrl | Name {self.name} index {self.index}')

        self.animationIndex = br.read_uint32()
        print(f'PartAnmCtrl | animationIndex {self.animationIndex}')

        self.ctrlCount = br.read_uint16()
        print(f'PartAnmCtrl | ctrlCount {self.ctrlCount}')
        br.seek(2, 1)  # Skip CCCC

        # Read and append ccPartGeneratorCtrl
        for i in range(self.ctrlCount):
            self.partGeneratorCtrl.append(br.read_struct(ccPartGeneratorCtrl, None))
            print(f'PartAnmCtrl | GeneratorCtrl # {i}')
        

    def __br_write__(self, br: BinaryReader, version=0x120):
        br.write_uint32(self.index)
        br.write_uint32(self.animationIndex)
        br.write_uint16(self.ctrlCount)
        br.write_uint16(0xCCCC)  # Write 0xCCCC bytes

        for generatorCtrl in self.partGeneratorCtrl:
            generatorCtrl: ccPartGeneratorCtrl
            br.write_struct(generatorCtrl)


    def finalize(self, chunks):
        #if self.animationIndex:
        self.animation = chunks.get(self.animationIndex)
        if self.animation:
            print(f'PartAnmCtrl finalize | {self.name} PartAnmCtrlIdx {self.index} AnmIdx {self.animationIndex}')
            print(f'PartAnmCtrl finalize | {self.name} {self.index} animation {self.animation.name}')

        for generatorCtrl in self.partGeneratorCtrl:
            generatorCtrl.finalize(chunks)
            print(f'PartAnmCtrl finalize | GeneratorCtrl {generatorCtrl.generator.name}')
            print(f'PartAnmCtrl finalize | GeneratorCtrl.ctrlData {generatorCtrl.ctrlBytes}')
            print(f'PartAnmCtrl finalize | GeneratorCtrl.ctrlData[1] {generatorCtrl.ctrlBytes[1]}')


class ccPartGeneratorCtrl(BrStruct):
#class generatorController(BrStruct):
    def __init__(self):
        self.generator = None
        self.object = None
        self.extraObject = None
        self.frameCount = 0
        self.frames = []
        self.ctrlBytes = []
        self.busyFlags = defaultdict(dict)
        self.floats = defaultdict(dict)
        self.strings = defaultdict(dict)

    def __br_read__(self, br: BinaryReader):
        self.partGeneratorIndex = br.read_uint32()
        self.objectIndex = br.read_uint32()
        self.extraIndex = br.read_uint32() # Extra Object index
        self.unk2 = br.read_uint32() # padding?

        self.frameCount = br.read_uint16()
        br.seek(2, 1)  # Skip CCCC

        dataSize = ((self.frameCount + 3) >> 2 ) * 4
        print(f'PartAnmCtrl | GeneratorCtrl dataSize = {dataSize}')
        if dataSize != 0:

            ctrlBuffer = BinaryReader(br.read_bytes(dataSize), encoding='cp932')
            self.ctrlBytes = bytes(ctrlBuffer.buffer())

            #for i in range(1, dataSize):
            for frame in range(dataSize):
                #ctrlData = ctrlBuffer
                ctrlBuffer.seek(frame, 0)
                ctrlFlag = ctrlBuffer.read_int8()
                getBusy(self, frame, ctrlFlag)

            # in rear cases ctrlBuffercontains floats
            for f32 in range(dataSize // 4):
                #ctrlData = ctrlBuffer
                ctrlBuffer.seek(f32 * 4, 0)
                self.floats[f32] = ctrlBuffer.read_float32()

            '''
            # in rear cases ctrlBuffer contains strings
            strings_Length = 0
            s = 0
            while strings_Length < dataSize:
                #ctrlData = ctrlBuffer
                ctrlBuffer.seek(strings_Length, 0)
                try:
                    string = ctrlBuffer.read_str()
                except:
                    strings_Length += 1 # skip empty strings
                    continue
                if string == "":
                    strings_Length += 1 # skip empty strings
                    continue

                self.strings[s] = string
                strings_Length += len(string.encode("cp932")) + 1 # +1 for null terminator
                s += 1
            '''

        print(f'PartAnmCtrl | GeneratorCtrl ctrlData {self.ctrlBytes}')
        print(f'PartAnmCtrl | GeneratorCtrl ctrlData[0] {self.ctrlBytes[1]}')
        print(f'PartAnmCtrl | self.busyFlags {range(self.frameCount)}, {range(dataSize)} | self.busyFlags {self.busyFlags}')
        print(f'PartAnmCtrl | floats {range(dataSize // 4)}, self.floats {self.floats}')
        print(f'PartAnmCtrl | self.strings {self.strings}')


    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.partGeneratorIndex)
        br.write_uint32(self.objectIndex)
        br.write_uint32(self.extraIndex) # Extra Object index
        br.write_uint32(self.unk2) # padding?

        br.write_uint16(self.frameCount)
        br.write_uint16(0xCCCC)  # Write 0xCCCC bytes

        dataSize = (self.frameCount + 3) >> 2
        if dataSize != 0:

            br.write_bytes(self.ctrlBytes)
            

    def finalize(self, chunks):
        self.generator = chunks.get(self.partGeneratorIndex)
        self.object = chunks.get(self.objectIndex)

        #if self.extraIndex:
        self.extraObject = chunks.get(self.extraIndex)
        if self.extraObject:
            print(f'PartAnmCtrl | GeneratorCtrl extraObject index {self.extraIndex}')
            #raise ValueError(f' extraObject index ture: name {extraObject.name}, type {extraObject.type}')
            print(f' extraObject index ture: name {self.extraObject.name}, type {self.extraObject.type}')
            

def getBusy(self, current_frame, ctrlFlag):
            #self.busyFlags[frame] = ctrlFlag
            if ctrlFlag == 1:
                self.busyFlags[current_frame] = 1
            elif ctrlFlag == 2:
                self.busyFlags[current_frame] = 0
            
            '''
            if ctrlFlag == 1:
                self.busyFlags[current_frame] = 1
            elif ctrlFlag == 2:
                self.busyFlags[current_frame] = 2
            else:
                self.busyFlags[current_frame] = 0
            '''