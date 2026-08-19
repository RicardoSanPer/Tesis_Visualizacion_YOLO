import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty

class LayerColor(PropertyGroup):
    name : StringProperty(
        name="Label",
        default="Color de Capa"
    )
    color : FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5, 0.5, 0.5, 1.0)
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
    layer_colors : CollectionProperty(
        type=LayerColor
        )

    def add_layer_color(self, name:str, rgba: tuple = (0.5, 0.5, 0.5, 1.0)):
        item = self.layer_colors.get(name)
        if not item:
            item = self.layer_colors.add()
            item.name = name
        item.color = rgba
        return item

    def get_layer_color(self, name: str):
        item = self.layer_colors.get(name)
        if item:
            return tuple(item.color)
        return (0.5, 0.5, 0.5, 1.0)


