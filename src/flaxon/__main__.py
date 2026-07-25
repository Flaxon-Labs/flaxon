"""
Flaxon command-line entry point.

This module allows Flaxon to be run as a module:
    python -m flaxon
"""

from __future__ import annotations

import sys

from flaxon.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
