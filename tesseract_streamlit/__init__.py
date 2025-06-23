from . import _version, parse

__version__ = _version.get_versions()["version"]

# import public API of the package
# from . import <obj>

# add public API as strings here, for example __all__ = ["obj"]
__all__ = ["parse"]
