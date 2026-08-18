import bpy

def register_classes(CLASSES):
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister_classes(CLASSES):
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)