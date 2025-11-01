# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "CCS_Importer",
    "author" : "HydraBladeZ",
    "description" : "A tool to import CCS files",
    "blender" : (4, 2, 0),
    "version" : (1, 2, 0),
    "location" : "View3D",
    "warning" : "",
    "category" : "Import"
}

import bpy

from .importer import *
from .exporter import *
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty, PointerProperty,
                       FloatVectorProperty, IntProperty, StringProperty, EnumProperty)
class CCS_UL_SceneMaterials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.material:
            row.label(text=item.material.name, icon='MATERIAL')
        else:
            row.label(text=item.name)
        row.prop(item, 'material',emboss= True, text='', icon='MATERIAL')


class CCS_SceneMaterial_OT_Add(bpy.types.Operator):
    bl_idname = 'ccs_mat.add_material'
    bl_label = 'Add Material'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager

        new_mat = manager.ccs_materials.add()

        return {'FINISHED'}

class CCS_SceneMaterial_OT_Remove(bpy.types.Operator):
    bl_idname = 'ccs_mat.remove_material'
    bl_label = 'Remove Material'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        manager.ccs_materials.remove(manager.ccs_material_index)
        if manager.ccs_material_index > 0:
            manager.ccs_material_index -= 1

        return {'FINISHED'}
    
class CCSSceneMaterialPropertyGroup(PropertyGroup):
    def update_name(self, context):
        if self.material:
            self.name = self.material.name
        else:
            self.name = 'Material'
    name: StringProperty(name='Name', default='Material')
    
    material: PointerProperty(
        type= bpy.types.Material,
        name='Material',
        update= update_name
    )
    
    uvOffset0: FloatVectorProperty(name='UV Offset', size=2, default=(0.0, 0.0))
    uvScale0: FloatVectorProperty(name='UV Scale', size=2, default=(1.0, 1.0))

class ccsSceneManager(bpy.types.PropertyGroup):
    lightdir_object: bpy.props.PointerProperty(type=bpy.types.Object)
    lightdir_color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=3, default=(1, 1, 1), min=0, max=1)
    lightdir_intensity: bpy.props.FloatProperty(name="Intensity", default=1, min=0, max=1)
    
    lightpoint_object: bpy.props.PointerProperty(type=bpy.types.Object)
    lightpoint_color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=3, default=(1, 1, 1), min=0, max=1)
    lightpoint_intensity: bpy.props.FloatProperty(name="Intensity", default=0)
    lightpoint_range: bpy.props.FloatProperty(name="Range", default=10, min=0)
    lightpoint_attenuation: bpy.props.FloatProperty(name="Attenuation", default=2, min=0)
    
    ambient_color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=3, default=(0.5, 0.5, 0.5), min=0, max=1)
    ambient_intensity: bpy.props.FloatProperty(name="Intensity", default=1, min=0, max=1)
    
    fog_color: bpy.props.FloatVectorProperty(name='Fog Color',default=(0.0, 0.0, 0.0),min=0.0,max=1.0,subtype='COLOR',size=3 )
    fog_start: bpy.props.FloatProperty(name='Fog Start',default=10.0,subtype='NONE',)
    
    fog_end: bpy.props.FloatProperty(name='Fog End',default=10000.0,subtype='NONE',)
    
    fog_density: bpy.props.FloatProperty(name='Fog Density',default=0.0,min=0.0,max=100.0,subtype='PERCENTAGE')
    
    ccs_materials : CollectionProperty(
        type=CCSSceneMaterialPropertyGroup,
        name='XFBIN Materials',
    )
    
    ccs_material_index: IntProperty(
        name='XFBIN Material Index',
    )
    
    
class ccsCreateDirLight(bpy.types.Operator):
    bl_idname = "ccs.create_dir_light"
    bl_label = "Create Light"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        
        # create arrow empty for light direction
        lightdir = bpy.data.objects.new("LightDir", None)
        lightdir.empty_display_type = 'SINGLE_ARROW'
        lightdir.empty_display_size = 2
        
        #set the scale to -1 to make the arrow point in the opposite direction
        lightdir.scale = (-1, -1, -1)
        lightdir.location = (0, 0, 0)
        lightdir.rotation_euler = (0, 0, 0)

        # link the object to the scene
        scene.collection.objects.link(lightdir)
        manager.lightdir_object = lightdir
        
        return {'FINISHED'}
    
class ccsCreatePointLight(bpy.types.Operator):
    bl_idname = "ccs.create_point_light"
    bl_label = "Create Light"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        
        # create sphere empty for light point
        lightpoint = bpy.data.objects.new("LightPoint", None)
        lightpoint.empty_display_type = 'SPHERE'
        lightpoint.empty_display_size = 0.5
        lightpoint.location = (0, 0, 0)
        lightpoint.rotation_euler = (0, 0, 0)

        # link the object to the scene
        scene.collection.objects.link(lightpoint)
        manager.lightpoint_object = lightpoint
        
        return {'FINISHED'}


