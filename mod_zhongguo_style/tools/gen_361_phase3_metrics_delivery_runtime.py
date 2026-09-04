#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the AA/AG/AJ phase-3 CK3 static-ready runtime slice.

This generator intentionally owns only new files.  It composes numbered domain
behaviour over the public shared case-kernel ABI; it does not edit the kernel,
scoreboard, B1/B2, on_actions, decisions, or release plumbing.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_phase3_metrics_delivery_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
DEFER_ROUTE_EN = "Defer this mechanism and open one next-cycle policy debt."
DEFER_ROUTE_CN = "延期本机制，并登记一笔下周期制度债。"
LANGUAGES = (
    "english",
    "simp_chinese",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)


@dataclass(frozen=True)
class Mechanism:
    mid: int
    domain: str
    state: int
    field: str
    title_en: str
    title_cn: str
    desc_en: str
    desc_cn: str
    routes_en: tuple[str, str, str]
    routes_cn: tuple[str, str, str]


def m(
    mid: int,
    domain: str,
    state: int,
    field: str,
    title_en: str,
    title_cn: str,
    desc_en: str,
    desc_cn: str,
    a_en: str,
    b_en: str,
    c_en: str,
    a_cn: str,
    b_cn: str,
    c_cn: str,
) -> Mechanism:
    return Mechanism(
        mid, domain, state, field, title_en, title_cn, desc_en, desc_cn,
        # Runtime authority is uniform: legacy per-item C copy remains only as
        # research context; generated player copy is canonical policy.defer.
        (a_en, b_en, DEFER_ROUTE_EN), (a_cn, b_cn, DEFER_ROUTE_CN),
    )


MECHANISMS = (
    m(229, "aa", 1, "metric_dictionary_owner", "Who Owns the Metric Dictionary?", "指标字典归谁管",
      "A metric without an owner is a slogan with a denominator. Freeze who may define it and who must sign later changes.",
      "没有口径主人的指标，就是一个带分母的口号。先冻结谁能定义、谁要为改口径签字。",
      "Name one accountable owner.", "Require owner and steward co-signature.", "Let the committee own it collectively.",
      "指定一名口径责任人。", "责任人与数据管家双签。", "交给委员会集体负责。"),
    m(230, "aa", 1, "reconciliation_basis", "Two Dashboards, One Number", "两张看板，一个数字",
      "Two sources disagree. The review needs a recorded reconciliation rule, not whichever screenshot looks kinder.",
      "两套数据源打起来了。考核需要一条可追溯的对账规则，而不是挑那张更好看的截图。",
      "Use the named authoritative source.", "Reconcile jointly and publish the delta.", "Defer the metric and record uncertainty.",
      "采用预先指定的权威源。", "联合对账并公开差额。", "暂缓该指标并记录不确定性。"),
    m(231, "aa", 2, "denominator_policy", "The Denominator Moved", "分母怎么又变了",
      "A denominator change can rescue any KPI. Choose how the old and new versions coexist before calibration.",
      "分母一改，什么 KPI 都能被救活。校准前先决定新旧版本如何共存。",
      "Restate both periods on the new denominator.", "Keep both versions side by side.", "Use the old denominator for this cycle.",
      "按新分母重算两个时期。", "新旧口径并列展示。", "本周期继续沿用旧分母。"),
    m(232, "aa", 2, "backfill_policy", "The Spreadsheet Has a Hole", "表里少了一块",
      "Missing data demands a visible backfill rule and an owner for the estimate error.",
      "缺失数据不能靠沉默填平：人工回填规则和估算误差都要有人署名。",
      "Backfill with audit samples.", "Impute and show an uncertainty band.", "Leave the gap visible.",
      "抽样审计后回填。", "插补并展示误差带。", "保留缺口，不假装完整。"),
    m(233, "aa", 2, "visibility_level", "Who May See the Dashboard?", "谁能看见这张看板",
      "Access asymmetry creates performance asymmetry. Freeze a queryable visibility route for the assessed official.",
      "看不见数据，就只能靠猜绩效。为被考核者冻结一条可查询的可见路径。",
      "Open the full dashboard.", "Expose role-bounded detail and a query channel.", "Expose only the signed summary.",
      "开放完整看板。", "按职责开放明细，并保留查询通道。", "只开放签字后的摘要。"),
    m(234, "aa", 3, "signal_split", "Leading Signals, Lagging Results", "领先指标与滞后结果",
      "Separate effort signals from eventual outcomes so a late result cannot rewrite the work already observed.",
      "把过程信号和最终结果分账，别让迟到的结果倒改已经发生的工作。",
      "Weight leading signals first.", "Balance signals and outcomes.", "Weight verified outcomes first.",
      "领先信号优先。", "过程与结果各半。", "已验证结果优先。"),
    m(235, "aa", 3, "guardrail_split", "A KPI Needs Guardrails", "主指标也得系安全带",
      "Hitting the primary number while breaking quality is not delivery. Freeze the guardrail share before the run.",
      "冲上主指标却把质量撞碎，不叫交付。开跑前先冻结护栏权重。",
      "Give guardrails equal weight.", "Keep a sixty-forty balance.", "Permit a narrow primary-metric bias.",
      "主指标与护栏各半。", "主指标六、护栏四。", "允许有限度偏向主指标。"),
    m(236, "aa", 3, "scoring_curve", "The KPI Cliff", "KPI 悬崖",
      "One decimal point should not turn a year of work into zero. Lock the scoring curve before results arrive.",
      "一个小数点不该把一年努力清零。结果出来前，先把计分曲线锁死。",
      "Use a continuous curve.", "Use a hybrid threshold with partial credit.", "Keep the hard cliff and accept its risk.",
      "采用连续计分。", "阈值与部分得分混合。", "保留硬悬崖并承担风险。"),
    m(237, "aa", 3, "window_audit", "The Most Beautiful Time Window", "截最美的一段",
      "A flattering time window is still cherry-picking. Register the window and the comparison period now.",
      "好看的时间窗也可能是挑数据。现在就登记观察窗和对照期。",
      "Use the preregistered full window.", "Publish full and selected windows together.", "Allow the slice but flag it for audit.",
      "使用预注册完整时间窗。", "完整窗与精选窗并列。", "允许截取，但挂上审计标记。"),
    m(240, "aa", 4, "sample_route", "Everyone Wants the Same Sample", "大家都想抢这批样本",
      "Two teams cannot both claim a clean experiment on the same population. Spend a slot, partition it, or admit contamination.",
      "同一批人不能同时给两支团队当“纯净样本”。要么占槽，要么切分，要么承认污染。",
      "Reserve one exclusive sample slot.", "Partition one slot with a signed boundary.", "Queue the test and record no clean claim.",
      "占用一个独享样本槽。", "占用一个槽并签字切分。", "排队等待，不声称纯净实验。"),
    m(238, "aa", 5, "vanity_value_split", "Vanity Is Not Value", "热闹不等于价值",
      "Traffic can rise while the final value stays flat. Settle both ledgers instead of promoting the louder chart.",
      "流量可以很热闹，最终价值却原地踏步。两本账都结，别只奖嗓门大的图。",
      "Weight verified value heavily.", "Balance adoption and value.", "Credit reach first but retain value debt.",
      "大幅偏向已验证价值。", "采用与价值均衡结算。", "先认覆盖面，但保留价值债。"),
    m(239, "aa", 5, "learning_credit", "A Failed Experiment Still Learned", "实验失败，学习不能归零",
      "A preregistered failure may buy useful knowledge. Decide how much bounded learning credit survives the miss.",
      "预注册实验失败，也可能买到真知识。决定有多少有界学习收益能留下。",
      "Credit verified learning strongly.", "Split credit between learning and delivery.", "Record learning without score credit.",
      "充分认可已验证学习。", "学习与交付分账。", "只入知识库，不计绩效分。"),
    m(241, "aa", 6, "long_tail_attribution", "Who Owns the Long Tail?", "长尾效果算谁的",
      "Impact arrives after the team has moved on. Freeze attribution shares now so future value cannot be grabbed retroactively.",
      "效果在团队散场后才慢慢冒出来。现在冻结归属份额，免得未来价值被倒抢。",
      "Credit the builder most.", "Split builder, operator and successor evenly.", "Credit the long-term operator most.",
      "建设者拿大头。", "建设、运营、继任近似均分。", "长期运营者拿大头。"),

    m(301, "ag", 1, "halo_normalization", "The Core-Business Halo", "核心业务光环",
      "A tailwind is not personal magic. Separate inherited momentum from controllable contribution before calibration.",
      "顺风不是个人法术。校准前，把继承来的势能和可控贡献拆开。",
      "Normalize the halo aggressively.", "Use a peer benchmark adjustment.", "Keep raw results but label the tailwind.",
      "强力剥离光环。", "按同类基准校正。", "保留原始结果，但标注顺风。"),
    m(302, "ag", 1, "headwind_normalization", "The Declining Business Headwind", "衰退业务的逆风",
      "A shrinking market should not automatically become one official's failure. Freeze the uncontrollable headwind share.",
      "大盘缩水不能自动变成某个人的罪。先冻结不可控逆风的份额。",
      "Normalize against the market decline.", "Compare with matched declining teams.", "Keep raw results with an explicit caveat.",
      "按市场跌幅校正。", "与同类衰退团队比较。", "保留原始结果并写明限制。"),
    m(303, "ag", 2, "incubation_protection", "Incubation Needs a Clock", "孵化保护也要到点",
      "A new team needs protection, but not an immortal exemption. Sign its protected window and expiry.",
      "新团队需要保护，但不能拿永久免死金牌。把保护期和到期日一起签了。",
      "Grant one short protected cycle.", "Use milestone-gated protection.", "Decline protection and fund extra support.",
      "给一个短周期保护。", "按里程碑逐段保护。", "不保护分布，但追加支持。"),
    m(304, "ag", 2, "dual_parent_weights", "Two Parents, One Review", "两个家长，一份绩效",
      "Project and functional managers both claim authority. Freeze weights and goal shares before either writes the review.",
      "项目线和职能线都说自己说了算。写评语前，先冻结权重与目标份额。",
      "Give the project parent sixty percent.", "Use equal parent weights.", "Give the functional parent sixty percent.",
      "项目家长六成。", "双方各半。", "职能家长六成。"),
    m(305, "ag", 3, "quiet_period", "Reorg Quiet Period", "重组静默期",
      "A reporting-line change must not rewrite a nearly finished review. Choose the protected quiet-period rule.",
      "汇报线刚换，不能顺手重写快结束的考核。请选择静默期规则。",
      "Freeze ratings until calibration ends.", "Allow evidence additions but no score edits.", "Permit edits only with dual signature.",
      "校准结束前冻结评级。", "可补证据，不许改分。", "只有双签才能修改。"),
    m(306, "ag", 3, "double_hat_weights", "One Head, Two Hats", "一个脑袋，两顶帽子",
      "A temporary dual-role lead has finite capacity. Split both responsibility and review weight to one hundred percent.",
      "临时双帽负责人只有一份时间。责任和考核权重都必须拆到百分之百。",
      "Split thirty-seventy toward the expert role.", "Split fifty-fifty.", "Split seventy-thirty toward management.",
      "管理三、专业七。", "两边各半。", "管理七、专业三。"),
    m(307, "ag", 4, "center_scorecard", "Profit Center or Cost Center?", "利润中心还是成本中心",
      "Revenue and enablement teams need different scorecards. Pick one before comparing their outcomes.",
      "创收团队和支撑团队不能共用一把尺。比较结果前先选记分卡。",
      "Use a profit-center scorecard.", "Use a cost-and-service scorecard.", "Use a signed hybrid scorecard.",
      "采用利润中心记分卡。", "采用成本与服务记分卡。", "采用签字确认的混合记分卡。"),
    m(308, "ag", 4, "hc_mix", "Managers or Experts?", "管理岗还是专业岗",
      "Changing the title mix must conserve total HC. Choose the composition without manufacturing headcount.",
      "调岗位结构不能凭空长编制。请在总 HC 守恒下选择构成。",
      "Keep twenty managers and eighty experts.", "Use a thirty-seventy mix.", "Use a forty-sixty mix.",
      "二十管理、八十专业。", "三十管理、七十专业。", "四十管理、六十专业。"),
    m(309, "ag", 4, "remote_visibility", "The Far Team Is Quiet", "边远团队没声量",
      "Visibility work consumes management capacity. Spend it on a visit, a review forum, or accept a documented discount.",
      "让边远团队被看见，也要占用管理带宽。走访、评审会，或者明着承认可见度折损。",
      "Spend capacity on an on-site visit.", "Spend capacity on a remote evidence forum.", "Accept the visibility discount and record debt.",
      "花带宽实地走访。", "花带宽开远程证据会。", "接受可见度折损并记债。"),
    m(310, "ag", 4, "legacy_rating_map", "Old Ratings, New Org", "旧档怎么搬进新组织",
      "A reorg changes reporting lines, not historical authorship. Map the old case without moving its frozen owner.",
      "重组会换汇报线，不会穿越回去换作者。映射旧案，但历史 owner 不能漂移。",
      "Map by frozen historical owner.", "Map through a dual-signed bridge.", "Keep the old case separate for one cycle.",
      "按冻结历史 owner 映射。", "通过双签桥接映射。", "旧案独立保留一个周期。"),
    m(311, "ag", 5, "pivot_policy", "A Pivot Is Not a Time Machine", "战略转向不是时光机",
      "New strategy may change future goals, never the old signed target. Freeze the boundary between both records.",
      "新战略可以改未来目标，不能倒改旧签字目标。把两份记录的边界冻结。",
      "Close the old target and open a new one.", "Bridge them with explicit split credit.", "Delay the pivot until next cycle.",
      "关闭旧目标，另开新目标。", "明确拆分贡献后桥接。", "推迟到下一周期再转向。"),

    m(334, "aj", 1, "demand_source", "One Door for Every Demand", "需求统一从正门进",
      "A demand without a source tag becomes free work. Record who asked, why, and where it entered.",
      "没来源标签的需求，最后都会变成免费加班。把谁提的、为什么、从哪进来的记清楚。",
      "Tag it as superior-sponsored.", "Tag it as territory demand.", "Tag it as incident-driven.",
      "标为上级发起。", "标为属地需求。", "标为事故驱动。"),
    m(335, "aj", 1, "emergency_route", "Everything Is Urgent", "怎么每件事都紧急",
      "An emergency label spends a real slot. Use one, trade scope, or send the request through the ordinary queue.",
      "“紧急”标签要吃真实槽位。占一个、拿范围交换，或者老老实实排队。",
      "Spend one emergency slot.", "Trade equal scope instead of a slot.", "Reject urgency and keep queue order.",
      "消耗一个紧急插单槽。", "等量换出范围，不占槽。", "不认紧急，按原顺序排队。"),
    m(336, "aj", 2, "admission_definition", "Definition of Ready", "准入完成定义",
      "A request enters delivery only after benefit, boundary and dependencies are signed—or its sponsor owns the ambiguity.",
      "收益、边界、依赖没签清楚，就不算能开工；硬塞进来，模糊责任归发起人。",
      "Return it for completion.", "Admit a bounded exploration.", "Force admission with sponsor liability.",
      "退回补全。", "准入一个有边界的探索。", "强制准入，发起人背模糊责任。"),
    m(338, "aj", 2, "triangle_signature", "Scope, Time, Quality: Pick Two", "范围、期限、质量：请签字",
      "The delivery triangle cannot be wished away. Freeze which corner moves and whose signature accepts the tradeoff.",
      "交付铁三角不会被口号消灭。冻结哪一角要动，以及谁签字承担取舍。",
      "Cut scope and sign it.", "Extend time and sign it.", "Add HC and sign the budget.",
      "缩范围并签字。", "延期限并签字。", "加 HC，并给预算签字。"),
    m(339, "aj", 3, "estimate_calibration", "Estimate the Work, Not the Hero", "校准估算，不奖赌命",
      "Rewarding only on-time delivery trains sandbagging and heroics. Compare estimate error with its recorded cause.",
      "只奖准时，会训练出灌水和赌命。把估算误差和已记录原因一起校准。",
      "Credit calibrated accuracy.", "Credit transparent uncertainty.", "Credit recovery but record estimate debt.",
      "奖励校准后的准确度。", "奖励公开不确定性。", "认可救火，但记录估算债。"),
    m(340, "aj", 4, "wip_route", "Stop Starting, Start Finishing", "少开工，多完工",
      "New work consumes delivery capacity and a WIP position. Respect the limit, sign an exception, or hide debt in plain sight.",
      "新开工要同时占交付容量和 WIP 位。守上限、签例外，或者把偷开的债明着记下来。",
      "Start within the WIP limit.", "Start with a signed WIP exception.", "Start over limit and record hidden-work debt.",
      "在 WIP 上限内开工。", "签署 WIP 例外后开工。", "超限开工并记录隐性工作债。"),
    m(342, "aj", 4, "blocker_attribution", "Who Owns the Blocked Time?", "阻塞时间算谁的",
      "Blocked hours belong to a cause and an unblock owner, not automatically to the delivery team.",
      "阻塞工时要归因到原因和解阻人，不能自动扣在交付团队头上。",
      "Charge the external dependency.", "Split shared causation.", "Charge the team with a review flag.",
      "计入外部依赖。", "按共同原因拆分。", "暂计团队，但挂复核标记。"),
    m(337, "aj", 5, "change_tax_route", "A Change Request Has a Tax", "改需求要交税",
      "Changing scope after work starts must move time, scope or capacity. A true disaster gets one recorded waiver.",
      "开工后改范围，必须动期限、范围或容量。真灾害可以用一次有记录的豁免。",
      "Pay ten capacity hours and extend time.", "Pay ten capacity hours and remove equal scope.", "Use the one disaster waiver and record policy debt.",
      "支付十小时容量并延期。", "支付十小时容量并等量减范围。", "使用一次灾害豁免并记录政策债。"),
    m(341, "aj", 5, "carryover_route", "Unfinished Work Crosses the Line", "未完工跨周期",
      "Carryover is not free progress. Release the current reservation and charge the next cycle exactly once.",
      "跨周期不是免费进度。释放本周期预留，并且只向下周期精确记账一次。",
      "Carry the whole remainder.", "Split and accept a finished slice.", "Cancel the remainder and close its debt.",
      "整体结转剩余工作。", "拆分并验收已完成部分。", "取消剩余部分并关闭其债。"),
    m(343, "aj", 6, "acceptance_route", "Three Signatures, One Delivery", "提出、执行、验收三方签收",
      "Delivery is not complete because the builder says so. Freeze proposer, executor and acceptor signatures with the outcome.",
      "不是执行者说“好了”就算交付。把提出、执行、验收三方签字和结论一起冻结。",
      "Accept with all three signatures.", "Accept conditionally with follow-up debt.", "Reject with a signed defect list.",
      "三方签字后验收。", "有条件验收，并留下跟进债。", "附签字缺陷清单后拒收。"),
    m(344, "aj", 7, "value_stage_split", "Launch Is Not Value", "上线不等于价值",
      "Settle launch, adoption and verified value as three conserved shares; no stage may mint a second hundred percent.",
      "上线、采用、验证价值要拆成三份守恒账；任何阶段都不能再印一套百分之百。",
      "Front-load launch credit.", "Use a balanced staged settlement.", "Back-load credit to verified value.",
      "前置认可上线。", "三阶段均衡结算。", "把大头留给已验证价值。"),
)


