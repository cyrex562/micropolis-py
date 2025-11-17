import importlib

m1 = importlib.import_module("micropolis.types")
try:
    m2 = importlib.import_module("src.micropolis.types")
except Exception:
    m2 = None
print("micropolis.types id=", id(m1), "name=", getattr(m1, "__name__", None))
print("src.micropolis.types id=", id(m2), "name=", getattr(m2, "__name__", None))
print("same=", m1 is m2)
print("sys.modules contains:")
import sys

for k in sorted(k for k in sys.modules.keys() if "types" in k):
    print("  ", k)
