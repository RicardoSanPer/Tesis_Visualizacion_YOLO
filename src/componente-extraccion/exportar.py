import extractor
from pathlib import Path
import openvdb
import json

class ModelExporter:
    output_path = Path.cwd() / "data" / "output"
    output_data_file = "manifest"
    transform_matrix = [
        [1.0,   0.0,   0.0, 0.0],
        [0.0,   0.0,  -1.0, 0.0],  # Inverted Y-to-Z mapping to un-flip vertical axis
        [0.0,  -1.0,   0.0, 0.0],  # Z moves to -Y
        [0.0,   0.0,   0.0, 1.0]
    ]
    def __init__(self, extractor):
        self.model_extractor = extractor

    def export(self):
        self._file_validation(self.output_path)

        with open(str(self.output_path / f"{self.output_data_file}.json"), "w", encoding="utf-8") as file:
            json.dump(self.model_extractor.layers_data, file, indent=4)

        for key in self.model_extractor.layers.keys():
            self._convert_tensor(key)

        self._save_io_images()
        #self._convert_boxes()

    def _save_io_images(self):
        self.model_extractor.input_image.save(str(self.output_path / "input.png"))
        self.model_extractor.output_image.save(str(self.output_path / "output.png"))

    def _convert_boxes(self, box):
        pass

    def _convert_tensor(self, layer):
        # Convertir tensores a arreglo de numpy
        data = self.model_extractor.layers[layer].numpy()
        data = data.astype("float32")
        # Eliminar la dimensión extra
        data = data.squeeze()

        #Convertir a OpenVDB
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.transform = openvdb.createLinearTransform(matrix=self.transform_matrix)
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