DOMAIN_ORDER = {
    "aa": (229, 230, 231, 232, 233, 234, 235, 236, 237, 240, 238, 239, 241),
    "ag": (301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311),
    "aj": (334, 335, 336, 338, 339, 340, 342, 337, 341, 343, 344),
}
STAGE_LAST = {
    "aa": {230: 1, 233: 2, 237: 3, 240: 4, 239: 5, 241: 6},
    "ag": {302: 1, 304: 2, 306: 3, 310: 4, 311: 5},
    "aj": {335: 1, 338: 2, 339: 3, 342: 4, 341: 5, 343: 6, 344: 7},
}
NEXT_DOMAIN = {"aa": "ag", "ag": "aj", "aj": None}
QUEUE_EVENTS = {"aa": 9001, "ag": 9002}
DOMAIN_TOTALS = {domain: len(order) for domain, order in DOMAIN_ORDER.items()}
LEGACY_EFFECT_FILENAME = "zg361_phase3_metrics_delivery_runtime_effects.txt"
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# A future hard-limit exception is valid only with both an engineering reason
# and a concrete CK3 live-artifact reference.  The current B5 layout needs no
# exception: every purpose shard contains two to five effects.
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}

# Keep public portfolio lifecycle, debt lifecycle, and each domain's internal
# orchestration independently loadable.  Every numbered mechanism then owns a
# five-effect unit: due-debt consumer, business consumer, and A/B/C routes.
# This is a purpose boundary, not an arbitrary line-count split.
EFFECT_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "zg361_phase3_portfolio_lifecycle_effects.txt",
        (
            "zg361_p3_initialize_portfolio_effect",
            "zg361_p3_open_portfolio_effect",
            "zg361_p3_finalize_portfolio_effect",
        ),
    ),
    (
        "zg361_phase3_policy_debt_lifecycle_effects.txt",
        (
            "zg361_p3_consume_due_policy_debts_effect",
            "zg361_p3_settle_deferred_portfolio_effect",
        ),
    ),
    *(
        (
            f"zg361_phase3_{domain}_orchestration_effects.txt",
            (
                f"zg361_p3_{domain}_initialize_effect",
                f"zg361_p3_{domain}_subject_read_effect",
                f"zg361_p3_{domain}_run_authorized_ai_effect",
                f"zg361_p3_{domain}_launch_effect",
            ),
        )
        for domain in ("aa", "ag", "aj")
    ),
    *(
        (
            "zg361_phase3_aj_m343_three_party_signoff_effects.txt"
            if spec.mid == 343
            else f"zg361_phase3_{spec.domain}_m{spec.mid}_{spec.field}_effects.txt",
            (
                f"zg361_p3_m{spec.mid}_consume_due_debt_effect",
                f"zg361_p3_m{spec.mid}_consume_effect",
                f"zg361_p3_m{spec.mid}_route_a_effect",
                f"zg361_p3_m{spec.mid}_route_b_effect",
                f"zg361_p3_m{spec.mid}_route_c_effect",
            ),
        )
        for spec in MECHANISMS
    ),
)


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.rstrip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.rstrip() + "\n").encode("utf-8")


def by_id() -> dict[int, Mechanism]:
    return {spec.mid: spec for spec in MECHANISMS}


def validate_specs() -> None:
    expected = set(range(229, 242)) | set(range(301, 312)) | set(range(334, 345))
    specs = by_id()
    if set(specs) != expected or len(specs) != len(MECHANISMS):
        raise ValueError("runtime slice must map exactly AA229-241, AG301-311, AJ334-344")
    if {mid for order in DOMAIN_ORDER.values() for mid in order} != expected:
        raise ValueError("domain execution order must touch every numbered mechanism once")
    if len({spec.field for spec in MECHANISMS}) != len(MECHANISMS):
        raise ValueError("every mechanism needs a unique semantic write field")
    for domain, order in DOMAIN_ORDER.items():
        prior_state = 0
        for mid in order:
            spec = specs[mid]
            if spec.domain != domain or spec.state < prior_state:
                raise ValueError(f"invalid stage order for {mid}")
            prior_state = spec.state
        if set(STAGE_LAST[domain]) != {mid for mid in order if mid == max(x for x in order if specs[x].state == specs[mid].state)}:
            raise ValueError(f"stage barriers incomplete for {domain}")


def indent(text: str, tabs: int = 1) -> str:
    prefix = "\t" * tabs
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def tuple_guard(spec: Mechanism) -> str:
    d = spec.domain
    return f"""zg361_case_kernel_full_guard_trigger = {{
\tOWNER_VAR = zg361_case_{d}_owner
\tSUBJECT_VAR = zg361_case_{d}_subject
\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\tCASE_VAR = zg361_case_{d}_case_serial
\tSTATE_VAR = zg361_case_{d}_state
\tACTIVE_VAR = zg361_case_{d}_active
\tEXPECTED_OWNER = $TICKET_OWNER$
\tEXPECTED_SUBJECT = $TICKET_SUBJECT$
\tEXPECTED_CYCLE = $TICKET_CYCLE$
\tEXPECTED_CASE = $TICKET_CASE$
\tEXPECTED_STATE = {spec.state}
}}"""


def receipt_guard(spec: Mechanism, choice: int) -> str:
    d, mid = spec.domain, spec.mid
    return f"""zg361_case_kernel_receipt_is_current_trigger = {{
\tRECEIPT_OWNER_VAR = zg361_p3_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = zg361_p3_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = zg361_p3_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = zg361_p3_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = zg361_p3_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = zg361_p3_m{mid}_receipt_choice
\tEXPECTED_OWNER = $TICKET_OWNER$
\tEXPECTED_SUBJECT = $TICKET_SUBJECT$
\tEXPECTED_CYCLE = $TICKET_CYCLE$
\tEXPECTED_CASE = $TICKET_CASE$
\tEXPECTED_STATE = {spec.state}
\tEXPECTED_CHOICE = {choice}
}}"""


def any_receipt(spec: Mechanism) -> str:
    return "OR = {\n" + "\n".join(indent(receipt_guard(spec, choice)) for choice in (1, 2, 3)) + "\n}"


def resource_checks(spec: Mechanism, choice: int) -> list[str]:
    d, mid = spec.domain, spec.mid
    checks = [
        f"has_variable = zg361_p3_{d}_operation_total",
        f"has_variable = zg361_p3_{d}_operation_used",
        "has_variable = zg361_p3_portfolio_deferred",
        f"var:zg361_p3_{d}_operation_used < var:zg361_p3_{d}_operation_total",
        "var:zg361_p3_portfolio_deferred = 0",
    ]
    if 230 <= mid <= 241:
        checks += [
            "has_variable = zg361_p3_metric_object_owner",
            "has_variable = zg361_p3_metric_object_subject",
            "has_variable = zg361_p3_metric_object_case",
            "has_variable = zg361_p3_metric_object_cycle",
            "has_variable = zg361_p3_metric_object_version",
            "var:zg361_p3_metric_object_subject = $TICKET_SUBJECT$",
            "var:zg361_p3_metric_object_cycle = $TICKET_CYCLE$",
            "var:zg361_p3_metric_object_case = $TICKET_CASE$",
        ]
    if 302 <= mid <= 311:
        checks += [
            "has_variable = zg361_p3_reorg_object_owner",
            "has_variable = zg361_p3_reorg_object_subject",
            "has_variable = zg361_p3_reorg_object_case",
            "has_variable = zg361_p3_reorg_object_cycle",
            "has_variable = zg361_p3_reorg_object_version",
            "var:zg361_p3_reorg_object_owner = $TICKET_OWNER$",
            "var:zg361_p3_reorg_object_subject = $TICKET_SUBJECT$",
            "var:zg361_p3_reorg_object_cycle = $TICKET_CYCLE$",
            "var:zg361_p3_reorg_object_case = $TICKET_CASE$",
        ]
    if 335 <= mid <= 344:
        checks += [
            "has_variable = zg361_p3_demand_object_owner",
            "has_variable = zg361_p3_demand_object_subject",
            "has_variable = zg361_p3_demand_object_case",
            "has_variable = zg361_p3_demand_object_cycle",
            "has_variable = zg361_p3_demand_object_version",
            "has_variable = zg361_p3_demand_admitted",
            "var:zg361_p3_demand_object_owner = $TICKET_OWNER$",
            "var:zg361_p3_demand_object_subject = $TICKET_SUBJECT$",
            "var:zg361_p3_demand_object_cycle = $TICKET_CYCLE$",
            "var:zg361_p3_demand_object_case = $TICKET_CASE$",
        ]
    if mid in (342, 337, 341, 343, 344):
        checks += [
            "has_variable = zg361_p3_delivery_object_owner",
            "has_variable = zg361_p3_delivery_object_subject",
            "has_variable = zg361_p3_delivery_object_cycle",
            "has_variable = zg361_p3_delivery_object_case",
            "has_variable = zg361_p3_delivery_object_version",
            "has_variable = zg361_p3_delivery_demand_case",
            "var:zg361_p3_delivery_object_owner = $TICKET_OWNER$",
            "var:zg361_p3_delivery_object_subject = $TICKET_SUBJECT$",
            "var:zg361_p3_delivery_object_cycle = $TICKET_CYCLE$",
            "var:zg361_p3_delivery_object_case = $TICKET_CASE$",
            "var:zg361_p3_delivery_demand_case = var:zg361_p3_demand_object_case",
        ]
    if mid == 240 and choice in (1, 2):
        checks += ["has_variable = zg361_p3_aa_sample_total", "has_variable = zg361_p3_aa_sample_used", "var:zg361_p3_aa_sample_used < var:zg361_p3_aa_sample_total"]
    if mid == 335 and choice == 1:
        checks += ["has_variable = zg361_p3_aj_emergency_total", "has_variable = zg361_p3_aj_emergency_used", "var:zg361_p3_aj_emergency_used < var:zg361_p3_aj_emergency_total"]
    if mid == 337 and choice in (1, 2):
        checks += [
            "has_variable = zg361_p3_aj_capacity_remaining",
            "OR = { var:zg361_p3_demand_admitted = 0 var:zg361_p3_aj_capacity_remaining >= 10 }",
        ]
    if mid == 337 and choice == 3:
        checks += [
            "has_variable = zg361_p3_aj_disaster_waiver_used",
            "OR = { var:zg361_p3_demand_admitted = 0 var:zg361_p3_aj_disaster_waiver_used = 0 }",
        ]
    if mid == 340:
        checks += [
            "has_variable = zg361_p3_aj_capacity_remaining",
            "has_variable = zg361_p3_demand_estimated_hours",
            "has_variable = zg361_p3_demand_estimated_plus_exception",
            (
                "OR = { var:zg361_p3_demand_admitted = 0 "
                + (
                    "var:zg361_p3_aj_capacity_remaining >= var:zg361_p3_demand_estimated_hours"
                    if choice == 1
                    else "var:zg361_p3_aj_capacity_remaining >= var:zg361_p3_demand_estimated_plus_exception"
                )
                + " }"
            ),
        ]
        if choice == 1:
            checks += [
                "has_variable = zg361_p3_aj_wip_used",
                "has_variable = zg361_p3_aj_wip_limit",
                "OR = { var:zg361_p3_demand_admitted = 0 var:zg361_p3_aj_wip_used < var:zg361_p3_aj_wip_limit }",
            ]
    if mid == 341:
        checks += [
            "has_variable = zg361_p3_demand_active",
            "has_variable = zg361_p3_demand_reserved_hours",
            "has_variable = zg361_p3_aj_wip_used",
            "has_variable = zg361_p3_aj_capacity_reserved",
            "OR = { var:zg361_p3_demand_active = 0 AND = { var:zg361_p3_aj_wip_used > 0 var:zg361_p3_aj_capacity_reserved >= var:zg361_p3_demand_reserved_hours } }",
        ]
        if choice == 1:
            checks += ["has_variable = zg361_p3_aj_next_capacity_remaining", "OR = { var:zg361_p3_demand_active = 0 var:zg361_p3_aj_next_capacity_remaining >= 10 }"]
        elif choice == 2:
            checks += ["has_variable = zg361_p3_aj_next_capacity_remaining", "OR = { var:zg361_p3_demand_active = 0 var:zg361_p3_aj_next_capacity_remaining >= 5 }"]
    if mid == 309 and choice in (1, 2):
        checks += ["has_variable = zg361_p3_ag_management_capacity_remaining", "var:zg361_p3_ag_management_capacity_remaining >= 10"]
    if mid == 343:
        checks += [
            "has_variable = zg361_p3_demand_proposer",
            "has_variable = zg361_p3_demand_executor",
            "has_variable = zg361_p3_demand_acceptor",
            "has_variable = zg361_p3_cross_reviewer_valid",
            "var:zg361_p3_cross_reviewer_valid = 1",
            "NOT = { var:zg361_p3_demand_proposer = var:zg361_p3_demand_executor }",
            "NOT = { var:zg361_p3_demand_proposer = var:zg361_p3_demand_acceptor }",
            "NOT = { var:zg361_p3_demand_executor = var:zg361_p3_demand_acceptor }",
        ]
    if mid == 344:
        checks += [
            "has_variable = zg361_p3_aj_value_credit_remaining",
            "has_variable = zg361_p3_demand_acceptance_outcome",
            "var:zg361_p3_aj_value_credit_remaining = 10000",
            "OR = { var:zg361_p3_demand_acceptance_outcome = 1 var:zg361_p3_demand_acceptance_outcome = 2 var:zg361_p3_demand_acceptance_outcome = 3 var:zg361_p3_demand_acceptance_outcome = 4 }",
        ]
    return checks


def atomic_precheck(spec: Mechanism, choice: int) -> str:
    """Render an existence-gated precheck; CK3 trigger blocks do not short-circuit."""
    checks = resource_checks(spec, choice)
    existence = [line for line in checks if line.startswith("has_variable = ")]
    reads = [line for line in checks if not line.startswith("has_variable = ")]
    return "trigger_if = {\n\tlimit = {\n" + indent("\n".join(existence), 2) + "\n\t}\n" + indent("\n".join(reads)) + "\n}\ntrigger_else = { always = no }"


def defer_precheck(spec: Mechanism) -> str:
    """Route C needs only case capacity and a free per-ID debt slot.

    It deliberately does not inspect or create the metric/reorg/demand/delivery
    objects required by A/B.  An older open debt is never overwritten: until
    its exact owner consumes it through the next-cycle portfolio adapter, a new
    C attempt for the same mechanism fails closed.
    """

    d, mid = spec.domain, spec.mid
    return f"""trigger_if = {{
\tlimit = {{
\t\thas_variable = zg361_p3_{d}_operation_total
\t\thas_variable = zg361_p3_{d}_operation_used
\t\thas_variable = zg361_p3_policy_debt_open_n
\t\thas_variable = zg361_p3_policy_debt_settled_n
\t\thas_variable = zg361_p3_portfolio_deferred
\t}}
\tvar:zg361_p3_{d}_operation_used < var:zg361_p3_{d}_operation_total
\ttrigger_if = {{
\t\tlimit = {{ has_variable = zg361_p3_m{mid}_debt_status }}
\t\tvar:zg361_p3_m{mid}_debt_status != 1
\t}}
\ttrigger_else = {{ always = yes }}
}}
trigger_else = {{ always = no }}"""


def stage_barrier(spec: Mechanism) -> str:
    """Require every receipt in this stage before the sole stage dispatcher."""
    same_stage = [
        item for item in MECHANISMS
        if item.domain == spec.domain and item.state == spec.state
    ]
    return "\n".join(any_receipt(item) for item in same_stage)


