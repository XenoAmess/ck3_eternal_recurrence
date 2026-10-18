"""Package the canonical live-run identity functions without a repo path dependency."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/ck3_live_run_id.py"
TARGET = ROOT / "ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py"
NAMES = ("MACHINE_ENV", "SLUG_RE", "LiveRunIdError", "_slug", "_automatic_machine_token",
         "derive_machine_id", "current_machine_id")


def render():
    text = SOURCE.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    selected = []
    for node in tree.body:
        names = ([node.name] if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else
                 [v.id for v in node.targets if isinstance(v, ast.Name)] if isinstance(node, ast.Assign) else [])
        if any(name in NAMES for name in names):
            selected.append(ast.get_source_segment(text, node))
    if len(selected) != len(NAMES):
        raise ValueError("canonical machine identity changed its packaging contract")
    body = "\n\n\n".join(selected) + "\n"
    digest = hashlib.sha256(body.encode()).hexdigest()
    return ('# GENERATED FILE: tools/gen_ck3_live_run_identity_package.py\n'
            '# Canonical: tools/ck3_live_run_id.py; selected-source SHA256: ' + digest + '\n'
            '"""Exact packaged canonical machine identity; no independent algorithm."""\n'
            'from __future__ import annotations\n\n'
            'import hashlib\nimport os\nimport platform\nimport re\nfrom pathlib import Path\n\n\n' + body)


if __name__ == "__main__":
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
