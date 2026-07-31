import torch
from torch.fx import symbolic_trace

class ModelExtractor:
    def __init__(self, model):
        self.modelexe = model
        self.model = model.model
        self.layers = {}
        self.layers_data = {}

        # Placeholder para la entrada
        self.layers_data["input"] = {
            "type": "Input",
            "data": False,
            "connections": []
        }

        self._set_hooks()
        self._get_connections()

    def _hook(self, module, input, output):
        for name, layer in self.model.named_modules():
            # Omitir raíz
            if name == '':
                continue
            # Omitir capas para las cuales no se extraen datos
            if not self.layers_data[name]["data"]:
                continue
            if layer is module:
                self.layers[name] = output.detach().cpu()
                break
                


    def _set_hooks(self):
        ## Extrae configuración de las capas y crea el forward hook
        for name, layer in self.model.named_modules():
            # Obtener nombre correcto de la capa
            if not name:
                continue
            # Convolucion
            if isinstance(layer, torch.nn.Conv2d):
                self.layers_data[name] = {
                    "type"           : type(layer).__name__,
                    "input_channels" : layer.in_channels,
                    "output_channels": layer.out_channels,
                    "kernel_size"    : layer.kernel_size,
                    "stride"         : layer.stride,
                    "padding"        : layer.padding,
                    "data"           : True,
                    "connections"    : []
                    }
                layer.register_forward_hook(self._hook)
            # Max Pooling
            elif isinstance(layer, torch.nn.MaxPool2d):
                self.layers_data[name] = {
                    "type"           : type(layer).__name__,
                    "kernel_size"    : layer.kernel_size,
                    "stride"         : layer.stride,
                    "padding"        : layer.padding,
                    "data"           : True,
                    "connections"    : []
                    }
                layer.register_forward_hook(self._hook)
            # Para capas no definidas solo registrar el nombre y tipo
            else:
                self.layers_data[name] = {
                    "type"           : type(layer).__name__,
                    "data"           : False,
                    "connections"    : []
                    }

    def _get_connections(self):
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
        if node.op == "placeholder":
            return "input"
        elif node.op == "call_module":
            return node.target
        return None

    def get_data(self):
        return {
            "confidence"    : self.modelexe.conf_threshold,
            "nms"           : self.modelexe.nms_threshold,
            "layers_data"   : self.layers_data

        }