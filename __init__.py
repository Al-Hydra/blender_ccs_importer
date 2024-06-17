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
    "blender" : (4, 1, 0),
    "version" : (1, 0, 9),
    "location" : "View3D",
    "warning" : "",
    "category" : "Import"
}

import bpy

from .importer import *


def register():
    bpy.utils.register_class(CCS_PropertyGroup)
    bpy.types.Scene.ccs_importer = bpy.props.PointerProperty(type=CCS_PropertyGroup)
    bpy.utils.register_class(CCS_IMPORTER_OT_IMPORT)
    bpy.utils.register_class(DropCCS)
    bpy.utils.register_class(CCS_FH_import)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(CCS_PropertyGroup)
    bpy.utils.unregister_class(CCS_IMPORTER_OT_IMPORT)
    bpy.utils.unregister_class(DropCCS)
    bpy.utils.unregister_class(CCS_FH_import)
    del bpy.types.Scene.ccs_importer
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
