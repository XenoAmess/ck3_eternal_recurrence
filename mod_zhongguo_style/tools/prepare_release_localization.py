#!/usr/bin/env python3
"""Generate, preserve, apply, and audit release localization candidates.

MiniMax-M3 is used only through the repository's read-only candidate caller.
This orchestrator selects small key batches, stores every returned JSON object
outside the repository, and applies candidates only in an explicit second step.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = MOD_ROOT.parent
ROOT_TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(ROOT_TOOLS))
sys.path.insert(0, str(MOD_ROOT / "tools"))

import translate_localization_minimax as minimax  # noqa: E402
from gen_361_mechanisms import (  # noqa: E402
    release_translation_source_sha256,
)
from zg361_mechanism_data import load_mechanisms  # noqa: E402


LANGUAGES = {
    "french": "French (France)",
    "german": "German",
    "japanese": "Japanese",
    "korean": "Korean",
    "polish": "Polish",
    "russian": "Russian",
    "spanish": "Spanish (Spain)",
}
PROTECTED_TERMS = ("3.75", "3.5", "3.25", "361", "KPI", "OKR", "PIP", "HC")
CORE_CONTEXT = (
    "Crusader Kings III ZhongGuo 361 performance-review UI. Preserve the dry, "
    "satirical Chinese internet-company tone while keeping buttons and tooltips concise."
)
MECHANISM_CONTEXT = (
    "Crusader Kings III ZhongGuo 361 performance-policy cards. Each five-key group is one "
    "distinct policy dilemma; preserve its concrete decision, tradeoff, humor, and concise UI tone."
)
TRANSLATION_SOURCE_OVERRIDES = {
    "zg361m.14.desc": (
        "[C / P0] An official appeals with frozen evidence after discussing the case with the "
        "direct superior. If upheld, the superior recalibrates the result, refunds the three "
        "immediate 3.25 charges to local treasury, personal gold, and merit item by item, stops "
        "the unfinished one-year salary cut of 25%, and corrects the ranking; failed or abusive "
        "appeals cost standing and credibility."
    ),
    "zg361m.18.desc": (
        "[C / P0] This frozen record shows rating, KPI, rank, superior, and reasons. For 3.25 it "
        "also shows local treasury -50, personal gold -25, merit -60, salary -25% for one year, "
        "and the appeal refund or stop-deduction status."
    ),
    "zg361m.21.desc": (
        "[D / P1] A ruler allocates a limited bonus pool: 3.75 receives a bonus or short raise, "
        "3.5 stays unchanged, and 3.25 keeps the fourfold penalty. Top rewards consume real "
        "finances, while repeatedly unrewarded 3.75 talent may seek a transfer or leave."
    ),
}
ENTRY = re.compile(r'^(?P<prefix> (?P<key>[^:\s]+):\d+ ")(?P<value>(?:[^"\\]|\\.)*)(?P<suffix>")$')
MECHANISM_KEY = re.compile(r"^zg361m\.(\d+)\.(?:t|desc|a|b|c)$")
TECHNICAL_WORDS = re.compile(
    r"\b(?:KPI|OKR|PIP|HC|AI|CK3|DLC|UI|A|B|C|P0|P1|P2|P3)\b",
    re.I,
)
ALLOWED_IDENTICAL = {
    "german": {"zg361_scoreboard_col_status"},
    "polish": {"zg361_scoreboard_col_status"},
}
JAPANESE_SIMPLIFIED_CHINESE = frozenset(
    "绩评关闭坚达标员务业为过进风压价证财门团队级议划录线经济变实术专处罚劳费资备质显预扩认让归监时层长权开动从报奖惩废领导绝虑优续择项额总调环应岁带园义节发险职华众这们还账译诉产构筛转输设货损骗测规态稳创护边个卖约岗离际网话单远场执审养选"
)
JAPANESE_SIMPLIFIED_CHINESE = JAPANESE_SIMPLIFIED_CHINESE | frozenset(
    "试舍亲侪势协查辩遗收胜赢趋轮验"
)
JAPANESE_FORBIDDEN_FRAGMENTS = (
    "互相高評",
    "反噬",
    "可控",
    "全体長会",
    "阻塞",
    "算法",
    "流程",
    "明星",
    "工時",
    "抽查",
    "灌水",
    "今周期",
    "考核",
    "留用",
    "末位淘汰",
    "本層",
    "考績告身",
    "主持",
    "地方財政庫",
    "自席",
    "覆審",
    "空欠",
    "ランポ",
    "人員退去",
    "抽せん",
    "成本",
    "社内倒錯",
)
JAPANESE_FORBIDDEN_LATIN = re.compile(
    r"(?<![A-Za-z])(?:backfill|blocker|cliff|cohort|handcuffs|leaver|managers?|nomination|narrative|onboarding|one|owner|override|rent\s+seeking|scapegoat|sponsor|throughput|toil|usal)(?![A-Za-z])",
    re.I,
)
LANGUAGE_FORBIDDEN_RESIDUALS = {
    "german": (
        "bottom-tier",
        "bottom-quote",
        "backfill",
        "blocker",
        "cliff",
        "credential",
        "cultural mismatch",
        "leaver",
        "offer",
        "owner",
        "organisations-ledger",
        "performer",
        "shared services",
        "toil",
    ),
    "french": (
        "backfill",
        "cliff",
        "denúncias",
        "leaver",
        "override",
        "owner",
        "performers",
        "raider",
        "toil",
    ),
    "korean": (
        "(shared organizational ledger)",
        "blocker",
        "backfill",
        "cliff",
        "cohort",
        "delivery",
        "disciplinary",
        "favorites",
        "governance",
        "integrity",
        "jingcha",
        "leaver",
        "ossier",
        "offer",
        "owner",
        "override",
        "ramp",
        "sponsor",
        "spot bonus",
        "vesting",
    ),
    "polish": (
        "backfill",
        "credit",
        "deliverable",
        "deadline",
        "feedback",
        "mid-year check",
        "override",
        "reflow",
        "cliff",
        "leaver",
        "realm",
        "toil",
    ),
    "russian": (
        "backfill",
        "cliff",
        "cohort",
        "leaver",
        "override",
        "owner",
        "sponsor",
        "toil",
    ),
    "spanish": (
        "backfill",
        "blocker",
        "bonuses",
        "cliff",
        "leaver",
        "mutually boost",
        "organizational",
        "ledger",
        "offer",
        "owner",
        "rent seeking",
        "override",
        "toil",
    ),
}
REVIEW5G_EXACT_FORBIDDEN = {
    "japanese": {
        "rule_zg361_bottom_ratio": ("末尾",),
        "setting_zg361_ratio_relaxed_desc": ("末尾",),
        "setting_zg361_ratio_off_desc": ("末尾",),
        "zg361_purge_interaction": ("末位",),
        "zg361_force_retire_interaction": ("末位",),
        "zg361_pip_desc": ("末端",),
        "zg361.1.desc": ("末端",),
        "zg361.5.desc": ("末端",),
        "zg361.11.desc": ("やい行",),
        "zg361m.32.a": ("翻案",),
        "zg361m.76.a": ("翻案",),
        "zg361m.295.b": ("vesting",),
        "zg361m.359.t": ("翻案",),
    },
    "korean": {
        "zg361_demoted_desc": ("말년 퇴출",),
        "zg361.4.desc": ("말등 탈락",),
        "zg361m.361.b": ("헌법",),
    },
    "spanish": {
        "zg361m.296.a": ("vesting",),
        "zg361m.347.t": ("anulación",),
        "zg361m.347.a": ("anulación",),
    },
    "german": {
        "zg361_mechanism_choice_c_tt": ("policy", "review"),
        "zg361m.3.a": ("coaching-review", "reset", "managementzeit"),
        "zg361m.61.a": ("narrative", "template"),
        "zg361m.84.t": ("vesting",),
        "zg361m.84.a": ("vesting",),
        "zg361m.85.a": ("vesting", "peers"),
        "zg361m.114.t": ("manager-credit",),
        "zg361m.114.b": ("star", "output", "credit"),
        "zg361m.119.a": ("ramp-up", "mismatch"),
        "zg361m.121.a": ("skip-level-review",),
        "zg361m.123.a": ("manager", "reviewer-credit"),
        "zg361m.277.b": ("low performer",),
        "zg361m.280.a": ("cohort", "service-"),
        "zg361m.296.t": ("vesting",),
        "zg361m.347.t": ("override",),
        "zg361m.347.a": ("override",),
    },
    "french": {
        "zg361m.20.b": ("sponsor", "packaging"),
        "zg361m.41.a": ("ramp-up",),
        "zg361m.130.b": ("performer",),
        "zg361m.277.b": ("performer",),
    },
}
REVIEW5J_EXACT_FORBIDDEN = {
    "japanese": {
        "zg361m.112.t": ("stay interview",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
        "zg361m.340.t": ("wip",),
    },
    "korean": {
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
        "zg361m.340.t": ("wip",),
    },
    "german": {
        "zg361m.112.t": ("stay interview",),
        "zg361_next_mechanism_decision": ("performance policy",),
        "zg361_scoreboard_tab_system": ("policy", "cockpit"),
        "zg361_ledger_title": ("policy", "dashboard"),
        "zg361_ledger_explainer": ("burnout", "policy"),
        "zg361_ledger_policy_debt": ("policy",),
        "zg361m.2.a": ("baselines", "reset"),
        "zg361m.3.t": ("mid-cycle-check-in", "reset"),
        "zg361m.3.b": ("reset",),
        "zg361m.11.t": ("skip-level", "steward"),
        "zg361m.11.b": ("skip-level", "manager"),
        "zg361m.26.a": ("skip-level",),
        "zg361m.28.t": ("review",),
        "zg361m.31.b": ("review",),
        "zg361m.42.a": ("review",),
        "zg361m.48.a": ("review",),
        "zg361m.54.a": ("template", "manager"),
        "zg361m.56.b": ("manager", "output", "skip-level"),
        "zg361m.58.t": ("skip-level",),
        "zg361m.58.a": ("skip-level", "audit", "manager"),
        "zg361m.58.b": ("skip-level", "manager"),
        "zg361m.104.b": ("output", "pay-inversion", "pipeline"),
        "zg361m.111.a": ("mismatch",),
        "zg361m.116.b": ("manager", "output"),
        "zg361m.120.b": (
            "star",
            "output",
            "ramp-",
            "retention",
            "management",
            "pipeline",
        ),
        "zg361m.141.b": ("skip-level",),
        "zg361m.178.t": ("narrative",),
        "zg361m.213.t": ("review",),
        "zg361m.343.b": ("review",),
        "zg361m.355.b": ("output",),
        "zg361m.356.b": ("output",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
    },
    "polish": {
        "zg361m.112.t": ("stay interview",),
        "zg361m.2.a": ("baseline", "reset"),
        "zg361m.3.t": ("check-in", "reset"),
        "zg361m.3.a": ("coaching", "reset"),
        "zg361m.26.a": ("skip-level",),
        "zg361m.121.a": ("skip-level",),
        "zg361m.141.b": ("skip-level",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
    },
    "spanish": {
        "zg361m.11.t": ("skip-level", "steward"),
        "zg361m.24.b": ("output",),
        "zg361m.26.a": ("skip-level",),
        "zg361m.41.a": ("ramp-up",),
        "zg361m.92.b": ("contributor", "output"),
        "zg361m.114.b": ("output",),
        "zg361m.116.b": ("output",),
        "zg361m.120.b": ("output", "managers"),
        "zg361m.121.a": ("skip-level",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
        "zg361m.340.t": ("wip",),
    },
    "french": {
        "zg361m.112.t": ("stay interview",),
        "zg361m.26.a": ("skip-level",),
        "zg361m.104.b": ("output",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
        "zg361m.340.t": ("wip",),
    },
    "russian": {
        "zg361m.112.t": ("stay interview",),
        "zg361m.26.a": ("skip-level",),
        "zg361m.121.a": ("skip-level",),
        "zg361m.256.a": ("sla",),
        "zg361m.259.t": ("sla",),
    },
}
FINAL_EXACT_FORBIDDEN = {
    "german": {
        "zg361.4.desc": ("performance improvement plan",),
        "zg361m.340.t": ("work-in-progress",),
        "zg361m.347.a": ("verantwortlichen",),
    },
    "french": {
        "zg361m.85.a": ("packages de renouvellement",),
        "zg361m.136.t": ("préc réunion",),
    },
    "korean": {
        "zg361m.361.b": ("즉시 배달",),
    },
    "russian": {
        "zg361m.202.a": ("named supporters",),
    },
    "spanish": {
        "zg361m.29.a": ("claw back",),
        "zg361m.344.b": ("elbonus",),
    },
}
REVIEW6C_EXACT_FORBIDDEN = {
    "french": {
        "zg361.4.desc": ("dernier tiers",),
    },
    "japanese": {
        "zg361_grade_325_desc": ("自国庫", "人事評価 -60"),
        "zg361.4.desc": ("3.25 を付けば",),
        "zg361m.14.desc": ("地方財庫",),
        "zg361m.14.a": ("俸禄停止",),
        "zg361m.18.desc": ("地方財庫",),
        "zg361m.18.a": ("財庫", "俸禄減成", "決済時"),
    },
    "korean": {
        "zg361m.14.a": ("봉록 중단", "항목을 항목별로"),
    },
    "russian": {
        "zg361m.21.desc": ("repeatedly",),
    },
}
OFFICIAL_RESOURCE_KEYS = {
    "zg361_grade_325_desc",
    "zg361.4.desc",
    "zg361m.14.desc",
    "zg361m.18.desc",
    "zg361m.18.a",
}
CJK = re.compile(r"[一-龯]")
KANA = re.compile(r"[ぁ-んァ-ン]")
HANGUL = re.compile(r"[가-힣]")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
LANGUAGE_PROMPT_SUFFIX = {
    "japanese": (
        " Write only natural modern Japanese. The Simplified Chinese reference is "
        "meaning-only: never copy its wording or simplified glyph forms. Translate every "
        "sentence fully with normal Japanese kana and kanji. Never leave Latin fragments "
        "such as backfill, blocker, cliff, cohort, leaver, manager, nomination, narrative, "
        "onboarding, owner, override, rent seeking, scapegoat, sponsor, one, or usal, and render Chinese management compounds "
        "as natural Japanese. Sample audit means 抜き取り検査, never a lottery. Internal inversion "
        "means an internal pay/reward inversion, never sexual or psychological perversion. 工時 is "
        "not natural Japanese; use 作業時間 or 労働時間. Translate toil, throughput, and golden "
        "handcuffs into natural Japanese. A reversed rating means an evaluation was overturned, "
        "not merely withdrawn or cancelled. In "
        "policy #353, preserve the explicit compliance-over-capacity motive. Use 最下位 for the "
        "bottom-ranked tier or person, never the Chinese-style 末位/末端 or the list-tail word 末尾. "
        "Never output 本層; use この階層 or 現在の階層. "
        "For reversals in policies #32, #76, and #359, use 評価の覆り or 判定の覆り, never 翻案. "
        "Policy #119 must name the requester, selector, and final approver. Translate vesting as "
        "権利確定 or 段階的権利確定 rather than retaining Latin text. Translate Stay Interview "
        "as 定着面談 or 在籍継続面談, SLA as サービス水準合意, and WIP as 進行中作業; do not "
        "retain the English acronym in parentheses."
        " For the fourfold 3.25 settlement, use 地方国庫 for local treasury, 個人の金 or "
        "個人の所持金 for personal gold, 功徳 for merit, and 俸給 or 俸禄 for salary. Use "
        "natural 俸給減額 for salary reduction, never literal compounds such as 地方財庫, "
        "地方財務, 自国庫, 個人資金, 人事評価 -60, 功績, or 俸禄減成."
    ),
    "korean": (
        " Write only natural modern Korean in Hangul. The Simplified Chinese reference is "
        "meaning-only: never copy Chinese wording and never use Hanja. Jingcha means a "
        "periodic large-scale administrative performance review of officials, never police. "
        "Celestial government is not the Japanese emperor. In zg361_demoted_desc only, salary "
        "halved must explicitly remain 절반 or 50%. Translate cohort as 평가 집단 or 평가군 and translate every English "
        "management term (including governance, sponsor, owner, blocker, backfill, offer, cohort, "
        "vesting, cliff, ramp, delivery, override, and disciplinary) into idiomatic Hangul. Translate Good/Bad "
        "Leaver labels into natural Hangul rather than retaining English. Owner must be 담당자 or "
        "책임자 and blocker must be 방해 요인 or 차단자; never output those Latin spellings. "
        "Down-weight suspected mutual "
        "boosters by lowering those people's evaluation weight. Rent seeking is 지대 추구, "
        "a rating-not-guaranteed clause must say 등급 미보장, and crisis overrides are "
        "temporary rule exceptions or bypasses rather than redefinitions. Use a consistent "
        "concise 해라체 UI register rather than switching to 합니다체. In policy #351, controls "
        "means a control group (대조군 or 통제군), not generic control. A second raise within "
        "the same grade is pay calibration, not promotion; dual credit means attributing performance "
        "credit to both lines, and personal contribution growth is not personal development. Avoid "
        "duplicated adverbs such as 즉시 ... 즉시."
        " For core keys zg361.2.desc, zg361.3.desc, and zg361.4.desc, write 평가군 or "
        "평가 집단 and never output the Latin spelling cohort. Bottom-tier elimination is 최하위 "
        "탈락 or 최하위 퇴출, never 말년 퇴출 or 말등 탈락. A hard organizational charter is "
        "강경 헌장, never 헌법. In the current 3.25 text, preserve all four Arabic-numbered "
        "consequences: local treasury -50, personal gold -25, merit -60 where supported, and "
        "salary -25% for one year where applicable. In policy #361, immediate delivery means "
        "immediate work delivery or 납품/성과 인도, never food/package 배달. Translate SLA as "
        "서비스 수준 협약 and WIP as 진행 중 작업, without retaining the English acronyms. "
        "Never mix Cyrillic or any other foreign script into Korean."
        " In policy #21, short raise means a temporary pay/salary increase such as 단기 녹봉 "
        "인상, never a promotion or 승급. In #263, temporary loan means temporary secondment: "
        "use exactly the meaning 임시 파견을 무기한 연장하고, 프로젝트 종료 후에야 소속을 "
        "결정한다; never 차관 or 책임자를 정한다. In #283, the promotion has happened but its pay has not "
        "caught up; write No.283 · 무급 승진의 급여 반영 기한 or an equally explicit natural "
        "Korean title, never 무승급."
    ),
    "russian": (
        " Write natural Russian in Cyrillic. Never copy Chinese reference fragments or leave "
        "English source phrases untranslated. Translate backfill, owner, sponsor, override, toil, cliff, and "
        "Good/Bad Leaver into idiomatic Russian. Never output the Latin word cohort; translate it as "
        "группа оценки or пул оценки, and "
        "translate non-crisis as вне кризиса rather than pre-crisis. "
        "Waiving proven performers means releasing them from a test or assessment, never releasing "
        "or firing the people themselves. Preserve scope, resources, and signed accountability as "
        "distinct rule inputs; do not replace them with schedule or signed choice. In policy #351, "
        "controls means контрольная группа."
        " For core keys zg361.2.desc, zg361.3.desc, and zg361.4.desc, write оценочная "
        "группа and never output the Latin spelling cohort. In policies #295 and #296, "
        "cliff is a waiting period before benefits vest; use a natural Russian phrase for "
        "that waiting period and never output the Latin spelling cliff. For a 3.25 result, preserve "
        "all four Arabic-numbered consequences: local treasury -50, personal gold -25, merit -60 "
        "where supported, and salary -25% for one year where applicable. In #202 translate named "
        "supporters fully into natural Russian. Translate skip-level "
        "review as проверка вышестоящим руководителем and SLA as соглашение об уровне услуг, "
        "without retaining the English spelling. Translate Stay Interview as интервью по удержанию "
        "without an English parenthetical."
        " In policy #21, short raise must explicitly be a short-term increase in жалованье, "
        "зарплата, or оклад, never an unspecified promotion; render repeatedly as неоднократно "
        "or repeatedly recurring in natural Russian, with no Latin word."
    ),
    "french": (
        " Never copy Chinese reference fragments or leave English source phrases untranslated. "
        "When down-weighting suspected mutual boosters, lower the evaluation weight of the "
        "people suspected of rating one another too highly, not the suspicion itself. Render "
        "this explicitly as the evaluation weight assigned to personnes soupçonnées de se surnoter "
        "mutuellement; the people must be the grammatical object. Render "
        "high performers as people or employees, never an untranslated English label. Do not "
        "mix Spanish or Portuguese words into French. Translate backfill, owner, override, toil, cliff, "
        "and Good/Bad Leaver rather than retaining English. In policy #351, controls means a control "
        "group (groupe témoin or groupe de contrôle), not generic controls."
        " In policies #295 and #296, cliff is the initial waiting period before benefits "
        "vest; use délai de carence or another natural French phrase and never output cliff. "
        "Translate sponsor as parrain or responsable, ramp-up as montée en compétence, low "
        "performer as salarié peu performant, and packaging as mise en scène or présentation."
        " Translate skip-level as entretien avec le supérieur indirect, output as résultats, SLA "
        "as accord de niveau de service, and WIP as travail en cours, without retaining English "
        "spellings. Translate Stay Interview as entretien de fidélisation or entretien de rétention "
        "without an English parenthetical. In policy #85 use offres or ensembles de renouvellement, "
        "never the Franglais packages. In #136 produce a grammatical title for a small cross-manager "
        "pre-calibration meeting. Bottom-tier elimination means elimination of the lowest-ranked "
        "tier or person: use niveau le plus bas, échelon le plus bas, or les moins bien classés, "
        "never dernier tiers (bottom third) or vague dernier niveau. In policy #130, rebrand means "
        "requalifier or rebaptiser, never rebailler."
    ),
    "german": (
        " Never copy Chinese reference fragments or leave English source phrases untranslated. "
        "Use idiomatic German rather than English ledger/reserve/Offer/Owner/Blocker/Backfill/Toil/Shared "
        "Services fragments, and give ledger "
        "instructions a complete verb. Translate Performer as Leistungsträger or another natural "
        "person noun. In policy #351, controls means a Kontrollgruppe. Address the player "
        "consistently as informal singular du/dein, never Sie/Ihr/euer, and translate Bottom Tier. "
        "Leapfrog promotion means promoting a person over a rank or level, never skipping the person. "
        "In policies #27 and #339, translate owner as Verantwortlicher and blocker as Hindernis "
        "or Blockierer; never output the Latin spellings owner or blocker. In policy #205, "
        "translate toil as unnötige Routinearbeit or Arbeitslast and never output toil. In "
        "policies #295 and #296, cliff is a Sperrfrist or Wartefrist before benefits vest; "
        "never output the Latin spelling cliff. For the specifically requested policy keys, "
        "also localize Policy, Review, Reset, Narrative, Template, Vesting, Peers, Manager, "
        "Credit, Star, Output, Ramp-up, Mismatch, Skip-Level, Low Performer, Cohort, Service, "
        "and Override instead of leaving those English words inside German compounds. For #84, "
        "#85, and #296, use Anwartschaft or Anspruchserwerb instead of Vesting. For #121, use "
        "hierarchieübergreifende Überprüfung instead of Skip-Level-Review. For #277, use "
        "leistungsschwacher Mitarbeiter instead of Low Performer. For #347, use manuelle "
        "Ermessensanpassung instead of Override. In #85, use vergleichbare Beschäftigte or "
        "Kollegen instead of Peers. Also localize remaining English: Richtlinie for Policy, "
        "Übersicht for Dashboard/Cockpit, Überlastung for Burnout, Ausgangswert for Baseline, "
        "Neufestsetzung for Reset, Zwischengespräch for Mid-Cycle Check-in, hierarchieübergreifend "
        "for Skip-Level, Personalbeauftragter for Steward, Überprüfung for Review, Vorlage for "
        "Template, Führungskraft for Manager, Leistung or Ergebnis for Output, Prüfung for Audit, "
        "Gehaltsumkehr for Pay Inversion, Nachwuchspool for Pipeline, Fehlbesetzung for Mismatch, "
        "Spitzenkraft for Star, Einarbeitung for Ramp, Bindung for Retention, beschreibend for "
        "Narrative, and Dienstgütevereinbarung for SLA. In #119 name HC-Anfragender, "
        "Auswahlverantwortlicher, and Genehmiger as three people. Translate Stay Interview as "
        "Bindungsgespräch or Bleibegespräch without an English parenthetical. Translate Performance "
        "Improvement Plan as Leistungsverbesserungsplan (PIP), and Work-in-Progress Limit as a natural "
        "German limit on laufende/gleichzeitige Arbeit. In #347, bearer is the distinct person bearing "
        "the consequence or burden (Lastenträger/Träger der Folgen), not merely Verantwortlicher. "
        "In #341, use fully paired German quotation marks such as „Phase eins abgeschlossen“ or no "
        "quotation marks; never add an ASCII quotation mark."
    ),
    "polish": (
        " Never copy Chinese reference fragments or leave English source phrases untranslated. "
        "Translate backfill as obsadzenie zastępstwa or uzupełnienie wakatu, and translate "
        "deliverable, deadline, realm, override, toil, cliff, Good/Bad Leaver, credit, and visible hero "
        "credit into idiomatic Polish. In "
        "performance-attribution contexts, credit means uznanie or zasługa, never financial kredyt. When "
        "a reorganization requires superior ownership, the superior must take responsibility for "
        "the list rather than merely supervise it. In policy #351, controls means grupa kontrolna."
        " Translate baseline as punkt odniesienia, reset as ponowne ustalenie, coaching as rozmowa "
        "rozwojowa, skip-level review as przegląd przez przełożonego wyższego szczebla, and SLA as "
        "umowa o poziomie usług; do not retain the English spelling. Translate Stay Interview as "
        "rozmowa retencyjna without an English parenthetical. In #283, promotion always means the "
        "career advancement awans, never a sales promotion or promocja. Preserve the No.283 title number."
    ),
    "spanish": (
        " Never copy Chinese reference fragments or leave English source phrases untranslated. "
        "Translate backfill as cobertura de la vacante or reemplazo, and translate bonuses, offer, "
        "owner, blocker, override, toil, rent seeking, cliff, Good/Bad Leaver, ledger, organizational wording, and "
        "visible hero credit into idiomatic Spanish. Render "
        "high performers as people or employees, not the abstract phrase Altos Rendimientos. "
        "Reward nominations are candidaturas, not appointments; dual credit is shared attribution, "
        "not financial credit; superior ownership means taking responsibility, not property ownership. "
        "In policy #351, controls means grupo de control. In policies #295 and #296, cliff "
        "is the initial waiting period before benefits vest; use periodo de carencia or another "
        "natural Spanish phrase and never output cliff. Translate vesting as consolidación de "
        "derechos. Manager override means a small manual discretionary adjustment budget "
        "(ajuste manual o discrecional), never cancellation or anulación. Translate skip-level "
        "review as revisión por el superior indirecto, steward as responsable, output as resultados, "
        "ramp-up as incorporación, individual contributor as especialista individual, manager as "
        "responsable, SLA as acuerdo de nivel de servicio, and WIP as trabajo en curso; do not "
        "retain the English spellings or acronyms. In #29 translate claw back rewards as recuperar or "
        "reclamar las recompensas. In #344 keep crédito and bonificación as two separate, correctly "
        "spaced nouns."
        " In policy #21, short raise is an aumento salarial temporal, not a vague promotion, and "
        "repeatedly unrewarded 3.75 talent must remain no recompensado, never premiado."
    ),
}
AUDIT_FORMAT_VERSION = 1
AUDIT_PRODUCT_ID = "mod_zhongguo_style"
AUDIT_CHECKS = (
    "key_order",
    "protected_tokens",
    "quality",
    "no_english_placeholders",
    "target_script",
)
DEFAULT_AUDIT_REPORT = MOD_ROOT / "docs" / "release-localization-audit.json"


@dataclass(frozen=True)
class SourceSpec:
    name: str
    english: Path
    chinese: Path
    context: str


@dataclass(frozen=True)
class Batch:
    source: str
    name: str
    keys: tuple[str, ...]


SOURCES = {
    "core": SourceSpec(
        "core",
        MOD_ROOT / "localization" / "english" / "zg361_l_english.yml",
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml",
        CORE_CONTEXT,
    ),
    "mechanisms": SourceSpec(
        "mechanisms",
        MOD_ROOT / "localization" / "english" / "zg361_mechanisms_l_english.yml",
        MOD_ROOT
        / "localization"
        / "simp_chinese"
        / "zg361_mechanisms_l_simp_chinese.yml",
        MECHANISM_CONTEXT,
    ),
}


class ReleaseLocalizationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new_or_equal(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ReleaseLocalizationError(f"refusing to overwrite differing artifact: {path}")
        return
    path.write_bytes(data)


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def git_commit(reference: str) -> str:
    """Resolve one immutable commit without invoking a shell."""
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise ReleaseLocalizationError(
            f"cannot resolve baseline Git reference {reference!r}"
        )
    commit = completed.stdout.decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", commit) is None:
        raise ReleaseLocalizationError(
            f"baseline Git reference did not resolve to one commit: {reference!r}"
        )
    return commit.lower()


def git_blob(commit: str, relative_path: str) -> bytes:
    """Read one exact tracked source blob for source-change provenance."""
    if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
        raise ReleaseLocalizationError(
            f"baseline source path is not repository-relative: {relative_path}"
        )
    completed = subprocess.run(
        ["git", "show", f"{commit}:{Path(relative_path).as_posix()}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise ReleaseLocalizationError(
            f"cannot read baseline source {relative_path} from {commit}"
        )
    return completed.stdout


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def audit_file_record(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPO_ROOT.resolve()).as_posix(),
        "size": resolved.stat().st_size,
        "sha256": sha256(resolved).lower(),
    }


def release_audit_payload(
    source_paths: list[Path], target_paths: list[Path]
) -> dict[str, object]:
    return {
        "format_version": AUDIT_FORMAT_VERSION,
        "product_id": AUDIT_PRODUCT_ID,
        "result": "GREEN",
        "checks": list(AUDIT_CHECKS),
        "source_files": [
            audit_file_record(path)
            for path in sorted(set(source_paths), key=lambda row: row.as_posix())
        ],
        "target_files": [
            audit_file_record(path)
            for path in sorted(set(target_paths), key=lambda row: row.as_posix())
        ],
    }


def build_batches() -> tuple[Batch, ...]:
    core = tuple(minimax.parse_ck3_localization(SOURCES["core"].english))
    mechanism = tuple(minimax.parse_ck3_localization(SOURCES["mechanisms"].english))
    batches: list[Batch] = []
    for index in range(0, len(core), 80):
        batches.append(
            Batch("core", f"core_{index // 80 + 1:02d}", core[index : index + 80])
        )
    common = tuple(key for key in mechanism if MECHANISM_KEY.fullmatch(key) is None)
    by_id: dict[int, list[str]] = {identifier: [] for identifier in range(1, 362)}
    for key in mechanism:
        match = MECHANISM_KEY.fullmatch(key)
        if match:
            by_id[int(match.group(1))].append(key)
    for identifier, keys in by_id.items():
        if len(keys) != 5:
            raise ReleaseLocalizationError(
                f"mechanism {identifier:03d} has {len(keys)} localization keys, expected 5"
            )
    for start in range(1, 362, 25):
        end = min(start + 24, 361)
        keys = tuple(
            key
            for identifier in range(start, end + 1)
            for key in by_id[identifier]
        )
        if start == 1:
            keys = common + keys
        batches.append(Batch("mechanisms", f"mechanisms_{start:03d}_{end:03d}", keys))
    covered = tuple(key for batch in batches if batch.source == "mechanisms" for key in batch.keys)
    if covered != mechanism:
        raise ReleaseLocalizationError("mechanism localization batching changed source key order")
    if len(batches) != 18:
        raise ReleaseLocalizationError(f"expected 18 translation batches, got {len(batches)}")
    return tuple(batches)


def plan_payload() -> dict[str, object]:
    batches = build_batches()
    return {
        "schema": 1,
        "model": minimax.MODEL,
        "languages": LANGUAGES,
        "protected_terms": list(PROTECTED_TERMS),
        "sources": {
            name: {
                "english": spec.english.relative_to(REPO_ROOT).as_posix(),
                "english_sha256": sha256(spec.english),
                "simp_chinese": spec.chinese.relative_to(REPO_ROOT).as_posix(),
                "simp_chinese_sha256": sha256(spec.chinese),
            }
            for name, spec in SOURCES.items()
        },
        "batches": [
            {"source": batch.source, "name": batch.name, "keys": list(batch.keys)}
            for batch in batches
        ],
        "request_count": len(batches) * len(LANGUAGES),
    }


def candidate_path(root: Path, batch: Batch, language: str) -> Path:
    return root / "candidates" / batch.source / batch.name / f"{language}.json"


def load_candidate_payload(path: Path, source: dict[str, str]) -> dict[str, str]:
    """Load a structurally valid candidate without accepting its translated values."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseLocalizationError(f"cannot read candidate {path}: {error}") from error
    candidate = minimax.extract_candidate(
        json.dumps(payload, ensure_ascii=False), tuple(source)
    )
    for key, value in candidate.items():
        if "\r" in value or "\n" in value:
            raise ReleaseLocalizationError(f"candidate contains a literal newline: {path} [{key}]")
    return candidate


