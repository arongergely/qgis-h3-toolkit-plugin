from importlib.util import find_spec
from importlib.metadata import version

def _isModuleImportable(module_name):
    """Verify whether or not a module can be imported."""
    
    module_spec = find_spec(module_name)
    
    return bool(module_spec)


IS_H3_PRESENT = _isModuleImportable("h3")
H3_VERSION = version("h3") if IS_H3_PRESENT else None
