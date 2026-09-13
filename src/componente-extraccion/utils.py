from pathlib import Path

def directory_validation(path: Path):
    """Valida la ruta de directorio para guardar los datos extraidos.

    Args:
        path (Path): Ruta de directorio

    Raises:
        ValueError: Si no se proporciona una ruta válida.
        NotADirectoryError: Si se proporciona una ruta de archivo en vez de directorio

    Returns:
        Path: ruta de archivo
    """
    if not path:
        raise ValueError("No se ingresó ningun archivo.")
    if path.is_file():
        raise NotADirectoryError(f"Esperado un directorio, es archivo: {path}")
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path

def file_validation(path: Path):
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