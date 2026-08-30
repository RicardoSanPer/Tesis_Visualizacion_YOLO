from ejecucion import ModelExecutor
from extractor import ModelExtractor
from exportar import ModelExporter

from pathlib import Path

import time
import sys
import json

INPUT_DIR = Path("./data/images/VOC2007")
OUTPUT_DIR = Path("./data/output/benchmark")
EXECUTION_COUNT = 10

executor = ModelExecutor()
extractor = ModelExtractor(model=executor)
exporter = ModelExporter(extractor=extractor)

def run(input_file: Path, output_dir: Path):
    data = {}

    # Configurar entrada
    executor.input_path = input_file
    executor.configure_input_image()

    # Ejecutar
    starting_time = time.perf_counter()
    extractor.extract()
    exporter.export(output_dir)
    elapsed_time = time.perf_counter() - starting_time

    # Datos
    data["Input File"] = str(input_file)
    data["Output Directory"] = str(output_dir)
    data["Runtime"] = elapsed_time

    # Parametros de la ejecución
    run_params = {}
    run_params["nms"] = executor.nms_threshold
    run_params["confidence"] = executor.conf_threshold
    run_params["layers"] = extractor.capture_layers
    run_params["include"] = extractor.include
    run_params["exclude"] = extractor.exclude
    run_params["formats"] = exporter.formats
    
    data["run parameters"] = run_params
    data["Files"] = {}

    if len(exporter.formats) > 0:
        for ext in exporter.formats:
            data["Files"][ext] = output_tree_info(output_dir / ext)
    else:
        data["Files"]["openvdb"] = output_tree_info(output_dir / "openvdb")
    return data

def output_tree_info(path: Path):
    tree = {}
    tree["Total Size"] = 0
    for item in sorted(path.iterdir()):
        if item.is_dir():
            subtree = output_tree_info(item)
            tree[item.name] = subtree
            tree["Total Size"] += subtree["Total Size"]
        elif item.is_file():
            file_size = item.stat().st_size
            tree[item.name] = file_size
            tree["Total Size"] += file_size
    return tree

def batch_run(batch_count: int = 1, batch_output_path: Path = OUTPUT_DIR):

    # Datos de ejecucion
    batch_data = {}
    batch_data["Runs"] = 0
    batch_data["Min Runtime"] = sys.float_info.max
    batch_data["Max Runtime"] = 0
    batch_data["Avg Runtime"] = 0
    batch_data["Total Runtime"] = 0
    batch_data["items"] = {}

    total_runtime = 0
    count = 0
    
    for item in INPUT_DIR.iterdir():
        if count >= batch_count:
            break
        
        if not item.is_file():
            continue

        # Configuracion de entrada y salida
        input_file = INPUT_DIR / str(item.name)
        output_target = batch_output_path / str(item.stem)
        
        # Ejecutar inferencia
        data = run(input_file, output_target)

        # Datos
        batch_data["Runs"] += 1
        total_runtime += data["Runtime"]

        if data["Runtime"] < batch_data["Min Runtime"]:
            batch_data["Min Runtime"] = data["Runtime"]

        if data["Runtime"] > batch_data["Max Runtime"]:
            batch_data["Max Runtime"] = data["Runtime"]

        batch_data["items"][item.name] = data
        count += 1

    batch_data["Avg Runtime"] = total_runtime / batch_data["Runs"]
    batch_data["Total Runtime"] = total_runtime

    print(f"Batch results in: {batch_output_path}")
    print(f"Avg Runtime: {batch_data["Avg Runtime"]:.4f}s\t| Min: {batch_data["Min Runtime"]:.4f}s\t| Max: {batch_data["Max Runtime"]:.4f}s")

    with open(str(batch_output_path / "batch_results.json"), "w", encoding="utf-8") as file:
        json.dump(batch_data, file, indent=4)


if __name__=="__main__":
    extractor.capture_layers = ["Conv2d"]
    exporter.formats = ["vdb"]
    batch_run(10, OUTPUT_DIR / "batch1")
    

    