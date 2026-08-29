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
        "--input",
        type=Path,
        help="Ubicación de archivo de imagen"
    )
    parser.add_argument(
        "--output",
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
        "--view-layers",
        action="store_true",
        help="Mostrar capas de la red"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar capas de la red"
    )
    parser.add_argument(
        "--images",
        type=lambda s: [item.strip() for item in s.split(",")],
        default=[],
        help="Formatos de imagen"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.55,
        help="Umbral de confianza (ejemplo: 0.25)"
    )
    parser.add_argument(
        "--nms",
        type=float,
        default=0.55,
        help="Umbral de nms (ejemplo: 0.25)"
    )
    args = parser.parse_args()

    # Crear y ejecutar el modelo
    model = Exe.ModelExecutor(args.input)
    model.conf_threshold = args.conf
    model.nms_threshold = args.nms
    extractor = Ext.ModelExtractor(model, args.layers, args.include, args.exclude)
    if args.view_layers:
        extractor.print_info()

    else:
        extractor.extract()
        exporter = Exp.ModelExporter(extractor, args.dry_run, args.images)
        exporter.export(args.output)