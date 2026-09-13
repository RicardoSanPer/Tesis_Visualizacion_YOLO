import bpy
from pathlib import Path
from bpy.types import Operator
from ..geometry_nodes import load
from ..properties.graph_properties import LayerItem
from ..properties.visualization_properties import update_dimensions
"""Generación de la geometría
"""

class MESH_OT_CreateYolov2Object(Operator):
    """Generar geometría de la red"""
    bl_idname = "mesh.create_yolov2_object"
    bl_label = "Generar visualización de red"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        root_collection = scene.collection
        yolo_collection = self._get_or_create_collection("YOLOv2", root_collection)

        yolo_data = scene.yolo_settings
        yolo_graph = scene.yolo_graph

        yolo_graph.empty()

        parsed = yolo_data.get_parsed_json()

        if "layers_data" not in parsed:
            self.report({'ERROR'}, "No se encontró datos de capas")
            return {'CANCELLED'}

        path = context.scene.yolo_settings.get_manifest_location()

         # Entrada
        input = self._instance_nodes("YV2 Input Viewer", "input", context)
        if not input:
            return {'CANCELLED'}

        self._configure_input_viewer(input)

        item_entrada = yolo_graph.add_layer("input", "Input", input)
        item_entrada.dimensions = (416, 416, 4)

        # Cargar informacion de las capas
        last_node = None
        first_node = None
        for layer, layer_info in parsed.get("layers_data").items():
            # Omitir entrada y raíz
            if layer in ("input", "cnn"):
                continue

            obj = self._instance_nodes("YV2 Volume Viewer", layer, context)
            if not obj:
                return {'CANCELLED'}

            ## Grafo
            item = yolo_graph.add_layer(layer, layer_info.get("type", "unknown"), obj)
            self._layer_parameters(item, path, layer_info)
            self._configure_volume_viewer_objects(item)
            yolo_graph.set_children_nodes(item, layer_info["connections"])

            #Coleccion
            node_collection = self._get_or_create_collection(layer_info.get("type"), yolo_collection)
            self._assign_object_to_collection(obj, node_collection)

            last_node = item
            if first_node is None: first_node = item

        # Instancias cajas de salida
        salida = self._instance_nodes("YV2 Box Viewer", "boxes", context)
        if not salida:
            return {'CANCELLED'}
        
        self._configure_box_viewer(salida, path, parsed)

        item_salida = yolo_graph.add_layer("boxes", "Output", salida)
        item_salida.dimensions = (416, 416, 1)

        # Colecciones
        io_collection = self._get_or_create_collection("IO", yolo_collection)
        self._assign_object_to_collection(input, io_collection)
        self._assign_object_to_collection(salida, io_collection)

        # Conexiones entrada/salida
        input_layer_data = parsed["layers_data"]["input"]
        yolo_graph.set_children_nodes(last_node, [item_salida.name])
        yolo_graph.set_children_nodes(item_entrada, input_layer_data["connections"])

        # Instanciar geometria de conexiones
        connection_collection = self._get_or_create_collection("Connections", yolo_collection)
       
        for node in yolo_graph.layers:
            for child in node.children:
                name = f"{node.name}_{child.value}_CONN"
                con = self._instance_nodes("YV2 Volume Connection", name, context)
                if not con:
                    return {'CANCELLED'}

                parent_node = yolo_graph.layers.get(node.name)
                child_node = yolo_graph.layers.get(child.value)
                self._configure_connections(con, parent_node, child_node)
                self._assign_object_to_collection(con, connection_collection)

                yolo_graph.add_connection(name, con)

        load.deduplicate_nodes()
        load.deduplicate_materials()
        load.update_input_image(str(path / "input.png"))

        update_dimensions(self, context)
        scene.yolo_visualization_settings.update_all(context)
        
        self.report({'INFO'}, "Creada red")
        return {'FINISHED'}

    def _instance_nodes(self, node_group_name: str, object_name: str, context):
        """Genera un objeto y asigna un grupo de nodos de geometría

        Args:
            node_group_name (str): Nombre del grupo de nodos
            object_name (str): Nombre del objeto
            context (_type_): Contexto

        Returns:
            bpy.data.objects: Objeto con nodos
        """
        try:
            # 1. Cargar grupo de nodos
            node_group = load.load_geonode_group(node_group_name)
            if not node_group:
                self.report({'ERROR'}, f"No se pudo cargar el grupo '{node_group_name}'")
                return None

            # 2. Crear objeto y asignar ubicación
            mesh_data = bpy.data.meshes.new(name=f"{object_name}_Mesh")
            obj = bpy.data.objects.new(name=object_name, object_data=mesh_data)

            # 3. Vincular a la colección
            context.collection.objects.link(obj)

            # 4. Modificador Geometry Nodes
            modifier = obj.modifiers.new(name="Geometry Nodes", type='NODES')
            modifier.node_group = node_group

            return obj

        except Exception as e:
            self.report({'ERROR'}, f"Failed to instantiate: {e}")
            return None

    def _configure_volume_viewer_objects(self, layer_item: LayerItem):
        """Configura los parametros del grupo de nodos de visualización de volúmenes
        para visualizar una capa de la red

        Args:
            layer_item (LayerItem): LayerItem con los datos de la capa/volymen
        """
        params = {
            "World Size": layer_item.dimensions,
            "Type": layer_item.type,
            "Resolution": layer_item.resolution,
            "Slice Count": layer_item.slice_count,
            "Volume File": layer_item.file,
            "Simplified Volume": True
        }
        load.set_node_parameters(layer_item.object, "Geometry Nodes", params)

    def _configure_box_viewer(self, target_object: bpy.types.Object, boxes_path: Path, parameters: dict):
        """Configura los parametros del grupo de nodos para la visualizacipn de las cajas

        Args:
            obj (bpy.types.Object): Objeto con grupo de nodos de visualización de cajas
            directory (Path): Ruta de directorio del manifesto
            config (dict): Datos
        """
        file = boxes_path / "boxes.vdb"
        params = {
                "Box File" : str(file),
                "Box Count" : parameters["n_boxes"],
                "Class Labels" : parameters["classes"],
                "Confidence" : parameters["confidence"],
                "World Size" : (416, 416, 0)
            }
        load.set_node_parameters(target_object, "Geometry Nodes", params)

    def _configure_input_viewer(Self, target_object: bpy.types.Object):
        """Configura los parametros de la visualización de entrada

        Args:
            target_object (bpy.types.Object): Objeto con el visalizador de entrada asignado.
        """
        params = {
            "World Size" : (416, 416, 3),
            "Resolution" : 416,
            "View Channels" : True
        }
        load.set_node_parameters(target_object, "Geometry Nodes", params)

    def _configure_connections(self, connection_object:bpy.types.Object, parent_layer: LayerItem, child_layer: LayerItem):
        """Configura los parametros del grupo de nodos para la visualización de una conexión entre
        dos capas

        Args:
            connection_object (bpy.types.Object): Objeto con el grupo de nodos de visualización de conexión
            parent_layer (LayerItem): LayerItem con el padre
            child_layer (LayerItem): LayerItem con el hijo
        """
        params = {
            "Input Layer": parent_layer.object,
            "Output Layer": child_layer.object,
            "Kernel Size": child_layer.kernel_size,
            "Stride": child_layer.stride,
            "Ceiling Mode": child_layer.ceiling
        }
        load.set_node_parameters(connection_object, "Geometry Nodes", params)

    def _layer_parameters(self, layer_item: LayerItem, manifest_dir: Path, layer_data: dict):
        """Configura LayerItem con los datos de la capa correspondiente

        Args:
            layer_item (LayerItem): LayerItem
            manifest_dir (Path): Ruta de directorio del manifesto
            layer_data (dict): Datos de la capa
        """
        #Kernel
        if layer_data.get("kernel_size"):
            kernel_size = layer_data["kernel_size"]
            if isinstance(kernel_size, list):
                kernel_size = kernel_size[0]
            elif isinstance(kernel_size, int):
                kernel_size = kernel_size
            layer_item.kernel_size = kernel_size
        # Stride
        if layer_data.get("stride"):
            stride = layer_data["stride"]
            if isinstance(stride, list):
                stride = stride[0]
            elif isinstance(stride, int):
                stride = stride
            layer_item.stride = stride
        # Ceiling
        if layer_data.get("ceiling"):
            layer_item.ceiling = layer_data["ceiling"]
        #Dimensiones
        if layer_data.get("dimensions"):
            dim = layer_data["dimensions"]

            layer_item.dimensions = (dim[2], dim[3], dim[1])
            layer_item.resolution = dim[2]
            
            # Dato del volumen
            if layer_data.get("data"):
                layer_item.slice_count = dim[1]
                layer_item.file = str(manifest_dir / "vdb" / f"{layer_item.name}.vdb")

    def _get_or_create_collection(self, name: str, parent_collection: bpy.types.Collection = None):
        """
        Obtiene o crea una colección
        """
        # Si la colección ya existe
        col = bpy.data.collections.get(name)
        if not col:
            col = bpy.data.collections.new(name)

        # Determinar coleccion padre
        parent_col = parent_collection if parent_collection is not None else bpy.context.scene.collection

        # Vincular a la jerarquia
        if col.name not in parent_col.children:
            parent_col.children.link(col)

        return col

    def _assign_object_to_collection(self, object: bpy.types.Object, target_collection: bpy.types.Collection):
        """Asigna un objeto a una coleccion

        Args:
            object (bpy.types.Object): Objeto a asignar a la coleccion
            target_collection (bpy.types.Collection): Coleccion de destino
        """
        if not object or not target_collection:
            return

        # Vincular a coleccion
        if object.name not in target_collection.objects:
            target_collection.objects.link(object)

        # Quitar de otras colecciones como default
        for col in list(object.users_collection):
            if col != target_collection:
                col.objects.unlink(object)