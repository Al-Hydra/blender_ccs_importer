import bpy, bmesh, math, mathutils
from bpy.types import PropertyGroup, Operator, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty, CollectionProperty, IntProperty
from .ccs_lib.ccs import *
from mathutils import Vector, Matrix, Euler, Quaternion
from math import radians, tan
import numpy as np
from time import perf_counter, time
from bpy_extras.io_utils import ExportHelper
from .ccs_lib.ccsClump import *
from .ccs_lib.ccsModel import *
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


class CCS_IMPORTER_OT_EXPORT(Operator, ExportHelper):
    bl_idname = 'export_scene.ccs'
    bl_label = 'Export CCSF Archive'
    filename_ext = '.ccs'

    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    
    '''
    export_original_bone_data: bpy.props.BoolProperty(
        name="Use Original Bone Data",
        default=False,
        description="Export bone data using stored matrix/rotation/scale from custom bone properties")
    '''
    

    def draw(self, context):
        layout = self.layout
        #layout.prop(self, "export_original_bone_data")
    
    def execute(self, context):
        start_time = time()

        ccsf = readCCS(self.filepath)
        blender_model = context.object
        print(f"Exporting model: {blender_model.name}")
        print(f"Exporting model: {blender_model.parent}")
        
        #ccsf_model = next((m for m in ccsf.sortedChunks["Model"] if m.name == blender_model.name), None)
        cmpChunk = next((m for m in ccsf.sortedChunks["Clump"] if m.name == blender_model.name), None)
        if not cmpChunk:
            self.report({'ERROR'}, "Matching CCSF clump not found.")
            return {"CANCELLED"}
        else:
            print("Found matching CCSF clump.")

        # Mesh
        for i, child in enumerate(blender_model.children):
            mesh_obj = child
            mdlChunk = next((m for m in ccsf.sortedChunks["Model"] if m.name == mesh_obj.name), None)
            #print(f"mdlChunk: {mdlChunk}")
            if not mdlChunk:
                self.report({'ERROR'}, f"Matching CCSF model not found {mesh_obj.name}.")
                return {"CANCELLED"}
            else:
                print("Found matching CCSF model.")

            #print(f"mesh_obj: {mesh_obj}")
            blender_mesh = mesh_obj.data
            blender_mesh.calc_loop_triangles()
            blender_mesh.calc_tangents()
            #print(f"blender_mesh: {blender_mesh}")

            if not blender_mesh.color_attributes:
                blender_mesh.vertex_colors.new(name='Color', type="BYTE_COLOR", domain="CORNER")
            color_layer = blender_mesh.color_attributes[0].data
            uv_layer = blender_mesh.uv_layers[0].data if blender_mesh.uv_layers else None
            vertex_groups = mesh_obj.vertex_groups


            # Replace mesh data in model chunks
            if mdlChunk.modelType & ModelTypes.Deformable and not mdlChunk.modelType & ModelTypes.TrianglesList:
                exportDeformable(self, blender_model, mesh_obj, blender_mesh, cmpChunk, mdlChunk, ccsf, uv_layer, color_layer)
                print(f'Exported mdlChunk: {mdlChunk.name}')

            elif mdlChunk.modelType == ModelTypes.ShadowMesh:
                print(f'TODO: Export ShadowMesh')

            elif mdlChunk.modelType & ModelTypes.TrianglesList:
                print(f'TODO: Export TrianglesList')

            else:
                print(f'TOFINISH: Export Rigid')
                exportRigid(self, blender_model, mesh_obj, blender_mesh, cmpChunk, mdlChunk, ccsf, uv_layer, color_layer)
                

        elapsed = time() - start_time
        msg = f"Exported in {elapsed:.2f}s"
        print(msg)
        self.report({'INFO'}, msg)

        writeCCS(f"{self.filepath}", ccsf)

        return {'FINISHED'}



