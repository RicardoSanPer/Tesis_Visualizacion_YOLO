import sys, argparse, torch, torchvision
import TinyYoloV2.utils as utils
from TinyYoloV2.model import TinyYoloV2
from PIL import Image
from pathlib import Path

class ModelExecution:
    """Clase para la ejecución del modelo TinyYoloV2. Encapsula el modelo, los datos que utiliza
    y métodos auxiliares para su ejecución.

    Raises:
        ValueError: Si no se proporciona una ruta de archivo para la entrada del modelo o pesos
        FileNotFoundError: Si se proporciona una ruta de archivo inválida para la entrada o pesos
        IsADirectoryError: Si se proporciona un directorio en vez de un archivo para la entrada o pesos

    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    weight_path = Path.cwd() / "data" / "weights" / "yolov2-tiny-voc.weights"

    conf_threshold = 0.66
    nms_threshold = 0.55
    class_names = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle',
               'bus', 'car', 'cat', 'chair', 'cow', 'diningtable',
               'dog', 'horse', 'motorbike', 'person', 'pottedplant',
               'sheep', 'sofa', 'train', 'TVmonitor']

    def __init__(self, input_path):
        """Constructor de la clase de ejecución

        Args:
            input_path (Path): Ruta de archivo de entrada del modelo
        """
        self.input_path = input_path
        self.__load_image()
        self.__load_model()
        self.__load_input_tensor()

    def execute(self):
        """Ejecuta el modelo
        """
        self.model.eval()
        with torch.no_grad():
            self.output = self.model(self.input_tensor)

        self.boxes = utils.find_all_boxes(self.output, self.conf_threshold, self.model.num_classes,
                                          self.model.anchors, self.model.num_anchors)[0]
        self.boxes = utils.nms(self.boxes, self.nms_threshold)
        output_file = self.input_path.parent / "output.jpg"
        self.output_image = utils.plot_boxes(self.input_image, self.boxes, savename=None, class_names=self.class_names)


    def __load_image(self):
        """Carga una imagen dada la ruta de entrada
        """
        if self.__file_validation(self.input_path):
            self.input_image = Image.open(self.input_path)

    def __load_model(self):
        """Carga el modelo y los pesos
        """
        self.__file_validation(self.weight_path)
        self.model = TinyYoloV2()
        self.model.load_weights(self.weight_path)
        self.model = self.model.to(self.device)

    def __load_input_tensor(self):
        """Transforma la imagen de entrada al formato y dimensiones requeridas de la red
        y la transforma a un tensor. 
        """
        self.input_image = self.input_image.convert("RGB")
        transform = torchvision.transforms.Compose([
                    torchvision.transforms.Resize((416, 416)),
                    torchvision.transforms.ToTensor()
                    ])
        self.input_tensor = transform(self.input_image).unsqueeze(0).to(self.device)

    def __file_validation(self, path):
        """Valida la ruta de archivo

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

if __name__=="__main__":
    """Funcion main utilizada cuando el script se ejecuta directamente desde la terminal.
    Recibe como argumentos una ruta de archivo para la entrada de la red.
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
    model = ModelExecution(args.image_path)
    model.execute()
    #print(model.boxes)