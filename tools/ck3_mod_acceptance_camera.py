"""One file-only camera coordination namespace for public continuation cases."""
from pathlib import Path

AWAITING_NAME = 'before-action-camera-awaiting.json'
STARTED_NAME = 'before-action-camera-started.json'


def camera_paths(output):
    output=Path(output).resolve()
    return output/AWAITING_NAME, output/STARTED_NAME


def validate_camera_paths(awaiting, signal, *, live, output_name):
    """Reject stale aliases during configuration, before loading or movement."""
    if (type(output_name) is not str or not output_name or output_name in ('.','..')
            or Path(output_name).name!=output_name):
        raise ValueError('Camera output must be one explicit public output basename')
    expected=camera_paths(Path(live)/output_name)
    actual=Path(awaiting).resolve(),Path(signal).resolve()
    if actual!=expected:
        raise ValueError('Camera coordination must use before-action-camera-{awaiting,started}.json')
    return expected
