from pathlib import Path

import sys
import bpy
import time
import argparse
import json

import math
from mathutils import Euler, Vector

SAVE_RENDER = False  # Guardar resultado del renderizado como imagen PNG

def run(input_directory: Path):
    """Ejecuta una carga de trabajo, cargando los datos extraidos y renderizando incrementalmente más capas.

    Args:
        input_directory (Path): Directorio con datos de entrada

    Returns:
        dict: Métricas de la ejecución
    """
    # Cargar archivo JSON
    import_start_time = time.perf_counter()
    bpy.ops.import_scene.load_yolov2_json(filepath=str(input_directory / "manifest.json"))
    import_runtime = time.perf_counter() - import_start_time

    # Quitar el cubo predeterminado si existe
    cube = bpy.data.objects.get("Cube")
    if cube:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Generar geometría
    geometry_generation_start_time = time.perf_counter()
    bpy.ops.mesh.create_yolov2_object()
    geometry_generation_runtime = time.perf_counter() - geometry_generation_start_time

    set_camera()
    # Renderizado de calentamiento para evitar el tiempo de inicialización
    warmup()  

    ### Renderizado de geometría simple
    render_runtime_simple = run_render()

    if SAVE_RENDER:
        save_render_result(input_directory, filename="render_output_simple.png")

    # Propiedades de visualización
    scene = bpy.context.scene
    vis_props = scene.yolo_visualization_settings

    # Renderizado de geometría una capa (Solo Conv2d)
    vis_props.layer_properties.get("Conv2d").visibility = False
    vis_props.update_all(bpy.context)

    render_runtime_one_layer = run_render()

    if SAVE_RENDER:
        save_render_result(input_directory, filename="render_output_one_layer.png")

    ### Renderizado de geometria dos capas
    vis_props.layer_properties.get("MaxPool2d").visibility = False
    vis_props.layer_properties.get("MaxPoolStride1").visibility = False
    vis_props.update_all(bpy.context)

    render_runtime_two_layers = run_render()

    if SAVE_RENDER:
        save_render_result(input_directory, filename="render_output_two_layers.png")

    ### Renderizado de geometria tres capas
    vis_props.layer_properties.get("BatchNorm2d").visibility = False
    vis_props.update_all(bpy.context)

    render_runtime_three_layers = run_render()

    if SAVE_RENDER:
        save_render_result(input_directory, filename="render_output_three_layers.png")

    ### Renderizado de geometria completa (cuatro capas)
    for layer in vis_props.layer_properties:
        layer.visibility = False
    vis_props.update_all(bpy.context)

    render_runtime_complex = run_render()

    if SAVE_RENDER:
            save_render_result(input_directory)

    # Guardar resultados en el diccionario
    data = {
        "Import Runtime": import_runtime,
        "Geometry Generation Runtime": geometry_generation_runtime,
        "Simple Render Runtime": render_runtime_simple,
        "One Layer Render Runtime": render_runtime_one_layer,
        "Two Layers Render Runtime": render_runtime_two_layers,
        "Three Layers Render Runtime": render_runtime_three_layers,
        "Complex Render Runtime": render_runtime_complex,
        "Render Engine": scene.render.engine,
        "Input Directory": str(input_directory)
    }

    output_file = input_directory / "blender_headless_benchmark.json"

    with open(str(output_file), "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=4)

    return data

def warmup():
    """Renderizado de prueba para generar shaders y poblar el cache
    """
    scene = bpy.context.scene
    vis_props = scene.yolo_visualization_settings

    for layer in vis_props.layer_properties:
        layer.visibility = False
        vis_props.update_all(bpy.context)
    
    run_render()

    for layer in vis_props.layer_properties:
        layer.visibility = True
        vis_props.update_all(bpy.context)

def run_render():
    """Ejecuta renderizado

    Returns:
        float: tiempo de renderizado en segundos
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    render_start_time = time.perf_counter()
    bpy.ops.render.render(write_still=False)
    render_runtime = time.perf_counter() - render_start_time

    return render_runtime

def set_camera():
    """
    Coloca la cámara para encuadrar todos los objetos de la colección 
    especificada en la vista de renderizado (Perspective).
    """
    scene = bpy.context.scene
    cam = scene.camera

    # Asegurar la existencia de una camara activa, si no existe, crear una nueva
    if not cam:
        cam_data = bpy.data.cameras.new(name="BenchmarkCam")
        cam = bpy.data.objects.new(name="BenchmarkCam", object_data=cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam

    # Posicionar la camara en angulo (isometrico) para ver todos los objetos
    cam.rotation_euler = Euler((math.radians(65), 0.0, math.radians(45)), 'XYZ')
    cam.location = Vector((18, 10, 12))
    cam.data.clip_end = 500
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 46

def save_render_result(output_path: Path, filename: str = "render_output.png"):
    """Guarda los resultados del renserizado más reciente al disco

    Args:
        output_path (Path): Ruta del directorio donde guardar los resultados
    """
    scene = bpy.context.scene
    scene.render.filepath = str(output_path / "render_output.png")
    scene.render.image_settings.file_format = 'PNG'
    render_result = bpy.data.images.get("Render Result")
    if render_result:
        render_result.save_render(filepath=str(output_path / filename), scene=scene)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Datos de la red")
    parser.add_argument(
        "--input",
        type=Path,
        help="Ubicación de directorio de entrada"
    )

    raw_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(raw_args)

    run(args.input)