import importlib
import pkgutil
import traceback
from pathlib import Path

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

_NODES_DIR = Path(__file__).parent / "nodes"
_TAG = "[my_vfx_nodes]"

for _mod in sorted(pkgutil.iter_modules([str(_NODES_DIR)]), key=lambda m: m.name):
    # bỏ qua file bắt đầu bằng "_" (ví dụ _helpers.py)
    if _mod.name.startswith("_"):
        continue

    try:
        module = importlib.import_module(f".nodes.{_mod.name}", __name__)
    except Exception:
        print(f"{_TAG} IMPORT FAILED: nodes/{_mod.name}.py")
        traceback.print_exc()
        continue

    classes = getattr(module, "NODE_CLASS_MAPPINGS", None)
    if not classes:
        continue  # file phụ trợ, không phải file node

    for key in classes:
        if key in NODE_CLASS_MAPPINGS:
            print(f"{_TAG} WARNING: trùng key '{key}' trong nodes/{_mod.name}.py, bị ghi đè")

    NODE_CLASS_MAPPINGS.update(classes)
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(module, "NODE_DISPLAY_NAME_MAPPINGS", {}))

print(f"{_TAG} đã nạp {len(NODE_CLASS_MAPPINGS)} node: {', '.join(NODE_CLASS_MAPPINGS)}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]