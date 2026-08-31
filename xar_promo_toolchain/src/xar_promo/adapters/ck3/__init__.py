"""CK3 capture/evidence adapter.

``load_capture_bundle`` is the stable entry point.  The adapter is deliberately
read-only: a rejected run remains on disk as a preserved failed attempt.
"""

from .capture import (
    CK3CaptureError,
    CaptureBundle,
    CaptureFile,
    CaptureMark,
    CleanSpan,
    load_capture_bundle,
)

__all__ = [
    "CK3CaptureError",
    "CaptureBundle",
    "CaptureFile",
    "CaptureMark",
    "CleanSpan",
    "load_capture_bundle",
]
