import sys, argparse, torch, torchvision
from TinyYoloV2.model import TinyYoloV2
from PIL import Image
from pathlib import Path

def load_image(img_path):
    if not img_path:
        print("Error: No se ingresó ningun archivo")
        return
    if not img_path.is_file():
        print(f"Error: El archivo '{img_path}' no existe.")
        return
    return Image.open(img_path)

def load_model(weights=None):
    model = TinyYoloV2()
    if weights:
        model.load_weights(weights)
    return model

def execute(img_path):
    # Obtener archivo de pesos relativo al directorio raíz del proyecto
    weight_path = Path.cwd() / "data" / "weights" / "yolov2-tiny-voc.weights"
    if not weight_path.is_file():
        print(f"Error: No se encontró el archivo de pesos: {weight_path}")
        return
    
    # Intentar cargar imagen
    input_img = load_image(img_path)
    if not input_img:
        return
    input_img = input_img.convert("RGB")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print(f"Imagen de entrada: {img_path} ({input_img.width}x{input_img.height})")
    print("Dispositivo: ", device)

    # Convertir imagen a tensor de entrada
    transform = torchvision.transforms.Compose([
        torchvision.transforms.Resize((416, 416)),
        torchvision.transforms.ToTensor()
    ])
    input_tensor = transform(input_img).unsqueeze(0).to(device)

    # Cargar modelo y evaluar
    model = load_model(weight_path).to(device)
    model.eval()

    with torch.no_grad():
        output = model(input_tensor)
        print(output)


if __name__=="__main__":
    # Argumentos del script
    ## El script toma como argumento una ubicación de archivo de imagen como entrada para la red
    parser = argparse.ArgumentParser(description="Imagen de entrada para la red")
    parser.add_argument(
        "image_path",
        type=Path,
        help="Ubicación de archivo de imagen"
    )
    args = parser.parse_args()
    execute(args.image_path)