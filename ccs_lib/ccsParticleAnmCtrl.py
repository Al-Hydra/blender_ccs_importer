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
        self.frameCount  = 0
        self.frames = []
        self.ctrlData = []

    def __br_read__(self, br: BinaryReader):
        self.partGeneratorIndex = br.read_uint32()
        self.objectIndex = br.read_uint32()
        self.extraIndex = br.read_uint32() # Extra Object index
        self.unk2 = br.read_uint32() # padding?

        self.frameCount = br.read_uint16()
        br.seek(2, 1)  # Skip CCCC
        '''print(f'PartAnmCtrl | GeneratorCtrl frameCount {self.frameCount}')
        self.frames = br.read_uint8(self.frameCount)
        br.align_pos(4)'''

        dataSize = (self.frameCount + 3) >> 2
        print(f'PartAnmCtrl | GeneratorCtrl dataSize = {dataSize}')
        if dataSize != 0:
            dataSize *= 4
            print(f'PartAnmCtrl | GeneratorCtrl dataSize*4 = {dataSize}')
            #self.ctrlData = br.read_uint8(dataSize * 4)
            while True:
                self.ctrlData.extend(br.read_uint8(4))
                if len(self.ctrlData) >= dataSize:
                    print(f'PartAnmCtrl | GeneratorCtrl self.ctrlData size = {len(self.ctrlData)}')
                    break

            print(f'PartAnmCtrl | GeneratorCtrl ctrlData {self.ctrlData}')


    def finalize(self, chunks):
        self.generator = chunks.get(self.partGeneratorIndex)
        self.object = chunks.get(self.objectIndex)

        #if self.extraIndex:
        self.extraObject = chunks.get(self.extraIndex)
        if self.extraObject:
            print(f'PartAnmCtrl | GeneratorCtrl extraObject index {self.extraIndex}')
            #raise ValueError(f' extraObject index ture: name {extraObject.name}, type {extraObject.type}')
            print(f' extraObject index ture: name {self.extraObject.name}, type {self.extraObject.type}')
            