def business_effects(spec: Mechanism, choice: int) -> list[str]:
    d, mid = spec.domain, spec.mid

    if choice not in (1, 2):
        raise ValueError("route C is a pure defer and must not render business/resource writes")

    def setv(name: str, value: str | int) -> str:
        return f"set_variable = {{ name = {name} value = {value} }}"

    def addv(name: str, value: str | int) -> str:
        return f"change_variable = {{ name = {name} add = {value} }}"

    def subv(name: str, value: str | int) -> str:
        return f"change_variable = {{ name = {name} subtract = {value} }}"

    lines = [
        setv(f"zg361_p3_{spec.field}", choice),
        addv(f"zg361_p3_{d}_operation_used", 1),
    ]
    if choice == 1:
        lines += [addv(f"zg361_p3_{d}_quality", 2)]
    elif choice == 2:
        lines += [addv(f"zg361_p3_{d}_quality", 1), addv(f"zg361_p3_{d}_management_debt", 1)]
    else:
        raise AssertionError("unreachable route choice")

    # AA: one stable metric object.  Every later record points back to the
    # frozen metric cycle/case/version rather than treating its route receipt
    # as the business object.
    if mid == 229:
        definition_owner = ("$TICKET_SUBJECT$", "$TICKET_OWNER$", "$TICKET_SUBJECT$")[choice - 1]
        coauthor = ("$TICKET_OWNER$", "var:zg361_p3_cross_reviewer", "$TICKET_OWNER$")[choice - 1]
        lines += [
            setv("zg361_p3_metric_object_owner", definition_owner),
            setv("zg361_p3_metric_object_subject", "$TICKET_SUBJECT$"),
            setv("zg361_p3_metric_object_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_metric_object_case", "$TICKET_CASE$"),
            setv("zg361_p3_metric_object_version", 1),
            setv("zg361_p3_metric_definition_owner", definition_owner),
            setv("zg361_p3_metric_definition_coauthor", coauthor),
            setv("zg361_p3_metric_source_code", choice),
            setv("zg361_p3_metric_frequency_code", (1, 2, 3)[choice - 1]),
            setv("zg361_p3_metric_scope_code", (3, 2, 1)[choice - 1]),
            setv("zg361_p3_metric_denominator", 100),
            setv("zg361_p3_metric_definition_debt", (0, 1, 2)[choice - 1]),
            setv("zg361_p3_metric_confidence", (100, 80, 60)[choice - 1]),
            setv("zg361_p3_metric_provenance_case", "$TICKET_CASE$"),
            # Freeze the cross-domain business correlation only when the
            # portfolio initializer proved a current CP #026 receipt.  The
            # AA kernel keeps its own case identity; these fields are the
            # explicit project/contribution identity consumed by the metrics
            # provider and never infer lineage from coincident case numbers.
            "if = {",
            "\tlimit = { has_variable = zg361_p3_project_source_ready var:zg361_p3_project_source_ready = 1 has_variable = zg361_p3_project_source_owner has_variable = zg361_p3_project_source_subject has_variable = zg361_p3_project_source_cycle has_variable = zg361_p3_project_source_case has_variable = zg361_p3_project_source_contribution_receipt_id has_variable = zg361_p3_project_source_contribution_receipt_revision has_variable = zg361_p3_project_source_contribution_value }",
            "\tset_variable = { name = zg361_p3_m229_result_owner value = var:zg361_p3_project_source_owner }",
            "\tset_variable = { name = zg361_p3_m229_result_subject value = var:zg361_p3_project_source_subject }",
            "\tset_variable = { name = zg361_p3_m229_result_cycle value = var:zg361_p3_project_source_cycle }",
            "\tset_variable = { name = zg361_p3_m229_result_case value = var:zg361_p3_project_source_case }",
            "\tset_variable = { name = zg361_p3_m229_source_contribution_receipt_id value = var:zg361_p3_project_source_contribution_receipt_id }",
            "\tset_variable = { name = zg361_p3_m229_source_contribution_receipt_revision value = var:zg361_p3_project_source_contribution_receipt_revision }",
            "\tset_variable = { name = zg361_p3_m229_metrics_revision value = var:zg361_case_aa_revision }",
            "\tset_variable = { name = zg361_p3_m229_dictionary_key_code value = var:zg361_p3_metric_dictionary_owner }",
            "}",
        ]
    elif mid == 230:
        lines += [
            setv("zg361_p3_m230_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m230_metric_version", "var:zg361_p3_metric_object_version"),
            setv("zg361_p3_m230_source_count", (2, 3, 2)[choice - 1]),
            setv("zg361_p3_m230_resolved_value", (100, 95, 0)[choice - 1]),
            setv("zg361_p3_m230_pending", (0, 0, 1)[choice - 1]),
            setv("zg361_p3_m230_responsibility_owner", ("$TICKET_SUBJECT$", "$TICKET_OWNER$", "var:zg361_p3_cross_reviewer")[choice - 1]),
            setv("zg361_p3_m230_provenance_case", "$TICKET_CASE$"),
        ]
    elif mid == 231:
        lines += [
            setv("zg361_p3_m231_old_version", "var:zg361_p3_metric_object_version"),
            setv("zg361_p3_m231_old_denominator", "var:zg361_p3_metric_denominator"),
            setv("zg361_p3_m231_new_version", (2, 2, 1)[choice - 1]),
            setv("zg361_p3_m231_new_denominator", (120, 120, 100)[choice - 1]),
            setv("zg361_p3_m231_effective_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_m231_effective_cycle", (1, 0, 1)[choice - 1]),
            setv("zg361_p3_m231_dual_track", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m231_awards_rewritten", 0),
            setv("zg361_p3_metric_object_version", (2, 2, 1)[choice - 1]),
        ]
    elif mid == 232:
        lines += [
            setv("zg361_p3_m232_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m232_missing_units", 10),
            setv("zg361_p3_m232_filled_units", (10, 8, 0)[choice - 1]),
            setv("zg361_p3_m232_method_code", choice),
            setv("zg361_p3_m232_confidence", (100, 70, 0)[choice - 1]),
            setv("zg361_p3_m232_filler", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m232_approver", ("var:zg361_p3_cross_reviewer", "var:zg361_p3_cross_reviewer", "$TICKET_OWNER$")[choice - 1]),
            setv("zg361_p3_m232_signature_count", (2, 2, 0)[choice - 1]),
            setv("zg361_p3_m232_deviation_owner_code", (1, 2, 0)[choice - 1]),
        ]
    elif mid == 233:
        lines += [
            setv("zg361_p3_m233_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m233_access_level", (3, 2, 1)[choice - 1]),
            setv("zg361_p3_m233_query_channel", (1, 1, 0)[choice - 1]),
            setv("zg361_p3_m233_target_adjusted", (0, 0, 1)[choice - 1]),
            setv("zg361_p3_m233_unseen_anomaly_blame_eligible", (1, 1, 0)[choice - 1]),
        ]
    elif mid == 234:
        lines += [
            setv("zg361_p3_m234_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m234_leading_value", 80),
            setv("zg361_p3_m234_lagging_value", 60),
            setv("zg361_p3_m234_recognition_state", choice),
            setv("zg361_p3_m234_direction_conflict", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m234_requires_calibration", (0, 1, 0)[choice - 1]),
        ]
    elif mid == 235:
        lines += [
            setv("zg361_p3_m235_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m235_primary_value", 110),
            setv("zg361_p3_m235_guardrail_value", (90, 90, 95)[choice - 1]),
            setv("zg361_p3_m235_guardrail_breach", 1),
            setv("zg361_p3_m235_top_credit_eligible", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m235_crisis_override", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m235_liability_owner", ("$TICKET_SUBJECT$", "$TICKET_OWNER$", "$TICKET_SUBJECT$")[choice - 1]),
        ]
    elif mid == 236:
        lines += [
            setv("zg361_p3_m236_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m236_policy_code", choice),
            setv("zg361_p3_m236_threshold", 100),
            setv("zg361_p3_m236_locked_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_m236_year_end_mutable", 0),
            setv("zg361_p3_m236_gaming_risk", (1, 2, 3)[choice - 1]),
        ]
    elif mid == 237:
        lines += [
            setv("zg361_p3_m237_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m237_registered_days", 365),
            setv("zg361_p3_m237_declared_days", (365, 90, 30)[choice - 1]),
            setv("zg361_p3_m237_full_window_value", 90),
            setv("zg361_p3_m237_declared_value", (90, 110, 130)[choice - 1]),
            setv("zg361_p3_m237_cherry_picked", (0, 0, 1)[choice - 1]),
            setv("zg361_p3_m237_settled_value", (90, 95, 90)[choice - 1]),
            setv("zg361_p3_m237_integrity_penalty", (0, 0, 2)[choice - 1]),
        ]
    elif mid == 238:
        lines += [
            setv("zg361_p3_m238_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m238_provisional_credit_bps", 6000),
            setv("zg361_p3_m238_adoption_verified", (1, 0, 0)[choice - 1]),
            setv("zg361_p3_m238_governance_proxy", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m238_kept_credit_bps", (5000, 3000, 0)[choice - 1]),
            setv("zg361_p3_m238_clawback_bps", (1000, 3000, 6000)[choice - 1]),
        ]
    elif mid == 239:
        lines += [
            setv("zg361_p3_m239_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m239_primary_success_bps", 0),
            setv("zg361_p3_m239_preregistered", (1, 1, 0)[choice - 1]),
            setv("zg361_p3_m239_reusable_conclusion", (1, 0, 0)[choice - 1]),
            setv("zg361_p3_m239_negative_result_quality", (100, 60, 0)[choice - 1]),
        ]
    elif mid == 240:
        lines += [
            setv("zg361_p3_m240_experiment_owner", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m240_experiment_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_m240_experiment_case", "$TICKET_CASE$"),
            setv("zg361_p3_m240_experiment_version", 1),
            setv("zg361_p3_m240_sample_route", choice),
            setv("zg361_p3_m240_boundary_signer", ("$TICKET_SUBJECT$", "var:zg361_p3_cross_reviewer", "$TICKET_OWNER$")[choice - 1]),
            setv("zg361_p3_m240_boundary_signed", (0, 1, 0)[choice - 1]),
        ]
    elif mid == 241:
        lines += [
            setv("zg361_p3_m241_metric_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m241_attribution_version", 1),
            setv("zg361_p3_m241_builder", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m241_operator", "$TICKET_OWNER$"),
            setv("zg361_p3_m241_successor", "var:zg361_p3_cross_reviewer"),
            setv("zg361_p3_m241_effective_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_m241_effective_cycle", 1),
        ]

    # AG: a stable organization-change object keeps pre/post snapshots and
    # historical ownership independent from the operation receipt.
    elif mid == 301:
        lines += [
            setv("zg361_p3_reorg_object_owner", "$TICKET_OWNER$"),
            setv("zg361_p3_reorg_object_subject", "$TICKET_SUBJECT$"),
            setv("zg361_p3_reorg_object_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_reorg_object_case", "$TICKET_CASE$"),
            setv("zg361_p3_reorg_object_version", 1),
            setv("zg361_p3_m301_raw_outcome", 120),
            setv("zg361_p3_m301_tailwind", 40),
            setv("zg361_p3_m301_evidence_strength", (90, 70, 40)[choice - 1]),
            setv("zg361_p3_m301_adjustment", (-30, -20, -10)[choice - 1]),
            setv("zg361_p3_m301_personal_increment", (90, 100, 110)[choice - 1]),
            setv("zg361_p3_m301_adjustment_cap", (30, 20, 10)[choice - 1]),
        ]
    elif mid == 302:
        lines += [
            setv("zg361_p3_m302_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m302_expected_decline", -20),
            setv("zg361_p3_m302_actual_decline", -10),
            setv("zg361_p3_m302_avoided_decline", 10),
            setv("zg361_p3_m302_defense_quality", (90, 70, 20)[choice - 1]),
            setv("zg361_p3_m302_disclosed", (1, 1, 0)[choice - 1]),
            setv("zg361_p3_m302_sponsor_liability", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m302_integrity_penalty", (0, 0, 2)[choice - 1]),
        ]
    elif mid == 303:
        lines += [
            setv("zg361_p3_m303_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m303_start_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_m303_expiry_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_m303_expiry_cycle", (1, 2, 1)[choice - 1]),
            setv("zg361_p3_m303_milestone_evidence", 1),
            setv("zg361_p3_m303_exit_code", choice),
            setv("zg361_p3_m303_permanent_c_immunity", 0),
        ]
    elif mid == 304:
        lines += [
            setv("zg361_p3_m304_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m304_project_parent", "$TICKET_OWNER$"),
            setv("zg361_p3_m304_function_parent", "var:zg361_p3_cross_reviewer"),
            setv("zg361_p3_m304_project_parent_signed", 1),
            setv("zg361_p3_m304_function_parent_signed", 1),
            setv("zg361_p3_m304_final_owner", ("$TICKET_OWNER$", "$TICKET_OWNER$", "var:zg361_p3_cross_reviewer")[choice - 1]),
            setv("zg361_p3_m304_final_owner_count", 1),
        ]
    elif mid == 305:
        lines += [
            setv("zg361_p3_m305_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m305_quiet_period", 1),
            setv("zg361_p3_m305_route_code", choice),
            setv("zg361_p3_m305_crisis_reason", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m305_superior_signer", ("$TICKET_OWNER$", "var:zg361_p3_cross_reviewer", "$TICKET_OWNER$")[choice - 1]),
            setv("zg361_p3_m305_superior_signed", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m305_moved_subjects", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m305_old_cohort_frozen", 1),
        ]
    elif mid == 306:
        lines += [
            setv("zg361_p3_m306_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m306_actor", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m306_expiry_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_m306_expiry_cycle", 1),
            setv("zg361_p3_m306_support_code", choice),
            setv("zg361_p3_m306_full_target_count", 1),
        ]
    elif mid == 307:
        lines += [
            setv("zg361_p3_m307_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m307_team", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m307_center_type", choice),
            setv("zg361_p3_m307_revenue_metric", (1, 0, 1)[choice - 1]),
            setv("zg361_p3_m307_quality_metric", 1),
            setv("zg361_p3_m307_savings_metric", (0, 1, 1)[choice - 1]),
            setv("zg361_p3_m307_stability_metric", (0, 1, 1)[choice - 1]),
            setv("zg361_p3_m307_internal_value_metric", (0, 1, 1)[choice - 1]),
            setv("zg361_p3_m307_forced_common_metric", 0),
        ]
    elif mid == 308:
        manager, expert = ((20, 80), (30, 70), (40, 60))[choice - 1]
        lines += [
            setv("zg361_p3_m308_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m308_before_manager_hc", "var:zg361_p3_ag_manager_hc"),
            setv("zg361_p3_m308_before_expert_hc", "var:zg361_p3_ag_expert_hc"),
            setv("zg361_p3_m308_reporting_tax", manager * 2),
            setv("zg361_p3_m308_management_span", (5, 4, 3)[choice - 1]),
            setv("zg361_p3_m308_hc_version", 2),
        ]
    elif mid == 309:
        lines += [
            setv("zg361_p3_m309_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m309_team", "$TICKET_SUBJECT$"),
            setv("zg361_p3_m309_route_code", choice),
            setv("zg361_p3_m309_manager_hours", (10, 10, 0)[choice - 1]),
            setv("zg361_p3_m309_delivery_output_created", 0),
        ]
    elif mid == 310:
        lines += [
            setv("zg361_p3_m310_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m310_old_case", "var:zg361_p3_portfolio_result_case"),
            setv("zg361_p3_m310_mapping_version", "var:zg361_p3_reorg_object_version"),
            setv("zg361_p3_m310_mapping_route", choice),
            setv("zg361_p3_m310_historical_context_only", 1),
            setv("zg361_p3_m310_current_quota_slots", 0),
            setv("zg361_p3_m310_bridge_signer_old", "var:zg361_p3_portfolio_result_owner"),
            setv("zg361_p3_m310_bridge_signer_new", "var:zg361_p3_cross_reviewer"),
            setv("zg361_p3_m310_bridge_old_signed", 1),
            setv("zg361_p3_m310_bridge_new_signed", 1),
            setv("zg361_p3_m310_bridge_signature_count", 2),
        ]
    elif mid == 311:
        lines += [
            setv("zg361_p3_m311_reorg_case", "var:zg361_p3_reorg_object_case"),
            setv("zg361_p3_m311_pivot_version", 1),
            setv("zg361_p3_m311_old_goal_case", "var:zg361_p3_metric_object_case"),
            setv("zg361_p3_m311_old_goal_completed", 80),
            setv("zg361_p3_m311_old_goal_rewritten", 0),
            setv("zg361_p3_m311_new_goal_version", 2),
            setv("zg361_p3_m311_effective_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_m311_effective_cycle", (0, 0, 1)[choice - 1]),
            setv("zg361_p3_m311_overlap_visible", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m311_interruption_cost", (0, 0, 10)[choice - 1]),
        ]

    # AJ: one demand object survives intake, admission, WIP, carryover,
    # tri-party acceptance and the value chain.  A returned demand follows an
    # explicit N/A path and cannot mint work, signatures or value.
    elif mid == 334:
        proposer = ("$TICKET_OWNER$", "$TICKET_OWNER$", "var:zg361_p3_cross_reviewer")[choice - 1]
        acceptor = ("var:zg361_p3_cross_reviewer", "var:zg361_p3_cross_reviewer", "$TICKET_OWNER$")[choice - 1]
        source_owner = ("$TICKET_OWNER$", "$TICKET_SUBJECT$", "var:zg361_p3_cross_reviewer")[choice - 1]
        lines += [
            setv("zg361_p3_demand_object_owner", "$TICKET_OWNER$"),
            setv("zg361_p3_demand_object_subject", "$TICKET_SUBJECT$"),
            setv("zg361_p3_demand_object_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_demand_object_case", "$TICKET_CASE$"),
            setv("zg361_p3_demand_object_version", 1),
            setv("zg361_p3_demand_source_code", choice),
            setv("zg361_p3_demand_source_owner", source_owner),
            setv("zg361_p3_demand_proposer", proposer),
            setv("zg361_p3_demand_executor", "$TICKET_SUBJECT$"),
            setv("zg361_p3_demand_acceptor", acceptor),
            setv("zg361_p3_demand_queue_sequence", "$TICKET_CASE$"),
            setv("zg361_p3_demand_provenance_case", "$TICKET_CASE$"),
            setv("zg361_p3_demand_deadline_cycle", "$TICKET_CYCLE$"),
            addv("zg361_p3_demand_deadline_cycle", 1),
            setv("zg361_p3_demand_status", 1),
            setv("zg361_p3_demand_admitted", 0),
            setv("zg361_p3_demand_active", 0),
            setv("zg361_p3_demand_reserved_hours", 0),
            setv("zg361_p3_demand_accepted_hours", 0),
            setv("zg361_p3_demand_carry_hours", 0),
            setv("zg361_p3_demand_acceptance_outcome", 0),
            setv("zg361_p3_demand_estimated_plus_exception", 10),
        ]
    elif mid == 335:
        lines += [
            setv("zg361_p3_m335_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m335_route_code", choice),
            setv("zg361_p3_m335_slot_consumed", (1, 0, 0)[choice - 1]),
            setv("zg361_p3_m335_scope_trade_hours", (0, 10, 0)[choice - 1]),
            setv("zg361_p3_m335_queue_debt", (0, 0, 1)[choice - 1]),
        ]
    elif mid == 336:
        lines += [
            setv("zg361_p3_m336_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m336_admission_route", choice),
            setv("zg361_p3_m336_benefit_defined", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m336_acceptance_defined", (0, 0, 0)[choice - 1]),
            setv("zg361_p3_m336_boundary_defined", (0, 1, 0)[choice - 1]),
            setv("zg361_p3_m336_dependency_count", (1, 1, 2)[choice - 1]),
            setv("zg361_p3_demand_estimated_hours", (5, 10, 20)[choice - 1]),
            setv("zg361_p3_demand_estimated_plus_exception", (15, 20, 30)[choice - 1]),
            setv("zg361_p3_demand_admitted", (0, 1, 1)[choice - 1]),
            setv("zg361_p3_demand_status", (2, 3, 3)[choice - 1]),
            setv("zg361_p3_m336_forcing_owner", ("$TICKET_OWNER$", "$TICKET_OWNER$", "$TICKET_OWNER$")[choice - 1]),
            setv("zg361_p3_m336_sponsor_liability_signed", (0, 0, 1)[choice - 1]),
            addv("zg361_p3_demand_object_version", 1),
        ]
    elif mid == 338:
        lines += [
            setv("zg361_p3_m338_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m338_applicable", "var:zg361_p3_demand_admitted"),
            setv("zg361_p3_m338_tradeoff_code", choice),
            setv("zg361_p3_m338_tradeoff_signed", 0),
            setv("zg361_p3_m338_signer", "$TICKET_OWNER$"),
            setv("zg361_p3_m338_scope_reduction", 0),
            setv("zg361_p3_m338_deadline_extension", 0),
            setv("zg361_p3_m338_hc_added", 0),
            "if = {\n\tlimit = { var:zg361_p3_demand_admitted = 1 }\n\tset_variable = { name = zg361_p3_m338_tradeoff_signed value = 1 }\n\tchange_variable = { name = zg361_p3_demand_object_version add = 1 }\n\t"
            + ("set_variable = { name = zg361_p3_m338_scope_reduction value = 10 }" if choice == 1 else "change_variable = { name = zg361_p3_demand_deadline_cycle add = 1 }\n\tset_variable = { name = zg361_p3_m338_deadline_extension value = 1 }" if choice == 2 else "set_variable = { name = zg361_p3_m338_hc_added value = 1 }")
            + "\n}",
        ]
    elif mid == 339:
        lines += [
            setv("zg361_p3_m339_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m339_applicable", "var:zg361_p3_demand_admitted"),
            setv("zg361_p3_m339_estimated_hours", "var:zg361_p3_demand_estimated_hours"),
            setv("zg361_p3_m339_actual_hours", (8, 12, 20)[choice - 1]),
            setv("zg361_p3_m339_external_blocking_hours", (0, 4, 0)[choice - 1]),
            setv("zg361_p3_m339_normalized_actual", (8, 8, 20)[choice - 1]),
            setv("zg361_p3_m339_reason_code", choice),
            setv("zg361_p3_m339_padding_flag", (0, 0, 1)[choice - 1]),
            addv("zg361_p3_demand_object_version", 1),
        ]
    elif mid == 340:
        extra = 0 if choice == 1 else 10
        slots = 1 if choice == 1 else 2
        lines += [
            setv("zg361_p3_m340_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m340_applicable", "var:zg361_p3_demand_admitted"),
            setv("zg361_p3_m340_wip_slots", 0),
            setv("zg361_p3_m340_exception_signed", 0),
            setv("zg361_p3_m340_exception_owner", "$TICKET_OWNER$"),
            setv("zg361_p3_m340_hidden_penalty", 0),
            setv("zg361_p3_delivery_object_owner", "$TICKET_OWNER$"),
            setv("zg361_p3_delivery_object_subject", "$TICKET_SUBJECT$"),
            setv("zg361_p3_delivery_object_cycle", "$TICKET_CYCLE$"),
            setv("zg361_p3_delivery_object_case", "$TICKET_CASE$"),
            setv("zg361_p3_delivery_object_version", 1),
            setv("zg361_p3_delivery_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_delivery_deadline_cycle", "var:zg361_p3_demand_deadline_cycle"),
            setv("zg361_p3_delivery_status", 0),
            setv("zg361_p3_delivery_wip_slots", 0),
            setv("zg361_p3_delivery_reserved_hours", 0),
            "if = {\n\tlimit = { var:zg361_p3_demand_admitted = 1 }\n\tset_variable = { name = zg361_p3_demand_reserved_hours value = var:zg361_p3_demand_estimated_hours }\n"
            + (f"\tchange_variable = {{ name = zg361_p3_demand_reserved_hours add = {extra} }}\n" if extra else "")
            + "\tchange_variable = { name = zg361_p3_aj_capacity_remaining subtract = var:zg361_p3_demand_reserved_hours }\n\tchange_variable = { name = zg361_p3_aj_capacity_reserved add = var:zg361_p3_demand_reserved_hours }\n"
            + f"\tchange_variable = {{ name = zg361_p3_aj_wip_used add = {slots} }}\n\tset_variable = {{ name = zg361_p3_m340_wip_slots value = {slots} }}\n\tset_variable = {{ name = zg361_p3_delivery_wip_slots value = {slots} }}\n\tset_variable = {{ name = zg361_p3_delivery_reserved_hours value = var:zg361_p3_demand_reserved_hours }}\n\tset_variable = {{ name = zg361_p3_delivery_status value = 1 }}\n\tset_variable = {{ name = zg361_p3_demand_active value = 1 }}\n\tset_variable = {{ name = zg361_p3_demand_status value = 4 }}\n\tchange_variable = {{ name = zg361_p3_demand_object_version add = 1 }}"
            + ("\n\tset_variable = { name = zg361_p3_m340_exception_signed value = 1 }\n\tchange_variable = { name = zg361_p3_aj_wip_exception_count add = 1 }" if choice == 2 else "\n\tset_variable = { name = zg361_p3_m340_hidden_penalty value = 2 }\n\tchange_variable = { name = zg361_p3_aj_hidden_wip_debt add = 2 }\n\tchange_variable = { name = zg361_p3_aj_wip_exception_count add = 1 }" if choice == 3 else "")
            + "\n}",
        ]
    elif mid == 342:
        team_bps, external_bps = ((0, 10000), (5000, 5000), (10000, 0))[choice - 1]
        lines += [
            setv("zg361_p3_m342_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m342_applicable", "var:zg361_p3_demand_active"),
            setv("zg361_p3_m342_blocker_owner", ("var:zg361_p3_cross_reviewer", "$TICKET_OWNER$", "$TICKET_SUBJECT$")[choice - 1]),
            setv("zg361_p3_m342_blocked_since_sequence", 1),
            setv("zg361_p3_m342_escalated_sequence", (2, 0, 0)[choice - 1]),
            setv("zg361_p3_m342_team_blocker_bps", team_bps),
            setv("zg361_p3_m342_external_blocker_bps", external_bps),
            setv("zg361_p3_m342_blocker_total", 10000),
            setv("zg361_p3_m342_executor_low_output_penalty", 0),
            setv("zg361_p3_m342_shared_responsibility", (0, 1, 1)[choice - 1]),
            addv("zg361_p3_delivery_object_version", 1),
            addv("zg361_p3_demand_object_version", 1),
        ]
    elif mid == 337:
        lines += [
            setv("zg361_p3_m337_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m337_applicable", "var:zg361_p3_demand_admitted"),
            setv("zg361_p3_m337_change_route", choice),
            setv("zg361_p3_m337_change_tax", 0),
            setv("zg361_p3_m337_approver", "$TICKET_OWNER$"),
            setv("zg361_p3_m337_scope_removed", 0),
            setv("zg361_p3_m337_policy_debt", 0),
            "if = {\n\tlimit = { var:zg361_p3_demand_admitted = 1 }\n"
            + ("\tchange_variable = { name = zg361_p3_aj_capacity_remaining subtract = 10 }\n\tchange_variable = { name = zg361_p3_aj_capacity_reserved add = 10 }\n\tchange_variable = { name = zg361_p3_demand_reserved_hours add = 10 }\n\tset_variable = { name = zg361_p3_m337_change_tax value = 10 }\n\tchange_variable = { name = zg361_p3_demand_deadline_cycle add = 1 }" if choice == 1 else "\tchange_variable = { name = zg361_p3_aj_capacity_remaining subtract = 10 }\n\tchange_variable = { name = zg361_p3_aj_capacity_reserved add = 10 }\n\tchange_variable = { name = zg361_p3_demand_reserved_hours add = 10 }\n\tset_variable = { name = zg361_p3_m337_change_tax value = 10 }\n\tset_variable = { name = zg361_p3_m337_scope_removed value = 10 }" if choice == 2 else "\tset_variable = { name = zg361_p3_aj_disaster_waiver_used value = 1 }\n\tchange_variable = { name = zg361_p3_aj_policy_debt add = 10 }\n\tset_variable = { name = zg361_p3_m337_policy_debt value = 10 }")
            + "\n\tset_variable = { name = zg361_p3_delivery_deadline_cycle value = var:zg361_p3_demand_deadline_cycle }\n\tchange_variable = { name = zg361_p3_delivery_object_version add = 1 }\n\tchange_variable = { name = zg361_p3_demand_object_version add = 1 }\n}",
        ]
    elif mid == 341:
        carry = (10, 5, 0)[choice - 1]
        lines += [
            setv("zg361_p3_m341_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m341_applicable", "var:zg361_p3_demand_active"),
            setv("zg361_p3_m341_transfer_hours", 0),
            setv("zg361_p3_m341_accepted_hours", 0),
            setv("zg361_p3_m341_cancelled", 0),
            setv("zg361_p3_m341_released_current", 0),
            "if = {\n\tlimit = { var:zg361_p3_demand_active = 1 }\n\tset_variable = { name = zg361_p3_m341_released_current value = var:zg361_p3_demand_reserved_hours }\n\tchange_variable = { name = zg361_p3_aj_capacity_reserved subtract = var:zg361_p3_demand_reserved_hours }\n\tchange_variable = { name = zg361_p3_aj_capacity_remaining add = var:zg361_p3_demand_reserved_hours }\n\tchange_variable = { name = zg361_p3_aj_wip_used subtract = var:zg361_p3_m340_wip_slots }\n"
            + (f"\tset_variable = {{ name = zg361_p3_m341_transfer_hours value = {carry} }}\n\tset_variable = {{ name = zg361_p3_demand_carry_hours value = {carry} }}\n\tchange_variable = {{ name = zg361_p3_aj_next_capacity_remaining subtract = {carry} }}\n\tchange_variable = {{ name = zg361_p3_aj_next_capacity_reserved add = {carry} }}\n\tset_variable = {{ name = zg361_p3_m341_accepted_hours value = var:zg361_p3_demand_reserved_hours }}\n\tchange_variable = {{ name = zg361_p3_m341_accepted_hours subtract = {carry} }}\n\tset_variable = {{ name = zg361_p3_demand_accepted_hours value = var:zg361_p3_m341_accepted_hours }}" if carry else "\tset_variable = { name = zg361_p3_m341_cancelled value = 1 }\n\tset_variable = { name = zg361_p3_demand_admitted value = 0 }\n\tset_variable = { name = zg361_p3_demand_status value = 7 }")
            + f"\n\tset_variable = {{ name = zg361_p3_demand_active value = 0 }}\n\tset_variable = {{ name = zg361_p3_demand_reserved_hours value = 0 }}\n\tset_variable = {{ name = zg361_p3_delivery_reserved_hours value = 0 }}\n\tset_variable = {{ name = zg361_p3_delivery_wip_slots value = 0 }}\n\tset_variable = {{ name = zg361_p3_delivery_status value = {(2, 2, 3)[choice - 1]} }}\n\tchange_variable = {{ name = zg361_p3_delivery_object_version add = 1 }}\n\tchange_variable = {{ name = zg361_p3_demand_object_version add = 1 }}\n}}",
        ]
    elif mid == 343:
        outcome = (1, 2, 3)[choice - 1]
        lines += [
            setv("zg361_p3_m343_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m343_applicable", 0),
            setv("zg361_p3_m343_proposer_signer", "var:zg361_p3_demand_proposer"),
            setv("zg361_p3_m343_executor_signer", "var:zg361_p3_demand_executor"),
            setv("zg361_p3_m343_acceptor_signer", "var:zg361_p3_demand_acceptor"),
            setv("zg361_p3_m343_proposer_signed", 0),
            setv("zg361_p3_m343_executor_signed", 0),
            setv("zg361_p3_m343_acceptor_signed", 0),
            setv("zg361_p3_m343_signature_count", 0),
            setv("zg361_p3_demand_acceptance_outcome", 4),
            "if = {\n\tlimit = { var:zg361_p3_demand_accepted_hours > 0 }\n\tset_variable = { name = zg361_p3_m343_applicable value = 1 }\n\tset_variable = { name = zg361_p3_m343_proposer_signed value = 1 }\n\tset_variable = { name = zg361_p3_m343_executor_signed value = 1 }\n\tset_variable = { name = zg361_p3_m343_acceptor_signed value = 1 }\n\tset_variable = { name = zg361_p3_m343_signature_count value = 3 }\n"
            + f"\tset_variable = {{ name = zg361_p3_demand_acceptance_outcome value = {outcome} }}\n\tset_variable = {{ name = zg361_p3_demand_status value = 6 }}\n\tset_variable = {{ name = zg361_p3_delivery_status value = {3 + outcome} }}\n\tchange_variable = {{ name = zg361_p3_delivery_object_version add = 1 }}\n\tchange_variable = {{ name = zg361_p3_demand_object_version add = 1 }}\n}}",
        ]
    elif mid == 344:
        launch, adoption, value = ((6000, 2500, 1500), (3000, 3000, 4000), (1000, 2000, 7000))[choice - 1]
        lines += [
            setv("zg361_p3_m344_demand_case", "var:zg361_p3_demand_object_case"),
            setv("zg361_p3_m344_applicable", 0),
            setv("zg361_p3_m344_launch_share", 0),
            setv("zg361_p3_m344_adoption_share", 0),
            setv("zg361_p3_m344_verified_value_share", 0),
            setv("zg361_p3_m344_share_total", 0),
            setv("zg361_p3_m344_launch_settled", 0),
            setv("zg361_p3_m344_adoption_settled", 0),
            setv("zg361_p3_m344_value_settled", 0),
            setv("zg361_p3_m344_maturity", 0),
            setv("zg361_p3_m344_unallocated_share", 10000),
            setv("zg361_p3_m344_ledger_total", 10000),
            setv("zg361_p3_m344_launch_order", 0),
            setv("zg361_p3_m344_adoption_order", 0),
            setv("zg361_p3_m344_value_order", 0),
            "if = {\n\tlimit = { OR = { var:zg361_p3_demand_acceptance_outcome = 1 var:zg361_p3_demand_acceptance_outcome = 2 } }\n\tset_variable = { name = zg361_p3_m344_applicable value = 1 }\n"
            + f"\tset_variable = {{ name = zg361_p3_m344_launch_share value = {launch} }}\n\tset_variable = {{ name = zg361_p3_m344_launch_settled value = 1 }}\n\tset_variable = {{ name = zg361_p3_m344_launch_order value = 1 }}\n\tset_variable = {{ name = zg361_p3_m344_maturity value = 1 }}\n\tset_variable = {{ name = zg361_p3_m344_adoption_share value = {adoption} }}\n\tset_variable = {{ name = zg361_p3_m344_adoption_settled value = 1 }}\n\tset_variable = {{ name = zg361_p3_m344_adoption_order value = 2 }}\n\tset_variable = {{ name = zg361_p3_m344_maturity value = 2 }}\n\tset_variable = {{ name = zg361_p3_m344_verified_value_share value = {value} }}\n\tset_variable = {{ name = zg361_p3_m344_value_settled value = 1 }}\n\tset_variable = {{ name = zg361_p3_m344_value_order value = 3 }}\n\tset_variable = {{ name = zg361_p3_m344_maturity value = 3 }}\n\tset_variable = {{ name = zg361_p3_m344_share_total value = 10000 }}\n\tset_variable = {{ name = zg361_p3_m344_unallocated_share value = 0 }}\n\tset_variable = {{ name = zg361_p3_aj_value_credit_remaining value = 0 }}\n\tset_variable = {{ name = zg361_p3_demand_status value = 8 }}\n\tset_variable = {{ name = zg361_p3_delivery_status value = 7 }}\n\tchange_variable = {{ name = zg361_p3_delivery_object_version add = 1 }}\n\tchange_variable = {{ name = zg361_p3_demand_object_version add = 1 }}\n}}",
        ]

    split_10000: dict[int, tuple[tuple[int, int, int], tuple[str, str, str]]] = {
        234: ((6000, 4000, 0) if choice == 1 else (5000, 5000, 0) if choice == 2 else (3000, 7000, 0), ("leading_share", "lagging_share", "signal_reserve")),
        235: ((5000, 5000, 0) if choice == 1 else (6000, 4000, 0) if choice == 2 else (7000, 3000, 0), ("primary_share", "guardrail_share", "guardrail_reserve")),
        238: ((1000, 7000, 2000) if choice == 1 else (3000, 5000, 2000) if choice == 2 else (6000, 2000, 2000), ("vanity_share", "value_share", "unverified_share")),
        241: ((5000, 3000, 2000) if choice == 1 else (3300, 3300, 3400) if choice == 2 else (2000, 3000, 5000), ("builder_share", "operator_share", "successor_share")),
    }
    if mid in split_10000:
        values, names = split_10000[mid]
        lines += [f"set_variable = {{ name = zg361_p3_m{mid}_{name} value = {value} }}" for name, value in zip(names, values)]
        lines += [f"set_variable = {{ name = zg361_p3_m{mid}_share_total value = 10000 }}"]
        if mid == 241:
            lines += [
                f"set_variable = {{ name = zg361_p3_m241_builder_cost_bps value = {values[0]} }}",
                f"set_variable = {{ name = zg361_p3_m241_operator_cost_bps value = {values[1]} }}",
                f"set_variable = {{ name = zg361_p3_m241_successor_cost_bps value = {values[2]} }}",
                "set_variable = { name = zg361_p3_m241_cost_share_total value = 10000 }",
                "set_variable = { name = zg361_p3_m241_cost_provenance_case value = $TICKET_CASE$ }",
            ]
    if mid == 239:
        lines += [f"set_variable = {{ name = zg361_p3_m239_learning_credit_bps value = {(7000, 4000, 0)[choice - 1]} }}"]
    if mid == 240:
        if choice in (1, 2):
            lines += [addv("zg361_p3_aa_sample_used", 1), setv("zg361_p3_m240_clean_claim", 1), setv("zg361_p3_m240_queue_sequence", 0)]
        else:
            lines += [setv("zg361_p3_m240_clean_claim", 0), addv("zg361_p3_aa_sample_queue", 1), setv("zg361_p3_m240_queue_sequence", "var:zg361_p3_aa_sample_queue")]
    if mid == 304:
        weights = ((6000, 4000), (5000, 5000), (4000, 6000))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_p3_m304_project_parent_bps value = {weights[0]} }}",
            f"set_variable = {{ name = zg361_p3_m304_function_parent_bps value = {weights[1]} }}",
            "set_variable = { name = zg361_p3_m304_parent_weight_total value = 10000 }",
            f"set_variable = {{ name = zg361_p3_m304_project_goal_bps value = {weights[0]} }}",
            f"set_variable = {{ name = zg361_p3_m304_function_goal_bps value = {weights[1]} }}",
            "set_variable = { name = zg361_p3_m304_goal_share_total value = 10000 }",
            setv("zg361_p3_m304_dual_signature", 1),
        ]
    if mid == 306:
        weights = ((30, 70), (50, 50), (70, 30))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_p3_m306_manager_weight value = {weights[0]} }}",
            f"set_variable = {{ name = zg361_p3_m306_expert_weight value = {weights[1]} }}",
            "set_variable = { name = zg361_p3_m306_weight_total value = 100 }",
        ]
    if mid == 308:
        weights = ((20, 80), (30, 70), (40, 60))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_p3_ag_manager_hc value = {weights[0]} }}",
            f"set_variable = {{ name = zg361_p3_ag_expert_hc value = {weights[1]} }}",
            "set_variable = { name = zg361_p3_ag_hc_total value = 100 }",
        ]
    if mid == 309:
        if choice in (1, 2):
            lines += [subv("zg361_p3_ag_management_capacity_remaining", 10), addv("zg361_p3_ag_management_capacity_used", 10), setv("zg361_p3_m309_visibility_gain", 10)]
        else:
            lines += [setv("zg361_p3_m309_visibility_gain", 0), addv("zg361_p3_ag_visibility_debt", 10)]
    if mid == 310:
        lines += [
            "set_variable = { name = zg361_p3_m310_historical_owner value = var:zg361_p3_portfolio_result_owner }",
            "set_variable = { name = zg361_p3_m310_mapped_owner value = var:zg361_p3_reorg_object_owner }",
            "set_variable = { name = zg361_p3_m310_bridge_dual_signed value = 1 }",
            "change_variable = { name = zg361_p3_reorg_object_version add = 1 }",
        ]
    if mid == 311:
        lines += ["set_variable = { name = zg361_p3_m311_old_target_locked value = 1 }", f"set_variable = {{ name = zg361_p3_m311_future_target_route value = {choice} }}"]
    if mid == 335:
        if choice == 1:
            lines += ["change_variable = { name = zg361_p3_aj_emergency_used add = 1 }"]
        elif choice == 2:
            lines += ["change_variable = { name = zg361_p3_aj_scope_traded add = 10 }"]
        else:
            lines += ["change_variable = { name = zg361_p3_aj_queue_debt add = 1 }"]
    return lines


def operation_call(spec: Mechanism, choice: int) -> str:
    d, mid = spec.domain, spec.mid
    return f"""zg361_case_kernel_record_operation_effect = {{
\tOWNER_VAR = zg361_case_{d}_owner
\tSUBJECT_VAR = zg361_case_{d}_subject
\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\tCASE_VAR = zg361_case_{d}_case_serial
\tSTATE_VAR = zg361_case_{d}_state
\tREVISION_VAR = zg361_case_{d}_revision
\tACTIVE_VAR = zg361_case_{d}_active
\tTIMELINE_VAR = zg361_case_{d}_timeline_serial
\tFEEDBACK_VAR = zg361_case_{d}_feedback_revision
\tLAST_OPERATION_VAR = zg361_case_{d}_last_operation
\tLAST_CHOICE_VAR = zg361_case_{d}_last_choice
\tRECEIPT_OWNER_VAR = zg361_p3_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = zg361_p3_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = zg361_p3_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = zg361_p3_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = zg361_p3_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = zg361_p3_m{mid}_receipt_choice
\tTICKET_OWNER = $TICKET_OWNER$
\tTICKET_SUBJECT = $TICKET_SUBJECT$
\tTICKET_CYCLE = $TICKET_CYCLE$
\tTICKET_CASE = $TICKET_CASE$
\tTICKET_STATE = {spec.state}
\tOPERATION_ID = {mid}
\tCHOICE = {choice}
}}"""


CONSUMER_SOURCES: dict[int, tuple[str, ...]] = {
    229: ("zg361_p3_metric_definition_owner", "zg361_p3_metric_source_code", "zg361_p3_metric_confidence", "zg361_p3_metric_definition_debt"),
    230: ("zg361_p3_m230_resolved_value", "zg361_p3_m230_pending", "zg361_p3_m230_responsibility_owner", "zg361_p3_m230_source_count"),
    231: ("zg361_p3_m231_old_version", "zg361_p3_m231_new_version", "zg361_p3_m231_effective_cycle", "zg361_p3_m231_awards_rewritten"),
    232: ("zg361_p3_m232_missing_units", "zg361_p3_m232_filled_units", "zg361_p3_m232_signature_count", "zg361_p3_m232_confidence"),
    233: ("zg361_p3_m233_access_level", "zg361_p3_m233_query_channel", "zg361_p3_m233_target_adjusted", "zg361_p3_m233_unseen_anomaly_blame_eligible"),
    234: ("zg361_p3_m234_leading_value", "zg361_p3_m234_lagging_value", "zg361_p3_m234_direction_conflict", "zg361_p3_m234_requires_calibration"),
    235: ("zg361_p3_m235_primary_value", "zg361_p3_m235_guardrail_value", "zg361_p3_m235_guardrail_breach", "zg361_p3_m235_top_credit_eligible"),
    236: ("zg361_p3_m236_policy_code", "zg361_p3_m236_threshold", "zg361_p3_m236_locked_cycle", "zg361_p3_m236_gaming_risk"),
    237: ("zg361_p3_m237_declared_days", "zg361_p3_m237_cherry_picked", "zg361_p3_m237_settled_value", "zg361_p3_m237_integrity_penalty"),
    238: ("zg361_p3_m238_adoption_verified", "zg361_p3_m238_governance_proxy", "zg361_p3_m238_kept_credit_bps", "zg361_p3_m238_clawback_bps"),
    239: ("zg361_p3_m239_primary_success_bps", "zg361_p3_m239_preregistered", "zg361_p3_m239_reusable_conclusion", "zg361_p3_m239_learning_credit_bps"),
    240: ("zg361_p3_m240_experiment_case", "zg361_p3_m240_sample_route", "zg361_p3_m240_boundary_signed", "zg361_p3_m240_clean_claim", "zg361_p3_m240_queue_sequence"),
    241: ("zg361_p3_m241_attribution_version", "zg361_p3_m241_effective_cycle", "zg361_p3_m241_share_total", "zg361_p3_m241_cost_share_total"),
    301: ("zg361_p3_m301_raw_outcome", "zg361_p3_m301_tailwind", "zg361_p3_m301_adjustment", "zg361_p3_m301_personal_increment"),
    302: ("zg361_p3_m302_expected_decline", "zg361_p3_m302_actual_decline", "zg361_p3_m302_avoided_decline", "zg361_p3_m302_integrity_penalty"),
    303: ("zg361_p3_m303_start_cycle", "zg361_p3_m303_expiry_cycle", "zg361_p3_m303_exit_code", "zg361_p3_m303_permanent_c_immunity"),
    304: ("zg361_p3_m304_project_parent", "zg361_p3_m304_function_parent", "zg361_p3_m304_parent_weight_total", "zg361_p3_m304_goal_share_total", "zg361_p3_m304_final_owner"),
    305: ("zg361_p3_m305_quiet_period", "zg361_p3_m305_crisis_reason", "zg361_p3_m305_superior_signed", "zg361_p3_m305_old_cohort_frozen"),
    306: ("zg361_p3_m306_expiry_cycle", "zg361_p3_m306_manager_weight", "zg361_p3_m306_expert_weight", "zg361_p3_m306_weight_total"),
    307: ("zg361_p3_m307_center_type", "zg361_p3_m307_revenue_metric", "zg361_p3_m307_savings_metric", "zg361_p3_m307_forced_common_metric"),
    308: ("zg361_p3_m308_before_manager_hc", "zg361_p3_m308_before_expert_hc", "zg361_p3_ag_manager_hc", "zg361_p3_ag_expert_hc", "zg361_p3_ag_hc_total"),
    309: ("zg361_p3_m309_manager_hours", "zg361_p3_m309_visibility_gain", "zg361_p3_m309_delivery_output_created", "zg361_p3_ag_management_capacity_remaining"),
    310: ("zg361_p3_m310_old_case", "zg361_p3_m310_mapping_version", "zg361_p3_m310_mapping_route", "zg361_p3_m310_historical_owner", "zg361_p3_m310_mapped_owner", "zg361_p3_m310_bridge_signature_count", "zg361_p3_m310_current_quota_slots"),
    311: ("zg361_p3_m311_old_goal_case", "zg361_p3_m311_old_goal_completed", "zg361_p3_m311_old_goal_rewritten", "zg361_p3_m311_new_goal_version", "zg361_p3_m311_effective_cycle"),
    334: ("zg361_p3_demand_source_code", "zg361_p3_demand_source_owner", "zg361_p3_demand_proposer", "zg361_p3_demand_executor", "zg361_p3_demand_acceptor", "zg361_p3_demand_queue_sequence"),
    335: ("zg361_p3_m335_slot_consumed", "zg361_p3_m335_scope_trade_hours", "zg361_p3_m335_queue_debt", "zg361_p3_aj_emergency_used"),
    336: ("zg361_p3_m336_admission_route", "zg361_p3_m336_benefit_defined", "zg361_p3_m336_acceptance_defined", "zg361_p3_m336_boundary_defined", "zg361_p3_demand_estimated_hours", "zg361_p3_demand_admitted"),
    337: ("zg361_p3_m337_applicable", "zg361_p3_m337_change_route", "zg361_p3_m337_change_tax", "zg361_p3_m337_scope_removed", "zg361_p3_m337_policy_debt", "zg361_p3_demand_deadline_cycle"),
    338: ("zg361_p3_m338_applicable", "zg361_p3_m338_tradeoff_code", "zg361_p3_m338_tradeoff_signed", "zg361_p3_m338_signer", "zg361_p3_demand_deadline_cycle"),
    339: ("zg361_p3_m339_applicable", "zg361_p3_m339_estimated_hours", "zg361_p3_m339_actual_hours", "zg361_p3_m339_normalized_actual", "zg361_p3_m339_reason_code", "zg361_p3_m339_padding_flag"),
    340: ("zg361_p3_m340_applicable", "zg361_p3_m340_wip_slots", "zg361_p3_m340_exception_signed", "zg361_p3_m340_hidden_penalty", "zg361_p3_delivery_reserved_hours"),
    341: ("zg361_p3_m341_applicable", "zg361_p3_m341_transfer_hours", "zg361_p3_m341_accepted_hours", "zg361_p3_m341_cancelled", "zg361_p3_m341_released_current", "zg361_p3_aj_next_capacity_reserved"),
    342: ("zg361_p3_m342_applicable", "zg361_p3_m342_blocker_owner", "zg361_p3_m342_blocked_since_sequence", "zg361_p3_m342_escalated_sequence", "zg361_p3_m342_blocker_total", "zg361_p3_m342_executor_low_output_penalty"),
    343: ("zg361_p3_m343_applicable", "zg361_p3_m343_proposer_signer", "zg361_p3_m343_executor_signer", "zg361_p3_m343_acceptor_signer", "zg361_p3_m343_signature_count", "zg361_p3_demand_acceptance_outcome"),
    344: ("zg361_p3_m344_applicable", "zg361_p3_m344_launch_share", "zg361_p3_m344_adoption_share", "zg361_p3_m344_verified_value_share", "zg361_p3_m344_maturity", "zg361_p3_m344_launch_order", "zg361_p3_m344_adoption_order", "zg361_p3_m344_value_order", "zg361_p3_m344_unallocated_share", "zg361_p3_m344_ledger_total"),
}


def consumer_fields(spec: Mechanism) -> tuple[str, ...]:
    mid = spec.mid
    common: list[str] = []
    if 229 <= mid <= 241:
        common += ["zg361_p3_metric_object_case", "zg361_p3_metric_object_version"]
    elif 301 <= mid <= 311:
        common += ["zg361_p3_reorg_object_case", "zg361_p3_reorg_object_version"]
    else:
        common += ["zg361_p3_demand_object_case", "zg361_p3_demand_object_version", "zg361_p3_demand_deadline_cycle", "zg361_p3_demand_status"]
        if mid in (340, 342, 337, 341, 343, 344):
            common += ["zg361_p3_delivery_object_case", "zg361_p3_delivery_object_version", "zg361_p3_delivery_deadline_cycle", "zg361_p3_delivery_status"]
    return tuple(dict.fromkeys((*common, *CONSUMER_SOURCES[mid])))


def render_consumer(spec: Mechanism) -> str:
    d, mid = spec.domain, spec.mid
    projection = consumer_fields(spec)
    required = [
        f"zg361_p3_m{mid}_write_owner", f"zg361_p3_m{mid}_write_subject",
        f"zg361_p3_m{mid}_write_cycle", f"zg361_p3_m{mid}_write_case",
        f"zg361_p3_m{mid}_write_state", f"zg361_p3_{spec.field}",
        f"zg361_case_{d}_owner", f"zg361_case_{d}_subject",
        f"zg361_case_{d}_cycle_serial", f"zg361_case_{d}_case_serial", f"zg361_case_{d}_state",
        *projection,
    ]
    required = list(dict.fromkeys(required))
    existence = "\n".join(f"\t\t\t\thas_variable = {name}" for name in required)
    comparisons = "\n".join((
        f"\t\t\tvar:zg361_p3_m{mid}_write_owner = var:zg361_case_{d}_owner",
        f"\t\t\tvar:zg361_p3_m{mid}_write_subject = var:zg361_case_{d}_subject",
        f"\t\t\tvar:zg361_p3_m{mid}_write_cycle = var:zg361_case_{d}_cycle_serial",
        f"\t\t\tvar:zg361_p3_m{mid}_write_case = var:zg361_case_{d}_case_serial",
        f"\t\t\tvar:zg361_p3_m{mid}_write_state = var:zg361_case_{d}_state",
    ))
    consumed_required = "\n".join(f"\t\t\t\t\t\thas_variable = zg361_p3_m{mid}_consumed_{name}" for name in ("owner", "subject", "cycle", "case", "state"))
    consumed_compare = "\n".join(f"\t\t\t\t\tvar:zg361_p3_m{mid}_consumed_{name} = var:zg361_p3_m{mid}_write_{name}" for name in ("owner", "subject", "cycle", "case", "state"))
    business_projection = "\n".join(
        f"\t\tset_variable = {{ name = zg361_p3_m{mid}_visible_{source.removeprefix('zg361_p3_')} value = var:{source} }}"
        for source in projection
    )
    return f"""# #{mid:03d} read-side consumer; existence gates precede every tuple read.
zg361_p3_m{mid}_consume_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
{existence}
\t\t\t\t}}
{comparisons}
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{
{consumed_required}
\t\t\t\t\t}}
\t\t\t\t\tNOT = {{
{consumed_compare}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = yes }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
\t\tset_variable = {{ name = zg361_p3_m{mid}_consumed_owner value = var:zg361_p3_m{mid}_write_owner }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_consumed_subject value = var:zg361_p3_m{mid}_write_subject }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_consumed_cycle value = var:zg361_p3_m{mid}_write_cycle }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_consumed_case value = var:zg361_p3_m{mid}_write_case }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_consumed_state value = var:zg361_p3_m{mid}_write_state }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_visible_value value = var:zg361_p3_{spec.field} }}
\t\tset_variable = {{ name = zg361_p3_m{mid}_visible_provenance_case value = var:zg361_p3_m{mid}_write_case }}
{business_projection}
\t\tchange_variable = {{ name = zg361_p3_{d}_visible_revision add = 1 }}
\t}}
}}"""


def render_due_debt_consumer(spec: Mechanism) -> str:
    """Settle one exact debt once; classify every other pending state."""

    mid = spec.mid
    p = f"zg361_p3_m{mid}"
    identity = ("owner", "subject", "cycle", "case", "state")
    debt_fields = (*identity, "mechanism", "due_cycle", "status", "audit_state", "business_object_created")
    exact_required = "\n".join(f"\t\t\thas_variable = {p}_debt_{name}" for name in debt_fields)
    receipt_required = "\n".join(
        f"\t\t\thas_variable = {p}_receipt_{name}" for name in (*identity, "choice")
    )
    tuple_compare = "\n".join(
        f"\t\tvar:{p}_debt_{name} = var:{p}_receipt_{name}" for name in identity
    )
    future_required = exact_required.replace("\t\t\t", "\t\t\t")
    return f"""# #{mid:03d} next-cycle route-C debt consumer.  The exact frozen
# owner receives the KPI sink; every other pending state blocks new lifecycle work.
{p}_consume_due_debt_effect = {{
\tremove_variable = {p}_debt_expected_due_cycle
\tif = {{
\t\tlimit = {{ has_variable = {p}_debt_cycle }}
\t\tset_variable = {{ name = {p}_debt_expected_due_cycle value = var:{p}_debt_cycle }}
\t\tchange_variable = {{ name = {p}_debt_expected_due_cycle add = 1 }}
\t}}
\tif = {{
\t\tlimit = {{
{exact_required}
{receipt_required}
\t\t\thas_variable = {p}_debt_expected_due_cycle
\t\t\thas_variable = zg361_p3_policy_debt_open_n
\t\t\thas_variable = zg361_p3_policy_debt_settled_n
\t\t\troot = {{
\t\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\t\thas_variable = zg361_review_serial
\t\t\t}}
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = root
\t\t\tvar:{p}_debt_status = 1
\t\t\tvar:{p}_debt_audit_state = 1
\t\t\tvar:{p}_debt_business_object_created = 0
\t\t\tvar:{p}_debt_mechanism = {mid}
\t\t\tvar:zg361_p3_policy_debt_open_n >= 1
\t\t\tvar:{p}_debt_owner = root
\t\t\tvar:{p}_debt_subject = this
{tuple_compare}
\t\t\tvar:{p}_receipt_choice = 3
\t\t\tvar:{p}_debt_due_cycle = var:{p}_debt_expected_due_cycle
\t\t\troot.var:zg361_review_serial = var:{p}_debt_due_cycle
\t\t}}
\t\tvar:{p}_debt_owner = {{
\t\t\tchange_variable = {{ name = zg361_b2_management_debt add = 1 }}
\t\t}}
\t\tset_variable = {{ name = {p}_debt_status value = 2 }}
\t\tset_variable = {{ name = {p}_debt_audit_state value = 3 }}
\t\tset_variable = {{ name = {p}_debt_settled_by value = root }}
\t\tset_variable = {{ name = {p}_debt_settled_cycle value = root.var:zg361_review_serial }}
\t\tset_variable = {{ name = {p}_debt_performance_sink value = 1 }}
\t\tset_variable = {{ name = {p}_debt_consumer_status value = 1 }}
\t\tchange_variable = {{ name = zg361_p3_policy_debt_open_n add = -1 }}
\t\tchange_variable = {{ name = zg361_p3_policy_debt_settled_n add = 1 }}
\t}}
\telse_if = {{
\t\t# Exact settled replay is audit-only and never reaches the KPI sink again.
\t\tlimit = {{
\t\t\thas_variable = {p}_debt_owner
\t\t\thas_variable = {p}_debt_subject
\t\t\thas_variable = {p}_debt_status
\t\t\thas_variable = {p}_debt_audit_state
\t\t\thas_variable = {p}_debt_settled_by
\t\t\thas_variable = {p}_debt_settled_cycle
\t\t\troot = {{
\t\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\t\thas_variable = zg361_review_serial
\t\t\t}}
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = root
\t\t\tvar:{p}_debt_owner = root
\t\t\tvar:{p}_debt_subject = this
\t\t\tvar:{p}_debt_status = 2
\t\t\tvar:{p}_debt_audit_state = 3
\t\t\tvar:{p}_debt_settled_by = root
\t\t\troot.var:zg361_review_serial >= var:{p}_debt_settled_cycle
\t\t}}
\t\tset_variable = {{ name = {p}_debt_consumer_status value = 2 }}
\t}}
\telse_if = {{
\t\t# Complete exact input whose due cycle is later is future, never current work.
\t\tlimit = {{
{future_required}
{receipt_required}
\t\t\thas_variable = {p}_debt_expected_due_cycle
\t\t\troot = {{
\t\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\t\thas_variable = zg361_review_serial
\t\t\t}}
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = root
\t\t\tvar:{p}_debt_status = 1
\t\t\tvar:{p}_debt_audit_state = 1
\t\t\tvar:{p}_debt_business_object_created = 0
\t\t\tvar:{p}_debt_mechanism = {mid}
\t\t\tvar:{p}_debt_owner = root
\t\t\tvar:{p}_debt_subject = this
{tuple_compare}
\t\t\tvar:{p}_receipt_choice = 3
\t\t\tvar:{p}_debt_due_cycle = var:{p}_debt_expected_due_cycle
\t\t\troot.var:zg361_review_serial < var:{p}_debt_due_cycle
\t\t}}
\t\tset_variable = {{ name = {p}_debt_consumer_status value = 5 }}
\t\tset_variable = {{ name = zg361_p3_policy_debt_consumer_blocked value = 1 }}
\t}}
\telse_if = {{
\t\t# Pending stale/cross-owner/corrupt identity: fail closed.
\t\tlimit = {{
\t\t\tOR = {{
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{ has_variable = {p}_debt_status }}
\t\t\t\t\tvar:{p}_debt_status = 1
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{ has_variable = {p}_receipt_choice }}
\t\t\t\t\tvar:{p}_receipt_choice = 3
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {p}_debt_consumer_status value = 3 }}
\t\tset_variable = {{ name = zg361_p3_policy_debt_consumer_blocked value = 1 }}
\t\tset_variable = {{ name = zg361_p3_last_red_code value = {60000 + mid} }}
\t}}
}}"""


def render_due_debt_aggregate() -> str:
    calls = "\n".join(
        f"\tzg361_p3_m{spec.mid}_consume_due_debt_effect = yes"
        for spec in MECHANISMS
    )
    return f"""# The sole next-cycle debt route.  It is called once by the public
# portfolio adapter before a new AA case can overwrite any per-ID history.
zg361_p3_consume_due_policy_debts_effect = {{
\tremove_variable = zg361_p3_deferred_cleanup_due_cycle
\tif = {{
\t\tlimit = {{ has_variable = zg361_p3_portfolio_cycle }}
\t\tset_variable = {{ name = zg361_p3_deferred_cleanup_due_cycle value = var:zg361_p3_portfolio_cycle }}
\t\tchange_variable = {{ name = zg361_p3_deferred_cleanup_due_cycle add = 1 }}
\t}}
\tif = {{
\t\tlimit = {{ NOT = {{ has_variable = zg361_p3_policy_debt_open_n }} }}
\t\tset_variable = {{ name = zg361_p3_policy_debt_open_n value = 0 }}
\t}}
\tif = {{
\t\tlimit = {{ NOT = {{ has_variable = zg361_p3_policy_debt_settled_n }} }}
\t\tset_variable = {{ name = zg361_p3_policy_debt_settled_n value = 0 }}
\t}}
\tremove_variable = zg361_p3_policy_debt_consumer_blocked
{calls}
\tif = {{
\t\tlimit = {{ NOT = {{ has_variable = zg361_p3_policy_debt_consumer_blocked }} }}
\t\tzg361_p3_settle_deferred_portfolio_effect = yes
\t}}
}}"""


def render_deferred_portfolio_cleanup() -> str:
    """Release only AJ340 current-cycle reservation/WIP after all debts settle."""

    return """# Lifecycle cleanup is deliberately separate from route C and its
# same-cycle finalizer.  It releases only a prior AJ340 reservation/WIP after
# every exact C debt settled, with no blocked consumer and an exact due tuple.
zg361_p3_settle_deferred_portfolio_effect = {
	if = {
		limit = {
			has_variable = zg361_p3_portfolio_deferred
			has_variable = zg361_p3_deferred_cleanup_status
			has_variable = zg361_p3_policy_debt_open_n
			has_variable = zg361_p3_policy_debt_settled_n
			has_variable = zg361_p3_portfolio_closed
			has_variable = zg361_p3_portfolio_owner
			has_variable = zg361_p3_portfolio_subject
			has_variable = zg361_p3_portfolio_cycle
			has_variable = zg361_p3_deferred_cleanup_due_cycle
			has_variable = zg361_p3_final_owner
			has_variable = zg361_p3_final_subject
			has_variable = zg361_p3_final_cycle
			has_variable = zg361_p3_final_case
			has_variable = zg361_p3_final_deferred
			has_variable = zg361_p3_final_conservation_ok
			has_variable = zg361_p3_final_current_capacity_check
			has_variable = zg361_p3_aj_capacity_total
			has_variable = zg361_p3_aj_capacity_remaining
			has_variable = zg361_p3_aj_capacity_reserved
			has_variable = zg361_p3_aj_wip_used
			root = {
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
			}
			zg361_is_reviewable_vassal_trigger = yes
			liege = root
			var:zg361_p3_portfolio_deferred = 1
			var:zg361_p3_deferred_cleanup_status = 1
			var:zg361_p3_policy_debt_open_n = 0
			var:zg361_p3_policy_debt_settled_n >= 1
			var:zg361_p3_portfolio_closed = 1
			var:zg361_p3_portfolio_owner = root
			var:zg361_p3_portfolio_subject = this
			var:zg361_p3_final_owner = root
			var:zg361_p3_final_subject = this
			var:zg361_p3_final_cycle = var:zg361_p3_portfolio_cycle
			var:zg361_p3_final_deferred = 1
			var:zg361_p3_final_conservation_ok = 1
			var:zg361_p3_final_current_capacity_check = var:zg361_p3_aj_capacity_total
			root.var:zg361_review_serial = var:zg361_p3_deferred_cleanup_due_cycle
			trigger_if = {
				limit = {
					OR = {
						var:zg361_p3_aj_capacity_reserved > 0
						var:zg361_p3_aj_wip_used > 0
					}
				}
				has_variable = zg361_p3_demand_object_owner
				has_variable = zg361_p3_demand_object_subject
				has_variable = zg361_p3_demand_object_cycle
				has_variable = zg361_p3_demand_object_case
				has_variable = zg361_p3_delivery_object_owner
				has_variable = zg361_p3_delivery_object_subject
				has_variable = zg361_p3_delivery_object_cycle
				has_variable = zg361_p3_delivery_object_case
				has_variable = zg361_p3_demand_active
				has_variable = zg361_p3_demand_reserved_hours
				has_variable = zg361_p3_delivery_reserved_hours
				has_variable = zg361_p3_delivery_wip_slots
				var:zg361_p3_demand_object_owner = root
				var:zg361_p3_demand_object_subject = this
				var:zg361_p3_demand_object_cycle = var:zg361_p3_portfolio_cycle
				var:zg361_p3_demand_object_case = var:zg361_p3_final_case
				var:zg361_p3_delivery_object_owner = root
				var:zg361_p3_delivery_object_subject = this
				var:zg361_p3_delivery_object_cycle = var:zg361_p3_portfolio_cycle
				var:zg361_p3_delivery_object_case = var:zg361_p3_final_case
				var:zg361_p3_demand_active = 1
				var:zg361_p3_aj_capacity_reserved > 0
				var:zg361_p3_aj_wip_used > 0
				var:zg361_p3_demand_reserved_hours = var:zg361_p3_aj_capacity_reserved
				var:zg361_p3_delivery_wip_slots = var:zg361_p3_aj_wip_used
			}
			trigger_else = {
				var:zg361_p3_aj_capacity_reserved = 0
				var:zg361_p3_aj_wip_used = 0
			}
		}
		set_variable = { name = zg361_p3_deferred_cleanup_released_capacity value = var:zg361_p3_aj_capacity_reserved }
		set_variable = { name = zg361_p3_deferred_cleanup_released_wip value = var:zg361_p3_aj_wip_used }
		if = {
			limit = {
				var:zg361_p3_aj_capacity_reserved > 0
				var:zg361_p3_aj_wip_used > 0
			}
			change_variable = { name = zg361_p3_aj_capacity_remaining add = var:zg361_p3_aj_capacity_reserved }
			set_variable = { name = zg361_p3_aj_capacity_reserved value = 0 }
			set_variable = { name = zg361_p3_aj_wip_used value = 0 }
			set_variable = { name = zg361_p3_demand_reserved_hours value = 0 }
			set_variable = { name = zg361_p3_delivery_reserved_hours value = 0 }
			set_variable = { name = zg361_p3_delivery_wip_slots value = 0 }
			set_variable = { name = zg361_p3_demand_active value = 0 }
		}
		set_variable = { name = zg361_p3_deferred_cleanup_status value = 2 }
		set_variable = { name = zg361_p3_deferred_cleanup_settled_by value = root }
		set_variable = { name = zg361_p3_deferred_cleanup_settled_cycle value = root.var:zg361_review_serial }
	}
	else_if = {
		limit = {
			has_variable = zg361_p3_deferred_cleanup_status
			var:zg361_p3_deferred_cleanup_status = 1
		}
		set_variable = { name = zg361_p3_policy_debt_consumer_blocked value = 1 }
		set_variable = { name = zg361_p3_last_red_code value = 60999 }
	}
}"""


def final_domain_action(domain: str) -> str:
    next_domain = NEXT_DOMAIN[domain]
    if next_domain is not None:
        return f"""var:zg361_case_{domain}_owner = {{
\ttrigger_event = {{ id = zg361p3.{QUEUE_EVENTS[domain]} days = 1 }}
}}"""
    return "zg361_p3_finalize_portfolio_effect = yes"


def render_route_effect(spec: Mechanism, choice: int) -> str:
    mid, d = spec.mid, spec.domain
    letter = "abc"[choice - 1]
    guard = tuple_guard(spec)
    receipts = any_receipt(spec)
    checks = defer_precheck(spec) if choice == 3 else atomic_precheck(spec, choice)
    advance = ""
    if mid in STAGE_LAST[d]:
        barrier = stage_barrier(spec)
        edge = STAGE_LAST[d][mid]
        after = ""
        if edge == max(STAGE_LAST[d].values()):
            after = f"""
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\ttrigger_if = {{
\t\t\t\t\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\t\t\t\t\t\tvar:zg361_case_kernel_applied = 1
\t\t\t\t\t\t}}
\t\t\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t\t\t}}
{indent(final_domain_action(d), 5)}
\t\t\t\t}}"""
        advance = f"""
\t\t\tif = {{
\t\t\t\tlimit = {{
{indent(barrier, 5)}
\t\t\t\t}}
\t\t\t\tzg361_case_{d}_advance_{edge:02d}_effect = {{
\t\t\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\t\t}}{after}
\t\t\t}}
"""
    red_code = spec.mid * 10 + choice
    if choice == 3:
        applied_writes = f"""\t\t\tchange_variable = {{ name = zg361_p3_{d}_operation_used add = 1 }}
\t\t\tremove_variable = zg361_p3_m{mid}_debt_settled_by
\t\t\tremove_variable = zg361_p3_m{mid}_debt_settled_cycle
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_owner value = $TICKET_OWNER$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_subject value = $TICKET_SUBJECT$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_cycle value = $TICKET_CYCLE$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_case value = $TICKET_CASE$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_state value = {spec.state} }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_mechanism value = {mid} }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_due_cycle value = $TICKET_CYCLE$ }}
\t\t\tchange_variable = {{ name = zg361_p3_m{mid}_debt_due_cycle add = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_status value = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_audit_state value = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_business_object_created value = 0 }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_performance_sink value = 0 }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_debt_consumer_status value = 0 }}
\t\t\tset_variable = {{ name = zg361_p3_portfolio_deferred value = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_deferred_cleanup_status value = 1 }}
\t\t\tchange_variable = {{ name = zg361_p3_policy_debt_open_n add = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_runtime_status value = 1 }}
{advance.rstrip()}"""
        route_comment = "pure defer; no business object or resource write"
    else:
        business = "\n".join(business_effects(spec, choice))
        applied_writes = f"""{indent(business, 3)}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_write_owner value = $TICKET_OWNER$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_write_subject value = $TICKET_SUBJECT$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_write_cycle value = $TICKET_CYCLE$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_write_case value = $TICKET_CASE$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_write_state value = {spec.state} }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_provenance_case value = $TICKET_CASE$ }}
\t\t\tset_variable = {{ name = zg361_p3_m{mid}_provenance_choice value = {choice} }}
\t\t\tzg361_p3_m{mid}_consume_effect = yes
\t\t\tset_variable = {{ name = zg361_p3_runtime_status value = 1 }}
{advance.rstrip()}"""
        route_comment = "full guard + mutually exclusive receipt + atomic resource precheck"
    return f"""# #{mid:03d} route {letter.upper()}: {route_comment}.
zg361_p3_m{mid}_route_{letter}_effect = {{
\tremove_variable = zg361_p3_runtime_applied
\tremove_variable = zg361_p3_last_red_code
\tif = {{
\t\tlimit = {{
{indent(guard, 3)}
\t\t\tNOT = {{
{indent(receipts, 4)}
\t\t\t}}
{indent(checks, 3)}
\t\t}}
{indent(operation_call(spec, choice), 2)}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
\t\t\tset_variable = {{ name = zg361_p3_runtime_applied value = 1 }}
{applied_writes}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
\t\t\tNOT = {{
{indent(receipts, 4)}
\t\t\t}}
\t\t\tNOT = {{
{indent(checks, 4)}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_p3_last_red_code value = {red_code} }}
\t\tset_variable = {{ name = zg361_p3_runtime_status value = 4 }} # typed RED; no receipt/business/resource write
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
{indent(receipts, 3)}
\t\t}}
\t\tset_variable = {{ name = zg361_p3_runtime_status value = 2 }} # idempotent no-op
\t}}
\telse = {{ set_variable = {{ name = zg361_p3_runtime_status value = 3 }} }} # stale no-op
}}"""


def render_init(domain: str) -> str:
    specs = [spec for spec in MECHANISMS if spec.domain == domain]
    cleanup = []
    for spec in specs:
        cleanup.extend((
            f"remove_variable = zg361_p3_{spec.field}",
            f"remove_variable = zg361_p3_m{spec.mid}_visible_value",
        ))
    resource = {
        "aa": [
            "set_variable = { name = zg361_p3_aa_sample_total value = 1 }",
            "set_variable = { name = zg361_p3_aa_sample_used value = 0 }",
            "set_variable = { name = zg361_p3_aa_sample_queue value = 0 }",
        ],
        "ag": [
            "set_variable = { name = zg361_p3_ag_management_capacity_total value = 20 }",
            "set_variable = { name = zg361_p3_ag_management_capacity_remaining value = 20 }",
            "set_variable = { name = zg361_p3_ag_management_capacity_used value = 0 }",
            "set_variable = { name = zg361_p3_ag_visibility_debt value = 0 }",
            "set_variable = { name = zg361_p3_ag_hc_total value = 100 }",
            "set_variable = { name = zg361_p3_ag_manager_hc value = 20 }",
            "set_variable = { name = zg361_p3_ag_expert_hc value = 80 }",
        ],
        "aj": [
            "set_variable = { name = zg361_p3_aj_capacity_total value = 100 }",
            "set_variable = { name = zg361_p3_aj_capacity_remaining value = 100 }",
            "set_variable = { name = zg361_p3_aj_capacity_reserved value = 0 }",
            "set_variable = { name = zg361_p3_aj_next_capacity_total value = 100 }",
            "set_variable = { name = zg361_p3_aj_next_capacity_remaining value = 100 }",
            "set_variable = { name = zg361_p3_aj_next_capacity_reserved value = 0 }",
            "set_variable = { name = zg361_p3_aj_emergency_total value = 1 }",
            "set_variable = { name = zg361_p3_aj_emergency_used value = 0 }",
            "set_variable = { name = zg361_p3_aj_scope_traded value = 0 }",
            "set_variable = { name = zg361_p3_aj_queue_debt value = 0 }",
            "set_variable = { name = zg361_p3_aj_wip_limit value = 1 }",
            "set_variable = { name = zg361_p3_aj_wip_used value = 0 }",
            "set_variable = { name = zg361_p3_aj_wip_exception_count value = 0 }",
            "set_variable = { name = zg361_p3_aj_hidden_wip_debt value = 0 }",
            "set_variable = { name = zg361_p3_aj_disaster_waiver_used value = 0 }",
            "set_variable = { name = zg361_p3_aj_policy_debt value = 0 }",
            "set_variable = { name = zg361_p3_aj_value_credit_remaining value = 10000 }",
        ],
    }[domain]
    lines = [
        f"set_variable = {{ name = zg361_p3_{domain}_operation_total value = {DOMAIN_TOTALS[domain]} }}",
        f"set_variable = {{ name = zg361_p3_{domain}_operation_used value = 0 }}",
        f"set_variable = {{ name = zg361_p3_{domain}_quality value = 0 }}",
        f"set_variable = {{ name = zg361_p3_{domain}_throughput value = 0 }}",
        f"set_variable = {{ name = zg361_p3_{domain}_management_debt value = 0 }}",
        f"set_variable = {{ name = zg361_p3_{domain}_visible_revision value = 0 }}",
        *resource,
        *cleanup,
    ]
    return f"""zg361_p3_{domain}_initialize_effect = {{
{indent(chr(10).join(lines))}
}}"""


def render_subject_read(domain: str) -> str:
    return f"""# Assessed-only read adapter: counts/barons can consume their own active case,
# but this effect grants no open, stage, HC, calibration or allocation authority.
zg361_p3_{domain}_subject_read_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tzg361_case_kernel_subject_self_guard_trigger = {{
\t\t\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\t\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_p3_{domain}_subject_seen_revision value = var:zg361_p3_{domain}_visible_revision }}
\t}}
}}"""


def render_ai(domain: str) -> str:
    specs = by_id()
    calls = []
    for mid in DOMAIN_ORDER[domain]:
        spec = specs[mid]
        ticket = f"""TICKET_OWNER = scope:zg361_p3_{domain}_owner
TICKET_SUBJECT = scope:zg361_p3_{domain}_subject
TICKET_CYCLE = scope:zg361_p3_{domain}_cycle
TICKET_CASE = scope:zg361_p3_{domain}_case"""
        calls.append(f"""if = {{
\tlimit = {{
\t\thas_variable = zg361_p3_portfolio_deferred
\t\tvar:zg361_p3_portfolio_deferred = 1
\t}}
\tzg361_p3_m{mid}_route_c_effect = {{
{indent(ticket, 2)}
\t}}
}}
else = {{
\tzg361_p3_m{mid}_route_a_effect = {{
{indent(ticket, 2)}
\t}}
}}""")
    return f"""zg361_p3_{domain}_run_authorized_ai_effect = {{
\t# The project owner's second AI exception is background-only and still
\t# inherits the kernel's celestial, landed, duke+, alive and direct-liege gate.
\tif = {{
\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
{indent(chr(10).join(calls), 2)}
\t}}
}}"""


def render_portfolio_entries() -> str:
    return r'''# Freeze the institutional cycle and delivered result case once.  This is the
# only manager-scope ABI exposed to a future central dispatcher.
zg361_p3_initialize_portfolio_effect = {
	save_temporary_scope_as = zg361_p3_portfolio_subject_scope
	# Remove only the prior Phase3 projection.  The authoritative CP receipt
	# remains owned by the subject and is copied below only through a complete,
	# current owner/subject/cycle guard.
	remove_variable = zg361_p3_project_source_owner
	remove_variable = zg361_p3_project_source_subject
	remove_variable = zg361_p3_project_source_cycle
	remove_variable = zg361_p3_project_source_case
	remove_variable = zg361_p3_project_source_contribution_receipt_id
	remove_variable = zg361_p3_project_source_contribution_receipt_revision
	remove_variable = zg361_p3_project_source_contribution_value
	set_variable = { name = zg361_p3_project_source_ready value = 0 }
	set_variable = { name = zg361_p3_portfolio_subject value = this }
	set_variable = { name = zg361_p3_portfolio_cycle value = root.var:zg361_review_serial }
	root = { set_variable = { name = zg361_p3_manager_portfolio_cycle value = var:zg361_review_serial } }
	set_variable = { name = zg361_p3_portfolio_owner value = root }
	set_variable = { name = zg361_p3_portfolio_result_owner value = var:zg361_result_case_owner }
	set_variable = { name = zg361_p3_portfolio_result_subject value = this }
	set_variable = { name = zg361_p3_portfolio_result_cycle value = var:zg361_result_cycle_serial }
	set_variable = { name = zg361_p3_portfolio_result_case value = var:zg361_result_case_serial }
	set_variable = { name = zg361_p3_portfolio_result_state value = var:zg361_result_case_state }
	set_variable = { name = zg361_p3_portfolio_opened_domain value = 1 }
	set_variable = { name = zg361_p3_portfolio_closed value = 0 }
	set_variable = { name = zg361_p3_portfolio_deferred value = 0 }
	if = {
		limit = {
			has_variable = zg361_cp_m26_receipt_owner
			has_variable = zg361_cp_m26_receipt_subject
			has_variable = zg361_cp_m26_receipt_cycle
			has_variable = zg361_cp_m26_receipt_case
			has_variable = zg361_cp_m26_contribution_receipt_id
			has_variable = zg361_cp_m26_contribution_receipt_revision
			has_variable = zg361_cp_m26_visible_value
			var:zg361_cp_m26_receipt_owner = root
			var:zg361_cp_m26_receipt_subject = this
			var:zg361_cp_m26_receipt_cycle = root.var:zg361_review_serial
			var:zg361_cp_m26_contribution_receipt_id > 0
			var:zg361_cp_m26_contribution_receipt_revision > 0
		}
		set_variable = { name = zg361_p3_project_source_owner value = var:zg361_cp_m26_receipt_owner }
		set_variable = { name = zg361_p3_project_source_subject value = var:zg361_cp_m26_receipt_subject }
		set_variable = { name = zg361_p3_project_source_cycle value = var:zg361_cp_m26_receipt_cycle }
		set_variable = { name = zg361_p3_project_source_case value = var:zg361_cp_m26_receipt_case }
		set_variable = { name = zg361_p3_project_source_contribution_receipt_id value = var:zg361_cp_m26_contribution_receipt_id }
		set_variable = { name = zg361_p3_project_source_contribution_receipt_revision value = var:zg361_cp_m26_contribution_receipt_revision }
		set_variable = { name = zg361_p3_project_source_contribution_value value = var:zg361_cp_m26_visible_value }
		set_variable = { name = zg361_p3_project_source_ready value = 1 }
	}
	if = {
		limit = { NOT = { has_variable = zg361_p3_policy_debt_open_n } }
		set_variable = { name = zg361_p3_policy_debt_open_n value = 0 }
	}
	if = {
		limit = { NOT = { has_variable = zg361_p3_policy_debt_settled_n } }
		set_variable = { name = zg361_p3_policy_debt_settled_n value = 0 }
	}
	set_variable = { name = zg361_p3_cross_reviewer value = root }
	set_variable = { name = zg361_p3_cross_reviewer_valid value = 0 }
	root = {
		if = {
			limit = { exists = liege liege = { zg361_is_celestial_liege_trigger = yes } }
			liege = { save_temporary_scope_as = zg361_p3_cross_candidate }
			scope:zg361_p3_portfolio_subject_scope = {
				set_variable = { name = zg361_p3_cross_reviewer value = scope:zg361_p3_cross_candidate }
				set_variable = { name = zg361_p3_cross_reviewer_valid value = 1 }
			}
		}
		ordered_vassal = {
			limit = {
				zg361_is_reviewable_vassal_trigger = yes
				NOT = { this = scope:zg361_p3_portfolio_subject_scope }
			}
			order_by = stewardship
			position = 0
			save_temporary_scope_as = zg361_p3_cross_candidate
			scope:zg361_p3_portfolio_subject_scope = {
				set_variable = { name = zg361_p3_cross_reviewer value = scope:zg361_p3_cross_candidate }
				set_variable = { name = zg361_p3_cross_reviewer_valid value = 1 }
			}
		}
	}
}

# Public manager-scope portfolio adapter. Counts/barons may be $SUBJECT$, never
# the manager ROOT. Replay in the same frozen review cycle is a strict no-op.
zg361_p3_open_portfolio_effect = {
	# The package-owned due pass always runs before any new portfolio state can
	# overwrite debt receipts.  A blocked or nonzero-open result forbids launch.
	$SUBJECT$ = { zg361_p3_consume_due_policy_debts_effect = yes }
	if = {
		limit = {
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			has_variable = zg361_review_serial
			OR = {
				any_vassal = {
					zg361_is_reviewable_vassal_trigger = yes
					NOT = { this = $SUBJECT$ }
				}
				liege = { zg361_is_celestial_liege_trigger = yes }
			}
			trigger_if = {
				limit = { has_variable = zg361_p3_manager_portfolio_cycle }
				NOT = { var:zg361_p3_manager_portfolio_cycle = var:zg361_review_serial }
			}
			trigger_else = { always = yes }
			$SUBJECT$ = {
				NOT = { has_variable = zg361_p3_policy_debt_consumer_blocked }
				has_variable = zg361_p3_policy_debt_open_n
				var:zg361_p3_policy_debt_open_n = 0
				zg361_is_reviewable_vassal_trigger = yes
				liege = root
				trigger_if = {
					limit = {
						has_variable = zg361_result_case_owner
						has_variable = zg361_result_cycle_serial
						has_variable = zg361_result_case_serial
						has_variable = zg361_result_case_state
						root = { has_variable = zg361_review_serial }
					}
					var:zg361_result_case_owner = root
					var:zg361_result_cycle_serial = root.var:zg361_review_serial
					var:zg361_result_case_state >= 3
				}
				trigger_else = { always = no }
				trigger_if = {
					limit = { has_variable = zg361_p3_portfolio_cycle }
					NOT = { var:zg361_p3_portfolio_cycle = root.var:zg361_review_serial }
				}
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_aa_active } var:zg361_case_aa_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_ag_active } var:zg361_case_ag_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_aj_active } var:zg361_case_aj_active = 0 }
				trigger_else = { always = yes }
			}
		}
		# The adapter opens only AA.  AG and AJ are reachable solely through the
		# frozen D+1 queue edges emitted after their predecessor closes.
		$SUBJECT$ = {
			zg361_p3_aa_launch_effect = yes
		}
	}
}

zg361_p3_finalize_portfolio_effect = {
	set_variable = { name = zg361_p3_portfolio_closed value = 1 }
	set_variable = { name = zg361_p3_portfolio_opened_domain value = 3 }
	set_variable = { name = zg361_p3_final_owner value = var:zg361_case_aj_owner }
	set_variable = { name = zg361_p3_final_subject value = var:zg361_case_aj_subject }
	set_variable = { name = zg361_p3_final_cycle value = var:zg361_case_aj_cycle_serial }
	set_variable = { name = zg361_p3_final_case value = var:zg361_case_aj_case_serial }
	set_variable = { name = zg361_p3_final_state value = var:zg361_case_aj_state }
	set_variable = { name = zg361_p3_final_current_capacity_check value = { value = var:zg361_p3_aj_capacity_remaining add = var:zg361_p3_aj_capacity_reserved } }
	set_variable = { name = zg361_p3_final_wip_outstanding value = var:zg361_p3_aj_wip_used }
	set_variable = { name = zg361_p3_final_wip_limit_check value = { value = var:zg361_p3_aj_wip_limit add = var:zg361_p3_aj_wip_exception_count } }
	set_variable = { name = zg361_p3_final_conservation_ok value = 0 }
	set_variable = { name = zg361_p3_final_deferred value = 0 }
	if = {
		limit = {
			trigger_if = {
				limit = {
					has_variable = zg361_p3_aa_operation_used
					has_variable = zg361_p3_ag_operation_used
					has_variable = zg361_p3_aj_operation_used
					has_variable = zg361_case_aa_active
					has_variable = zg361_case_ag_active
					has_variable = zg361_case_aj_active
					has_variable = zg361_p3_aa_sample_used
					has_variable = zg361_p3_aa_sample_total
					has_variable = zg361_p3_ag_hc_total
					has_variable = zg361_p3_ag_management_capacity_used
					has_variable = zg361_p3_ag_management_capacity_total
					has_variable = zg361_p3_portfolio_deferred
					has_variable = zg361_p3_policy_debt_open_n
					has_variable = zg361_p3_aj_capacity_total
					has_variable = zg361_p3_aj_capacity_remaining
					has_variable = zg361_p3_aj_capacity_reserved
					has_variable = zg361_p3_aj_wip_used
					has_variable = zg361_p3_aj_wip_limit
					has_variable = zg361_p3_aj_wip_exception_count
					has_variable = zg361_p3_m344_receipt_choice
				}
				var:zg361_p3_aa_operation_used = 13
				var:zg361_p3_ag_operation_used = 11
				var:zg361_p3_aj_operation_used = 11
				var:zg361_case_aa_active = 0
				var:zg361_case_ag_active = 0
				var:zg361_case_aj_active = 0
				var:zg361_p3_aa_sample_used <= var:zg361_p3_aa_sample_total
				var:zg361_p3_ag_hc_total = 100
				var:zg361_p3_ag_management_capacity_used <= var:zg361_p3_ag_management_capacity_total
				trigger_if = {
					limit = { var:zg361_p3_portfolio_deferred = 1 }
					has_variable = zg361_p3_deferred_cleanup_status
					var:zg361_p3_deferred_cleanup_status = 1
					var:zg361_p3_policy_debt_open_n >= 1
					var:zg361_p3_final_current_capacity_check = var:zg361_p3_aj_capacity_total
					var:zg361_p3_aj_wip_used <= var:zg361_p3_final_wip_limit_check
					var:zg361_p3_m344_receipt_choice = 3
					OR = {
						AND = {
							var:zg361_p3_aj_capacity_reserved = 0
							var:zg361_p3_aj_wip_used = 0
						}
						AND = {
							var:zg361_p3_aj_capacity_reserved > 0
							var:zg361_p3_aj_wip_used > 0
						}
					}
				}
				trigger_else = {
					var:zg361_p3_portfolio_deferred = 0
					var:zg361_p3_policy_debt_open_n = 0
					var:zg361_p3_aj_capacity_reserved = 0
					var:zg361_p3_aj_wip_used = 0
					trigger_if = {
						limit = { has_variable = zg361_p3_m344_ledger_total }
						var:zg361_p3_m344_ledger_total = 10000
					}
					trigger_else = { always = no }
				}
			}
			trigger_else = { always = no }
		}
		if = {
			limit = { var:zg361_p3_portfolio_deferred = 1 }
			set_variable = { name = zg361_p3_final_deferred value = 1 }
		}
		set_variable = { name = zg361_p3_final_conservation_ok value = 1 }
	}
	debug_log = "ZG361P3: metrics/delivery portfolio closed static runtime"
}'''


def render_launch(domain: str) -> str:
    first = DOMAIN_ORDER[domain][0]
    portfolio_init = "\n\t\tzg361_p3_initialize_portfolio_effect = yes" if domain == "aa" else ""
    return f"""# Internal domain entry. Call in assessed-subject scope with ROOT = frozen manager.
zg361_p3_{domain}_launch_effect = {{
\tremove_variable = zg361_p3_runtime_applied
\tzg361_case_{domain}_open_effect = yes
\tif = {{
\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
{portfolio_init}
\t\tzg361_p3_{domain}_initialize_effect = yes
\t\tvar:zg361_case_{domain}_owner = {{ save_scope_as = zg361_p3_{domain}_owner }}
\t\tsave_scope_as = zg361_p3_{domain}_subject
\t\tsave_scope_value_as = {{ name = zg361_p3_{domain}_cycle value = var:zg361_case_{domain}_cycle_serial }}
\t\tsave_scope_value_as = {{ name = zg361_p3_{domain}_case value = var:zg361_case_{domain}_case_serial }}
\t\tif = {{
\t\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tzg361_p3_{domain}_run_authorized_ai_effect = yes
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ root = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tscope:zg361_p3_{domain}_owner = {{ trigger_event = {{ id = zg361p3.{first} }} }}
\t\t}}
\t}}
}}"""


def render_effects() -> bytes:
    """Render the frozen pre-shard monolith for semantic comparison only."""

    validate_specs()
    sections = [
        "# ZhongGuo 361 phase 3 — AA metrics, AG reorg, AJ demand delivery.\n"
        f"# READINESS: {READINESS}. No CK3 parser/paused/live evidence is claimed.\n"
        "# Public entry: zg361_p3_open_portfolio_effect = { SUBJECT = <direct assessed vassal> }.\n"
        "# Stable status: 1=applied, 2=idempotent no-op, 3=stale no-op, 4=typed RED.\n",
        render_portfolio_entries(),
        render_due_debt_aggregate(),
        render_deferred_portfolio_cleanup(),
    ]
    for domain in ("aa", "ag", "aj"):
        sections += [render_init(domain), render_subject_read(domain), render_ai(domain), render_launch(domain)]
    for spec in MECHANISMS:
        sections.append(render_due_debt_consumer(spec))
        sections.append(render_consumer(spec))
        for choice in (1, 2, 3):
            sections.append(render_route_effect(spec, choice))
    return generated("\n\n".join(sections))


def _top_level_effect_blocks(source: str) -> tuple[tuple[str, str], ...]:
    """Return top-level effect blocks in source order, preserving their bytes."""

    blocks: list[tuple[str, str]] = []
    pattern = re.compile(r"(?m)^([a-z0-9_]+_effect)\s*=\s*\{")
    for match in pattern.finditer(source):
        depth = 0
        quoted = False
        escaped = False
        commented = False
        for index in range(match.end() - 1, len(source)):
            char = source[index]
            if char == "\n":
                commented = False
                continue
            if commented:
                continue
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == "#":
                commented = True
            elif char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(
                        (match.group(1), source[match.start() : index + 1])
                    )
                    break
        else:
            raise ValueError(f"unterminated phase-3 effect block: {match.group(1)}")
    return tuple(blocks)


def render_effect_parts() -> dict[str, bytes]:
    """Render purpose shards without changing any top-level effect block."""

    historical = render_effects().decode("utf-8-sig")
    historical_blocks = _top_level_effect_blocks(historical)
    historical_names = tuple(name for name, _block in historical_blocks)
    block_by_name = dict(historical_blocks)
    configured_names = tuple(
        name for _filename, names in EFFECT_GROUPS for name in names
    )

    if len(EFFECT_GROUPS) != 40:
        raise ValueError("phase-3 runtime must remain split into 40 purpose files")
    if len(historical_names) != 192 or len(set(historical_names)) != 192:
        raise ValueError("phase-3 historical render must contain 192 unique effects")
    if len(configured_names) != 192 or len(set(configured_names)) != 192:
        raise ValueError("phase-3 purpose map must contain 192 unique effects")
    if set(configured_names) != set(historical_names):
        missing = sorted(set(historical_names) - set(configured_names))
        extra = sorted(set(configured_names) - set(historical_names))
        raise ValueError(
            "phase-3 purpose map mismatch: "
            f"missing={missing}, extra={extra}"
        )

    rendered: dict[str, bytes] = {}
    for filename, names in EFFECT_GROUPS:
        if not names:
            raise ValueError(
                f"phase-3 purpose file must contain at least one effect: {filename}"
            )
        if len(names) > EFFECT_HARD_MAX:
            exception = EFFECT_HARD_LIMIT_EXCEPTIONS.get(filename)
            if (
                exception is None
                or len(exception) != 2
                or not exception[0].strip()
                or not exception[1].strip()
            ):
                raise ValueError(
                    "phase-3 purpose file exceeds "
                    f"{EFFECT_HARD_MAX} effects without a reason and CK3 "
                    f"live-evidence reference: {filename}"
                )
        body = "\n\n".join(block_by_name[name] for name in names)
        rendered[filename] = generated(
            f"# Phase-3 purpose shard: {filename}\n"
            f"# READINESS: {READINESS}. No CK3 parser/paused/live evidence is claimed.\n\n"
            f"{body}"
        )

    exception_files = set(EFFECT_HARD_LIMIT_EXCEPTIONS)
    oversized_files = {
        filename
        for filename, names in EFFECT_GROUPS
        if len(names) > EFFECT_HARD_MAX
    }
    if exception_files != oversized_files:
        raise ValueError(
            "phase-3 hard-limit exceptions must exactly match oversized shards: "
            f"exceptions={sorted(exception_files)}, "
            f"oversized={sorted(oversized_files)}"
        )
    return rendered


def event_guard(spec: Mechanism) -> str:
    d = spec.domain
    return f"""is_ai = no
exists = scope:zg361_p3_{d}_owner
exists = scope:zg361_p3_{d}_subject
exists = scope:zg361_p3_{d}_cycle
exists = scope:zg361_p3_{d}_case
this = scope:zg361_p3_{d}_owner
scope:zg361_p3_{d}_subject = {{
\tzg361_case_kernel_full_guard_trigger = {{
\t\tOWNER_VAR = zg361_case_{d}_owner
\t\tSUBJECT_VAR = zg361_case_{d}_subject
\t\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\t\tCASE_VAR = zg361_case_{d}_case_serial
\t\tSTATE_VAR = zg361_case_{d}_state
\t\tACTIVE_VAR = zg361_case_{d}_active
\t\tEXPECTED_OWNER = scope:zg361_p3_{d}_owner
\t\tEXPECTED_SUBJECT = scope:zg361_p3_{d}_subject
\t\tEXPECTED_CYCLE = scope:zg361_p3_{d}_cycle
\t\tEXPECTED_CASE = scope:zg361_p3_{d}_case
\t\tEXPECTED_STATE = {spec.state}
\t}}
}}"""


def render_option(spec: Mechanism, choice: int, next_mid: int | None) -> str:
    d, mid = spec.domain, spec.mid
    letter = "abc"[choice - 1]
    next_event = ""
    if next_mid is not None:
        next_event = f"""
\tif = {{
\t\tlimit = {{ scope:zg361_p3_{d}_subject = {{ has_variable = zg361_p3_runtime_applied var:zg361_p3_runtime_applied = 1 }} }}
\t\ttrigger_event = {{ id = zg361p3.{next_mid} days = 1 }}
\t}}"""
    return f"""option = {{
\tname = zg361p3.{mid}.{letter}
\tscope:zg361_p3_{d}_subject = {{
\t\tzg361_p3_m{mid}_route_{letter}_effect = {{
\t\t\tTICKET_OWNER = scope:zg361_p3_{d}_owner
\t\t\tTICKET_SUBJECT = scope:zg361_p3_{d}_subject
\t\t\tTICKET_CYCLE = scope:zg361_p3_{d}_cycle
\t\t\tTICKET_CASE = scope:zg361_p3_{d}_case
\t\t}}
\t}}{next_event}
}}"""


def render_queue_event(domain: str) -> str:
    next_domain = NEXT_DOMAIN[domain]
    if next_domain is None:
        raise ValueError("the final AJ domain has no queue event")
    event_id = QUEUE_EVENTS[domain]
    final_state = max(STAGE_LAST[domain].values()) + 1
    opened_domain = ("aa", "ag", "aj").index(next_domain) + 1
    return f"""# Hidden D+1 edge: closed {domain.upper()} -> first {next_domain.upper()} case.
zg361p3.{event_id} = {{
\ttype = character_event
\thidden = yes
\ttrigger = {{
\t\texists = scope:zg361_p3_{domain}_owner
\t\texists = scope:zg361_p3_{domain}_subject
\t\texists = scope:zg361_p3_{domain}_cycle
\t\texists = scope:zg361_p3_{domain}_case
\t\tthis = scope:zg361_p3_{domain}_owner
\t\tzg361_is_celestial_liege_trigger = yes
\t\ttrigger_if = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = zg361_review_serial
\t\t\t\thas_variable = zg361_p3_manager_portfolio_cycle
\t\t\t}}
\t\t\tvar:zg361_p3_manager_portfolio_cycle = var:zg361_review_serial
\t\t}}
\t\ttrigger_else = {{ always = no }}
\t\tscope:zg361_p3_{domain}_subject = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
\t\t\t\t\thas_variable = zg361_case_{domain}_owner
\t\t\t\t\thas_variable = zg361_case_{domain}_subject
\t\t\t\t\thas_variable = zg361_case_{domain}_cycle_serial
\t\t\t\t\thas_variable = zg361_case_{domain}_case_serial
\t\t\t\t\thas_variable = zg361_case_{domain}_state
\t\t\t\t\thas_variable = zg361_case_{domain}_active
\t\t\t\t\thas_variable = zg361_p3_portfolio_owner
\t\t\t\t\thas_variable = zg361_p3_portfolio_subject
\t\t\t\t\thas_variable = zg361_p3_portfolio_cycle
\t\t\t\t\thas_variable = zg361_p3_portfolio_result_owner
\t\t\t\t\thas_variable = zg361_p3_portfolio_result_subject
\t\t\t\t\thas_variable = zg361_p3_portfolio_result_cycle
\t\t\t\t\thas_variable = zg361_p3_portfolio_result_case
\t\t\t\t\thas_variable = zg361_p3_portfolio_result_state
\t\t\t\t\thas_variable = zg361_p3_portfolio_opened_domain
\t\t\t\t\thas_variable = zg361_p3_portfolio_closed
\t\t\t\t\thas_variable = zg361_result_case_owner
\t\t\t\t\thas_variable = zg361_result_cycle_serial
\t\t\t\t\thas_variable = zg361_result_case_serial
\t\t\t\t\thas_variable = zg361_result_case_state
\t\t\t\t}}
\t\t\t\tvar:zg361_case_{domain}_owner = scope:zg361_p3_{domain}_owner
\t\t\t\tvar:zg361_case_{domain}_subject = scope:zg361_p3_{domain}_subject
\t\t\t\tvar:zg361_case_{domain}_cycle_serial = scope:zg361_p3_{domain}_cycle
\t\t\t\tvar:zg361_case_{domain}_case_serial = scope:zg361_p3_{domain}_case
\t\t\t\tvar:zg361_case_{domain}_state = {final_state}
\t\t\t\tvar:zg361_case_{domain}_active = 0
\t\t\t\tvar:zg361_p3_portfolio_owner = scope:zg361_p3_{domain}_owner
\t\t\t\tvar:zg361_p3_portfolio_subject = scope:zg361_p3_{domain}_subject
\t\t\t\tvar:zg361_p3_portfolio_cycle = root.var:zg361_review_serial
\t\t\t\tvar:zg361_p3_portfolio_result_owner = var:zg361_result_case_owner
\t\t\t\tvar:zg361_p3_portfolio_result_subject = scope:zg361_p3_{domain}_subject
\t\t\t\tvar:zg361_p3_portfolio_result_cycle = var:zg361_result_cycle_serial
\t\t\t\tvar:zg361_p3_portfolio_result_case = var:zg361_result_case_serial
\t\t\t\tvar:zg361_p3_portfolio_result_state = var:zg361_result_case_state
\t\t\t\tvar:zg361_p3_portfolio_opened_domain = {opened_domain - 1}
\t\t\t\tvar:zg361_p3_portfolio_closed = 0
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
\t}}
\timmediate = {{
\t\tscope:zg361_p3_{domain}_subject = {{
\t\t\tset_variable = {{ name = zg361_p3_portfolio_opened_domain value = {opened_domain} }}
\t\t\tzg361_p3_{next_domain}_launch_effect = yes
\t\t}}
\t}}
}}"""


def render_events() -> bytes:
    validate_specs()
    specs = by_id()
    events = ["namespace = zg361p3"]
    for domain in ("aa", "ag", "aj"):
        order = DOMAIN_ORDER[domain]
        for index, mid in enumerate(order):
            spec = specs[mid]
            next_mid = order[index + 1] if index + 1 < len(order) else None
            options = "\n".join(render_option(spec, choice, next_mid) for choice in (1, 2, 3))
            events.append(f"""# #{mid:03d} — {spec.title_en}
zg361p3.{mid} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = zg361p3.{mid}.t
\tdesc = zg361p3.{mid}.desc
\ttrigger = {{
{indent(event_guard(spec), 2)}
\t}}
{indent(options)}
}}""")
    events.extend(render_queue_event(domain) for domain in ("aa", "ag"))
    return generated("\n\n".join(events))


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    validate_specs()
    if language == "simp_chinese":
        header = "l_simp_chinese:"
        rows = []
        for spec in MECHANISMS:
            rows += [
                f' zg361p3.{spec.mid}.t:0 "{esc(spec.title_cn)}"',
                f' zg361p3.{spec.mid}.desc:0 "{esc(spec.desc_cn)}"',
                *(f' zg361p3.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", spec.routes_cn)),
            ]
    else:
        header = f"l_{language}:"
        rows = []
        for spec in MECHANISMS:
            rows += [
                f' zg361p3.{spec.mid}.t:0 "{esc(spec.title_en)}"',
                f' zg361p3.{spec.mid}.desc:0 "{esc(spec.desc_en)}"',
                *(f' zg361p3.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", spec.routes_en)),
            ]
    return localized(header + "\n" + "\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    rendered = {
        MOD_ROOT / "events" / "zg361_phase3_metrics_delivery_runtime_events.txt": render_events(),
    }
    rendered.update(
        {
            effects_dir / filename: payload
            for filename, payload in render_effect_parts().items()
        }
    )
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_phase3_metrics_delivery_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    expected_effect_paths = {
        path for path in rendered if path.parent == effects_dir
    }
    effect_residue = sorted(
        path
        for path in effects_dir.glob("zg361_phase3_*_effects.txt")
        if path not in expected_effect_paths
    )
    if args.check:
        if stale or effect_residue:
            print("RED: stale phase-3 metrics/delivery generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            for path in effect_residue:
                label = (
                    "legacy monolith"
                    if path.name == LEGACY_EFFECT_FILENAME
                    else "unexpected generated effect residue"
                )
                print(f"{path.relative_to(MOD_ROOT)} ({label})")
            return 1
        print(f"GREEN: {len(rendered)} generated files are current ({READINESS})")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    for path in effect_residue:
        path.unlink()
    print(f"GREEN: generated {len(rendered)} phase-3 metrics/delivery runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
