from .utils.PyBinaryReader.binary_reader import *
from .ccsClump import ccsClump
from .ccsModel import ccsModel, RigidMesh
from .ccsMaterial import ccsMaterial

def makeEffect(self):
    self.model = ccsModel()
    #self.model.name = (f'{self.name}_{self.name.replace("EFF_", "MDL_")}')
    self.model.name = self.name
    self.model.type = "Effect_Model"
    self.model.matFlags1 = self.matFlags1
    self.model.matFlags2 = self.matFlags2
    self.model.modelType = 0
    self.model.meshCount = 1
    self.model.vertexCount = 4
    self.model.mesh = RigidMesh()
    self.model.mesh.material = None
    self.model.mesh.vertices = []
        
    for i in range(self.model.vertexCount):
        vertex = EffectVertex(self, i)
        self.model.mesh.vertices.append(vertex)
        
def makeMaterial(self, texture):
    self.mesh.material = ccsMaterial()
    self.mesh.material.name = self.name.replace("EFF_", "MAT_")
    self.mesh.material.texture = texture


class EffectVertex:    
    def __init__(self, effect, v):
        self.position = [0, 0, 0]
        self.normals = (0, 0, 0)
        self.UV = [0, 0]
        if v == 0:
            self.position = [effect.vOffset_Left, effect.vOffset_Bottem, 0]
            self.UV = [0, 0]
        elif v == 1:
            self.position = [effect.vOffset_Right, effect.vOffset_Bottem, 0]
            self.UV = [effect.scaledX, 0]
        elif v == 2:
            self.position = [effect.vOffset_Left, effect.vOffset_Top, 0]
            self.UV = [0, effect.scaledY]
        else:
            self.position = [effect.vOffset_Right, effect.vOffset_Top, 0]
            self.UV = [effect.scaledX, effect.scaledY]
