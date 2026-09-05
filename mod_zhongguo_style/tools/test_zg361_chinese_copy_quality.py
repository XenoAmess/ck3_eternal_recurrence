#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Product-wide quality gates for player-facing Simplified Chinese copy.

The checks intentionally read the generated localization files.  A generator
unit test can be green while the bytes CK3 actually loads still contain a
template, a stale manual row, or a malformed opening.  Failures therefore name
the final localization key and file instead of only naming the producer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unittest


MOD_ROOT = Path(__file__).resolve().parents[1]
LOC_ROOT = MOD_ROOT / "localization" / "simp_chinese"
EVENT_ROOT = MOD_ROOT / "events"

LOC_ROW_RE = re.compile(
    r'^\s*(?P<key>[^\s:#]+):\d+\s+"(?P<value>.*)"\s*$'
)
BODY_KEY_RE = re.compile(r"(?:\.desc|_desc)$")
OPTION_KEY_RE = re.compile(r"(?:\.[abcd]|_(?:option|route)_[abcd])$")

# Body copy may explain the situation and its stakes.  It must not enumerate
# abstract choices that belong on the buttons or tell the player to read them.
BODY_CHOICE_META_RE = re.compile(
    r"(?:"
    r"路线\s*[甲乙丙ＡＢＣABC]"
    r"|[甲乙丙ＡＢＣABC]\s*[/／、和与或]\s*[甲乙丙ＡＢＣABC]"
    r"\s*(?:的)?\s*(?:具体|实际|所述)?\s*"
    r"(?:路线|方案|选项|动作|处理|后果|选择)"
    r"|按\s*[ＡＢＣABC](?:做|办|执行|处理|走)?"
    r"|(?:按钮|选项)(?:上|中|里)?[^。！？；]{0,12}"
    r"(?:写明|列明|说明|展示)[^。！？；]{0,12}"
    r"(?:动作|选择|处理|后果)"
    r"|(?:下方|以下)[^。！？；]{0,8}按钮"
    r"|按钮及说明"
    r")",
    re.IGNORECASE,
)

# An option must name the actual act.  These labels merely point at an
# implementation branch and reproduce the exact problem seen in live UI.
GENERIC_OPTION_RE = re.compile(
    r"(?:"
    r"(?:按|照|选|走|采用)\s*[ＡＢＣABC](?:做|办|执行|处理|路线)?"
    r"|路线\s*[甲乙丙ＡＢＣABC]"
    r"|登记\s*路线\s*[甲乙丙ＡＢＣABC]\s*倾向"
    r"|按\s*(?:证据|政治)\s*办"
    r")",
    re.IGNORECASE,
)

# Player-facing copy must stay inside the fiction and describe the record or
# decision itself.  These terms expose implementation/testing vocabulary or
# refer to the UI as a card instead of speaking naturally to the player.
PLAYER_IMPLEMENTATION_JARGON_RE = re.compile(
    r"(?:"
    r"玩家|本卡|结算器|运行时纵切|脚本|回写"
    r"|后台事项|裁[决定]卡|原始弹窗|弹窗|批处理|合批"
    r"|期限闸门|归档卡|首项处置|次项处置|失败项"
    r"|(?<![A-Za-z0-9_])(?:GUI|CK3|live|player|runtime|RED|N/A|P[012])"
    r"(?![A-Za-z0-9_])"
    r"|source\s+serial|state[- ]machine|pipeline|fingerprint|availability"
    r")",
    re.IGNORECASE,
)

VAGUE_DECISION_CONFIRM_LABELS = frozenset(
    {
        "从严！",
        "松绑",
        "放养",
        "我全都要，现在就要",
        "叫下一位产品经理进来",
    }
)

