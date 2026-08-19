from ..utils import utils
from .generate_ui import VIEW3D_PT_GeoNodesGeneratorPanel

CLASSES = [VIEW3D_PT_GeoNodesGeneratorPanel]

def register_ui():
    utils.register_classes(CLASSES)

def unregister_ui():
    utils.unregister_classes(CLASSES)