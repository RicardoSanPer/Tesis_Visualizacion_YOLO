import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty, PointerProperty, BoolProperty
from ..geometry_nodes import load

def update_colors(self, context):
    type_name = self.name
    new_color = tuple(self.color)
    vis_props = context.scene.yolo_visualization_settings

    yolo_data = context.scene.yolo_settings
    parsed = yolo_data.get_parsed_json()

    if "layers_data" not in parsed:
                self.report({'ERROR'}, "No se encontró datos de capas")
                return {'CANCELLED'}

    for item in vis_props.cnn_geometry:
        if parsed["layers_data"][item.layer_name]["type"] == type_name:
            params = {"Color" : new_color}
            load.configurar_parametros_nodo(item.layer_object, "Geometry Nodes", params)

def update_visibility(self, context):
    type_name = self.name
    new_visibility = self.visibility
    vis_props = context.scene.yolo_visualization_settings

    yolo_data = context.scene.yolo_settings
    parsed = yolo_data.get_parsed_json()

    if "layers_data" not in parsed:
                self.report({'ERROR'}, "No se encontró datos de capas")
                return {'CANCELLED'}

    for item in vis_props.cnn_geometry:
        if parsed["layers_data"][item.layer_name]["type"] == type_name:
            params = {"Simplified Volume" : new_visibility}
            load.configurar_parametros_nodo(item.layer_object, "Geometry Nodes", params)
    
class LayerTypeProperty(PropertyGroup):
    name : StringProperty(
        name="Label",
        default="Propiedades de Capa"
    )
    color : FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5, 0.5, 0.5, 1.0),
        update=update_colors
    )
    visibility : BoolProperty(
        name="Visible",
        default=True,
        description="Determina si la capa es visible o no",
        update=update_visibility
    )
          


class ObjectHolder(PropertyGroup):
    layer_name: StringProperty(
        name="Object Name"
    )
    layer_object: PointerProperty(
        name="Object",
        type=bpy.types.Object
    )

class VisualizationDataProperties(PropertyGroup):
    size_scale : FloatProperty(
        name = "Escala",
        description = "Escala de las capas en relacióna a la resolución",
        default = 0.01,
        soft_min= 0.0
    )
    layer_gap : FloatProperty(
        name = "Espaciado",
        description= "Espaciado entre capas de la red",
        default= 0.5,
        soft_min=0.0
    )
    layer_properties : CollectionProperty(
        type=LayerTypeProperty
        )

    cnn_geometry : CollectionProperty(
        type=ObjectHolder
    )

    def create_layer_properties(self, name:str, rgba: tuple = (0.5, 0.5, 0.5, 1.0), visibility: bool = True):
        item = self.layer_properties.get(name)
        if not item:
            item = self.layer_properties.add()
            item.name = name
        item.visibility = visibility
        item.color = rgba
        return item

    def update_layer_color(self, name:str, rgba: tuple = (0.5, 0.5, 0.5, 1.0)):
        item = self.layer_properties.get(name)
        if not item:
            item = self.create_layer_properties(name)
        item.color = rgba
        return item

    def update_layer_visibility(self, name:str, visibility: bool = True):
        item = self.layer_properties.get(name)
        if not item:
            item = self.create_layer_properties(name)
        item.visibility = visibility
        return item

    def get_layer_color(self, name: str):
        item = self.layer_properties.get(name)
        if item:
            return tuple(item.color)
        return (0.5, 0.5, 0.5, 1.0)

    def get_layer_visibility(self, name: str):
        item = self.layer_properties.get(name)
        if item:
            return item.visibility
        return True

    def add_layer(self, name:str, obj:bpy.types.Object):
        item = self.cnn_geometry.add()
        item.name = name
        item.layer_name = name
        item.layer_object = obj
        return item

    def get_layer(self, name:str):
        item = self.cnn_geometry.get(name)
        if item and item.layer_object:
            return item.layer_object
        return None


