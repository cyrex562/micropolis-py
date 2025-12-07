import sys
import os

# Add src to path if running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from citysim.core.engine import Engine


def main():
    engine = Engine()
    engine.run()


if __name__ == "__main__":
    main()
