import bpy
import json
from pathlib import Path
from bpy.types import PropertyGroup
from bpy.props import StringProperty

"""Datos del manifesto
"""


class ManifestDataSettings(PropertyGroup):
    filepath: StringProperty(
        name="Yolo Manifest Path",
        description="Path to the imported manifest JSON file",
        default="",
        subtype='FILE_PATH'
    )
    raw_data: StringProperty(
        name="Raw JSON",
        description="Serialized JSON content",
        default="{}"
    )

    def get_parsed_json(self):
        """Función auxiliar para parsear datos JSON"""
        try:
            return json.loads(self.raw_data)
        except json.JSONDecodeError:
            return {}

    def set_json(self, data_string: str):
        """Función para cargar JSON a los datos

        Args:
            data_string (str): Manifesto en string
        """
        self.raw_data = json.dumps(data_string)

    def get_manifest_location(self):
        """Obtiene la ruta de directorio del manifesto"""
        return Path(self.filepath).parent