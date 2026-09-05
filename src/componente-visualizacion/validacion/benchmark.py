import subprocess
import csv
import json

from pathlib import Path

INPUT_PATH = Path("./data/output/blender_testing")

PROGRESS_BAR_WIDTH = 50

def progress_bar(count, total):
    """Imprime una barra de progreso dinámica"""
    progress = count / total
    filled = int(progress * PROGRESS_BAR_WIDTH)
    bar = "█" * filled + " " * (PROGRESS_BAR_WIDTH - filled)    

    print(f"\rProgreso: [{bar}] {progress * 100:5.1f}% ({count}/{total})", end="", flush=True)

if __name__ == "__main__":
    # Iterar por los archivos de entrada
    total_items = sum(1 for item in INPUT_PATH.iterdir() if item.is_dir())
    completed_items = 0

    batch_data = {
        "Average Import Runtime": 0.0,
        "Average Geometry Generation Runtime": 0.0,
        "Average Simple Render Runtime": 0.0,
        "Average One Layer Render Runtime": 0.0,
        "Average Two Layers Render Runtime": 0.0,
        "Average Three Layers Render Runtime": 0.0,
        "Average Complex Render Runtime": 0.0,
        "Total Items": total_items,
        "Runs" : {}
    }

    for item in INPUT_PATH.iterdir():
        if not item.is_dir():
            continue

        # Configuracion de entrada y salida
        input_directory = INPUT_PATH / str(item.name)
        cmd = [
            "blender",
            "--background",
            "--python",
            "src/componente-visualizacion/validacion/run.py",
            "--",
            "--input",
            str(input_directory)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        with open(str(input_directory / "blender_headless_benchmark.json"), "r", encoding="utf-8") as jsonfile:
            data = json.load(jsonfile)
            
            batch_data["Average Import Runtime"] += data["Import Runtime"]
            batch_data["Average Geometry Generation Runtime"] += data["Geometry Generation Runtime"]
            batch_data["Average Simple Render Runtime"] += data["Simple Render Runtime"]
            batch_data["Average One Layer Render Runtime"] += data["One Layer Render Runtime"]
            batch_data["Average Two Layers Render Runtime"] += data["Two Layers Render Runtime"]
            batch_data["Average Three Layers Render Runtime"] += data["Three Layers Render Runtime"]
            batch_data["Average Complex Render Runtime"] += data["Complex Render Runtime"]  

            batch_data["Runs"][item.name] = data

        completed_items += 1
        progress_bar(completed_items, total_items)

    batch_data["Average Import Runtime"] /= total_items
    batch_data["Average Geometry Generation Runtime"] /= total_items
    batch_data["Average Simple Render Runtime"] /= total_items
    batch_data["Average One Layer Render Runtime"] /= total_items
    batch_data["Average Two Layers Render Runtime"] /= total_items
    batch_data["Average Three Layers Render Runtime"] /= total_items
    batch_data["Average Complex Render Runtime"] /= total_items

    # Guardar resultados en un archivo JSON
    output_file = INPUT_PATH / "blender_headless_benchmark_batch.json"
    with open(str(output_file), "w", encoding="utf-8") as jsonfile:
        json.dump(batch_data, jsonfile, indent=4)

    print("\nBenchmark completado. Resultados guardados en:", output_file)
    print(f"Avg Import Runtime: {batch_data['Average Import Runtime']:0.4f}")
    print(f"Avg Geometry Generation Runtime: {batch_data['Average Geometry Generation Runtime']:.4f}")
    print(f"Avg Simple Render Runtime: {batch_data['Average Simple Render Runtime']:.4f}")
    print(f"Avg One Layer Render Runtime: {batch_data['Average One Layer Render Runtime']:.4f}")
    print(f"Avg Two Layers Render Runtime: {batch_data['Average Two Layers Render Runtime']:.4f}")
    print(f"Avg Three Layers Render Runtime: {batch_data['Average Three Layers Render Runtime']:.4f}")
    print(f"Avg Complex Render Runtime: {batch_data['Average Complex Render Runtime']:.4f}")