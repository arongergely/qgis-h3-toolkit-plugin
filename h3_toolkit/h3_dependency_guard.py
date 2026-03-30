from importlib.util import find_spec
from importlib.metadata import version, PackageNotFoundError


IS_H3_PRESENT: bool = bool(find_spec("h3"))

# Use PackageNotFoundError rather than relying on IS_H3_PRESENT being True —
# find_spec can find a partially-installed package that has no metadata, so
# version() could still raise even when IS_H3_PRESENT is True.
try:
    H3_VERSION: str | None = version("h3")
except PackageNotFoundError:
    H3_VERSION = None
