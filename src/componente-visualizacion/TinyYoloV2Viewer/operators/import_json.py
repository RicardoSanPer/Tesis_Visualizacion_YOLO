import bpy
import json
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

# Agrega opción para cargar el manifesto en el menu de importación
def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_LoadJSON.bl_idname, text="YOLOv2 Manifest (.json)")

# Clase para cargar JSON
class IMPORT_OT_LoadJSON(Operator, ImportHelper):
    """Cargar un archivo JSON con el manifesto de YOLOv2"""
    bl_idname = "import_scene.load_yolo_json"
    bl_label = "Import YOLOv2 Manifest"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Guardar JSON como propiedad de la escena
            settings = context.scene.yolo_settings
            settings.filepath = self.filepath
            settings.set_json(data)

            self.report({'INFO'}, f"Loaded: {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {e}")
            return {'CANCELLED'}