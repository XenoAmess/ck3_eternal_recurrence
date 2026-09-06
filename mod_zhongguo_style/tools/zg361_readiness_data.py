#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authoritative per-mechanism readiness ledger for Zhongguo 361.

This module records the highest evidence tier reached by every mechanism ID.
It deliberately does not discover files at runtime: an uncommitted generated
file in a dirty worktree must never promote readiness.  Update these explicit
claims only after the named package is committed to ``master`` and reviewed at
the stated boundary.

The generic 361 policy cards and aggregate organization-ledger fixture are not
domain-runtime evidence.  ``central-wired`` means only that a committed central
product hook reaches the package; it is not full semantic completion.  The
highest tier here is bounded CK3 fixture evidence, never production-live.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType
from typing import Final, Iterable, Mapping


MECHANISM_COUNT: Final = 361


class ReadinessLevel(IntEnum):
    """Ordered, mutually exclusive highest-evidence tiers."""

    DESIGN_ONLY = 0
    PYTHON_L0 = 1
    CK3_STATIC_READY = 2
    CENTRAL_WIRED = 3
    CK3_LIVE = 4

    @property
    def key(self) -> str:
        return {
            ReadinessLevel.DESIGN_ONLY: "design-only",
            ReadinessLevel.PYTHON_L0: "python-l0",
            ReadinessLevel.CK3_STATIC_READY: "ck3-static-ready",
            ReadinessLevel.CENTRAL_WIRED: "central-wired",
            ReadinessLevel.CK3_LIVE: "ck3-live",
        }[self]


LEVELS: Final = tuple(ReadinessLevel)
LEVEL_BY_KEY: Final[Mapping[str, ReadinessLevel]] = MappingProxyType(
    {level.key: level for level in LEVELS}
)


def mechanism_ids(*parts: int | range) -> tuple[int, ...]:
    """Flatten explicit IDs/ranges while retaining declaration order."""

    result: list[int] = []
    for part in parts:
        if isinstance(part, range):
            result.extend(part)
        elif isinstance(part, int) and not isinstance(part, bool):
            result.append(part)
        else:
            raise TypeError(f"unsupported mechanism ID declaration: {part!r}")
    return tuple(result)


@dataclass(frozen=True, slots=True)
class ReadinessClaim:
    ids: tuple[int, ...]
    level: ReadinessLevel
    package: str
    evidence: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class ReadinessRecord:
    mechanism_id: int
    level: ReadinessLevel
    package: str
    evidence: tuple[str, ...]
    note: str

    def manifest_payload(self) -> dict[str, object]:
        return {
            "highest_level": self.level.key,
            "ordinal": int(self.level),
            "package": self.package,
            "evidence": list(self.evidence),
            "note": self.note,
            "cumulative_gates": {
                level.key: self.level >= level for level in LEVELS
            },
        }


@dataclass(frozen=True, slots=True)
class ProductAcceptanceSnapshot:
    """Latest whole-product run, kept separate from per-ID readiness claims."""

    run_id: str
    observed_at: str
    result: str
    product_commit: str
    projection: str
    verified_file_count: int
    product_tree_sha256: str
    release_manifest_sha256: str
    loader_database_nodes: int
    loader_fatal_count: int
    speed: int
    observation_days: int
    native_observations: int
    drained_event_keys: tuple[str, ...]
    cleared_product_signatures: tuple[str, ...]
    evidence: tuple[str, ...]
    boundary: str


@dataclass(frozen=True, slots=True)
class ProductAcceptanceAttempt:
    """Bounded recent whole-product attempt that did not promote per-ID readiness."""

    run_id: str
    observed_at: str
    product_commit: str
    projection: str
    verified_file_count: int
    product_tree_sha256: str
    release_manifest_sha256: str
    loader_and_result: str
    closure_boundary: str


