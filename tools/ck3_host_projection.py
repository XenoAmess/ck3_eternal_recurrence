"""Freeze Python host text with the exact bytes checked by the runtime wrapper."""
from __future__ import annotations

import hashlib
from pathlib import Path


def checked_effective_host(config: dict) -> str:
    """Use the wrapper's byte pin, decode, edit and final-SHA semantics; no exec."""
    reference = config["original_host"]
    raw = Path(reference["path"]).read_bytes()
    if (len(raw) != reference["bytes"] or
            hashlib.sha256(raw).hexdigest() != reference["sha256"]):
        raise ValueError("Frozen host input differs from its byte pin")
    source = raw.decode("utf-8-sig")
    for before, after in config["edits"]:
        if source.count(before) != 1:
            raise ValueError("Host overlay insertion differs")
        source = source.replace(before, after, 1)
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != config["effective_host_sha256"]:
        raise ValueError("Effective host differs from reviewed projection")
    return source


def freeze_host_projection(destination: Path, source: str, edits=()) -> dict:
    """Write explicit UTF-8 LF bytes and derive both pins from the written bytes.

    The destination is a new immutable artifact. A platform text writer would
    translate LF into CRLF on Windows after a precomputed source hash, which
    caused the actual R0015 host admission failure.
    """
    destination = destination.resolve()
    raw = source.replace("\r\n", "\n").encode("utf-8")
    with destination.open("xb") as stream:
        stream.write(raw)
    written = destination.read_bytes()
    projected = written.decode("utf-8-sig")
    for before, after in edits:
        if projected.count(before) != 1:
            raise ValueError("Host overlay insertion differs")
        projected = projected.replace(before, after, 1)
    config = {"original_host": {"path": str(destination), "bytes": len(written),
                               "sha256": hashlib.sha256(written).hexdigest()},
              "edits": list(edits),
              "effective_host_sha256": hashlib.sha256(projected.encode("utf-8")).hexdigest()}
    checked_effective_host(config)
    return config