def load_candidate(path: Path, source: dict[str, str]) -> dict[str, str]:
    candidate = load_candidate_payload(path, source)
    minimax.assert_protected_tokens(source, candidate, PROTECTED_TERMS)
    return candidate


def is_translatable_english(value: str) -> bool:
    stripped = TECHNICAL_WORDS.sub("", value)
    stripped = minimax.PROTECTED.sub("", stripped)
    return re.search(r"[A-Za-z]{2,}", stripped) is not None


def candidate_residuals(
    english: dict[str, str], candidate: dict[str, str], language: str | None = None
) -> list[str]:
    return [
        key
        for key, value in candidate.items()
        if value == english[key]
        and is_translatable_english(value)
        and key not in ALLOWED_IDENTICAL.get(language or "", set())
    ]


def copied_english_phrase(source: str, candidate: str, words: int = 4) -> str | None:
    source_words = [word.casefold() for word in LATIN_WORD.findall(source)]
    candidate_words = [word.casefold() for word in LATIN_WORD.findall(candidate)]
    if len(source_words) < words or len(candidate_words) < words:
        return None
    source_ngrams = {
        tuple(source_words[index : index + words])
        for index in range(len(source_words) - words + 1)
    }
    for index in range(len(candidate_words) - words + 1):
        phrase = tuple(candidate_words[index : index + words])
        if phrase in source_ngrams:
            return " ".join(phrase)
    return None


