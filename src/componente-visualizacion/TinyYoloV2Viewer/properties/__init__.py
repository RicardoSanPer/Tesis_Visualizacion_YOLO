import bpy
from .manifest_properties import ManifestDataSettings
from .visualization_properties import VisualizationDataProperties
from .visualization_properties import LayerTypeProperty, ObjectHolder
from ..utils import utils

CLASSES = [LayerTypeProperty, ObjectHolder, ManifestDataSettings, VisualizationDataProperties]

def register_properties():
    utils.register_classes(CLASSES)

    bpy.types.Scene.yolo_settings = bpy.props.PointerProperty(
        type=ManifestDataSettings
    )

    bpy.types.Scene.yolo_visualization_settings = bpy.props.PointerProperty(
        type = VisualizationDataProperties
    )

def unregister_properties():
    if hasattr(bpy.types.Scene, "yolo_visualization_settings"):
                del bpy.types.Scene.yolo_visualization_settings

    if hasattr(bpy.types.Scene, "yolo_settings"):
            del bpy.types.Scene.yolo_settings

    utils.unregister_classes(CLASSES)
    