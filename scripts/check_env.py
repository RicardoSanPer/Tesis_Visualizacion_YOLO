"""Verifica el ambiente de desarrollo para YOLOv8.

Este script comprueba que las dependencias necesarias (por ejemplo, torch y
ultralytics) estén correctamente instaladas y funcionando.

Ejemplo:
    python scripts/check_env.py

Notas:
    - Ejecutar desde el directorio raíz del proyecto.
    - Descarga un modelo preentrenado en src/yolo/modelos/preentrenados/yolov8n.pt
    si no existe ya uno en el directorio.
"""

from ultralytics import YOLO

model = YOLO("modelos/preentrenados/yolov8n.pt")
model.info()
print("Check OK")