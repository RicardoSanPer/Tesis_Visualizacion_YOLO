from pathlib import Path

import sys
import bpy
import time
import argparse
import csv

import math
from mathutils import Euler, Vector

SAVE_RENDER = False  # Guardar resultado del renderizado como imagen PNG

def run(input_directory: Path):
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

    # Activar visibilidad de todas las capas y actualizar propiedades
    scene = bpy.context.scene
    vis_props = scene.yolo_visualization_settings

    # Deshabilitar visibilidad simple de capas
    for layer in vis_props.layer_properties:
        layer.visibility = False

    vis_props.update_all(bpy.context)

    set_camera()

    # Renderizado
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    render_start_time = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    render_runtime = time.perf_counter() - render_start_time

    if SAVE_RENDER:
        save_render_result(input_directory)

    # Guardar resultados en el diccionario
    data = {
        "Import Runtime": import_runtime,
        "Geometry Generation Runtime": geometry_generation_runtime,
        "Render Runtime": render_runtime,
        "Total Runtime": import_runtime + geometry_generation_runtime + render_runtime,
        "Render Engine": scene.render.engine,
        "Input Directory": str(input_directory)
    }

    fields = ["Import Runtime", "Geometry Generation Runtime", "Render Runtime", "Render Engine", "Total Runtime", "Input Directory"]

    output_file = input_directory / "blender_headless_benchmark.csv"

    with open(str(output_file), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerow(data)

    return data

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
    cam.rotation_euler = Euler((math.radians(75), 0.0, 0.0), 'XYZ')
    cam.location = Vector((0, -3, 8))
    cam.data.clip_end = 500
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 42

def save_render_result(output_path):
    scene = bpy.context.scene
    scene.render.filepath = str(output_path / "render_output.png")
    scene.render.image_settings.file_format = 'PNG'
    render_result = bpy.data.images.get("Render Result")
    if render_result:
        render_result.save_render(filepath=str(output_path / "render_output.png"), scene=scene)

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