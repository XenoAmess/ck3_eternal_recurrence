"""Deterministic campaign scoring; unknown inputs remain intervals, never means.

Pure arithmetic only. Native/save adapters must supply units, scope and sources.
Rules: docs/ck3-native-ai/campaign-development-scoring-v1-design-2026-10-19.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext, ROUND_HALF_EVEN, ROUND_FLOOR, ROUND_CEILING
from typing import Mapping

D = Decimal
VERSION = "campaign-development-v1-design-2026-10-19"
DOMAINS = {
    "L": ("领地品质", D(".25")), "E": ("财政偿付", D(".25")),
    "M": ("军事保障", D(".15")), "U": ("治理稳定", D(".10")),
    "D": ("宗族发展", D(".15")), "H": ("继承韧性", D(".10")),
}
UNITS = {
    "Q_realm": "quality_county_equivalent", "K_dynasty": "quality_county_equivalent",
    "legacy_ranks": "rank", "control_average": "fraction", "rebel_share": "fraction",
    "gold": "gold", "gross_income": "gold/month", "total_expenses": "gold/month",
    "military_current": "gold/month", "military_all_raised": "gold/month",
    "due_commitments": "gold", "P_quality": "standard_soldier_equivalent",
    "continuation_legal": "boolean", "backup_heirs": "person", "u_discretionary": "gold/month",
    "realm_county_count": "county", "dynasty_county_count": "county", "house_anchor_id": "id",
    "dynasty_anchor_id": "id", "active_family_branches": "house",
}


def dec(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("scoring decimal requires an explicit decimal string/integer")
    result = D(value)
    if not result.is_finite():
        raise ValueError("nonfinite scoring input")
    return result


def fmt(value: Decimal) -> str:
    return format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else str(value)


def interval_text(lower, upper, places=2):
    """Display intervals outwards; displayed bounds never exclude valid values."""
    lower, upper = dec(lower), dec(upper)
    quantum = D(1).scaleb(-places)
    with localcontext() as context:
        context.prec = 80
        if lower == upper:
            return format(lower.quantize(quantum), f".{places}f")
        lo = lower.quantize(quantum, rounding=ROUND_FLOOR)
        hi = upper.quantize(quantum, rounding=ROUND_CEILING)
        return f"{lo:.{places}f}–{hi:.{places}f}"


@dataclass(frozen=True)
class Interval:
    lower: Decimal
    upper: Decimal

    def __post_init__(self):
        if not self.lower.is_finite() or not self.upper.is_finite() or self.lower > self.upper:
            raise ValueError("invalid score interval")

    @classmethod
    def exact(cls, x):
        x = dec(x)
        return cls(x, x)

    def scale(self, weight):
        weight = dec(weight)
        if weight < 0:
            raise ValueError("negative interval weight")
        with localcontext() as context:
            context.prec = 80
            return Interval(self.lower * weight, self.upper * weight)

    def add(self, other):
        with localcontext() as context:
            context.prec = 80
            return Interval(self.lower + other.lower, self.upper + other.upper)

    def export(self):
        return {"lower": fmt(self.lower), "upper": fmt(self.upper),
                "value": fmt(self.lower) if self.lower == self.upper else None,
                "known": self.lower == self.upper}


UNKNOWN = Interval(D(0), D(100))


def metric(metrics: Mapping, name: str):
    row = metrics.get(name)
    if not isinstance(row, Mapping) or row.get("availability") not in {"observed", "known_absent"}:
        return None
    if row.get("unit") != UNITS[name]:
        raise ValueError(f"wrong scoring unit for {name}")
    value = dec(row.get("value"))
    if name != "gold" and value < 0:
        raise ValueError(f"negative {name}")
    if name in {"control_average", "rebel_share", "continuation_legal"} and value > 1:
        raise ValueError(f"fraction/boolean out of range: {name}")
    if name == "continuation_legal" and value not in {0, 1}:
        raise ValueError("continuation is a proven Boolean, never a probability")
    if name in {"legacy_ranks", "backup_heirs"} and value != value.to_integral_value():
        raise ValueError("discrete metric is fractional")
    return value


def R(x: Decimal, baseline: Decimal, scale: Decimal) -> Decimal:
    if x < 0 or baseline < 0 or scale <= 0:
        raise ValueError("invalid normalization inputs")
    return 100 * x / (x + max(baseline, scale))


def relative(x, baseline, scale) -> Interval:
    if x is None:
        return UNKNOWN
    if x == 0:
        return Interval.exact(0)
    if baseline is None:
        return Interval(D(0), R(x, D(0), D(scale)))
    return Interval.exact(R(x, baseline, D(scale)))


def bounded_metric(metrics: Mapping, name: str):
    value = metric(metrics, name)
    if value is not None:
        return Interval.exact(value)
    row = metrics.get(name, {})
    if row.get("availability") != "bounded":
        return None
    if row.get("unit") != UNITS[name]:
        raise ValueError("bounded metric unit mismatch")
    interval = Interval(dec(row["lower"]), dec(row["upper"]))
    if name != "gold" and interval.lower < 0:
        raise ValueError("bounded metric below zero")
    if name in {"control_average", "rebel_share"} and interval.upper > 1:
        raise ValueError("bounded fraction above one")
    return interval


def bounded_relative(current, baseline, scale):
    if current is None:
        return UNKNOWN
    if baseline is None:
        return Interval(D(0), R(current.upper, D(0), D(scale)))
    return Interval(R(current.lower, baseline.upper, D(scale)),
                    R(current.upper, baseline.lower, D(scale)))


def quality_power(rows: list[Mapping], *, damage_ref, toughness_ref) -> Decimal:
    """One current effective-stat row per owned permanent regiment; no battle forecast."""
    dr, tr = dec(damage_ref), dec(toughness_ref)
    if dr <= 0 or tr <= 0:
        raise ValueError("positive fixed reference stats required")
    result, seen = D(0), set()
    with localcontext() as context:
        context.prec, context.rounding = 40, ROUND_HALF_EVEN
        for row in sorted(rows, key=lambda r: str(r["regiment_id"])):
            identity = row["regiment_id"]
            if identity in seen:
                raise ValueError("duplicate regiment identity")
            seen.add(identity)
            n, damage, toughness = (dec(row[key]) for key in ("current_available_men", "effective_damage", "effective_toughness"))
            if min(n, damage, toughness) < 0 or row.get("stats_source_bound") is not True:
                raise ValueError("actual nonnegative source-bound stats required")
            if row.get("force_kind") not in {"levy", "permanent_maa"}:
                raise ValueError("temporary/allied/unknown force not admitted into P")
            result += n * (damage * toughness / (dr * tr)).sqrt()
        return +result


def state_intervals(current: Mapping, baseline: Mapping) -> dict[str, Interval]:
    with localcontext() as context:
        context.prec, context.rounding = 40, ROUND_HALF_EVEN
        c = {name: metric(current, name) for name in UNITS}
        b = {name: metric(baseline, name) for name in UNITS}
        scores = {"L": bounded_relative(bounded_metric(current, "Q_realm"), bounded_metric(baseline, "Q_realm"), 1)}
        g, e, m = (c[key] for key in ("gross_income", "total_expenses", "military_current"))
        civil = None
        if e is not None and m is not None:
            if m > e:
                raise ValueError("military rate exceeds compatible total expense rate")
            civil = e - m
        bg = b["gross_income"]
        bu = b["u_discretionary"]
        if bu is None and all(b[key] is not None for key in ("gross_income", "total_expenses", "military_current")):
            if b["military_current"] > b["total_expenses"]:
                raise ValueError("baseline military/expense mismatch")
            bu = max(D(0), bg - (b["total_expenses"] - b["military_current"]))
        gold, due = c["gold"], c["due_commitments"]
        scores["E"] = UNKNOWN
        if all(x is not None for x in (g, e, civil, gold, due, bg, bu)):
            u, net = max(D(0), g - civil), g - e
            wealth, debt = gold - due, max(-gold, D(0)) + due
            q12 = 12 * max(g, bg, D(1))
            flow = R(u, bu, D(1))
            buffer = 100 * min(D(1), max(D(0), wealth / q12))
            solvency = 100 / (1 + debt / q12)
            money = D(".55") * flow + D(".30") * buffer + D(".15") * solvency
            if net < 0 and wealth <= 0:
                money = min(money, D(25))
            scores["E"] = Interval.exact(money)
        elif gold is not None and gold <= 0 and g is not None and e is not None and g < e:
            scores["E"] = Interval(D(0), D(25))
        power = relative(c["P_quality"], b["P_quality"], 100)
        full = c["military_all_raised"]
        factor = Interval(D(".65"), D(1))
        if all(x is not None for x in (g, civil, full)):
            total = civil + full
            afford = D(1) if total == 0 else min(D(1), g / total)
            factor = Interval.exact(D(".65") + D(".35") * afford)
        scores["M"] = Interval(power.lower * factor.lower, power.upper * factor.upper)
        control, rebels = bounded_metric(current, "control_average"), bounded_metric(current, "rebel_share")
        control_score = Interval(D(0), D(60)) if control is None else control.scale(60)
        rebel_score = Interval(D(0), D(40)) if rebels is None else Interval(40 * (1 - rebels.upper), 40 * (1 - rebels.lower))
        scores["U"] = control_score.add(rebel_score)
        scores["D"] = bounded_relative(bounded_metric(current, "K_dynasty"), bounded_metric(baseline, "K_dynasty"), 1).scale(".8").add(
            relative(c["legacy_ranks"], b["legacy_ranks"], 1).scale(".2"))
        legal, backup = c["continuation_legal"], c["backup_heirs"]
        top = D(100) if backup is None else 70 + 15 * min(backup, D(2))
        scores["H"] = (Interval.exact(0) if legal == 0 else
                       Interval(D(70), top) if legal == 1 and backup is None else
                       Interval.exact(top) if legal == 1 else Interval(D(0), top))
        return scores


def aggregate_state(scores: Mapping[str, Interval]) -> Interval:
    total = Interval.exact(0)
    for key, (_, weight) in DOMAINS.items():
        total = total.add(scores[key].scale(weight))
    return total


def score_360(samples: list[Interval], endpoint: Interval) -> Interval:
    """Caller must separately prove fixed 360 date slots and exact endpoint identity."""
    if len(samples) != 360:
        raise ValueError("exactly 360 fixed month slots required; do not shorten denominator")
    with localcontext() as context:
        context.prec, context.rounding = 40, ROUND_HALF_EVEN
        bounds = []
        for side in ("lower", "upper"):
            values = [getattr(x, side) for x in samples]
            if any(x < 0 or x > 100 for x in values):
                raise ValueError("monthly state outside 0..100")
            end = getattr(endpoint, side)
            if end < 0 or end > 100:
                raise ValueError("endpoint outside 0..100")
            last, mean = sum(values[-12:]) / 12, sum(values) / 360
            low = sum(sorted(values)[:36]) / 36
            bounds.append(10 * (D(".7") * (D(".6") * end + D(".4") * last) + D(".2") * mean + D(".1") * low))
        return Interval(*bounds)


def build_report(current: dict, baseline: dict, *, snapshot: dict, sources: list,
                 facts: list, machine_id: str, observed_at_utc: str,
                 unknown_fields: list, strict_endpoint_verified: bool = False) -> dict:
    sources = list(sources)
    for packet in (current, baseline):
        for row in packet.values():
            for source in row.get("additional_sources", []):
                if source["id"] not in {s["id"] for s in sources}:
                    sources.append(source)
    scores = state_intervals(current, baseline)
    a = aggregate_state(scores)
    baseline_a = aggregate_state(state_intervals(baseline, baseline))
    baseline_scores = state_intervals(baseline, baseline)
    shared = [key for key in DOMAINS if scores[key].lower == scores[key].upper
              and baseline_scores[key].lower == baseline_scores[key].upper]
    known_current = aggregate_state({key: scores[key] if key in shared else Interval.exact(0) for key in DOMAINS})
    known_baseline = aggregate_state({key: baseline_scores[key] if key in shared else Interval.exact(0) for key in DOMAINS})
    coverage = sum((DOMAINS[key][1] for key in shared), D(0))
    with localcontext() as context:
        context.prec = 80
        known_delta = known_current.lower - known_baseline.lower
    steps, exported = [], {}
    explanations = {
        "L": "保有的县域品质相对真实开局；正式失地移出，控制与占领折损。",
        "E": "经常收入、净现金、真实负债与军费；未核清债务不当作零。",
        "M": "按同版本有效伤害/坚韧计算标准兵当量，并考察全动员负担。",
        "U": "县域结构加权控制力与真实内战占比；无数据不当作稳定。",
        "D": "固定开局宗族/家族；县域去重，境外折价，已解锁传承可跨代。",
        "H": "合法玩家后继及备用资格；主头衔候选不冒充完整继承合同。",
    }
    def show(row):
        if row.get("availability") in {"observed", "known_absent"}:
            return f"{dec(row['value']):.2f}"
        if row.get("availability") == "bounded":
            return interval_text(row['lower'], row['upper'])
        return "未取得"
    cq, bq = current.get("Q_realm", {}), baseline.get("Q_realm", {})
    explanations["L"] = f"品质县：{show(bq)}→{show(cq)}，L=100×当前/(当前+max(开局,1))；含控制与实际占领折损。"
    g, e, m = (metric(current, k) for k in ("gross_income", "total_expenses", "military_current"))
    bu = metric(baseline, "u_discretionary")
    bg, be, bm = (metric(baseline, k) for k in ("gross_income", "total_expenses", "military_current"))
    if bu is None and None not in (bg, be, bm):
        bu = max(D(0), bg - (be - bm))
    money_inputs = [("总收入", g), ("总支出", e), ("当前军费", m),
                    ("现金", metric(current, "gold")), ("到期承诺", metric(current, "due_commitments")),
                    ("开局收入", bg), ("开局可支配收入", bu)]
    missing = [label for label, value in money_inputs if value is None]
    explanations["E"] = ("E=55%经常收入归一+30%现金缓冲+15%偿付。" +
        (f"收入/支出/军费={fmt(g)}/{fmt(e)}/{fmt(m)}；开局u={fmt(bu)}，现金/承诺="
         f"{show(current.get('gold', {}))}/{show(current.get('due_commitments', {}))}；赤字且净财富≤0时封顶25。"
         if not missing else f"现金{show(baseline.get('gold', {}))}→{show(current.get('gold', {}))}；缺" + "、".join(missing) + "，保留区间。"))
    power = metric(current, "P_quality")
    power0 = metric(baseline, "P_quality")
    full = metric(current, "military_all_raised")
    missing_m = [label for label, value in [("常规军有效质量", power), ("开局有效质量", power0),
                  ("收入", g), ("总支出", e), ("当前军费", m), ("全动员军费", full)] if value is None]
    explanations["M"] = (f"P={show(current.get('P_quality', {}))}，开局P={show(baseline.get('P_quality', {}))}；"
        "M=R(P;P0,100)×(0.65+0.35×全动员负担率)。" +
        ("缺" + "、".join(missing_m) + ("；零兵力已使M确定为0。" if power == 0 else "，保留区间。")
         if missing_m else f"收入={fmt(g)}，民政={fmt(e-m)}，全动员军费={fmt(full)}，负担率=min(1,收入/总费)，总费0时取1。"))
    control = current.get("control_average", {})
    explanations["U"] = f"q加权控制比例{show(control)}；本国内战占比{show(current.get('rebel_share', {}))}；U=60×控制+40×(1−内战)。"
    explanations["D"] = f"宗族土地K：{show(baseline.get('K_dynasty', {}))}→{show(current.get('K_dynasty', {}))}；传承{show(baseline.get('legacy_ranks', {}))}→{show(current.get('legacy_ranks', {}))}级已计入20%，土地占80%；支系数量仅列事实。"
    legal, backup = metric(current, "continuation_legal"), metric(current, "backup_heirs")
    explanations["H"] = ("已确认无合法玩家后继，k=0，H=0；备用数量不改变结果。" if legal == 0 else
        f"H=k×(70+15×min(备用,2))；k={fmt(legal) if legal is not None else '未确认'}，"
        f"备用={fmt(backup) if backup is not None else '资格未确认'}。" +
        ("合法继续及备用资格均已核实。" if legal == 1 and backup is not None else "缺少的合法资格保留区间，候选列表不能补证。"))
    comparison_facts = []
    cn, bn = metric(current, "realm_county_count"), metric(baseline, "realm_county_count")
    cg, bg = metric(current, "gold"), metric(baseline, "gold")
    if cn is not None and bn is not None:
        comparison_facts.append({"label_zh": "实际统治领地", "value_text": f"{fmt(bn)} → {fmt(cn)} 县（变化{fmt(cn-bn)}）", "source_refs": ["baseline_save", "current_save"]})
    if cg is not None and bg is not None:
        change = ("+" if cg >= bg else "") + fmt(cg-bg)
        comparison_facts.append({"label_zh": "保存时现金", "value_text": f"{fmt(bg)} → {fmt(cg)} 金（变化{change}）", "source_refs": ["baseline_save", "current_save"]})
    cb, bb = metric(current, "active_family_branches"), metric(baseline, "active_family_branches")
    dynasty = metric(current, "dynasty_anchor_id")
    if cb is not None and bb is not None and dynasty is not None:
        cl, bl = metric(current, "legacy_ranks"), metric(baseline, "legacy_ranks")
        legacy = f"；传承{fmt(bl)} → {fmt(cl)}级" if cl is not None and bl is not None else ""
        comparison_facts.append({"label_zh": "固定宗族与家族支系", "value_text": f"宗族{fmt(dynasty)}；已建立支系{fmt(bb)} → {fmt(cb)}" + legacy, "source_refs": [x["id"] for x in sources]})
    facts = comparison_facts + facts
    facts.append({"label_zh": "共同已确认领域的固定权重贡献", "value_text":
        f"{','.join(shared)}；覆盖{fmt(100*coverage)}%；{fmt(known_baseline.lower)} → {fmt(known_current.lower)} / 100；变化{fmt(known_delta)}（非总分）",
        "source_refs": [x["id"] for x in sources]})
    for key, (label, weight) in DOMAINS.items():
        interval = scores[key]
        exported[key] = {"label_zh": label, "weight": float(weight), **interval.export(),
                         "contribution": interval.scale(weight).export()}
        value = interval.export()["value"]
        text = interval_text(interval.lower, interval.upper) + ("（区间）" if value is None else "")
        contribution = interval.scale(weight)
        steps.append({"id": key, "title_zh": label, "value_text": text + " / 100",
                      "explanation_zh": explanations[key] + f" 加权贡献{interval_text(contribution.lower, contribution.upper)}分。", "source_refs": [x["id"] for x in sources]})
    steps.append({"id": "A_state", "title_zh": "当前存档局面", "value_text":
                  interval_text(a.lower, a.upper) + ("（区间）" if a.lower != a.upper else "") + " / 100",
                  "explanation_zh": "六项按固定权重汇总；这是存档局面，不冒充完整三十年总分。" +
                  f"共同已确认项贡献{known_baseline.lower:.2f}→{known_current.lower:.2f}，覆盖{fmt(100*coverage)}%（非总分）。", "source_refs": [x["id"] for x in sources]})
    steps.append({"id": "S30", "title_zh": "三十年总分", "value_text": "历史采样不足，无法完整计算",
                  "explanation_zh": "需要固定360个月、准点状态与真实开局基线；不补均值、不缩短分母。", "source_refs": []})
    if snapshot.get("T0") and snapshot.get("date"):
        def fixed_date(text):
            y, m, day = (int(x) for x in text.split("."))
            months = [31,28,31,30,31,30,31,31,30,31,30,31]
            if not 1 <= m <= 12 or not 1 <= day <= months[m-1]:
                raise ValueError("invalid fixed365 CK3 date")
            return y*365 + sum(months[:m-1]) + day-1
        y, m, day = (int(x) for x in snapshot["T0"].split("."))
        target = f"{y+30}.{m}.{day}"
        snapshot = {**snapshot, "target_date": target,
                    "lateness_game_days": fixed_date(snapshot["date"])-fixed_date(target),
                    "calendar": "CK3_fixed_365_days_no_Gregorian_leap_days"}
    late = snapshot.get("lateness_game_days")
    if strict_endpoint_verified and (not snapshot.get("T0") or not snapshot.get("date") or late != 0):
        raise ValueError("strict endpoint contradicts the actual CK3 date")
    reason = (f"保存于三十周年后{late}个游戏日；这是当前存档局面分，360月史不完整。"
              if late is not None and late > 0 else "这是当前存档局面分析；360月史不完整，S30不可计算。")
    return {
        "schema": "xar.ck3.campaign-development-score/v1", "scoring_version": VERSION,
        "machine_id": machine_id, "observed_at_utc": observed_at_utc,
        "qualification": {"status": "FINAL_STATE_ONLY", "state_completeness":
                          "COMPLETE" if a.lower == a.upper else "BOUNDED_INCOMPLETE",
                          "reason_zh": reason},
        "snapshot": snapshot, "scores": exported,
        "aggregate": {"A_state": a.export(), "A_end": a.export() if strict_endpoint_verified else None,
                      "known_domains": shared, "known_domains_coverage_weight": fmt(coverage),
                      "known_domains_baseline_contribution": fmt(known_baseline.lower),
                      "known_domains_current_contribution": fmt(known_current.lower),
                      "known_domains_delta_contribution": fmt(known_delta),
                      "S30": {"lower": "0", "upper": "1000", "value": None, "available": False},
                      "delta_from_baseline": (fmt(a.lower - baseline_a.lower)
                                               if a.lower == a.upper and baseline_a.lower == baseline_a.upper else None)},
        "raw_metrics": current, "baseline_metrics": baseline,
        "display_steps": steps, "facts": facts, "unknown_fields": unknown_fields,
        "sources": sources, "claims": {"no_missing_value_imputation": True,
                                       "weights_renormalized": False,
                                       "actual_gameplay_score_not_video_progress": True},
    }