def targeted_quality_errors(key: str, value: str, language: str) -> list[str]:
    """Reject concrete semantic and mixed-language regressions found in review."""
    errors: list[str] = []
    folded = value.casefold()
    residual_visible = minimax.PROTECTED.sub("", value).casefold()

    for residual in LANGUAGE_FORBIDDEN_RESIDUALS.get(language, ()):
        if re.search(
            rf"(?<![A-Za-z]){re.escape(residual)}(?![A-Za-z])",
            residual_visible,
        ):
            errors.append(f"{key}: contains untranslated or mistranslated fragment {residual!r}")

    for fragment in REVIEW5G_EXACT_FORBIDDEN.get(language, {}).get(key, ()):
        if fragment.casefold() in residual_visible:
            errors.append(
                f"{key}: contains reviewed release-blocker fragment {fragment!r}"
            )
    for fragment in REVIEW5J_EXACT_FORBIDDEN.get(language, {}).get(key, ()):
        if fragment.casefold() in residual_visible:
            errors.append(
                f"{key}: contains reviewed non-protected English fragment {fragment!r}"
            )
    for fragment in FINAL_EXACT_FORBIDDEN.get(language, {}).get(key, ()):
        if fragment.casefold() in residual_visible:
            errors.append(
                f"{key}: contains final independently reviewed blocker {fragment!r}"
            )
    for fragment in REVIEW6C_EXACT_FORBIDDEN.get(language, {}).get(key, ()):
        if fragment.casefold() in residual_visible:
            errors.append(
                f"{key}: contains reviewed source-migration blocker {fragment!r}"
            )

    fourfold_keys = {
        "zg361_grade_325_desc",
        "zg361.4.desc",
        "zg361m.18.desc",
    }
    if key in fourfold_keys:
        standalone_25 = re.findall(r"(?<![\d.])25(?!\d)", value)
        if (
            re.search(r"(?<![\d.])50(?!\d)", value) is None
            or len(standalone_25) < 2
            or re.search(r"(?<![\d.])60(?!\d)", value) is None
            or re.search(r"(?<!\d)25\s*%", value) is None
        ):
            errors.append(
                f"{key}: does not preserve all four exact 3.25 consequences "
                "(50, 25, 60, and 25%)"
            )
    if key == "zg361m.14.desc" and (
        "3.25" not in value or re.search(r"(?<!\d)25\s*%", value) is None
    ):
        errors.append(
            f"{key}: does not preserve the appeal's 3.25 refund and 25% salary-stop semantics"
        )
    if key == "zg361m.14.a" and language == "japanese" and re.search(
        r"(?:俸給|俸禄)(?:の)?(?:減額|控除).{0,8}(?:停止|終了)", value
    ) is None:
        errors.append(f"{key}: does not say to stop the salary reduction/deduction")
    if key == "zg361m.14.a" and language == "korean" and re.search(
        r"(?:녹봉|봉록|봉급).{0,8}(?:감액|공제).{0,8}(?:중단|종료)", value
    ) is None:
        errors.append(f"{key}: does not say to stop the salary reduction/deduction")
    if key == "zg361m.14.a" and language == "korean" and re.search(
        r"(?:합|습)니다[.!]?\s*$", value
    ):
        errors.append(f"{key}: switches from concise UI register into formal 합니다체")
    if key == "zg361m.21.desc" and any(
        rating not in value for rating in ("3.75", "3.5", "3.25")
    ):
        errors.append(
            f"{key}: does not preserve the 3.75/3.5/3.25 reward matrix"
        )
    if key == "zg361m.21.desc" and language == "korean" and re.search(
        r"(?:녹봉|봉급|급여|보수).{0,10}인상|인상.{0,10}(?:녹봉|봉급|급여|보수)",
        value,
    ) is None:
        errors.append(f"{key}: does not express the short raise as a Korean pay increase")
    if key == "zg361m.21.desc" and language == "russian" and re.search(
        r"(?:повышени\w*\s+(?:жалован|зарплат|оклад)\w*|(?:жалован|зарплат|оклад)\w*\s+повышени\w*)",
        folded,
    ) is None:
        errors.append(f"{key}: does not express the short raise as a Russian pay increase")
    if key == "zg361m.21.desc" and language == "spanish":
        if re.search(
            r"(?:aumento|subida)\s+(?:salarial|de\s+(?:salario|sueldo))",
            folded,
        ) is None:
            errors.append(f"{key}: does not express the short raise as a Spanish pay increase")
        if re.search(
            r"(?:no|sin)\s+(?:ser\s+)?(?:recompens|premiad)", folded
        ) is None:
            errors.append(f"{key}: reverses or drops the repeatedly-unrewarded talent condition")
    if key == "zg361.4.desc" and language == "french" and re.search(
        r"(?:(?:niveau|échelon)\s+le\s+plus\s+bas|(?:personnes?|agents?)\s+(?:les\s+)?moins\s+bien\s+class)",
        folded,
    ) is None:
        errors.append(f"{key}: does not explicitly express the lowest-ranked tier or people")
    if key in OFFICIAL_RESOURCE_KEYS and language == "japanese":
        if "地方国庫" not in value:
            errors.append(f"{key}: does not use 地方国庫 for the local treasury")
        if re.search(r"個人の(?:所持)?金", value) is None:
            errors.append(f"{key}: does not use 個人の金/個人の所持金 for personal gold")
        if "功徳" not in value:
            errors.append(f"{key}: does not use CK3's official Japanese merit term 功徳")
        if key == "zg361m.18.a" and re.search(r"(?:精算|決算)時", value) is None:
            errors.append(f"{key}: does not use a natural settlement/accounting term")
    if key == "zg361.4.desc" and language == "japanese" and re.search(
        r"(?:もう一度|再び).{0,12}3\.25.{0,10}(?:取れば|付けられれば|評価されれば|受ければ)",
        value,
    ) is None:
        errors.append(f"{key}: does not state another 3.25 in grammatical Japanese")
    if key in OFFICIAL_RESOURCE_KEYS and language == "korean":
        if re.search(r"지방\s*(?:국고|금고)", value) is None:
            errors.append(f"{key}: does not state the local treasury in Korean")
        if "개인 금화" not in value:
            errors.append(f"{key}: does not preserve personal gold as 개인 금화")
        if "공덕" not in value:
            errors.append(f"{key}: does not use CK3's official Korean merit term 공덕")

    control_group_patterns = {
        "french": r"groupe\s+(?:témoin|de\s+contrôle)",
        "german": r"kontrollgruppe",
        "korean": r"(?:대조|통제)(?:군|\s*집단)",
        "polish": r"grup\w*\s+kontrol",
        "russian": r"контрольн\w*\s+груп",
        "spanish": r"grupo\s+de\s+control",
    }
    if key == "zg361m.351.a" and language in control_group_patterns:
        if re.search(control_group_patterns[language], folded) is None:
            errors.append(f"{key}: does not explicitly preserve the control-group design")

    if language == "japanese":
        fragments = [fragment for fragment in JAPANESE_FORBIDDEN_FRAGMENTS if fragment in value]
        if fragments:
            errors.append(f"{key}: contains non-idiomatic Chinese fragment(s) {fragments!r}")
        latin = JAPANESE_FORBIDDEN_LATIN.search(minimax.PROTECTED.sub("", value))
        if latin:
            errors.append(f"{key}: contains stray Latin fragment {latin.group(0)!r}")
        if key == "zg361m.227.b" and re.search(r"(?<![A-Za-z])owner(?![A-Za-z])", value, re.I):
            errors.append(f"{key}: mixes English 'owner' into an otherwise Japanese phrase")
        reversal_terms = {
            "zg361m.12.b": ("翻案",),
            "zg361m.23.a": ("覆命", "撤回"),
            "zg361m.95.a": ("覆案",),
        }
        reviewed_terms = reversal_terms.get(key, ())
        if any(term in value for term in reviewed_terms):
            errors.append(f"{key}: uses a reviewed mistranslation for appeal or reversal")
        if key == "zg361.1.desc" and re.search(r"末尾(?:規則|淘汰)", value):
            errors.append(f"{key}: mistranslates bottom-tier as the end of a string")
        if key == "zg361m.272.a" and "報酬倒錯" in value:
            errors.append(f"{key}: mistranslates pay inversion as perversion")
        bottom_tier_keys = {
            "rule_zg361_bottom_ratio",
            "setting_zg361_ratio_relaxed_desc",
            "setting_zg361_ratio_off_desc",
            "zg361_purge_interaction",
            "zg361_force_retire_interaction",
            "zg361_pip_desc",
            "zg361.1.desc",
            "zg361.5.desc",
        }
        if key in bottom_tier_keys and "最下位" not in value:
            errors.append(f"{key}: does not express the bottom-ranked tier as 最下位")
        reversal_keys = {"zg361m.32.a", "zg361m.76.a", "zg361m.359.t"}
        if key in reversal_keys and "覆" not in value:
            errors.append(f"{key}: does not express an overturned evaluation or decision")
        if key == "zg361m.119.a" and re.search(
            r"(?:最終)?(?:承認者|決裁者)", value
        ) is None:
            errors.append(f"{key}: omits the final approver from the hiring feedback loop")
        if key == "zg361m.353.b" and re.search(
            r"(?:コンプライアンス|法令遵守|規則遵守)", value
        ) is None:
            errors.append(f"{key}: drops the explicit compliance-over-capacity motive")
    elif language == "korean":
        if "경찰" in value:
            errors.append(f"{key}: mistranslates Jingcha as police")
        if key == "setting_zg361_on_desc" and "천황" in value:
            errors.append(f"{key}: mistranslates celestial-government ruler as Japanese emperor")
        if key == "zg361_demoted_desc":
            if "봉록 반납" in value:
                errors.append(f"{key}: changes salary halved into salary surrender")
            if "절반" not in value and re.search(r"\b50\s*%", value) is None:
                errors.append(f"{key}: does not preserve salary-halved semantics")
        if key == "zg361m.50.b":
            if re.search(
                r"(?:쌍|두\s*사람|평가자|당사자|인물|사람)(?:을|를).*?가중치(?:를|을)\s*(?:낮|내리)",
                value,
            ):
                errors.append(f"{key}: uses a double-object construction instead of lowering the pair's weight")
            if not re.search(r"(?:가중치|비중|신뢰도)", value) or not re.search(
                r"(?:쌍|두\s*사람|평가자|당사자|인물|사람|이들)", value
            ):
                errors.append(f"{key}: does not clearly lower the suspected people's evaluation weight")
        if key == "zg361m.75.a" and re.search(r"(?:합니다|됩니다|습니다|입니다)", value):
            errors.append(f"{key}: switches abruptly into formal 합니다체")
        if key == "zg361m.95.a" and "번안" in value:
            errors.append(f"{key}: mistranslates review reversals as adaptations")
        if key == "zg361m.100.b" and "권력 뇌물" in value:
            errors.append(f"{key}: mistranslates rent seeking as power bribery")
        if key == "zg361m.150.a" and "비예정 등급 조항" in value:
            errors.append(f"{key}: does not naturally express that the rating is not guaranteed")
        if key == "zg361m.200.b" and "제한 없는 재정의" in value:
            errors.append(f"{key}: mistranslates unrestricted overrides as unlimited redefinitions")
        if key == "zg361m.130.t" and not any(
            prefix in value for prefix in ("#130", "No.130")
        ):
            errors.append(f"{key}: drops the policy number 130")
        if key == "zg361m.263.b":
            if (
                "파견" not in value
                or "소속" not in value
                or "차관" in value
                or "책임자" in value
            ):
                errors.append(
                    f"{key}: does not preserve temporary secondment and team affiliation"
                )
        if key == "zg361m.283.t":
            if not any(prefix in value for prefix in ("#283", "No.283")):
                errors.append(f"{key}: drops the policy number 283")
            if "승진" not in value or re.search(r"(?:무급|무보수|급여\s*(?:없|미지급))", value) is None:
                errors.append(f"{key}: does not express an unpaid or title-only promotion")
            if re.search(r"(?:기한|시한|마감)", value) is None:
                errors.append(f"{key}: does not express the pay-adjustment deadline")
        if key == "zg361m.285.t" and "승진" in value:
            errors.append(f"{key}: mistranslates a same-grade second raise as promotion")
        if key == "zg361m.301.a" and "개인 성장" in value:
            errors.append(f"{key}: mistranslates personal contribution growth as personal development")
        if key == "zg361m.315.a" and "신규 부서 동시 집행" in value:
            errors.append(f"{key}: drops dual performance-credit attribution")
        if key == "zg361m.330.b" and "즉시 외부에서 즉시" in value:
            errors.append(f"{key}: contains a reviewed duplicated Korean adverb")
        if key == "zg361m.361.b" and "어짜는" in value:
            errors.append(f"{key}: contains reviewed Korean corruption '어짜는'")
        if key == "zg361m.361.b" and "헌장" not in value:
            errors.append(f"{key}: does not translate organizational charter as 헌장")
    elif language == "polish":
        if key == "zg361.30.b" and "ukar" not in folded:
            errors.append(f"{key}: does not clearly express punishment")
        if key == "zg361m.24.a" and "uzgodnić" in folded:
            errors.append(f"{key}: retains the reviewed Polish infinitive error")
        if key == "zg361m.325.a":
            has_assessment = re.search(
                r"\b(?:test|sprawdzian|ocen|weryfikac)", folded
            ) is not None
            releases_people = re.search(
                r"\b(?:zwalni|zwolni)\w*\s+sprawdzon\w*\s+\w+", folded
            )
            explicitly_from_assessment = re.search(
                r"\b(?:zwalni|zwolni)\w*\s+sprawdzon\w*\s+\w+\s+z(?:e)?\s+"
                r"(?:\w+\s+){0,2}(?:test|sprawdzian|ocen|weryfikac)",
                folded,
            )
            if releases_people and explicitly_from_assessment is None:
                errors.append(f"{key}: reads as firing proven performers rather than waiving a check")
            if not has_assessment:
                errors.append(f"{key}: does not explicitly waive a test or assessment")
        if key == "zg361m.125.b" and "kredytu bohatera" in folded:
            errors.append(f"{key}: literally translates visible hero credit instead of visible recognition")
        if key == "zg361m.305.a" and "nadzor" in folded:
            errors.append(f"{key}: reduces superior ownership of the list to mere supervision")
        if key == "zg361m.315.a" and "podwójnym kredytem" in folded:
            errors.append(f"{key}: mistranslates dual performance credit as financial credit")
        if key == "zg361m.283.t" and not any(
            prefix in value for prefix in ("#283", "No.283")
        ):
            errors.append(f"{key}: drops the policy number 283")
        if key == "zg361m.283.a":
            if "awan" not in folded or "promocj" in folded:
                errors.append(f"{key}: does not express career advancement as awans")
        performance_credit_keys = {
            "zg361m.252.b",
            "zg361m.262.a",
            "zg361m.273.a",
            "zg361m.315.a",
            "zg361m.326.a",
        }
        if key in performance_credit_keys and re.search(r"\bkredyt\w*\b", folded):
            errors.append(f"{key}: uses financial kredyt for performance attribution")
        if key == "zg361m.330.b" and "wyjdź ze starych pracowników" in folded:
            errors.append(f"{key}: contains a reviewed nonsensical action toward existing staff")
    elif language == "russian":
        if key.startswith("zg361m.1.") and "покварталь" in folded:
            errors.append(f"{key}: mistranslates itemized evidence as quarterly evidence")
        if key == "zg361m.75.a" and "оплачивая казну" in folded:
            errors.append(f"{key}: reverses the treasury-cost direction")
        if key == "zg361m.325.a" and re.search(
            r"от(?:\s+\w+){0,2}\s+(?:провер|оцен|испыт)", folded
        ) is None:
            errors.append(f"{key}: does not explicitly release proven performers from a test or assessment")
        if key == "zg361m.125.b" and "героического кредита" in folded:
            errors.append(f"{key}: literally translates visible hero credit as a financial credit")
        if key == "zg361m.305.a" and "докризисн" in folded:
            errors.append(f"{key}: mistranslates non-crisis reorganizations as pre-crisis reorganizations")
        if key == "zg361m.335.a" and (
            "сдвига сроков" in folded or "подписанного выбора" in folded
        ):
            errors.append(f"{key}: changes scope/accountability inputs into schedule/signed choice")
    elif language == "german":
        if key == "zg361m.101.a" and re.search(r"\breserve\b", folded):
            errors.append(f"{key}: contains untranslated English 'reserve'")
        if key == "zg361m.132.a" and "unmachbarkeitsevdenz" in folded:
            errors.append(f"{key}: contains reviewed German corruption 'Unmachbarkeitsevdenz'")
        if key == "zg361m.96.b" and re.search(r"\bbeförder", folded) is None:
            errors.append(f"{key}: does not clearly express leapfrog promotion of the person")
        if key == "zg361m.125.a" and re.search(r"\breviewe\b", folded):
            errors.append(f"{key}: contains the reviewed Denglish verb 'reviewe'")
        if key == "zg361m.125.b" and "helden-credit" in folded:
            errors.append(f"{key}: contains the reviewed Denglish phrase 'Helden-Credit'")
        if key == "zg361m.258.a" and re.search(
            r"(?:eintrag|verbuch|erfass|protokollier|dokumentier)", folded
        ) is None:
            errors.append(f"{key}: leaves the governance-risk ledger instruction without a verb")
        if key == "zg361m.258.a" and re.search(r"kontrollgruppen-?risik", folded):
            errors.append(f"{key}: mistranslates governance risk as control-group risk")
        if key == "zg361m.119.a" and re.search(
            r"(?:auswähl\w+|auswahlverantwort\w+|personalauswähl\w+)", folded
        ) is None:
            errors.append(f"{key}: omits the selector as an accountable person")
        formal_keys = {
            "zg361_review_now_decision_desc",
            "zg361_review_talk_interaction_desc",
            "zg361_recommend_interaction_desc",
        }
        if key in formal_keys and re.search(
            r"\b(?:Sie|Ihnen|Ihr(?:e|en|em|er|es)?)\b", value
        ):
            errors.append(f"{key}: uses formal address instead of informal singular du/dein")
        plural_keys = {
            "activity_zg361_jingcha_desc",
            "activity_zg361_jingcha_host_desc",
            "activity_zg361_jingcha_guest_desc",
            "activity_zg361_jingcha_selection_tooltip",
            "zg361_jingcha_province_desc",
        }
        if key in plural_keys and re.search(
            r"\b(?:euer|eure|euren|eurem|eurer|eures|euch)\b", folded
        ):
            errors.append(f"{key}: uses informal plural address instead of informal singular du/dein")
        if key == "zg361_jingcha_attended" and "grosser prüfung" in folded:
            errors.append(f"{key}: contains the reviewed German case error 'Großer Prüfung'")
    elif language == "french":
        if key == "zg361m.50.b":
            if re.search(r"(?:poids\s+des\s+soupçons|dépréci\w*(?:\s+\w+){0,2}\s+les\s+soupçons)", folded):
                errors.append(f"{key}: down-weights suspicion instead of suspected mutual boosters")
            if re.search(r"(?:personn|collègu|évaluat|agent|auteur|suspect)", folded) is None:
                errors.append(f"{key}: does not name the people whose evaluation weight is lowered")
        if key == "zg361m.130.b" and re.search(
            r"(?:requalifi|rebaptis|reclass)", folded
        ) is None:
            errors.append(f"{key}: does not express rebranding or reclassification")
    elif language == "spanish":
        if key in {"zg361m.25.t", "zg361m.25.a"} and "altos rendimientos" in folded:
            errors.append(f"{key}: treats high performers as abstract performance rather than people")
        if key == "zg361m.125.b" and "crédito de héroe visible" in folded:
            errors.append(f"{key}: literally translates visible hero credit instead of visible recognition")
        if key in {"zg361m.290.t", "zg361m.290.a"} and "nombramiento" in folded:
            errors.append(f"{key}: mistranslates reward nominations as appointments")
        if key == "zg361m.305.a" and "propiedad del superior" in folded:
            errors.append(f"{key}: mistranslates superior responsibility as property ownership")
        if key == "zg361m.315.a" and "crédito dual" in folded:
            errors.append(f"{key}: mistranslates dual performance attribution as financial credit")
        if key == "zg361m.353.a" and "re picos" in folded:
            errors.append(f"{key}: contains the reviewed corrupted Spanish phrase 're picos'")
        if key in {"zg361m.347.t", "zg361m.347.a"} and not (
            re.search(r"(?:ajust|correcci|modific)", folded)
            and re.search(r"(?:manual|discrecional)", folded)
        ):
            errors.append(f"{key}: does not express a manual discretionary adjustment")

    return errors


