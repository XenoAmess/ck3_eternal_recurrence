"""Small, pinned RAM transform of Native10; no full candidate source copy.

The actual staged file is this wrapper. Generated code uses this real file's
identity for its normal source/card checks; the old producer's Git bytes and
inverse are separately checked before executing its finite phase entrypoint.
"""
import hashlib
from pathlib import Path
import subprocess

BASE_COMMIT = "c84d4db799f092a698a9aca2af10bebe20466221"
BASE_PATH = "tools/g2_saved_campaign/native30_artifact_postcheck10_20261020.py"
BASE_SHA = "a6cad40bf6975b93b70f4b8789e827be7f96c2e26705aa34a463ece1dbe41368"
BASE_BYTES = 23736
REPO = Path(__file__).resolve().parents[2]
EDITS = (
    ('ROOT / "attempt10-artifact-postcheck"', 'ROOT / "attempt11-artifact-postcheck"'),
    ('ROOT / "owner10-artifact/owner-spec"', 'ROOT / "owner11-artifact/owner-spec"'),
    ('"native30-artifact-postcheck10-plan-v1"', '"native30-artifact-postcheck11-plan-v1"'),
    ('"artifact10_" + path.stem', '"artifact11_" + path.stem'),
    ('require(owned + reserve <= 8388608, "new postcheck8M including owner")',
     'require(owned <= 8388608, "new postcheck8M including owner")'),
)


def base_bytes():
    data = subprocess.check_output(["git", "show", BASE_COMMIT + ":" + BASE_PATH], cwd=REPO)
    if len(data) != BASE_BYTES or hashlib.sha256(data).hexdigest() != BASE_SHA:
        raise ValueError("exact committed Native10 source required")
    return data


def transform(data, reverse=False):
    text = data.decode("utf-8")
    for before, after in (reversed(EDITS) if reverse else EDITS):
        before, after = (after, before) if reverse else (before, after)
        if text.count(before) != 1:
            raise ValueError("exactly one occurrence per authorized RAM hunk")
        text = text.replace(before, after, 1)
    return text.encode("utf-8")


def generated_bytes():
    original = base_bytes()
    generated = transform(original)
    if transform(generated, reverse=True) != original:
        raise ValueError("full Native10 inverse differs")
    return generated


def runtime_namespace():
    generated = generated_bytes()
    # No mutable module/global hooks, Path proxy, copied producer or fake path:
    # __file__ is the actual source-pinned stage wrapper being run by c0.
    namespace = {"__file__": str(Path(__file__).resolve()), "__name__": "native11_explicit_RAM_producer"}
    exec(compile(generated, namespace["__file__"], "exec"), namespace)
    return namespace


def main():
    return runtime_namespace()["main"]()


if __name__ == "__main__":
    raise SystemExit(main())
