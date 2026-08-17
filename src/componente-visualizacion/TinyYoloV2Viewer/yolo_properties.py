import bpy
import json
from bpy.props import StringProperty, PointerProperty
from bpy.types import PropertyGroup


class YoloDataSettings(PropertyGroup):
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
        """Helper method to return data as a Python dictionary."""
        try:
            return json.loads(self.raw_data)
        except json.JSONDecodeError:
            return {}

    def set_json(self, data_dict):
        """Helper method to serialize a dictionary into the raw_data string."""
        self.raw_data = json.dumps(data_dict)