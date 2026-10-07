"""Render bounded preservation gates for existing faith-bound assets.

Cross-faith C2 transfer is unsupported while either affected faith has native
orders or registered saints. Rendering does not migrate or create an asset and
does not prove CK3 iterator, artifact, warfare or reload behavior.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIGGERS = """# Faith scope. Orders include military and monastic orders: neither is moved.
# Registered saints retain their native faith association and relic references.
lyd_m3_faith_assets_clear_trigger = {
    NOT = { any_faith_holy_order = { always = yes } }
    NOT = { any_saint = { always = yes } }
}
# Character scope; read only captured C2 faiths, with presence before dereference.
# Re-evaluate at final authorization, rather than trusting the opening state.
lyd_m3_c2_assets_clear_trigger = {
    trigger_if = {
        limit = { has_variable = lyd_c2_source_faith exists = var:lyd_c2_source_faith }
        var:lyd_c2_source_faith = { lyd_m3_faith_assets_clear_trigger = yes }
    }
    trigger_else = { always = no }
    trigger_if = {
        limit = { has_variable = lyd_c2_kind }
        trigger_if = {
            limit = { var:lyd_c2_kind = 1 }
            trigger_if = {
                limit = { has_variable = lyd_c2_target_faith exists = var:lyd_c2_target_faith }
                var:lyd_c2_target_faith = { lyd_m3_faith_assets_clear_trigger = yes }
            }
            trigger_else = { always = no }
        }
        trigger_else = { var:lyd_c2_kind = 2 }
    }
    trigger_else = { always = no }
}
"""


def build_outputs() -> dict[str, bytes]:
    header = '# GENERATED FILE: edit tools/gen_faith_assets.py and run tools/gen_runtime.py.\n'
    return {'common/scripted_triggers/lyd_m3_faith_asset_triggers.txt':
            (header + TRIGGERS).encode('utf-8-sig')}


def generate(output: Path, *, check: bool = False) -> list[str]:
    mismatches = []
    for relative, payload in build_outputs().items():
        path = output / relative
        if check:
            if not path.is_file() or path.read_bytes() != payload:
                mismatches.append(relative)
        else:
            if path.exists():
                raise ValueError(f'Refuse to overwrite a prior projection: {path}')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    mismatches = generate(args.output, check=args.check)
    if mismatches:
        print('Generated faith asset gates differ: ' + ', '.join(mismatches))
        return 1
    print('Faith asset source projection verified' if args.check else 'Faith asset source projection generated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
