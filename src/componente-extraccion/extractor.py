import torch
from torch.fx import symbolic_trace
import torch.nn.functional as F

class ModelExtractor:
    """Clase para extraer los datos del modelo de la red YOLOv2, incluyendo
    tensores de capas de interés, configuraciones de las capas, y la arquitectura
    de la red en la forma de las conexiones entre capas.
    """
    def __init__(self, model, capture_layers: list=[], includes: list=[], excludes: list = []):
        """Constructor

        Args:
            model (ModelExecutor): Módulo de ejecución del modelo
            capture_layers (list): Lista de tipos de capa a incluir en la extracción
            includes (list): Lista de capas (por nombre) a incluir en la extracción
            excludes (list): Lista de capas (por nombre) a excluir en la extracción
        """
        self.modelexe = model
        self.model = model.model
        self.layers = {}
        self.layers_data = {}
        self.classes = model.class_names

        # Includes y exlcudes
        self.capture_layers = capture_layers
        self.include = includes
        self.exclude = excludes

        # Placeholder para la entrada
        self.layers_data["input"] = {
            "type": "Input",
            "data": False,
            "connections": []
        }

        self._get_layer_data()
        self._get_layer_connections()

    def _hook(self, module, input, output):
        """Hook para el paso hacia adelante. Extrae los tensores de las capas de 
        interés.

        Args:
            module (torch.nn.modules): Modulo de la capa
            input (torch.Tensor): Tensor de entrada de la capa
            output (torch.Tensor): Tensor de salida de la capa
        """
        for name, layer in self.model.named_modules():
            # Omitir raíz
            if name == '':
                continue
            
            # Guardar tensor de salida
            if layer is module:
                # Extraer tensor solo de capas indicadas
                tensor = output.detach().cpu()
                if self.layers_data[name].get("data"):
                    self.layers[name] = tensor
                self.layers_data[name]["dimensions"] = tensor.shape
                break
                


    def _get_layer_data(self):
        """ Extrae datos de las capas y configura los hooks para las capas con datos
        intermedios de interés.
        """
        ## Extrae configuración de las capas y crea el forward hook
        for name, layer in self.model.named_modules():
            # Obtener nombre correcto de la capa
            if not name:
                continue

            if name in ("cnn", "input"):
                continue

            # Datos de capa
            self.layers_data[name] = {
                "type"           : type(layer).__name__,
                "connections"    : [],
                "data"           : False
            }

            # Capturar dato si tipo fue especificado
            layer_type = self.layers_data[name].get("type")
            if layer_type in self.capture_layers:
                self.layers_data[name]["data"] = True

            if name in self.include:
                self.layers_data[name]["data"] = True

            if name in self.exclude:
                self.layers_data[name]["data"] = False
                
            # Convolucion
            if isinstance(layer, torch.nn.Conv2d):
                self.layers_data[name]["kernel_size"] = layer.kernel_size
                self.layers_data[name]["stride"] = layer.stride
                self.layers_data[name]["padding"] = layer.padding
            # Max Pooling
            elif isinstance(layer, torch.nn.MaxPool2d):
                self.layers_data[name]["kernel_size"] = layer.kernel_size
                self.layers_data[name]["stride"] = layer.stride
                self.layers_data[name]["padding"] = layer.padding
                self.layers_data[name]["ceiling"] = layer.ceil_mode
            
            layer.register_forward_hook(self._hook)

    def _get_layer_connections(self):
        """ Obtiene las conexiones entre capas.
        """
        gm = symbolic_trace(self.model)
        for node in gm.graph.nodes:
            dst = self._node_name(node)
            if dst is None:
                continue
            for inp in node.all_input_nodes:
                src = self._node_name(inp)
                if src is None:
                    continue
                self.layers_data[src]["connections"].append(dst)

    def _node_name(self, node):
        """Funcion auxiliar para obtener el nombre de un nodo del grafo de la red.

        Args:
            node (torch.fx.node.Nose): Nodo del grafo de la red generado por torch.fx

        Returns:
            _type_: _description_
        """
        # Para el nodo de la entrada
        if node.op == "placeholder":
            return "input"
        # Para otros nodos, con el nombre correcto
        elif node.op == "call_module":
            return node.target
        return None

    def print_info(self):
        """Imprime información de la red"""
        operations = {}
        for name, layer in self.model.named_modules():
            if name == "cnn":
                continue

            layer_type = type(layer).__name__
            if layer_type not in operations:
                operations[layer_type] = []
            operations[layer_type].append(name)

        for layer in operations.keys():
            print(f"{layer}:")
            for item in operations[layer]:
                print(f"\t{item}")
    
    def extract(self):
        """Ejecuta el modelo y extrae la imagen de entrada y salida.
        """
        self.modelexe.execute()
        self.input_image = self.modelexe.input_image
        self.output_image = self.modelexe.output_image
        self.boxes = self.modelexe.boxes

    def get_data(self):
        """Obtener los datos de la red en un formato estructurado.

        Returns:
            dict: datos de la red
        """
        return {
            "confidence"    : self.modelexe.conf_threshold,
            "nms"           : self.modelexe.nms_threshold,
            "n_boxes"       : len(self.boxes),
            "classes"       : ",".join(self.classes),
            "layers_data"   : self.layers_data
        }