class ccsSceneManagerPanel(bpy.types.Panel):
    bl_label = "CCS Scene Manager"
    bl_idname = "SCENE_PT_ccs_manager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'CCS'
    
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.name == "CCS Scene Manager"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        manager = scene.ccs_manager
        
        box = layout.box()
        box.label(text="CCS Scene Manager")
        
        box = layout.box()
        row = box.row()
        row.label(text='Scene Materials:')
        
        row = box.row()
        # list
        row.template_list("CCS_UL_SceneMaterials", "", manager, "ccs_materials", manager, "ccs_material_index")
        col = row.column(align=True)
        col.operator("ccs_mat.add_material", icon='ADD', text="")
        col.operator("ccs_mat.remove_material", icon='REMOVE', text="")


        row = box.row()
        if manager.ccs_materials and manager.ccs_material_index >= 0:
            matprop: CCSSceneMaterialPropertyGroup = manager.ccs_materials[manager.ccs_material_index]
            row.prop(matprop, 'uvOffset0', text='UV0 Offset')
            row.prop(matprop, 'uvScale0', text='UV0 Scale')
        
        box = layout.box()
        box.label(text="Directional Light")
        row = box.row()
        row.prop(manager, "lightdir_object")
        row.prop(manager, "lightdir_color", text="")
        row.prop(manager, "lightdir_intensity")
        row = box.row()
        row.operator("ccs.create_dir_light")
        
        box = layout.box()
        box.label(text="Point Light")
        row = box.row()
        row.prop(manager, "lightpoint_object")
        row.prop(manager, "lightpoint_color", text="")
        row.prop(manager, "lightpoint_intensity")
        row.prop(manager, "lightpoint_range")
        row.prop(manager, "lightpoint_attenuation")
        
        row = box.row()
        row.operator("ccs.create_point_light")
        
        box = layout.box()
        box.label(text="Ambient Light")
        row = box.row()
        row.prop(manager, "ambient_color", text="")
        row.prop(manager, "ambient_intensity")
        
        box = layout.box()
        box.label(text="Fog")
        row = box.row()
        row.prop(manager, "fog_color", text="")
        row.prop(manager, "fog_density")
        row = box.row()
        row.prop(manager, "fog_start")
        row.prop(manager, "fog_end")
        


class ccsMaterialProperties(bpy.types.PropertyGroup):
    def update_action(self, context):
        action = bpy.data.actions.get(self.action)
        material = context.object.active_material
        if action:
            material.animation_data_create()
            material.animation_data.action = action
    
    alpha: bpy.props.FloatProperty(name="Alpha", default=1, min=0, max=1)
    uvOffset: bpy.props.FloatVectorProperty(name="UV Offset", size=4, default=(0, 0, 1, 1))
    
    #create action prop with update function
    action: bpy.props.StringProperty(name="Action", update=update_action)
    

            

class ccsMaterialPanel(bpy.types.Panel):
    bl_label = "CCS Material Properties"
    bl_idname = "MATERIAL_PT_ccs_material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_category = 'CCS'
    
    @classmethod
    def poll(self, context):
        obj = context.object
        return obj.active_material and obj.active_material.ccs_material
    
    
    
    def draw(self, context):
        obj = context.object
        material = obj.active_material
        properties = material.ccs_material
        
        layout = self.layout
        box = layout.box()
        box.label(text="CCS Material Properties")
        row = box.row()
        row.prop(properties, "alpha")
        row.prop_search(properties, "action", bpy.data, "actions")
        row = box.row()
        row.prop(properties, "uvOffset")


def register():
    bpy.utils.register_class(ccsMaterialProperties)
    bpy.types.Material.ccs_material = bpy.props.PointerProperty(type=ccsMaterialProperties)
    bpy.utils.register_class(CCS_UL_SceneMaterials)
    bpy.utils.register_class(CCS_SceneMaterial_OT_Add)
    bpy.utils.register_class(CCS_SceneMaterial_OT_Remove)
    bpy.utils.register_class(CCSSceneMaterialPropertyGroup)
    bpy.utils.register_class(ccsMaterialPanel)
    bpy.utils.register_class(ccsSceneManager)
    bpy.utils.register_class(ccsCreateDirLight)
    bpy.utils.register_class(ccsCreatePointLight)
    bpy.utils.register_class(ccsSceneManagerPanel)
    bpy.types.Scene.ccs_manager = bpy.props.PointerProperty(type=ccsSceneManager)
    bpy.utils.register_class(ccsObjectProperties)
    bpy.utils.register_class(ccsPropertyGroup)
    bpy.types.Scene.ccs_importer = bpy.props.PointerProperty(type=ccsPropertyGroup)
    bpy.utils.register_class(CCS_IMPORTER_OT_IMPORT)
    bpy.utils.register_class(DropCCS)
    bpy.utils.register_class(CCS_FH_import)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.utils.register_class(CCS_IMPORTER_OT_EXPORT)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ccsMaterialProperties)
    bpy.utils.unregister_class(ccsMaterialPanel)
    del bpy.types.Material.ccs_material
    bpy.utils.unregister_class(CCS_UL_SceneMaterials)
    bpy.utils.unregister_class(CCS_SceneMaterial_OT_Add)
    bpy.utils.unregister_class(CCS_SceneMaterial_OT_Remove)
    bpy.utils.unregister_class(CCSSceneMaterialPropertyGroup)
    bpy.utils.unregister_class(ccsSceneManager)
    bpy.utils.unregister_class(ccsCreateDirLight)
    bpy.utils.unregister_class(ccsCreatePointLight)
    bpy.utils.unregister_class(ccsSceneManagerPanel)
    del bpy.types.Scene.ccs_manager
    bpy.utils.unregister_class(ccsObjectProperties)
    bpy.utils.unregister_class(ccsPropertyGroup)
    bpy.utils.unregister_class(CCS_IMPORTER_OT_IMPORT)
    bpy.utils.unregister_class(DropCCS)
    bpy.utils.unregister_class(CCS_FH_import)
    del bpy.types.Scene.ccs_importer
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(CCS_IMPORTER_OT_EXPORT)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)