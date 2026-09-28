"""Fast unit tests: no model downloads, no network.

Everything here must run in CI in seconds. Anything that needs model weights
belongs in tests/eval/ (accuracy) or benchmarks/ (speed), not here.
"""

import os
import tempfile

# Must be set before app modules are imported: config reads them at import time,
# and autoconfig would otherwise size worker pools from the CI runner.
os.environ.setdefault("SLOPTOTAL_PROFILE", "lite")
os.environ.setdefault("SLOPTOTAL_DATA_DIR", tempfile.mkdtemp(prefix="sloptotal-test-"))