CENTRAL_WIRING_BOUNDARY: Final = (
    "central-wired records committed hook reachability only; it does not prove "
    "complete per-ID semantics, a complete player-visible loop, or CK3 live acceptance"
)
CORE_EFFECT_EVIDENCE: Final = (
    "common/scripted_effects/zg361_core_review_cycle_effects.txt",
    "common/scripted_effects/zg361_core_result_delivery_effects.txt",
    "common/scripted_effects/zg361_core_appeal_scoreboard_effects.txt",
    "common/scripted_effects/zg361_core_elimination_effects.txt",
)
CENTRAL_RUNTIME_EVIDENCE: Final = (
    "tools/gen_361_phase2_central_runtime.py",
    "tools/test_zg361_phase2_central_runtime.py",
    "docs/361-phase2-central-runtime-spec.md",
    *CORE_EFFECT_EVIDENCE,
)
CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY: Final = (
    "central-wired records committed reachability to the Workforce adapter and its "
    "typed external-wait/resume seam; #360-361 remain conditional on real 357-359 "
    "receipts and are not central-completable, CK3 live, or complete"
)
LIVE_BOUNDARY: Final = (
    "ck3-live means bounded fixture-live evidence for the named slice; no mechanism "
    "is promoted here to production-live or full semantic completion"
)

RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS: Final = (
    ProductAcceptanceAttempt(
        run_id="R111",
        observed_at="2026-09-06 09:54 Asia/Shanghai",
        product_commit="807f08d0c74bbd6126431c677d8cbb32a10417f0",
        projection="phase2-full-release-r111-807f08d",
        verified_file_count=1031,
        product_tree_sha256="c865244335ed6a749d07e62527f0772bb3fd913ccea2a6888f00e680e7e23674",
        release_manifest_sha256="326bf1a5a9940b09627387f2b3b09c70b26f1f1eeb44ab129fc3c6745def7196",
        loader_and_result=(
            "loader 303/303 GREEN；产品 RED 同时落在两族：B1 weak/dead manager 的 "
            "pending-subject resolver，以及 `zg361b2.40.desc` 的 Character / saved-scope "
            "本地化链。550 游戏日观察上限被更早的产品 RED 覆盖，不能据此判断性能或扩大时限。"
        ),
        closure_boundary=(
            "B1 终止/释放语义及 R111 的原始 loc 签名由 "
            "`3c005e45b6a6b6c1442a3903052a582bab48970d` 修改；R112 未重现 B1 旧族，"
            "但暴露了替代 loc 链的新错误，所以此处不把本地化记为 live GREEN。"
        ),
    ),
    ProductAcceptanceAttempt(
        run_id="R112",
        observed_at="2026-09-06 10:20 Asia/Shanghai",
        product_commit="3c005e45b6a6b6c1442a3903052a582bab48970d",
        projection="phase2-full-release-r112-3c005e4",
        verified_file_count=1031,
        product_tree_sha256="f467ac90703ad0323f6608da6562becb0bf2bbcde15ebd176c11ced7569d435c",
        release_manifest_sha256="92810fd470936c5dda05b3b2b7c66565610b6620a8dc0a6a8c41596b512c648d",
        loader_and_result=(
            "loader 303/303 GREEN；产品 RED：Character ROOT 上的 "
            "`ROOT.MakeScope.Var(...).Char.GetShortUIName` 无法 promote，"
            "`zg361b2.40.desc` 转换失败。"
        ),
        closure_boundary=(
            "B2、compensation、workforce AD 的同签名生成源由 "
            "`a9320a71b4d0e636dbcd99e8e496994f26490656` 统一改为 Character 合法路径；"
            "R113 未重现 R112 loc 签名。"
        ),
    ),
    ProductAcceptanceAttempt(
        run_id="R113",
        observed_at="2026-09-06 10:34 Asia/Shanghai",
        product_commit="a9320a71b4d0e636dbcd99e8e496994f26490656",
        projection="phase2-full-release-r113-a9320a7",
        verified_file_count=1031,
        product_tree_sha256="f99500645dc14e056ac40d77dabf6d23c97a0951479db09bead7d634dbe08342",
        release_manifest_sha256="bf83bd1b4219f1bce2e213c4baf1733fd8ac1299a951a36f1435a46d288af679",
        loader_and_result=(
            "loader 303/303 GREEN；产品 RED：`zg361b1.123` 的 queued continuation 在 roster "
            "行缺少 `zg361_b1_case_owner` 时仍进入冻结配额复核，触发变量读取与比较错误。"
        ),
        closure_boundary=(
            "stale continuation 的业务终止与 list-row owner guard 由 "
            "`f6cf65378158669e35e493ba8466685f1ace0e1d` 修复；R114 在出现下一族 RED 前"
            "未重现 R113 签名。"
        ),
    ),
    ProductAcceptanceAttempt(
        run_id="R114",
        observed_at="2026-09-06 10:54 Asia/Shanghai",
        product_commit="f6cf65378158669e35e493ba8466685f1ace0e1d",
        projection="phase2-full-release-r114-f6cf653",
        verified_file_count=1031,
        product_tree_sha256="d54d3beb0dcf26a3831b6b0441e92dbba28a56aca8e77fae770c01416f208aa5",
        release_manifest_sha256="bbd86499307e9a1499b1ade628334ed9219e4d097d2d4db54cbbc23f010eb191",
        loader_and_result=(
            "loader 303/303 GREEN；产品 RED：`zg361comp.2` 对 weak Character subject 执行 "
            "`has_variable`，且 portfolio refresh 继续裸比较不可用 `var`，分别落在 "
            "`zg361_compensation_07b_portfolio_apply_stage_effects.txt` 与 "
            "`07c_portfolio_refresh_effects.txt`。"
        ),
        closure_boundary=(
            "compensation 生成源、生成结果与回归由 "
            "`4e76cd78c5addc44bcf4522500e985dc34a7a745` 修复；R115 在出现下一族 RED 前"
            "未重现 R114 签名。R114 不构成完整迁移树 GREEN，也不提升任何逐号证据层。"
        ),
    ),
    ProductAcceptanceAttempt(
        run_id="R115",
        observed_at="2026-09-06 11:23 Asia/Shanghai",
        product_commit="4e76cd78c5addc44bcf4522500e985dc34a7a745",
        projection="phase2-full-release-r115-4e76cd7",
        verified_file_count=1031,
        product_tree_sha256="d4616282305cdc6761aaf624b771731f93d221fe3cce4ab5a324acfe87d2ae10",
        release_manifest_sha256="4ee547e643e5a34df3ba1da2c7d10bfce98e6acabed10ffa90d7a8f7c2f51aca",
        loader_and_result=(
            "loader 303/303 GREEN；产品 RED：`zg361_p2c_summary_desc` 在 Character ROOT 上"
            "使用四个 `ROOT.MakeScope.Var(...).GetValue` 数值链，均无法 promote `MakeScope`，"
            "并触发本地化转换失败。"
        ),
        closure_boundary=(
            "P2C 及全仓同签名数值本地化链由 `2911b07e717ad88e69ea6aec0ec16c475633fa74` "
            "收口为 `ROOT.Var(...).GetValue` 并补回归；R116 首次入口尝试未重现 R115 签名。"
            "R115 不构成完整迁移树 GREEN，也不提升任何逐号证据层。"
        ),
    ),
    ProductAcceptanceAttempt(
        run_id="R116",
        observed_at="2026-09-06 11:40–11:47 Asia/Shanghai",
        product_commit="2911b07e717ad88e69ea6aec0ec16c475633fa74",
        projection="phase2-full-release-r116-2911b07",
        verified_file_count=1031,
        product_tree_sha256="318d60a217065ffaaa51dd92ad9cf3b9db349d9a673ef86ee604b507553a5a44",
        release_manifest_sha256="3bfb52359100b060a60cc33aff05f7136282fbe0bb088ccd23633cfd11de48aa",
        loader_and_result=(
            "首次入口 loader 303/303 GREEN、fatal=0、项目 loader match=0；"
            "入口/导航 harness 在遇到未列入该路径的 `zg361.30` 时 RED。"
            "随后 resume1 复用 PID 54484、launch/restart 均为 false、restart_count=0；"
            "`zg361.30` drain GREEN，36/36 interrupts 全部 GREEN。resume 运行时增量随后在 22 个 "
            "Career desc 上产生 154 条同族产品本地化错误："
            "`[scope:<saved>.GetShortUIName]` 不能作为 localization 数据表达式。"
        ),
        closure_boundary=(
            "冻结 R116 产品树的全同签名扫描为 2,601 处，分布在 8 个九语言生成文件族；"
            "修复计划覆盖 Career HC、feedback/promotion/PIP、workforce endgame、credit project、"
            "Phase3 metrics delivery、workforce AD、workforce attribution、workforce remediation，"
            "并以全语言硬门禁归零。resume1 中 R113、R114、R115 旧签名均为 0。另有产品生命周期"
            "故障：Central active 期间年度 B1 旋转 serial，使冻结 central tuple stale abort；"
            "因此 runner 最终报告的 550 日观察边界不是唯一故障。R116 不是全量 GREEN；产品树已改变，"
            "R117 必须 fresh 启动后验收，旧 PID 不得复验新产品。"
        ),
    ),
)

