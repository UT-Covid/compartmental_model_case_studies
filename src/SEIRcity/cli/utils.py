import importlib


def dynamic_import(module, package=None):
    """Dynamically import a module by name at runtime
    Args:
        module (str): The name of the module to import
        package (str, optional): The package to import ``module`` from
    Returns:
        object: The imported module
    """
    return importlib.import_module(module, package=package)
