import argparse
from pathlib import Path
import ejecucion as Exe
import extractor as Ext
import exportar as Exp

if __name__=="__main__":
    """Funcion main para el componente de extracción. Toma como entrada la ruta de archivo de la entrada de la red.
    Uso: > python ejecucion.py ruta/a/imagen/de/entrada.jpg
    """
    # Argumentos del script
    ## El script toma como argumento una ubicación de archivo de imagen como entrada para la red
    parser = argparse.ArgumentParser(description="Imagen de entrada para la red")
    parser.add_argument(
        "image_path",
        type=Path,
        help="Ubicación de archivo de imagen"
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Directorio de salida",
        nargs="?",
        default=Path("./output")
    )
    parser.add_argument(
        "--layers",
        type=lambda s: [item.strip() for item in s.split(",")],
        default=["Conv2d", "MaxPool2d", "MaxPoolStride1"],
        help="Lista de capas a capturar"
    )
    parser.add_argument(
        "--include",
        type=lambda s: [item.strip() for item in s.split(",")],
        default=[],
        help="Lista de capas a incluir por nombre"
    )
    parser.add_argument(
        "--exclude",
        type=lambda s: [item.strip() for item in s.split(",")],
        default=[],
        help="Lista de capas a excluir por nombre"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Mostrar información de red"
    )
    args = parser.parse_args()

    # Crear y ejecutar el modelo
    model = Exe.ModelExecutor(args.image_path)
    extractor = Ext.ModelExtractor(model, args.layers, args.include, args.exclude)
    if args.info:
        extractor.print_info()

    else:
        extractor.extract()
        exporter = Exp.ModelExporter(extractor)
        exporter.export(args.output_path)