# Exact regressions found by the final human read-through.  These are not a
# blanket ban on satire or abbreviations: each listed player-facing key used a
# term without explaining it in that same surface, or exposed an internal
# phase label.  Keeping the check key-scoped avoids rejecting legitimate prose
# that gives an immediate Chinese explanation.
FORBIDDEN_LITERAL_BY_KEY: dict[str, tuple[str, ...]] = {
    "zg361.30.b": ("PIP",),
    "zg361pp.grade.325": ("PPT",),
    "zg361pp.174.b": ("PPT",),
    "zg361pp.174.b.tt": ("PPT",),
    "zg361m.174.desc": ("PPT",),
    "zg361we.handoff.3.t": ("PPT",),
    "zg361m.2.t": ("OKR",),
    "zg361m.131.t": ("OKR",),
    "zg361m.11.t": ("HR",),
    "zg361m.76.desc": ("HR",),
    "zg361m.11.desc": ("vs",),
    "zg361m.28.a": ("ID",),
    "zg361m.28.a.tt": ("ID",),
    "zg361m.90.a.tt": ("ID",),
    "zg361m.344.desc": ("ID",),
    "zg361m.344.a": ("ID",),
    "zg361m.344.a.tt": ("ID",),
    "zg361m.139.desc": ("cohort",),
    "zg361m.257.desc": ("cohort",),
    "zg361m.305.desc": ("cohort",),
    "zg361m.305.a": ("cohort",),
    "zg361m.305.a.tt": ("cohort",),
    "zg361m.322.desc": ("cohort",),
    "zg361_scoreboard_detail_field_b1_peer_sealed": ("B1",),
    "zg361_scoreboard_detail_peer_hint": ("received",),
    "zg361_scoreboard_detail_audit_hint": ("B1",),
    "zg361b2.statement.prepared": ("B2",),
    "zg361b2.statement.delivered": ("B2",),
    "zg361b2.statement.appeal": ("B2",),
    "zg361b2.statement.corrected": ("B2",),
    "zg361b2.statement.pip": ("B2",),
    "zg361b2.statement.retaliation": ("B2",),
    "zg361p3.342.a": ("外部依赖",),
    "zg361m.2.desc": ("原生治理成果",),
    "zg361comp.1.ae3.r1": ("干升职兑现",),
    "zg361comp.1.ae3.r2": ("干升职兑现",),
    "zg361comp.1.af4.r1": ("双门", "组织门"),
    "zg361comp.1.af4.r2": ("双门", "组织门"),
    "zg361comp.1.af4.r3": ("双门", "组织门"),
}

OPENING_PUNCTUATION = frozenset(
    "。！？；：，、,.!?;:)]}）】》〉」』”’…—-·/／"
)
DYNAMIC_OPENERS = frozenset("[$@")

# Literal CJK text limits.  CK3 formatting and scripted expressions are not
# charged because their rendered width is data-dependent.  zg361m policy
# choices may be a full consequence-bearing sentence; runtime event choices
# are held to the tighter popup-button limits below.  There are deliberately
# no per-key exceptions at this gate's introduction.
OPTION_LENGTH_LIMITS = (
    ("zg361m.", "361 policy", 64),
    ("zg361b1.", "B1", 40),
    ("zg361b2.", "B2", 42),
    ("zg361comp.", "compensation", 48),
    ("zg361wad.", "Workforce AD", 42),
    ("zg361workforce", "Workforce facts", 42),
    ("zg361ch.", "HC", 40),
    ("zg361_cl_", "HC learning", 40),
    ("zg361pp.", "PP", 32),
    ("zg361we.", "WE", 42),
    ("zg361cp.", "CP", 36),
    ("zg361p3.", "P3", 36),
    ("zg361.", "361 runtime", 40),
)
OPTION_LENGTH_EXCEPTIONS: dict[str, str] = {}


@dataclass(frozen=True)
class LocEntry:
    key: str
    value: str
    path: Path
    line: int

    @property
    def location(self) -> str:
        return f"{self.path.name}:{self.line}:{self.key}"


