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
        "Average Render Runtime": 0.0,
        "Average Total Runtime": 0.0,
        "Total Runtime": 0.0,
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

        with open(str(input_directory / "blender_headless_benchmark.csv"), "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                batch_data["Average Import Runtime"] += float(row["Import Runtime"])
                batch_data["Average Geometry Generation Runtime"] += float(row["Geometry Generation Runtime"])
                batch_data["Average Render Runtime"] += float(row["Render Runtime"])
                batch_data["Average Total Runtime"] += float(row["Total Runtime"])
                batch_data["Total Runtime"] += float(row["Total Runtime"])      

            batch_data["Runs"][item.name] = next(reader, {})

        completed_items += 1
        progress_bar(completed_items, total_items)

    batch_data["Average Import Runtime"] /= total_items
    batch_data["Average Geometry Generation Runtime"] /= total_items
    batch_data["Average Render Runtime"] /= total_items
    batch_data["Average Total Runtime"] /= total_items

    # Guardar resultados en un archivo JSON
    output_file = INPUT_PATH / "blender_headless_benchmark_batch.json"
    with open(str(output_file), "w", encoding="utf-8") as jsonfile:
        json.dump(batch_data, jsonfile, indent=4)

    print("\nBenchmark completado. Resultados guardados en:", output_file)
    print(f"Avg Import Runtime: {batch_data['Average Import Runtime']:0.4f}")
    print(f"Avg Geometry Generation Runtime: {batch_data['Average Geometry Generation Runtime']:0.4f}")
    print(f"Avg Render Runtime: {batch_data['Average Render Runtime']:0.4f}")
    print(f"Avg Total Runtime: {batch_data['Average Total Runtime']:0.4f}")