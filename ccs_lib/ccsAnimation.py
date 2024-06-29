from .utils.PyBinaryReader.binary_reader import *
from .ccsTypes import CCSTypes
from .Anms import *


class ccsAnimation(BrStruct):
    def __init__(self):
        self.name = ''
        self.type = "Animation"
        self.path = ''
        self.objectControllers = []
        self.morphControllers = []
        self.materialControllers = []
        self.objects = {}
        
    def __br_read__(self, br: BinaryReader, indexTable, version):
        self.index = br.read_uint32()
        self.name = indexTable.Names[self.index][0]
        self.path = indexTable.Names[self.index][1]
        
        self.frameCount = br.read_uint32()
        self.framesSectionSize = br.read_uint32()

        currentFrame = 0
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
            
            elif chunkType == CCSTypes.MorphController:
                morphCtrl = br.read_struct(morphController, None, currentFrame)
                self.morphControllers.append(morphCtrl)

            elif chunkType == CCSTypes.MaterialController:
                materialCtrl = br.read_struct(materialController, None, currentFrame)
                self.materialControllers.append(materialCtrl)

            else:
                chunkData = br.read_bytes(chunkSize * 4)
                #self.frames.append((chunkType, chunkData))
    
    def finalize(self, chunks):
        for objectCtrl in self.objectControllers:
            objectCtrl.finalize(chunks)
        