LATEST_PRODUCT_ACCEPTANCE: Final = ProductAcceptanceSnapshot(
    run_id="R107",
    observed_at="2026-09-06 06:23 Asia/Shanghai",
    result="RED",
    product_commit="275ee65",
    projection="phase2-full-release-r107-275ee65",
    verified_file_count=937,
    product_tree_sha256="309F14CBD47DAE5653171A8B70C0EE834799BEC28D48F467E0EC000443709AA2",
    release_manifest_sha256="7D38B0831E039A3328890AC56B0CF46E479BBBC2E9EA26E95951FC8394FA3E94",
    loader_database_nodes=303,
    loader_fatal_count=0,
    speed=5,
    observation_days=918,
    native_observations=221,
    drained_event_keys=(
        "zg361b2.40",
        "spymaster_task.0381",
        "zg361.40",
        "spymaster_task.0346",
        "zg361m.1",
        "zg361.1",
        "zg361ch.19",
        "spymaster_task.0342",
        "zg361ch.20",
        "zg361ch.21",
        "zg361ch.22",
        "zg361ch.23",
        "zg361ch.24",
        "zg361ch.25",
        "zg361ch.901",
        "zg361ch.92",
        "zg361ch.93",
        "zg361ch.94",
        "zg361ch.95",
        "zg361ch.96",
        "zg361ch.97",
        "zg361ch.902",
        "zg361ch.98",
        "zg361ch.99",
        "zg361ch.100",
        "zg361ch.101",
        "zg361ch.102",
        "zg361ch.103",
        "zg361ch.104",
        "zg361ch.105",
        "zg361ch.903",
        "zg361ch.106",
        "zg361ch.107",
        "zg361ch.108",
        "zg361ch.109",
        "zg361ch.110",
        "zg361ch.111",
        "zg361ch.112",
        "zg361ch.113",
        "zg361ch.904",
        "zg361ch.114",
        "zg361ch.115",
        "zg361ch.116",
        "zg361ch.117",
        "zg361ch.118",
        "zg361ch.119",
        "zg361ch.120",
        "zg361ch.905",
        "zg361ch.121",
        "zg361ch.122",
        "zg361ch.123",
        "zg361ch.124",
        "zg361ch.125",
        "zg361ch.126",
        "zg361ch.127",
        "zg361ch.128",
        "zg361ch.906",
        "zg361comp.1",
        "zg361comp.1",
        "zg361comp.1",
        "zg361comp.1",
        "zg361p2c.2",
        "zg361.40",
        "spymaster_task.0399",
        "ep3_governor_yearly.3060",
        "ep3_governor_yearly.8170",
        "zg361.40",
        "zg361m.2",
    ),
    cleared_product_signatures=(
        "Unknown effect: has_variable (R98 compensation portfolio dispatch)",
        "weak archived manager write (R99 B1 roster amendment)",
        "legacy compensation payer-share/dead payer (R99)",
        "dead jingcha superior opinion (R99)",
        "promotion/PIP first-use receipt revision (R99)",
        "legacy compensation funded shares (R102)",
        "career-transfer consumer/receiver state (R102)",
        "B2 redundancy state (R102)",
        "elimination rank read (R102)",
        "B1 delayed weak-subject calibration cascade (R103)",
        "promotion/PIP optional settlement and sample state (R103)",
        "manager-owned B1 roster rebuild across nested employee callback (R105)",
        "loader-attributed project errors",
    ),
    evidence=(
        "docs/phase2-promo/promotion-source-checkpoint-choreography-forensics-2026-09-04.md",
        "docs/phase2-promo/phase2-acceptance-case-index.md",
        r"Z:\b3r107\evidence-index.json",
        r"Z:\b3r107\cell\02_loader_error_scan.json",
        r"Z:\b3r107\cell\03_promotion_source_production_entry.json",
        r"Z:\b3r107\cell\final_error.log",
        r"Z:\b3r107\cell\final_debug.log",
        r"Z:\b3r107_resume_diag\report.json",
        r"Z:\b3r107_resume1\report.json",
        r"Z:\b3r107_resume_diag2\report.json",
        r"Z:\b3r107_resume2\report.json",
        r"Z:\b3r107_resume3\report.json",
        r"Z:\p2r107\phase2-product-projection.json",
        r"Z:\p2r107\p.manifest.json",
    ),
    boundary=(
        "The committed R107 release-identical product at commit 275ee65 loaded all 303/303 "
        "database nodes with fatal 0 and no loading-performance RED. PID 32972 advanced 918 "
        "game days at the default speed 5 across four replacement clients, 221 paused "
        "native/MCP observations and 68 exact GREEN event drains without a CK3 restart. It "
        "completed the full 44-card career/HC manager sequence, all six domain receipts and "
        "four compensation decisions. The fresh product proves the rewritten career-learning "
        "localization bytes are loadable, but the run has not yet revisited a player-visible "
        "career-learning response and therefore does not claim visual copy GREEN. R107 exposed "
        "two harness-only resource/context variants: annual summary zg361.1 can inherit B1, "
        "B2 and notice tuples with or without the expired bank tuple; dual-cost career/HC "
        "cards can render either all three funded options or the exact defer-only option. "
        "Both cases now retain exact contracts rather than wildcards. The current fail-closed "
        "window is a recurring zg361.1 with the extended later-cycle scope set; no click was "
        "sent. The broader Chinese copy audit remains RED: the screenshot repair covered only "
        "six career-learning subject cards and its digest, while the audited Career/HC, PP, "
        "B2, compensation and other player-facing families still require itemized closure. "
        "Further live continuation is intentionally paused until those copy findings are "
        "repaired. No zg361pp.146 -> D+1 .147 receipt exists yet and the canonical registry "
        "remains 0/4. The player remains alive; illness-death count is 0/3 and no health "
        "fixture was applied. This run promotes no per-ID tier."
    ),
)


