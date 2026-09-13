import bpy

def register_classes(CLASSES: list):
    """Registra las clases en la escena

    Args:
        CLASSES (list): Lista de clases
    """
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister_classes(CLASSES: list):
    """De-registra las clases en la escena

    Args:
        CLASSES (list): Lista de clases
    """
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)