def candidate_quality_errors(
    english: dict[str, str],
    chinese: dict[str, str],
    candidate: dict[str, str],
    language: str,
) -> list[str]:
    """Reject structurally valid output that copied the reference or wrong script."""
    errors: list[str] = []
    for key, value in candidate.items():
        source = english[key]
        reference = chinese[key]
        if "\ufffd" in value:
            errors.append(f"{key}: contains U+FFFD")
        if (
            value == reference
            and value != source
            and is_translatable_english(source)
        ):
            errors.append(f"{key}: copied Simplified Chinese reference verbatim")
        source_visible = minimax.PROTECTED.sub("", source)
        candidate_visible = minimax.PROTECTED.sub("", value)
        source_copy_text = TECHNICAL_WORDS.sub("", source_visible)
        candidate_copy_text = TECHNICAL_WORDS.sub("", candidate_visible)
        phrase = copied_english_phrase(source_copy_text, candidate_copy_text)
        if phrase is not None:
            errors.append(f"{key}: copied English phrase {phrase!r}")

        visible = candidate_visible
        visible_length = len(re.sub(r"\s+", "", visible))
        if language == "japanese":
            forbidden = sorted(set(value) & JAPANESE_SIMPLIFIED_CHINESE)
            if forbidden:
                errors.append(
                    f"{key}: contains Simplified Chinese glyphs {''.join(forbidden)!r}"
                )
            if CYRILLIC.search(visible):
                errors.append(f"{key}: Japanese output contains Cyrillic text")
            if visible_length >= 15 and CJK.search(value) and KANA.search(value) is None:
                errors.append(f"{key}: long Japanese text contains no kana")
        elif language == "korean":
            if CJK.search(value) or KANA.search(value):
                errors.append(f"{key}: Korean output contains CJK/kana text")
            if CYRILLIC.search(visible):
                errors.append(f"{key}: Korean output contains Cyrillic text")
            if visible_length >= 15 and HANGUL.search(value) is None:
                errors.append(f"{key}: long Korean text contains no Hangul")
        elif language == "russian":
            if CJK.search(value) or KANA.search(value) or HANGUL.search(value):
                errors.append(f"{key}: Russian output contains East Asian text")
            if visible_length >= 15 and CYRILLIC.search(value) is None:
                errors.append(f"{key}: long Russian text contains no Cyrillic")
        else:
            if (
                CJK.search(value)
                or KANA.search(value)
                or HANGUL.search(value)
                or CYRILLIC.search(value)
            ):
                errors.append(f"{key}: Latin-script output contains foreign-script text")
        errors.extend(targeted_quality_errors(key, value, language))
    return errors


