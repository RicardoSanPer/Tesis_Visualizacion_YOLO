import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatVectorProperty, BoolProperty, CollectionProperty

class StringItem(PropertyGroup):
    """Clase para almacenar un string en una colección de propiedades."""
    value: StringProperty(name="String Value")

class NodeItem(PropertyGroup):
    """Clase para almacenar los objetos que corresponden a cada capa de la red, 
    incluyendo su nombre, tipo y objeto asociado.
    """
    name: StringProperty(name="Nombre de Capa")
    type: StringProperty(name="Tipo de Capa")
    dimensions: FloatVectorProperty(name="Resolución de Capa", size=3, default=(0.0, 0.0, 0.0))
    kernel_size: IntProperty(name="Tamaño de Kernel", default=1, soft_min=1)
    stride: IntProperty(name="Stride", default=1, soft_min=1)
    ceiling: BoolProperty(name="Ceiling Mode", default=False)
    object: PointerProperty(name="Objeto de Capa", type=bpy.types.Object)

class GraphNodeProperty(PropertyGroup):
    """Clase para almacenar las propiedades de cada nodo en el grafo de la red, 
    incluyendo su nombre, profundidad, tamaño y posición y las relaciones de 
    padres e hijos entre los nodos.
    """
    # Nombre de la capa
    name: StringProperty(name="Node Name")
    # Profundidad en la red
    depth : IntProperty(
        name="Node Depth",
        default = 0,
        soft_min=0
     )
    # Numero de hijo respecto al padre
    width: IntProperty(
        name="Node Width",
        default = 0,
        soft_min=0
     )
    # Tamaño de la capa
    size: FloatVectorProperty(
        name="Node Size",
        size=3,
        min=0.0,
        default=(1.0, 1.0, 1.0)
    )
    # Posición respecto a la red
    position: FloatVectorProperty(
        name="Node Position",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    # Objetos padres de la capa
    parents: CollectionProperty(
        name="Padres",
        type=StringItem
    )
    # Objetos de los hijos de la capa
    children: CollectionProperty(
        name="Hijos",
        type=StringItem
    )

class GraphProperty(PropertyGroup):
    """Clase para almacenar las propiedades del grafo de la red, incluyendo
    la lista de nodos y las relaciones entre ellos."""
    layers: CollectionProperty(
        name="Capas",
        type=NodeItem
    )
    nodes: CollectionProperty(
        name="Nodos",
        type=GraphNodeProperty
    )

    def add_item(self, name:str, type:str, obj:bpy.types.Object):
        """Agrega un nuevo nodo al grafo."""
        item = self.layers.get(name)
        if not item:
            item = self.layers.add()

        item.name = name
        item.type = type
        item.object = obj

        return item

    def add_graph_node_from_item(self, item: NodeItem):
        """Agrega un nuevo nodo al grafo con sus propiedades y relaciones."""
        graph_node = self.nodes.get(item.name)

        if not graph_node:
            graph_node = self.nodes.add()

        graph_node.node = item
        graph_node.name = item.name

        return graph_node

    def add_graph_node_parent(self, parent: str, child: str):
        """Agrega una relación de padre-hijo entre dos nodos en el grafo."""
        child_node = self.nodes.get(child)
        if not child_node:
            child_node = self.nodes.add()
            child_node.name = child

        child_node.parents.add().value = parent

    def set_graph_node_children(self, graph_node: GraphNodeProperty, children_name:list):
        """Establece los hijos de un nodo en el grafo."""
        graph_node.children.clear()
        for child in children_name:
            self.add_graph_node_parent(graph_node.name, child)
            graph_node.children.add().value = child

    def calculate_nodes_depth(self):
        """Calcula la profundidad de cada nodo en el grafo."""
        for node in self.nodes:
            if not node.parents:
                node.depth = 0
            for child in node.children:
                child_node = self.nodes.get(child.value)
                if child_node:
                    child_node.depth = max(child_node.depth, node.depth + 1)

    

    
