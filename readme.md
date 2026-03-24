# Sistema Automatizado de Visualización Tridimensional de YOLOv8
**Por Ricardo Sánchez Pérez**

Este repositorio es el espacio de trabajo para el desarrollo de la tesis con titulo provisional:

> *Sistema Automatizado de Visualización Tridimensional Interactiva para la Interpretación de Redes Neuronales Convolucionales utilizando Python y Blender aplicado al Modelo YOLOv8*

Por lo tanto contiene archivos relacionados al codigo fuente, documentación, resultados de experimentos, datos extraidos, y al trabajo escrito.

## Estructura del proyecto
El repositorio esta estructurado de la siguiente forma:

- ```data``` Contiene los datos a usar por el pipeline, como datasets de YOLO.
- ```docs``` Contiene la documentación del codigo fuente y archivos auxiliares relacionados al desarrollo e implementació del software.
- ```experimentos``` Contiene resultados significativos de experimentos realizados, como mapas de activacion y pesos obtenidos del modelo YOLO, escenas de Blender, metricas de rendimiento, etc.
- ```resultados``` Contiene los resultados más significativos del proyecto para su presentación.
- ```scripts``` Contiene scripts de python para ejecutar el pipeline.
- ```src``` Contiene el codigo fuente de los modulos a desarrollar para YOLO, Blender, y el pipeline.
- ```tesis``` Contiene los archivos para el trabajo escrito de tesis.

## Software utilizado
**VS Code**

Editor de texto y ambiente de desarrollo integrado.

**Python 3.11**

Lenguaje de programación principal.

**Blender 4.5 LTS**

Sotware de modelado y animación 3D.

**Draw.io**

Software de creación de graficos y diagramas.

**TeX Live / TeX**

Redacción de tesis y documentación auxiliar.

**Git / GitHub**

Control de versiones.

## Hardware
El proyecto se desarrolló en una computadora personal con las siguientes características:

| Componente        | Características           |
| ----------------- | ------------------------- |
| Sistema Operativo | Windows 11 Home           |
| Procesador        | Intel i7 12th Gen         |
| Memoria           | 16 GB                     |
| GPU               | NVIDIA RTX 3050 Ti Laptop |
| VRAM              | 4 GB                      |
| Almacenamiento    | 1 TB SSD                  |

## Paquetes de Python utilizados
**pip**

Administración de paquetes.

**Pytorch**

Librería y funciones de aprendizaje profundo.

**Ultralytics**

Librería para la creación y administración de modelo YOLO.

**Numpy**

Soporte para arreglos grandes y multidimensionales, y funciones matemáticas para su manipulación.

**bpy**

API de Blender para Python

**Sphinx**

Generación de documentación del código fuente.

**venv**

Ambientes virtuales de desarrollo.

**pytest**

Pruebas unitarias.