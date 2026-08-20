from pathlib import Path
import bpy

def load_geometry_node_group(group_name: str) -> bpy.types.NodeTree:
    """Carga un grupo de nodos de la librería evitando la duplicación de subgrupos."""
    blend_path = (Path(__file__).parent.parent / "assets" / "library.blend").resolve()

    # 1. Retornar si el grupo principal ya está en memoria
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    # 2. Validar existencia del archivo
    if not blend_path.exists():
        raise FileNotFoundError(f"Archivo de assets no existe: {blend_path}")

    # 3. Cargar usando bpy.data.libraries.load
    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
        if group_name not in data_from.node_groups:
            raise KeyError(
                f"Grupo de nodos '{group_name}' no encontrado en {blend_path.name}."
            )
        # Solo solicitamos el grupo requerido
        data_to.node_groups = [group_name]

    # 4. Obtener el grupo cargado
    node_group = bpy.data.node_groups.get(group_name)
    if not node_group:
        raise KeyError(f"Error al obtener el grupo '{group_name}' tras la carga.")

    node_group.use_fake_user = True
    return node_group

def deduplicar_nodos():
    """
    Detecta grupos de nodos duplicados con sufijos (.001, .002, etc.),
    redirige a todos sus usuarios al grupo base original y elimina el duplicado.
    """
    for ng in list(bpy.data.node_groups):
        # Si el nombre termina en .001, .002, etc.
        if len(ng.name) > 4 and ng.name[-4] == '.' and ng.name[-3:].isdigit():
            base_name = ng.name[:-4]
            base_group = bpy.data.node_groups.get(base_name)

            if base_group and base_group != ng:
                # Redirigir todos los nodos internos al grupo original
                ng.user_remap(base_group)
                # Eliminar el bloque de datos duplicado
                bpy.data.node_groups.remove(ng)

def deduplicar_materiales():
    """
    Detecta materiales duplicados (.001, .002, etc.),
    redirige a todos sus usuarios al material base original y elimina el duplicado.
    """
    for mat in list(bpy.data.materials):
        # Si el nombre termina en .001, .002, etc.
        if len(mat.name) > 4 and mat.name[-4] == '.' and mat.name[-3:].isdigit():
            base_name = mat.name[:-4]
            base_mat = bpy.data.materials.get(base_name)

            if base_mat and base_mat != mat:
                # Redirigir al material original
                mat.user_remap(base_mat)
                # Eliminar duplicados
                bpy.data.materials.remove(mat)

def actualizar_imagen_entrada(image_path: str):
    """
    Asigna una imagen al material de entrada como textura
    """
    # Obtener material
    material_name = "YV2 Input Image"
    mat = bpy.data.materials.get(material_name)
    if not mat:
        print(f"No se encontró el material '{material_name}'")
        return None

    mat.use_fake_user = True
    mat.use_nodes = True

    # Cargar imagen
    img_path = Path(image_path).resolve()
    if not img_path.exists():
        print(f"Archivo no encontrado: {img_path}")
        return None

    img = bpy.data.images.load(str(img_path), check_existing=True)
    img.use_fake_user = True

    # Obtener nodo de imagen de textura
    tex_node = mat.node_tree.nodes.get("Image Texture")

    if not tex_node:
        print(f"No se encontró un nodo de imagen de textura apropiado para '{material_name}'.")
        return None

    # Asignar imagen y actualizar
    tex_node.image = img
    mat.update_tag()

    print(f"Actualizada textura de '{mat.name}' a '{img.name}'.")
    return img

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

    obj.update_tag()