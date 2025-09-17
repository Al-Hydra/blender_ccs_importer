from .utils.PyBinaryReader.binary_reader import *


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

        for i in range(self.ctrlCount):
            print(f'PartAnmCtrl finalize | GeneratorCtrl[{i}] {self.partGeneratorCtrl[i].generator.name}')


class ccPartGeneratorCtrl(BrStruct):
    def __init__(self):
        self.generator = None
        self.object = None
        self.extraObject = None
        self.count  = 0
        self.frames = []
        self.ctrlData = []

    def __br_read__(self, br: BinaryReader):
        self.partGeneratorIndex = br.read_uint32()
        self.objectIndex = br.read_uint32()
        self.extraIndex = br.read_uint32() # Extra Object index
        self.unk2 = br.read_uint32() # padding?

        self.count = br.read_uint16()
        br.seek(2, 1)  # Skip CCCC
        '''print(f'PartAnmCtrl | GeneratorCtrl frameCount {self.frameCount}')
        self.frames = br.read_uint8(self.frameCount)
        br.align_pos(4)'''

        self.dataCount = (self.count + 3) >> 2
        print(f'PartAnmCtrl | GeneratorCtrl dataSize = {self.dataCount}')
        if self.dataCount != 0:
            dataSize = self.dataCount * 4
            print(f'PartAnmCtrl | GeneratorCtrl dataSize*4 = {dataSize}')
            #self.ctrlData = br.read_uint8(dataSize * 4)
            while True:
                self.ctrlData.extend(br.read_uint8(4))
                if len(self.ctrlData) >= dataSize:
                    print(f'PartAnmCtrl | GeneratorCtrl self.ctrlData size = {len(self.ctrlData)}')
                    break

            print(f'PartAnmCtrl | GeneratorCtrl ctrlData {self.ctrlData}')


    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.partGeneratorIndex)
        br.write_uint32(self.objectIndex)
        br.write_uint32(self.extraIndex) # Extra Object index
        br.write_uint32(self.unk2) # padding?

        br.write_uint16(self.count)
        br.write_uint16(0xCCCC)  # Write 0xCCCC bytes

        self.dataCount = (self.count + 3) >> 2
        if self.dataCount != 0:

            br.write_bytes(bytes(self.ctrlData))
            

    def finalize(self, chunks):
        self.generator = chunks.get(self.partGeneratorIndex)
        self.object = chunks.get(self.objectIndex)

        #if self.extraIndex:
        self.extraObject = chunks.get(self.extraIndex)
        if self.extraObject:
            print(f'PartAnmCtrl | GeneratorCtrl extraObject index {self.extraIndex}')
            #raise ValueError(f' extraObject index ture: name {extraObject.name}, type {extraObject.type}')
            print(f' extraObject index ture: name {self.extraObject.name}, type {self.extraObject.type}')
            
