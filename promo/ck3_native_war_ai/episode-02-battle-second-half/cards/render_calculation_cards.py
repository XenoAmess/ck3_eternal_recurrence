"""Render three source-bound Episode 2 folio cards as standalone SVG frames.

No CK3, recording, promo-toolchain, network, or compositor access is involved.
The output is a full-frame intertitle; its lower 320 px remain empty for subtitles.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "calculation-cards.json"
Q = 100_000
PALETTE = {
    "bg": "#211813",
    "panel": "#35291F",
    "ink": "#F0E5CF",
    "muted": "#BBA98D",
    "gold": "#CBA56A",
    "rule": "#61503C",
    "green": "#ABB582",
    "red": "#CA7962",
}
FONT = "Microsoft YaHei, Noto Sans CJK SC, sans-serif"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict) -> None:
    require(data["schema"] == "xar.war-ai.episode02.calculation-cards.v1", "schema")
    canvas = data["canvas"]
    require((canvas["width"], canvas["height"], canvas["subtitle_safe_top"]) ==
            (2560, 1440, 1120), "canvas and subtitle safe area")
    require(canvas["presentation"] == "standalone_full_frame_intertitle_not_gameplay_overlay",
            "cards must not cover gameplay UI")
    game = data["game"]
    require((game["combat_id"], game["war_id"], game["province_id"]) ==
            (16777218, 4, 2633), "game identity")
    require(len(game["exe_sha256"]) == 64, "EXE SHA")
    a, b = data["replays"]["085"], data["replays"]["024"]
    require(a["kind"] != b["kind"] and a["source_save_sha256"] != b["source_save_sha256"],
            "085 and 024 must remain separate replays")
    for replay, source_keys in ((a, ("source_save", "source_finish", "source_cleanup")),
                                (b, ("source_save", "source_terminal", "source_session_result"))):
        for source_key in source_keys:
            require(len(replay[source_key + "_sha256"]) == 64, f"{source_key} SHA")
    require(a["date_raw"] == 53146512 and a["joining_army_id"] == 22, "join identity")
    require(a["incoming_regiments"] == 13 and
            a["incoming_starting_people"] - a["zero_current_regiment_starting_people"] ==
            a["incoming_current_people"] == 2560, "incoming count/current")
    require(a["side0_before_cache_raw_q100000"] -
            a["side0_before_entry_sum_raw_q100000"] ==
            a["side0_cache_minus_entry_raw_q100000"], "side0 entry residual")
    require(a["side1_before_cache_raw_q100000"] -
            a["side1_before_entry_sum_raw_q100000"] ==
            a["side1_cache_minus_entry_raw_q100000"], "side1 entry residual")
    require(a["side0_before_entry_sum_raw_q100000"] +
            a["incoming_current_people"] * Q ==
            a["side0_after_cache_and_entry_raw_q100000"], "side0 after join")
    require(a["side1_before_entry_sum_raw_q100000"] ==
            a["side1_after_cache_and_entry_raw_q100000"], "side1 after join")
    post_total = (a["side0_after_cache_and_entry_raw_q100000"] +
                  a["side1_after_cache_and_entry_raw_q100000"])
    require(max(a["base_width_before"], post_total // (2 * Q)) ==
            a["base_width_after"] == 2467, "historical base width and new total")
    require(a["base_width_after"] * a["forest_width_multiplier_raw_q100000"] // Q ==
            a["final_width_after"] == a["first_side0_fire_width_argument"] == 2220,
            "final width and native fire argument")
    require(a["forest_multiplier_source"].endswith("not attempt-085 runtime field"),
            "forest multiplier source must stay explicit")
    require(b["terminal_kind"] == "normal_result" and b["winner_side"] == 0 and
            b["loser_side"] == 1 and b["loser_successor"] == "subject_retreating",
            "normal terminal identity")
    require(b["terminal_date_raw"] == 53146992 and b["start_date_raw"] == 53146872,
            "024 date identity")
    require(sum(b["denominator_buckets_people"]) == b["denominator_people"] == 996,
            "native denominator buckets")
    require(min(Q, b["hard_loss_numerator_raw_q100000"] // b["denominator_people"]) ==
            b["ratio_raw_q100000"] == 53877, "native integer ratio")
    require(b["ratio_raw_q100000"] * b["cb_scale_raw_q100000"] // Q ==
            b["uncapped_score_raw_q100000"] == 8081550, "CB score scale")
    require(min(b["uncapped_score_raw_q100000"],
                b["single_battle_cap_raw_q100000"]) ==
            b["row_magnitude_raw_q100000"] == 5000000, "one-battle cap")
    require(b["winner_is_war_attacker"] is False and
            b["war_attacker_relative_delta_raw_q100000"] ==
            -b["row_magnitude_raw_q100000"], "war attacker sign")
    require([row["id"] for row in data["cards"]] == ["E2-06", "E2-07", "E2-09"],
            "card order")


class Svg:
    def __init__(self) -> None:
        self.parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="2560" '
                      'height="1440" viewBox="0 0 2560 1440" role="img">',
                      '<!-- GENERATED FILE: edit calculation-cards.json or render_calculation_cards.py -->']

    def text(self, x: int, y: int, value: str, size: int = 36,
             color: str = "ink", weight: int = 400, anchor: str = "start") -> None:
        self.parts.append(
            f'<text x="{x}" y="{y}" fill="{PALETTE[color]}" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">'
            f'{html.escape(value)}</text>')

    def rect(self, x: int, y: int, width: int, height: int,
             fill: str = "panel", stroke: str = "rule", radius: int = 4) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
            f'fill="{PALETTE[fill]}" stroke="{PALETTE[stroke]}" stroke-width="2"/>')

    def line(self, x1: int, y1: int, x2: int, y2: int,
             color: str = "rule", width: int = 2) -> None:
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{PALETTE[color]}" stroke-width="{width}"/>')

    def finish(self) -> bytes:
        self.parts.append("</svg>")
        return ("\n".join(self.parts) + "\n").encode("utf-8")


def frame(s: Svg, card: dict, replay: dict, data: dict, subtitle: str) -> None:
    s.rect(0, 0, 2560, 1440, "bg", "bg", 0)
    s.line(64, 30, 2496, 30, "rule", 1)
    s.line(64, 30, 174, 30, "gold", 2)
    s.line(2386, 30, 2496, 30, "gold", 2)
    s.text(90, 105, f'战斗后半笔账  /  {card["id"]}', 32, "gold", 700)
    s.text(2470, 105, f'独立原版回放 {card["replay"]}', 31, "muted", anchor="end")
    s.text(90, 188, card["title"], 70, "ink", 700)
    s.text(92, 238, subtitle, 32, "muted")
    s.line(90, 255, 2470, 255, "rule", 2)
    s.line(90, 1022, 2470, 1022, "gold", 2)
    game = data["game"]
    date = replay.get("date_raw", replay.get("terminal_date_raw"))
    s.text(92, 1060, f'{game["version"]}  ·  CombatID {game["combat_id"]}  ·  WarID {game["war_id"]}  ·  原生日戳 {date}',
           27, "muted")
    sha = replay.get("source_finish_sha256", replay.get("source_terminal_sha256"))
    s.text(92, 1100, f'原始回执 SHA-256  {sha}', 23, "gold")
    # A standalone card is inserted between gameplay shots. No CK3 UI is covered.
    s.line(0, 1120, 2560, 1120, "gold", 2)


def card_06(data: dict, card: dict) -> bytes:
    a = data["replays"]["085"]
    s = Svg()
    frame(s, card, a, data, "同一 join wrapper 入口与返回；全部人数先换成 Q100000 原生量")
    s.rect(90, 284, 1138, 665)
    s.rect(1332, 284, 1138, 665)
    s.text(125, 340, "入场前：旧 entry 与缓存", 39, "gold", 700)
    s.line(125, 360, 1193, 360)
    s.text(125, 415, "side 0 · 27 条旧 entry", 32, "muted")
    s.text(125, 472, "缓存     160,317,482", 43)
    s.text(125, 532, "entry 和 154,690,163", 43)
    s.text(125, 625, "差 5,627,319", 74, "gold", 700)
    s.text(125, 677, "Q100000 = 56.27319 人当量", 31, "muted")
    s.line(125, 713, 1193, 713)
    s.text(125, 770, "side 1 · 24 条旧 entry", 32, "muted")
    s.text(125, 835, "89,325,449 − 82,785,368", 40)
    s.text(125, 905, "差 6,540,081  = 65.40081 人当量", 37, "gold")
    s.text(1367, 340, "入场后：新军按 current 入账", 39, "gold", 700)
    s.line(1367, 360, 2435, 360)
    s.text(1367, 418, "ArmyID 22 · 13 团", 36, "muted")
    s.text(1367, 518, "2,570 → 2,560", 80, "ink", 700)
    s.text(1367, 566, "起始基础人数       实际 current 人数", 28, "muted")
    s.text(1367, 628, "RegimentID 177：起始 10，当前 0", 33)
    s.line(1367, 670, 2435, 670)
    s.text(1367, 725, "旧 side 0 entry      154,690,163", 35)
    s.text(1367, 780, "+ 新军 current       256,000,000", 35)
    s.text(1367, 845, "= 返回缓存 410,690,163", 50, "gold", 700)
    s.text(1367, 914, "side 1 返回 82,785,368；双方残差归零", 30, "muted")
    s.text(95, 996, "这次已发生的入场账；不预测下一支援军的到达日期。", 29, "muted")
    return s.finish()


def card_07(data: dict, card: dict) -> bytes:
    a = data["replays"]["085"]
    s = Svg()
    frame(s, card, a, data, "085 自己捕获 join 前、join 后、首次 side 0 出伤三点")
    panels = [(90, "入口 · phase day 7", "历史 base", "1,645", "final  1,480"),
              (895, "返回 · phase day 7", "更新 base", "2,467", "final  2,220"),
              (1700, "首次出伤 · day 8", "R8D 实参", "2,220", "= 存储 final")]
    for x, heading, label, value, secondary in panels:
        s.rect(x, 292, 770, 455)
        s.text(x + 38, 354, heading, 34, "gold", 700)
        s.line(x + 38, 378, x + 732, 378)
        s.text(x + 38, 447, label, 34, "muted")
        s.text(x + 38, 587, value, 112, "ink", 700)
        s.text(x + 38, 675, secondary, 42, "gold")
    s.rect(90, 788, 2380, 165)
    s.text(130, 850, "返回参战量  (410,690,163 + 82,785,368) ÷ 100,000 ÷ 2", 39)
    s.text(130, 922, "向下取整 → 2,467；森林 0.9 → 2,220", 53, "gold", 700)
    s.text(95, 997, "0.9 来自同版本原版森林脚本；085 未读到同帧运行时地形倍率。", 28, "muted")
    return s.finish()


def card_09(data: dict, card: dict) -> bytes:
    b = data["replays"]["024"]
    s = Svg()
    frame(s, card, b, data, "另一次第 27→32 日回放；原生 writer 当场读取，非 UI 封顶值倒推")
    widths = [(90, 730), (870, 730), (1650, 820)]
    for x, width in widths:
        s.rect(x, 284, width, 665)
    s.text(125, 342, "败方输入", 40, "gold", 700)
    s.line(125, 364, 785, 364)
    s.text(125, 421, "单场起始 1,298 人", 34, "muted")
    s.text(125, 507, "硬伤分子", 33)
    s.text(125, 603, "536.62042", 72, "ink", 700)
    s.text(125, 659, "人当量", 32, "muted")
    s.line(125, 698, 785, 698)
    s.text(125, 752, "八桶战争分母", 33)
    s.text(125, 828, "996 人", 71, "gold", 700)
    s.text(125, 888, "0+675+310+0+0+0+11+0", 29, "muted")
    s.text(905, 342, "整数计算", 40, "gold", 700)
    s.line(905, 364, 1565, 364)
    s.text(905, 424, "53,662,042 Q100000 ÷ 996 人", 31)
    s.text(905, 502, "= 53,877 / 100,000", 44, "ink", 700)
    s.text(905, 562, "= 53.877%", 37, "muted")
    s.line(905, 602, 1565, 602)
    s.text(905, 669, "CB 战分倍率 150", 40)
    s.text(905, 757, "未封顶", 33, "muted")
    s.text(905, 851, "80.8155", 75, "gold", 700)
    s.text(905, 910, "战分", 30, "muted")
    s.text(1685, 342, "正常终局 · 单场封顶", 40, "gold", 700)
    s.line(1685, 364, 2435, 364)
    s.text(1685, 431, "min(80.8155, 50)", 40)
    s.text(1685, 575, "50", 150, "ink", 700)
    s.text(1685, 628, "row 正幅度", 33, "muted")
    s.line(1685, 673, 2435, 673)
    s.text(1685, 735, "胜者：战争防守方", 37)
    s.text(1685, 831, "进攻方相对战分", 35, "muted")
    s.text(1685, 927, "−50", 97, "gold", 700)
    s.text(95, 997, "一场战斗的 row；不等于战争总分。败方为正常败退，并非主动撤退证据。", 28, "muted")
    return s.finish()


RENDERERS = {"E2-06": card_06, "E2-07": card_07, "E2-09": card_09}


def verify_sources(data: dict) -> None:
    sources = (("085", ("source_save", "source_finish", "source_cleanup")),
               ("024", ("source_save", "source_terminal", "source_session_result")))
    for key, fields in sources:
        replay = data["replays"][key]
        for field in fields:
            path = Path(replay[field])
            require(path.is_file(), f"source missing: {path}")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            require(digest.hexdigest().upper() == replay[field + "_sha256"],
                    f"source SHA mismatch: replay {key}, {field}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated SVG bytes with checked-in files")
    parser.add_argument("--verify-sources", action="store_true", help="Verify the two preserved raw receipt SHA-256 values")
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    validate(data)
    if args.verify_sources:
        verify_sources(data)
    for card in data["cards"]:
        path = ROOT / f'{card["id"].lower()}-calculation.svg'
        rendered = RENDERERS[card["id"]](data, card)
        if args.check:
            require(path.is_file() and path.read_bytes() == rendered,
                    f"generated SVG differs: {path}")
        else:
            path.write_bytes(rendered)
        print(f'{card["id"]}: {path.name} sha256={hashlib.sha256(rendered).hexdigest().upper()}')


if __name__ == "__main__":
    main()