def exportRigid(self, blender_model, mesh_obj, blender_mesh, cmpChunk, mdlChunk, ccsf, uv_layer, color_layer):

    next_index = 0

    bm = bmesh.new()
    bm.from_mesh(blender_mesh)
    bm.verts.ensure_lookup_table()

    # Prepare Bone matrix for export
    print(f"blender_model: {blender_model}")
    print(f"mesh_obj: {mesh_obj}")
    mesh_matrix = mesh_obj.matrix_world # Get the world matrix of the mesh object
    armature_matrix = blender_model.matrix_world
    print(f"mesh_matrix: {mesh_matrix}, armature_matrix: {armature_matrix}")

    mesh = RigidMesh()

    bone_name = mesh_obj.name.replace("MDL_", "OBJ_")
    print(f'RigidMesh bone_name: {bone_name}')
    # create bone matrix
    for b in blender_model.data.bones:
        if b.name == bone_name:
            br_w_mtx = armature_matrix @ b.matrix_local
            br_w_inv = br_w_mtx.inverted()
            bone_mtx = br_w_inv @ mesh_matrix
            bone_mtx_3x3 = bone_mtx.to_3x3()
            break


    for tri in blender_mesh.loop_triangles:

        for l, loop_index in enumerate(tri.loops):
            loop = blender_mesh.loops[loop_index]
            v_idx = loop.vertex_index
            v = blender_mesh.vertices[v_idx]
            bm_vert = bm.verts[v_idx]

            # Single trianle flags layout
            # Read from end
            # flags = [2, 2, 0]  # start, middle, end
            # Read from start ?
            # flags = [1, 1, 0]  # start, middle, end

            #flags = [2, 2, 0]  # start, middle, end
            flags = [1, 1, 0]  # start, middle, end
            
            # prepare position, normal, tangent, bitangent
            pos = bone_mtx @ v.co
            norm = (bone_mtx_3x3 @ loop.normal).normalized()
            tang = (bone_mtx_3x3 @ loop.tangent).normalized()
            bi = (bone_mtx_3x3 @ loop.bitangent).normalized()
            triFlag = flags[l]
            uv = uv_layer[loop_index].uv
            col = [int(c * 255) for c in color_layer[loop_index].color_srgb]

            if loop_index >= len(uv_layer):
                print(f"[UV ERROR] loop_index {loop_index} out of range for UV layer with length {len(uv_layer)}")

            mesh_v = Vertex()
            mesh_v.position = tuple(pos)
            mesh_v.normal = tuple(norm)
            #mesh_v.tangents = tuple(tang)
            #mesh_v.binormals = tuple(bi)
            mesh_v.color = col
            mesh_v.UV = uv
            #mesh_v.triangleFlag = 0
            mesh_v.triangleFlag = triFlag

            mesh.vertices.append(mesh_v)
            next_index += 1

    # copy parent anf material from original mesh in ccs
    mesh.parentIndex = mdlChunk.meshes[0].parentIndex
    mesh.materialIndex = mdlChunk.meshes[0].materialIndex

    mesh.vertexCount = len(mesh.vertices)
    mdlChunk.meshes = mesh

    bm.free()

    return



