import bpy
from pathlib import Path
from bpy.types import Operator
from ..geometry_nodes import load

class MESH_OT_CreateGeoNodesObject(Operator):
    """Create an empty mesh and attach a Geometry Nodes modifier"""
    bl_idname = "mesh.create_geonodes_object"
    bl_label = "Create GeoNodes Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        yolo_data = context.scene.yolo_settings
        parsed = yolo_data.get_parsed_json()

        if "layers_data" not in parsed:
            self.report({'ERROR'}, "No se encontró datos de capas")
            return {'CANCELLED'}

        # Espaciado
        offset_idx = 0

        path = Path(context.scene.yolo_settings.filepath).parent

        # Instanciar geometria de volumenes
        for layer, layer_info in parsed["layers_data"].items():
            if layer in ("input", "cnn"):
                continue

            obj = self._instanciar_nodos(context, "YV2 Volume Viewer", layer)
            if not obj:
                return {'CANCELLED'}

            # Espaciar
            depth = layer_info["dimensions"][1] * 0.01
            obj.location = (0.0, offset_idx , 0.0)
            if layer_info["data"]:
                offset_idx += depth  + 0.5
            else:
                offset_idx += 0.5
            self._configurar_volume_viewer(obj, layer, path, layer_info)

        self.report({'INFO'}, "Creada red")
        return {'FINISHED'}

    def _instanciar_nodos(self, context, group_name: str, name: str):
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

            node_group.interface_update(context)

            return obj

        except Exception as e:
            self.report({'ERROR'}, f"Failed to instantiate: {e}")
            return None

    def _configurar_volume_viewer(self, obj: bpy.types.Object, layer_name: str, directory: Path, layer_info: dict):

        colors = {
            "Conv2d" : (38/255, 31/255, 255/255, 1),           #"#261fff",
            "BatchNorm2d" : (31/255, 255/255, 150/255, 1),     #"#1fff96",
            "LeakyReLU" : (255/255, 31/255, 135/255, 1),       #"#ff1f87",
            "MaxPool2d" : (248/255, 255/255, 31/255, 1),       #"#f8ff1f"
            "MaxPoolStride1" : (248/255, 255/255, 31/255, 1)
        }

        size_factor = 0.01
        resolution = layer_info["dimensions"][2]*size_factor
        depth = layer_info["dimensions"][1]*size_factor
        size = (resolution, resolution, 0.05)
        params = {
            "Simplified Volume": True,
            "World Size" : size,
            "Color" : colors[layer_info.get("type")]

        }

        if layer_info["data"]:
            file = directory / f"{layer_name}.vdb"
            params["Resolution"] = layer_info["dimensions"][2]
            params["Slice Count"] = layer_info["dimensions"][1]
            params["Volume File"] = str(file)
            params["World Size"] = (resolution, resolution, depth)

        self._configurar_parametros_nodo(obj, "Geometry Nodes", params)

    def _configurar_parametros_nodo(self, obj: bpy.types.Object, modifier_name: str, parameters: dict):
        if not obj or not parameters:
            return

        modifier = obj.modifiers.get(modifier_name)
        if not modifier or modifier.type != 'NODES' or not modifier.node_group:
            print(f"[Warning] Modificador '{modifier_name}' no encontrado en {obj.name}")
            return

        node_group = modifier.node_group

        # Mapeo de identificador de propiedad a numero de socket
        socket_name_to_id = {
            item.name: item.identifier
            for item in node_group.interface.items_tree
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
        }

        # Asignar valor a parametros
        for param_name, param_value in parameters.items():
            if param_name not in socket_name_to_id:
                print(f"[Warning] Socket '{param_name}' no existe en '{node_group.name}'")
                continue

            socket_id = socket_name_to_id[param_name]

            try:
                getattr(modifier.properties.inputs, socket_id).value = param_value
            except Exception as e:
                print(f"[Error] Falló asignar '{param_name}' ({socket_id}) = {param_value}: {e}")

    def _get_layer_color(layer_type: str):
        pass