CLAIMS: Final[tuple[ReadinessClaim, ...]] = (
    ReadinessClaim(
        mechanism_ids(range(242, 278), range(355, 357)),
        ReadinessLevel.CENTRAL_WIRED,
        "workforce-endgame-ck3-runtime",
        (
            "tools/gen_361_workforce_endgame_runtime.py",
            "tools/test_zg361_workforce_endgame_runtime.py",
            "docs/361-workforce-endgame-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(360, 362)),
        ReadinessLevel.CENTRAL_WIRED,
        "workforce-endgame-conditional-external-wait",
        (
            "tools/gen_361_workforce_endgame_runtime.py",
            "tools/test_zg361_workforce_endgame_runtime.py",
            "docs/361-workforce-endgame-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(26, 32), range(54, 69), range(129, 135)),
        ReadinessLevel.CENTRAL_WIRED,
        "credit-project-ck3-runtime",
        (
            "tools/gen_361_credit_project_runtime.py",
            "tools/test_gen_361_credit_project_runtime.py",
            "docs/361-phase3-credit-project-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(312, 334)),
        ReadinessLevel.CENTRAL_WIRED,
        "career-learning-ck3-runtime",
        (
            "tools/gen_361_career_learning_runtime.py",
            "tools/test_zg361_career_learning_runtime.py",
            "docs/361-phase2-career-learning-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(82, 92), range(278, 301)),
        ReadinessLevel.CENTRAL_WIRED,
        "compensation-lti-ck3-runtime",
        (
            "tools/gen_361_compensation_runtime.py",
            "tools/test_zg361_compensation_runtime.py",
            "docs/361-compensation-lti-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(146, 192)),
        ReadinessLevel.CENTRAL_WIRED,
        "feedback-promotion-pip-ck3-runtime",
        (
            "tools/gen_361_feedback_promotion_pip_runtime.py",
            "tools/test_zg361_feedback_promotion_pip_runtime.py",
            "docs/361-feedback-promotion-pip-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(19, 26), range(92, 129)),
        ReadinessLevel.CENTRAL_WIRED,
        "career-hc-ck3-runtime",
        (
            "tools/gen_361_career_hc_runtime.py",
            "tools/test_zg361_career_hc_runtime.py",
            "docs/361-career-hc-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(32, 37), range(345, 355)),
        ReadinessLevel.CENTRAL_WIRED,
        "manager-governance-ck3-runtime",
        (
            "tools/gen_361_manager_governance_runtime.py",
            "tools/test_zg361_manager_governance_runtime.py",
            "docs/361-phase2-manager-governance-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(192, 229)),
        ReadinessLevel.CENTRAL_WIRED,
        "incident-platform-ck3-runtime",
        (
            "tools/gen_361_incident_platform_runtime.py",
            "tools/test_zg361_incident_platform_runtime.py",
            "docs/361-phase3-incident-platform-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(229, 242), range(301, 312), range(334, 345)),
        ReadinessLevel.CENTRAL_WIRED,
        "metrics-delivery-ck3-runtime",
        (
            "tools/gen_361_phase3_metrics_delivery_runtime.py",
            "tools/test_zg361_phase3_metrics_delivery_runtime.py",
            "docs/361-phase3-metrics-delivery-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(2, 14), range(37, 54), range(135, 146)),
        ReadinessLevel.CENTRAL_WIRED,
        "b1-performance-season-runtime",
        (
            "tools/zg361_b1_runtime_data.py",
            "tools/gen_361_b1_runtime.py",
            "tools/test_zg361_b1_runtime.py",
            "docs/361-b1-runtime-spec.md",
        ),
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(14, 18), range(70, 82), range(358, 360)),
        ReadinessLevel.CENTRAL_WIRED,
        "b2-delivery-appeal-runtime",
        (
            "tools/gen_361_b2_runtime.py",
            "tools/test_gen_361_b2_runtime.py",
            *CORE_EFFECT_EVIDENCE,
        ),
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(1, 357),
        ReadinessLevel.CK3_LIVE,
        "first-slice-facts-quota-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Bounded fixture-live covers frozen facts and fact-versus-quota reasons only; broader semantics remain incomplete.",
    ),
    ReadinessClaim(
        mechanism_ids(69),
        ReadinessLevel.CK3_LIVE,
        "first-slice-delivery-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Bounded fixture-live covers refusal, D+7 witnessed delivery, and the same-case receipt path.",
    ),
    ReadinessClaim(
        mechanism_ids(18),
        ReadinessLevel.CK3_LIVE,
        "first-slice-settlement-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Only receipt/refund behavior is fixture-live; reopening zg361.53 remains CK3 static-ready.",
    ),
)


def _build_records() -> Mapping[int, ReadinessRecord]:
    records: dict[int, ReadinessRecord] = {}
    for claim in CLAIMS:
        if not claim.ids or not claim.evidence:
            raise ValueError(f"readiness claim {claim.package!r} is incomplete")
        for mechanism_id in claim.ids:
            if isinstance(mechanism_id, bool) or not 1 <= mechanism_id <= MECHANISM_COUNT:
                raise ValueError(f"invalid readiness mechanism ID: {mechanism_id!r}")
            if mechanism_id in records:
                raise ValueError(f"mechanism {mechanism_id:03d} has multiple readiness claims")
            records[mechanism_id] = ReadinessRecord(
                mechanism_id,
                claim.level,
                claim.package,
                claim.evidence,
                claim.note,
            )
    expected = set(range(1, MECHANISM_COUNT + 1))
    if set(records) != expected:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        raise ValueError(f"readiness ledger is not exact; missing={missing}, extra={extra}")
    return MappingProxyType(dict(sorted(records.items())))


READINESS_BY_ID: Final = _build_records()


def ids_at_level(level: ReadinessLevel) -> tuple[int, ...]:
    return tuple(
        mechanism_id
        for mechanism_id, record in READINESS_BY_ID.items()
        if record.level is level
    )


def ids_at_least(level: ReadinessLevel) -> tuple[int, ...]:
    return tuple(
        mechanism_id
        for mechanism_id, record in READINESS_BY_ID.items()
        if record.level >= level
    )


def compress_ranges(ids: Iterable[int]) -> tuple[tuple[int, int], ...]:
    ordered = tuple(sorted(set(ids)))
    if not ordered:
        return ()
    result: list[tuple[int, int]] = []
    first = last = ordered[0]
    for mechanism_id in ordered[1:]:
        if mechanism_id == last + 1:
            last = mechanism_id
            continue
        result.append((first, last))
        first = last = mechanism_id
    result.append((first, last))
    return tuple(result)


def format_ranges(ids: Iterable[int]) -> str:
    return ", ".join(
        f"{first:03d}" if first == last else f"{first:03d}-{last:03d}"
        for first, last in compress_ranges(ids)
    )


EXCLUSIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {level.key: len(ids_at_level(level)) for level in LEVELS}
)
CUMULATIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {level.key: len(ids_at_least(level)) for level in LEVELS}
)

EXPECTED_EXCLUSIVE_RANGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "design-only": "",
        "python-l0": "",
        "ck3-static-ready": "",
        "central-wired": "002-017, 019-068, 070-356, 358-361",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_CUMULATIVE_RANGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "design-only": "001-361",
        "python-l0": "001-361",
        "ck3-static-ready": "001-361",
        "central-wired": "001-361",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_EXCLUSIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 0,
        "python-l0": 0,
        "ck3-static-ready": 0,
        "central-wired": 357,
        "ck3-live": 4,
    }
)
EXPECTED_CUMULATIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 361,
        "python-l0": 361,
        "ck3-static-ready": 361,
        "central-wired": 361,
        "ck3-live": 4,
    }
)


def validate_readiness() -> None:
    if tuple(READINESS_BY_ID) != tuple(range(1, MECHANISM_COUNT + 1)):
        raise ValueError("readiness IDs must be exactly 001-361 in order")
    if tuple(level.key for level in LEVELS) != tuple(LEVEL_BY_KEY):
        raise ValueError("readiness level keys are not ordered")
    exclusive_ranges = {
        level.key: format_ranges(ids_at_level(level)) for level in LEVELS
    }
    cumulative_ranges = {
        level.key: format_ranges(ids_at_least(level)) for level in LEVELS
    }
    if exclusive_ranges != dict(EXPECTED_EXCLUSIVE_RANGES):
        raise ValueError(f"exclusive readiness range drift: {exclusive_ranges!r}")
    if cumulative_ranges != dict(EXPECTED_CUMULATIVE_RANGES):
        raise ValueError(f"cumulative readiness range drift: {cumulative_ranges!r}")
    if dict(EXCLUSIVE_COUNTS) != dict(EXPECTED_EXCLUSIVE_COUNTS):
        raise ValueError(f"exclusive readiness count drift: {dict(EXCLUSIVE_COUNTS)!r}")
    if dict(CUMULATIVE_COUNTS) != dict(EXPECTED_CUMULATIVE_COUNTS):
        raise ValueError(f"cumulative readiness count drift: {dict(CUMULATIVE_COUNTS)!r}")
    cumulative = tuple(CUMULATIVE_COUNTS[level.key] for level in LEVELS)
    if any(left < right for left, right in zip(cumulative, cumulative[1:])):
        raise ValueError("readiness cumulative gates are not monotonic")


validate_readiness()


__all__ = [
    "CENTRAL_WIRING_BOUNDARY",
    "CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY",
    "CENTRAL_RUNTIME_EVIDENCE",
    "CLAIMS",
    "CUMULATIVE_COUNTS",
    "EXPECTED_CUMULATIVE_COUNTS",
    "EXPECTED_CUMULATIVE_RANGES",
    "EXPECTED_EXCLUSIVE_COUNTS",
    "EXPECTED_EXCLUSIVE_RANGES",
    "EXCLUSIVE_COUNTS",
    "LEVELS",
    "LEVEL_BY_KEY",
    "LIVE_BOUNDARY",
    "LATEST_PRODUCT_ACCEPTANCE",
    "MECHANISM_COUNT",
    "ProductAcceptanceAttempt",
    "ProductAcceptanceSnapshot",
    "RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS",
    "READINESS_BY_ID",
    "ReadinessClaim",
    "ReadinessLevel",
    "ReadinessRecord",
    "compress_ranges",
    "format_ranges",
    "ids_at_least",
    "ids_at_level",
    "validate_readiness",
]
