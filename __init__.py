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
    "blender" : (3, 4, 0),
    "version" : (0, 1, 0),
    "location" : "View3D",
    "warning" : "",
    "category" : "Object"
}

import bpy

from . import Panel


def register():
    bpy.utils.register_class(Panel.CCS_IMPORTER_PT_PANEL)
    bpy.utils.register_class(Panel.CCS_IMPORTER_OT_IMPORT)
    bpy.utils.register_class(Panel.CCS_PropertyGroup)
    bpy.types.Scene.ccs_importer = bpy.props.PointerProperty(type=Panel.CCS_PropertyGroup)

def unregister():
    bpy.utils.unregister_class(Panel.CCS_IMPORTER_PT_PANEL)
    bpy.utils.unregister_class(Panel.CCS_IMPORTER_OT_IMPORT)
    bpy.utils.unregister_class(Panel.CCS_PropertyGroup)
    del bpy.types.Scene.ccs_importer
