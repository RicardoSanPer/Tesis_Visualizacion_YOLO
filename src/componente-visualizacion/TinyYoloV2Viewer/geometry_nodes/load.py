from pathlib import Path
import bpy

def load_geometry_node_group(group_name):
    """Función para cargar y obtener un grupo de nodos de la libreria.

    Args:
        group_name (str): Nombre del grupo de nodos.

    Raises:
        FileNotFoundError: Si no se encuentra el archivo library.blend.
        KeyError: Si no se encuentra el grupo de nodos solicitado.

    Returns:
        _type_: Grupo de nodos
    """
    blend_path = (Path(__file__).parent.parent    / "assets" / "library.blend").resolve()

    # Verificar si se cargó anteriormente
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    # Verificar que existe el archivo libreria
    if not blend_path.exists():
        raise FileNotFoundError(f"Archivo de assets no existe: {blend_path}")

    # Importar bloque de datos, específicamente de grupos de nodos
    inner_dir = str(blend_path / "NodeTree") + "\\"
    bpy.ops.wm.append(
        filepath=str(blend_path / "NodeTree" / group_name), # Path del asset/grupo de nodos
        directory=inner_dir,    # Categoria de TreeNode
        filename=group_name,    # Bloque de dato específico (nombre del grupo de nodos)
        link=False,             # Copia el nodo en vez de vincular
        autoselect=False,       # Evita cambiar la vista del editor
        active_collection=False
    )

    # Obtener grupo de nodos y prevenir purgacion
    node_group = bpy.data.node_groups.get(group_name)
    if not node_group:
        raise KeyError(
            f"Grupo de nodos '{group_name}' no pudo ser cargado. "
            f"Verifica el nombre en {blend_path.name}."
        )

    node_group.use_fake_user = True
    return node_group

def configurar_parametros_nodo(obj: bpy.types.Object, modifier_name: str, parameters: dict):
    if not obj or not parameters:
        return

    # Obtener modificador
    modifier = obj.modifiers.get(modifier_name)
    if not modifier or modifier.type != 'NODES' or not modifier.node_group:
        print(f"Modificador '{modifier_name}' no encontrado en {obj.name}")
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
            print(f"Socket '{param_name}' no existe en '{node_group.name}'")
            continue

        socket_id = socket_name_to_id[param_name]

        try:
            getattr(modifier.properties.inputs, socket_id).value = param_value
        except Exception as e:
            print(f"Falló asignar '{param_name}' ({socket_id}) = {param_value}: {e}")