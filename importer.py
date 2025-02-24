import bpy, bmesh, math, mathutils
from bpy.types import PropertyGroup, Operator, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty, CollectionProperty, IntProperty
from .ccs_lib.ccs import *
from mathutils import Vector, Matrix, Euler, Quaternion
from math import radians
import numpy as np
from time import perf_counter, time
from bpy_extras.io_utils import ImportHelper
from .ccs_lib.ccsAnimation import *
from .ccs_lib.ccsStream import *
import os, zlib
import cProfile
import pstats

class ccsObjectProperties(bpy.types.PropertyGroup):
    name: StringProperty(
        name="",
        default=""
    ) # type: ignore
    path: StringProperty(
        name="",
        default=""
    ) # type: ignore
    parent: StringProperty(
        name="",
        default=""
    ) # type: ignore
    clump: StringProperty(
        name="",
        default=""
    ) # type: ignore
    model: StringProperty(
        name="",
        default=""
    ) # type: ignore
    shadow: StringProperty(
        name="",
        default=""
    ) # type: ignore
    layer: StringProperty(
        name="",
        default=""
    ) # type: ignore


class ccsPropertyGroup(bpy.types.PropertyGroup):
    objects: CollectionProperty(type= ccsObjectProperties) # type: ignore
    
    def add_object(self, chunk, clumpName):
        blenderChunk = bpy.context.scene.ccs_importer.objects.get(chunk.name, self.objects.add())
        blenderChunk.name = chunk.name
        blenderChunk.path = chunk.path
        blenderChunk.parent = chunk.parent.name if chunk.parent else ""
        blenderChunk.clump = clumpName


class CCS_IMPORTER_OT_IMPORT(bpy.types.Operator, ImportHelper):
    bl_label = "Import CCS"
    bl_idname = "import_scene.ccs"


    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    filter_glob: StringProperty(default="*.ccs", options={"HIDDEN"}) # type: ignore
    filename_ext = ".ccs"
    filepath: StringProperty(subtype='FILE_PATH') # type: ignore

    swap_names: BoolProperty(name = "Swap Character Code", default = False) # type: ignore
    source_name: StringProperty(name= "Source Name") # type: ignore
    target_name: StringProperty(name = "Target Name") # type: ignore
    use_target_skeleton: BoolProperty(name = "Select a target skeleton") #type: ignore
    target_skeleton: StringProperty(name = "Target Armature") #type: ignore
    slice_name: BoolProperty(name = "Slice Names", default = False) #type: ignore
    slice_count: IntProperty(name = "Slice Count", default = 0) #type: ignore
    import_shadow: BoolProperty(name = "Import Shadow Meshes", default = False) #type: ignore
    find_missing_chunks: BoolProperty(name = "Find Missing Chunks", default = False) #type: ignore
    import_models: BoolProperty(name = "Import Models", default = True) #type: ignore
    import_animations: BoolProperty(name = "Import Animations", default = True) #type: ignore
    import_morphs: BoolProperty(name = "Import Morphs", default = True) #type: ignore
    import_cameras: BoolProperty(name = "Import Cameras", default = True) #type: ignore
    import_all_textures: BoolProperty(name = "Import All textures", default = True) #type: ignore
    import_stream: BoolProperty(name = "Import Scenes (Stream Chunks)", default = True) #type: ignore
    import_lights: BoolProperty(name = "Import Lights", default = True) #type: ignore

    
    def execute(self, context):

        start_time = time()
        '''profiler = cProfile.Profile()
        profiler.enable()'''

        ccsFiles = []

        if self.find_missing_chunks:

            for file in self.files:
                
                self.filepath = os.path.join(self.directory, file.name)

                ccsf = readCCS(self.filepath)

                ccsFiles.append(ccsf)
            
            ccsf1 = ccsFiles[0]

            all_chunks = {}

            for ccs in ccsFiles[1:]:
                for asset in ccs.assets.keys():
                    if not asset.startswith("#"):
                        for chunk in ccs.assets[asset]:
                            all_chunks[chunk.name] = chunk
            
            for ext in ccsf1.sortedChunks["ExternalObject"]:
                extObjName = ext.referencedObjectName[0]
                if extObjName in all_chunks:
                    ext.object = all_chunks[extObjName]
            
            importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)), ccsf1)

            importer.read(context)
        else:
            for file in self.files:
                
                self.filepath = os.path.join(self.directory, file.name)

                ccsf = readCCS(self.filepath)

                importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)), ccsf)

                importer.read(context)

        #profiler.disable()
        elapsed_s = "{:.2f}s".format(time() - start_time)
        self.report({'INFO'}, "CCS files imported in " + elapsed_s)
        
        #profile results
        '''stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats('cumtime')
        stats.print_stats()'''

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "import_models")
        row = layout.row()
        row.prop(self, "import_animations")

        if self.import_animations:
            row = layout.row()
            row.prop(self, "import_morphs")
        
        row = layout.row()
        row.prop(self, "import_cameras")
        row = layout.row()
        row.prop(self, "import_all_textures")
        row = layout.row()
        row.prop(self, "import_stream")
        row = layout.row()
        row.prop(self, "import_lights")
        

        row = layout.row()
        row.prop(self, "swap_names")
        row = layout.row()
        if self.swap_names:
            row.prop(self, "source_name")
            row = layout.row()
            row.prop(self, "target_name")
        
        
        row = layout.row()
        row.prop(self, "use_target_skeleton")
        if self.use_target_skeleton:
            row = layout.row()
            row.prop_search(self, "target_skeleton", bpy.data, "armatures")

        source_example = f"OBJ_{self.source_name}00t0 trall"
        target_example = f"OBJ_{self.target_name}00t0 trall"

        row = layout.row()
        row.prop(self, "slice_name")
        if self.slice_name:
            row.prop(self, "slice_count")
        

        if self.swap_names:
            row = layout.row()
            row.label(text = f"Old name example: {source_example[self.slice_count:]}")
            row = layout.row()
            row.label(text = f"New name example: {target_example[self.slice_count:]}")
        
        row = layout.row()
        row.prop(self, "find_missing_chunks")


            