def exportDeformable(self, blender_model, mesh_obj, blender_mesh, cmpChunk, mdlChunk, ccsf, uv_layer, color_layer):
    # get bone reference from clump
    if mdlChunk.lookupList != None:
        bones = [cmpChunk.bones[cmpChunk.boneIndices[i]] for i in mdlChunk.lookupList]
    else:
        bones = blender_mesh
    print(f'bones = {bones}')

    next_index = 0

    bm = bmesh.new()
    bm.from_mesh(blender_mesh)
    bm.verts.ensure_lookup_table()

    # Sort triangles by single or multi-weight vertices, weight groups & material
    # This will help in organizing triangles into meshes within the CCSF model
    tri_weights_single = []
    tri_weights_single_mat_groups = {}
    tri_weights_multi = []
    tri_weights_multi_mat = {}
    bonelookupList_groups = {}  # track bones and their related data
    
    matList = {}  # To track materials and their corresponding CCSF material chunks

    # Prepare Bone matrix for export
    print(f"blender_model: {blender_model}")
    print(f"mesh_obj: {mesh_obj}")
    mesh_matrix = mesh_obj.matrix_world # Get the world matrix of the mesh object
    armature_matrix = blender_model.matrix_world
    print(f"mesh_matrix: {mesh_matrix}, armature_matrix: {armature_matrix}")

    for tri in blender_mesh.loop_triangles:
        tri_single = True  # default to single weight until proven otherwise
        group_indices = []

        for loop_index in tri.loops:
            loop = blender_mesh.loops[loop_index]
            v_idx = loop.vertex_index
            v = blender_mesh.vertices[v_idx]
            v_groups = []

            for g in v.groups:
                if g.weight > 0.0:
                    v_groups.append(g)
                    group_idx = g.group
                    group_name = mesh_obj.vertex_groups[group_idx].name

                    for obj in ccsf.sortedChunks["Object"]:
                        if obj.name == group_name:
                            chunk_idx = obj.index
                            break

                    if group_idx not in bonelookupList_groups:
                        
                        # create bone matrix
                        for b in blender_model.data.bones:
                            if b.name == group_name:
                                #print(f"ArmatureBone: {b.name}")
                                # get bone rest matrix
                                br_w_mtx = armature_matrix @ b.matrix_local
                                br_w_inv = br_w_mtx.inverted()
                                bone_mtx = br_w_inv @ mesh_matrix
                                break

                        for i , bone in enumerate(bones):
                            if bone.name == group_name:
                                bone_idx = i
                                break

                        bonelookupList_groups[group_idx] = (group_name, chunk_idx, bone_idx, bone_mtx)

            #print(f"v_groups: {v_groups}")

            if len(v_groups) == 0:
                tri_single = False
                break

            elif len(v_groups) != 1:
                tri_single = False
                break

            else:
                group_idx = next(i.group for i in v_groups)
                group_indices.append(group_idx)

        if tri_single:
            #tri_weights_single.append(tri)
            # Group triangles where all vertices share the same material & weight group
            if group_indices[0] == group_indices[1] == group_indices[2]:
                tri_weights_single.append(tri)
                group_idx = group_indices[0]
                mat_idx = tri.material_index

                if mat_idx not in tri_weights_single_mat_groups:
                    tri_weights_single_mat_groups[mat_idx] = {}

                if group_idx not in tri_weights_single_mat_groups[mat_idx]:
                    tri_weights_single_mat_groups[mat_idx][group_idx] = []

                tri_weights_single_mat_groups[mat_idx][group_idx].append(tri)

                # Create refrance list for materials and their corresponding CCSF material chunks
                if mat_idx not in matList:
                    mdl_prefix = blender_mesh.name
                    print(f"mdl_prefix: {mdl_prefix}")
                    mat_name = blender_mesh.materials[mat_idx].name
                    mat_name = mat_name.removeprefix(mdl_prefix + "_")
                    print(f"mdl_prefix: {mdl_prefix}, mat_name: {mat_name}")

                    ccsf_mat = next((m for m in ccsf.sortedChunks["Material"] if m.name == mat_name), None)
                    if not ccsf_mat:
                        self.report({'ERROR'}, "Matching CCSF material not found.")
                        return {"CANCELLED"}
                    else:
                        chunk_idx = ccsf_mat.index
                        print("Found matching CCSF material.")
            
                    matList[mat_idx] = (mat_name, chunk_idx)
                    print(f"matList: {matList[mat_idx]}")
            else:
                tri_weights_multi.append(tri)
                # Group triangles where vertices share the same material
                mat_idx = tri.material_index
                if mat_idx not in tri_weights_multi_mat:
                    tri_weights_multi_mat[mat_idx] = []
                tri_weights_multi_mat[mat_idx].append(tri)
        else:
            tri_weights_multi.append(tri)
            # Group triangles where vertices share the same material
            mat_idx = tri.material_index
            if mat_idx not in tri_weights_multi_mat:
                tri_weights_multi_mat[mat_idx] = []
            tri_weights_multi_mat[mat_idx].append(tri)


    meshes = list()

    for mat_idx in tri_weights_single_mat_groups:
        for group_idx in tri_weights_single_mat_groups[mat_idx]:

            mesh = DeformableMesh()
            deformableVerticesCount = 0

            for i, tri in enumerate(tri_weights_single_mat_groups[mat_idx][group_idx]):
                mat_name = blender_mesh.materials[tri.material_index].name
                chunk_idx = matList[tri.material_index][1]

                # Single trianle flags layout
                # Read from end
                # flags = [2, 2, 0]  # start, middle, end
                # Read from start ?
                # flags = [1, 1, 0]  # start, middle, end

                #flags = [2, 2, 0]  # start, middle, end
                flags = [1, 1, 0]  # start, middle, end

                for l, loop_index in enumerate(tri.loops):
                    loop = blender_mesh.loops[loop_index]
                    v_idx = loop.vertex_index
                    v = blender_mesh.vertices[v_idx]
                    bm_vert = bm.verts[v_idx]

                    bone_mtx = bonelookupList_groups[group_idx][3]
                    #bone_mtx_3x3 = bone_mtx.to_3x3().inverted().transposed()
                    bone_mtx_3x3 = bone_mtx.to_3x3()
                    #print(f"bonelookupList_groups{bonelookupList_groups[group_idx]}, bone_mtx {bone_mtx}")
                    bone_idx = bonelookupList_groups[group_idx][2]
                    #print(f"bone_idx: {bone_idx}")

                    # prepare position, normal, tangent, bitangent
                    pos = bone_mtx @ v.co
                    norm = (bone_mtx_3x3 @ loop.normal).normalized()
                    tang = (bone_mtx_3x3 @ loop.tangent).normalized()
                    bi = (bone_mtx_3x3 @ loop.bitangent).normalized()
                    triFlag = flags[l]
                    uv = uv_layer[loop_index].uv
                    col = [int(c * 255) for c in color_layer[loop_index].color_srgb]
                    #print(f"pos: {pos}")
                    #print(f"uv : {uv}")
                    #print(f"uv_final : {uv_final}")

                    if loop_index >= len(uv_layer):
                        print(f"[UV ERROR] loop_index {loop_index} out of range for UV layer with length {len(uv_layer)}")

                    weights = None
                    bone_ids = None

                    mesh_v = DeformableVertex()
                    mesh_v.positions = [tuple(pos), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
                    mesh_v.normals = [tuple(norm), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
                    mesh_v.tangents = [tuple(tang), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
                    mesh_v.binormals = [tuple(bi), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
                    mesh_v.weights = [1,0,0,0]
                    mesh_v.UV = uv
                    mesh_v.boneIDs = [bone_idx,0,0,0] # Bone bone_idx
                    #mesh_v.triangleFlag = 0
                    mesh_v.triangleFlag = triFlag
                    mesh_v.multiWeight = False

                    mesh.vertices.append(mesh_v)
                    next_index += 1

                mesh.vertexCount = len(mesh.vertices)

            mesh.materialIndex = chunk_idx
            meshes.append(mesh)


    for mat_idx in tri_weights_multi_mat:

        mesh = DeformableMesh()
        deformableVerticesCount = 0
        
        for i, tri in enumerate(tri_weights_multi_mat[mat_idx]):

            # Single trianle flags layout
            # Read from end
            # flags = [2, 2, 0]  # start, middle, end
            # Read from start ?
            # flags = [1, 1, 0]  # start, middle, end

            #flags = [2, 2, 0]  # start, middle, end
            flags = [1, 1, 0]  # start, middle, end

            for l, loop_index in enumerate(tri.loops):
                loop = blender_mesh.loops[loop_index]
                v_idx = loop.vertex_index
                v = blender_mesh.vertices[v_idx]
                bm_vert = bm.verts[v_idx]
                
                groups = sorted(v.groups, key=lambda g: 1 - g.weight)
                #print(f"groups: {groups}")
                b_weights = []
                for g in groups:
                    if g.group in bonelookupList_groups:
                        group_name, _, lookup_idx, _ = bonelookupList_groups[g.group]
                        b_weights.append((g.group, group_name, lookup_idx, g.weight))
                
                if ccsf.version < 0x125:
                    b_weights = b_weights[:2]
                else:
                    b_weights = b_weights[:4]

                weightCount = len(b_weights)
                #print(f"b_weights: {b_weights}")
                normalized_weights = normalize_weights(b_weights)
                #print(f"normalized_weights: {normalized_weights}")

                bone_mtx = []
                bone_mtx_3x3 = []
                boneIDs = []
                weights = []
                for w in normalized_weights:
                    group_idx, _, bone_idx, weight = w
                    if group_idx is not None:
                        bone_mtx.append(bonelookupList_groups[group_idx][3])
                        #bone_mtx_3x3.append(bonelookupList_groups[group_idx][3].to_3x3().inverted().transposed())
                        bone_mtx_3x3.append(bonelookupList_groups[group_idx][3].to_3x3())
                        boneIDs.append(bone_idx)
                        weights.append(weight)
                    else:
                        boneIDs.append(0)
                        weights.append(0)

                pos = []
                norm = []
                tang = []
                bi = []
                for m, bone_mtx in enumerate(bone_mtx):
                    # prepare position, normal, tangent, bitangent
                    pos.append(tuple(bone_mtx @ v.co))
                    norm.append(tuple((bone_mtx_3x3[m] @ loop.normal).normalized()))
                    tang.append(tuple((bone_mtx_3x3[m] @ loop.tangent).normalized()))
                    bi.append(tuple((bone_mtx_3x3[m] @ loop.bitangent).normalized()))

                uv = uv_layer[loop_index].uv
                col = [int(c * 255) for c in color_layer[loop_index].color_srgb]
                triFlag = flags[l]

                mesh_v = DeformableVertex()
                mesh_v.positions = pos
                #print(f"pos: {pos}")
                #print(f" mesh_v.positions: { mesh_v.positions}")
                mesh_v.normals = norm
                mesh_v.tangents = tang
                mesh_v.binormals = bi
                mesh_v.weights = [weights[0],weights[1],weights[2],weights[3]]
                mesh_v.UV = uv
                mesh_v.boneIDs = [boneIDs[0],boneIDs[1],boneIDs[2],boneIDs[3]] # Bone index
                #mesh_v.triangleFlag = 0
                mesh_v.triangleFlag = triFlag
                mesh_v.multiWeight = False
                #print(f"len(pos): {len(norm)}")
                if len(pos) > 1:
                    mesh_v.multiWeight = True

                mesh.vertices.append(mesh_v)
                deformableVerticesCount += len(norm)

            mesh.vertexCount = len(mesh.vertices)
            mesh.deformableVerticesCount = deformableVerticesCount 

        mesh.materialIndex = chunk_idx
        meshes.append(mesh)


    mdlChunk.meshes = meshes
    mdlChunk.meshCount = len(mdlChunk.meshes)

    bm.free()

    return


def normalize_weights(b_weights):
    # Extract only real weights (group_idx != None)
    weights = [w for w in b_weights if w[1] is not None]
    total = sum(w[3] for w in weights)

    if total > 0:
        # Normalize weights
        normalized_weights = [(w[0], w[1], w[2], w[3] / total) for w in weights]
    #print(f"normalized_weights: {normalized_weights}")
    else: 
        print(f'b_weights == {b_weights}')
        normalized_weights = [(w[0], w[1], w[2], w[3]) for w in weights]

    # Replace original list, add dummy weights
    final_weights = (normalized_weights + [(None, None, None, 0.0)] * 4)[:4]
    #print(f"final_weights: {final_weights}")

    return final_weights


def menu_func_export(self, context):
    self.layout.operator(CCS_IMPORTER_OT_EXPORT.bl_idname,
                        text='CyberConnect Streaming File (.ccs)')
