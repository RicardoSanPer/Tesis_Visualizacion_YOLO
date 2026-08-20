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
        yolo_vis = context.scene.yolo_visualization_settings
        parsed = yolo_data.get_parsed_json()

        if "layers_data" not in parsed:
            self.report({'ERROR'}, "No se encontró datos de capas")
            return {'CANCELLED'}

        # Espaciado
        offset_idx = 0

        path = context.scene.yolo_settings.get_manifest_location()

        #
        # Instanciar geometria de volumenes
        #
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
            self._configurar_volume_viewer(obj, layer, path, layer_info, context)
            yolo_vis.add_layer(layer, obj)

        #
        # Instancias cajas de salida
        #
        salida = self._instanciar_nodos(context, "YV2 Box Viewer", "boxes")
        if not obj:
            return {'CANCELLED'}
        
        salida.location = (0.0, offset_idx, 0.0)
        self._configurar_box_viewer(salida, "boxes", path, parsed)

        #
        # Instanciar conexiones
        #

        for layer, layer_info in parsed["layers_data"].items():
            if layer in ("input", "cnn"):
                continue
            count = 0
            for child in layer_info["connections"]:
                con = self._instanciar_nodos(context, "YV2 Volume Connection", layer + str(count))
                if not con:
                    return {'CANCELLED'}
                child_layer_info = parsed["layers_data"][child]
                self._configurar_conexiones(con, layer, child, child_layer_info, context)
                count += 1

        load.deduplicar_nodos()
        load.deduplicar_materiales()
        load.actualizar_imagen_entrada(str(path / "input.png"))
        
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

            #node_group.interface_update(context)

            return obj

        except Exception as e:
            self.report({'ERROR'}, f"Failed to instantiate: {e}")
            return None

    def _configurar_volume_viewer(self, obj: bpy.types.Object, layer_name: str, directory: Path, layer_info: dict, context):
        vis_props = context.scene.yolo_visualization_settings
        size_factor = vis_props.size_scale

        resolution = layer_info["dimensions"][2]*size_factor
        depth = layer_info["dimensions"][1]*size_factor
        size = (resolution, resolution, 0.05)
        params = {
            "Simplified Volume": True,
            "World Size" : size,
            "Color" : vis_props.get_layer_color(layer_info.get("type")),
            "Resolution" : layer_info["dimensions"][2],
            "Slice Count" : layer_info["dimensions"][1]
        }

        if layer_info["data"]:
            file = directory / f"{layer_name}.vdb"
            params["Volume File"] = str(file)
            params["World Size"] = (resolution, resolution, depth)

        load.configurar_parametros_nodo(obj, "Geometry Nodes", params)

    def _configurar_box_viewer(self, obj: bpy.types.Object, layer_name: str, directory: Path, config: dict):
        file = directory / "boxes.vdb"
        params = {
                "Box File" : str(file),
                "Box Count" : config["n_boxes"],
                "Class Labels" : config["classes"],
                "Confidence" : config["confidence"]
            }

        load.configurar_parametros_nodo(obj, "Geometry Nodes", params)

    def _configurar_conexiones(self, obj: bpy.types.Object, parent:str, child:str, layer_info: dict, context):
        yolo_vis = context.scene.yolo_visualization_settings
        parent_obj = yolo_vis.get_layer(parent)
        child_obj = yolo_vis.get_layer(child)
        kernel_size = 1
        stride = 1
        ceil_mode = False

        if layer_info.get("kernel_size"):
            value = layer_info["kernel_size"]
            if isinstance(value, list):
                kernel_size = value[0]
            else:
                kernel_size = value

        if layer_info.get("stride"):
            value = layer_info["stride"]
            if isinstance(value, list):
                stride = value[0]
            else:
                stride = value

        if layer_info.get("ceiling"):
            ceil_mode = layer_info["ceiling"]

        params = {
            "Input Layer": parent_obj,
            "Output Layer": child_obj,
            "Kernel Size": kernel_size,
            "Stride": stride,
            "Ceiling Mode": ceil_mode
        }

        load.configurar_parametros_nodo(obj, "Geometry Nodes", params)



