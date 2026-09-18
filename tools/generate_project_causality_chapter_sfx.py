#!/usr/bin/env python3
"""Generate deterministic non-musical chapter-gate sound effects."""

from __future__ import annotations

import argparse
import math
import random
import struct
import wave
from pathlib import Path
from typing import Callable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "promo" / "project_causality" / "30m" / "sfx"
SAMPLE_RATE = 48_000
DURATION_SECONDS = 8.0
SAMPLE_COUNT = int(SAMPLE_RATE * DURATION_SECONDS)


def _blank() -> list[float]:
    return [0.0] * SAMPLE_COUNT


def _add_tone(
    samples: list[float],
    *,
    start: float,
    duration: float,
    frequency: float,
    amplitude: float,
    decay: float = 0.0,
) -> None:
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), SAMPLE_COUNT - first)
    attack = max(1, int(0.012 * SAMPLE_RATE))
    release = max(1, int(0.08 * SAMPLE_RATE))
    for offset in range(max(0, count)):
        t = offset / SAMPLE_RATE
        envelope = 1.0
        if offset < attack:
            envelope *= offset / attack
        remaining = count - offset
        if remaining < release:
            envelope *= max(0.0, remaining / release)
        if decay:
            envelope *= math.exp(-decay * t)
        samples[first + offset] += (
            amplitude * envelope * math.sin(2.0 * math.pi * frequency * t)
        )


def _add_noise(
    samples: list[float],
    *,
    start: float,
    duration: float,
    amplitude: float,
    seed: int,
) -> None:
    generator = random.Random(seed)
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), SAMPLE_COUNT - first)
    previous = 0.0
    for offset in range(max(0, count)):
        phase = offset / max(1, count - 1)
        envelope = math.sin(math.pi * phase) ** 2
        raw = generator.uniform(-1.0, 1.0)
        previous = previous * 0.78 + raw * 0.22
        samples[first + offset] += amplitude * envelope * previous


def _spell() -> list[float]:
    samples = _blank()
    for frequency, amplitude in ((110.0, 0.34), (220.0, 0.18), (330.0, 0.08)):
        _add_tone(
            samples,
            start=3.05,
            duration=3.7,
            frequency=frequency,
            amplitude=amplitude,
            decay=0.92,
        )
    _add_tone(samples, start=5.9, duration=0.18, frequency=55.0, amplitude=0.12)
    _add_tone(samples, start=6.8, duration=0.18, frequency=55.0, amplitude=0.10)
    return samples


def _method() -> list[float]:
    samples = _blank()
    _add_noise(samples, start=2.9, duration=0.62, amplitude=0.24, seed=0xCA551)
    for index, start in enumerate((4.0, 4.72, 5.44, 6.16)):
        _add_tone(
            samples,
            start=start,
            duration=0.18,
            frequency=178.0 + index * 11.0,
            amplitude=0.18,
            decay=7.0,
        )
    return samples


def _principle() -> list[float]:
    samples = _blank()
    _add_tone(samples, start=3.15, duration=0.55, frequency=72.0, amplitude=0.18, decay=5.0)
    _add_noise(samples, start=6.1, duration=0.18, amplitude=0.26, seed=0x5EA1)
    _add_tone(samples, start=6.1, duration=0.33, frequency=96.0, amplitude=0.32, decay=9.0)
    return samples


def _vision() -> list[float]:
    samples = _blank()
    notes = (261.63, 329.63, 392.00, 523.25, 659.25)
    for index, frequency in enumerate(notes):
        start = 3.0 + index * 0.62
        _add_tone(
            samples,
            start=start,
            duration=1.15,
            frequency=frequency,
            amplitude=0.13,
            decay=2.2,
        )
        _add_tone(
            samples,
            start=start,
            duration=0.9,
            frequency=frequency * 2.0,
            amplitude=0.045,
            decay=3.0,
        )
    return samples


GENERATORS: dict[str, Callable[[], list[float]]] = {
    "spell-low-bell.wav": _spell,
    "method-page-pulse.wav": _method,
    "principle-dry-seal.wav": _principle,
    "vision-five-note-rise.wav": _vision,
}


def _write_wave(path: Path, samples: list[float]) -> None:
    peak = max(abs(value) for value in samples) or 1.0
    gain = min(1.0, 0.82 / peak)
    payload = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, value * gain)) * 32767.0))
        for value in samples
    )
    temporary = path.with_name(f".{path.name}.tmp")
    with wave.open(str(temporary), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(payload)
    temporary.replace(path)


def generate(output_directory: Path) -> list[Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, generator in GENERATORS.items():
        path = output_directory / name
        _write_wave(path, generator())
        paths.append(path)
    return paths


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    for path in generate(args.output_dir.resolve()):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
