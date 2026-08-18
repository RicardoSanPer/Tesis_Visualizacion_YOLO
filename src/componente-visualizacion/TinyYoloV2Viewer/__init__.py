import bpy
from .operators import register_operators, unregister_operators
from .properties import register_properties, unregister_properties
from .ui import register_ui, unregister_ui

# Registrar extensión
def register():
    register_operators()
    register_properties()
    register_ui()

def unregister():
    unregister_ui()
    unregister_properties()
    unregister_operators()

if __name__=="__main__":
    register()