def assert_candidate_quality(
    english: dict[str, str],
    chinese: dict[str, str],
    candidate: dict[str, str],
    language: str,
) -> None:
    errors = candidate_quality_errors(english, chinese, candidate, language)
    if errors:
        raise ReleaseLocalizationError(
            f"{language} quality gate failed: " + "; ".join(errors[:12])
        )


def request_key_context(source: dict[str, str], language: str) -> str:
    """Add narrow, authoritative instructions for source values changed at release freeze."""
    keys = set(source)
    notes: list[str] = []
    if "zg361_review_now_decision_tooltip" in keys:
        notes.append(
            "zg361_review_now_decision_tooltip must say at least one direct incumbent official, "
            "not three and not merely one official anywhere"
        )
    if keys & {"zg361_grade_325_desc", "zg361.4.desc"}:
        notes.append(
            "zg361_grade_325_desc and zg361.4.desc must each state local treasury -50 when "
            "present, personal gold -25, merit -60 where supported, and salary -25% for one "
            "year where applicable; keep 50, 25, 60, 25%, and one year explicit"
        )
    if "zg361m.14.desc" in keys:
        notes.append(
            "zg361m.14.desc must follow the authoritative Chinese reference, not the generic "
            "English ledger boilerplate: an upheld appeal returns to superior recalibration, "
            "refunds local-treasury, personal-gold, and merit charges item by item, immediately "
            "stops the unfinished one-year 25% salary cut, and corrects the ranking"
        )
    if "zg361m.18.desc" in keys:
        notes.append(
            "zg361m.18.desc must follow the authoritative Chinese reference, not the generic "
            "English ledger boilerplate: show rating, KPI, rank, superior and reasons, then local "
            "treasury -50, personal gold -25, merit -60, salary -25% for one year, and appeal "
            "refund/stop-deduction status; retain every Arabic number"
        )
    if "zg361m.21.desc" in keys:
        notes.append(
            "zg361m.21.desc must follow the authoritative Chinese reference, not the generic "
            "English ledger boilerplate: a limited bonus pool funds top-rating rewards, 3.75 gets "
            "a bonus or short raise, 3.5 stays unchanged, and 3.25 keeps the fourfold penalty"
        )
    if language == "korean" and keys & {
        "zg361_grade_325_desc",
        "zg361.4.desc",
    }:
        notes.append(
            "in Korean use 네 가지 조치 or 네 가지 책임 for fourfold consequence, 공덕 for "
            "merit, and 녹봉 for salary; never copy 问责, 俸禄, 贤能, or any CJK glyph"
        )
    if language == "japanese" and "zg361_grade_325_desc" in keys:
        notes.append(
            "in Japanese begin zg361_grade_325_desc with 今回の評価結果 or 今期の評価結果; "
            "never use the Chinese-style 今周期 or 考核"
        )
    if language == "japanese" and "zg361.4.desc" in keys:
        notes.append(
            "in Japanese zg361.4.desc must say もう一度3.25を取れば or an equally grammatical "
            "passive equivalent; never the ungrammatical 3.25 を付けば"
        )
    if language == "japanese" and "zg361m.14.a" in keys:
        notes.append(
            "in Japanese zg361m.14.a must say 俸給減額の停止 or 俸給控除の停止; "
            "never 俸禄停止, which wrongly means stopping salary itself"
        )
    if language == "japanese" and keys & OFFICIAL_RESOURCE_KEYS:
        notes.append(
            "for every explicit fourfold resource in these keys, use CK3 1.19.0.6 official "
            "Japanese terminology exactly: 地方国庫 for local treasury, 個人の金 or "
            "個人の所持金 for personal gold, and 功徳 for merit; never 地方財務, 個人資金, "
            "個人金貨, 人事評価, or 功績"
        )
    if language == "japanese" and "zg361m.18.a" in keys:
        notes.append(
            "in Japanese zg361m.18.a begins with 精算時 or 決算時 for accounting settlement; "
            "never 決済時, which means a payment transaction"
        )
    if language == "korean" and "zg361m.14.a" in keys:
        notes.append(
            "in Korean zg361m.14.a must say 녹봉 감액 중단 or 봉급 공제 중단; never "
            "봉록 중단, which wrongly means stopping salary itself. End concisely with 각각 "
            "대조·기록한다 or an equivalent 한다 form; never 합니다 and never repeat 항목을 항목별로"
        )
    if language == "korean" and keys & OFFICIAL_RESOURCE_KEYS:
        notes.append(
            "for every explicit fourfold resource in these keys, use CK3 1.19.0.6 Korean "
            "terminology: 지방 국고 or 지방 금고, 개인 금화, and 공덕; never 공적 or 업적 "
            "for the merit resource"
        )
    if not notes:
        return ""
    return " CRITICAL EXACT-KEY REQUIREMENTS: " + "; ".join(notes) + "."


