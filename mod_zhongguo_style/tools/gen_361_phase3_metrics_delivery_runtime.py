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

from zg361_localization_style import normalize_localization_rows


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_phase3_metrics_delivery_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
DEFER_ROUTE_EN = "Close this item and record policy debt."
DEFER_ROUTE_CN = "关闭本项，登记制度债。"
DEFER_TOOLTIP_EN = "No business action is taken. One next-cycle policy debt is recorded, and this item will not be proposed again automatically."
DEFER_TOOLTIP_CN = "不执行业务动作；登记一笔下周期制度债。本项不会自动重提。"
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
        mid, domain, state, field, title_en, title_cn,
        desc_en,
        desc_cn,
        # Runtime authority is uniform: legacy per-item C copy remains only as
        # research context; generated player copy is canonical policy.defer.
        (a_en, b_en, DEFER_ROUTE_EN), (a_cn, b_cn, DEFER_ROUTE_CN),
    )


MECHANISMS = (
    m(229, "aa", 1, "metric_dictionary_owner", "Who Owns the Metric Dictionary?", "指标字典归谁管",
      "The metric has no named owner, and later changes have no accountable signer. Two readings of the same number are already circulating.",
      "这项指标没有具名口径责任人，后续改动也无人签认；同一个数字已经流传出两种解释。",
      "Name one accountable owner.", "Require owner and steward co-signature.", "Let the committee own it collectively.",
      "指定受评者为唯一口径责任人，并由直属上司共同维护。", "指定直属上司为口径责任人，并由数据管家共同维护；登记一笔口径债。", "交给委员会集体负责。"),
    m(230, "aa", 1, "reconciliation_basis", "Two Dashboards, One Number", "两张看板，一个数字",
      "Two sources disagree. The review needs a recorded reconciliation rule, not whichever screenshot looks kinder.",
      "两套数据源打起来了。考核需要一条可追溯的对账规则，而不是挑那张更好看的截图。",
      "Use the named authoritative source.", "Reconcile jointly and publish the delta.", "Defer the metric and record uncertainty.",
      "采用预先指定的权威源。", "联合对账并公开差额。", "暂缓该指标并记录不确定性。"),
    m(231, "aa", 2, "denominator_policy", "The Denominator Moved", "分母怎么又变了",
      "A changed denominator has produced two incompatible results for the same period. The file does not yet say which version governs calibration.",
      "分母变更后，同一周期出现了两份互不相容的结果；案卷还没有说明校准应以哪一版为准。",
      "Restate both periods on the new denominator.", "Keep both versions side by side.", "Use the old denominator for this cycle.",
      "按新分母重算两个时期。", "新旧口径并列展示。", "本周期继续沿用旧分母。"),
    m(232, "aa", 2, "backfill_policy", "The Spreadsheet Has a Hole", "表里少了一块",
      "One section of the table is empty. The file contains neither a visible backfill rule nor anyone accountable for estimation error.",
      "表中有一段数据空缺；案卷里既没有公开回填规则，也没有人为估算误差负责。",
      "Backfill with audit samples.", "Impute and show an uncertainty band.", "Leave the gap visible.",
      "用审计样本回填全部十个缺失单元，并由独立复核人批准。", "插补其中八个缺失单元，展示误差带，并由独立复核人批准。", "保留缺口，不假装完整。"),
    m(233, "aa", 2, "visibility_level", "Who May See the Dashboard?", "谁能看见这张看板",
      "The assessed official can see only a summary score. The underlying detail and a query route are both missing from the file.",
      "受评者目前只能看见汇总分；底层明细和可查询路径都还没有写进案卷。",
      "Open the full dashboard.", "Expose role-bounded detail and a query channel.", "Expose only the signed summary.",
      "开放完整看板。", "按职责开放明细，并保留查询通道。", "只开放签字后的摘要。"),
    m(234, "aa", 3, "signal_split", "Leading Signals, Lagging Results", "领先指标与滞后结果",
      "Effort signals and eventual outcomes currently share one ledger, allowing a late result to rewrite work that was already observed.",
      "过程信号与最终结果目前挤在同一本账里，迟到的结果因此能倒改早已发生的工作。",
      "Weight leading signals first.", "Balance signals and outcomes.", "Weight verified outcomes first.",
      "按领先信号六成、滞后结果四成结算。", "按领先信号与滞后结果各五成结算，并进入校准。", "已验证结果优先。"),
    m(235, "aa", 3, "guardrail_split", "A KPI Needs Guardrails", "主指标也得系安全带",
      "The primary metric has risen while its quality guardrail has fallen. Their relative weight is absent from the settlement file.",
      "主指标已经上涨，质量护栏却同步下跌；结算案卷里还没有两者的相对权重。",
      "Give guardrails equal weight.", "Keep a sixty-forty balance.", "Permit a narrow primary-metric bias.",
      "按主指标与质量护栏各五成结算；护栏失守时不得获最高功劳。", "按主指标六成、质量护栏四成结算；由责任人承担护栏失守。", "允许有限度偏向主指标。"),
    m(236, "aa", 3, "scoring_curve", "The KPI Cliff", "KPI 悬崖",
      "The current scoring rule drops from full credit to zero at one threshold. A tiny measurement change can erase a full cycle of work.",
      "现行规则在一道阈值上从满分骤降为零，极小的测量变化就可能抹掉整周期工作。",
      "Use continuous scoring so near-threshold results do not collapse to zero.", "Keep a threshold but award partial credit based on proximity.", "Keep the hard cliff and accept its risk.",
      "改用连续计分，避免阈值附近的成绩骤然归零。", "保留达标阈值，但按接近程度给予部分得分。", "保留硬悬崖并承担风险。"),
    m(237, "aa", 3, "window_audit", "The Most Beautiful Time Window", "截最美的一段",
      "The submitted chart shows only its most favorable interval. Neither the full observation window nor the comparison period appears in the file.",
      "上报图表只截取了最有利的一段；完整观察窗与对照期都没有出现在案卷里。",
      "Use the full 365-day window recorded before the review began.", "Publish full and selected windows together.", "Allow the slice but flag it for audit.",
      "按考核开始前事先登记的三百六十五日完整时间窗结算。", "并列公开三百六十五日完整窗与九十日精选窗。", "允许截取，但挂上审计标记。"),
    m(240, "aa", 4, "sample_route", "Everyone Wants the Same Sample", "大家都想抢这批样本",
      "The same assessed officials appear in two experiment files. Both teams claim an uncontaminated sample, so the same people are being counted twice.",
      "同一批受评者同时出现在两份实验案卷中；两支团队都声称拿到了未受干扰的样本，因而重复计入了同一批人。",
      "Assign this sample exclusively to the current experiment.", "Have an independent reviewer sign off and divide the sample between both experiments.", "Queue the test and record no clean claim.",
      "将这批样本独占分配给当前实验。", "由独立复核人签字，将样本划分给两项实验。", "排队等待，不声称纯净实验。"),
    m(238, "aa", 5, "vanity_value_split", "Vanity Is Not Value", "热闹不等于价值",
      "Traffic has risen while verified value remains flat. The louder adoption chart is currently crowding out the value ledger.",
      "采用数据十分热闹，验证价值却原地踏步；声量更大的图表正在挤掉价值账。",
      "Weight verified value heavily.", "Balance adoption and value.", "Credit reach first but retain value debt.",
      "按声量一成、已验证价值七成、未验证两成结算；追回一成功劳。", "按声量三成、已验证价值五成、未验证两成结算；追回三成功劳。", "先认覆盖面，但保留价值债。"),
    m(239, "aa", 5, "learning_credit", "A Failed Experiment Still Learned", "实验失败，学习不能归零",
      "The experiment followed rules recorded in advance and missed its business target, but it left verifiable new knowledge. The dispute is how much bounded credit that evidence deserves.",
      "实验规则已在开始前登记，实验虽未达到业务目标，却留下了可验证的新知识；争议在于这些学习证据应获得多少有界权重。",
      "Credit verified learning strongly.", "Split credit between learning and delivery.", "Record learning without score credit.",
      "给事先登记且可复核、可复用的学习证据七成功劳；业务交付仍记失败。", "给学习证据四成功劳，并与失败的业务交付分账。", "只入知识库，不计绩效分。"),
    m(241, "aa", 6, "long_tail_attribution", "Who Owns the Long Tail?", "长尾效果算谁的",
      "The team has dispersed, but its impact is still arriving. No attribution shares govern the value that appears after handoff.",
      "团队已经散场，长期效果却还在出现；交接后的新增价值目前没有归属份额可依。",
      "Credit the builder most.", "Split builder, operator and successor evenly.", "Credit the long-term operator most.",
      "按建设者五成、运营者三成、继任者两成分配长尾功劳与成本。", "按建设者三成三、运营者三成三、继任者三成四分配长尾功劳与成本。", "长期运营者拿大头。"),

    m(301, "ag", 1, "halo_normalization", "The Core-Business Halo", "核心业务光环",
      "The team inherited strong momentum, but the assessment file currently credits all of it as controllable personal contribution.",
      "团队继承了强劲势能，考核案卷却把它全部记成了个人可控贡献。",
      "Remove most inherited momentum from personal credit.", "Adjust personal credit against a peer benchmark.", "Keep raw results but label the tailwind.",
      "从原始结果一百二十分中扣除三十分继承势能，个人功劳记九十分。", "按同类基准扣除二十分继承势能，个人功劳记一百分。", "保留原始结果，但标注顺风。"),
    m(302, "ag", 1, "headwind_normalization", "The Declining Business Headwind", "衰退业务的逆风",
      "The market contracted during the assessment period, but the file does not separate that uncontrollable headwind from personal contribution.",
      "考核期内大盘已经缩水，案卷却没有把不可控逆风与个人贡献拆开。",
      "Normalize against the market decline.", "Compare with matched declining teams.", "Keep raw results with an explicit caveat.",
      "按市场跌幅校正。", "与同类衰退团队比较。", "保留原始结果并写明限制。"),
    m(303, "ag", 2, "incubation_protection", "Incubation Needs a Clock", "孵化保护也要到点",
      "The new team is still ramping up, yet its file contains neither a protection period nor an expiry. Permanent immunity would hide later underperformance.",
      "新团队仍在爬坡，案卷里却既没有保护期，也没有到期日；永久豁免又会遮住后续失责。",
      "Grant the new team one short protected cycle.", "Protect the new team only at signed milestones.", "Decline protection and fund extra support.",
      "给予新团队一个周期保护；到期后恢复正常考核。", "只在签字里程碑处保护新团队，保护最多持续两个周期。", "不保护分布，但追加支持。"),
    m(304, "ag", 2, "dual_parent_weights", "Two Parents, One Review", "两个家长，一份绩效",
      "Project and functional managers both claim authority. The file has no single frozen set of weights and goal shares, and neither manager has personally replied.",
      "项目线和职能线都声称自己说了算；案卷里还没有唯一冻结的权重、目标份额和最终责任人。",
      "Direct a sixty-percent project-line weight.", "Direct equal parent weights.", "Direct a sixty-percent functional-line weight.",
      "责令项目线权重为六成。", "责令双方权重各半。", "责令职能线权重为六成。"),
    m(305, "ag", 3, "quiet_period", "Reorg Quiet Period", "重组静默期",
      "The reporting line changed just before the review closed. Without a quiet-period rule, the incoming manager can rewrite an almost finished case.",
      "汇报线在考核收口前刚刚变更；若没有静默期规则，新任上司就能改写一宗几乎结案的考核。",
      "Freeze ratings until calibration ends.", "Allow evidence additions but no score edits.", "Permit edits only with dual signature.",
      "校准结束前冻结评级。", "可补证据，不许改分。", "只有双签才能修改。"),
    m(306, "ag", 3, "double_hat_weights", "One Head, Two Hats", "一个脑袋，两顶帽子",
      "The temporary dual-role lead has one finite pool of time, while current responsibility and review weights do not yet close to one hundred percent.",
      "临时双帽负责人只有一份时间，而当前责任份额与考核权重都还没有合计到百分之百。",
      "Split thirty-seventy toward the expert role.", "Split management and expert roles fifty-fifty.", "Split seventy-thirty toward management.",
      "按管理责任三成、专业责任七成分配考核权。", "按管理责任与专业责任各五成分配考核权。", "按管理七成、专业三成分配考核权。"),
    m(307, "ag", 4, "center_scorecard", "Profit Center or Cost Center?", "利润中心还是成本中心",
      "Revenue and enablement teams are currently measured with the same scorecard, mixing growth with cost control before comparison.",
      "创收团队与支撑团队目前共用一张记分卡，收入增长和成本控制在比较前就被混到了一起。",
      "Use a profit-center scorecard.", "Use a cost-and-service scorecard.", "Use a signed hybrid scorecard.",
      "采用利润中心记分卡。", "采用成本与服务记分卡。", "采用签字确认的混合记分卡。"),
    m(308, "ag", 4, "hc_mix", "Managers or Experts?", "管理岗还是专业岗",
      "Management and specialist roles are competing for the same fixed headcount. Any new mix must remain within that total.",
      "管理岗与专业岗正在争用同一份固定编制；任何新构成都不能突破总额。",
      "Keep twenty managers and eighty experts.", "Use a thirty-seventy mix.", "Use a forty-sixty mix.",
      "把百人编制调整为二十名管理岗、八十名专业岗。", "把百人编制调整为三十名管理岗、七十名专业岗。", "把百人编制调整为四十名管理岗、六十名专业岗。"),
    m(309, "ag", 4, "remote_visibility", "The Far Team Is Quiet", "边远团队没声量",
      "The remote team is nearly absent from current review material. Management has bandwidth for only one additional verification, while the visibility gap is already distorting the assessment.",
      "边远团队在本期考核材料中几乎不可见；管理层只剩一次额外核验的带宽，可见度差距却已经开始扭曲考核。",
      "Spend capacity on an on-site visit.", "Spend capacity on a remote evidence forum.", "Accept the visibility discount and record debt.",
      "投入十小时管理容量实地走访；增加十点可见度，不增加交付产出。", "投入十小时管理容量举办远程证据会；增加十点可见度，不增加交付产出。", "接受可见度折损并记债。"),
    m(310, "ag", 4, "legacy_rating_map", "Old Ratings, New Org", "旧档怎么搬进新组织",
      "The reporting line has changed, but authorship of each existing case remains attached to its original author. The old file does not yet identify both that author and the successor now responsible.",
      "汇报线已经变更，既有案卷的署名责任仍由原任承担；归档记录尚未同时标明原责任人与接任者。",
      "Add the successor to the old case without changing its original owner.", "Create a transfer record naming both former owner and successor.", "Keep the old case separate for one cycle.",
      "在旧案补记接任者，原责任仍归原任。", "另立交接记录，同时列明原责任人与接任者。", "旧案独立保留一个周期。"),
    m(311, "ag", 5, "pivot_policy", "A Pivot Is Not a Time Machine", "战略转向不是时光机",
      "The new strategy is in force, while the old cycle still has signed goals. An unclear boundary would let future priorities rewrite past commitments.",
      "新战略已经生效，旧周期仍留有签字目标；两份记录边界不清，就会让未来优先级倒改过去承诺。",
      "Close the old target and open a new one.", "Split credit between the old and new targets, then link both records.", "Delay the pivot until next cycle.",
      "关闭旧目标，另开新目标。", "分别核清新旧目标的贡献，再衔接两份案卷。", "推迟到下一周期再转向。"),

    m(334, "aj", 1, "demand_source", "One Door for Every Demand", "需求统一从正门进",
      "One demand has arrived without a requester, business reason or intake label. In that state, its cost will fall into unowned overtime.",
      "一条需求已经送达，却没有提出者、业务理由和入口标签；照此推进，成本只会落成无人负责的加班。",
      "Tag it as superior-sponsored.", "Tag it as territory demand.", "Tag it as incident-driven.",
      "标为上级发起。", "标为属地需求。", "标为事故驱动。"),
    m(335, "aj", 1, "emergency_route", "Everything Is Urgent", "怎么每件事都紧急",
      "Several demands are marked urgent, but the portfolio has only one remaining slot and no free scope. The labels promise more capacity than exists.",
      "多条需求都贴着“紧急”标签，组合账本却只剩一个槽位，也没有空余范围；标签承诺的容量已经超过现实。",
      "Spend one emergency slot.", "Trade equal scope instead of a slot.", "Reject urgency and keep queue order.",
      "占用唯一的紧急插单槽；不削减原需求范围。", "换出十小时原需求范围；保留紧急插单槽。", "不认紧急，按原顺序排队。"),
    m(336, "aj", 2, "admission_definition", "Ready to Begin?", "开工条件尚未齐备",
      "A request enters delivery only after benefit, boundary and dependencies are signed—or its sponsor owns the ambiguity.",
      "收益、边界、依赖没签清楚，就不算能开工；硬塞进来，模糊责任归发起人。",
      "Return the demand to complete benefit, boundary and dependencies.", "Admit the demand as a bounded exploration.", "Force admission with sponsor liability.",
      "退回需求且不准入；先补齐收益、边界与依赖。", "按有界探索准入需求；预估占用十小时容量。", "强制准入，发起人背模糊责任。"),
    m(338, "aj", 2, "triangle_signature", "Scope, Time, Quality: Pick Two", "范围、期限、质量：请签字",
      "The demand has strained both scope and deadline, but the file names no signer for either tradeoff. The delivery team cannot own that choice by silence.",
      "需求已经同时挤压范围与期限，案卷却没有给任何一项列出签字责任人；交付团队不能因沉默独吞取舍。",
      "Cut scope and sign it.", "Extend time and sign it.", "Add HC and sign the budget.",
      "削减十小时范围并由发起人签字；期限不变。", "期限延长一个周期并由发起人签字；范围不变。", "加 HC，并给预算签字。"),
    m(339, "aj", 3, "estimate_calibration", "Estimate the Work, Not the Hero", "校准估算，不奖赌命",
      "The current on-time reward has produced both padded estimates and last-minute heroics. Estimate errors are not yet paired with their recorded causes.",
      "现行准时奖励同时养出了灌水估算和临门赌命；估算误差尚未与已记录原因对应起来。",
      "Credit calibrated accuracy.", "Credit transparent uncertainty.", "Credit recovery but record estimate debt.",
      "按实际八小时结算校准后的估算；不记灌水。", "公开四小时外部阻塞：实际十二小时按八小时校准结算。", "认可救火，但记录估算债。"),
    m(340, "aj", 4, "wip_route", "Stop Starting, Start Finishing", "少开工，多完工",
      "The pending start would exceed both delivery capacity and the work-in-progress limit. No signed exception covers that excess.",
      "这项待开任务会同时突破交付容量与在制任务上限，案卷里也没有覆盖超额部分的签字例外。",
      "Start within the WIP limit.", "Start with a signed WIP exception.", "Start over limit and record hidden-work debt.",
      "占用一个在制任务槽，并按需求估算值预留容量后开工。", "签署例外后占用两个在制任务槽；额外预留十小时容量。", "超限开工并记录隐性工作债。"),
    m(342, "aj", 4, "blocker_attribution", "Who Owns the Blocked Time?", "阻塞时间算谁的",
      "A block of stalled time has been charged directly to the delivery team, while the file names neither its cause nor anyone responsible for clearing it.",
      "一段阻塞工时被直接扣在交付团队名下，案卷却既没有记录阻塞原因，也没有列出解阻责任人。",
      "Name the independent reviewer as unblock owner; assign all blocked time to obstacles beyond the delivery team's control and apply no team penalty.", "Split blocked hours across shared causes.", "Charge the team with a review flag.",
      "指定独立复核人解阻；阻塞工时全归团队不可控阻碍，交付团队不扣分。", "阻塞工时由团队与外部原因各承担一半；交付团队不作低产出扣分。", "阻塞工时暂计团队，并挂复核标记。"),
    m(337, "aj", 5, "change_tax_route", "A Change Request Has a Tax", "改需求要交税",
      "The requested scope change has consumed capacity after work began. Its added cost is absent from both the deadline ledger and the remaining-scope ledger.",
      "开工后的范围变更已经吃掉额外容量，但新增成本既没有进入期限账，也没有进入剩余范围账。",
      "Pay ten capacity hours and extend time.", "Pay ten capacity hours and remove equal scope.", "Use the one disaster waiver and record policy debt.",
      "支付十小时容量并延期。", "支付十小时容量并等量减范围。", "使用一次灾害豁免并记录政策债。"),
    m(341, "aj", 5, "carryover_route", "Unfinished Work Crosses the Line", "未完工跨周期",
      "The unfinished work still occupies this cycle's reservation, while the next-cycle ledger is ready to charge it again. That would count the same capacity twice.",
      "未完工作仍占着本周期预留，下周期账本却准备再次扣减；同一份容量将被重复计算。",
      "Carry the whole remainder.", "Split and accept a finished slice.", "Cancel the remainder and close its debt.",
      "结转十小时剩余工作；本期释放原预留，下期预占十小时容量。", "验收已完成部分并结转五小时；本期释放原预留，下期预占五小时。", "取消剩余部分并关闭其债。"),
    m(343, "aj", 6, "acceptance_route", "Three Parties, One Delivery Ruling", "提出、执行、验收三方送达",
      "The executor reports completion, but the file contains no acceptance conclusion visible to proposer, executor and acceptor. A delivery record is not their personal consent.",
      "执行人已经报称完成，案卷里却没有一份让提出人、执行人和验收人共同可见的结论；交付记录也不等于三方亲自同意。",
      "Serve all three parties and accept.", "Serve a conditional acceptance with follow-up debt.", "Serve a rejection with a defect list.",
      "向提出人、执行人和验收人送达结论，并通过验收。", "向提出人、执行人和验收人送达结论，并作有条件验收。", "向三方送达缺陷清单并拒收。"),
    m(344, "aj", 7, "value_stage_split", "Launch Is Not Value", "上线不等于价值",
      "Launch, adoption and verified value have each been credited as a fresh hundred percent. The portfolio ledger is counting the same result more than once.",
      "上线、采用与验证价值目前各记了一套百分之百，组合总账因此把同一成果重复计功。",
      "Put most credit in the launch stage.", "Split credit evenly across all three stages.", "Back-load credit to verified value.",
      "按上线六成、采用两成五、已验证价值一成五分配功劳。", "按上线三成、采用三成、已验证价值四成分配功劳。", "把大头留给已验证价值。"),
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
PLAYER_MODE_EVENT = 9000
# Only low-risk, no-payment/no-person-movement policy mechanics may be
# auto-resolved.  Resource gates, signatures, delayed settlement and final
# delivery rulings stay visible.  This list is deliberately frozen and tested:
# widening it is a product decision, not a generator convenience.
PLAYER_BACKGROUND_IDS = frozenset({
    230, 231, 232, 233, 234, 235, 236, 237, 238, 239,
    301, 302, 303, 304, 305, 306, 307, 308,
    334, 336, 339, 342,
})
PLAYER_VISIBLE_IDS = frozenset({
    229, 240, 241,
    309, 310, 311,
    335, 337, 338, 340, 341, 343, 344,
})
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
                f"zg361_p3_{domain}_continue_player_effect",
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
    if PLAYER_BACKGROUND_IDS & PLAYER_VISIBLE_IDS:
        raise ValueError("player background and visible mechanism sets must be disjoint")
    if PLAYER_BACKGROUND_IDS | PLAYER_VISIBLE_IDS != expected:
        raise ValueError("player background and visible mechanism sets must cover every mechanism")
    if len(PLAYER_BACKGROUND_IDS) != 22 or len(PLAYER_VISIBLE_IDS) != 13:
        raise ValueError("player portfolio mode must preserve the frozen 22/13 split")
    if any(order[-1] not in PLAYER_VISIBLE_IDS for order in DOMAIN_ORDER.values()):
        raise ValueError("every domain settlement node must remain player-visible")
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
        # Route B is often a legitimate balanced or alternative policy.  A
        # mechanism may still add an explicit debt in its own payload, but
        # there is no hidden blanket penalty merely for choosing B.
        lines += [addv(f"zg361_p3_{d}_quality", 1)]
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
            setv("zg361_p3_m304_project_parent_named", 1),
            setv("zg361_p3_m304_function_parent_named", 1),
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
            setv("zg361_p3_m310_bridge_old_owner_recorded", 1),
            setv("zg361_p3_m310_bridge_new_owner_recorded", 1),
            setv("zg361_p3_m310_bridge_owner_count", 2),
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
            setv("zg361_p3_m343_proposer_served", 0),
            setv("zg361_p3_m343_executor_served", 0),
            setv("zg361_p3_m343_acceptor_served", 0),
            setv("zg361_p3_m343_service_count", 0),
            setv("zg361_p3_demand_acceptance_outcome", 4),
            "if = {\n\tlimit = { var:zg361_p3_demand_accepted_hours > 0 }\n\tset_variable = { name = zg361_p3_m343_applicable value = 1 }\n\tset_variable = { name = zg361_p3_m343_proposer_served value = 1 }\n\tset_variable = { name = zg361_p3_m343_executor_served value = 1 }\n\tset_variable = { name = zg361_p3_m343_acceptor_served value = 1 }\n\tset_variable = { name = zg361_p3_m343_service_count value = 3 }\n"
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
            setv("zg361_p3_m304_directive_issued", 1),
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
            "set_variable = { name = zg361_p3_m310_bridge_record_issued value = 1 }",
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
    310: ("zg361_p3_m310_old_case", "zg361_p3_m310_mapping_version", "zg361_p3_m310_mapping_route", "zg361_p3_m310_historical_owner", "zg361_p3_m310_mapped_owner", "zg361_p3_m310_bridge_owner_count", "zg361_p3_m310_current_quota_slots"),
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
    343: ("zg361_p3_m343_applicable", "zg361_p3_m343_proposer_signer", "zg361_p3_m343_executor_signer", "zg361_p3_m343_acceptor_signer", "zg361_p3_m343_service_count", "zg361_p3_demand_acceptance_outcome"),
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


def player_ticket(domain: str) -> str:
    return f"""TICKET_OWNER = scope:zg361_p3_{domain}_owner
TICKET_SUBJECT = scope:zg361_p3_{domain}_subject
TICKET_CYCLE = scope:zg361_p3_{domain}_cycle
TICKET_CASE = scope:zg361_p3_{domain}_case"""


def render_player_background_step(spec: Mechanism) -> str:
    """Render one fail-open-to-UI background attempt.

    The numbered route effect remains the sole business authority.  The batch
    dispatcher only selects A/B/C and verifies the route's existing applied
    receipt.  Any guard or resource RED reopens this exact numbered event on
    D+1; it never skips ahead or substitutes a different route.
    """

    domain, mid = spec.domain, spec.mid
    ticket = player_ticket(domain)
    route_branches = []
    for mode, letter in enumerate("abc", 1):
        keyword = "if" if mode == 1 else "else_if"
        route_branches.append(f"""{keyword} = {{
	limit = {{
		root = {{
			has_variable = zg361_p3_player_batch_mode
			var:zg361_p3_player_batch_mode = {mode}
		}}
	}}
	zg361_p3_m{mid}_route_{letter}_effect = {{
{indent(ticket, 2)}
	}}
}}""")
    route_branches.append(f"""else = {{
	# Missing/invalid mode is itself a reason to fall back to the original card.
	scope:zg361_p3_{domain}_owner = {{ trigger_event = {{ id = zg361p3.{mid} days = 1 }} }}
	set_variable = {{ name = zg361_p3_player_dispatch_blocked value = 1 }}
}}""")
    return f"""if = {{
	limit = {{
		var:zg361_p3_player_dispatch_blocked = 0
		NOT = {{ has_variable = zg361_p3_m{mid}_receipt_choice }}
	}}
{indent(chr(10).join(route_branches))}
	if = {{
		limit = {{
			var:zg361_p3_player_dispatch_blocked = 0
			NOT = {{
				AND = {{
					has_variable = zg361_p3_runtime_applied
					var:zg361_p3_runtime_applied = 1
				}}
			}}
		}}
		# Preserve the exact item and its three original buttons after any
		# tuple-guard, dependency or resource failure.
		scope:zg361_p3_{domain}_owner = {{ trigger_event = {{ id = zg361p3.{mid} days = 1 }} }}
		set_variable = {{ name = zg361_p3_player_dispatch_blocked value = 1 }}
		root = {{ set_variable = {{ name = zg361_p3_player_batch_fallback_mid value = {mid} }} }}
	}}
	else_if = {{
		limit = {{
			var:zg361_p3_player_dispatch_blocked = 0
			root = {{
				has_variable = zg361_p3_player_batch_mode
				var:zg361_p3_player_batch_mode = 3
			}}
		}}
		root = {{ change_variable = {{ name = zg361_p3_player_policy_debt_disclosed_n add = 1 }} }}
	}}
}}"""


def render_player_visible_step(spec: Mechanism) -> str:
    domain, mid = spec.domain, spec.mid
    return f"""if = {{
	limit = {{
		var:zg361_p3_player_dispatch_blocked = 0
		NOT = {{ has_variable = zg361_p3_m{mid}_receipt_choice }}
	}}
	scope:zg361_p3_{domain}_owner = {{ trigger_event = {{ id = zg361p3.{mid} days = 1 }} }}
	set_variable = {{ name = zg361_p3_player_dispatch_blocked value = 1 }}
}}"""


def render_player_dispatch(domain: str) -> str:
    specs = by_id()
    steps = []
    for mid in DOMAIN_ORDER[domain]:
        spec = specs[mid]
        if mid in PLAYER_BACKGROUND_IDS:
            steps.append(render_player_background_step(spec))
        else:
            steps.append(render_player_visible_step(spec))
    return f"""# Player-only portfolio dispatcher.  It never owns business writes: every
# automatic item calls the unchanged numbered route core, and every failed
# automatic item falls back to its original D+1 event instead of being skipped.
zg361_p3_{domain}_continue_player_effect = {{
	remove_variable = zg361_p3_player_dispatch_blocked
	set_variable = {{ name = zg361_p3_player_dispatch_blocked value = 0 }}
{indent(chr(10).join(steps))}
	remove_variable = zg361_p3_player_dispatch_blocked
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
	root = {
		remove_variable = zg361_p3_player_batch_mode
		remove_variable = zg361_p3_player_batch_fallback_mid
		set_variable = { name = zg361_p3_player_policy_debt_disclosed_n value = 0 }
	}
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
    if domain == "aa":
        player_entry = (
            f"scope:zg361_p3_{domain}_owner = {{ "
            f"trigger_event = {{ id = zg361p3.{PLAYER_MODE_EVENT} }} }}"
        )
    else:
        player_entry = f"""if = {{
\tlimit = {{
\t\troot = {{
\t\t\thas_variable = zg361_p3_player_batch_mode
\t\t\tvar:zg361_p3_player_batch_mode < 4
\t\t}}
\t}}
\tzg361_p3_{domain}_continue_player_effect = yes
}}
else = {{
\tscope:zg361_p3_{domain}_owner = {{ trigger_event = {{ id = zg361p3.{first} }} }}
}}"""
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
{indent(player_entry, 3)}
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
        sections += [
            render_init(domain),
            render_subject_read(domain),
            render_ai(domain),
            render_player_dispatch(domain),
            render_launch(domain),
        ]
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
    if len(historical_names) != 195 or len(set(historical_names)) != 195:
        raise ValueError("phase-3 historical render must contain 195 unique effects")
    if len(configured_names) != 195 or len(set(configured_names)) != 195:
        raise ValueError("phase-3 purpose map must contain 195 unique effects")
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
    post_apply = []
    if choice == 3:
        post_apply.append(
            "change_variable = { name = "
            "zg361_p3_player_policy_debt_disclosed_n add = 1 }"
        )
    if next_mid is not None:
        post_apply.append(f"""if = {{
\tlimit = {{
\t\thas_variable = zg361_p3_player_batch_mode
\t\tvar:zg361_p3_player_batch_mode < 4
\t}}
\tscope:zg361_p3_{d}_subject = {{ zg361_p3_{d}_continue_player_effect = yes }}
}}
else = {{
\ttrigger_event = {{ id = zg361p3.{next_mid} days = 1 }}
}}""")
    retry = f"""# A manual choice that fails its current tuple/resource guard returns to
# this exact card on D+1; the chain never advances on a failed write.
trigger_event = {{ id = zg361p3.{mid} days = 1 }}
set_variable = {{ name = zg361_p3_player_batch_fallback_mid value = {mid} }}"""
    if post_apply:
        applied_body = indent(chr(10).join(post_apply), 2)
        next_event = f"""
\tif = {{
\t\tlimit = {{ scope:zg361_p3_{d}_subject = {{ has_variable = zg361_p3_runtime_applied var:zg361_p3_runtime_applied = 1 }} }}
{applied_body}
\t}}
\telse = {{
{indent(retry, 2)}
\t}}"""
    else:
        next_event = f"""
\tif = {{
\t\tlimit = {{
\t\t\tscope:zg361_p3_{d}_subject = {{
\t\t\t\tNOT = {{
\t\t\t\t\tAND = {{
\t\t\t\t\t\thas_variable = zg361_p3_runtime_applied
\t\t\t\t\t\tvar:zg361_p3_runtime_applied = 1
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}
\t\t}}
{indent(retry, 2)}
\t}}"""
    tooltip = f"\n\tcustom_tooltip = zg361p3.{mid}.c.tt" if choice == 3 else ""
    return f"""option = {{
\tname = zg361p3.{mid}.{letter}{tooltip}
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


def render_player_mode_event() -> str:
    options = []
    for mode, letter in enumerate("abcd", 1):
        options.append(f"""option = {{
\tname = zg361p3.{PLAYER_MODE_EVENT}.{letter}
\tset_variable = {{ name = zg361_p3_player_batch_mode value = {mode} }}
\tscope:zg361_p3_aa_subject = {{ zg361_p3_aa_continue_player_effect = yes }}
}}""")
    return f"""# One player-visible portfolio-mode choice.  Modes A/B/C affect only the
# frozen background whitelist; mode D keeps the original 35-card route.
zg361p3.{PLAYER_MODE_EVENT} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = zg361p3.{PLAYER_MODE_EVENT}.t
\tdesc = zg361p3.{PLAYER_MODE_EVENT}.desc
\ttrigger = {{
{indent(event_guard(by_id()[DOMAIN_ORDER['aa'][0]]), 2)}
\t}}
{indent(chr(10).join(options))}
}}"""


def render_events() -> bytes:
    validate_specs()
    specs = by_id()
    events = ["namespace = zg361p3", render_player_mode_event()]
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


PLAYER_DEBT_STATUS_CN = "本轮已经登记制度债 [ROOT.Var('zg361_p3_player_policy_debt_disclosed_n').GetValue|0] 笔。"
PLAYER_DEBT_STATUS_EN = "This portfolio has recorded [ROOT.Var('zg361_p3_player_policy_debt_disclosed_n').GetValue|0] policy debts so far."
PLAYER_MODE_CN = {
    "t": "本轮办案方式",
    "desc": (
        "当事人 [zg361_p3_aa_subject.GetShortUIName] 的指标、改组与交付案已经立卷。"
        "全案共三十五项：二十二项常规案可以统一口径办理，十三项涉及资源、人物去留或最终结算，必须单独呈报。"
        "统一办理仍为每项保留正式案卷、期限与回执。"
        + PLAYER_DEBT_STATUS_CN
    ),
    "a": "证据完整、可复核者统一办理二十二项；条件不足则逐案呈报。",
    "b": "以迅速交付为先统一办理二十二项；条件不足则逐案呈报。",
    "c": "搁置二十二项常规案，每件各记一笔下周期制度债。",
    "d": "全部三十五项逐案呈报，由我分别裁决。",
}
PLAYER_MODE_EN = {
    "t": "How This Portfolio Will Be Heard",
    "desc": (
        "The metrics, reorganization, and delivery portfolio for "
        "[zg361_p3_aa_subject.GetShortUIName] is open. It contains thirty-five items: "
        "twenty-two routine matters can follow one common standard, while thirteen matters "
        "involving resources, people, or final settlement must be presented individually. "
        "Common handling still preserves a formal file, deadline, and receipt for every matter. "
        + PLAYER_DEBT_STATUS_EN
    ),
    "a": "Resolve twenty-two routine matters by evidence; present any failed preflight separately.",
    "b": "Resolve twenty-two routine matters for delivery; present any failed preflight separately.",
    "c": "Defer twenty-two routine matters and record one next-cycle policy debt for each.",
    "d": "Present all thirty-five matters one by one for my separate ruling.",
}


def render_localization(language: str) -> bytes:
    validate_specs()
    if language == "simp_chinese":
        header = "l_simp_chinese:"
        rows = [
            f' zg361p3.{PLAYER_MODE_EVENT}.{key}:0 "{esc(value)}"'
            for key, value in PLAYER_MODE_CN.items()
        ]
        for spec in MECHANISMS:
            desc = spec.desc_cn
            if spec.mid in PLAYER_VISIBLE_IDS:
                desc += PLAYER_DEBT_STATUS_CN
            rows += [
                f' zg361p3.{spec.mid}.t:0 "{esc(spec.title_cn)}"',
                f' zg361p3.{spec.mid}.desc:0 "{esc(desc)}"',
                *(f' zg361p3.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", spec.routes_cn)),
                f' zg361p3.{spec.mid}.c.tt:0 "{esc(DEFER_TOOLTIP_CN)}"',
            ]
    else:
        header = f"l_{language}:"
        rows = [
            f' zg361p3.{PLAYER_MODE_EVENT}.{key}:0 "{esc(value)}"'
            for key, value in PLAYER_MODE_EN.items()
        ]
        for spec in MECHANISMS:
            desc = spec.desc_en
            if spec.mid in PLAYER_VISIBLE_IDS:
                desc += f" {PLAYER_DEBT_STATUS_EN}"
            rows += [
                f' zg361p3.{spec.mid}.t:0 "{esc(spec.title_en)}"',
                f' zg361p3.{spec.mid}.desc:0 "{esc(desc)}"',
                *(f' zg361p3.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", spec.routes_en)),
                f' zg361p3.{spec.mid}.c.tt:0 "{esc(DEFER_TOOLTIP_EN)}"',
            ]
    if language == "simp_chinese":
        rows = normalize_localization_rows(rows)
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
