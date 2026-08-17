import bpy
from .import_data import IMPORT_OT_LoadYoloManifest
from .yolo_properties import YoloDataSettings

classes = (YoloDataSettings, IMPORT_OT_LoadYoloManifest)

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_LoadYoloManifest.bl_idname, text="Load Yolo Manifest (.json)")

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.yolo_settings = bpy.props.PointerProperty(
        type=YoloDataSettings
    )
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    if hasattr(bpy.types.Scene, "yolo_settings"):
        del bpy.types.Scene.json_settings

    for cls in classes:
            bpy.utils.unregister_class(cls)

if __name__=="__main__":
    register()