import torch, torchvision
import TinyYoloV2.utils as utils
## Asume que los scripts de https://github.com/miladlink/TinyYoloV2 están en el subdirectorio TinyYoloV2
from TinyYoloV2.model import TinyYoloV2
from PIL import Image
from pathlib import Path

"""
Clase de encapsulación para la ejecución del modelo Tiny YoloV2.
"""

class ModelExecutor:
    """Clase para la ejecución del modelo TinyYoloV2. Encapsula el modelo, los datos que utiliza
    y métodos auxiliares para su ejecución.

    Raises:
        ValueError: Si no se proporciona una ruta de archivo para la entrada del modelo o pesos
        FileNotFoundError: Si se proporciona una ruta de archivo inválida para la entrada o pesos
        IsADirectoryError: Si se proporciona un directorio en vez de un archivo para la entrada o pesos

    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    weight_path = Path.cwd() / "data" / "weights" / "yolov2-tiny-voc.weights"

    conf_threshold = 0.55
    nms_threshold = 0.55
    class_names = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle',
               'bus', 'car', 'cat', 'chair', 'cow', 'diningtable',
               'dog', 'horse', 'motorbike', 'person', 'pottedplant',
               'sheep', 'sofa', 'train', 'TVmonitor']

    def __init__(self, input_path: Path):
        """Constructor de la clase de ejecución.

        Args:
            input_path (Path): Ruta de archivo de entrada del modelo
        """
        self.input_path = input_path
        self._load_image()
        self._load_model()
        self._load_input_tensor()

    def execute(self):
        """Ejecuta el modelo.
        """
        self.model.eval()
        with torch.no_grad():
            self.output = self.model(self.input_tensor)

        self.boxes = utils.find_all_boxes(self.output, self.conf_threshold, self.model.num_classes,
                                          self.model.anchors, self.model.num_anchors)[0]
        self.boxes = utils.nms(self.boxes, self.nms_threshold)
        output_file = self.input_path.parent / "output.jpg"
        self.output_image = utils.plot_boxes(self.input_image.copy(), self.boxes, savename=None, class_names=self.class_names)


    def _load_image(self):
        """Carga una imagen dada la ruta de entrada.
        """
        if self._file_validation(self.input_path):
            self.input_image = Image.open(self.input_path)

    def _load_model(self):
        """Carga el modelo y los pesos
        """
        self._file_validation(self.weight_path)
        self.model = TinyYoloV2()
        self.model.load_weights(self.weight_path)
        self.model = self.model.to(self.device)

    def _load_input_tensor(self):
        """Transforma la imagen de entrada al formato y dimensiones requeridas de la red
        y la transforma a un tensor. 
        """
        self.input_image = self.input_image.convert("RGB")
        transform = torchvision.transforms.Compose([
                    torchvision.transforms.Resize((416, 416)),
                    torchvision.transforms.ToTensor()
                    ])
        self.input_tensor = transform(self.input_image).unsqueeze(0).to(self.device)

    def _file_validation(self, path: Path):
        """Valida la ruta de archivo.

        Args:
            path (Path): Ruta de archivo

        Raises:
            ValueError: Si no se proporciona una ruta de archivo para la entrada del modelo o pesos
            FileNotFoundError: Si se proporciona una ruta de archivo inválida para la entrada o pesos
            IsADirectoryError: Si se proporciona un directorio en vez de un archivo para la entrada o pesos

        Returns:
            Path: ruta de archivo
        """
        if not path:
            raise ValueError("No se ingresó ningun archivo.")
        if not path.exists():
            raise FileNotFoundError(f"El archivo especificado no existe: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Esperado un archivo, es directorio: {path}")
        return path