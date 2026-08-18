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
        spacing = 5.0
        offset_idx = 0

        # Instanciar geometria de volumenes
        for layer, layer_info in parsed["layers_data"].items():
            if layer in ("input", "cnn"):
                continue

            obj = self._instanciar_nodos(context, "YV2 Volume Viewer", layer)
            if not obj:
                return {'CANCELLED'}

            # Espaciar
            obj.location = (0.0, offset_idx * spacing, 0.0)
            offset_idx += 1
            self._configurar_volume_viewer(obj, layer_info)

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

    def _configurar_volume_viewer(self, obj: bpy.types.Object, layer_info: dict):

        size = (layer_info["dimensions"][2], layer_info["dimensions"][3], layer_info["dimensions"][1]) * 0.01
        params = {
            "Simplified Volume": True,
            "World Size" : size,

        }

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