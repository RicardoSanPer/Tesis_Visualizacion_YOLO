import bpy
from pathlib import Path
from bpy.types import Operator
from ..geometry_nodes import load
from ..properties.graph_properties import LayerItem
from ..properties.visualization_properties import actualizar_dimensiones

class MESH_OT_CreateGeoNodesObject(Operator):
    """Generar geometría de la red"""
    bl_idname = "mesh.create_geonodes_object"
    bl_label = "Generar visualización de red"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        root_collection = scene.collection

        yolo_collection = self.get_or_create_scene_collection("YOLOv2", root_collection)

        yolo_data = scene.yolo_settings
        yolo_graph = scene.yolo_graph
        parsed = yolo_data.get_parsed_json()

        if "layers_data" not in parsed:
            self.report({'ERROR'}, "No se encontró datos de capas")
            return {'CANCELLED'}

        path = context.scene.yolo_settings.get_manifest_location()

        # Cargar informacion de las capas
        for layer, layer_info in parsed.get("layers_data").items():
            # Omitir entrada y raíz
            if layer in ("input", "cnn"):
                continue

            obj = self._instanciar_nodos("YV2 Volume Viewer", layer, context)
            if not obj:
                return {'CANCELLED'}

            ## Grafo
            item = yolo_graph.add_layer(layer, layer_info.get("type", "unknown"), obj)
            self.parametros_capa(item, path, layer_info)
            self.configurar_volume_viewer_objects(item)
            yolo_graph.set_graph_node_children(item, layer_info["connections"])

            #Coleccion
            node_collection = self.get_or_create_scene_collection(layer_info.get("type"), yolo_collection)
            self.assign_object_to_collection(obj, node_collection)

        # Instancias cajas de salida
        salida = self._instanciar_nodos("YV2 Box Viewer", "boxes", context)
        if not salida:
            return {'CANCELLED'}
        
        self.configurar_box_viewer(salida, path, parsed)
        yolo_graph.boxes = salida

        io_collection = self.get_or_create_scene_collection("IO", yolo_collection)
        self.assign_object_to_collection(salida, io_collection)

        # Instanciar geometria de conexiones
        connection_collection = self.get_or_create_scene_collection("Connections", yolo_collection)

        for node in yolo_graph.layers:
            for child in node.children:
                con = self._instanciar_nodos("YV2 Volume Connection", f"{node.name}_{child.value}_CONN", context)
                if not con:
                    return {'CANCELLED'}

                parent_node = yolo_graph.layers.get(node.name)
                child_node = yolo_graph.layers.get(child.value)
                self.configurar_conexiones(con, parent_node, child_node)
                self.assign_object_to_collection(con, connection_collection)


        load.deduplicar_nodos()
        load.deduplicar_materiales()
        load.actualizar_imagen_entrada(str(path / "input.png"))

        actualizar_dimensiones(self, context)
        
        self.report({'INFO'}, "Creada red")
        return {'FINISHED'}

    def _instanciar_nodos(self, group_name: str, name: str, context):
        """Genera un objeto y asigna un grupo de nodos de geometría

        Args:
            group_name (str): Nombre del grupo de nodos
            name (str): Nombre del objeto
            context (_type_): Contexto

        Returns:
            _type_: Objeto con nodos
        """
        try:
            # 1. Cargar grupo de nodos
            node_group = load.load_geometry_node_group(group_name)
            if not node_group:
                self.report({'ERROR'}, f"No se pudo cargar el grupo '{group_name}'")
                return None

            # 2. Crear objeto y asignar ubicación
            mesh_data = bpy.data.meshes.new(name=f"{name}_Mesh")
            obj = bpy.data.objects.new(name=name, object_data=mesh_data)

            # 3. Vincular a la colección
            context.collection.objects.link(obj)

            # 4. Modificador Geometry Nodes
            modifier = obj.modifiers.new(name="Geometry Nodes", type='NODES')
            modifier.node_group = node_group

            return obj

        except Exception as e:
            self.report({'ERROR'}, f"Failed to instantiate: {e}")
            return None

    def configurar_volume_viewer_objects(self, node: LayerItem):
        """Configura los parametros del grupo de nodos de visualización de volúmenes
        para visualizar una capa de la red

        Args:
            node (LayerItem): LayerItem con los datos de la capa/volymen
        """
        params = {
            "World Size": node.dimensions,
            "Resolution": node.resolution,
            "Slice Count": node.slice_count,
            "Volume File": node.file,
            "Simplified Volume": True
        }
        load.configurar_parametros_nodo(node.object, "Geometry Nodes", params)

    def configurar_box_viewer(self, obj: bpy.types.Object, directory: Path, config: dict):
        """Configura los parametros del grupo de nodos para la visualizacipn de las cajas

        Args:
            obj (bpy.types.Object): Objeto con grupo de nodos de visualización de cajas
            directory (Path): Ruta de directorio del manifesto
            config (dict): Datos
        """
        file = directory / "boxes.vdb"
        params = {
                "Box File" : str(file),
                "Box Count" : config["n_boxes"],
                "Class Labels" : config["classes"],
                "Confidence" : config["confidence"]
            }
        load.configurar_parametros_nodo(obj, "Geometry Nodes", params)

    def configurar_conexiones(self, connection:bpy.types.Object, parent: LayerItem, child: LayerItem):
        """Configura los parametros del grupo de nodos para la visualización de una conexión entre
        dos capas

        Args:
            connection (bpy.types.Object): Objeto con el grupo de nodos de visualización de conexión
            parent (LayerItem): LayerItem con el padre
            child (LayerItem): LayerItem con el hijo
        """
        params = {
            "Input Layer": parent.object,
            "Output Layer": child.object,
            "Kernel Size": child.kernel_size,
            "Stride": child.stride,
            "Ceiling Mode": child.ceiling
        }
        load.configurar_parametros_nodo(connection, "Geometry Nodes", params)

    def parametros_capa(self, nodo: LayerItem, path: Path, datos: dict):
        """Configura LayerItem con los datos de la capa correspondiente

        Args:
            nodo (LayerItem): LayerItem
            path (Path): Ruta de directorio del manifesto
            datos (dict): Datos de la capa
        """
        #Kernel
        if datos.get("kernel_size"):
            kernel_size = datos["kernel_size"]
            if isinstance(kernel_size, list):
                kernel_size = kernel_size[0]
            elif isinstance(kernel_size, int):
                kernel_size = kernel_size
            nodo.kernel_size = kernel_size
        # Stride
        if datos.get("stride"):
            stride = datos["stride"]
            if isinstance(stride, list):
                stride = stride[0]
            elif isinstance(stride, int):
                stride = stride
            nodo.stride = stride
        # Ceiling
        if datos.get("ceiling"):
            nodo.ceiling = datos["ceiling"]
        #Dimensiones
        if datos.get("dimensions"):
            dim = datos["dimensions"]

            nodo.dimensions = (dim[2], dim[3], dim[1])
            nodo.resolution = dim[2]
            
            # Dato del volumen
            if datos.get("data"):
                nodo.slice_count = dim[1]
                nodo.file = str(path / f"{nodo.name}.vdb")

    def get_or_create_scene_collection(self, name: str, parent: bpy.types.Collection = None):
        """
        Obtiene o crea una colección
        """
        # Si la colección ya existe
        col = bpy.data.collections.get(name)
        if not col:
            col = bpy.data.collections.new(name)

        # Determinar coleccion padre
        parent_col = parent if parent is not None else bpy.context.scene.collection

        # Vincular a la jerarquia
        if col.name not in parent_col.children:
            parent_col.children.link(col)

        return col

    def assign_object_to_collection(self, obj: bpy.types.Object, target_col: bpy.types.Collection):
        """
        Asigna un objeto a una coleccion
        """
        if not obj or not target_col:
            return

        # Vincular a coleccion
        if obj.name not in target_col.objects:
            target_col.objects.link(obj)

        # Quitar de otras colecciones como default
        for col in list(obj.users_collection):
            if col != target_col:
                col.objects.unlink(obj)