class DropCCS(Operator):
    """Allows CCS files to be dropped into the viewport to import them"""
    bl_idname = "import_scene.drop_ccs"
    bl_label = "Import CCS"

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    filter_glob: StringProperty(default="*.ccs", options={"HIDDEN"}) # type: ignore
    index: IntProperty(name="Index") # type: ignore
    swap_names: BoolProperty(name = "Swap Character Code", default = False) # type: ignore
    source_name: StringProperty(name= "Source Name") # type: ignore
    target_name: StringProperty(name = "Target Name") # type: ignore
    use_target_skeleton: BoolProperty(name = "Select a target skeleton") #type: ignore
    target_skeleton: StringProperty(name = "Target Armature") #type: ignore
    slice_name: BoolProperty(name = "Slice Names", default = False) #type: ignore
    slice_count: IntProperty(name = "Slice Count", default = 0) #type: ignore
    import_shadow: BoolProperty(name = "Import Shadow Meshes", default = False) #type: ignore
    find_missing_chunks: BoolProperty(name = "Find Missing Chunks", default = False) #type: ignore
    import_models: BoolProperty(name = "Import Models", default = True) #type: ignore
    import_animations: BoolProperty(name = "Import Animations", default = True) #type: ignore
    import_morphs: BoolProperty(name = "Import Morphs", default = True) #type: ignore
    import_cameras: BoolProperty(name = "Import Cameras", default = True) #type: ignore
    import_all_textures: BoolProperty(name = "Import All textures", default = True) #type: ignore
    import_stream: BoolProperty(name = "Import Scenes (Stream Chunks)", default = True) #type: ignore
    import_lights: BoolProperty(name = "Import Lights", default = True) #type: ignore

    
    def execute(self, context):

        start_time = time()

        ccsFiles = []

        if self.find_missing_chunks:

            for file in self.files:
                
                self.filepath = os.path.join(self.directory, file.name)

                ccsf = readCCS(self.filepath)

                ccsFiles.append(ccsf)
            
            ccsf1 = ccsFiles[0]

            all_chunks = {}

            for ccs in ccsFiles[1:]:
                for asset in ccs.assets.keys():
                    if not asset.startswith("#"):
                        for chunk in ccs.assets[asset]:
                            all_chunks[chunk.name] = chunk
            
            for ext in ccsf1.sortedChunks["ExternalObject"]:
                extObjName = ext.referencedObjectName[0]
                if extObjName in all_chunks:
                    ext.object = all_chunks[extObjName]
            
            importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)), ccsf1)

            importer.read(context)
        else:
            for file in self.files:
                
                self.filepath = os.path.join(self.directory, file.name)

                ccsf = readCCS(self.filepath)

                importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)), ccsf)

                importer.read(context)


        elapsed_s = "{:.2f}s".format(time() - start_time)
        self.report({'INFO'}, "CCS files imported in " + elapsed_s)

        return {'FINISHED'}


class CCS_FH_import(bpy.types.FileHandler):
    bl_idname = "CCS_FH_import"
    bl_label = "File handler for CCS files"
    bl_import_operator = "import_scene.drop_ccs"
    bl_file_extensions = ".ccs"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')
    
    def draw():
        pass


