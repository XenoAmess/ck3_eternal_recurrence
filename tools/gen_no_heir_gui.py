import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Crusader Kings III/game/gui/window_succession_event.gui"
OUTPUT = ROOT / "XenoAmess_s_Eternal_Recurrence/gui/window_succession_event.gui"
HEADER = "# GENERATED FILE - native 1.19 succession window plus XAR no-heir widget\n"
NATIVE_SHA256 = "322971347711308a51bcb16e3c34a7bd9eae5e7938243699ec8fe3691d8c7406"
ANCHOR = '\n}\n\n\nwindow = {\n\tname = "succession_select_destiny_window"'
INJECTION = '\n\txar_no_heir_settlement_widget = {}\n'


def native_digest(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def validate_native_source(source):
    digest = native_digest(source)
    if digest != NATIVE_SHA256:
        raise RuntimeError(
            f"native succession window digest changed: {digest} != {NATIVE_SHA256}")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("native succession window anchor changed")
    if INJECTION in source:
        raise RuntimeError("native succession window already contains the XAR injection")


def render_source(source):
    validate_native_source(source)
    return source.replace(ANCHOR, INJECTION + ANCHOR, 1)


def render():
    return render_source(SOURCE.read_text(encoding="utf-8-sig"))


def recover_source(projection):
    if not projection.startswith(HEADER):
        raise RuntimeError("succession projection header changed")
    body = projection[len(HEADER):]
    injected_anchor = INJECTION + ANCHOR
    if body.count(injected_anchor) != 1 or body.count(INJECTION) != 1:
        raise RuntimeError("succession projection must contain exactly one XAR injection")
    source = body.replace(injected_anchor, ANCHOR, 1)
    validate_native_source(source)
    if HEADER + render_source(source) != projection:
        raise RuntimeError("succession projection is not reversibly generated")
    return source


def main():
    OUTPUT.write_text(
        HEADER + render(),
        encoding="utf-8-sig",
        newline="\n",
    )
    print(f"generated {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
