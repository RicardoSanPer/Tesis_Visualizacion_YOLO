import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty, PointerProperty, BoolProperty
from ..geometry_nodes import load

"""Propiedades para la visualización de la red, como colores de capa, escala de tamaño
y visibilidad
"""

def actualizar_colores(self, context):
    """Actualiza los colores de las capas en base al tipo"""
    type_name = self.name
    new_color = tuple(self.color)
    graph = context.scene.yolo_graph

    for item in graph.layers:
        if item.type == type_name:
            params = {"Color" : new_color}
            load.configurar_parametros_nodo(item.object, "Geometry Nodes", params)

def actualizar_visibilidad(self, context):
    """Actualiza la visualización simplificada en base al tipo de capa"""
    type_name = self.name
    new_visibility = self.visibility
    graph = context.scene.yolo_graph

    for item in graph.layers:
        if item.type == type_name:
            params = {"Simplified Volume" : new_visibility}
            load.configurar_parametros_nodo(item.object, "Geometry Nodes", params)

def actualizar_dimensiones(self, context):
    """Actualiza las dimensiones de los objetos de visualización de capas
    en base a la escala y profunidad máxima"""
    yolo_vis = context.scene.yolo_visualization_settings
    yolo_graph = context.scene.yolo_graph
    parsed = context.scene.yolo_settings.get_parsed_json()

    ## Capas
    for layer in yolo_graph.layers:
        x = layer.dimensions[0] * yolo_vis.size_scale
        y = layer.dimensions[1] * yolo_vis.size_scale
        z = layer.dimensions[2] * yolo_vis.layer_depth

        if z > yolo_vis.layer_max_depth: z = yolo_vis.layer_max_depth

        params = {"World Size": (x, y, z)}

        load.configurar_parametros_nodo(layer.object, "Geometry Nodes", params)

    actualizar_posiciones(self, context)

def actualizar_posiciones(self, context):
    """Actualiza la posición de los objetos de visualización de capas
    en base al espaciado de capas, escala y tamaño máximo"""
    yolo_vis = context.scene.yolo_visualization_settings
    yolo_graph = context.scene.yolo_graph

    offset = 0
    for layer in yolo_graph.layers:
        if not layer.object:
            self.report({'ERROR'}, f"No se encontró datos de capas {layer.name}")
            return {'CANCELLED'}
        
        layer.object.location = (0, offset, 0)

        depth = layer.dimensions[2] * yolo_vis.layer_depth
        if depth > yolo_vis.layer_max_depth: depth = yolo_vis.layer_max_depth

        offset += depth + yolo_vis.layer_gap
    
class LayerTypeProperty(PropertyGroup):
    """Propiedades de los tipos de capa"""
    name : StringProperty(
        name="Label",
        default="Propiedades de Capa"
    )
    color : FloatVectorProperty(
        name="Color",
        description="Color para este tipo de capa",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5, 0.5, 0.5, 1.0),
        update=actualizar_colores
    )
    visibility : BoolProperty(
        name="Visible",
        default=True,
        description="Determina si la usa la visualización simplificada",
        update=actualizar_visibilidad
    )

class VisualizationDataProperties(PropertyGroup):
    """Propiedades de la visualización"""
    size_scale : FloatProperty(
        name = "Escala",
        description = "Escala de las capas en relación a la resolución",
        default = 0.01,
        soft_min= 0.0,
        update=actualizar_dimensiones
    )
    layer_depth : FloatProperty(
        name = "Escala de Profundidad",
        description= "Escala de la profunidad en base al numero de capas",
        default= 0.01,
        soft_min=0.0,
        update = actualizar_dimensiones
    )
    layer_gap : FloatProperty(
        name = "Espaciado",
        description= "Espaciado entre capas de la red",
        default= 0.5,
        soft_min=0.0,
        update= actualizar_posiciones
    )
    layer_max_depth : FloatProperty(
         name="Profundidad Máxima",
         description= "Pofundidad máxima de las capas",
         default=2.0,
         soft_min = 0,
         update=actualizar_dimensiones
    )
    layer_properties : CollectionProperty(
        type=LayerTypeProperty
        )

    def crear_propiedades_capa(self, name:str, rgba: tuple = (0.5, 0.5, 0.5, 1.0), visibility: bool = True):
        """Crea las propiedades iniciales de un tipo de capa"""
        item = self.layer_properties.get(name)
        if not item:
            item = self.layer_properties.add()
            item.name = name
        item.visibility = visibility
        item.color = rgba
        return item


