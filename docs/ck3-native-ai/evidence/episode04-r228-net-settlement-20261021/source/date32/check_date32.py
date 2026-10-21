from pathlib import Path
import difflib, hashlib, json, struct

base = Path("D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/native_bridge/src")
rows: list[dict[str, object]] = []
patch = ""
names = ("war_payment_window_12004.cpp", "army_natural_phase_scope_12004.cpp")
expected = ("66d311b72913e55eb37c0b6d76a8b04515001a6d273f372d79a296ed19e9a639", "ba6566c39bc2e1ab6bc1044c14572b7fa002196adacf751fa206904ca2d958b9")
for name, digest in zip(names, expected):
    old = (base / name).read_bytes()
    if hashlib.sha256(old).hexdigest() != digest:
        raise ValueError("immutable base changed")
    text = old.decode()
    if name == names[0]:
        text = text.replace("  return w.read&&", "  std::uint32_t date32=0;\n  const bool complete=w.read&&", 1)
        text = text.replace("identity+8,&date,sizeof date)", "identity+8,&date32,sizeof date32)", 1)
        text = text.replace("identity+0x9C,&day,sizeof day);\n}", "identity+0x9C,&day,sizeof day);\n  if(complete)date=static_cast<std::uint64_t>(date32);\n  return complete;\n}", 1)
    else:
        for field in ("scope.date_raw", "out.returned_date_raw"):
            old_read = field + " = Read<std::uint64_t>(b, scope.game_state_identity + 8);"
            new_read = field + " = std::optional<std::uint64_t>(\n          Read<std::uint32_t>(b, scope.game_state_identity + 8));"
            if text.count(old_read) != 1:
                raise ValueError("date site differs")
            text = text.replace(old_read, new_read)
    new = text.encode()
    path = "ck3_autonomous_player/native_bridge/src/" + name
    patch += "".join(difflib.unified_diff(old.decode().splitlines(True), text.splitlines(True), "a/"+path, "b/"+path, n=1))
    rows.append(dict(path=path, before=digest, after=hashlib.sha256(new).hexdigest(), bytes=len(new)))
raw = 300064548703630608
if struct.unpack("<I", struct.pack("<Q", raw)[:4])[0] != 53146896:
    raise ValueError("actual journal regression")
for high in (0, 69864222, 0xffffffff):
    if struct.unpack("<I", struct.pack("<II", 53146896, high)[:4])[0] != 53146896:
        raise ValueError("adjacent word polluted date")
print(json.dumps(dict(patch=patch, sources=rows, checks=3, native_executed=False), separators=(",", ":")))
