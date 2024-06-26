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
import os

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
        blenderChunk.parent = chunk.parent.name
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
    
    def execute(self, context):

        start_time = time()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)))

            importer.read(context)

        elapsed_s = "{:.2f}s".format(time() - start_time)
        self.report({'INFO'}, "CCS files imported in " + elapsed_s)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "swap_names")
        row = layout.row()
        if self.swap_names:
            row.prop(self, "source_name")
            row = layout.row()
            row.prop(self, "target_name")


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
    
    def execute(self, context):

        start_time = time()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = importCCS(self, self.filepath, self.as_keywords(ignore=("filter_glob",)))

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


class importCCS:
    def __init__(self, operator: Operator, filepath, import_settings: dict):
        self.operator = operator
        self.filepath = filepath
        for key, value in import_settings.items():
            setattr(self, key, value)
        

    def read(self, context):
        
        self.ccsf: ccsFile = readCCS(self.filepath)

        self.collection = bpy.data.collections.new(self.ccsf.name)
        bpy.context.collection.children.link(self.collection)

        for cmp in self.ccsf.chunks.values():
            if cmp != None and cmp.type == 'Clump':
                clump = bpy.data.armatures.get(cmp.name, self.makeClump(cmp))


        for model in self.ccsf.chunks.values():
            if model != None and model.type == 'Model':
                if model.meshCount > 0 and model.modelType & 8:
                    continue
                    for i, mesh in enumerate(model.meshes):                        
                        bm = bmesh.new()

                        verts = [bm.verts.new(v.position) for v in mesh.vertices]
                        bm.verts.ensure_lookup_table()
                        
                        triangles = [bm.faces.new((verts[t[0]], verts[t[1]], verts[t[2]])) for t in mesh.triangles]
                        bm.faces.ensure_lookup_table()                        

                        blender_mesh = bpy.data.meshes.new(f'{model.name}')
                        bm.to_mesh(blender_mesh)

                        obj = bpy.data.objects.new(f'{model.name}', blender_mesh)
                        self.collection.objects.link(obj)
                

                elif model.meshCount > 0 and model.modelType & 4 and not model.modelType & 2:
                    #Create the object and its mesh data
                    meshdata = bpy.data.meshes.new(f'{model.name}')
                    obj = bpy.data.objects.new(f'{model.name}', meshdata)
                    
                    #find the armature and add all the bones to a dict
                    armature = bpy.data.objects.get(model.clump.name)
                    bone_indices = {}
                    for i in range(len(armature.pose.bones)):
                        obj.vertex_groups.new(name = armature.pose.bones[i].name)
                        bone_indices[armature.pose.bones[i].name] = i
                    
                    normals = []

                    if len(model.lookupList) > 1:
                        meshRange = model.meshes[0:-1]
                    else:
                        meshRange = model.meshes

                    for i, mesh in enumerate(meshRange):
                        parent = armature.data.bones.get(model.lookupNames[mesh.parentIndex])
                        
                        #add the mesh material
                        mat = self.makeMaterial(model, mesh)
                        mat_slot = obj.material_slots.get(mat.name)
                        if mat_slot:
                            matIndex = mat_slot.slot_index
                        else:
                            obj.data.materials.append(mat)
                            mat_slot = obj.material_slots.get(mat.name)
                            matIndex = mat_slot.slot_index

                        meshdata = self.makeMeshSingleWeight(meshdata, mesh, parent, bone_indices, matIndex, normals)                        
                    
                    #deformable mesh
                    if len(model.lookupList) > 1:
                        mesh = model.meshes[-1]
                        #add the mesh material
                        mat = self.makeMaterial(model, mesh)
                        mat_slot = obj.material_slots.get(mat.name)
                        if mat_slot:
                            matIndex = mat_slot.slot_index
                        else:
                            obj.data.materials.append(mat)
                            mat_slot = obj.material_slots.get(mat.name)
                            matIndex = mat_slot.slot_index
                    
                        meshdata = self.makeMeshMultiWeight(meshdata, model, mesh, bone_indices, matIndex, normals)

                    #meshdata.normals_split_custom_set_from_vertices(normals)
      
                    self.collection.objects.link(obj)
                    obj.parent = armature

                    #add armature modifier
                    armature_modifier = obj.modifiers.new(name = f'{armature.name}', type = 'ARMATURE')
                    armature_modifier.object = armature

                elif model.meshCount > 0 and model.modelType & 2:
                        for mesh in model.meshes:
                            meshdata = bpy.data.meshes.new(f'{model.name}')
                            obj = bpy.data.objects.new(f'{model.name}', meshdata)

                            bone_indices = {}
                            parent_clump = bpy.data.objects.get(model.clump.name)
                            for i in range(len(parent_clump.pose.bones)):
                                obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                                bone_indices[parent_clump.pose.bones[i].name] = i

                            meshdata = self.makeMeshTriList(meshdata, model, mesh, bone_indices)

                            #add the mesh material
                            mat = self.makeMaterial(model, mesh)
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
                        meshdata = bpy.data.meshes.new(f'{model.name}')
                        obj = bpy.data.objects.new(f'{model.name}', meshdata)
                        
                        #find the armature and add all the bones to a dict
                        armature = bpy.data.objects.get(model.clump.name)
                        parent = armature.data.bones.get(model.parentBone.name)
                        bone_indices = {}
                        for i in range(len(armature.pose.bones)):
                            obj.vertex_groups.new(name = armature.pose.bones[i].name)
                            bone_indices[armature.pose.bones[i].name] = i
                        
                        normals = []

                        for m, mesh in enumerate(model.meshes):
                            #add the mesh material
                            mat = self.makeMaterial(model, mesh)
                            mat_slot = obj.material_slots.get(mat.name)
                            if mat_slot:
                                matIndex = mat_slot.slot_index
                            else:
                                obj.data.materials.append(mat)
                                mat_slot = obj.material_slots.get(mat.name)
                                matIndex = mat_slot.slot_index
                            
                            meshdata = self.makeMeshSingleWeight(meshdata, mesh, parent, bone_indices, matIndex, normals)

                        obj.modifiers.new(name = 'Armature', type = 'ARMATURE')
                        obj.modifiers['Armature'].object = armature

                        obj.parent = armature

                        self.collection.objects.link(obj)
        
        for camera in self.ccsf.chunks.values():
            if camera.type == "Camera":
                bCamera = bpy.data.cameras.get(camera.name)
                if not bCamera:
                    bCamera = bpy.data.cameras.new(camera.name)
                    cameraObject = bpy.data.objects.new(camera.name, bCamera)
                    self.collection.objects.link(cameraObject)

        #anims
        for anim in self.ccsf.chunks.values():
            if anim == None:
                continue
            if anim.name.startswith("ANM_"): #"ANM_1garslc12, ANM_ctu1atc0"
                action = self.makeAction(anim)
        
        streamChunk: ccsStream = self.ccsf.stream
        if streamChunk.frameCount > 1:
            self.makeAction(streamChunk)

    def makeMaterial(self, model, mesh):
        mat = bpy.data.materials.get(f'{model.name}_{mesh.material.name}')
        if not mat:
            mat = bpy.data.materials.new(f'{model.name}_{mesh.material.name}')
            mat.use_nodes = True
            #add image texture
            tex = mesh.material.texture
            if tex.type == "Texture":
                img = None
                image = tex.convertTexture()

                if image:
                    if hasattr(tex, "name"):
                        img = bpy.data.images.get(tex.name)    
                    if not img: 
                        img = bpy.data.images.new(tex.name, tex.width, tex.height, alpha=True)
                        img.pack(data=bytes(image), data_len=len(image))
                        img.source = 'FILE'
                
                #add texture node
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = img
                tex_node.location = (-200, 200)
                #link texture node to principled node
                links.new(tex_node.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])
                links.new(tex_node.outputs['Alpha'], nodes['Principled BSDF'].inputs['Alpha'])

                mat.blend_method = 'CLIP'
                mat.shadow_method = 'NONE'
                mat.show_transparent_back = False
        return mat


    def makeMeshSingleWeight(self, meshdata, mesh, parent, boneIndices, matIndex, normals):
            bm = bmesh.new()

            uv_layer = bm.loops.layers.uv.new(f"UV")
            color_layer = bm.loops.layers.color.new(f"Color")
            vgroup_layer = bm.verts.layers.deform.new("Weights")

            boneID = boneIndices[parent.name]

            #Triangles
            direction = 1
            for i, v in enumerate(mesh.vertices):
                bmVertex = bm.verts.new(v.position)

                bmVertex[vgroup_layer][boneID] = 1
                
                #normals must be normalized
                normals_vector = np.array(v.normal)
                normals_vector = normals_vector / np.linalg.norm(normals_vector)
                normals.append(normals_vector)


                bm.verts.ensure_lookup_table()
                bm.verts.index_update()

                flag = v.triangleFlag
                
                if flag == 1:
                    direction = 1
                elif flag == 2:
                    direction = -1
                
                if flag == 0:
                    if direction == 1:
                        face = bm.faces.new((bm.verts[i-2], bm.verts[i-1], bm.verts[i]))
                    elif direction == -1:
                        face = bm.faces.new((bm.verts[i], bm.verts[i-1], bm.verts[i-2]))
                    
                    face.material_index = matIndex
                    face.smooth = True
                    for loop in face.loops:
                        loop[uv_layer].uv = mesh.vertices[loop.vert.index].UV
                        loop[color_layer] = mesh.vertices[loop.vert.index].color
                    
                    #we need to flip the direction for the next face
                    direction *= -1
            
            bm.faces.ensure_lookup_table()

            bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.000001)

            bm.transform(Matrix(parent["matrix"]))
            bm.from_mesh(meshdata)
            bm.to_mesh(meshdata)

            return meshdata
        

    def makeMeshTriList(self, meshdata, model, mesh, bone_indices):
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new(f"UV")
        vgroup_layer = bm.verts.layers.deform.new("Weights")

        normals = []

        for i, ccsVertex in enumerate(mesh.vertices):
            #calculate vertex final position
            boneID1 = model.lookupList[ccsVertex.boneIDs[0]]
            boneID2 = model.lookupList[ccsVertex.boneIDs[1]]

            vertex_matrix1 = model.clump.bones[boneID1].matrix
            vertex_matrix2 = model.clump.bones[boneID2].matrix
            vp1 = (vertex_matrix1 @ Vector(ccsVertex.positions[0]) * ccsVertex.weights[0]) 
            vn1 = Vector(ccsVertex.normals[0])

            if ccsVertex.boneIDs[1] != "":
                vp2 = (vertex_matrix2 @ Vector(ccsVertex.positions[1]) * ccsVertex.weights[1])
                vn2 = Vector(ccsVertex.normals[1])
            else:
                vp2 = Vector((0,0,0))
                vn2 = Vector((0,0,0))
            

            bmVertex = bm.verts.new(vp1 + vp2)

            normals_vector = np.array(vn1 + vn2)
            normals_vector = normals_vector / np.linalg.norm(normals_vector)
            normals.append(normals_vector)   

            bm.verts.ensure_lookup_table()
            bm.verts.index_update()

            #add vertex weights
            boneID1 = bone_indices[model.lookupNames[ccsVertex.boneIDs[0]]]
            boneID2 = bone_indices[model.lookupNames[ccsVertex.boneIDs[1]]]

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
                except:
                    print(f"error at {i}")

            bm.faces.ensure_lookup_table()

        bm.to_mesh(meshdata)

        meshdata.normals_split_custom_set_from_vertices(normals)
        return meshdata
    
    def makeMeshMultiWeight(self, meshdata, model, mesh, bone_indices, matIndex, normals):        
        bm = bmesh.new()
        vgroup_layer = bm.verts.layers.deform.new("Weights")
        uv_layer = bm.loops.layers.uv.new(f"UV")        

        for i, ccsVertex in enumerate(mesh.vertices):
            #calculate vertex final position
            boneID1 = model.lookupList[ccsVertex.boneIDs[0]]
            boneID2 = model.lookupList[ccsVertex.boneIDs[1]]

            vertex_matrix1 = model.clump.bones[boneID1].matrix
            vertex_matrix2 = model.clump.bones[boneID2].matrix
            vp1 = (vertex_matrix1 @ Vector(ccsVertex.positions[0]) * ccsVertex.weights[0])
            vn1 = Vector(ccsVertex.normals[0])

            if ccsVertex.boneIDs[1] != "":
                vp2 = (vertex_matrix2 @ Vector(ccsVertex.positions[1]) * ccsVertex.weights[1])
                vn2 = Vector(ccsVertex.normals[1])
            else:
                vp2 = Vector((0,0,0))
                vn2 = Vector((0,0,0))
            

            bmVertex = bm.verts.new(vp1 + vp2)

            #normals must be normalized
            normals_vector = np.array(vn1 + vn2)
            normals_vector = normals_vector / np.linalg.norm(normals_vector)
            normals.append(normals_vector)
            
            bm.verts.ensure_lookup_table()
            bm.verts.index_update()
            

            #add vertex groups with 0 weights
            boneID1 = bone_indices[model.lookupNames[ccsVertex.boneIDs[0]]]
            boneID2 = bone_indices[model.lookupNames[ccsVertex.boneIDs[1]]]
            bmVertex[vgroup_layer][boneID1] = 0
            bmVertex[vgroup_layer][boneID2] = 0

            #this is done in case a vertex uses the same bone twice
            bmVertex[vgroup_layer][boneID1] += ccsVertex.weights[0]
            bmVertex[vgroup_layer][boneID2] += ccsVertex.weights[1]

            flag = ccsVertex.triangleFlag
            
            if flag == 1:
                direction = 1
            elif flag == 2:
                direction = -1
            
            if flag == 0:
                if direction == 1:
                    face = bm.faces.new((bm.verts[i-2], bm.verts[i-1], bm.verts[i]))
                elif direction == -1:
                    face = bm.faces.new((bm.verts[i], bm.verts[i-1], bm.verts[i-2]))
                face.material_index = matIndex
                face.smooth = True
                for loop in face.loops:
                    loop[uv_layer].uv = mesh.vertices[loop.vert.index].UV
                    #loop[color_layer] = mesh.vertices[loop.vert.index].color
                #we need to flip the direction for the next face
                direction *= -1
        
        #clean up the mesh
        bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.000001)

        bm.from_mesh(meshdata)
        bm.to_mesh(meshdata)

        return meshdata


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
                b.matrix = b.parent.matrix @ Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            else:
                b.matrix = Matrix.LocRotScale(Vector(b.pos) * 0.01, rotation, b.scale)
            
            bone.matrix = b.matrix
            
            bone["original_coords"] = [b.pos, b.rot, b.scale]
            bone["rotation_quat"] = rotation
            bone["matrix"] = b.matrix

            bone.parent = clump.edit_bones[b.parent.name] if b.parent else None
        
        bpy.ops.object.editmode_toggle()
    

    def makeAction(self, anim):
        action = bpy.data.actions.new(anim.name)
        #set fps to 30
        bpy.context.scene.render.fps = 30

        #adjust the timeline
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = anim.frameCount

        source = self.source_name
        target = self.target_name

        for objCtrl in anim.objectControllers:
            objCtrl: objectController
            ccsAnmObj = objCtrl.object
            target_bone = ccsAnmObj.name

            if ccsAnmObj.name.find(source) != -1:
                target_bone = ccsAnmObj.name.replace(source, target)
            
            if ccsAnmObj.clump:
                clump = ccsAnmObj.clump.name
            else:
                #try to get it from blender
                clump = bpy.context.scene.ccs_importer.objects.get(target_bone)
                if clump:
                    clump = clump.clump
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
            for frame, loc in objCtrl.positions.items():
                loc = Vector(loc) * 0.01
                bind_loc = Vector(bloc)
                loc.rotate(brot)
                bind_loc.rotate(brot)

                locations[frame] = loc - bind_loc
            
            data_path = f'{bone_path}.{"location"}'
            if len(locations):
                for i in range(3):
                    fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(objCtrl.positions.keys()))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), objCtrl.positions.keys(), locations.values())) for x in co])

                    fc.update()
            
            #Rotations Euler
            rotations = {}
            startQuat = brot
            for frame, rot in objCtrl.rotationsEuler.items():
                
                endQuat = brot @ Euler((radians(x) for x in rot), "ZYX").to_quaternion()

                if startQuat.dot(endQuat) < 0:
                    endQuat.negate()
                
                rotations[frame] = endQuat
                startQuat = endQuat

            data_path = f'{bone_path}.{"rotation_quaternion"}'
            if len(rotations):
                for i in range(4):
                    fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(rotations.keys()))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), rotations.keys(), rotations.values())) for x in co])

                    fc.update()
            
            #Rotations Quaternion
            rotations_quat = {}
            for frame, rotation in objCtrl.rotationsQuat.items():
                bind_rotaion = brot.conjugated()
                rotation = Quaternion((rotation[3], *rotation[:3]))
                #rotate it with the new rotation
                bind_rotaion.rotate(rotation)
                #invert the result
                rotations_quat[frame] = Quaternion(bind_rotaion).conjugated()
            
            data_path = f'{bone_path}.{"rotation_quaternion"}'
            if len(rotations_quat):
                for i in range(4):
                    fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(rotations_quat.keys()))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), rotations_quat.keys(), rotations_quat.values())) for x in co])
                    fc.update()

        
        fcurves = {}
        for obj in anim.objects.keys():

            target_bone = obj

            if obj.find(source) != -1:
                target_bone = obj.replace(source, target)

            #try to get it from blender
            clump = bpy.context.scene.ccs_importer.objects.get(target_bone)
            if clump:
                clump = clump.clump
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

            '''group_name = action.groups.new(name = posebone.name).name

            bone_path = f'pose.bones["{posebone.name}"]'

            locations = {}
            loc = objF.position

            #positions
            loc = Vector(loc) * 0.01
            bind_loc = Vector(bloc)
            loc.rotate(brot)
            bind_loc.rotate(brot)

            locations[objF.frame] = loc - bind_loc
            
            
            data_path = f'{bone_path}.{"location"}'
            if len(locations):

                for frame, value in locations.items():
                    for i in range(3):
                        fc = fcurves.get(f"{data_path}_{i}", action.fcurves.new(data_path=data_path, index=i, action_group=posebone.name))

                        fc.keyframe_points.add(1)
                        fc.keyframe_points.insert(frame,value[i])
                        fcurves[f"{data_path}_{i}"] = fc
                        fc.update()
            
            #Rotations Euler
            rotations = {}
            rot = objF.rotation
            startQuat = brot
            endQuat = brot @ Euler((radians(x) for x in rot), "ZYX").to_quaternion()

            if startQuat.dot(endQuat) < 0:
                endQuat.negate()
            
            rotations[objF.frame] = endQuat

            data_path = f'{bone_path}.{"rotation_quaternion"}'
            if len(rotations):
                for frame, value in rotations.items():
                    for i in range(4):
                        fc = fcurves.get(f"{data_path}_{i}", action.fcurves.new(data_path=data_path, index=i, action_group=posebone.name))
                        fc.keyframe_points.add(1)
                        fc.keyframe_points.insert(frame,value[i])
                        fcurves[f"{data_path}_{i}"] = fc
                        fc.update()'''

            group_name = action.groups.new(name = posebone.name).name

            bone_path = f'pose.bones["{group_name}"]'

            locations = {}
            rotations = {}
            startQuat = brot
            for frame, locrotscale in anim.objects[obj].items():
                loc, rot, scale = locrotscale

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
            
            data_path = f'{bone_path}.{"location"}'
            if len(locations):
                for i in range(3):
                    fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(locations.keys()))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), locations.keys(), locations.values())) for x in co])

                    fc.update()

            data_path = f'{bone_path}.{"rotation_quaternion"}'
            if len(rotations):
                for i in range(4):
                    fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(rotations.keys()))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), rotations.keys(), rotations.values())) for x in co])

                    fc.update()
        
        locations = {}
        rotations = {}
        fovs = {}
        for cam in anim.cameras.keys():
            cameraObject = self.collection.objects.get(cam)

            group_name = action.groups.new(name = cam).name

            if cameraObject:
                #create a separate action for each camera
                action = bpy.data.actions.new(f"{anim.name} ({cam})")
                #apply the animation on the camera
                cameraObject.animation_data_create()
                cameraObject.animation_data.action = action
                for frame, values in anim.cameras[cam].items():
                    loc, rot, fov = values
                    locations[frame] = Vector(loc) * 0.01
                    rotations[frame] = [radians(r) for r in rot] #Euler([radians(r) for r in rot], "ZYX")
                    fovs[frame] = cameraObject.data.sensor_width / (2 * math.tan(radians(fov) / 2))

                data_path = f'{"location"}'
                if len(locations):
                    for i in range(3):
                        fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                        fc.keyframe_points.add(len(locations.keys()))
                        fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), locations.keys(), locations.values())) for x in co])

                        fc.update()
                
                data_path = f'{"rotation_euler"}'
                if len(rotations):
                    for i in range(3):
                        fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                        fc.keyframe_points.add(len(rotations.keys()))
                        fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), rotations.keys(), rotations.values())) for x in co])

                        fc.update()
                

                data_path = f'{"data.lens"}'
                if len(rotations):
                        fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                        fc.keyframe_points.add(len(fovs.keys()))
                        fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v), fovs.keys(), fovs.values())) for x in co])

                        fc.update()

    
    def convert_anm_values_tranformed(self, data_path, values, loc: Vector, rot: Quaternion, parent: bool):
        if data_path == "location":
            updated_values = list()
            for value_loc in values:
                vec_loc = Vector([value_loc[0],value_loc[1],value_loc[2]])
                vec_loc.rotate(rot)
                updated_values.append(vec_loc)
            updated_loc = loc
            updated_loc.rotate(rot)

            return [((x*0.01) - updated_loc)[:] for x in updated_values]

        if data_path == "rotation_euler":
            return [(rot @ ((Euler((radians(y) for y in x), "ZYX").to_quaternion()).to_euler()).to_quaternion())[:] for x in values]

        if data_path == "rotation_quaternion":
            quat_list = list()
            for rotation in values:
                q = rot.conjugated().copy()
                q.rotate(rot)
                quat = q
                q = rot.conjugated().copy()

                if not parent:
                    q.rotate(Quaternion((rotation[3], *rotation[:3])).conjugated())
                else:
                    q.rotate(Quaternion((rotation[3], *rotation[:3])))
                quat.rotate(q.conjugated())

                quat_list.append(quat)

            return quat_list

        if data_path == "scale":
            return [Vector(([abs(y) for y in x]))[:] for x in values]
        return values

    def convert_anm_values_tranformed_root(self, data_path, values, loc: Vector, rot: Quaternion):
        if data_path == "location":
            return [loc + Vector((y * 0.01 for y in x)) for x in values]
        if data_path == "rotation_euler":
            return [(rot @ ((Euler((radians(y) for y in x), "ZYX").to_quaternion()).to_euler()).to_quaternion())[:] for x in values]
        if data_path == "rotation_quaternion":
            return [Quaternion((x[3], *x[:3])) for x in values]
        if data_path == "scale":
            return [Vector((abs(y) for y in x)) for x in values]
        return values


def menu_func_import(self, context):
    self.layout.operator(CCS_IMPORTER_OT_IMPORT.bl_idname,
                        text='CyberConnect Streaming File (.ccs)')
