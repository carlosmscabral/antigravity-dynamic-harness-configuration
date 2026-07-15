#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Back-compat CLI shim. The real logic lives in merge_config.py (importable module).
Prefer `merge_config.py` / importing it directly. Kept so any old references keep working."""

import os
import sys
import importlib.util

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_config.py")
_spec = importlib.util.spec_from_file_location("merge_config", _p)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    sys.exit(_mod.main(sys.argv))
