from ejecucion import ModelExecutor
from extractor import ModelExtractor
from exportar import ModelExporter

from pathlib import Path
from PIL import Image

import time
import json
import gc
import numpy as np

INPUT_DIR = Path("./data/images/VOC2007")
OUTPUT_DIR = Path("./data/output/benchmark")
CAPTURE_LAYERS = ["Conv2d"]
EXECUTION_COUNT = 100
FORMAT = "vdb"

PROGRESS_BAR_WIDTH  = 50

executor = ModelExecutor()
extractor = ModelExtractor(model=executor)
exporter = ModelExporter(extractor=extractor)

def progress_bar(count, total):
    """Imprime una barra de progreso dinámica"""
    progress = count / total
    filled = int(progress * PROGRESS_BAR_WIDTH)
    bar = "█" * filled + " " * (PROGRESS_BAR_WIDTH - filled)    

    print(f"\rProgreso: [{bar}] {progress * 100:5.1f}% ({count}/{total})", end="", flush=True)

def run(input_file: Path, output_dir: Path):
    """Ejecución de inferencia, extracción y exportación de datos. Captura métricas como
    parámetros de ejecución, tiempo de ejecución (solo de inferencia, extracción y exportación),
    tamaño en disco de archivos generados y error de presición entre los datos exportados y los
    originales.

    Args:
        input_file (Path): Imagen de entrada de la red
        output_dir (Path): Directorio de salida de archivos generados por la exportación

    Returns:
        dict: Métricas capturadas
    """

    # Configurar entrada
    executor.input_path = input_file
    executor.configure_input_image()

    # Ejecutar
    starting_time = time.perf_counter()
    extractor.extract()
    exporter.export(output_dir)
    elapsed_time = time.perf_counter() - starting_time

    # Datos    
    run_params = {
        "nms": executor.nms_threshold,
        "confidence": executor.conf_threshold,
        "layers": extractor.capture_layers,
        "include": extractor.include,
        "exclude": extractor.exclude,
        "formats": exporter.formats
    }

    data ={
        "Input File" : str(input_file),
        "Output Directory" : str(output_dir),
        "Runtime" : elapsed_time,
        "Total Filesize" : 0,
        "Total Filecount" : 0,
        "Run parameters" : run_params,
        "Presicion Error" : {},
        "Files" : {}
    }

    # Parametros de la ejecución

    for ext in exporter.formats:
        path = output_dir / ext
        path.mkdir(parents=True, exist_ok=True)

        # Metricas de archivos por tipo de extensión generado
        data["Files"][ext] = output_tree_info(path)
        # Métricas totales de archivo por ejecución
        data["Total Filesize"] += data["Files"][ext]["Total Size"]
        data["Total Filecount"] += data["Files"][ext]["File Count"]
        # Error de presición agrupado por extension de archivo
        data["Presicion Error"][ext] = calculate_presition_loss(ext)

    # Limpieza entre ejecuciones
    executor.clear()
    extractor.clear()
    gc.collect()

    return data

def output_tree_info(path: Path):
    """Obtiene la información de archivos generados (cuenta da archivos y tamaño en disco).
    'Total Size': Tamaño total en disco del directorio, incluyendo subdirectorios
    'File Count': Cuenta total de archivos en el directorio, incluyendo archivos en
    subdirectorios
    'Directorio/Archivo': Datos de los datos del subdirectorio, o tamaño si es un archivo

    Args:
        path (Path): Directorio a examinar

    Returns:
        dict: Información ("Total Size", "File Count", datos de subarboles)
    """
    tree = {
        "Total Size": 0,
        "File Count": 0
    }
    # Iterar
    for item in sorted(path.iterdir()):
        # Recursión de directorios
        if item.is_dir():
            subtree = output_tree_info(item)
            tree[item.name] = subtree
            tree["Total Size"] += subtree["Total Size"]
            tree["File Count"] += subtree["File Count"]
        # Tamaño de archivo
        elif item.is_file():
            file_size = item.stat().st_size
            tree[item.name] = file_size
            tree["Total Size"] += file_size
            tree["File Count"] += 1
    return tree