class importCCS:
    def __init__(self, operator: Operator, filepath, import_settings: dict, ccsfile):
        self.operator = operator
        self.filepath = filepath
        for key, value in import_settings.items():
            setattr(self, key, value)
        
        self.ccsf: ccsFile = ccsfile
        

    def read(self, context):
        
        self.collection = bpy.data.collections.new(self.ccsf.name)
        self.emptiesCollection = bpy.data.collections.new(f"{self.ccsf.name} Empties")
        bpy.context.collection.children.link(self.collection)
        self.collection.children.link(self.emptiesCollection)
        
        
        if not bpy.data.collections.get("CCS Scene Manager"):
            ccs_manager_collection = bpy.data.collections.new("CCS Scene Manager")
            bpy.context.collection.children.link(ccs_manager_collection)
        else:
            ccs_manager_collection = bpy.data.collections.get("CCS Scene Manager")
        
        if not bpy.data.objects.get("CCS Scene Manager"):
            #create an empty object for CCS Scene Manager
            ccs_manager = bpy.data.objects.new("CCS Scene Manager", None)
            ccs_manager.empty_display_size = 0.01
            ccs_manager_collection.objects.link(ccs_manager)
        else:
            ccs_manager = bpy.data.objects.get("CCS Scene Manager")
        


        #clumps
        for cmpChunk in self.ccsf.sortedChunks["Clump"]:
            if bpy.data.armatures.get(cmpChunk.name):
                cmpChunk: ccsClump
                armature = bpy.data.armatures.get(cmpChunk.name)
                if len(cmpChunk.bones) > len(armature.bones):
                    self.updateClump(cmpChunk, armature)
            else:
                self.makeClump(cmpChunk)
        
        if self.import_all_textures:
            for tex in self.ccsf.sortedChunks["Texture"]:
                if not bpy.data.images.get(tex.name) and tex.textureData:
                    texture = tex.convertTexture()

                    img = bpy.data.images.new(tex.name, tex.width, tex.height, alpha=True)
                    img.pack(data=bytes(texture), data_len=len(texture))
                    img.source = 'FILE'

        
        if self.import_models:
            #objects
            for objChunk in self.ccsf.sortedChunks["Object"]:
                bObject = bpy.data.objects.new(objChunk.name, None)
                bObject.empty_display_size = 0.01
                self.emptiesCollection.objects.link(bObject)
                objectClump = bpy.data.objects.get(objChunk.clump.name) if objChunk.clump else None
                if objectClump:
                    #bObject.parent = objectClump
                    bObject["clump"] = objChunk.clump.name
                
                    if objChunk.parent:
                        #bObject.parent_type = "BONE"
                        #bObject.parent_bone = objChunk.parent.name
                        bObject["parent"] = objChunk.parent.name
                
                if objChunk.model:
                    bObject["model"] = objChunk.model.name
                    self.makeModels(objChunk.model, objChunk.clump, objChunk.name)


            #External Objects/ References
            for extChunk in self.ccsf.sortedChunks["ExternalObject"]:
                existRefObject = bpy.data.objects.get(extChunk.name)
                if not existRefObject:
                    bObject = bpy.data.objects.new(extChunk.name, None)
                    bObject.empty_display_size = 0.01
                    self.emptiesCollection.objects.link(bObject)
                    refObjectClump = bpy.data.objects.get(extChunk.clump.name) if extChunk.clump else None
                    if refObjectClump:
                        #bObject.parent = refObjectClump
                        bObject["clump"] = extChunk.clump.name 

                        if extChunk.parent:
                            #bObject.parent_type = "BONE"
                            #bObject.parent_bone = extChunk.parent.name if extChunk.parent else ""
                            bObject["parent"] = extChunk.parent.name

                    if extChunk.object:
                        #check if the object exist in blender
                        existing_object = bpy.data.objects.get(extChunk.object.name)
                        if existing_object: 
                            existingObjectModel = existing_object.get("Model")
                            bObject["model"] = existingObjectModel if existingObjectModel else None
                        else:
                            bObject["model"] = extChunk.name.replace("OBJ_", "MDL_")
                        
                        if extChunk.clump:
                            self.makeModels(extChunk.object.model, extChunk.clump, extChunk.name)
        

        if self.import_morphs:
            #morph chunks
            for morph in self.ccsf.sortedChunks["Morph"]:
                morph: ccsMorph
                morphModel = bpy.data.objects.get(morph.targetName)

                if morphModel:
                    morphModel.shape_key_add(name = "Basis")

        if self.import_cameras:
            #Cameras
            for cam in self.ccsf.sortedChunks["Camera"]:
                bCamera = bpy.data.cameras.get(cam.name)
                if not bCamera:
                    bCamera = bpy.data.cameras.new(cam.name)
                    cameraObject = bpy.data.objects.new(cam.name, bCamera)
                    self.collection.objects.link(cameraObject)

        if self.import_lights:
            # Distant Lights
            for light in self.ccsf.sortedChunks["Light"]:
                bLight = bpy.data.lights.get(light.name)
                if not bLight:
                    #check the light type
                    if light.lightType.value == 1:
                        bLight = bpy.data.objects.new(light.name, None)
                        bLight.empty_display_type = 'SINGLE_ARROW'
                        bLight.empty_display_size = 2
                        bLight.scale = (-1, -1, -1)
                        #set this object as the light direction object
                        ccs_manager["lightdir_object"] = bLight
                        
                        lightObject = bLight

                        
                    elif light.lightType.value == 2:
                        bLight = bpy.data.lights.new(name = light.name, type = 'AREA')
                        lightObject = bpy.data.objects.new(light.name, bLight)
                    elif light.lightType.value == 3:
                        bLight = bpy.data.lights.new(name = light.name, type = 'SPOT')
                        lightObject = bpy.data.objects.new(light.name, bLight)
                    elif light.lightType.value == 4:
                        bLight = bpy.data.objects.new(light.name, None)
                        bLight.empty_display_type = 'SPHERE'
                        bLight.empty_display_size = 0.5
                        
                        #set this object as the light point object
                        ccs_manager["lightpoint_object"] = bLight

                    
                        lightObject = bLight
                    self.collection.objects.link(lightObject)


        if self.import_animations:
            #Animations
            for anm in self.ccsf.sortedChunks["Animation"]:
                self.makeAction(anm)
        
        if self.import_stream:
            #Stream Chunk / Frame Chunk / Scene
            streamChunk: ccsStream = self.ccsf.stream
            if streamChunk.frameCount > 1:
                self.makeAction(streamChunk)



    def makeModels(self, model, clump, parentBone):
        model_name = parentBone.replace("OBJ_", "MDL_")
        if model != None and model.type == 'Model':
            if model.meshCount > 0 and model.modelType & 8 and self.import_shadow:
                for i, mesh in enumerate(model.meshes):
                    bm = bmesh.new()

                    verts = [bm.verts.new(v.position) for v in mesh.vertices]
                    bm.verts.ensure_lookup_table()
                    
                    triangles = [bm.faces.new((verts[t[0]], verts[t[1]], verts[t[2]])) for t in mesh.triangles]
                    bm.faces.ensure_lookup_table()                        

                    blender_mesh = bpy.data.meshes.new(f'{model_name}')
                    bm.to_mesh(blender_mesh)

                    obj = bpy.data.objects.new(f'{model_name}', blender_mesh)
                    self.collection.objects.link(obj)
            

            elif model.meshCount > 0 and model.modelType & 4 and not model.modelType & 2:
                #Create the object and its mesh data
                meshdata = bpy.data.meshes.new(f'{model_name}')
                obj = bpy.data.objects.new(f'{model_name}', meshdata)
                obj["emissive"] = 0
                obj["invert_colors"] = 0
                obj["opacity"] = 1
                if model.matFlags1 & 1:
                    obj["emissive"] = 1
                elif model.matFlags1 & 2:
                    obj["emissive"] = 1
                    obj["invert_colors"] = 1
                
                #find the armature and add all the bones to a dict
                armature = bpy.data.objects.get(clump.name)
                bone_indices = {}
                for i in range(len(armature.pose.bones)):
                    obj.vertex_groups.new(name = armature.pose.bones[i].name)
                    bone_indices[armature.pose.bones[i].name] = i
                
                normals = []
                vCount = 0
                bm = bmesh.new()
                vgroup_layer = bm.verts.layers.deform.new("Weights")
                uv_layer = bm.loops.layers.uv.new(f"UV")
                color_layer = bm.loops.layers.color.new(f"Color")

                for mesh in model.meshes:
                    
                    #add the mesh material
                    mat = self.makeMaterial(model, mesh)
                    mat_slot = obj.material_slots.get(mat.name)
                    if obj["emissive"]:
                            mat.surface_render_method = 'BLENDED'
                            mat.use_transparency_overlap = True
                    if mat_slot:
                        matIndex = mat_slot.slot_index
                    else:
                        obj.data.materials.append(mat)
                        mat_slot = obj.material_slots.get(mat.name)
                        matIndex = mat_slot.slot_index

                    #meshdata = self.makeMeshSingleWeight(meshdata, mesh, parent, bone_indices, matIndex, normals) 
                    self.makeMeshMultiWeight(bm, model, mesh, bone_indices, matIndex, normals, clump, vgroup_layer, uv_layer, color_layer, vCount)                       
                    vCount = len(bm.verts)
                
                bm.to_mesh(meshdata)
                bm.free()
                
                meshdata.normals_split_custom_set_from_vertices(normals)
    
                self.collection.objects.link(obj)
                obj.parent = armature

                #add armature modifier
                armature_modifier = obj.modifiers.new(name = f'{armature.name}', type = 'ARMATURE')
                armature_modifier.object = armature

            elif model.meshCount > 0 and model.modelType & 2:
                    for mesh in model.meshes:
                        meshdata = bpy.data.meshes.new(f'{model_name}')
                        obj = bpy.data.objects.new(f'{model_name}', meshdata)
                        obj["emissive"] = 0
                        obj["invert_colors"] = 0
                        obj["opacity"] = 1
                        if model.matFlags1 & 1:
                            obj["emissive"] = 1
                        elif model.matFlags1 & 2:
                            obj["emissive"] = 1
                            obj["invert_colors"] = 1

                        bone_indices = {}
                        parent_clump = bpy.data.objects.get(clump.name)
                        for i in range(len(parent_clump.pose.bones)):
                            obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                            bone_indices[parent_clump.pose.bones[i].name] = i

                        meshdata = self.makeMeshTriList(meshdata, model, mesh, bone_indices, parent_clump)

                        #add the mesh material
                        mat = self.makeMaterial(model, mesh)
                        if obj["emissive"]:
                            mat.surface_render_method = 'BLENDED'
                            mat.use_transparency_overlap = True
                        obj.data.materials.append(mat)

                        if model.clump:
                            clump = bpy.data.objects.get(model.clump.name)
                            parent = clump.pose.bones.get(model.parentBone.name)
                            if parent:
                                meshdata.transform(parent.matrix)

                            obj.parent = clump
                            
                    #add armature modifier
                    armature_modifier = obj.modifiers.new(name = f'{parent_clump.name}', type = 'ARMATURE')
                    armature_modifier.object = parent_clump
                    self.collection.objects.link(obj)

            else:
                #single bone
                if model.meshCount > 0 and model.modelType < 2:
                    #Create the object and its mesh data
                    meshdata = bpy.data.meshes.new(f'{model_name}')
                    obj = bpy.data.objects.new(f'{model_name}', meshdata)
                    obj["emissive"] = 0
                    obj["invert_colors"] = 0
                    obj["opacity"] = 1
                    if model.matFlags1 & 1:
                        obj["emissive"] = 1
                    elif model.matFlags1 & 2:
                        obj["emissive"] = 1
                        obj["invert_colors"] = 1
                    
                    #find the armature and add all the bones to a dict
                    if not hasattr(clump, "name"):
                        breakpoint()
                    armature = bpy.data.objects.get(clump.name)
                    parent = armature.data.bones.get(parentBone)
                    if not parent:
                        parent = armature.data.bones[0]

                    bone_indices = {}
                    for i in range(len(armature.pose.bones)):
                        obj.vertex_groups.new(name = armature.pose.bones[i].name)
                        bone_indices[armature.pose.bones[i].name] = i
                    
                    normals = []
                    bm = bmesh.new()
                    uv_layer = bm.loops.layers.uv.new(f"UV")
                    color_layer = bm.loops.layers.color.new(f"Color")
                    vgroup_layer = bm.verts.layers.deform.new("Weights")
                    vCount = 0

                    for m, mesh in enumerate(model.meshes):
                        #add the mesh material
                        mat = self.makeMaterial(model, mesh)
                        if obj["emissive"]:
                            mat.surface_render_method = 'BLENDED'
                            mat.use_transparency_overlap = True
                        mat_slot = obj.material_slots.get(mat.name)
                        if mat_slot:
                            matIndex = mat_slot.slot_index
                        else:
                            obj.data.materials.append(mat)
                            mat_slot = obj.material_slots.get(mat.name)
                            matIndex = mat_slot.slot_index
                        
                        self.makeMeshSingleWeight(bm, mesh, parent, bone_indices, matIndex, normals, uv_layer, color_layer, vgroup_layer, vCount)
                        vCount = len(bm.verts)
                    
                    bm.to_mesh(meshdata)
                    
                    meshdata.normals_split_custom_set_from_vertices(normals)

                    obj.modifiers.new(name = 'Armature', type = 'ARMATURE')
                    obj.modifiers['Armature'].object = armature
                    #set the active color layer
                    meshdata.vertex_colors.active = meshdata.vertex_colors[0]

                    obj.parent = armature

                    self.collection.objects.link(obj)


    def makeMaterial(self, model, mesh):
        ccs_material = mesh.material
        if not ccs_material:
            mat = bpy.data.materials.get("ccsMaterial").copy()
            mat["uvOffset"] = [0, 0, 1, 1]
            return mat

        mat = bpy.data.materials.get(f'{model.name}_{ccs_material.name}')
        if not mat:
            #check if ccsMaterial exists already
            mat = bpy.data.materials.get("ccsMaterial")
            

            if not mat:
                ccsMaterial_path = r"materials\ccsMaterial.blend"
                importer_path = os.path.realpath(__file__)
                dir_path = os.path.dirname(importer_path)

                ccsMaterial_path = os.path.join(dir_path, ccsMaterial_path)
                
                with bpy.data.libraries.load(ccsMaterial_path) as (data_from, data_to):
                    material_name = data_from.materials[1]
                    data_to.materials = ["ccsMaterial"]

                mat = bpy.data.materials["ccsMaterial"].copy()
            else:
                mat = mat.copy()
                mat["uvOffset"] = [0, 0, 1, 1]
            
            mat.name = f'{model.name}_{ccs_material.name}'
            
            #add image texture
            tex = ccs_material.texture
            img = None
            if hasattr(tex, "name"):
                img = bpy.data.images.get(tex.name)    
                
                if not img and tex.type == 'Texture' and tex.textureData:
                    texture = tex.convertTexture()

                    img = bpy.data.images.new(tex.name, tex.width, tex.height, alpha=True)
                    img.pack(data=bytes(texture), data_len=len(texture))
                    img.source = 'FILE'
                
                texture_node = mat.node_tree.nodes["ccsTexture"]
                texture_node.image = img

                mat["uvOffset"] = [ccs_material.offsetX, ccs_material.offsetY, ccs_material.scaleX, ccs_material.scaleY]
        else:
            mat["uvOffset"] = [ccs_material.offsetX, ccs_material.offsetY, ccs_material.scaleX, ccs_material.scaleY]
        
        mat.use_backface_culling = True
            
        return mat


    def makeMeshSingleWeight(self, bm, mesh, parent, boneIndices, matIndex, normals,uv_layer, color_layer, vgroup_layer, vCount):

            boneID = boneIndices[parent.name]

            #Triangles
            direction = 1
            for i, v in enumerate(mesh.vertices):

                #transform vertices by their parent bone
                vp = Matrix(parent["matrix"]) @ Vector(v.position)
                vn = Matrix(parent["matrix"]).to_3x3() @ Vector(v.normal)

                bmVertex = bm.verts.new(vp)
                bmVertex[vgroup_layer][boneID] = 1
                
                #normals must be normalized
                normals.append(vn.normalized())


                bm.verts.ensure_lookup_table()
                bm.verts.index_update()

                flag = v.triangleFlag
                
                if flag == 1:
                    direction = 1
                elif flag == 2:
                    direction = -1
                
                if flag == 0:
                    if direction == 1:
                        face = bm.faces.new((bm.verts[vCount + i-2], bm.verts[vCount + i-1], bm.verts[vCount + i]))
                    elif direction == -1:
                        face = bm.faces.new((bm.verts[vCount + i], bm.verts[vCount + i-1], bm.verts[vCount + i-2]))
                    
                    face.material_index = matIndex  
                    face.smooth = True
                    for loop in face.loops:
                        loop[uv_layer].uv = mesh.vertices[loop.vert.index - vCount].UV
                        color = mesh.vertices[loop.vert.index - vCount].color
                        loop[color_layer] = [(c / 255) for c in color]
                    
                    #we need to flip the direction for the next face
                    direction *= -1
            
            bm.faces.ensure_lookup_table()


    def makeMeshTriList(self, meshdata, model, mesh, bone_indices, parent_clump):
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new(f"UV")
        vgroup_layer = bm.verts.layers.deform.new("Weights")
        color_layer = bm.loops.layers.color.new(f"Color")

        normals = []

        bonesList = [b.name for b in parent_clump.data.bones]

        for i, ccsVertex in enumerate(mesh.vertices):
            #calculate vertex final position
            vertex_matrix1 = parent_clump.data.bones[ccsVertex.boneIDs[0]]["matrix"]
            vertex_matrix2 = parent_clump.data.bones[ccsVertex.boneIDs[1]]["matrix"]
            
            vp1 = (Matrix(vertex_matrix1) @ Vector(ccsVertex.positions[0]) * ccsVertex.weights[0]) 
            vn1 = Matrix(vertex_matrix1).to_3x3() @ Vector(ccsVertex.normals[0])

            vp2 = (Matrix(vertex_matrix2) @ Vector(ccsVertex.positions[1]) * ccsVertex.weights[1])

            #if ccsVertex.boneIDs[1] != "":
                #vp2 = (vertex_matrix2 @ Vector(ccsVertex.positions[1]) * ccsVertex.weights[1])
                #vn2 = Vector(ccsVertex.normals[1])
            #else:
            #vp2 = Vector((0,0,0))
            #vn2 = Vector((0,0,0))
            

            bmVertex = bm.verts.new(vp1 + vp2)

            normals.append(vn1.normalized())   

            bm.verts.ensure_lookup_table()
            bm.verts.index_update()

            #add vertex weights
            boneID1 = bone_indices[bonesList[ccsVertex.boneIDs[0]]]
            boneID2 = bone_indices[bonesList[ccsVertex.boneIDs[1]]]

            if ccsVertex.weights[0] == 1:
                    bmVertex[vgroup_layer][boneID1] = 1
            else:
                bmVertex[vgroup_layer][boneID1] = ccsVertex.weights[0]
                bmVertex[vgroup_layer][boneID2] = ccsVertex.weights[1]
            
        for i in range(len(mesh.triangleIndices)):
            flag = mesh.triangleFlags[i]
            if flag == 0:
                try:
                    vert1 = mesh.triangleIndices[i-2]
                    vert2 = mesh.triangleIndices[i-1]
                    vert3 = mesh.triangleIndices[i]
                    face = bm.faces.new((bm.verts[vert1], bm.verts[vert2], bm.verts[vert3]))
                    face.smooth = True

                    triUV1 = mesh.uvs[i-2]
                    triUV2 = mesh.uvs[i-1]
                    triUV3 = mesh.uvs[i]

                    face.loops[0][uv_layer].uv = triUV1
                    face.loops[1][uv_layer].uv = triUV2
                    face.loops[2][uv_layer].uv = triUV3
                    
                    face.loops[0][color_layer] = 1, 1, 1, 1
                    face.loops[1][color_layer] = 1, 1, 1, 1
                    face.loops[2][color_layer] = 1, 1, 1, 1
                except:
                    print(f"error at {i}")

            bm.faces.ensure_lookup_table()

        bm.to_mesh(meshdata)

        meshdata.normals_split_custom_set_from_vertices(normals)
        return meshdata
    
    def makeMeshMultiWeight(self, bm, model, mesh, bone_indices, matIndex, normals, clump: ccsClump, vgroup_layer, uv_layer, color_layer, vCount): 
        
        
        if not model.lookupList:
            bones = [bone for bone in clump.bones.values()]
        else:
            bones = [clump.bones[clump.boneIndices[i]] for i in model.lookupList]

        for i, ccsVertex in enumerate(mesh.vertices):
            #calculate vertex final position
            boneID1 = bones[ccsVertex.boneIDs[0]]
            boneID2 = bones[ccsVertex.boneIDs[1]]
            boneID3 = bones[ccsVertex.boneIDs[2]]
            boneID4 = bones[ccsVertex.boneIDs[3]]

            vertex_matrix1 = Matrix(boneID1.matrix)
            vertex_matrix2 = Matrix(boneID2.matrix)
            vertex_matrix3 = Matrix(boneID3.matrix)
            vertex_matrix4 = Matrix(boneID4.matrix)

            #positions
            vp1 = (vertex_matrix1 @ Vector(ccsVertex.positions[0]) * ccsVertex.weights[0]) 
            vp2 = (vertex_matrix2 @ Vector(ccsVertex.positions[1]) * ccsVertex.weights[1])
            vp3 = (vertex_matrix3 @ Vector(ccsVertex.positions[2]) * ccsVertex.weights[2])
            vp4 = (vertex_matrix4 @ Vector(ccsVertex.positions[3]) * ccsVertex.weights[3])

            #normals
            vn1 = vertex_matrix1.to_3x3() @ Vector(ccsVertex.normals[0]) 
            #vn2 = vertex_matrix2.to_3x3() @ Vector(ccsVertex.normals[1])
            #vn3 = vertex_matrix3.to_3x3() @ Vector(ccsVertex.normals[2])
            #vn4 = vertex_matrix4.to_3x3() @ Vector(ccsVertex.normals[3])
            normal = vn1 #+ vn2 + vn3 + vn4  #only the first normals vector is needed

            bmVertex = bm.verts.new(vp1 + vp2 + vp3 + vp4)

            #normals must be normalized
            normals.append(normal.normalized())
            
            bm.verts.ensure_lookup_table()
            bm.verts.index_update()            

            #add vertex groups with 0 weights
            boneID1 = bone_indices[boneID1.name]
            boneID2 = bone_indices[boneID2.name]
            boneID3 = bone_indices[boneID3.name]
            boneID4 = bone_indices[boneID4.name]
            
            bmVertex[vgroup_layer][boneID1] = 0
            bmVertex[vgroup_layer][boneID2] = 0
            bmVertex[vgroup_layer][boneID3] = 0
            bmVertex[vgroup_layer][boneID4] = 0

            bmVertex[vgroup_layer][boneID1] += ccsVertex.weights[0]
            bmVertex[vgroup_layer][boneID2] += ccsVertex.weights[1]
            bmVertex[vgroup_layer][boneID3] += ccsVertex.weights[2]
            bmVertex[vgroup_layer][boneID4] += ccsVertex.weights[3]


            flag = ccsVertex.triangleFlag
            
            if flag == 1:
                direction = 1
            elif flag == 2:
                direction = -1
            
            if flag == 0:
                if direction == 1:
                    face = bm.faces.new((bm.verts[vCount + (i-2)], bm.verts[vCount + (i-1)], bm.verts[vCount + i]))
                elif direction == -1:
                    face = bm.faces.new((bm.verts[vCount + i], bm.verts[vCount + i-1], bm.verts[vCount + i-2]))
                face.material_index = matIndex
                face.smooth = True
                for loop in face.loops:
                    loop[uv_layer].uv = mesh.vertices[loop.vert.index - vCount].UV
                    loop[color_layer] = 1, 1, 1, 1
                    #loop[color_layer] = mesh.vertices[loop.vert.index].color
                #we need to flip the direction for the next face
                direction *= -1
        
        #clean up the mesh
        #bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.000001)




    def makeClump(self, cmp):
        armname = cmp.name

        clump = bpy.data.armatures.new(armname)
        clump.display_type = 'STICK'
        clumpobj = bpy.data.objects.new(armname, clump)
        clumpobj.show_in_front = True
        
        self.collection.objects.link(clumpobj)

        bpy.context.view_layer.objects.active = clumpobj
        bpy.ops.object.editmode_toggle()

        importerProp = bpy.context.scene.ccs_importer

        for b in cmp.bones.values():
            bone = clump.edit_bones.new(b.name)

            bone_object = b.object

            importerProp.add_object(bone_object, cmp.name)

            bone.use_deform = True
            bone.tail = Vector((0, 0.01, 0))
            
            rotation = Euler((radians(x) for x in b.rot), "ZYX").to_quaternion()

            if b.parent:
                b.matrix = Matrix(b.parent.matrix) @ Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            else:
                b.matrix = Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            
            bone.matrix = b.matrix
            
            bone["original_coords"] = [b.pos, b.rot, b.scale]
            bone["rotation_quat"] = rotation
            bone["matrix"] = b.matrix

            bone.parent = clump.edit_bones[b.parent.name] if b.parent else None
        
        bpy.ops.object.editmode_toggle()


    def updateClump(self, cmp, armature):
        armname = cmp.name

        armature_object = self.collection.objects.get(armature.name)
        if not armature_object:
            armature_object = bpy.data.objects.new(armname, armature)
            armature_object.show_in_front = True
            
            self.collection.objects.link(armature_object)


        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode = 'EDIT')

        importerProp = bpy.context.scene.ccs_importer

        for b in cmp.bones.values():
            if armature.bones.get(b.name):
                continue
            bone = armature.edit_bones.new(b.name)

            bone_object = b.object

            importerProp.add_object(bone_object, cmp.name)

            bone.use_deform = True
            bone.tail = Vector((0, 0.01, 0))
            
            rotation = Euler((radians(x) for x in b.rot), "ZYX").to_quaternion()

            if b.parent:
                b.matrix = Matrix(b.parent.matrix) @ Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            else:
                b.matrix = Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            
            bone.matrix = b.matrix
            
            bone["original_coords"] = [b.pos, b.rot, b.scale]
            bone["rotation_quat"] = rotation
            bone["matrix"] = b.matrix

            bone.parent = armature.edit_bones[b.parent.name] if b.parent else None
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
    

    def makeAction(self, anim):
        action = bpy.data.actions.new(anim.name)
        
        scene_action = bpy.data.actions.new(f"{anim.name}_CCS_Scene")
        
        #set fps to 30
        bpy.context.scene.render.fps = 30

        #adjust the timeline
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = anim.frameCount - 1

        source = self.source_name
        target = self.target_name

        for objCtrl in anim.objectControllers:
            objCtrl: objectController
            ccsAnmObj = objCtrl.object
            target_bone = ccsAnmObj.name

            #if ccsAnmObj.name.find(source) != -1:
                #target_bone = ccsAnmObj.name.replace(source, target)
            
            if ccsAnmObj.clump:
                clump = ccsAnmObj.clump.name
            else:
                #try to get it from blender
                clump = bpy.context.scene.ccs_importer.objects.get(target_bone)
                if clump:
                    clump = clump.clump
                else:
                    continue

            if self.use_target_skeleton:
                target_armature = bpy.data.objects.get(self.target_skeleton)
                target_armature.animation_data_create()
                target_armature.animation_data.action = action

            armatureObj = bpy.data.objects.get(clump)

            armatureObj.animation_data_create()
            armatureObj.animation_data.action = action
            posebone = armatureObj.pose.bones.get(target_bone)

            if not posebone:
                continue    

            bone = armatureObj.data.bones.get(posebone.name)

            bloc = Vector(bone["original_coords"][0]) * 0.01
            brot = Quaternion(bone["rotation_quat"])
            bscale = Vector(bone["original_coords"][2])

            group_name = action.groups.new(name = posebone.name).name
            #group_name = posebone.name

            if self.swap_names:
                if ccsAnmObj.name.find(source) != -1:
                    new_bone_name = posebone.name.replace(source, target)

                    if self.slice_name:
                        new_bone_name = new_bone_name[self.slice_count:]
                    
                    if self.use_target_skeleton:
                        if target_armature.get(new_bone_name):
                            new_bone_name = target_armature.get(new_bone_name)

                    group_name = action.groups.new(name = new_bone_name).name
            
            bone_path = f'pose.bones["{group_name}"]'

            locations = self.convertVectorLocation(objCtrl.positions.items(), bloc, brot.inverted())
            data_path = f'{bone_path}.{"location"}'
            self.insertFrames(action, group_name, data_path, locations, 3)
            
            #Rotations Euler
            rotations = self.convertEulerRotation(objCtrl.rotationsEuler.items(), brot.inverted())
            data_path = f'{bone_path}.{"rotation_quaternion"}'
            self.insertFrames(action, group_name, data_path, rotations, 4)
            
            #Rotations Quaternion
            rotations_quat = self.convertQuaternionRotation(objCtrl.rotationsQuat.items(), brot)
            
            data_path = f'{bone_path}.{"rotation_quaternion"}'
            self.insertFrames(action, group_name, data_path, rotations_quat, 4)

            scales = self.convertVectorScale(objCtrl.scales.items(), bscale)
            data_path = f'{bone_path}.{"scale"}'
            self.insertFrames(action, group_name, data_path, scales, 3)
        
        for obj in anim.objects.keys():

            target_bone = obj

            if obj.find(source) != -1:
                target_bone = obj.replace(source, target)

            #try to get it from blender
            '''if target_bone.startswith("OBJ_1nrk"):
                breakpoint()'''
            clump_ref = None
            clump = bpy.context.scene.ccs_importer.objects.get(target_bone)
            if clump:
                clump = clump.clump
            else:
                #attempt to get it from the scene
                empty_obj = bpy.data.objects.get(target_bone)
                
                if empty_obj:
                    clump_ref = empty_obj.get("clump")
                
                if clump_ref:
                    clump = bpy.data.objects.get(clump_ref).name

                
                else:
                    continue

            armatureObj = bpy.data.objects.get(clump)

            armatureObj.animation_data_create()
            armatureObj.animation_data.action = action

            posebone = armatureObj.pose.bones.get(target_bone)
            if not posebone:
                continue

            bone = armatureObj.data.bones.get(posebone.name)
            bloc = Vector(bone["original_coords"][0]) * 0.01
            brot = Quaternion(bone["rotation_quat"]).inverted()
            bscale = Vector(bone["original_coords"][2])

            group_name = action.groups.new(name = posebone.name).name

            bone_path = f'pose.bones["{group_name}"]'

            locations = {}
            rotations = {}
            scales = {}
            opacity_dict = {}
            startQuat = brot
            for frame, locrotscaleop in anim.objects[obj].items():
                loc, rot, scale, opacity = locrotscaleop

                loc = Vector(loc) * 0.01
                bind_loc = Vector(bloc)
                loc.rotate(brot)
                bind_loc.rotate(brot)

                locations[frame] = loc - bind_loc

                endQuat = brot @ Euler((radians(x) for x in rot), "ZYX").to_quaternion()

                if startQuat.dot(endQuat) < 0:
                    endQuat.negate()
                
                rotations[frame] = endQuat
                startQuat = endQuat

                scale_factor = Vector([s / b for s, b in zip(scale, bscale)])
                scales[frame] = scale_factor
                
                opacity_dict[frame] = [opacity]
                
            data_path = f'{bone_path}.{"location"}'
            self.insertFrames(action, group_name, data_path, locations, 3)

            data_path = f'{bone_path}.{"rotation_quaternion"}'
            self.insertFrames(action, group_name, data_path, rotations, 4)
            
            data_path = f'{bone_path}.{"scale"}'
            self.insertFrames(action, group_name, data_path, scales, 3)
            
            data_path = f'{bone_path}.{"opacity"}'
            self.insertFrames(action, group_name, data_path, opacity_dict, 1)
            
            
        
        
        if self.import_morphs:
            for morphF in anim.morphs:
                morphF: morphFrame
                sourceModel = f"MDL_{morphF[4:]}"
                if not sourceModel:
                    continue
                sourceModelBlender = bpy.data.objects.get(sourceModel)
                
                if sourceModelBlender:
                    #check if a Basis shape key exists
                    basisShapeKey = sourceModelBlender.data.shape_keys.key_blocks.get("Basis")
                    if not basisShapeKey:
                        sourceModelBlender.shape_key_add(name = "Basis")
                    
                    sourceModelBlender.animation_data_create()
                    sourceModelBlender.animation_data.action = action
                    
                    for target in anim.morphs[morphF].keys():
                        #check if the source model has a shape key for this target
                        targetShapeKey = sourceModelBlender.data.shape_keys.key_blocks.get(morphF)
                        if not targetShapeKey:
                            targetShapeKey = sourceModelBlender.shape_key_add(name = morphF)
                            targetModelBlender = bpy.data.objects.get(target)

                            if targetModelBlender:
                                for i in range(len(targetModelBlender.data.vertices)):
                                    try:
                                        targetShapeKey.data[i].co = targetModelBlender.data.vertices[i].co
                                    except:
                                        print(f"Error at {targetShapeKey.name}")
                    

                                data_path = f'data.shape_keys.key_blocks["{targetShapeKey.name}"].value'
                                
                                morph_values = {f: [1 - anim.morphs[morphF][target][f][0]] for f in anim.morphs[morphF][target].keys()}
                                
                                self.insertFrames(action, targetShapeKey.name, data_path, morph_values, 1)
                    #except:
                    #    print(f"Error at {targetShapeKey.name}")

        

        for cam in anim.cameras.keys():
            cameraObject = self.collection.objects.get(cam)

            group_name = action.groups.new(name = cam).name

            if cameraObject:
                #create a separate action for each camera
                camera_action = bpy.data.actions.new(f"{anim.name} ({cam})")
                #apply the animation on the camera
                cameraObject.animation_data_create()
                cameraObject.animation_data.action = camera_action

                locations = {}
                rotations = {}
                fovs = {}
                for frame, values in anim.cameras[cam].items():
                    loc, rot, fov = values
                    locations[frame] = Vector(loc) * 0.01
                    rotations[frame] = [radians(r) for r in rot] 
                    fovs[frame] = [cameraObject.data.sensor_width / (2 * math.tan(radians(fov) / 2))]

                data_path = f'{"location"}'
                self.insertFrames(camera_action, group_name, data_path, locations, 3)
                
                data_path = f'{"rotation_euler"}'
                self.insertFrames(camera_action, group_name, data_path, rotations, 3)
                
                data_path = f'{"data.lens"}'
                self.insertFrames(camera_action, group_name, data_path, fovs, 1)
        
        for light in anim.lights.keys():
            if light == "Ambient":
                ambient = anim.lights[light]
                scene_manager = bpy.context.scene.ccs_manager
                
                group_name = scene_action.groups.new(name = f"Ambient").name
                
                ambient_color = {}
                for frame, values in ambient.items():
                    ambient_color[frame] = [c / 255 for c in values]
                    
                data_path = f'{"ccs_manager.ambient_color"}'
                self.insertFrames(scene_action, group_name, data_path, ambient_color, 4)
                
                
            lightObject = self.collection.objects.get(light)

            group_name = action.groups.new(name = light).name

            if lightObject:
                #create a separate action for each light
                light_action = bpy.data.actions.new(f"{anim.name} ({light})")
                #apply the animation on the light
                lightObject.animation_data_create()
                lightObject.animation_data.action = light_action
                
                #create a scene manager action
                light_scene_manager_action = scene_action
                bpy.context.scene.animation_data_create()
                bpy.context.scene.animation_data.action = light_scene_manager_action
                

                locations = {}
                rotations = {}
                energy = {}
                color = {}
                for frame, values in anim.lights[light].items():
                    rot, col, en = values
                    rotations[frame] = [radians(r) for r in rot] 
                    energy[frame] = [en]
                    color[frame] = [c / 255 for c in col]

                data_path = f'{"rotation_euler"}'
                self.insertFrames(light_action, group_name, data_path, rotations, 3)
                
                data_path = f'{"ccs_manager.lightdir_intensity"}'
                self.insertFrames(light_scene_manager_action, group_name, data_path, energy, 1)
                
                data_path = f'{"ccs_manager.lightdir_color"}'
                self.insertFrames(light_scene_manager_action, group_name, data_path, color, 4)

        for mat in anim.materialControllers:
            bmats = [bmat for bmat in bpy.data.materials if bmat.name.endswith(mat.name)]
            if bmats:
                blender_mat = bmats[0]
                group_name = blender_mat.name

                material_action = bpy.data.actions.new(f"{action.name} ({mat.name})")
                blender_mat.animation_data_create()
                blender_mat.animation_data.action = material_action
                
                offsetX_value = blender_mat["uvOffset"][0]
                offsetY_value = blender_mat["uvOffset"][1]
                scaleX_value = blender_mat["uvOffset"][2]
                scaleY_value = blender_mat["uvOffset"][3]
                
                offsetsX = {f: [v - offsetX_value] for f, v in mat.offsetX.items()}
                offsetsY = {f: [v - offsetY_value] for f, v in mat.offsetY.items()}
                scalesX = {f: [1 + scaleX_value - v] for f, v in mat.scaleX.items()}
                scalesY = {f: [1 + scaleY_value - v] for f, v in mat.scaleY.items()}
                
                data_path = f'{"ccs_material.uvOffset"}'
                self.insertMaterialFrames(material_action, group_name, data_path, offsetsX, 0)
                data_path = f'{"ccs_material.uvOffset"}'
                self.insertMaterialFrames(material_action, group_name, data_path, offsetsY, 1)
                data_path = f'{"ccs_material.uvOffset"}'
                self.insertMaterialFrames(material_action, group_name, data_path, scalesX, 2)
                data_path = f'{"ccs_material.uvOffset"}'
                self.insertMaterialFrames(material_action, group_name, data_path, scalesY, 3)

        
        for mat in anim.materials.keys():
            bmats = [bmat for bmat in bpy.data.materials if bmat.name.endswith(mat)]
            if bmats:
                blender_mat = bmats[0]
                group_name = blender_mat.name

                material_action = bpy.data.actions.new(f"{action.name} ({mat})")
                blender_mat.animation_data_create()
                blender_mat.animation_data.action = material_action
                
                
                offsetX_value = blender_mat["uvOffset"][0]
                offsetY_value = blender_mat["uvOffset"][1]
                scaleX_value = blender_mat["uvOffset"][2]
                scaleY_value = blender_mat["uvOffset"][3]

                
                data_path = f'{"ccs_material.uvOffset"}'
                offsetsX = {}
                offsetsY = {}
                scalesX = {}
                scalesY = {}
                for frame, values in anim.materials[mat].items():
                    offsetsX[frame] = [values[0] - offsetX_value]
                    offsetsY[frame] = [1 - (values[1] - offsetY_value)]
                    
                    if values[2] == 1:
                        scalesX[frame] = [1]
                    else:
                        scalesX[frame] = [1 + values[2] - scaleX_value]
                        
                    if values[3] == 1:
                        scalesY[frame] = [1]
                    else:
                        scalesY[frame] = [1 + values[3] - scaleY_value]
                        
                self.insertMaterialFrames(material_action, group_name, data_path, offsetsX, 0)
                self.insertMaterialFrames(material_action, group_name, data_path, offsetsY, 1)
                self.insertMaterialFrames(material_action, group_name, data_path, scalesX, 2)
                self.insertMaterialFrames(material_action, group_name, data_path, scalesY, 3)

                '''for frame, values in anim.materials[mat].items():
                    UV_node.inputs[1].default_value = values[0] - offsetX_value
                    UV_node.inputs[1].keyframe_insert('default_value', frame= frame)

                    UV_node.inputs[2].default_value = 1 - (values[1] - offsetY_value)
                    UV_node.inputs[2].keyframe_insert('default_value', frame= frame)

                if values[2] == 1:
                    UV_node.inputs[3].default_value = 1
                    UV_node.inputs[3].keyframe_insert('default_value', frame= frame)
                else:
                    UV_node.inputs[3].default_value = 1 + values[2] - scaleX_value
                    UV_node.inputs[3].keyframe_insert('default_value', frame= frame)
                if values[3] == 1:
                    UV_node.inputs[4].default_value = 1
                    UV_node.inputs[4].keyframe_insert('default_value', frame= frame)
                else:
                    UV_node.inputs[4].default_value = 1 + values[3] - scaleY_value
                    UV_node.inputs[4].keyframe_insert('default_value', frame= frame)'''

                
                '''material_action = blender_mat.node_tree.animation_data.action

                if material_action:
                    material_action.name = f"{action.name} ({mat})"
                    for fcurve in material_action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'LINEAR'''


    def convertEulerRotation(self, keyframes, brot):
        #Rotations Euler
        rotations = {}
        startQuat = brot
        for frame, rot in keyframes:
            
            endQuat = brot @ Euler((radians(x) for x in rot), "ZYX").to_quaternion()

            if startQuat.dot(endQuat) < 0:
                endQuat.negate()
            
            rotations[frame] = endQuat
            startQuat = endQuat
        
        return rotations
    

    def convertQuaternionRotation(self, keyframes, brot):
        #Rotations Quaternion
        rotations = {keyframe : brot.rotation_difference(Quaternion((rotation[3], *rotation[:3])).inverted()) for keyframe, rotation in keyframes}

        return rotations


    def convertVectorLocation(self, keyframes, bloc, brot):
        #locations = {frame : ((Vector(loc) * 0.01) - bloc) for frame, loc in keyframes}
        locations = {}
        for frame, loc in keyframes:
            loc = Vector(loc) * 0.01
            bind_loc = Vector(bloc)
            loc.rotate(brot)
            bind_loc.rotate(brot)

            locations[frame] = loc - bind_loc
        
        return locations

    def convertVectorScale(self, keyframes, bscale):
        scales = {keyframe: Vector([s / b for s, b in zip(value, bscale)]) for keyframe,value in keyframes}
        
        return scales


    def insertFrames(self, action, group_name, data_path, values, values_count):
        if len(values):
            for i in range(values_count):
                fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                fc.keyframe_points.add(len(values.keys()))
                fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), values.keys(), values.values())) for x in co])

                fc.update()
    
    
    def insertMaterialFrames(self, action, group_name, data_path, values, index):
        if len(values):
            fc = action.fcurves.new(data_path=data_path, index=index, action_group=group_name)
            fc.keyframe_points.add(len(values.keys()))
            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[0]), values.keys(), values.values())) for x in co])

            fc.update()
        
    
def menu_func_import(self, context):
    self.layout.operator(CCS_IMPORTER_OT_IMPORT.bl_idname,
                        text='CyberConnect Streaming File (.ccs)')
