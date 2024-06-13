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
import os

class CCS_PropertyGroup(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File Path",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )

class CCS_IMPORTER_OT_IMPORT(bpy.types.Operator, ImportHelper):
    bl_label = "Import CCS"
    bl_idname = "import_scene.ccs"


    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    filter_glob: StringProperty(default="*.ccs", options={"HIDDEN"})
    filename_ext = ".ccs"
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):

        start_time = time()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = importCCS(self, self.filepath)

            importer.read(context)

        elapsed_s = "{:.2f}s".format(time() - start_time)
        self.report({'INFO'}, "CCS files imported in " + elapsed_s)

        return {'FINISHED'}        


class DropCCS(Operator):
    """Allows CCS files to be dropped into the viewport to import them"""
    bl_idname = "import_scene.drop_ccs"
    bl_label = "Import CCS"

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    filter_glob: StringProperty(default="*.ccs", options={"HIDDEN"})
    index: IntProperty(name="Index")
    
    def execute(self, context):

        start_time = time()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = importCCS(self, self.filepath)

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
    def __init__(self, operator: Operator, filepath, **kwargs):
        self.operator = operator
        self.filepath = filepath
        super().__init__(**kwargs)

    def read(self, context):
        
        ccsf:ccsFile = readCCS(self.filepath)

        collection = bpy.data.collections.new(ccsf.name)
        bpy.context.collection.children.link(collection)

        for cmp in ccsf.chunks.values():
            if cmp != None and cmp.type == 'Clump':
                armname = cmp.name

                clump = bpy.data.armatures.new(armname)
                clump.display_type = 'STICK'
                clumpobj = bpy.data.objects.new(armname, bpy.data.armatures[armname])
                clumpobj.show_in_front = True
                
                collection.objects.link(clumpobj)

                bpy.context.view_layer.objects.active = clumpobj
                bpy.ops.object.editmode_toggle()

                for b in cmp.bones.values():
                    bone = bpy.data.armatures[armname].edit_bones.new(b.name)

                    bone.use_deform = True
                    bone.tail = Vector((0, 0.01, 0))
                    
                    rotation = (radians(b.rot[0]), radians(b.rot[1]), radians(b.rot[2]))

                    if b.parent:
                        b.matrix = b.parent.matrix @ Matrix.LocRotScale(Vector(b.pos) * 0.01, Euler(rotation, 'ZYX'), b.scale)
                    else:
                        b.matrix = Matrix.LocRotScale(Vector(b.pos) * 0.01, Euler(rotation, 'ZYX'), b.scale)
                    
                    bone.matrix = b.matrix
                    
                    bone["original_coords"] = [b.pos, b.rot, b.scale]
                    bone["matrix"] = b.matrix

                    bone.parent = bpy.data.armatures[armname].edit_bones[b.parent.name] if b.parent else None
                
                bpy.ops.object.editmode_toggle()


        for model in ccsf.chunks.values():
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
                        collection.objects.link(obj)
                

                elif model.meshCount > 0 and model.modelType & 4 and not model.modelType & 2:
                    for i, mesh in enumerate(model.meshes[0:-1]):
                        meshdata = bpy.data.meshes.new(f'{model.name}_{i}')
                        obj = bpy.data.objects.new(f'{model.name}_{i}', meshdata)

                        meshdata = self.makeMeshSingleWeight(meshdata, mesh)
                        #add the mesh material
                        mat = self.makeMaterial(model, mesh)
                        obj.data.materials.append(mat)
                        
                        if model.clump:
                            clump = bpy.data.objects.get(model.clump.name)
                            parent = clump.pose.bones.get(model.lookupNames[mesh.parentIndex])
                            obj.parent = clump
                            if parent:
                                meshdata.transform(parent.matrix)

                                vertex_group = obj.vertex_groups.new(name = parent.name)
                                vertex_group.add(range(mesh.vertexCount), 1, 'ADD')
                                obj.modifiers.new(name = 'Armature', type = 'ARMATURE')
                                obj.modifiers['Armature'].object = clump
                        
                        collection.objects.link(obj)
                    
                    mesh = model.meshes[-1]
                    meshdata = bpy.data.meshes.new(f'{model.name}_deformable')
                    obj = bpy.data.objects.new(f'{model.name}_deformable', meshdata)

                    bone_indices = {}
                    parent_clump = bpy.data.objects.get(model.clump.name)
                    for i in range(len(parent_clump.pose.bones)):
                        obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                        bone_indices[parent_clump.pose.bones[i].name] = i
                    
                    obj.parent = parent_clump

                    meshdata = self.makeMeshMultiWeight(meshdata, model, mesh, bone_indices)

                    #add the mesh material
                    mat = self.makeMaterial(model, mesh)
                    obj.data.materials.append(mat)           
                    
                    collection.objects.link(bpy.data.objects[f'{model.name}_deformable'])

                    #add armature modifier
                    armature_modifier = obj.modifiers.new(name = f'{parent_clump.name}', type = 'ARMATURE')
                    armature_modifier.object = parent_clump

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
                        collection.objects.link(obj)

                else:
                    #single bone
                    if model.meshCount > 0 and model.modelType < 2:
                        for m, mesh in enumerate(model.meshes):
                            meshdata = bpy.data.meshes.new(f'{model.name}')
                            obj = bpy.data.objects.new(f'{model.name}', meshdata)

                            meshdata = self.makeMeshSingleWeight(meshdata, mesh)

                            #add the mesh material
                            mat = self.makeMaterial(model, mesh)
                            obj.data.materials.append(mat)

                            if model.clump:
                                clump = bpy.data.objects.get(model.clump.name)
                                parent = clump.pose.bones.get(model.parentBone.name)
                                if parent:
                                    meshdata.transform(parent.matrix)

                                vertex_group = obj.vertex_groups.new(name = parent.name)
                                vertex_group.add(range(mesh.vertexCount), 1, 'ADD')
                                obj.modifiers.new(name = 'Armature', type = 'ARMATURE')
                                obj.modifiers['Armature'].object = clump

                                obj.parent = clump

                        collection.objects.link(obj)
        

        #anims
        for anim in ccsf.chunks.values():
            if anim == None:
                continue
            if anim.name.startswith("ANM_"):
                action = bpy.data.actions.new(anim.name)
                #set fps to 30
                bpy.context.scene.render.fps = 30

                #adjust the timeline
                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = anim.frameCount


                matrix_dict = {}
                for objCtrl in anim.objectControllers:
                    ccsAnmObj = ccsf.chunks[objCtrl.objectIndex]
                    for armature in bpy.data.armatures:
                        bone = armature.bones.get(ccsAnmObj.name)
                        if bone:
                            break
                        else:
                            continue
                    
                    if not bone:
                        continue
                    
                    armatureObj = bpy.data.objects.get(armature.name)

                    for b in armatureObj.data.bones:
                        matrix_dict[b.name] = b.matrix_local

                    posebone = armatureObj.pose.bones.get(bone.name)

                    if not posebone:
                        continue

                    if bone.parent:
                        #print(bone.parent.name)
                        parent_matrix = matrix_dict.get(bone.parent.name)
                    else:
                        parent_matrix = Matrix.Identity(4)

                    mat = matrix_dict.get(bone.name)
                    mat = (parent_matrix.inverted() @ mat)

                    loc, rot, sca = mat.decompose()
                    rot.invert()
                    sca = Vector(map(lambda a: 1/a, sca))

                    rotate_vector = bone["original_coords"][1]

                    group_name = action.groups.new(name = bone.name).name

                    bone_path = f'pose.bones["{group_name}"]'

                    bone_parent = False
                    if bone.parent:
                        bone_parent = True
                    
                    frames = [x for x in objCtrl.positions.keys()]

                    #positions
                    if (bone.parent != None):
                        values = self.convert_anm_values_tranformed("location", [objCtrl.positions[x] for x in objCtrl.positions.keys()], loc, rot, sca, rotate_vector, bone_parent)
                    else:
                        values = self.convert_anm_values_tranformed_root("location", [objCtrl.positions[x] for x in objCtrl.positions.keys()], loc, rot, sca)

                    data_path = f'{bone_path}.{"location"}'
                    if len(values):
                        for i in range(len(values[0])):
                            fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                            fc.keyframe_points.add(len(frames))
                            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])

                            fc.update()

                    
                    
                    #rotations euler
                    frames = [x for x in objCtrl.rotationsEuler.keys()]

                    if (bone.parent != None):
                        values = self.convert_anm_values_tranformed("rotation_euler", [objCtrl.rotationsEuler[x] for x in objCtrl.rotationsEuler.keys()], loc, rot, sca, rotate_vector, bone_parent)
                    else:
                        values = self.convert_anm_values_tranformed_root("rotation_euler", [objCtrl.rotationsEuler[x] for x in objCtrl.rotationsEuler.keys()], loc, rot, sca)

                    data_path = f'{bone_path}.{"rotation_quaternion"}'

                    if len(values):
                        for i in range(len(values[0])):
                            fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                            fc.keyframe_points.add(len(frames))
                            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])

                            fc.update()
                    

                    #rotations Quaternion
                    frames = [x for x in objCtrl.rotationsQuat.keys()]

                    '''if len(objCtrl.rotationsQuat[0]) < 4:
                        raise ValueError'''

                    if (bone.parent != None):
                        values = self.convert_anm_values_tranformed("rotation_quaternion", [objCtrl.rotationsQuat[x] for x in objCtrl.rotationsQuat.keys()], loc, rot, sca, rotate_vector, bone_parent)
                    else:
                        values = self.convert_anm_values_tranformed_root("rotation_quaternion", [objCtrl.rotationsQuat[x] for x in objCtrl.rotationsQuat.keys()], loc, rot, sca)

                    data_path = f'{bone_path}.{"rotation_quaternion"}'

                    if len(values):
                        for i in range(len(values[0])):
                            fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                            fc.keyframe_points.add(len(frames))
                            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])

                            fc.update()


                    '''
                    for frame in range(anim.frameCount):

                        #get current pose bone translation, rotation and scale
                        if objCtrl.positions.get(frame):
                            translation = Vector(objCtrl.positions[frame]) * 0.01
                        else:
                            translation = posebone.location
                        if objCtrl.rotations.get(frame):
                            rotation = Euler((radians(x) for x in objCtrl.rotations[frame]), 'ZYX')
                        else:
                            rotation = posebone.rotation_quaternion
                        if objCtrl.scales.get(0):
                            scale = objCtrl.scales[0]
                        else:
                            scale = posebone.scale

                        matrix = Matrix.LocRotScale(translation, rotation, scale)

                        posebone.matrix = matrix

                        #posebone.translate(translation)
                        

                        #set the keyframes
                        if objCtrl.positions.get(frame):
                            posebone.keyframe_insert(data_path = 'location', frame = frame, group = group_name)
                        if objCtrl.rotations.get(frame):
                            posebone.keyframe_insert(data_path = 'rotation_quaternion', frame = frame, group = group_name)
                        if objCtrl.scales.get(frame):
                            posebone.keyframe_insert(data_path = 'scale', frame = frame, group = group_name)


'''
                    '''

                    for frame in objCtrl.positions.keys():
                        #frame = frame + 1
                        posebone.location = (Vector(objCtrl.positions[frame]) / 256) * 0.01
                        posebone.keyframe_insert(data_path = 'location', frame = frame, group = group_name)
                    
                    for frame in objCtrl.rotations.keys():
                        rotaion = (radians(x) for x in objCtrl.rotations[frame])
                        posebone.rotation_quaternion = Euler(rotaion, 'XYZ').to_quaternion()
                        posebone.keyframe_insert(data_path = 'rotation_quaternion', frame = frame, group = group_name)
'''
                        #posebone.scale = objCtrl.scales[frame]
                        
                        #posebone.keyframe_insert(data_path = 'rotation_quaternion', frame = frame, group = group_name)
                        #posebone.keyframe_insert(data_path = 'scale', frame = frame, group = group_name)
    

    def makeMaterial(self, model, mesh):
        mat = bpy.data.materials.get(f'{model.name}_{mesh.material.name}')
        if not mat:
            mat = bpy.data.materials.new(f'{model.name}_{mesh.material.name}')
            mat.use_nodes = True
            #add image texture
            tex = mesh.material.texture
            if tex:
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


    def makeMeshSingleWeight(self, meshdata, mesh):
            bm = bmesh.new()

            uv_layer = bm.loops.layers.uv.new(f"UV")
            color_layer = bm.loops.layers.color.new(f"Color")

            normals = []

            #Triangles
            direction = 1
            for i, v in enumerate(mesh.vertices):
                bmVertex = bm.verts.new(v.position)
                
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
                    face.smooth = True
                    for loop in face.loops:
                        loop[uv_layer].uv = mesh.vertices[loop.vert.index].UV
                        loop[color_layer] = mesh.vertices[loop.vert.index].color
                    
                    #we need to flip the direction for the next face
                    direction *= -1
            
            bm.faces.ensure_lookup_table()

            bm.to_mesh(meshdata)

            meshdata.normals_split_custom_set_from_vertices(normals)

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
    
    def makeMeshMultiWeight(self, meshdata, model, mesh, bone_indices):        
        bm = bmesh.new()
        vgroup_layer = bm.verts.layers.deform.new("Weights")
        uv_layer = bm.loops.layers.uv.new(f"UV")
        #color_layer = bm.loops.layers.color.new(f"Color")

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
                face.smooth = True
                for loop in face.loops:
                    loop[uv_layer].uv = mesh.vertices[loop.vert.index].UV
                    #loop[color_layer] = mesh.vertices[loop.vert.index].color
                #we need to flip the direction for the next face
                direction *= -1
        
        #clean up the mesh
        #bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.00001)
        #make sure that all the normals are pointing the right way
        #bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        bm.to_mesh(meshdata)
        #meshdata.normals_split_custom_set_from_vertices(normals)

        return meshdata
    

    def convert_anm_values_tranformed(self, data_path, values, loc: Vector, rot: Quaternion, sca: Vector, rotate_vector: Euler, parent: bool):
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
            return [rot @ Euler((radians(y) for y in x), "ZYX").to_quaternion() for x in values]

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

    def convert_anm_values_tranformed_root(self, data_path, values, loc: Vector, rot: Quaternion, sca: Vector):
        if data_path == "location":
            return [loc + Vector((y * 0.01 for y in x)) for x in values]
        if data_path == "rotation_euler":
            return [Euler((radians(y) for y in x), "ZYX").to_quaternion() for x in values]
        if data_path == "rotation_quaternion":
            return [Quaternion((x[3], *x[:3])) for x in values]
        if data_path == "scale":
            return [Vector((abs(y) for y in x)) for x in values]
        return values


def menu_func_import(self, context):
    self.layout.operator(CCS_IMPORTER_OT_IMPORT.bl_idname,
                         text='CyberConnect Streaming File (.ccs)')
