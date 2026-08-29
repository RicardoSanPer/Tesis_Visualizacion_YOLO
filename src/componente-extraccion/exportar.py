import extractor
from pathlib import Path
from utils import directory_validation
import torch
from PIL import Image
import numpy as np
import openvdb
import json

class ModelExporter:
    """_summary_

    Raises:
        ValueError: Cuando la ruta de destino está vacía
        NotADirectoryError: Si la ruta de destuno es de un archivo y no un directorio
    """
    
    def __init__(self, extractor, dry_run = False, extensions = []):
        self.model_extractor = extractor
        self.dry_run = dry_run
        self.image_extensions = extensions

    def export(self, output_path: Path):
        """Exporta los datos extraidos del modelo a JSON y OpenVDB

        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        directory_validation(output_path)

        print(f"Guardando datos en: {output_path}\n")

        manifest_file = str(output_path / f"manifest.json")
        print(f"Manifesto: {manifest_file}\n")

        if not self.dry_run:
            with open(manifest_file, "w", encoding="utf-8") as file:
                json.dump(self.model_extractor.get_data(), file, indent=4)

        for key in self.model_extractor.layers.keys():
            if len(self.image_extensions) == 0:
                self._convert_tensor(key, output_path)
            else:
                self._tensor_to_image(key, output_path)

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

        #Cada caja tiene formato (x, y, w, h, confidence, class probability, class id)
        data = np.array([[[t.item() for t in row] for row in self.model_extractor.boxes]])

        if data.ndim < 3:
            print("No se detectó ningun objeto. Omitiendo creacion de cajas")
            return

        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.name = "density"

        print(f"Cajas: {file_path}\n")
        if self.dry_run: return
        
        openvdb.write(file_path, grid)

    def _convert_tensor(self, layer:str, output_path: Path):
        """Convierte un tensor a cuadrícula OpenVDB y guarda el archivo

        Args:
            layer (str): nombre de la capa del tensor
            output_path (Path) : Ruta de directorio de salida
        """

        file_path = output_path / "openvdb" / f"{layer}.vdb"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"{layer}: {file_path}")

        # Convertir tensores a arreglo de numpy
        data = self.model_extractor.layers[layer].numpy().astype("float32").squeeze()

        # Convertir a OpenVDB
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.transform = openvdb.createLinearTransform(voxelSize=0.1)
        grid.name = "density"

        if self.dry_run:
            return

        openvdb.write(str(file_path), grid)

    def _tensor_to_image(self, layer:str, output_path: Path):
        """Guarda el tensor como una secuencia de imagenes."""
        data = self.model_extractor.layers[layer].numpy().astype("float32").squeeze()

        # Guardar a disco
        for ext in self.image_extensions:
            print(f"{layer}: {output_path}\\{ext}\\{layer}")

        # Creación de imagen
        for idx, channel in enumerate(data):
            for ext in self.image_extensions:
                out_file = output_path / ext / layer / f"frame_{idx:04d}.{ext}"
                out_file.parent.mkdir(parents=True, exist_ok=True)

                if ext in ("tiff", "tif"):
                    # Modo 'F': Float32 puro sin escalado ni clipping
                    img = Image.fromarray(channel, mode="F")
                    img.save(out_file)

                elif ext == "png":
                    # PNG no soporta mode='F'; convertimos [0.0, 1.0] -> [0, 255] uint8 sin estirar contraste
                    arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                    img = Image.fromarray(arr, mode="L")
                    img.save(out_file, compress_level=6)

                elif ext in ("jpg", "jpeg"):
                    # JPEG requiere uint8; especificamos calidad máxima para evitar artefactos de compresión
                    arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                    img = Image.fromarray(arr, mode="L")
                    img.save(out_file, quality=95)