from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes
from .Anms import *


class ccsStream(BrStruct):

    def __init__(self):
        self.name = "streamAnimation"
        self.type = "Stream"
        self.frameCount = 0
        self.chunks = []
        self.objectControllers = []
        self.objects = {}
        self.objectFrames = []

    def __br_read__(self, br: BinaryReader, name, ccsChunks, indexTable):
        self.name = name


        self.frameCount = br.read_uint32()
        currentFrame = 0
        while currentFrame != -1:
            #read chunk type
            #print(hex(br.pos()))
            chunkType = CCSTypes(br.read_uint16())
            #print(chunkType)
            br.seek(2, 1)
            chunkSize = br.read_uint32()
            
            if chunkType == CCSTypes.Frame:
                currentFrame = br.read_int32()
            elif chunkType == CCSTypes.ObjectController:
                objectCtrl = br.read_struct(objectController, None, currentFrame)
                self.objectControllers.append(objectCtrl)

            elif chunkType == CCSTypes.ObjectFrame:
                objF: objectFrame = br.read_struct(objectFrame, None, currentFrame, indexTable)
                obj = self.objects.get(objF.name)
                if not obj:
                    self.objects[objF.name] = {currentFrame: (objF.position, objF.rotation, objF.scale)}
                else:
                    self.objects[objF.name][currentFrame] = (objF.position, objF.rotation, objF.scale)
                #self.objectFrames.append(objF)
            else:
                chunkData = br.read_bytes(chunkSize * 4)
                self.chunks.append((chunkType, chunkData))

        '''for objf in self.objectFrames:
            objf.finalize(ccsChunks)'''

class ccsStreamOutlineParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamOutlineParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.layer = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamCelShadeParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamCelShadeParam"
        self.path = ""
        self.layer = None
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamToneShadeParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamToneShadeParam"
        self.path = ""
        self.object = None
        self.texture = None
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk = br.read_uint32()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]

        self.objectIndex = br.read_uint32()
        self.textureIndex = br.read_uint32()
    
    def finalize(self, chunks):
        self.object = chunks[self.objectIndex]
        self.texture = chunks[self.textureIndex]


class ccsStreamFBSBlurParam(BrStruct):
    def __init__(self):
        self.name = ""
        self.type = "StreamFBSBlurParam"
        self.path = ""
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.unk1 = br.read_uint16()
        self.unk2 = br.read_uint16()
        self.index = br.read_uint32()

        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
    
    def finalize(self, chunks):
        pass