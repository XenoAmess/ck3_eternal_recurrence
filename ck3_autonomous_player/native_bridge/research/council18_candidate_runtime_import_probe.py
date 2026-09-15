"""Import the R693 runtime closure from one verified candidate-local source."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from candidate_runtime_identity import (
    assert_imported_module,
    verify_candidate_source,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.candidate_root.resolve()
    source_root, identity = verify_candidate_source(root)
    sys.path.insert(0, str(source_root))

    import xar_autoplayer.bridge.native_driver as native_driver_module
    import xar_autoplayer.environment as environment_module
    import xar_autoplayer.native_auto_run as native_auto_run_module
    import xar_autoplayer.runtime as runtime_module
    import build_release

    modules = (
        build_release,
        native_driver_module,
        environment_module,
        native_auto_run_module,
        runtime_module,
    )
    for module in modules:
        assert_imported_module(
            module,
            expected_name=module.__name__,
            source_root=source_root,
            identity=identity,
        )
    if not hasattr(
        native_driver_module.NativeHeadlessGameplayDriver,
        "take_internal_semantic_snapshot",
    ):
        raise RuntimeError("candidate-local driver lacks internal snapshot API")
    print(
        json.dumps(
            {
                "status": "green",
                "mode": "optimized" if not __debug__ else "normal",
                "source_commit": identity["source_commit"],
                "source_tree_sha256": identity["source_tree_sha256"],
                "tools_tree_sha256": identity["tools_tree_sha256"],
                "module_files": {
                    module.__name__: str(Path(module.__file__).resolve())
                    for module in modules
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

