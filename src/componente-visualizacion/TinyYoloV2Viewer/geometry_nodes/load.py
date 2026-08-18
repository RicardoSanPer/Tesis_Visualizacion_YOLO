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