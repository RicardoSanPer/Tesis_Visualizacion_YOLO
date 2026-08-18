import bpy
from .yolo_properties import YoloDataSettings
from ..utils import utils

CLASSES = [YoloDataSettings]

def register_properties():
    utils.register_classes(CLASSES)

    bpy.types.Scene.yolo_settings = bpy.props.PointerProperty(
            type=YoloDataSettings
        )

def unregister_properties():
    if hasattr(bpy.types.Scene, "yolo_settings"):
            del bpy.types.Scene.yolo_settings

    utils.unregister_classes(CLASSES)
    