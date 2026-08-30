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
        "--no-io",
        action="store_true",
        help="Omitir extracción de imagenes de entrada y salida"
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
        "--info",
        action="store_true",
        help="Mostrar información de archivos de salida"
    )
    parser.add_argument(
        "--formats",
        type=lambda s: [item.strip() for item in s.split(",")],
        default=["vdb"],
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
    extractor = Ext.ModelExtractor(model)

    # Parametros modelos
    model.conf_threshold = args.conf
    model.nms_threshold = args.nms

    #Parametros extraccion
    extractor.capture_layers = args.layers
    extractor.include = args.include
    extractor.exclude = args.exclude

    if args.view_layers:
        extractor.print_info()

    else:
        extractor.extract()
        exporter = Exp.ModelExporter(extractor)

        # Parametros exportacion
        exporter.dry_run = args.dry_run
        exporter.info = args.info
        exporter.formats = args.formats

        exporter.export(args.output)