from importlib.util import find_spec

def _isModuleImportable(module_name):
    """Verify whether or not a module can be imported."""
    
    module_spec = find_spec(module_name)
    
    return bool(module_spec)


IS_H3_PRESENT = _isModuleImportable("h3")
