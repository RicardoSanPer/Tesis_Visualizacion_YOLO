import argparse
from pathlib import Path
import ejecucion as Exe
import extractor as Ext

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
    args = parser.parse_args()
    # Crear y ejecutar el modelo
    model = Exe.ModelExecutor(args.image_path)
    extractor = Ext.ModelExtractor(model)
    model.execute()
    print(extractor.layers_data)
