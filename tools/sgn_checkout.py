"""Locate the SGN source checkout that some tests compare against.

Set SGN_CHECKOUT to an sgn checkout (for example a clone of
https://github.com/solgenomics/sgn). Tests that read SGN files are skipped,
with this reason, when it is not set; a set but wrong path fails them.
"""

import os
import unittest
from pathlib import Path

SGN = Path(os.environ["SGN_CHECKOUT"]).resolve() if os.environ.get("SGN_CHECKOUT") else None
needs_sgn = unittest.skipUnless(SGN is not None, "set SGN_CHECKOUT to an SGN source checkout")
