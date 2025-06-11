from importlib.util import find_spec
from importlib.metadata import version


IS_H3_PRESENT = bool(find_spec("h3"))
H3_VERSION = version("h3") if IS_H3_PRESENT else None
