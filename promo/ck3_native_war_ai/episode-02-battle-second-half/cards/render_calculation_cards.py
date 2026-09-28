"""Render source-bound Episode 2 folio cards as standalone SVG frames.

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
SOURCE_FIELDS = {
    "004": ("source_save", "source_capture_report", "source_day27_checkpoint",
            "source_index", "source_day28_control",
            "source_day29_control", "source_day30_control", "source_day31_control",
            "source_day32_terminal"),
    "039_040": ("source_day5_finish", "source_day6_save", "source_day6_v3"),
    "020": ("source_save", "source_finish"),
    "070": ("source_save", "source_finish"),
    "036_038": ("source_day26_finish", "source_day27_save", "source_day27_v3",
                "source_day27_capture_report"),
    "085": ("source_save", "source_finish", "source_cleanup"),
    "024": ("source_save", "source_terminal", "source_session_result"),
    "A05": ("source_save", "source_preflight", "source_start_readback",
            "source_terminal", "source_post_snapshot", "source_observe",
            "source_same_recorder_verify",
            "source_recorder_final"),
}


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
    replays = data["replays"]
    a, b = replays["085"], replays["024"]
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
    live = replays["A05"]
    require(live["kind"] == "new_paired_live_run_from_004_day27_checkpoint" and
            live["source_save_sha256"] == pursuit_save_sha(replays) and
            live["source_terminal_sha256"] != b["source_terminal_sha256"],
            "A05 checkpoint relation and independent writer")
    require(live["terminal_kind"] == "normal_result" and
            (live["winner_side"], live["loser_side"], live["loser_successor"]) ==
            (0, 1, "subject_retreating") and
            (live["start_date_raw"], live["terminal_date_raw"]) ==
            (53146872, 53146992), "A05 terminal identity")
    require(live["loser_baseline_raw_q100000"] -
            live["loser_stored_current_raw_q100000"] -
            live["loser_levy_soft_raw_q100000"] -
            live["loser_men_at_arms_soft_raw_q100000"] ==
            live["hard_loss_numerator_raw_q100000"], "A05 hard-loss inputs")
    require(sum(live["denominator_buckets_people"]) ==
            live["denominator_people"] == 996, "A05 native denominator buckets")
    require(min(Q, live["hard_loss_numerator_raw_q100000"] //
                live["denominator_people"]) == live["ratio_raw_q100000"] == 53877,
            "A05 integer ratio")
    require(live["ratio_raw_q100000"] * live["cb_scale_raw_q100000"] // Q ==
            live["uncapped_score_raw_q100000"] == 8081550,
            "A05 uncapped CB score")
    require(min(live["uncapped_score_raw_q100000"],
                live["single_battle_cap_raw_q100000"]) ==
            live["row_magnitude_raw_q100000"] == 5000000 and
            live["winner_is_war_attacker"] is False and
            live["war_attacker_relative_delta_raw_q100000"] ==
            -live["row_magnitude_raw_q100000"] and
            live["post_snapshot_player_relative_war_score"] == -50,
            "A05 capped row, war sign, and poststate")
    require(live["media_status"] == "ENCODED_UNREVIEWED" and
            len(live["raw_video_sha256_reported_by_recorder"]) == 64,
            "A05 media scope")
    pursuit = replays["004"]
    require(pursuit["source_index_sha256"] == pursuit["primary_receipt_sha256"],
            "004 original index binding")
    require(pursuit["date_raw"] == 53146896 and pursuit["pursuit_begin_day"] == 28 and
            pursuit["retreater_regiments"] == 24, "004 pursuit identity")
    require(pursuit["levy_soft_pool_raw_q100000"] +
            pursuit["men_at_arms_soft_pool_raw_q100000"] ==
            pursuit["total_soft_pool_raw_q100000"] == 82432227,
            "004 initial soft pool")
    require(pursuit["pursuit_damage_raw_q100000"] == 75203000 and
            pursuit["retreater_screen_raw_q100000"] == 0,
            "004 pursuit and observed zero loser screen")
    require(pursuit["daily_hard_raw_q100000"] == [2070677, 2097473, 2126119] and
            sum(pursuit["daily_hard_raw_q100000"]) ==
            pursuit["total_hard_raw_q100000"] == 6294269,
            "004 three-day hard loss")
    require(pursuit["daily_toughness_soft_raw_q100000"] ==
            [1489459979, 1452047877, 1414150820], "004 shrinking toughness-soft")
    require((pursuit["exact_soft_rows"], pursuit["exact_hard_rows"],
             pursuit["stable_current_rows"], pursuit["unreadable_hard_rows"]) ==
            (72, 69, 72, 3), "004 native comparable rows")
    require(pursuit["terminal_kind"] == "normal_result" and
            pursuit["terminal_winner_side"] == 0, "004 terminal identity")
    maim = replays["039_040"]
    require(maim["source_day5_finish_sha256"] == maim["primary_receipt_sha256"] and
            maim["source_day6_save_sha256"] ==
            "9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A",
            "039 to 040 same saved bytes")
    require((maim["character_id"], maim["opponent_id"], maim["regiment_id"]) ==
            (34333, 47032, 61) and maim["new_traits"] ==
            ["one_legged", "wounded_1"], "maim event identity")
    require(maim["knights_before_after"] == [24, 24] and
            maim["regiments_before_after"] == [51, 51] and
            maim["regiment_current_before_after"] == [1, 1] and
            maim["base_prowess_before_after"] == [3, 3], "maimed knight remains")
    require(maim["effective_prowess_before_after"] == [11, 7] and
            maim["effectiveness_raw_q100000"] == 175000 and
            maim["damage_raw_q100000_before_after"] ==
            [p * maim["effectiveness_raw_q100000"] * 50
             for p in maim["effective_prowess_before_after"]] and
            maim["toughness_raw_q100000_before_after"] ==
            [p * maim["effectiveness_raw_q100000"] * 10
             for p in maim["effective_prowess_before_after"]] and
            maim["opponent_prestige_delta"] == 150, "039 to 040 effective stat math")
    killer = replays["020"]
    require(killer["source_finish_sha256"] == killer["primary_receipt_sha256"] and
            killer["source_knights"] == 19 and killer["eligible_candidates"] == 14 and
            killer["selector_draw31"] % killer["eligible_candidates"] ==
            killer["selected_index_zero_based"] == 8, "020 native unweighted draw")
    require((killer["event_load_index"], killer["selected_killer_character_id"],
             killer["killed_character_id"], killer["killed_regiment_id"]) ==
            (11, 34120, 33437, 65), "020 killer/victim identity")
    require(killer["victim_base_prowess_before_after"] == [2, 2] and
            killer["victim_effective_prowess_before_after"] == [4, 2] and
            killer["killer_prestige_delta"] == 150 and
            killer["full_effect_write_set_proven"] is False,
            "020 narrow writeback boundary")
    growth = replays["070"]
    require(growth["source_finish_sha256"] == growth["primary_receipt_sha256"] and
            growth["source_save_sha256"] == killer["source_save_sha256"],
            "070 same input save, independent replay")
    require(growth["runtime_growth_weights"] == [40, 30, 15] and
            sum(growth["runtime_growth_weights"]) == growth["positive_weight_total"] == 85 and
            growth["selection_draw31"] * growth["positive_weight_total"] // (1 << 31) ==
            growth["threshold"] == 2 and growth["selected_source_order_index"] == 0 and
            growth["selected_branch"] == "no_op" and
            growth["selected_killer_character_id"] == 34120 and
            growth["full_effect_write_set_proven"] is False,
            "070 runtime growth choice")
    next_roster = replays["036_038"]
    require(next_roster["source_day26_finish_sha256"] ==
            next_roster["primary_receipt_sha256"] and
            next_roster["source_day27_save_sha256"] ==
            "CD0648D7603290E470ED07261128C05FF449C0FFAEA89D01A1102D0D56208A55",
            "036 to 038 exact post-save identity")
    require(next_roster["source_day26_finish_sha256"] !=
            growth["source_finish_sha256"] and
            next_roster["source_day27_save_sha256"] !=
            killer["source_save_sha256"], "independent knight tracks")
    require(next_roster["regiments_before_after"] == [69, 68] and
            next_roster["knights_before_after"] == [30, 29] and
            (next_roster["victim_character_id"], next_roster["removed_regiment_id"]) ==
            (33437, 65) and next_roster["other_base_inputs_identical"] is True and
            next_roster["full_mutable_write_set_proven"] is False,
            "036 to 038 narrow roster readback")
    for key in ("004", "039_040", "020", "070", "036_038"):
        for field in SOURCE_FIELDS[key]:
            require(len(replays[key][field + "_sha256"]) == 64,
                    f"{key} {field} SHA")
    require([row["id"] for row in data["cards"]] ==
            ["E2-02", "E2-03", "E2-04", "E2-05A", "E2-05B", "E2-05C",
             "E2-06", "E2-07", "E2-09"] and
            data["cards"][-1]["replay"] == "A05" and
            data["cards"][-1]["artifact"] == "e2-09-a05-calculation.svg",
            "card order")
    historical = data["historical_cards"]
    require(len(historical) == 1 and historical[0]["id"] == "E2-09" and
            historical[0]["replay"] == "024" and
            historical[0]["artifact"] == "e2-09-calculation.svg" and
            historical[0]["sha256"] ==
            "1A9EDC4CAEDC662F2F3AA44925CE1C8F7493A154273A78B258D8C020F2F5DE31",
            "024 historical card remains archived")


def pursuit_save_sha(replays: dict) -> str:
    return replays["004"]["source_day27_checkpoint_sha256"]


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
    s.text(2470, 105, f'独立原版回放 {card.get("source_label", card["replay"])}',
           31, "muted", anchor="end")
    s.text(90, 188, card["title"], 70, "ink", 700)
    s.text(92, 238, subtitle, 32, "muted")
    s.line(90, 255, 2470, 255, "rule", 2)
    s.line(90, 1022, 2470, 1022, "gold", 2)
    game = data["game"]
    date = replay.get("date_raw", replay.get("terminal_date_raw"))
    s.text(92, 1060, f'{game["version"]}  ·  CombatID {game["combat_id"]}  ·  WarID {game["war_id"]}  ·  原生日戳 {date}',
           27, "muted")
    sha = replay.get("primary_receipt_sha256",
                     replay.get("source_finish_sha256", replay.get("source_terminal_sha256")))
    s.text(92, 1100, f'原始回执 SHA-256  {sha}', 23, "gold")
    # A standalone card is inserted between gameplay shots. No CK3 UI is covered.
    s.line(0, 1120, 2560, 1120, "gold", 2)


def scaled(raw: int) -> str:
    return f"{raw // Q:,}.{raw % Q:05d}"


def scaled_compact(raw: int) -> str:
    return scaled(raw).rstrip("0").rstrip(".")


def card_02(data: dict, card: dict) -> bytes:
    a = data["replays"]["004"]
    s = Svg()
    frame(s, card, a, data, "004 第 28 日单帧起算；败方掩护聚合为 0 的条件样本")
    s.rect(90, 284, 1138, 665)
    s.rect(1332, 284, 1138, 665)
    s.text(125, 344, "败方 · 24 团软伤池", 40, "gold", 700)
    s.line(125, 368, 1193, 368)
    s.text(125, 447, f'征召兵 soft    {a["levy_soft_pool_raw_q100000"]:,}', 42)
    s.text(125, 522, f'兵士 soft      {a["men_at_arms_soft_pool_raw_q100000"]:,}', 42)
    s.line(125, 572, 1193, 572)
    s.text(125, 664, f'合计 {a["total_soft_pool_raw_q100000"]:,}', 65, "ink", 700)
    s.text(125, 730, f'= {scaled(a["total_soft_pool_raw_q100000"])} 人当量', 42, "gold")
    s.text(125, 836, "这是第 28 日冻结输入，不是三日损失。", 31, "muted")
    s.text(1367, 344, "追击方 · 当日中间账", 40, "gold", 700)
    s.line(1367, 368, 2435, 368)
    s.text(1367, 445, "追击伤害原始值", 34, "muted")
    s.text(1367, 536, f'{a["pursuit_damage_raw_q100000"]:,}', 74, "ink", 700)
    s.text(1367, 606, f'败方有效掩护聚合  {a["retreater_screen_raw_q100000"]}',
           39, "gold")
    s.line(1367, 647, 2435, 647)
    s.text(1367, 712, f'首日 toughness-soft  {a["daily_toughness_soft_raw_q100000"][0]:,}',
           33)
    s.text(1367, 780, f'首日软转硬  {a["daily_hard_raw_q100000"][0]:,}',
           47, "gold", 700)
    s.text(1367, 842, "逐团比例分配后再处理余数；无追击抽签结论。", 28, "muted")
    s.text(95, 997, "只验证这次给定初态的条件计算；非零败方掩护仍待原版同帧取样。", 29, "muted")
    return s.finish()


def card_03(data: dict, card: dict) -> bytes:
    a = data["replays"]["004"]
    s = Svg()
    frame(s, card, a, data, "004 同一独立回放；第 29/30 日不重新喂入原版败方状态")
    for i, x in enumerate((90, 895, 1700)):
        start_day = 28 + i
        s.rect(x, 290, 770, 615)
        s.text(x + 36, 356, f'第 {start_day} → {start_day + 1} 日',
               42, "gold", 700)
        s.line(x + 36, 382, x + 734, 382)
        s.text(x + 36, 453, "toughness-soft", 35, "muted")
        s.text(x + 36, 515, f'{a["daily_toughness_soft_raw_q100000"][i]:,}', 42)
        s.text(x + 36, 625, f'{scaled(a["daily_hard_raw_q100000"][i])}',
               92, "ink", 700)
        s.text(x + 36, 682, "人当量 soft → hard", 33, "gold")
        s.line(x + 36, 724, x + 734, 724)
        s.text(x + 36, 783, "soft 24/24 零差", 32)
        s.text(x + 36, 841, "可读 hard 23/23 零差", 30)
    s.text(95, 972, f'三日合计 {scaled(a["total_hard_raw_q100000"])} 人当量',
           51, "gold", 700)
    s.text(1200, 973, "72/72 soft · 69/69 可读 hard · 72/72 current 不变", 32)
    s.text(95, 1007, "另有 1 团/日 hard 原始字段为 null，不得按零计。", 27, "muted")
    return s.finish()


def card_04(data: dict, card: dict) -> bytes:
    a = data["replays"]["039_040"]
    s = Svg()
    frame(s, card, a, data, "039 事件写回；040 逐字节复载 039 后档，不推进日期")
    s.rect(90, 284, 1138, 665)
    s.rect(1332, 284, 1138, 665)
    s.text(125, 345, "第 5 日 · 原生事件", 40, "gold", 700)
    s.line(125, 367, 1193, 367)
    s.text(125, 440, f'目标骑士 CharacterID {a["character_id"]}', 38)
    s.text(125, 507, f'对手 {a["opponent_id"]} · 威望 +{a["opponent_prestige_delta"]}',
           39)
    s.text(125, 606, "独腿 + 轻伤", 72, "ink", 700)
    s.text(125, 674, f'骑士 {a["knights_before_after"][0]} → {a["knights_before_after"][1]}；'
           f'61 号团人数 {a["regiment_current_before_after"][0]} → '
           f'{a["regiment_current_before_after"][1]}', 35, "gold")
    s.text(125, 780, f'基础勇武 {a["base_prowess_before_after"][0]} → '
           f'{a["base_prowess_before_after"][1]}，未被扣四点。', 35, "muted")
    s.text(1367, 345, "第 6 日 · 智能体原生输入", 40, "gold", 700)
    s.line(1367, 367, 2435, 367)
    s.text(1367, 442, f'有效勇武 {a["effective_prowess_before_after"][0]} → '
           f'{a["effective_prowess_before_after"][1]}', 52, "ink", 700)
    s.text(1367, 510, "骑士效能仍为 1.75", 35, "muted")
    s.text(1367, 605, "有效伤害", 35, "muted")
    s.text(1367, 684, f'{scaled_compact(a["damage_raw_q100000_before_after"][0])} → '
           f'{scaled_compact(a["damage_raw_q100000_before_after"][1])}', 55, "gold", 700)
    s.text(1367, 763, "有效坚韧", 35, "muted")
    s.text(1367, 842, f'{scaled_compact(a["toughness_raw_q100000_before_after"][0])} → '
           f'{scaled_compact(a["toughness_raw_q100000_before_after"][1])}', 55, "gold", 700)
    s.text(95, 996, f'040 原生 v3 SHA-256  {a["source_day6_v3_sha256"]}', 23, "muted")
    return s.finish()


def card_05a(data: dict, card: dict) -> bytes:
    a = data["replays"]["020"]
    s = Svg()
    frame(s, card, a, data, "020 独立回放；无权重选择器，候选按原生尾项填洞顺序排列")
    s.rect(90, 284, 1138, 665)
    s.rect(1332, 284, 1138, 665)
    s.text(125, 345, "事件载入索引 11 · knight_killed", 38, "gold", 700)
    s.line(125, 367, 1193, 367)
    s.text(125, 457, f'来源骑士  {a["source_knights"]}', 54)
    s.text(125, 570, f'过勇武门槛  {a["eligible_candidates"]}',
           72, "ink", 700)
    s.text(125, 644, "被筛掉者用尾项填洞；不可稳定删除。", 32, "muted")
    s.line(125, 702, 1193, 702)
    s.text(125, 768, "这是击杀者选择，不是成长列表抽签。", 31)
    s.text(1367, 345, "局部 RNG 与原版战报", 40, "gold", 700)
    s.line(1367, 367, 2435, 367)
    s.text(1367, 471, f'{a["selector_draw31"]:,} % '
           f'{a["eligible_candidates"]} = {a["selected_index_zero_based"]}',
           57, "ink", 700)
    s.text(1367, 566, f'索引 8 → 击杀者 {a["selected_killer_character_id"]}',
           59, "gold", 700)
    s.text(1367, 654, f'阵亡 {a["killed_character_id"]} · '
           f'兵团 {a["killed_regiment_id"]} 脱团', 43)
    s.text(1367, 735, f'击杀者威望 +{a["killer_prestige_delta"]}', 39)
    s.text(1367, 835, "死者基础勇武 2→2；有效勇武 4→2", 34, "muted")
    s.text(95, 996, "只证本次选择与狭窄写回；020 不是 070 或 036→038 的同一次回放。", 28, "muted")
    return s.finish()


def card_05b(data: dict, card: dict) -> bytes:
    a = data["replays"]["070"]
    s = Svg()
    frame(s, card, a, data, "070 另一次第 26 日回放；实际运行时权重由原生入口直接采得")
    panels = ((90, "运行时权重", "40 / 30 / 15", "正权重合计 85"),
              (895, "子作用域抽签", "51,510,340", "阈值 floor(draw × 85 / 2³¹) = 2"),
              (1700, "执行来源第 0 项", "no_op", "本次未加基础勇武"))
    for x, heading, value, explanation in panels:
        s.rect(x, 292, 770, 600)
        s.text(x + 36, 360, heading, 39, "gold", 700)
        s.line(x + 36, 385, x + 734, 385)
        s.text(x + 36, 585, value, 73 if x != 1700 else 103, "ink", 700)
        s.text(x + 36, 685, explanation, 30, "muted")
    s.text(95, 969, f'本次击杀者 {a["selected_killer_character_id"]}；'
           "选择器与成长列表各用自己的 draw。", 36, "gold")
    s.text(95, 1008, "070 与 020/036 均为独立运行；038 并未复载 070 的后存档。", 27, "muted")
    return s.finish()


def card_05c(data: dict, card: dict) -> bytes:
    a = data["replays"]["036_038"]
    s = Svg()
    frame(s, card, a, data, "036 保存第 27 日不可变后档；038 只读复载同一份 bytes")
    s.rect(90, 284, 1138, 610)
    s.rect(1332, 284, 1138, 610)
    s.text(125, 350, "第 26 日事件前 · 036 源档", 38, "gold", 700)
    s.line(125, 375, 1193, 375)
    s.text(125, 488, f'{a["regiments_before_after"][0]} 团', 91, "ink", 700)
    s.text(125, 631, f'{a["knights_before_after"][0]} 名骑士', 82, "ink", 700)
    s.text(125, 770, "036 触发事件后保存不可变后档。", 32, "muted")
    s.text(1367, 350, "第 27 日暂停输入 · 038", 41, "gold", 700)
    s.line(1367, 375, 2435, 375)
    s.text(1367, 488, f'{a["regiments_before_after"][1]} 团', 91, "gold", 700)
    s.text(1367, 631, f'{a["knights_before_after"][1]} 名骑士', 82, "gold", 700)
    s.text(1367, 770, f'缺骑士 {a["victim_character_id"]} / 团 '
           f'{a["removed_regiment_id"]}', 40)
    s.text(95, 941, f'036 后存档 SHA-256  {a["source_day27_save_sha256"]}', 23, "muted")
    s.text(95, 993, f'038 原生 v3 SHA-256  {a["source_day27_v3_sha256"]}', 23, "muted")
    return s.finish()


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
    b = data["replays"][card["replay"]]
    s = Svg()
    subtitle = ("A05 新独立冷载第 27 日检查点；第 32 日 writer 与同录制器后态"
                if card["replay"] == "A05" else
                "历史研究板：024 第 27→32 日独立回放；本板不是新拍 run 的读数")
    frame(s, card, b, data, subtitle)
    widths = [(90, 730), (870, 730), (1650, 820)]
    for x, width in widths:
        s.rect(x, 284, width, 665)
    s.text(125, 342, "败方输入", 40, "gold", 700)
    s.line(125, 364, 785, 364)
    s.text(125, 421, f'单场起始 {scaled_compact(b["loser_baseline_raw_q100000"])} 人', 34, "muted")
    s.text(125, 507, "硬伤分子", 33)
    s.text(125, 603, scaled(b["hard_loss_numerator_raw_q100000"]), 72, "ink", 700)
    s.text(125, 659, "人当量", 32, "muted")
    s.line(125, 698, 785, 698)
    s.text(125, 752, "八桶战争分母", 33)
    s.text(125, 828, f'{b["denominator_people"]} 人', 71, "gold", 700)
    s.text(125, 888, "+".join(map(str, b["denominator_buckets_people"])), 29, "muted")
    s.text(905, 342, "整数计算", 40, "gold", 700)
    s.line(905, 364, 1565, 364)
    s.text(905, 424, f'{b["hard_loss_numerator_raw_q100000"]:,} Q100000 ÷ {b["denominator_people"]} 人', 31)
    s.text(905, 502, f'= {b["ratio_raw_q100000"]:,} / 100,000', 44, "ink", 700)
    s.text(905, 562, f'= {b["ratio_raw_q100000"] / 1000:g}%', 37, "muted")
    s.line(905, 602, 1565, 602)
    s.text(905, 669, f'CB 战分系数 {scaled_compact(b["cb_scale_raw_q100000"])}', 40)
    s.text(905, 757, "未封顶", 33, "muted")
    s.text(905, 851, scaled_compact(b["uncapped_score_raw_q100000"]), 75, "gold", 700)
    s.text(905, 910, "战分", 30, "muted")
    s.text(1685, 342, "正常终局 · 单场封顶", 40, "gold", 700)
    s.line(1685, 364, 2435, 364)
    s.text(1685, 431, f'min({scaled_compact(b["uncapped_score_raw_q100000"])}, '
           f'{scaled_compact(b["single_battle_cap_raw_q100000"])})', 40)
    s.text(1685, 575, scaled_compact(b["row_magnitude_raw_q100000"]), 150, "ink", 700)
    s.text(1685, 628, "row 正幅度", 33, "muted")
    s.line(1685, 673, 2435, 673)
    s.text(1685, 735, "胜者：战争防守方", 37)
    s.text(1685, 831, "进攻方相对战分", 35, "muted")
    s.text(1685, 927, f'−{scaled_compact(-b["war_attacker_relative_delta_raw_q100000"])}', 97, "gold", 700)
    footer = ("A05 原生单场 row −50；同 run 第 32 日暂停后态总分 −50；录制仍待人工审阅。"
              if card["replay"] == "A05" else
              "仅对应历史 024 的单场 row；新拍镜头须另取同 run writer 与战争面板回执。")
    s.text(95, 997, footer, 28, "muted")
    return s.finish()


RENDERERS = {
    "E2-02": card_02, "E2-03": card_03, "E2-04": card_04,
    "E2-05A": card_05a, "E2-05B": card_05b, "E2-05C": card_05c,
    "E2-06": card_06, "E2-07": card_07, "E2-09": card_09,
}


def verify_sources(data: dict) -> None:
    checked = {}
    for key, fields in SOURCE_FIELDS.items():
        replay = data["replays"][key]
        for field in fields:
            path = Path(replay[field])
            require(path.is_file(), f"source missing: {path}")
            if path not in checked:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                checked[path] = digest.hexdigest().upper()
            require(checked[path] == replay[field + "_sha256"],
                    f"source SHA mismatch: replay {key}, {field}")
    verify_a05_sources(data["replays"]["A05"])


def verify_a05_sources(a: dict) -> None:
    """Check source semantics after the byte hashes; never decode the raw video."""
    preflight = json.loads(Path(a["source_preflight"]).read_text(encoding="utf-8"))
    start = json.loads(Path(a["source_start_readback"]).read_text(encoding="utf-8"))
    writer = json.loads(Path(a["source_terminal"]).read_text(encoding="utf-8"))
    post = json.loads(Path(a["source_post_snapshot"]).read_text(encoding="utf-8"))
    observe = json.loads(Path(a["source_observe"]).read_text(encoding="utf-8"))
    verify = json.loads(Path(a["source_same_recorder_verify"]).read_text(encoding="utf-8"))
    recorder = json.loads(Path(a["source_recorder_final"]).read_text(encoding="utf-8"))
    require(preflight["result"] == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            preflight["checkpoint_source"]["save"]["sha256"] ==
            a["source_save_sha256"] and
            start["postcondition_verified"] is True and
            start["source_checkpoint"]["save"]["sha256"] ==
            a["source_save_sha256"] and
            start["snapshot"]["date_raw"] == a["start_date_raw"] and
            start["snapshot"]["played_character"]["character_id"] == 29829,
            "A05 independent cold-load readback")
    require(writer["result"] == "CALL_COMPLETED" and
            writer["body"]["status"] == "available" and
            writer["body"]["battle_terminal_transition_ready"] is True,
            "A05 writer response")
    transition = writer["body"]["battle_terminal_transition"]
    prior = transition["prior"]
    hard = prior["hard_loss_inputs"]
    row = prior["battle_warscore"]
    denom = row["denominator_inputs"]
    require((transition["prior_combat_id"], transition["subject_public_cunit_id"],
             transition["observed_date_raw"], prior["province_id"],
             prior["terminal_kind"], prior["winner_raw"],
             transition["successor"]["state"]) ==
            (16777218, 18, a["terminal_date_raw"], 2633, "normal_result", 0,
             "subject_retreating"), "A05 writer terminal identity")
    require((hard["losing_side_index"], hard["baseline_raw"],
             hard["stored_current_raw"], hard["levy_soft_raw"],
             hard["men_at_arms_soft_raw"], hard["hard_loss_raw"]) ==
            (1, a["loser_baseline_raw_q100000"],
             a["loser_stored_current_raw_q100000"],
             a["loser_levy_soft_raw_q100000"],
             a["loser_men_at_arms_soft_raw_q100000"],
             a["hard_loss_numerator_raw_q100000"]), "A05 writer hard-loss fields")
    require(denom["sum_int32"] == denom["after_minimum_int32"] ==
            a["denominator_people"] and
            denom["participants"] == [
                {"character_id": 29829,
                 "buckets_native_add_order_int32": a["denominator_buckets_people"]}],
            "A05 writer denominator fields")
    require((row["status"], row["war_id"], row["war_battle_row_index"],
             row["value_raw_q100000"], row["winner_is_war_attacker"],
             row["attacker_relative_delta_raw_q100000"],
             row["selected_cb_battle_scale_raw_q100000"]) ==
            ("recorded", 4, 0, a["row_magnitude_raw_q100000"], False,
             a["war_attacker_relative_delta_raw_q100000"],
             a["cb_scale_raw_q100000"]), "A05 writer battle row")
    require(post["result"] == "CALL_COMPLETED" and
            post["body"]["date_raw"] == a["terminal_date_raw"] and
            post["body"]["paused"] is True and
            post["body"]["played_character"]["character_id"] == 29829,
            "A05 pause poststate")
    wars = [w for w in post["body"]["active_wars"] if w["war_id"] == 4]
    require(len(wars) == 1 and wars[0]["player_side"] == "attacker" and
            wars[0]["player_relative_war_score"] ==
            a["post_snapshot_player_relative_war_score"] and
            any(army["army_id"] == 18 and army["retreating"] is True and
                army["in_combat"] is False for army in wars[0]["allied_armies"]),
            "A05 WarID 4 score and ArmyID 18 successor")
    require(observe["native_response"]["sha256"] ==
            a["source_terminal_sha256"] and
            observe["snapshot"]["sha256"] ==
            a["source_post_snapshot_sha256"] and
            verify["observed"]["sha256"] ==
            a["source_observe_sha256"] and
            verify["mark"]["response_sha256"] ==
            a["source_terminal_sha256"] and
            verify["status"] == "same-recorder-terminal-mark-bound-unreviewed" and
            (verify["day"], verify["date_raw"]) == (32, a["terminal_date_raw"]),
            "A05 same-recorder writer/poststate binding")
    raw = recorder["raw"]
    require(recorder["result"] == a["media_status"] == "ENCODED_UNREVIEWED" and
            recorder["clean_spans_certified"] is False and
            recorder["human_review_completed"] is False and
            recorder["video_pts_complete"] is True and
            raw["path"] == verify["recorder_gate"]["raw_path"] and
            raw["sha256"] == a["raw_video_sha256_reported_by_recorder"] and
            Path(raw["path"]).stat().st_size == raw["bytes"],
            "A05 raw recorder identity and unreviewed boundary")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated SVG bytes with checked-in files")
    parser.add_argument("--verify-sources", action="store_true", help="Verify all preserved raw source SHA-256 values")
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    validate(data)
    if args.verify_sources:
        verify_sources(data)
    archived = data["historical_cards"][0]
    archive_path = ROOT / archived["artifact"]
    require(archive_path.is_file() and
            hashlib.sha256(archive_path.read_bytes()).hexdigest().upper() ==
            archived["sha256"], "024 historical SVG bytes")
    for card in data["cards"]:
        path = ROOT / card.get("artifact", f'{card["id"].lower()}-calculation.svg')
        rendered = RENDERERS[card["id"]](data, card)
        if args.check:
            require(path.is_file() and path.read_bytes() == rendered,
                    f"generated SVG differs: {path}")
        else:
            path.write_bytes(rendered)
        print(f'{card["id"]}: {path.name} sha256={hashlib.sha256(rendered).hexdigest().upper()}')


if __name__ == "__main__":
    main()
