"""Small content utilities shared by this film's producers."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from PIL import ImageFont
from xar_promo.layout import FontSpec, WrapPolicy, wrap_text


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def binding(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.as_posix(), "bytes": path.stat().st_size, "sha256": digest}


def verify(row):
    actual = binding(row["path"])
    if any(actual[k] != row[k] for k in ("bytes", "sha256")):
        raise ValueError(f"Input bytes changed: {row['path']}")
    return Path(actual["path"])


@lru_cache(maxsize=48)
def font(size, bold=False):
    path = Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc")
    return ImageFont.truetype(str(path), int(size))


def lines(text, size, width, bold=False):
    face = font(size, bold)
    spec = FontSpec("msyh", "Microsoft YaHei", size, weight=700 if bold else 400)
    return wrap_text(text, font=spec, max_width=width, max_lines=100,
                     measure=lambda value, _: face.getlength(value),
                     policy=WrapPolicy(prefer_break_after=frozenset("，。！？；： "))).lines
