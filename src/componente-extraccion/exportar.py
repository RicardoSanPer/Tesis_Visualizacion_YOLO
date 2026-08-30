from extractor import ModelExtractor
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
    supported_formats = ("vdb", "tiff", "tif", "png", "jpeg", "jpg")
    
    dry_run = False
    formats = []
    info = False
    
    def __init__(self, extractor: ModelExtractor):
        self.model_extractor = extractor

    def export(self, output_path: Path):
        """Exporta los datos extraidos del modelo a JSON y OpenVDB

        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        directory_validation(output_path)

        manifest_file = str(output_path / f"manifest.json")
        if self.info: 
            print(f"Ejecutando red con entrada: {self.model_extractor.modelexe.input_path}")
            print(f"Guardando datos en: {output_path}\n")
            print(f"Manifesto: {manifest_file}\n")
            for ext in self.formats:
                if ext not in self.supported_formats:
                    print(f"Formato no soportado: '{ext}'")
                    print(f"Soportados: {self.supported_formats}")

        if not self.dry_run:
            with open(manifest_file, "w", encoding="utf-8") as file:
                json.dump(self.model_extractor.get_data(), file, indent=4)

        for key in self.model_extractor.layers.keys():
            self._convert_tensor(key, output_path)
            self._tensor_to_image(key, output_path)

        if self.info: print()

        self._save_io_images(output_path)
        self._convert_boxes(output_path)

    def _save_io_images(self, output_path: Path):
        """Exporta las imagenes de entrada y salida
        
        Args:
            output_path (Path) : Ruta de directorio de salida
        """
        in_file = str(output_path / "input.png")
        out_file = str(output_path / "output.png")

        if self.info:
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
        if 'vdb' not in self.formats: return

        file_path = str(output_path / "boxes.vdb")

        #Cada caja tiene formato (x, y, w, h, confidence, class probability, class id)
        data = np.array([[[t.item() for t in row] for row in self.model_extractor.boxes]])

        if data.ndim < 3:
            if self.info: print("No se detectó ningun objeto. Omitiendo creacion de cajas")
            return

        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.name = "density"

        if self.info: print(f"Cajas: {file_path}\n")
        if self.dry_run: return
        
        openvdb.write(file_path, grid)

    def _convert_tensor(self, layer:str, output_path: Path):
        """Convierte un tensor a cuadrícula OpenVDB y guarda el archivo

        Args:
            layer (str): nombre de la capa del tensor
            output_path (Path) : Ruta de directorio de salida
        """
        if 'vdb' not in self.formats: return

        file_path = output_path / "vdb" / f"{layer}.vdb"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.info: print(f"{layer}: {file_path}")

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

        # Creación de imagen
        for ext in self.formats:
            # Omitir extensiones no admitidas o vdb
            if ext == 'vdb' or ext not in ("tiff", "tif", "png", "jpeg", "jpg"): continue
            if self.info: print(f"{layer}: {output_path}\\{ext}\\{layer}")

            for idx, channel in enumerate(data):
                out_file = output_path / ext / layer / f"frame_{idx:04d}.{ext}"
                if not self.dry_run: out_file.parent.mkdir(parents=True, exist_ok=True)

                if ext in ("tiff", "tif"):
                    # Modo 'F': Float32 puro sin escalado ni clipping
                    img = Image.fromarray(channel, mode="F")
                    if not self.dry_run: img.save(out_file)

                elif ext == "png":
                    # PNG no soporta mode='F'; convertimos [0.0, 1.0] -> [0, 255] uint8 sin estirar contraste
                    arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                    img = Image.fromarray(arr, mode="L")
                    if not self.dry_run: img.save(out_file, compress_level=6)

                elif ext in ("jpg", "jpeg"):
                    # JPEG requiere uint8; especificamos calidad máxima para evitar artefactos de compresión
                    arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                    img = Image.fromarray(arr, mode="L")
                    if not self.dry_run:    img.save(out_file, quality=95)