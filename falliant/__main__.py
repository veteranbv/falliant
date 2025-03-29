#!/usr/bin/env python3
"""
Allows the package to be run as a module
python -m falliant
"""

import sys

from . import main

if __name__ == "__main__":
    sys.exit(main())
