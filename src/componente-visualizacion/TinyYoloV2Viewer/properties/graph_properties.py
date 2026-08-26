import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatVectorProperty, BoolProperty, CollectionProperty

"""Propiedades de la red por capa y de la geometría
"""


class StringItem(PropertyGroup):
    """Clase para almacenar un string en una colección de propiedades."""
    value: StringProperty(name="String Value")

class LayerItem(PropertyGroup):
    """Clase para almacenar los objetos que corresponden a cada capa de la red, 
    incluyendo su nombre, tipo y objeto asociado.
    """
    name: StringProperty(name="Nombre de Capa")
    type: StringProperty(name="Tipo de Capa")
    dimensions: FloatVectorProperty(name="Tamaño de objeto", size=3, default=(0.0, 0.0, 0.0))
    kernel_size: IntProperty(name="Tamaño de Kernel", default=1, soft_min=1)
    stride: IntProperty(name="Stride", default=1, soft_min=1)
    ceiling: BoolProperty(name="Ceiling Mode", default=False)
    resolution: IntProperty(name="Resolución de Capa", default=0, soft_min=0)
    slice_count: IntProperty(name="Slice Count", default=0, soft_min=0)
    file: StringProperty(name="Archivo de Capa")
    object: PointerProperty(name="Objeto de Capa", type=bpy.types.Object)
    parents: CollectionProperty(name="Padres", type=StringItem)
    children: CollectionProperty(name="Hijos", type=StringItem)

class GraphProperty(PropertyGroup):
    """Clase para almacenar las propiedades del grafo de la red, incluyendo
    la lista de nodos y las relaciones entre ellos."""
    layers: CollectionProperty(
        name="Capas",
        type=LayerItem
    )

    def add_layer(self, name:str, type:str, obj:bpy.types.Object):
        """Agrega un nuevo nodo al grafo."""
        item = self.layers.get(name)
        if not item:
            item = self.layers.add()

        item.name = name
        item.type = type
        item.object = obj

        return item

    def add_node_parent(self, parent: str, child: str):
        """Agrega una relación de padre-hijo entre dos nodos en el grafo."""
        child_node = self.layers.get(child)
        if not child_node:
            child_node = self.layers.add()
            child_node.name = child

        child_node.parents.add().value = parent

    def set_children_nodes(self, graph_node: LayerItem, children_name:list):
        """Establece los hijos de un nodo en el grafo."""
        graph_node.children.clear()
        for child in children_name:
            self.add_node_parent(graph_node.name, child)
            graph_node.children.add().value = child

    def empty(self):
        """Elimina la geometría generada de las capas para regenerar la geometría de la red"""
        for layer in self.layers:
            if not layer.object:
                continue
            
            mesh_data = layer.object.data if isinstance(layer.object.data, bpy.types.Mesh) else None
            bpy.data.objects.remove(layer.object, do_unlink=True)
            if mesh_data and mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)
        self.layers.clear()

    
