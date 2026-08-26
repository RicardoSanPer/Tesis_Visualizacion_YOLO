import extractor
from pathlib import Path
import numpy as np
import openvdb
import json

class ModelExporter:
    """_summary_

    Raises:
        ValueError: Cuando la ruta de destino está vacía
        NotADirectoryError: Si la ruta de destuno es de un archivo y no un directorio
    """
    
    def __init__(self, extractor, dry_run = False):
        self.model_extractor = extractor
        self.dry_run = dry_run

    def export(self, output_path: Path):
        """Exporta los datos extraidos del modelo a JSON y OpenVDB

        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        self._file_validation(output_path)

        print(f"Guardando datos en: {output_path}\n")

        manifest_file = str(output_path / f"manifest.json")
        print(f"Manifesto: {manifest_file}\n")

        if not self.dry_run:
            with open(manifest_file, "w", encoding="utf-8") as file:
                json.dump(self.model_extractor.get_data(), file, indent=4)

        for key in self.model_extractor.layers.keys():
            self._convert_tensor(key, output_path)
        print()

        self._save_io_images(output_path)
        self._convert_boxes(output_path)

    def _save_io_images(self, output_path: Path):
        """Exporta las imagenes de entrada y salida
        
        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        in_file = str(output_path / "input.png")
        out_file = str(output_path / "output.png")
        
        print(f"Imagen de entrada: {in_file}")
        print(f"Imagen de salida: {out_file}")

        if self.dry_run: return

        self.model_extractor.input_image.save(in_file)
        self.model_extractor.output_image.save(out_file)

    def _convert_boxes(self, output_path: Path):
        """Convierte las cajas de salida a formato openvdb
        
        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        file_path = str(output_path / "boxes.vdb")
        print(f"Cajas: {file_path}\n")

        #Cada caja tiene formato (x, y, w, h, confidence, class probability, class id)
        data = np.array([[[t.item() for t in row] for row in self.model_extractor.boxes]])
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.name = "density"

        if self.dry_run: return
        
        openvdb.write(file_path, grid)

    def _convert_tensor(self, layer:str, output_path: Path):
        """Convierte un tensor a cuadrícula OpenVDB y guarda el archivo

        Args:
            layer (str): nombre de la capa del tensor
            output_path (Path) : Ruta de directorio de salida
        """

        file_path = str(output_path / f"{layer}.vdb")
        print(f"{layer}: {file_path}")
        
        # Convertir tensores a arreglo de numpy
        data = self.model_extractor.layers[layer].numpy()
        data = data.astype("float32")
        # Eliminar la dimensión extra
        data = data.squeeze()

        #Convertir a OpenVDB
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.transform = openvdb.createLinearTransform(voxelSize=0.1)
        grid.name = "density"

        if self.dry_run: return

        openvdb.write(file_path, grid)

    def _file_validation(self, path: Path):
            """Valida la ruta de directorio para guardar los datos extraidos.
    
            Args:
                path (Path): Ruta de directorio
    
            Raises:
                ValueError: Si no se proporciona una ruta válida.
                NotADirectoryError: Si se proporciona una ruta de archivo en vez de directorio
    
            Returns:
                Path: ruta de archivo
            """
            if not path:
                raise ValueError("No se ingresó ningun archivo.")
            if path.is_file():
                raise NotADirectoryError(f"Esperado un directorio, es archivo: {path}")
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            return path