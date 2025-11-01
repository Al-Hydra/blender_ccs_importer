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


class CCS_UL_SceneActions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.action:
            row.label(text=item.action.name, icon='ACTION')
        else:
            row.label(text=item.name)
        row.prop(item, 'action',emboss= True, text='', icon='ACTION')

class CCS_SceneActionPropertyGroup(PropertyGroup):
    def update_name(self, context):
        if self.action:
            self.name = self.action.name
        else:
            self.name = 'Action'
    
    name: StringProperty(name='Name', default='Action')
    
    action: PointerProperty(
        type= bpy.types.Action,
        name='Action',
        update=update_name
    )


class CCS_SceneAction_OT_Add(bpy.types.Operator):
    bl_idname = 'ccs_action.add_action'
    bl_label = 'Add Action'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager

        new_action = manager.ccs_actions.add()

        return {'FINISHED'}


class CCS_SceneAction_OT_Remove(bpy.types.Operator):
    bl_idname = 'ccs_action.remove_action'
    bl_label = 'Remove Action'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        manager.ccs_actions.remove(manager.ccs_action_index)
        if manager.ccs_action_index > 0:
            manager.ccs_action_index -= 1

        return {'FINISHED'}

class CCS_SceneAction_OT_Move(bpy.types.Operator):
    bl_idname = 'ccs_action.move_action'
    bl_label = 'Move Action'

    direction: EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        )
    )

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        index = manager.ccs_action_index

        if self.direction == 'UP' and index > 0:
            manager.ccs_actions.move(index, index - 1)
            manager.ccs_action_index -= 1
        elif self.direction == 'DOWN' and index < len(manager.ccs_actions) - 1:
            manager.ccs_actions.move(index, index + 1)
            manager.ccs_action_index += 1

        return {'FINISHED'}


class ccsSceneManager(bpy.types.PropertyGroup):
    def update_index(self, context):
        if self.auto_play_actions and self.ccs_actions and self.ccs_action_index >= 0:
            action_prop: CCS_SceneActionPropertyGroup = self.ccs_actions[self.ccs_action_index]
            action = action_prop.action
            if action and self.target_armature:
                # remove anims from the target armature
                target_armature = self.target_armature
                if target_armature.animation_data:
                    target_armature.animation_data_clear()
                
                # assign action to target armature
                if target_armature and target_armature.type == 'ARMATURE':
                    target_armature.animation_data_create()
                    target_armature.animation_data.action = action

                context.scene.frame_start = int(action.frame_range[0])
                context.scene.frame_end = int(action.frame_range[1])
                context.scene.frame_current = context.scene.frame_start
                if not context.screen.is_animation_playing:
                    bpy.ops.screen.animation_play()


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
        name='CCS Materials',
    )
    
    ccs_material_index: IntProperty(
        name='CCS Material Index',
    )
    
    ccs_actions : CollectionProperty(
        type=CCS_SceneActionPropertyGroup,
        name='CCS Actions',
    )
    ccs_action_index: IntProperty(
        name='CCS Action Index',
        default=0,
        update=update_index
    )
    
    target_armature: bpy.props.PointerProperty(type=bpy.types.Object)
    
    auto_play_actions: bpy.props.BoolProperty(name="Auto Play Actions", default=False)
    

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
        row = box.row()
        row.label(text='CCS Animations:')

        row = box.row()
        # list
        row.template_list("CCS_UL_SceneActions", "", manager, "ccs_actions", manager, "ccs_action_index")
        col = row.column(align=True)
        col.operator("ccs_action.add_action", icon='ADD', text="")
        col.operator("ccs_action.remove_action", icon='REMOVE', text="")
        col.separator()
        col.operator("ccs_action.move_action", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("ccs_action.move_action", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # target armature
        row = box.row()
        row.prop(manager, "target_armature")
        
        # play action button
        row.operator("ccs_action.play_action", text="Play Selected Action")
        row.operator("ccs_action.play_all", text="Apply to All")
        row.prop(manager, "auto_play_actions", text="Auto Play Actions")
        
        

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
            row.prop(matprop, 'uvOffset0', text='UV Offset')
            row.prop(matprop, 'uvScale0', text='UV Scale')
        
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


class CCS_SceneAction_OT_Play(bpy.types.Operator):
    bl_idname = 'ccs_action.play_action'
    bl_label = 'Play Action'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        
        index = manager.ccs_action_index
        action_prop: CCS_SceneActionPropertyGroup = manager.ccs_actions[index]
        action = action_prop.action
        if not action:
            return {'CANCELLED'}
        
        
        if manager.ccs_actions and manager.ccs_action_index >= 0:
            action_prop: CCS_SceneActionPropertyGroup = manager.ccs_actions[manager.ccs_action_index]
            action = action_prop.action
            if action:
                # remove anims from all objects
                for obj in scene.objects:
                    if obj.animation_data:
                        obj.animation_data_clear()
                # assign action to target armature
                target_armature = manager.target_armature
                if target_armature and target_armature.type == 'ARMATURE':
                    target_armature.animation_data_create()
                    target_armature.animation_data.action = action

                scene.frame_start = int(action.frame_range[0])
                scene.frame_end = int(action.frame_range[1])
                scene.frame_current = scene.frame_start
                
                # if the animation is already playing, don't start it again
                if not context.screen.is_animation_playing:
                    bpy.ops.screen.animation_play()
                
        return {'FINISHED'}


class CCS_SceneAction_OT_PlayAll(bpy.types.Operator):
    bl_idname = 'ccs_action.play_all'
    bl_label = 'Play All Actions'

    def execute(self, context):
        scene = context.scene
        manager = scene.ccs_manager
        
        index = manager.ccs_action_index
        action_prop: CCS_SceneActionPropertyGroup = manager.ccs_actions[index]
        action = action_prop.action
        if not action:
            return {'CANCELLED'}
        
        if action:
            # remove anims from all objects
            for obj in scene.objects:
                if obj.type == 'ARMATURE' and obj.animation_data:
                    obj.animation_data_clear()
                    # reset all bones
                    for bone in obj.pose.bones:
                        bone.location = (0, 0, 0)
                        bone.rotation_quaternion = (1, 0, 0, 0)
                        bone.scale = (1, 1, 1)
            
            # assign action to all armatures
            for obj in scene.objects:
                if obj.type == 'ARMATURE':
                    obj.animation_data_create()
                    obj.animation_data.action = action

            scene.frame_start = int(action.frame_range[0])
            scene.frame_end = int(action.frame_range[1])
            scene.frame_current = scene.frame_start
            if not context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(CCS_SceneActionPropertyGroup)
    bpy.utils.register_class(CCS_UL_SceneActions)
    bpy.utils.register_class(CCS_SceneAction_OT_Add)
    bpy.utils.register_class(CCS_SceneAction_OT_Remove)
    bpy.utils.register_class(CCS_SceneAction_OT_Move)
    bpy.utils.register_class(CCS_SceneAction_OT_Play)
    bpy.utils.register_class(CCS_SceneAction_OT_PlayAll)


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
    bpy.utils.unregister_class(CCS_SceneActionPropertyGroup)
    bpy.utils.unregister_class(CCS_UL_SceneActions)
    bpy.utils.unregister_class(CCS_SceneAction_OT_Add)
    bpy.utils.unregister_class(CCS_SceneAction_OT_Remove)
    bpy.utils.unregister_class(CCS_SceneAction_OT_Move)
    bpy.utils.unregister_class(CCS_SceneAction_OT_Play)
    bpy.utils.unregister_class(CCS_SceneAction_OT_PlayAll)
    
    
    
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