def request_with_bisection(
    language: str,
    spec: SourceSpec,
    english: dict[str, str],
    chinese: dict[str, str],
    api_key: str,
    max_tokens: int,
    artifact_root: Path | None = None,
    batch_name: str = "adhoc",
) -> dict[str, str]:
    """Retry malformed model batches as smaller, still-minimal requests."""

    def request_subset(keys: tuple[str, ...]) -> dict[str, str]:
        source = {key: english[key] for key in keys}
        prompt_source = {
            key: TRANSLATION_SOURCE_OVERRIDES.get(key, source[key]) for key in keys
        }
        reference = {key: chinese[key] for key in keys}
        subset_digest = hashlib.sha256(
            json.dumps(keys, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:12]

        def preserve_raw_response(attempt: int, payload: bytes) -> None:
            if artifact_root is None:
                return
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            target = (
                artifact_root
                / "responses"
                / batch_name
                / language
                / f"{stamp}_{subset_digest}_try{attempt}.raw"
            )
            write_new_or_equal(target, payload)

        single_key_quality_attempts = 3 if len(keys) == 1 else 1
        last_error: minimax.TranslationError | ReleaseLocalizationError | None = None
        for quality_attempt in range(single_key_quality_attempts):
            try:
                _, result = minimax.request_candidate(
                    language,
                    LANGUAGES[language],
                    minimax.make_prompt(
                        "English",
                        ("Simplified Chinese",),
                        LANGUAGES[language],
                        spec.context
                        + " This is a strict flat-string JSON batch using raw CK3/YML string values. "
                        "Every source \\\" sequence is a protected two-character token: a backslash followed "
                        "by a quote. Encode it as \\\\\\\" in JSON so the decoded JSON string still contains "
                        "the original \\\" token; never normalize it to an ordinary unescaped quote. "
                        "For the current 3.25 fourfold-settlement keys, retain Arabic numerals and all "
                        "four distinct consequences exactly: local treasury -50 when present, personal "
                        "gold -25, merit -60 where supported, and salary -25% for one year where applicable. "
                        "An upheld appeal refunds the three immediate charges and stops only future salary "
                        "deductions; already settled salary months are not refunded."
                        + request_key_context(source, language)
                        + LANGUAGE_PROMPT_SUFFIX[language],
                        prompt_source,
                        (reference,),
                        PROTECTED_TERMS,
                    ),
                    source,
                    api_key,
                    max_tokens,
                    PROTECTED_TERMS,
                    preserve_raw_response,
                )
                assert_candidate_quality(source, reference, result, language)
                residuals = candidate_residuals(source, result, language)
                if residuals:
                    raise ReleaseLocalizationError(
                        f"untranslated English values: {residuals[:12]}"
                    )
                return result
            except ReleaseLocalizationError as error:
                last_error = error
                if quality_attempt + 1 < single_key_quality_attempts:
                    continue
                if len(keys) == 1:
                    raise
                break
            except minimax.TranslationError as error:
                last_error = error
                message = str(error)
                transport_failure = "HTTP " in message or message.endswith(
                    ("URLError", "TimeoutError", "OSError", "IncompleteRead")
                )
                if (
                    len(keys) == 1
                    and not transport_failure
                    and quality_attempt + 1 < single_key_quality_attempts
                ):
                    continue
                if len(keys) == 1 or transport_failure:
                    raise
                break

        if last_error is None:
            raise ReleaseLocalizationError("translation retry ended without a result")
        middle = len(keys) // 2
        left = request_subset(keys[:middle])
        right = request_subset(keys[middle:])
        return {key: (left if key in left else right)[key] for key in keys}

    return request_subset(tuple(english))


def translate(root: Path, workers: int, max_tokens: int) -> int:
    if not os.environ.get(minimax.API_KEY_ENV):
        raise ReleaseLocalizationError(f"{minimax.API_KEY_ENV} is not configured")
    plan = plan_payload()
    write_new_or_equal(root / "translation-plan.json", json_bytes(plan))
    failures: list[dict[str, str]] = []
    for batch in build_batches():
        spec = SOURCES[batch.source]
        full_english = minimax.parse_ck3_localization(spec.english)
        full_chinese = minimax.parse_ck3_localization(spec.chinese)
        batch_english = {key: full_english[key] for key in batch.keys}
        request_keys = tuple(
            key for key in batch.keys if is_translatable_english(full_english[key])
        )
        english = {key: full_english[key] for key in request_keys}
        chinese = {key: full_chinese[key] for key in request_keys}
        pending: list[str] = []
        for language in LANGUAGES:
            path = candidate_path(root, batch, language)
            if path.is_file():
                preserved = load_candidate(path, batch_english)
                assert_candidate_quality(
                    batch_english,
                    {key: full_chinese[key] for key in batch.keys},
                    preserved,
                    language,
                )
            else:
                pending.append(language)
        if not pending:
            print(f"SKIP {batch.name}: {len(LANGUAGES)} preserved candidates")
            continue
        print(f"REQUEST {batch.name}: {len(batch.keys)} keys x {len(pending)} languages")
        with ThreadPoolExecutor(max_workers=min(workers, len(pending))) as executor:
            futures = {
                executor.submit(
                    request_with_bisection,
                    language,
                    spec,
                    english,
                    chinese,
                    os.environ[minimax.API_KEY_ENV],
                    max_tokens,
                    root,
                    batch.name,
                ): language
                for language in pending
            }
            for future in as_completed(futures):
                language = futures[future]
                try:
                    translated = future.result()
                    candidate = {
                        key: translated.get(key, batch_english[key])
                        for key in batch.keys
                    }
                    minimax.assert_protected_tokens(
                        batch_english, candidate, PROTECTED_TERMS
                    )
                    assert_candidate_quality(
                        batch_english,
                        {key: full_chinese[key] for key in batch.keys},
                        candidate,
                        language,
                    )
                    residuals = candidate_residuals(
                        batch_english, candidate, language
                    )
                    if residuals:
                        raise ReleaseLocalizationError(
                            f"untranslated English values: {residuals[:12]}"
                        )
                    write_new_or_equal(
                        candidate_path(root, batch, language), json_bytes(candidate)
                    )
                    print(f"  PASS {language}")
                except (minimax.TranslationError, ReleaseLocalizationError) as error:
                    safe_error = {
                        "batch": batch.name,
                        "language": language,
                        "error": str(error),
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                    error_path = root / "errors" / f"{stamp}_{batch.name}_{language}.json"
                    write_new_or_equal(error_path, json_bytes(safe_error))
                    failures.append(safe_error)
                    print(f"  RED {language}: {error}", file=sys.stderr)
    missing = [
        str(candidate_path(root, batch, language))
        for batch in build_batches()
        for language in LANGUAGES
        if not candidate_path(root, batch, language).is_file()
    ]
    completion = {
        "schema": 1,
        "complete": not missing,
        "candidate_count": len(build_batches()) * len(LANGUAGES) - len(missing),
        "expected_candidate_count": len(build_batches()) * len(LANGUAGES),
        "missing": missing,
        "failures_this_attempt": failures,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(root / "attempts" / f"{stamp}.json", json_bytes(completion))
    if missing:
        print(f"RED: {len(missing)} candidate batch/language files remain missing")
        return 1
    index = []
    for batch in build_batches():
        for language in LANGUAGES:
            path = candidate_path(root, batch, language)
            index.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    write_new_or_equal(root / "complete-index.json", json_bytes({"schema": 1, "files": index}))
    print(f"GREEN: preserved {len(index)} MiniMax candidate files in {root}")
    return 0


def seed_revision(source_root: Path, target_root: Path) -> int:
    """Copy only quality-gate-passing candidates into a new immutable revision."""
    expected_plan = json_bytes(plan_payload())
    source_plan = source_root / "translation-plan.json"
    if not source_plan.is_file() or source_plan.read_bytes() != expected_plan:
        raise ReleaseLocalizationError("source candidate plan is missing or stale")
    write_new_or_equal(target_root / "translation-plan.json", expected_plan)
    copied: list[dict[str, str]] = []
    rejected: list[dict[str, object]] = []
    missing: list[str] = []
    parsed_sources = {
        name: (
            minimax.parse_ck3_localization(spec.english),
            minimax.parse_ck3_localization(spec.chinese),
        )
        for name, spec in SOURCES.items()
    }
    for batch in build_batches():
        english, chinese = parsed_sources[batch.source]
        subset = {key: english[key] for key in batch.keys}
        reference = {key: chinese[key] for key in batch.keys}
        for language in LANGUAGES:
            source_path = candidate_path(source_root, batch, language)
            if not source_path.is_file():
                missing.append(source_path.relative_to(source_root).as_posix())
                continue
            try:
                candidate = load_candidate(source_path, subset)
                assert_candidate_quality(subset, reference, candidate, language)
            except (ReleaseLocalizationError, minimax.TranslationError) as error:
                rejected.append(
                    {
                        "batch": batch.name,
                        "language": language,
                        "source": source_path.relative_to(source_root).as_posix(),
                        "reason": str(error),
                    }
                )
                continue
            target_path = candidate_path(target_root, batch, language)
            write_new_or_equal(target_path, source_path.read_bytes())
            copied.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": target_path.relative_to(target_root).as_posix(),
                    "sha256": sha256(target_path),
                }
            )
    record = {
        "schema": 1,
        "source_root": str(source_root.resolve()),
        "copied_count": len(copied),
        "rejected_count": len(rejected),
        "missing_count": len(missing),
        "copied": copied,
        "rejected": rejected,
        "missing": missing,
    }
    write_new_or_equal(target_root / "seed" / "seed-index.json", json_bytes(record))
    print(
        f"GREEN: seeded {len(copied)} candidates; "
        f"rejected {len(rejected)} and left {len(missing)} missing for retranslation"
    )
    return 0


def candidate_value_errors(
    key: str,
    english_value: str,
    chinese_value: str,
    candidate_value: str,
    language: str,
) -> list[str]:
    """Validate one value so a repair can preserve every unaffected sibling byte-for-byte."""
    errors: list[str] = []
    source = {key: english_value}
    reference = {key: chinese_value}
    candidate = {key: candidate_value}
    if "\n" in candidate_value:
        errors.append(f"{key}: contains a literal newline")
    try:
        minimax.assert_protected_tokens(source, candidate, PROTECTED_TERMS)
    except minimax.TranslationError as error:
        errors.append(str(error))
    errors.extend(candidate_quality_errors(source, reference, candidate, language))
    if candidate_residuals(source, candidate, language):
        errors.append(f"{key}: untranslated English value")
    return errors


def classify_repair_candidate(
    english: dict[str, str],
    chinese: dict[str, str],
    candidate: dict[str, str] | None,
    language: str,
) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    """Split a candidate into exact preserved values and values requiring a request."""
    preserved: dict[str, str] = {}
    requested: dict[str, list[str]] = {}
    reset_nontranslatable: list[str] = []
    for key, source_value in english.items():
        if candidate is None:
            if is_translatable_english(source_value):
                requested[key] = ["source candidate file is missing"]
            else:
                preserved[key] = source_value
            continue
        value = candidate[key]
        errors = candidate_value_errors(
            key, source_value, chinese[key], value, language
        )
        if not errors:
            preserved[key] = value
            continue
        if is_translatable_english(source_value):
            requested[key] = errors
            continue
        baseline_errors = candidate_value_errors(
            key, source_value, chinese[key], source_value, language
        )
        if baseline_errors:
            raise ReleaseLocalizationError(
                f"non-translatable baseline is invalid for {language}/{key}: "
                + "; ".join(baseline_errors)
            )
        preserved[key] = source_value
        reset_nontranslatable.append(key)
    return preserved, requested, reset_nontranslatable


def source_value_changes(
    previous_english: dict[str, str],
    previous_chinese: dict[str, str],
    current_english: dict[str, str],
    current_chinese: dict[str, str],
) -> dict[str, list[str]]:
    """Return the exact existing keys whose English or Chinese source value changed."""
    expected_order = tuple(previous_english)
    if (
        tuple(previous_chinese) != expected_order
        or tuple(current_english) != expected_order
        or tuple(current_chinese) != expected_order
    ):
        raise ReleaseLocalizationError(
            "source migration changed localization key coverage or order"
        )
    changed: dict[str, list[str]] = {}
    for key in expected_order:
        reasons: list[str] = []
        if previous_english[key] != current_english[key]:
            reasons.append("English source value changed")
        if previous_chinese[key] != current_chinese[key]:
            reasons.append("Simplified Chinese source value changed")
        if reasons:
            changed[key] = reasons
    return changed


def classify_migration_candidate(
    previous_english: dict[str, str],
    current_english: dict[str, str],
    current_chinese: dict[str, str],
    candidate: dict[str, str] | None,
    language: str,
    changed: dict[str, list[str]],
) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    """Preserve unchanged values and request source-changed or newly rejected keys only."""
    if tuple(previous_english) != tuple(current_english):
        raise ReleaseLocalizationError(
            "source migration changed localization key coverage or order"
        )
    preserved: dict[str, str] = {}
    requested: dict[str, list[str]] = {}
    reset_nontranslatable: list[str] = []
    for key, source_value in current_english.items():
        reasons = list(changed.get(key, ()))
        if candidate is None:
            reasons.append("source candidate file is missing")
        elif not reasons:
            reasons.extend(
                candidate_value_errors(
                    key,
                    source_value,
                    current_chinese[key],
                    candidate[key],
                    language,
                )
            )
        if not reasons:
            preserved[key] = candidate[key]
            continue
        if is_translatable_english(source_value):
            requested[key] = reasons
            continue
        baseline_errors = candidate_value_errors(
            key,
            source_value,
            current_chinese[key],
            source_value,
            language,
        )
        if baseline_errors:
            raise ReleaseLocalizationError(
                f"non-translatable migrated baseline is invalid for {language}/{key}: "
                + "; ".join(baseline_errors)
            )
        preserved[key] = source_value
        reset_nontranslatable.append(key)
    return preserved, requested, reset_nontranslatable


def repair_one_candidate(
    batch: Batch,
    language: str,
    spec: SourceSpec,
    english: dict[str, str],
    chinese: dict[str, str],
    source_candidate: dict[str, str] | None,
    api_key: str,
    max_tokens: int,
    artifact_root: Path | None = None,
) -> tuple[dict[str, str], dict[str, object]]:
    """Preserve valid values and request only the failing keys in one candidate file."""
    preserved, requested, reset_nontranslatable = classify_repair_candidate(
        english, chinese, source_candidate, language
    )
    translated: dict[str, str] = {}
    if requested:
        request_english = {key: english[key] for key in requested}
        request_chinese = {key: chinese[key] for key in requested}
        translated = request_with_bisection(
            language,
            spec,
            request_english,
            request_chinese,
            api_key,
            max_tokens,
            artifact_root,
            batch.name,
        )
    result = {
        key: translated[key] if key in translated else preserved[key]
        for key in english
    }
    minimax.assert_protected_tokens(english, result, PROTECTED_TERMS)
    assert_candidate_quality(english, chinese, result, language)
    residuals = candidate_residuals(english, result, language)
    if residuals:
        raise ReleaseLocalizationError(
            f"{language}/{batch.name} repair left English values: {residuals[:12]}"
        )
    return result, {
        "preserved_keys": list(preserved),
        "requested_keys": list(requested),
        "request_reasons": requested,
        "reset_nontranslatable": reset_nontranslatable,
    }


def repair_plan_payload(source_root: Path) -> dict[str, object]:
    """Freeze which exact source values are preserved and which keys are re-requested."""
    expected_plan = json_bytes(plan_payload())
    source_plan = source_root / "translation-plan.json"
    if not source_plan.is_file() or source_plan.read_bytes() != expected_plan:
        raise ReleaseLocalizationError("source candidate plan is missing or stale")
    parsed_sources = {
        name: (
            minimax.parse_ck3_localization(spec.english),
            minimax.parse_ck3_localization(spec.chinese),
        )
        for name, spec in SOURCES.items()
    }
    files: list[dict[str, object]] = []
    preserved_total = 0
    requested_total = 0
    for batch in build_batches():
        full_english, full_chinese = parsed_sources[batch.source]
        english = {key: full_english[key] for key in batch.keys}
        chinese = {key: full_chinese[key] for key in batch.keys}
        for language in LANGUAGES:
            source_path = candidate_path(source_root, batch, language)
            source_candidate = (
                load_candidate_payload(source_path, english)
                if source_path.is_file()
                else None
            )
            preserved, requested, reset = classify_repair_candidate(
                english, chinese, source_candidate, language
            )
            preserved_total += len(preserved)
            requested_total += len(requested)
            preserved_digest = hashlib.sha256(
                json.dumps(
                    preserved, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest().upper()
            files.append(
                {
                    "batch": batch.name,
                    "source": batch.source,
                    "language": language,
                    "source_candidate": (
                        source_path.relative_to(source_root).as_posix()
                        if source_path.is_file()
                        else None
                    ),
                    "source_candidate_sha256": (
                        sha256(source_path) if source_path.is_file() else None
                    ),
                    "preserved_key_count": len(preserved),
                    "preserved_values_sha256": preserved_digest,
                    "requested_key_count": len(requested),
                    "requested": [
                        {"key": key, "reasons": reasons}
                        for key, reasons in requested.items()
                    ],
                    "reset_nontranslatable": reset,
                }
            )
    return {
        "schema": 1,
        "source_root": str(source_root.resolve()),
        "source_translation_plan_sha256": sha256(source_plan),
        "candidate_file_count": len(files),
        "preserved_key_count": preserved_total,
        "requested_key_count": requested_total,
        "files": files,
    }


def repair_candidates(
    source_root: Path,
    target_root: Path,
    workers: int,
    max_tokens: int,
) -> int:
    """Create an immutable candidate revision by repairing only failing values."""
    if not os.environ.get(minimax.API_KEY_ENV):
        raise ReleaseLocalizationError(f"{minimax.API_KEY_ENV} is not configured")
    expected_plan = json_bytes(plan_payload())
    write_new_or_equal(target_root / "translation-plan.json", expected_plan)
    repair_plan = repair_plan_payload(source_root)
    repair_plan_path = target_root / "repair" / "repair-plan.json"
    write_new_or_equal(repair_plan_path, json_bytes(repair_plan))
    records = {
        (record["batch"], record["language"]): record
        for record in repair_plan["files"]
    }
    parsed_sources = {
        name: (
            minimax.parse_ck3_localization(spec.english),
            minimax.parse_ck3_localization(spec.chinese),
        )
        for name, spec in SOURCES.items()
    }
    failures: list[dict[str, str]] = []
    completed_this_attempt: list[dict[str, object]] = []

    for batch in build_batches():
        spec = SOURCES[batch.source]
        full_english, full_chinese = parsed_sources[batch.source]
        english = {key: full_english[key] for key in batch.keys}
        chinese = {key: full_chinese[key] for key in batch.keys}
        pending = [
            language
            for language in LANGUAGES
            if not candidate_path(target_root, batch, language).is_file()
        ]
        if not pending:
            print(f"SKIP {batch.name}: {len(LANGUAGES)} repaired candidates")
            continue
        print(f"REPAIR {batch.name}: {len(pending)} candidate files")

        def run_language(language: str) -> tuple[str, Path, dict[str, object]]:
            source_path = candidate_path(source_root, batch, language)
            source_candidate = (
                load_candidate_payload(source_path, english)
                if source_path.is_file()
                else None
            )
            candidate, summary = repair_one_candidate(
                batch,
                language,
                spec,
                english,
                chinese,
                source_candidate,
                os.environ[minimax.API_KEY_ENV],
                max_tokens,
                target_root,
            )
            planned = records[(batch.name, language)]
            if summary["requested_keys"] != [
                item["key"] for item in planned["requested"]
            ]:
                raise ReleaseLocalizationError(
                    f"repair plan drift for {batch.name}/{language}"
                )
            path = candidate_path(target_root, batch, language)
            write_new_or_equal(path, json_bytes(candidate))
            return language, path, summary

        with ThreadPoolExecutor(max_workers=min(workers, len(pending))) as executor:
            futures = {executor.submit(run_language, language): language for language in pending}
            for future in as_completed(futures):
                language = futures[future]
                try:
                    _, path, summary = future.result()
                    completed_this_attempt.append(
                        {
                            "batch": batch.name,
                            "language": language,
                            "path": path.relative_to(target_root).as_posix(),
                            "sha256": sha256(path),
                            "preserved_key_count": len(summary["preserved_keys"]),
                            "requested_key_count": len(summary["requested_keys"]),
                        }
                    )
                    print(
                        f"  PASS {language}: preserved {len(summary['preserved_keys'])}, "
                        f"requested {len(summary['requested_keys'])}"
                    )
                except (minimax.TranslationError, ReleaseLocalizationError) as error:
                    safe_error = {
                        "batch": batch.name,
                        "language": language,
                        "error": str(error),
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                    write_new_or_equal(
                        target_root
                        / "errors"
                        / f"{stamp}_{batch.name}_{language}.json",
                        json_bytes(safe_error),
                    )
                    failures.append(safe_error)
                    print(f"  RED {language}: {error}", file=sys.stderr)

    missing = [
        candidate_path(target_root, batch, language).relative_to(target_root).as_posix()
        for batch in build_batches()
        for language in LANGUAGES
        if not candidate_path(target_root, batch, language).is_file()
    ]
    completion = {
        "schema": 1,
        "source_root": str(source_root.resolve()),
        "repair_plan_sha256": sha256(repair_plan_path),
        "complete": not missing,
        "candidate_count": len(build_batches()) * len(LANGUAGES) - len(missing),
        "expected_candidate_count": len(build_batches()) * len(LANGUAGES),
        "missing": missing,
        "completed_this_attempt": completed_this_attempt,
        "failures_this_attempt": failures,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(
        target_root / "repair" / "attempts" / f"{stamp}.json",
        json_bytes(completion),
    )
    if missing:
        print(f"RED: {len(missing)} repaired candidate files remain missing")
        return 1
    index = []
    for batch in build_batches():
        for language in LANGUAGES:
            path = candidate_path(target_root, batch, language)
            index.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": path.relative_to(target_root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    write_new_or_equal(
        target_root / "complete-index.json", json_bytes({"schema": 1, "files": index})
    )
    write_new_or_equal(
        target_root / "repair" / "complete-index.json",
        json_bytes(completion),
    )
    print(
        f"GREEN: repaired {len(index)} candidate files with "
        f"{repair_plan['requested_key_count']} requested keys"
    )
    return 0


def prepare_migration_context(
    source_root: Path,
    target_root: Path,
    baseline_git_ref: str,
) -> dict[str, object]:
    """Freeze and verify the previous/current source pairs for one immutable migration."""
    baseline_plan_path = source_root / "translation-plan.json"
    if not baseline_plan_path.is_file():
        raise ReleaseLocalizationError("baseline candidate plan is missing")
    try:
        baseline_plan = json.loads(baseline_plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseLocalizationError(
            f"cannot read baseline candidate plan: {error}"
        ) from error
    current_plan = plan_payload()
    for field in (
        "schema",
        "model",
        "languages",
        "protected_terms",
        "batches",
        "request_count",
    ):
        if baseline_plan.get(field) != current_plan[field]:
            raise ReleaseLocalizationError(
                f"source migration changed translation-plan field {field!r}"
            )
    if set(baseline_plan.get("sources", {})) != set(current_plan["sources"]):
        raise ReleaseLocalizationError("source migration changed source-file coverage")

    commit = git_commit(baseline_git_ref)
    previous_sources: dict[str, tuple[dict[str, str], dict[str, str]]] = {}
    current_sources: dict[str, tuple[dict[str, str], dict[str, str]]] = {}
    changed_by_source: dict[str, dict[str, list[str]]] = {}
    source_records: list[dict[str, object]] = []
    for source_name, spec in SOURCES.items():
        baseline_record = baseline_plan["sources"][source_name]
        current_record = current_plan["sources"][source_name]
        for path_field in ("english", "simp_chinese"):
            if baseline_record.get(path_field) != current_record[path_field]:
                raise ReleaseLocalizationError(
                    f"source migration changed {source_name}/{path_field} path"
                )

        source_snapshots: dict[str, Path] = {}
        record: dict[str, object] = {"source": source_name, "files": {}}
        for language_field, path_field, hash_field, current_path in (
            ("english", "english", "english_sha256", spec.english),
            ("simp_chinese", "simp_chinese", "simp_chinese_sha256", spec.chinese),
        ):
            relative_path = baseline_record[path_field]
            previous_data = git_blob(commit, relative_path)
            previous_hash = bytes_sha256(previous_data)
            if previous_hash != baseline_record[hash_field]:
                raise ReleaseLocalizationError(
                    f"{commit}:{relative_path} does not match the baseline plan hash"
                )
            current_data = current_path.read_bytes()
            current_hash = bytes_sha256(current_data)
            if current_hash != current_record[hash_field]:
                raise ReleaseLocalizationError(
                    f"current source hash drifted while preparing {source_name}/{language_field}"
                )
            previous_snapshot = (
                target_root
                / "migration"
                / "sources"
                / "previous"
                / source_name
                / current_path.name
            )
            current_snapshot = (
                target_root
                / "migration"
                / "sources"
                / "current"
                / source_name
                / current_path.name
            )
            write_new_or_equal(previous_snapshot, previous_data)
            write_new_or_equal(current_snapshot, current_data)
            source_snapshots[f"previous_{language_field}"] = previous_snapshot
            source_snapshots[f"current_{language_field}"] = current_snapshot
            record["files"][language_field] = {
                "path": relative_path,
                "previous_sha256": previous_hash,
                "current_sha256": current_hash,
                "previous_snapshot": previous_snapshot.relative_to(target_root).as_posix(),
                "current_snapshot": current_snapshot.relative_to(target_root).as_posix(),
            }

        previous_english = minimax.parse_ck3_localization(
            source_snapshots["previous_english"]
        )
        previous_chinese = minimax.parse_ck3_localization(
            source_snapshots["previous_simp_chinese"]
        )
        current_english = minimax.parse_ck3_localization(
            source_snapshots["current_english"]
        )
        current_chinese = minimax.parse_ck3_localization(
            source_snapshots["current_simp_chinese"]
        )
        changes = source_value_changes(
            previous_english,
            previous_chinese,
            current_english,
            current_chinese,
        )
        previous_sources[source_name] = (previous_english, previous_chinese)
        current_sources[source_name] = (current_english, current_chinese)
        changed_by_source[source_name] = changes
        record["changed_key_count"] = len(changes)
        record["changed_keys"] = [
            {
                "key": key,
                "reasons": reasons,
                "previous_english_sha256": bytes_sha256(
                    previous_english[key].encode("utf-8")
                ),
                "current_english_sha256": bytes_sha256(
                    current_english[key].encode("utf-8")
                ),
                "previous_simp_chinese_sha256": bytes_sha256(
                    previous_chinese[key].encode("utf-8")
                ),
                "current_simp_chinese_sha256": bytes_sha256(
                    current_chinese[key].encode("utf-8")
                ),
            }
            for key, reasons in changes.items()
        ]
        source_records.append(record)

    write_new_or_equal(
        target_root / "migration" / "baseline-translation-plan.json",
        baseline_plan_path.read_bytes(),
    )
    write_new_or_equal(
        target_root / "translation-plan.json", json_bytes(current_plan)
    )
    source_diff = {
        "schema": 1,
        "baseline_root": str(source_root.resolve()),
        "baseline_translation_plan_sha256": sha256(baseline_plan_path),
        "current_translation_plan_sha256": sha256(
            target_root / "translation-plan.json"
        ),
        "baseline_git_reference": baseline_git_ref,
        "baseline_git_commit": commit,
        "changed_key_count": sum(len(keys) for keys in changed_by_source.values()),
        "sources": source_records,
    }
    write_new_or_equal(
        target_root / "migration" / "source-diff.json", json_bytes(source_diff)
    )
    return {
        "baseline_plan": baseline_plan,
        "current_plan": current_plan,
        "previous_sources": previous_sources,
        "current_sources": current_sources,
        "changed_by_source": changed_by_source,
        "source_diff": source_diff,
    }


def migration_plan_payload(
    source_root: Path,
    context: dict[str, object],
) -> dict[str, object]:
    """Freeze every value preserved and every exact key requested during migration."""
    previous_sources = context["previous_sources"]
    current_sources = context["current_sources"]
    changed_by_source = context["changed_by_source"]
    files: list[dict[str, object]] = []
    preserved_total = 0
    requested_total = 0
    for batch in build_batches():
        previous_english, _ = previous_sources[batch.source]
        current_english, current_chinese = current_sources[batch.source]
        previous_subset = {key: previous_english[key] for key in batch.keys}
        current_subset = {key: current_english[key] for key in batch.keys}
        current_reference = {key: current_chinese[key] for key in batch.keys}
        changed_subset = {
            key: changed_by_source[batch.source][key]
            for key in batch.keys
            if key in changed_by_source[batch.source]
        }
        for language in LANGUAGES:
            source_path = candidate_path(source_root, batch, language)
            source_candidate = (
                load_candidate_payload(source_path, previous_subset)
                if source_path.is_file()
                else None
            )
            preserved, requested, reset = classify_migration_candidate(
                previous_subset,
                current_subset,
                current_reference,
                source_candidate,
                language,
                changed_subset,
            )
            preserved_total += len(preserved)
            requested_total += len(requested)
            files.append(
                {
                    "batch": batch.name,
                    "source": batch.source,
                    "language": language,
                    "source_candidate": (
                        source_path.relative_to(source_root).as_posix()
                        if source_path.is_file()
                        else None
                    ),
                    "source_candidate_sha256": (
                        sha256(source_path) if source_path.is_file() else None
                    ),
                    "preserved_key_count": len(preserved),
                    "preserved_values_sha256": bytes_sha256(
                        json.dumps(
                            preserved, ensure_ascii=False, separators=(",", ":")
                        ).encode("utf-8")
                    ),
                    "requested_key_count": len(requested),
                    "requested": [
                        {"key": key, "reasons": reasons}
                        for key, reasons in requested.items()
                    ],
                    "reset_nontranslatable": reset,
                }
            )
    return {
        "schema": 1,
        "baseline_root": str(source_root.resolve()),
        "baseline_translation_plan_sha256": context["source_diff"][
            "baseline_translation_plan_sha256"
        ],
        "current_translation_plan_sha256": context["source_diff"][
            "current_translation_plan_sha256"
        ],
        "baseline_git_commit": context["source_diff"]["baseline_git_commit"],
        "source_changed_key_count": context["source_diff"]["changed_key_count"],
        "candidate_file_count": len(files),
        "preserved_key_count": preserved_total,
        "requested_key_count": requested_total,
        "files": files,
    }


def migrate_one_candidate(
    batch: Batch,
    language: str,
    spec: SourceSpec,
    previous_english: dict[str, str],
    current_english: dict[str, str],
    current_chinese: dict[str, str],
    source_candidate: dict[str, str] | None,
    changed: dict[str, list[str]],
    api_key: str,
    max_tokens: int,
    artifact_root: Path,
) -> tuple[dict[str, str], dict[str, object]]:
    preserved, requested, reset_nontranslatable = classify_migration_candidate(
        previous_english,
        current_english,
        current_chinese,
        source_candidate,
        language,
        changed,
    )
    translated: dict[str, str] = {}
    if requested:
        translated = request_with_bisection(
            language,
            spec,
            {key: current_english[key] for key in requested},
            {key: current_chinese[key] for key in requested},
            api_key,
            max_tokens,
            artifact_root,
            batch.name,
        )
    result = {
        key: translated[key] if key in translated else preserved[key]
        for key in current_english
    }
    minimax.assert_protected_tokens(current_english, result, PROTECTED_TERMS)
    assert_candidate_quality(current_english, current_chinese, result, language)
    residuals = candidate_residuals(current_english, result, language)
    if residuals:
        raise ReleaseLocalizationError(
            f"{language}/{batch.name} migration left English values: {residuals[:12]}"
        )
    return result, {
        "preserved_keys": list(preserved),
        "requested_keys": list(requested),
        "request_reasons": requested,
        "reset_nontranslatable": reset_nontranslatable,
    }


def migrate_candidates(
    source_root: Path,
    target_root: Path,
    baseline_git_ref: str,
    workers: int,
    max_tokens: int,
    plan_only: bool = False,
) -> int:
    """Migrate one complete candidate artifact across a verified source-only change."""
    if not os.environ.get(minimax.API_KEY_ENV):
        raise ReleaseLocalizationError(f"{minimax.API_KEY_ENV} is not configured")
    context = prepare_migration_context(
        source_root, target_root, baseline_git_ref
    )
    migration_plan = migration_plan_payload(source_root, context)
    migration_plan_path = target_root / "migration" / "migration-plan.json"
    write_new_or_equal(migration_plan_path, json_bytes(migration_plan))
    if plan_only:
        print(
            f"GREEN: froze source migration plan with "
            f"{migration_plan['source_changed_key_count']} changed source keys, "
            f"{migration_plan['preserved_key_count']} preserved values, and "
            f"{migration_plan['requested_key_count']} requested values"
        )
        return 0
    records = {
        (record["batch"], record["language"]): record
        for record in migration_plan["files"]
    }
    previous_sources = context["previous_sources"]
    current_sources = context["current_sources"]
    changed_by_source = context["changed_by_source"]
    failures: list[dict[str, str]] = []
    completed_this_attempt: list[dict[str, object]] = []

    for batch in build_batches():
        previous_english, _ = previous_sources[batch.source]
        current_english, current_chinese = current_sources[batch.source]
        previous_subset = {key: previous_english[key] for key in batch.keys}
        current_subset = {key: current_english[key] for key in batch.keys}
        current_reference = {key: current_chinese[key] for key in batch.keys}
        changed_subset = {
            key: changed_by_source[batch.source][key]
            for key in batch.keys
            if key in changed_by_source[batch.source]
        }
        pending = [
            language
            for language in LANGUAGES
            if not candidate_path(target_root, batch, language).is_file()
        ]
        if not pending:
            print(f"SKIP {batch.name}: {len(LANGUAGES)} migrated candidates")
            continue
        print(f"MIGRATE {batch.name}: {len(pending)} candidate files")

        def run_language(language: str) -> tuple[str, Path, dict[str, object]]:
            source_path = candidate_path(source_root, batch, language)
            source_candidate = (
                load_candidate_payload(source_path, previous_subset)
                if source_path.is_file()
                else None
            )
            candidate, summary = migrate_one_candidate(
                batch,
                language,
                SOURCES[batch.source],
                previous_subset,
                current_subset,
                current_reference,
                source_candidate,
                changed_subset,
                os.environ[minimax.API_KEY_ENV],
                max_tokens,
                target_root,
            )
            planned = records[(batch.name, language)]
            if summary["requested_keys"] != [
                item["key"] for item in planned["requested"]
            ]:
                raise ReleaseLocalizationError(
                    f"migration plan drift for {batch.name}/{language}"
                )
            path = candidate_path(target_root, batch, language)
            write_new_or_equal(path, json_bytes(candidate))
            return language, path, summary

        with ThreadPoolExecutor(max_workers=min(workers, len(pending))) as executor:
            futures = {
                executor.submit(run_language, language): language
                for language in pending
            }
            for future in as_completed(futures):
                language = futures[future]
                try:
                    _, path, summary = future.result()
                    completed_this_attempt.append(
                        {
                            "batch": batch.name,
                            "language": language,
                            "path": path.relative_to(target_root).as_posix(),
                            "sha256": sha256(path),
                            "preserved_key_count": len(summary["preserved_keys"]),
                            "requested_key_count": len(summary["requested_keys"]),
                        }
                    )
                    print(
                        f"  PASS {language}: preserved {len(summary['preserved_keys'])}, "
                        f"requested {len(summary['requested_keys'])}"
                    )
                except (minimax.TranslationError, ReleaseLocalizationError) as error:
                    safe_error = {
                        "batch": batch.name,
                        "language": language,
                        "error": str(error),
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                    write_new_or_equal(
                        target_root
                        / "errors"
                        / f"{stamp}_{batch.name}_{language}.json",
                        json_bytes(safe_error),
                    )
                    failures.append(safe_error)
                    print(f"  RED {language}: {error}", file=sys.stderr)

    missing = [
        candidate_path(target_root, batch, language).relative_to(target_root).as_posix()
        for batch in build_batches()
        for language in LANGUAGES
        if not candidate_path(target_root, batch, language).is_file()
    ]
    completion = {
        "schema": 1,
        "baseline_root": str(source_root.resolve()),
        "migration_plan_sha256": sha256(migration_plan_path),
        "complete": not missing,
        "candidate_count": len(build_batches()) * len(LANGUAGES) - len(missing),
        "expected_candidate_count": len(build_batches()) * len(LANGUAGES),
        "missing": missing,
        "completed_this_attempt": completed_this_attempt,
        "failures_this_attempt": failures,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(
        target_root / "migration" / "attempts" / f"{stamp}.json",
        json_bytes(completion),
    )
    if missing:
        print(f"RED: {len(missing)} migrated candidate files remain missing")
        return 1
    index = []
    for batch in build_batches():
        for language in LANGUAGES:
            path = candidate_path(target_root, batch, language)
            index.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": path.relative_to(target_root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    write_new_or_equal(
        target_root / "complete-index.json", json_bytes({"schema": 1, "files": index})
    )
    write_new_or_equal(
        target_root / "migration" / "complete-index.json", json_bytes(completion)
    )
    print(
        f"GREEN: migrated {len(index)} candidate files with "
        f"{migration_plan['requested_key_count']} requested keys"
    )
    return 0


def collected_candidates(root: Path, source_name: str, language: str) -> dict[str, str]:
    spec = SOURCES[source_name]
    english = minimax.parse_ck3_localization(spec.english)
    chinese = minimax.parse_ck3_localization(spec.chinese)
    result: dict[str, str] = {}
    for batch in build_batches():
        if batch.source != source_name:
            continue
        subset = {key: english[key] for key in batch.keys}
        candidate = load_candidate(candidate_path(root, batch, language), subset)
        assert_candidate_quality(
            subset,
            {key: chinese[key] for key in batch.keys},
            candidate,
            language,
        )
        residuals = candidate_residuals(subset, candidate, language)
        if residuals:
            raise ReleaseLocalizationError(
                f"{language}/{batch.name} contains English placeholders: {residuals[:12]}"
            )
        result.update(candidate)
    if tuple(result) != tuple(english):
        raise ReleaseLocalizationError(f"candidate order/coverage mismatch: {source_name}/{language}")
    return result


def audit_candidate_artifact(root: Path) -> int:
    """Strictly audit one complete candidate artifact without touching source targets."""
    expected_plan = json_bytes(plan_payload())
    plan_path = root / "translation-plan.json"
    if not plan_path.is_file() or plan_path.read_bytes() != expected_plan:
        raise ReleaseLocalizationError(
            "candidate plan is missing or does not match the current source files"
        )
    index = []
    entries: dict[str, dict[str, int]] = {language: {} for language in LANGUAGES}
    for batch in build_batches():
        for language in LANGUAGES:
            path = candidate_path(root, batch, language)
            if not path.is_file():
                raise ReleaseLocalizationError(
                    f"candidate artifact is incomplete: {path.relative_to(root)}"
                )
            index.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    expected_index = json_bytes({"schema": 1, "files": index})
    index_path = root / "complete-index.json"
    if not index_path.is_file() or index_path.read_bytes() != expected_index:
        raise ReleaseLocalizationError(
            "candidate complete-index is missing, stale, or hash-inconsistent"
        )
    for language in LANGUAGES:
        for source_name in SOURCES:
            entries[language][source_name] = len(
                collected_candidates(root, source_name, language)
            )
    report = {
        "schema": 1,
        "result": "GREEN",
        "candidate_root": str(root.resolve()),
        "translation_plan_sha256": sha256(plan_path),
        "complete_index_sha256": sha256(index_path),
        "candidate_file_count": len(index),
        "entries": entries,
        "checks": [
            "current_source_plan",
            "complete_index_hashes",
            "key_order",
            "protected_tokens",
            "quality",
            "no_english_placeholders",
        ],
    }
    report_path = root / "audit" / "candidate-audit.json"
    write_new_or_equal(report_path, json_bytes(report))
    print(
        f"GREEN: audited {len(index)} current-source candidate files; "
        f"report {report_path.resolve()}"
    )
    return 0


def merge_raw_yml(path: Path, translations: dict[str, str]) -> bytes:
    data = path.read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise ReleaseLocalizationError(f"target yml lacks UTF-8 BOM: {path}")
    lines = data.decode("utf-8-sig").splitlines()
    target_keys: list[str] = []
    output: list[str] = []
    for key, value in translations.items():
        if ENTRY.fullmatch(f' {key}:0 "{value}"') is None:
            raise ReleaseLocalizationError(
                f"candidate is not safe CK3 localization syntax: {path} [{key}]"
            )
    for line in lines:
        match = ENTRY.fullmatch(line)
        if match:
            key = match.group("key")
            target_keys.append(key)
            if key in translations:
                output.append(
                    match.group("prefix")
                    + translations[key]
                    + match.group("suffix")
                )
            else:
                output.append(line)
        else:
            output.append(line)
    translation_keys = tuple(translations)
    if tuple(target_keys) != translation_keys[: len(target_keys)]:
        raise ReleaseLocalizationError(f"target yml key/order mismatch while merging: {path}")
    for key in translation_keys[len(target_keys) :]:
        output.append(f' {key}:0 "{translations[key]}"')
    return b"\xef\xbb\xbf" + ("\n".join(output) + "\n").encode("utf-8")


def decode_raw_yml_value(value: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value):
            output.append(value[index + 1])
            index += 2
        else:
            output.append(value[index])
            index += 1
    return "".join(output)


def apply_candidates(root: Path) -> int:
    expected_plan = json_bytes(plan_payload())
    plan_path = root / "translation-plan.json"
    if not plan_path.is_file() or plan_path.read_bytes() != expected_plan:
        raise ReleaseLocalizationError("candidate plan is missing or source files changed")
    mechanism_digest = release_translation_source_sha256(load_mechanisms(MOD_ROOT))
    changed: list[str] = []
    for language in LANGUAGES:
        core = collected_candidates(root, "core", language)
        core_target = (
            MOD_ROOT / "localization" / language / f"zg361_l_{language}.yml"
        )
        core_data = merge_raw_yml(core_target, core)
        if core_target.read_bytes() != core_data:
            core_target.write_bytes(core_data)
            changed.append(core_target.relative_to(MOD_ROOT).as_posix())

        mechanism_raw = collected_candidates(root, "mechanisms", language)
        catalog = {
            "schema": 1,
            "language": language,
            "source_sha256": mechanism_digest,
            "translations": {
                key: decode_raw_yml_value(value) for key, value in mechanism_raw.items()
            },
        }
        catalog_path = MOD_ROOT / "tools" / "mechanism_translations" / f"{language}.json"
        catalog_data = json_bytes(catalog)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        if not catalog_path.is_file() or catalog_path.read_bytes() != catalog_data:
            catalog_path.write_bytes(catalog_data)
            changed.append(catalog_path.relative_to(MOD_ROOT).as_posix())
    apply_record = {
        "schema": 1,
        "candidate_root": str(root.resolve()),
        "mechanism_source_sha256": mechanism_digest,
        "changed_files": changed,
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(root / "apply" / f"{stamp}.json", json_bytes(apply_record))
    print(f"GREEN: applied reviewed candidates to {len(changed)} authority/target files")
    print("NEXT: run gen_361_mechanisms.py to render the seven generated yml files")
    return 0


def audit(write_report: Path | None = None) -> int:
    errors: list[str] = []
    report: dict[str, object] = {"schema": 1, "languages": {}}
    source_paths = [
        path for spec in SOURCES.values() for path in (spec.english, spec.chinese)
    ]
    target_paths: list[Path] = []
    for language in LANGUAGES:
        language_report: dict[str, object] = {}
        for source_name, spec in SOURCES.items():
            english = minimax.parse_ck3_localization(spec.english)
            target_path = (
                MOD_ROOT
                / "localization"
                / language
                / spec.english.name.replace("_english.yml", f"_{language}.yml")
            )
            target_paths.append(target_path)
            target = minimax.parse_ck3_localization(target_path)
            if tuple(target) != tuple(english):
                errors.append(f"key/order mismatch: {target_path}")
                continue
            try:
                minimax.assert_protected_tokens(english, target, PROTECTED_TERMS)
            except minimax.TranslationError as error:
                errors.append(f"{target_path}: {error}")
            try:
                chinese = minimax.parse_ck3_localization(spec.chinese)
                assert_candidate_quality(english, chinese, target, language)
            except ReleaseLocalizationError as error:
                errors.append(f"{target_path}: {error}")
            residuals = candidate_residuals(english, target, language)
            if residuals:
                errors.append(f"English placeholders in {target_path}: {residuals[:12]}")
            target_chars = {
                "japanese": len(re.findall(r"[ぁ-んァ-ン一-龯]", "".join(target.values()))),
                "korean": len(re.findall(r"[가-힣]", "".join(target.values()))),
                "russian": len(re.findall(r"[А-Яа-яЁё]", "".join(target.values()))),
            }.get(language)
            if target_chars == 0:
                errors.append(f"no expected target-script characters in {target_path}")
            language_report[source_name] = {
                "entries": len(target),
                "exact_english_residuals": len(residuals),
                "target_script_characters": target_chars,
                "sha256": sha256(target_path),
            }
        report["languages"][language] = language_report
    if errors:
        print(f"RED: {len(errors)} release-localization problem(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    if write_report is not None:
        canonical = release_audit_payload(source_paths, target_paths)
        write_atomic(write_report.resolve(), json_bytes(canonical))
        print(f"GREEN: wrote release-localization audit report to {write_report.resolve()}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("GREEN: seven-language structure, tokens, scripts, and English-placeholder audit passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    translate_parser = subparsers.add_parser("translate")
    translate_parser.add_argument("--artifact-root", type=Path, required=True)
    translate_parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    translate_parser.add_argument("--max-completion-tokens", type=int, default=12000)
    seed_parser = subparsers.add_parser("seed")
    seed_parser.add_argument("--source-artifact-root", type=Path, required=True)
    seed_parser.add_argument("--artifact-root", type=Path, required=True)
    repair_parser = subparsers.add_parser("repair")
    repair_parser.add_argument("--source-artifact-root", type=Path, required=True)
    repair_parser.add_argument("--artifact-root", type=Path, required=True)
    repair_parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    repair_parser.add_argument("--max-completion-tokens", type=int, default=12000)
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--source-artifact-root", type=Path, required=True)
    migrate_parser.add_argument("--artifact-root", type=Path, required=True)
    migrate_parser.add_argument("--baseline-git-ref", required=True)
    migrate_parser.add_argument("--workers", type=int, default=3, choices=range(1, 5))
    migrate_parser.add_argument("--max-completion-tokens", type=int, default=12000)
    migrate_parser.add_argument("--plan-only", action="store_true")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--artifact-root", type=Path, required=True)
    candidate_audit_parser = subparsers.add_parser("audit-candidates")
    candidate_audit_parser.add_argument("--artifact-root", type=Path, required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument(
        "--write-report",
        type=Path,
        metavar="PATH",
        help=(
            "write a deterministic formal-release hash report only after every "
            "localization audit passes"
        ),
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "translate":
            return translate(args.artifact_root, args.workers, args.max_completion_tokens)
        if args.command == "seed":
            return seed_revision(args.source_artifact_root, args.artifact_root)
        if args.command == "repair":
            return repair_candidates(
                args.source_artifact_root,
                args.artifact_root,
                args.workers,
                args.max_completion_tokens,
            )
        if args.command == "migrate":
            return migrate_candidates(
                args.source_artifact_root,
                args.artifact_root,
                args.baseline_git_ref,
                args.workers,
                args.max_completion_tokens,
                args.plan_only,
            )
        if args.command == "apply":
            return apply_candidates(args.artifact_root)
        if args.command == "audit-candidates":
            return audit_candidate_artifact(args.artifact_root)
        return audit(args.write_report)
    except (ReleaseLocalizationError, minimax.TranslationError, OSError, ValueError) as error:
        print(f"RED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
