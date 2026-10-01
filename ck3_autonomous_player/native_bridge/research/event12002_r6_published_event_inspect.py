"""Offline-only R6 published-event diagnostic; never opens a process."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import capstone
import pefile

WORKSPACE = Path(r"Z:\ck3_mod_rewrite")
EXE = WORKSPACE / "artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe"
ARTIFACTS = WORKSPACE / "artifacts/g2-offline-2026-10-01"
OUTPUT = ARTIFACTS / "event12002-r6-published-event"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = EXE.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    assert sha == "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
    pe = pefile.PE(data=raw, fast_load=False)
    image = pe.get_memory_mapped_image()
    dis = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    ranges = [(0x29C57A0, 0x29C5950), (0xA7CFC0, 0xA7D100), (0xC45780, 0xC45B30), (0xC45B30, 0xC45E00)]
    lines = []
    for lo, hi in ranges:
        lines.append(f"RVA {lo:#x}..{hi:#x}")
        lines.extend(f"{ins.address:#010x} {ins.bytes.hex(' '):<28} {ins.mnemonic} {ins.op_str}" for ins in dis.disasm(image[lo:hi], lo))
    (OUTPUT / "narrow-disassembly.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {"exe_sha256": sha, "ranges": [{"start": hex(lo), "end": hex(hi)} for lo, hi in ranges], "snapshot_fields": []}
    targets = [ARTIFACTS / "construction-live-next/root-r6-fresh-material-01/snapshot-before.json"]
    targets.extend((ARTIFACTS / "targeted-sdk-r6/r6-current-event14-context-20261001T115859Z").glob("*ck3_take_snapshot.json"))
    def locate(data, trail=()):
        if isinstance(data, dict):
            if "active_event" in data:
                return [(trail, {key: data.get(key) for key in ("revision", "native_revision", "date_raw", "paused", "active_event", "played_character_id")})]
            found = []
            for key, value in data.items():
                if key == "text" and isinstance(value, str):
                    try:
                        found.extend(locate(json.loads(value), trail + (key,)))
                    except json.JSONDecodeError:
                        pass
                elif isinstance(value, (dict, list)):
                    found.extend(locate(value, trail + (key,)))
            return found
        if isinstance(data, list):
            return [row for idx, value in enumerate(data) for row in locate(value, trail + (str(idx),))]
        return []
    for target in targets:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
        summary["snapshot_fields"].append({"path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "fields": locate(data)})
    (OUTPUT / "offline-inspection.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
