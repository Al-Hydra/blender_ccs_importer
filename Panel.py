import bpy, bmesh, math, mathutils
from bpy.types import PropertyGroup, Operator, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty, CollectionProperty
from .ccs_lib import ccs_reader
from .ccs_lib.ccsf import ccs
from mathutils import Vector, Matrix, Euler, Quaternion
from time import perf_counter
import json

class CCS_IMPORTER_PT_PANEL(bpy.types.Panel):
    bl_label = "CCS Importer"
    bl_idname = "CCS_IMPORTER_PT_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CCS Importer"
    bl_context = "objectmode"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="CCS Importer")
        layout.prop(scene.ccs_importer, "filepath")
        layout.operator("import_scene.ccs")

class CCS_PropertyGroup(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File Path",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )

class CCS_IMPORTER_OT_IMPORT(bpy.types.Operator):
    bl_label = "Import CCS"
    bl_idname = "import_scene.ccs"
    
    def execute(self, context):

        scene = context.scene
        filepath = scene.ccs_importer.filepath

        start = perf_counter()
        ccsf = ccs_reader.read_ccs(filepath)
        
        

        def make_material(model, mesh):
            mat = bpy.data.materials.get(f'{model.name}_{mesh.Material.name}')
            if not mat:
                mat = bpy.data.materials.new(mesh.Material.name)
                mat.use_nodes = True
                #add image texture
                tex = mesh.Material.Texture
                if tex:
                    img = None

                    if hasattr(tex, "name"):
                        img = bpy.data.images.get(tex.name)    
                    if not img:
                        img = bpy.data.images.new(tex.name, tex.Width, tex.Height, alpha=True)
                        if hasattr(tex, "Image"):
                            img.pack(data=bytes(tex.Image), data_len=len(tex.Image))
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
                    
        collection = bpy.data.collections.new(ccsf.filename)
        bpy.context.collection.children.link(collection)
        for cmp in ccsf.ChunksDict.get:
            if cmp.type == 'Clump':
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

                    if b.parent:
                        b.matrix = b.parent.matrix @ Matrix.LocRotScale(b.position, Euler(b.rotation, 'ZYX'), b.scale)
                    else:
                        b.matrix = Matrix.LocRotScale(b.position, Euler(b.rotation, 'ZYX'), b.scale)
                    
                    bone.matrix = b.matrix
                    bone.parent = bpy.data.armatures[armname].edit_bones[b.parent.name] if b.parent else None
                
                bpy.ops.object.editmode_toggle()
                    

        for model in ccsf.ChunksDict.values():
            if model.type == 'Model':

                if model.MeshCount > 0 and model.ModelType in ("Rigid1", "Rigid2"):
                    empty =bpy.data.objects.new(f'{model.name}', None)
                    empty.empty_display_type = 'PLAIN_AXES'
                    empty.empty_display_size = 0.001

                    parent_clump = bpy.data.objects.get(model.clump.name)
                    parent_bone = model.clump.bones.get(model.ParentBone.name)
                    empty.parent = parent_clump
                    '''empty.parent_type = 'BONE'
                    empty.parent_bone = parent_bone.name'''
                    

                    for m, mesh in enumerate(model.meshes):

                        meshdata = bpy.data.meshes.new(f'{model.name}_{m}')
                        obj = bpy.data.objects.new(f'{model.name}_{m}', bpy.data.meshes[f'{model.name}_{m}'])
                        #parent_bone = parent_clump.pose.bones[mesh.Parent]

                        bone_indices = {}
                        for i in range(len(parent_clump.pose.bones)):
                            obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                            bone_indices[parent_clump.pose.bones[i].name] = i

                        bm = bmesh.new()
                        custom_normals = list()

                        for i in range(mesh.VertexCount):
                            
                            vert = bm.verts.new(Vector(mesh.Vertices[i].Position))
                        
                        bm.verts.ensure_lookup_table()
                        bm.verts.index_update()

                        uv_layer = bm.loops.layers.uv.new(f"UV")

                        for tris in mesh.Triangles:
                            face = bm.faces.new((bm.verts[tris[0]], bm.verts[tris[1]], bm.verts[tris[2]]))     
                            face.smooth = True
                            for loop in face.loops:
                                
                                loop[uv_layer].uv = mesh.Vertices[loop.vert.index].UV
                        
                        bm.faces.ensure_lookup_table()

                                
                        #bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.00001)
                        #bm.normal_update()                        
                        
                        meshdata.auto_smooth_angle = 180
                        meshdata.use_auto_smooth = True
                        
                        
                        bm.to_mesh(meshdata)
                        meshdata.create_normals_split()
                        meshdata.transform(parent_bone.matrix)

                        obj.vertex_groups[parent_bone.name].add(range(len(mesh.Vertices)), 1, 'ADD')
                        obj.modifiers.new(name = 'Armature', type = 'ARMATURE')
                        obj.modifiers['Armature'].object = parent_clump

                        collection.objects.link(bpy.data.objects[f'{model.name}_{m}'])
                        
                        obj.parent = empty
                        #materal
                        mat = make_material(model, mesh)
                        
                        obj.data.materials.append(mat)
                    collection.objects.link(empty)

                elif model.MeshCount > 0 and model.ModelType == 'ShadowMesh':
                    pass
                    '''for i, mesh in enumerate(model.meshes):
                        empty =bpy.data.objects.new(f'{model.name}', None)
                        empty.empty_display_type = 'PLAIN_AXES'
                        empty.empty_display_size = 0.001
                        
                        bm = bmesh.new()
                        for i in range(len(mesh.Vertices)):
                            vert = bm.verts.new(mesh.Vertices[i].Position)   
                        
                        bm.verts.ensure_lookup_table()
                        
                        for t in mesh.Triangles:
                            bm.faces.new((bm.verts[t[0]], bm.verts[t[1]], bm.verts[t[2]]))
                        bm.faces.ensure_lookup_table()

                        bpy.data.meshes.new(f'{model.name}_{i}')

                        bm.to_mesh(bpy.data.meshes[f'{model.name}_{i}'])

                        obj = bpy.data.objects.new(f'{model.name}_{i}', bpy.data.meshes[f'{model.name}_{i}'])
                        #obj.scale = (5.1,5.1,5.1)

                        collection.objects.link(bpy.data.objects[f'{model.name}_{i}'])
                        
                        obj.parent = empty
                        
                        collection.objects.link(empty)'''
                #third
                elif model.MeshCount > 0 and model.ModelType == 'Deformable':
                    
                    #print(model.name)
                    empty =bpy.data.objects.new(f'{model.name}', None)
                    empty.empty_display_type = 'PLAIN_AXES'
                    empty.empty_display_size = 0.001

                    #get the parent clump
                    parent_clump = collection.objects[model.clump.name]

                    #parent the model to the clump
                    empty.parent = parent_clump
                    '''empty.parent_type = 'BONE'
                    empty.parent_bone = model.ParentBone.name'''
                    
                    meshes = model.meshes[0:-1]
                    #Model has multiple meshes
                    for m, mesh in enumerate(meshes):

                        #get the parent bone
                        #parent_bone = parent_clump.data.bones[mesh.Parent]
                        meshdata = bpy.data.meshes.new(f'{model.name}_{m}')
                        obj = bpy.data.objects.new(f'{model.name}_{m}', bpy.data.meshes[f'{model.name}_{m}'])
                        parent_bone = parent_clump.pose.bones[mesh.Parent]

                        bone_indices = {}
                        for i in range(len(parent_clump.pose.bones)):
                            obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                            bone_indices[parent_clump.pose.bones[i].name] = i

                        
                        bm = bmesh.new()
                        #create vertex weights layer
                        vgroup_layer = bm.verts.layers.deform.new("Weights")

                        for i in range(mesh.VertexCount):
                            vert = bm.verts.new(parent_bone.matrix @ Vector(mesh.Vertices[i].Position))
                            bm.verts.ensure_lookup_table()
                            bm.verts[i][vgroup_layer][bone_indices[parent_bone.name]] = 1

                        bm.verts.ensure_lookup_table()
                        bm.verts.index_update()

                        uv_layer = bm.loops.layers.uv.new(f"UV")


                        for tris in mesh.Triangles:
                            face = bm.faces.new((bm.verts[tris[0]], bm.verts[tris[1]], bm.verts[tris[2]]))
                            face.smooth = True
                            for loop in face.loops:
                                original_uv = mesh.Vertices[loop.vert.index].UV
                                loop[uv_layer].uv = original_uv
                        bm.faces.ensure_lookup_table()
                        
                        
                        '''for face in bm.faces:
                            for loop in face.loops:
                                original_uv = mesh.Vertices[loop.vert.index].UV
                                loop[uv_layer].uv = original_uv'''
                                
                        
                        bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.00001)
                        bm.normal_update()

                        
                        meshdata.auto_smooth_angle = 180
                        meshdata.use_auto_smooth = True

                        bm.to_mesh(meshdata)

                        #obj = bpy.data.objects.new(f'{model.name}_{m}', bpy.data.meshes[f'{model.name}_{m}'])

                        #add weight groups
                        '''obj.vertex_groups.new(name = parent_bone.name)
                        obj.vertex_groups[parent_bone.name].add(range(len(mesh.Vertices)), 1, 'ADD')'''

                        #add armature modifier
                        armature_modifier = obj.modifiers.new(name = f'{parent_clump.name}', type = 'ARMATURE')
                        armature_modifier.object = parent_clump
                        
                        collection.objects.link(bpy.data.objects[f'{model.name}_{m}'])

                        #parent the mesh to the empty
                        obj.parent = empty
                        #materal
                        mat = make_material(model, mesh)
                        
                        obj.data.materials.append(mat)
                        
                    collection.objects.link(empty)
                
                    mesh = model.meshes[-1]
                    #we're gonna create the object early so we can add the vertex weights
                    meshdata = bpy.data.meshes.new(f'{model.name}_deformable')
                    meshdata.auto_smooth_angle = 180
                    meshdata.use_auto_smooth = True
                    obj = bpy.data.objects.new(f'{model.name}_deformable', bpy.data.meshes[f'{model.name}_deformable'])
                    bone_indices = {}
                    for i in range(len(parent_clump.pose.bones)):
                        obj.vertex_groups.new(name = parent_clump.pose.bones[i].name)
                        bone_indices[parent_clump.pose.bones[i].name] = i
                    
                    #print(bone_indices)
                    bm = bmesh.new()
                    vgroup_layer = bm.verts.layers.deform.new("Weights")
                    

                    for i in range(mesh.VertexCount):
                        #calculate vertex final position
                        vertex_matrix1 = model.clump.bones[mesh.Vertices[i].Bones[0]].matrix
                        vertex_matrix2 = model.clump.bones[mesh.Vertices[i].Bones[1]].matrix
                        vp1 = (vertex_matrix1 @ Vector(mesh.Vertices[i].Positions[0]) * mesh.Vertices[i].Weights[0]) 

                        if mesh.Vertices[i].Bones[1] != "":
                            '''if mesh.Vertices[i].Weights[1] == 0:
                                print(f"weight is 0, bone is {mesh.Vertices[i].Bones[1]}")
                                print(f"first bone is {mesh.Vertices[i].Bones[0]}, weight is {mesh.Vertices[i].Weights[0]}")'''
                            vp2 = (vertex_matrix2 @ Vector(mesh.Vertices[i].Positions[1]) * mesh.Vertices[i].Weights[1])
                        else:
                            vp2 = Vector((0,0,0))
                        

                        vert = bm.verts.new(vp1 + vp2)
                        
                        bm.verts.ensure_lookup_table()
                        #add vertex weights
                        BoneID1 = bone_indices.get(mesh.Vertices[i].Bones[0])
                        BoneID2 = bone_indices.get(mesh.Vertices[i].Bones[1])
                        bm.verts[i][vgroup_layer][BoneID1] = mesh.Vertices[i].Weights[0]
                        bm.verts[i][vgroup_layer][BoneID2] = mesh.Vertices[i].Weights[1]

                    bm.verts.ensure_lookup_table()
                    bm.verts.index_update()

                    uv_layer = bm.loops.layers.uv.new(f"UV")

                    for tris in mesh.Triangles:
                        face = bm.faces.new((bm.verts[tris[0]], bm.verts[tris[1]], bm.verts[tris[2]]))
                        face.smooth = True
                        for loop in face.loops:
                            original_uv = mesh.Vertices[loop.vert.index].UV
                            loop[uv_layer].uv = original_uv
                    bm.faces.ensure_lookup_table()

                    #clean up the mesh
                    bmesh.ops.remove_doubles(bm, verts= bm.verts, dist= 0.00001)
                    #make sure that all the normals are pointing the right way
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

                    bm.to_mesh(meshdata)
                    collection.objects.link(bpy.data.objects[f'{model.name}_deformable'])

                    #parent the mesh to the empty
                    obj.parent = empty
                    #materal
                    mat = make_material(model, mesh)
                    
                    obj.data.materials.append(mat)

                    #add armature modifier
                    armature_modifier = obj.modifiers.new(name = f'{parent_clump.name}', type = 'ARMATURE')
                    armature_modifier.object = parent_clump

        print(f'CCS read in {perf_counter() - start} seconds')

        return {'FINISHED'}

class InstallPillow(Operator):
    bl_idname = "object.install_pillow"
    bl_label = "Install Pillow"
    bl_description = "Install Pillow"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        if install_pillow():
            self.report({'INFO'}, "Pillow installed successfully")
        else:
            self.report({'ERROR'}, "Pillow installation failed")
        return {'FINISHED'}