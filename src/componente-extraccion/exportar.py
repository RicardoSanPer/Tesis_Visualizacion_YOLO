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
    output_path = Path.cwd() / "data" / "output"
    output_data_file = "manifest"
    
    def __init__(self, extractor):
        self.model_extractor = extractor

    def export(self):
        """Exporta los datos extraidos del modelo a JSON y OpenVDB
        """
        self._file_validation(self.output_path)

        with open(str(self.output_path / f"{self.output_data_file}.json"), "w", encoding="utf-8") as file:
            json.dump(self.model_extractor.get_data(), file, indent=4)

        for key in self.model_extractor.layers.keys():
            self._convert_tensor(key)

        self._save_io_images()
        self._convert_boxes()

    def _save_io_images(self):
        """Exporta las imagenes de entrada y salida
        """
        self.model_extractor.input_image.save(str(self.output_path / "input.png"))
        self.model_extractor.output_image.save(str(self.output_path / "output.png"))

    def _convert_boxes(self):
        """Convierte las cajas de salida a formato openvdb
        """
        #Cada caja tiene formato (x, y, w, h, confidence, class probability, class id)
        data = np.array([[[t.item() for t in row] for row in self.model_extractor.boxes]])
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.name = "density"
        openvdb.write(str(self.output_path / "boxes.vdb"), grid)

    def _convert_tensor(self, layer:str):
        """Convierte un tensor a cuadrícula OpenVDB y guarda el archivo

        Args:
            layer (str): nombre de la capa del tensor
        """
        
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
        openvdb.write(str(self.output_path / f"{layer}.vdb"), grid)

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