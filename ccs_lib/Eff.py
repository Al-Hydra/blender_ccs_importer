from .utils.PyBinaryReader.binary_reader import *
from .ccsClump import ccsClump
from .ccsModel import ccsModel, RigidMesh
from .ccsMaterial import ccsMaterial

def makeEffect(effect):
    effect.model = ccsModel()
    effect.model.name = (f'{effect.name}_{effect.name.replace("EFF_", "MDL_")}')
    effect.model.type = "Effect_Model"
    effect.model.matFlags1 = effect.matFlags1
    effect.model.matFlags2 = effect.matFlags2
    effect.model.modelType = 0
    effect.model.meshCount = 1
    effect.model.vertexCount = 4
    effect.model.mesh = RigidMesh()
    effect.model.mesh.material = None
    effect.model.mesh.vertices = []
        
    for i in range(effect.model.vertexCount):
        vertex = EffectVertex(effect, i, effect.frameInfo)
        effect.model.mesh.vertices.append(vertex)
        
def makeMaterial(effect):
    effect.model.mesh.material = ccsMaterial()
    effect.model.mesh.material.name = effect.name.replace("EFF_", "MAT_")
    effect.model.mesh.material.texture = effect.texture


class EffectVertex:    
    def __init__(self, effect, v, frameInfo=None):
        self.position = [0, 0, 0]
        self.normals = (0, 0, 0)
        self.UV = [0, 0]
        if v == 0:
            self.position = [effect.vOffset_Left, effect.vOffset_Bottem, 0]
            self.UV = [effect.scaledX + effect.frameInfo[0].offsetX, effect.scaledY + effect.frameInfo[0].offsetY]
        elif v == 1:
            self.position = [effect.vOffset_Right, effect.vOffset_Bottem, 0]
            self.UV = [0 + effect.frameInfo[0].offsetX, effect.scaledY + effect.frameInfo[0].offsetY]
        elif v == 2:
            self.position = [effect.vOffset_Left, effect.vOffset_Top, 0]
            self.UV = [effect.scaledX + effect.frameInfo[0].offsetX, 0 + effect.frameInfo[0].offsetY]
        else:
            self.position = [effect.vOffset_Right, effect.vOffset_Top, 0]
            self.UV = [0 + effect.frameInfo[0].offsetX, 0 + effect.frameInfo[0].offsetY]
