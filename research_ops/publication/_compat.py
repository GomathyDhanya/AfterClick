"""Keep historical publication imports/CLI names usable after organization."""

import importlib
import runpy


def expose(module_name, namespace):
    if namespace["__name__"] == "__main__":
        runpy.run_module(module_name, run_name="__main__")
    else:
        module = importlib.import_module(module_name)
        namespace.update({k: v for k, v in vars(module).items() if not k.startswith("__")})