def calculate_presition_loss(ext: str):
    """Calcula la perdida de presición de las capas por tipo de archivo
    'Avg': Media total de todas las capa
    'Min': Error minimo hallado en las capas
    'Max': Error máximo hallado en las capas
    'Layers': Perdida especpifica por capa, indecado por nombre de capa

    Args:
        output_dir (Path): directorio de archivos, incluyendo directorio de extensión (IE root/jpg)
        ext (str): extensión de archivo a comparar

    Returns:
        dict: diccionario con la información de perdida de presición ('Avg', 'Min', 'Max', 'Layers')
    """
    layer_data = {}

    total = 0

    count = 0
    min_value = float("inf")
    max_value = 0

    # Perdida por capa
    for name in extractor.layers.keys():
        # Reconstruye los datos del formato exportado a arreglo de numpy32
        data = exporter.get_exported_volume_as_numpy32(name, ext)
        volume = np.stack(data, axis=0)

        tensor = extractor.layers[name].numpy().astype("float32").squeeze()
        mae = np.mean(np.abs(tensor - volume))

        if mae < min_value: min_value = mae
        if mae > max_value: max_value = mae

        layer_data[name] = mae
        total += mae
        count += 1

    # MAE de toda la ejecucion por extension de archivo
    presicion_data = {
        "Avg": total / count if count > 0 else 0,
        "Min": min_value,
        "Max": max_value,
        "Layers": layer_data
    }
    return presicion_data


def batch_run(batch_count: int = 1, batch_output_path: Path = OUTPUT_DIR):
    """Ejecución por lotes de inferencias para capturar métricas.

    Args:
        batch_count (int, optional): Número de inferencias a realizar. Defaults to 1.
        batch_output_path (Path, optional): Directorio de salida para los datos
        generados en lote. Defaults to OUTPUT_DIR.

    Returns:
        dict: metricas de la ejecución por lotes
    """
    # Datos de ejecucion
    batch_data = {
        "Runs": 0,
        "Min Runtime": float("inf"),
        "Max Runtime": 0,
        "Avg Runtime": 0,
        "Total Runtime": 0,
        "Total Filesize": 0,
        "Total Filecount": 0,
        "Avg Filesize": 0,
        "MEA" : {},
        "items" : {}
    }

    count = 0

    # Warm up
    print("Warming up")
    for item in INPUT_DIR.iterdir():
        if count >= 5:
            break
        
        exporter.dry_run = True
        
        input_file = INPUT_DIR / str(item.name)
        output_target = batch_output_path / str(item.stem)

        run(input_file, output_target)
        count += 1

    count = 0
    exporter.dry_run = False

    # Iteracion por archivos de entrada
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
        batch_data["Total Runtime"] += data["Runtime"]
        batch_data["Total Filesize"] += data["Total Filesize"]
        batch_data["Total Filecount"] += data["Total Filecount"]

        # Datos generales
        ## Runtime
        if data["Runtime"] < batch_data["Min Runtime"]:
            batch_data["Min Runtime"] = data["Runtime"]

        if data["Runtime"] > batch_data["Max Runtime"]:
            batch_data["Max Runtime"] = data["Runtime"]

        ## Error de presicion
        for key in data["Presicion Error"].keys():
            if not batch_data["MEA"].get(key):
                batch_data["MEA"][key] = 0
            batch_data["MEA"][key] += data["Presicion Error"][key]["Avg"]

        batch_data["items"][item.name] = data
        
        count += 1
        progress_bar(count, batch_count)

    # Metricas
    batch_data["Avg Runtime"] = batch_data["Total Runtime"] / batch_data["Runs"]
    batch_data["Avg Filesize"] = batch_data["Total Filesize"] / batch_data["Runs"]

    total_mib = batch_data["Total Filesize"] / (1024 * 1024)
    avg_mib = batch_data["Avg Filesize"] / (1024 * 1024)

    # Imprimir resultados
    print("\n")
    print(f"Batch results in: {batch_output_path}")
    print(f"Extraction Runtime: {batch_data["Total Runtime"]:.4f}s\t| Avg: {batch_data["Avg Runtime"]:.4f}s\t| Min: {batch_data["Min Runtime"]:.4f}s\t| Max: {batch_data["Max Runtime"]:.4f}s")
    print(f"Total File Count: {batch_data['Total Filecount']}\t| Per run: {batch_data['Total Filecount']/batch_count:.0f}")
    print(f"Total Filesize: {total_mib:.0f} MiB\t| Avg: {avg_mib:.0f} MiB\t\n")

    for key in batch_data["MEA"].keys():
        batch_data["MEA"][key] = batch_data["MEA"][key] / batch_count
        print(f"{key} Avg MEA: {batch_data["MEA"][key]}")
    # Guardar resultados
    with open(str(batch_output_path / "batch_results.json"), "w", encoding="utf-8") as file:
        json.dump(batch_data, file, indent=4, default=float)

    return batch_data


if __name__=="__main__":
    extractor.capture_layers = CAPTURE_LAYERS

    # Ejecucion
    print("========= Extracción ===========")
    exporter.formats = [FORMAT]
    batch_run(EXECUTION_COUNT, OUTPUT_DIR / f"batch_{FORMAT}")

    print("Datos de salida guardados en:", OUTPUT_DIR / f"batch_{FORMAT}/batch_results.json")