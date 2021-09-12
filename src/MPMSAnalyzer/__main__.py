import os
import sys

path = os.path.dirname(__file__)
if not path in sys.path:
    sys.path.insert(0, path)

import Controller

if __name__ == "__main__":
    # execute only if run as a script
    Controller.launch()