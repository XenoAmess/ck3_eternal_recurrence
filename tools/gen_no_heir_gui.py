from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Crusader Kings III/game/gui/window_succession_event.gui"
OUTPUT = ROOT / "XenoAmess_s_Eternal_Recurrence/gui/window_succession_event.gui"
ANCHOR = '\n}\n\n\nwindow = {\n\tname = "succession_select_destiny_window"'
INJECTION = '\n\txar_no_heir_settlement_widget = {}\n'


def render():
    source = SOURCE.read_text(encoding="utf-8-sig")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("native succession window anchor changed")
    return source.replace(ANCHOR, INJECTION + ANCHOR, 1)


def main():
    OUTPUT.write_text(
        "# GENERATED FILE - native 1.19 succession window plus XAR no-heir widget\n"
        + render(),
        encoding="utf-8-sig",
        newline="\n",
    )
    print(f"generated {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
