import bpy
from .import_json import IMPORT_OT_LoadJSON
from .import_json import menu_func_import
from .generate_geometry import MESH_OT_CreateGeoNodesObject
from ..utils import utils

CLASSES = [IMPORT_OT_LoadJSON, MESH_OT_CreateGeoNodesObject]

def register_operators():
    utils.register_classes(CLASSES)

    # Registrar menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister_operators():
    # Remover menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    utils.unregister_classes(CLASSES)