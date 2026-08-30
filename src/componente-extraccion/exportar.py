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

        # Guardar manifesto
        if not self.dry_run:
            with open(manifest_file, "w", encoding="utf-8") as file:
                json.dump(self.model_extractor.get_data(), file, indent=4)

        # Exportar datos de tensores
        for key in self.model_extractor.layers.keys():
            self._save_tensor_as_grid(key, output_path)
            for ext in self.formats:
                self._save_tensor_as_image_seq(key, output_path, ext)

        if self.info: print()

        # Exportar cajas, imagenes de entrada y salida
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

    def _convert_tensor(self, layer:str):
        """Convierte un tensor a cuadrícula OpenVDB

        Args:
            layer (str): nombre de la capa del tensor

        Returns:
            openvdb: Volumen OpenVDB
        """

        # Convertir tensores a arreglo de numpy
        data = self.model_extractor.layers[layer].numpy().astype("float32").squeeze()

        # Convertir a OpenVDB
        grid = openvdb.FloatGrid()
        grid.copyFromArray(data)
        grid.transform = openvdb.createLinearTransform(voxelSize=0.1)
        grid.name = "density"

        return grid

    def _tensor_to_images(self, layer:str, ext: str):
        """Convierte el tensor a una secuencia de imagenes en el formato especificado
        (jpg, jpeg, png, tiff, tif)

        Args:
            layer (str): Capa a convertir
            ext (str): Extensión

        Returns:
            list: Arreglo de imagenes
        """
        data = self.model_extractor.layers[layer].numpy().astype("float32").squeeze()
        images = []
        
        for channel in data:
            if ext in ("tiff", "tif"):
                # Modo 'F': Float32 puro sin escalado ni clipping
                img = Image.fromarray(channel, mode="F")
                images.append(img)

            elif ext == "png":
                # PNG no soporta mode='F'; convertimos [0.0, 1.0] -> [0, 255] uint8 sin estirar contraste
                arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr, mode="L")
                images.append(img)

            elif ext in ("jpg", "jpeg"):
                # JPEG requiere uint8; especificamos calidad máxima para evitar artefactos de compresión
                arr = np.clip(channel * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr, mode="L")
                images.append(img)
        return images

    def _save_tensor_as_grid(self, layer:str, output_path: Path):
        """Convierte el tensor a volumen OpenVDB y exporta a un archivo.

        Args:
            layer (str): Capa a exportar
            output_path (Path): Directorio de salida
        """
        if 'vdb' not in self.formats: return

        file_path = output_path / "vdb" / f"{layer}.vdb"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        grid = self._convert_tensor(layer)

        if self.info: print(f"{layer}: {file_path}")
        if self.dry_run: return

        openvdb.write(str(file_path), grid)

    def _save_tensor_as_image_seq(self, layer: str, output_path: Path, ext: str):
        """Convierte el tensor a secuencias de imagenes en el formato especificado y las 
        guarda. Formatos: jpeg, jpg, png, tiff, tif

        Args:
            layer (str): Capa a guardar
            output_path (Path): Directorio de salida
            ext (str): Extension
        """
        if ext == 'vdb' or ext not in self.supported_formats: return
        if self.info: print(f"{layer}: {output_path}\\{ext}\\{layer}")

        images = self._tensor_to_images(layer, ext)
        # Guardar cada imagen individual
        for idx, img in enumerate(images):
            out_file = output_path / ext / layer / f"frame_{idx:04d}.{ext}"
            if not self.dry_run: 
                out_file.parent.mkdir(parents=True, exist_ok=True)
                if ext in ("jpg", "jpeg"):
                    img.save(out_file, quality=95)
                elif ext in ("png"):
                    img.save(out_file, compress_level=6)
                elif ext in ("tiff", "tif"):
                    img.save(out_file)

    def get_exported_volume_as_numpy32(self, layer:str, ext:str):
        """Reconstruye los datos del volumen exportado a partir del arreglo numpy32
        utilizado para escribir los datos
        Args:
            layer (str): capa de los datos a reconstruir
            ext (str): extensión utilizada para exportar

        Returns:
            numpy32: Arreglo numpy float32
        """
        if ext == "vdb":
            grid = self._convert_tensor(layer)
            return self._get_vdb_grid_as_numpy32(grid)
        elif ext in self.supported_formats:
            images = self._tensor_to_images(layer, ext)
            return self._get_images_as_numpy32(images)

    def _get_vdb_grid_as_numpy32(self, grid):
        """Reconstruye el arreglo numpy32 utilizado para exportar los datos de capa
        a partir de un volumen openvdb

        Args:
            grid: Volumen OpenVDB

        Returns:
            numpy32: Arreglo numpy float32
        """
        if grid is None:
            return
    
        min_coord, max_coord = grid.evalActiveVoxelBoundingBox()
        dim_x = max_coord[0] - min_coord[0] + 1
        dim_y = max_coord[1] - min_coord[1] + 1
        dim_z = max_coord[2] - min_coord[2] + 1
    
        dense_arr = np.zeros((dim_x, dim_y, dim_z), dtype=np.float32)
        grid.copyToArray(dense_arr, ijk=min_coord)
    
        return dense_arr

    def _get_images_as_numpy32(self, images: list):
        """A partir de un arreglo de imagenes reconstruye el arreglo numpy32 

        Args:
            images (list): Arreglo de imagenes

        Returns:
            numpy32: Arreglo numpy float32
        """
        data = []
        for img in images:
            arr = None
            if img.mode in ("F", "I;32F"):
                # TIFF en formato 32 bit
                arr = np.array(img, dtype=np.float32)
            elif img.mode == "I;16":
                # 16-bit grayscale TIFF/PNG (0 - 65535)
                arr = np.array(img, dtype=np.float32) / 65535.0
            else:
                # 8-bit JPEG/PNG a "F" y normalizar a [0.0, 1.0]
                arr = np.array(img.convert("F"), dtype=np.float32) / 255.0
            data.append(arr)
        return data
        