def read_final_chinese() -> dict[str, LocEntry]:
    entries: dict[str, LocEntry] = {}
    for path in sorted(LOC_ROOT.glob("*.yml")):
        for line_number, row in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), start=1
        ):
            match = LOC_ROW_RE.match(row)
            if match is None:
                continue
            key = match.group("key")
            if not key.startswith("zg361"):
                continue
            if key in entries:
                previous = entries[key]
                raise AssertionError(
                    f"duplicate loc key {key}: {previous.location}, "
                    f"{path.name}:{line_number}"
                )
            entries[key] = LocEntry(
                key=key,
                value=match.group("value"),
                path=path,
                line=line_number,
            )
    return entries


def read_event_loc_references(field: str) -> set[str]:
    """Collect localization keys actually wired into generated event fields.

    Several event families use semantic suffixes such as ``.l1``/``.r1``
    instead of the conventional ``.desc``/``.a`` names.  Reading the final
    event projection keeps those visible strings inside the product-wide gate.
    Non-localization ``name =`` values (for example variable names) are later
    discarded because they have no matching localization row.
    """

    # ``desc =`` also appears inline inside ``triggered_desc`` blocks, so it
    # cannot be restricted to the beginning of a physical line.
    pattern = re.compile(
        rf"(?<![\w]){re.escape(field)}\s*=\s*(zg361[\w.]+)\b"
    )
    references: set[str] = set()
    for path in sorted(EVENT_ROOT.glob("*.txt")):
        references.update(pattern.findall(path.read_text(encoding="utf-8-sig")))
    return references


def strip_ck3_markup(value: str) -> str:
    """Return literal player-visible prose for comparisons and length gates."""

    value = value.replace(r"\n", " ")
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = re.sub(r"\$[^$]+\$", "", value)
    value = re.sub(r"@[A-Za-z0-9_./-]+!", "", value)
    value = re.sub(r"#[A-Za-z0-9_]+\s*|#!", "", value)
    return re.sub(r"\s+", " ", value).strip()


def title_candidates_for(desc_key: str) -> tuple[str, ...]:
    if desc_key.endswith(".desc"):
        base = desc_key[: -len(".desc")]
        return (f"{base}.t", f"{base}.title", f"{base}.name")
    if desc_key.endswith("_desc"):
        base = desc_key[: -len("_desc")]
        return (base, f"{base}_title", f"{base}_name")
    return ()


def option_base(key: str) -> str | None:
    match = re.match(r"^(.*)\.[abcd]$", key)
    if match is not None:
        return match.group(1)
    match = re.match(r"^(.*)_(?:option|route)_[abcd]$", key)
    if match is not None:
        return match.group(1)
    return None


def desc_candidates_for_option(key: str) -> tuple[str, ...]:
    base = option_base(key)
    if base is None:
        return ()
    return (f"{base}.desc", f"{base}_desc")


def option_family(key: str) -> tuple[str, int] | None:
    for prefix, label, limit in OPTION_LENGTH_LIMITS:
        if key.startswith(prefix):
            return label, limit
    if key.startswith("zg361"):
        return "other zg361 event", 56
    return None


def format_failures(failures: list[str]) -> str:
    return "\n" + "\n".join(f"- {failure}" for failure in failures)


class ChineseCopyQualityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = read_final_chinese()
        event_bodies = read_event_loc_references("desc")
        event_options = read_event_loc_references("name")
        cls.bodies = {
            key: entry
            for key, entry in cls.entries.items()
            if BODY_KEY_RE.search(key) or key in event_bodies
        }
        cls.options = {
            key: entry
            for key, entry in cls.entries.items()
            if (OPTION_KEY_RE.search(key) or key in event_options)
            and option_family(key) is not None
        }

    def test_01_gate_covers_all_requested_copy_families(self) -> None:
        expected = {
            "361 policy",
            "HC",
            "HC learning",
            "PP",
            "WE",
            "CP",
            "P3",
            "361 runtime",
        }
        actual = {
            family[0]
            for key in self.options
            if (family := option_family(key)) is not None
        }
        self.assertTrue(expected.issubset(actual))
        self.assertIn("other zg361 event", actual)
        self.assertGreater(len(self.bodies), 100)
        self.assertGreater(len(self.options), 1_700)
        self.assertIn("zg361comp.1.l1", self.bodies)
        self.assertIn("zg361comp.1.l1.r1", self.options)

    def test_02_body_never_starts_with_punctuation_or_dynamic_expression(self) -> None:
        failures: list[str] = []
        for entry in self.bodies.values():
            raw = entry.value.lstrip()
            if not raw:
                failures.append(f"{entry.location} empty body")
                continue
            first = raw[0]
            if first in OPENING_PUNCTUATION:
                failures.append(
                    f"{entry.location} starts with punctuation {first!r}: "
                    f"{entry.value!r}"
                )
            elif first in DYNAMIC_OPENERS:
                failures.append(
                    f"{entry.location} starts with dynamic expression {first!r}: "
                    f"{entry.value!r}"
                )
        self.assertFalse(failures, format_failures(failures))

    def test_03_body_never_repeats_its_title_verbatim(self) -> None:
        failures: list[str] = []
        for entry in self.bodies.values():
            desc = strip_ck3_markup(entry.value)
            for candidate in title_candidates_for(entry.key):
                title_entry = self.entries.get(candidate)
                if title_entry is None:
                    continue
                title = strip_ck3_markup(title_entry.value)
                # Very short nouns can occur naturally in prose.  Four or more
                # literal characters constitute a recognizable copied title.
                if len(title) >= 4 and title in desc:
                    failures.append(
                        f"{entry.location} repeats {candidate} verbatim: {title!r}"
                    )
                    break
        self.assertFalse(failures, format_failures(failures))

    def test_04_body_never_enumerates_abstract_routes_or_button_instructions(self) -> None:
        failures = [
            f"{entry.location} contains choice meta-copy "
            f"{match.group(0)!r}: {entry.value!r}"
            for entry in self.bodies.values()
            if (match := BODY_CHOICE_META_RE.search(strip_ck3_markup(entry.value)))
            is not None
        ]
        self.assertFalse(failures, format_failures(failures))

    def test_05_body_never_duplicates_an_option_verbatim(self) -> None:
        failures: list[str] = []
        for option in self.options.values():
            option_text = strip_ck3_markup(option.value).rstrip("。！？”")
            if len(option_text) < 6:
                continue
            for candidate in desc_candidates_for_option(option.key):
                desc = self.entries.get(candidate)
                if desc is None:
                    continue
                if option_text in strip_ck3_markup(desc.value):
                    failures.append(
                        f"{desc.location} duplicates option {option.key}: "
                        f"{option_text!r}"
                    )
        self.assertFalse(failures, format_failures(failures))

    def test_06_options_name_actions_instead_of_abstract_branches(self) -> None:
        failures = [
            f"{entry.location} contains generic branch label "
            f"{match.group(0)!r}: {entry.value!r}"
            for entry in self.options.values()
            if (match := GENERIC_OPTION_RE.search(strip_ck3_markup(entry.value)))
            is not None
        ]
        self.assertFalse(failures, format_failures(failures))

    def test_07_option_literal_lengths_fit_popup_family_limits(self) -> None:
        failures: list[str] = []
        counts: dict[str, int] = {}
        maxima: dict[str, tuple[int, str]] = {}
        for entry in self.options.values():
            family = option_family(entry.key)
            assert family is not None
            label, limit = family
            length = len(strip_ck3_markup(entry.value))
            counts[label] = counts.get(label, 0) + 1
            if length > maxima.get(label, (-1, ""))[0]:
                maxima[label] = (length, entry.key)
            if entry.key in OPTION_LENGTH_EXCEPTIONS:
                continue
            if length > limit:
                failures.append(
                    f"{entry.location} is {length} chars; {label} limit is "
                    f"{limit}: {entry.value!r}"
                )
        stats = ", ".join(
            f"{label}={counts[label]} options/max {maxima[label][0]} "
            f"({maxima[label][1]})"
            for label in sorted(counts)
        )
        self.assertFalse(failures, f"\noption stats: {stats}{format_failures(failures)}")

    def test_08_player_copy_never_exposes_implementation_jargon(self) -> None:
        failures = [
            f"{entry.location} contains implementation jargon "
            f"{match.group(0)!r}: {entry.value!r}"
            for entry in self.entries.values()
            if (
                match := PLAYER_IMPLEMENTATION_JARGON_RE.search(
                    strip_ck3_markup(entry.value)
                )
            )
            is not None
        ]
        self.assertFalse(failures, format_failures(failures))

    def test_09_decision_confirms_name_the_action(self) -> None:
        failures = [
            f"{entry.location} uses vague confirm label {entry.value!r}"
            for entry in self.entries.values()
            if entry.key.endswith("_confirm")
            and strip_ck3_markup(entry.value) in VAGUE_DECISION_CONFIRM_LABELS
        ]
        self.assertFalse(failures, format_failures(failures))

    def test_10_known_unexplained_terms_and_internal_phase_labels_do_not_return(self) -> None:
        failures: list[str] = []
        for key, forbidden_literals in FORBIDDEN_LITERAL_BY_KEY.items():
            entry = self.entries.get(key)
            if entry is None:
                failures.append(f"missing audited player-facing key: {key}")
                continue
            visible = strip_ck3_markup(entry.value)
            for literal in forbidden_literals:
                if literal in visible:
                    failures.append(
                        f"{entry.location} contains unexplained/internal term "
                        f"{literal!r}: {entry.value!r}"
                    )
        self.assertFalse(failures, format_failures(failures))


