from ..utils import utils
from .generate_ui import OBJECT_PT_GeoNodesGeneratorPanel

CLASSES = [OBJECT_PT_GeoNodesGeneratorPanel]

def register_ui():
    utils.register_classes(CLASSES)

def unregister_ui():
    utils.unregister_classes(CLASSES)