class ChineseCopyQualityHelperTest(unittest.TestCase):
    def test_title_and_option_pairing_supports_dot_and_underscore_namespaces(self) -> None:
        self.assertIn("zg361we.242.t", title_candidates_for("zg361we.242.desc"))
        self.assertIn(
            "zg361_cl_m314_title",
            title_candidates_for("zg361_cl_m314_desc"),
        )
        self.assertIn(
            "zg361_cl_m314_desc",
            desc_candidates_for_option("zg361_cl_m314_route_a"),
        )

    def test_markup_is_excluded_from_literal_length_and_copy_comparison(self) -> None:
        self.assertEqual(
            strip_ck3_markup(
                "#P [scope:subject.GetShortUIName]#! @gold_icon! 落笔$SUFFIX$"
            ),
            "落笔",
        )

    def test_choice_meta_copy_patterns_cover_live_failure_shapes(self) -> None:
        for bad_body in (
            "路线甲、乙会执行所述业务选择。",
            "A/B 的具体动作与立即后果写在按钮上。",
            "按钮上写明本项实际处理。",
            "具体操作、代价和条件均写在下方按钮及说明中。",
            "按A做，后续再说。",
        ):
            with self.subTest(bad_body=bad_body):
                self.assertIsNotNone(BODY_CHOICE_META_RE.search(bad_body))

    def test_generic_option_patterns_cover_abstract_branch_labels(self) -> None:
        for bad_option in (
            "按A做",
            "按 B 办",
            "路线甲",
            "登记路线乙倾向：只调整账本",
            "按证据办",
            "按政治办",
        ):
            with self.subTest(bad_option=bad_option):
                self.assertIsNotNone(GENERIC_OPTION_RE.search(bad_option))

    def test_implementation_jargon_patterns_cover_audit_misses(self) -> None:
        for bad_copy in (
            "本卡不会替缺失事实编造解释。",
            "让玩家亲自看到两面性。",
            "结算器已经给出结果。",
            "当前运行时纵切尚无记录。",
            "结果回写原经理。",
            "失败项恢复原始弹窗。",
            "批处理仍逐项调用原裁定卡。",
        ):
            with self.subTest(bad_copy=bad_copy):
                self.assertIsNotNone(
                    PLAYER_IMPLEMENTATION_JARGON_RE.search(bad_copy)
                )


if __name__ == "__main__":
    unittest.main()
