"""Render Li Yu Dao school consent scripts without game/screen/process operations.

Native admission defaults closed. An optional, hash-bound root receipt can admit
observed primitives; it does not claim that this consent event flow was tested.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from school_consent_data import BASELINE_COMMIT, GAME_VERSION, NATIVE_PRIMITIVE_STATUS, POLICY

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / "school_consent_templates"
DEFAULT_OUTPUT = ROOT
DEFAULT_NATIVE_EVIDENCE = Path(__file__).resolve().parent / "reference/native-primitive-tracked-admission.json"
CHECKOUT = ROOT.parent
STATUSES = ("core", "permitted", "known", "prohibited")
SHARED_PATHS = frozenset({"common/scripted_effects/lyd_c3_head_factory.txt",
                          "common/scripted_effects/lyd_c3_migration_hooks.txt"})
ROUND_FIELDS = (
    "active", "kind", "terms_revision", "source_faith", "source_main", "moving_rite",
    "source_head", "target_rep", "target_faith", "target_main", "target_head",
    "source_total", "target_total", "target_rite_total", "dormant_total", "source_yes", "target_yes", "player_total", "player_yes",
    "source_signed", "target_signed", "source_head_yes", "target_head_yes",
    "source_singleton", "source_head_title", "source_rite_head", "source_head_retired",
    "target_requested", "old_permission", "snapshot_valid", "result",
    "active_receivers", "mandated_receivers", "unorganized_receivers",
)
ROUND_LISTS = ("source_electors", "target_electors", "target_followers", "players", "target_rites", "dormant_rites", "protected_head_titles") + tuple(
    f"source_{kind}" for kind in (*STATUSES, "doctrines")
)

LOC = {
    'lyd_c2_detach_requirements_tt': ('我已入儒门，成年且有领地，能够自由理事，学识至少为15；本派属于本模组学统、不是当前共同体主流，且没有正在议定的归属或领袖议案，也不在归属调整或重议等待期。', "I am an adult, landed initiate of a tradition in this mod, free to act and with at least 15 Learning. My tradition is not the current communion's main rite, has no current affiliation or leadership proposal, and is outside its transition and retry waiting periods."),
    'lyd_c2_review_requirements_tt': ('我仍具备发起资格，且本轮议案仍对应我的学统、共同体、领袖及接收代表；本派与接收方的本轮归属约定仍有效。人选或归属变化后须重新议定。', 'I remain eligible to initiate, and this proposal still matches my tradition, communion, heads and receiving representative. Its current affiliation arrangements remain valid; changes require a new round.'),
    'lyd_c2_cancel_requirements_tt': ('我有尚未实施的当前议案；即使已失去发起资格，仍可撤回自己的这一轮议案。', 'I have a current proposal that has not been enacted. I may withdraw my own round even after losing eligibility to initiate.'),
    'lyd_c2_join_requirements_tt': ('我具备发起资格，本派可以议定来归，且双方没有正在议定的归属或领袖议案。对方须是另一儒家共同体主流的合格学者；多礼仪共同体的主流不能随本议案迁出。', "I am eligible to initiate, my tradition may propose reunion, and neither side has a current affiliation or leadership proposal. The recipient must be a qualified scholar of another Confucian communion's main rite. A main rite with other affiliated rites cannot move through this proposal."),
    'lyd_c2_detach_open_tt': ('召集本派授权之议，并征询所有受影响玩家。本派须取得三分之二学者授权，所有受影响玩家须明确同意，之后方可签署、复核与实施；提出议案时不改变归属，也不收取分立费用。', "Open our school's mandate round and consult every affected player. A two-thirds scholarly mandate and every affected player's express consent are required before signing, revalidation and enactment. Opening a proposal changes no affiliation and charges no separation cost."),
    'lyd_c2_review_open_tt': ('重新核对本轮人选、归属、授权与条款，并打开复核议案。查阅本身不替任何一方投票或签署，也不实施归属或收取迁移费用。', "Recheck this round's representatives, affiliation, mandates and terms, then open its review. Reviewing casts no vote, grants no signature, changes no affiliation and charges no transition cost."),
    'lyd_c2_cancel_round_tt': ('结束自己的当前议案，仅解除属于自己这一轮的议案占用。不改变礼仪或共同体归属，也不收取合流或分立费用。', 'End my current proposal and release only the arrangements held by my own round. This changes no rite or communion affiliation and charges no reunion or separation cost.'),
    'lyd_c2_join_open_tt': ('提出接纳本派的议案，并分别征询本派、接收共同体各活跃礼仪与所有受影响玩家。送达不等于同意；各派须取得三分之二授权或规定的现任持有者背书，所有受影响玩家仍须明确同意。提出时不改变归属，也不收取合流费用。', 'Propose reception of our tradition and separately consult our school, every active receiving rite and every affected player. Delivery is not consent: each school requires its two-thirds mandate or the prescribed current-holder endorsement, and every affected player must expressly consent. Opening changes no affiliation and charges no reunion cost.'),
    "lyd_c2_propose_join_interaction": ("议定学统来归", "Propose a Tradition's Reunion"),
    "lyd_c2_propose_join_interaction_desc": ("向对方提出接纳本派的议案。发出议案不代表任何一方已同意；本派与接收方须各得三分之二授权，受影响玩家亦须明确选择。", "Propose that the recipient's communion receive our tradition. Delivery is not consent: each school needs a two-thirds mandate, and every affected player must choose."),
    "lyd_c2_propose_detach_decision": ("议请另立学统", "Propose an Independent Communion"),
    "lyd_c2_propose_detach_decision_desc": ("就本派的共同体归属召集议论。诸家之学仍可往来，另立共同体也不改变政治领属。", "Ask our school to consider its communal affiliation. Traditions may retain scholarly ties, and religious separation does not alter political allegiance."),
    "lyd_c2_propose_detach_decision_tooltip": ("提出本派独立议案，先征求授权", "Open a separation proposal and seek a mandate"),
    "lyd_c2_propose_detach_decision_confirm": ("先问本派之意", "Consult our school"),
    "lyd_c2_review_proposal_decision": ("复核本轮议案", "Review the Current Proposal"),
    "lyd_c2_review_proposal_decision_desc": ("查验本派授权、接收方答复与共同条款。人选或归属变化后，须重新议定。", "Review school mandates, the receiving party's reply and the terms. Changes in representatives or affiliation require a new round."),
    "lyd_c2_review_proposal_decision_tooltip": ("查看并复核当前议案", "Review and revalidate the current proposal"),
    "lyd_c2_review_proposal_decision_confirm": ("逐项复核", "Review the terms"),
    "lyd_c2_cancel_proposal_decision": ("撤回本轮议案", "Withdraw the Current Proposal"),
    "lyd_c2_cancel_proposal_decision_desc": ("撤回尚未实施的议案。撤回不替任何一方认可归属，也不收取合流或分立的费用。", "Withdraw a proposal that has not been enacted. Withdrawal grants no consent and incurs no transition cost."),
    "lyd_c2_cancel_proposal_decision_tooltip": ("结束本轮议案，不改变礼仪归属", "End this round without changing affiliation"),
    "lyd_c2_cancel_proposal_decision_confirm": ("撤回议案", "Withdraw it"),
    "lyd_c2_proposal_t": ("议经论礼，先问诸儒", "Consult before Changing Communion"),
    "lyd_c2_proposal_desc": ("议案只涉及本派整项礼仪的共同体归属，不改核心信条，不替换接收方主流。各地具备问学资格者将各自表决，受影响玩家另有同意或拒绝的选择。授权仅用于本轮条款，一年内未成即须重议。", "The proposal concerns the affiliation of this whole rite. It changes no core tenets and replaces no receiving main rite. Qualified scholars throughout the school vote individually; affected players separately consent or refuse. Authorization covers only this round's terms and expires after one year."),
    "lyd_c2_source_ballot_t": ("本派授权之议", "Our School's Mandate"),
    "lyd_c2_source_ballot_desc": ("是否授权本轮发起者代表本派签署这项归属议案？本派经典、祭修与学统将保留；此授权不处分他国国礼或祀产，亦不替受影响玩家作决定。", "Will you authorize this initiator to sign the current affiliation proposal for our school? Our learning and practice remain. This mandate does not dispose of another realm's state rites or property, nor decide for affected players."),
    "lyd_c2_target_ballot_t": ("接纳来归之议", "Mandate to Receive a Tradition"),
    "lyd_c2_target_ballot_desc": ("是否授权本轮所提代表同意接纳来归学统？现有主流保持，来归者保留自身礼仪。三分之二支持形成授权，代表仍须亲自答复。", "Will you authorize the proposed representative to receive the incoming tradition? Our main rite remains and the incoming school retains its own rite. Two-thirds support creates a mandate; the representative must still reply personally."),
    "lyd_c2_holder_t": ("本派现任持有者的背书", "Endorsement by This Rite's Current Holder"),
    "lyd_c2_holder_desc": ("本派仍有信众或伯爵领，本轮却没有符合问学资格的表决者。作为现任礼仪持有者，我可以明确背书，也可以拒绝；这不是三分之二学者票，且不能替代所有受影响玩家的同意。没有真实持有者的活跃礼仪须先补足组织条件。", "Our rite has followers or counties but no qualified scholar electorate in this round. As its current holder, I may expressly endorse or refuse. This is not a two-thirds scholarly vote and cannot replace consent from every affected player. An active rite without a real holder must first establish the required organization."),
    "lyd_c2_holder_yes": ("我以现任持有者身份明确背书", "I expressly endorse as the current holder"),
    "lyd_c2_holder_no": ("我拒绝，本轮须重新议定", "I refuse; a new round is required"),
    "lyd_c2_vote_yes": ("我授权此人签署本轮条款", "I authorize this representative for these terms"),
    "lyd_c2_vote_no": ("我不赞成这项授权", "I oppose this mandate"),
    "lyd_c2_player_consent_t": ("我的共同体归属", "My Communion's Affiliation"),
    "lyd_c2_player_consent_desc": ("本轮议案将作用于共享的礼仪共同体，可能影响各地人物与伯爵领。我可以同意，也可以拒绝。学者票数和保护者出资不能替代我的选择。", "This proposal acts on a shared rite and may affect characters and counties in different realms. I may consent or refuse. A scholarly majority or a sponsor's resources cannot substitute for my choice."),
    "lyd_c2_player_yes": ("我明确同意本轮归属条款", "I expressly consent to these affiliation terms"),
    "lyd_c2_player_no": ("我拒绝，本轮不得实施", "I refuse; this round must not proceed"),
    "lyd_c2_review_t": ("授权与条款", "Mandates and Terms"),
    "lyd_c2_review_desc": ("本派赞成票：[ROOT.Char.MakeScope.Var('lyd_c2_source_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_source_total').GetValue|0]。接收方汇总赞成票：[ROOT.Char.MakeScope.Var('lyd_c2_target_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_target_total').GetValue|0]，仅供参考。接收方已授权的活跃礼仪：[ROOT.Char.MakeScope.Var('lyd_c2_mandated_receivers').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_active_receivers').GetValue|0]；休眠模板：[ROOT.Char.MakeScope.Var('lyd_c2_dormant_total').GetValue|0]，不计作赞成。缺少合格学者及有效持有者的活跃礼仪：[ROOT.Char.MakeScope.Var('lyd_c2_unorganized_receivers').GetValue|0]，须先补足教师或组织条件。受影响玩家同意：[ROOT.Char.MakeScope.Var('lyd_c2_player_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_player_total').GetValue|0]。每个活跃礼仪须单独授权；签署后仍须最终复核。", "Our votes: [ROOT.Char.MakeScope.Var('lyd_c2_source_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_source_total').GetValue|0]. Aggregate receiving votes: [ROOT.Char.MakeScope.Var('lyd_c2_target_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_target_total').GetValue|0], for reference only. Mandated active receiving rites: [ROOT.Char.MakeScope.Var('lyd_c2_mandated_receivers').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_active_receivers').GetValue|0]. Dormant templates: [ROOT.Char.MakeScope.Var('lyd_c2_dormant_total').GetValue|0], excluded rather than counted as assent. Active rites lacking scholars and a valid holder: [ROOT.Char.MakeScope.Var('lyd_c2_unorganized_receivers').GetValue|0]; a teacher or organization is required first. Player consent: [ROOT.Char.MakeScope.Var('lyd_c2_player_yes').GetValue|0]/[ROOT.Char.MakeScope.Var('lyd_c2_player_total').GetValue|0]. Every active rite must authorize separately, followed by final revalidation."),
    "lyd_c2_sign_source": ("依本派授权，签署此议", "Sign under our school's mandate"),
    "lyd_c2_sign_source_tt": ("签署本轮归属与已展示的宗主退休／另立条款；合流还须接收方代表及其有效领袖答复。旧领袖离开认可不能替代授权，也不构成额外永久否决。", "Sign these affiliation and disclosed head retirement/provisioning terms. Reunion also requires the receiving representative and valid head to reply. The former head's recognition does not replace the mandate or add a permanent veto."),
    "lyd_c2_receive_t": ("接收方的答复", "The Receiving Representative's Reply"),
    "lyd_c2_receive_desc": ("接收共同体各活跃礼仪的授权已经形成；休眠礼仪仅保留模板，没有被记作赞成。是否亲自签署接纳条款？我可以同意或拒绝；被提名为代表本身不等于已经同意。", "Every active rite of the receiving communion has formed its mandate. Dormant rites retain their templates and were not counted as assent. Will I personally sign the reception terms? I may consent or refuse; nomination alone was not consent."),
    "lyd_c2_receive_yes": ("我同意并签署本轮条款", "I consent and sign these terms"),
    "lyd_c2_receive_no": ("我拒绝接纳本轮条款", "I refuse these terms"),
    "lyd_c2_head_receive_t": ("共同体领袖的接纳", "Reception by the Communion's Head"),
    "lyd_c2_head_receive_desc": ("学派代表已提出接纳意见。作为当前有效领袖，我仍须对这一轮的共同体安排明确答复；我的同意不能替代各派授权。", "The school representative has signed for reception. As the current head, I must explicitly answer for this round's communal arrangement. My consent does not replace school mandates."),
    "lyd_c2_head_source_t": ("来源共同体的答复", "The Source Communion's Reply"),
    "lyd_c2_head_source_desc": ("本派已议定来归。我可以认可，也可以记下不认可；额外的离开许可不能推翻本派授权、双方代表签署与全体受影响玩家的同意。若本轮明确退休本派专属宗主头衔，只解除并退休捕获的该职位，保留我本人、其他头衔与授业记录。", "Our school has authorized reunion. I may recognize it or record nonrecognition; an additional release permission cannot override the school mandate, both representatives' signatures and every affected player's consent. An expressly retired school-owned head title is the only office removed; my person, other titles and teaching record remain."),
    "lyd_c2_source_head_recognize": ("我认可此次来归", "I recognize this reunion"),
    "lyd_c2_source_head_withhold": ("记录我不认可，仍按有效授权处理", "Record my nonrecognition; valid mandates remain"),
    "lyd_c2_peaceful_t": ("请立与另立", "Permission and Autonomy"),
    "lyd_c2_peaceful_desc": ("本派请求另立共同体。是否认可为和平请立？拒绝会留下未获认可的记录，但不能永远阻止已有本派授权的自主自立。", "The school requests its own communion. Will I recognize a peaceful separation? Refusal leaves it unrecognized, but cannot permanently veto autonomy supported by the school's own mandate."),
    "lyd_c2_peaceful_yes": ("我认可和平请立", "I recognize a peaceful separation"),
    "lyd_c2_peaceful_no": ("我不认可，但这不取消本派之议", "I withhold recognition without cancelling the school's mandate"),
    "lyd_c2_confirm": ("复核无误，实施本轮归属", "Enact the revalidated affiliation"),
    "lyd_c2_confirm_tt": ("合流费用为300金币、1500虔诚；自立为200金币、1000虔诚。成功后本派调整期五年；不改变政治领属。", "Reunion costs 300 gold and 1500 piety; separation costs 200 gold and 1000 piety. A successful transition sets a five-year school cooldown and changes no political allegiance."),
    "lyd_c2_native_pending": ("本轮尚待归属机制核验", "Affiliation mechanics still await verification"),
    "lyd_c2_native_pending_tt": ("候选版本可以议定授权，最终归属操作尚未通过实机核验。授权不能当作已完成合流或分立。", "This candidate can collect mandates, but final affiliation operations have not passed live verification. Consent is not a completed reunion or separation."),
    "lyd_c2_result_t": ("本轮议案的记录", "The Record of This Round"),
    "lyd_c2_success_desc": ("本轮归属操作的即时条件已符合，费用已收取。学统身份保留，调整期届满可以重新议定；后续仍须观察共同体状态。", "The immediate affiliation postconditions were met and costs collected. School identity remains; another proposal may follow after the cooldown. Subsequent communal state still requires observation."),
    "lyd_c2_rejected_desc": ("本轮未取得所需同意，礼仪归属保持。拒绝不会永久关闭来日协商；本派一年后可以重新议定。", "This round lacked required consent and affiliation remains. Refusal does not permanently close negotiations; the school may reconsider after one year."),
    "lyd_c2_cancelled_desc": ("议案已撤回，没有收取归属调整费用。另议须重新取得授权。", "The proposal was withdrawn without transition costs. A new round requires fresh authorization."),
    "lyd_c2_expired_desc": ("本轮授权已届期，尚未实施的议案结束。旧票与旧签署不能用于新的条款。", "This round's authorization expired before enactment. Old ballots and signatures cannot authorize new terms."),
    "lyd_c2_failed_desc": ("归属操作后的状态未符合所议条件。当前实际状态保留，不伪作成功；需停止调整并查验。", "The affiliation operation did not meet its postconditions. The actual state is preserved without claiming success; further adjustment requires investigation."),
    "lyd_c2_wait": ("先待诸方答复", "Await the parties' replies"),
    "lyd_c2_cancel": ("撤回本轮议案", "Withdraw this round"),
    "lyd_c2_acknowledge": ("记下本轮经过", "Record this round"),
}


OFFICE_TERMS = (
    " 职位条款亦在本轮授权范围内：仅来源信仰恰有本派一项礼仪、且其捕获宗主头衔明确属于本mod与该来源faith时，来归才退休这一项职位；旧人、其他头衔与授业记录保留。多派来源或外来头衔不由此退休。若本派章程采用世俗宗主，另立时由本轮获授权的发起代表担任，并只建立一个专属宗主头衔；无宗主章程不暗改。旧宗主可以记录不认可，但不能替代学派与受影响玩家的决定。",
    " This mandate also covers these office terms: reunion retires only the captured head title when the source faith contains this sole rite and that title is explicitly owned by this mod and that source faith. The former person, other titles and teaching record remain. This does not retire multi-rite or foreign offices. If the school's rules already provide a temporal head, separation installs the authorized initiating representative and creates only one dedicated head title; no-head rules are not covertly changed. A former head may record nonrecognition without substituting for school and affected-player decisions.",
)
for _key in ("lyd_c2_proposal_desc", "lyd_c2_source_ballot_desc", "lyd_c2_target_ballot_desc", "lyd_c2_player_consent_desc", "lyd_c2_receive_desc"):
    LOC[_key] = tuple(text + clause for text, clause in zip(LOC[_key], OFFICE_TERMS))


def side_references(side: str) -> tuple[str, str]:
    return ("var:lyd_c2_moving_rite", "scope:lyd_c2_actor") if side == "source" else ("var:lyd_c2_target_main", "var:lyd_c2_target_rep")


def guarded_side(side: str, text: str) -> str:
    return text if side == "source" else "if = { limit = { var:lyd_c2_kind = 1 }\n" + text + "\n}"


def capture_terms() -> str:
    result = []
    for side in ("source",):
        rite, representative = side_references(side)
        lines = []
        for status in STATUSES:
            lines.append(f"""
set_variable = {{ name = lyd_c2_{side}_{status}_total value = 0 }}
{rite} = {{
    every_rite_tenet = {{
        status = {status}
        save_scope_as = lyd_c2_snapshot_item
        scope:lyd_c2_actor = {{
            add_to_variable_list = {{ name = lyd_c2_{side}_{status} target = scope:lyd_c2_snapshot_item }}
            change_variable = {{ name = lyd_c2_{side}_{status}_total add = 1 }}
        }}
    }}
}}
""")
        lines.append(f"""
set_variable = {{ name = lyd_c2_{side}_doctrines_total value = 0 }}
{representative} = {{
    every_character_doctrine = {{
        rite_filter = scope:lyd_c2_actor.{rite}
        save_scope_as = lyd_c2_snapshot_item
        scope:lyd_c2_actor = {{
            add_to_variable_list = {{ name = lyd_c2_{side}_doctrines target = scope:lyd_c2_snapshot_item }}
            change_variable = {{ name = lyd_c2_{side}_doctrines_total add = 1 }}
        }}
    }}
}}
""")
        result.append(guarded_side(side, "\n".join(lines)))
    lines = ["""
if = { limit = { var:lyd_c2_kind = 1 }
    every_in_list = { variable = lyd_c2_target_rites
        save_scope_as = lyd_c2_target_school
        set_variable = { name = lyd_c2_snapshot_counties value = rite_counties }
        remove_variable = lyd_c2_snapshot_holder
        if = { limit = { exists = head_of_rite } set_variable = { name = lyd_c2_snapshot_holder value = head_of_rite } }
"""]
    for status in STATUSES:
        lines.append(f"""
        clear_variable_list = lyd_c2_target_{status}
        set_variable = {{ name = lyd_c2_target_{status}_total value = 0 }}
        every_rite_tenet = {{ status = {status}
            save_scope_as = lyd_c2_snapshot_item
            scope:lyd_c2_target_school = {{
                add_to_variable_list = {{ name = lyd_c2_target_{status} target = scope:lyd_c2_snapshot_item }}
                change_variable = {{ name = lyd_c2_target_{status}_total add = 1 }}
            }}
        }}
""")
    lines.append("""
        clear_variable_list = lyd_c2_target_doctrines
        set_variable = { name = lyd_c2_target_doctrines_total value = 0 }
        scope:lyd_c2_actor.var:lyd_c2_target_rep = {
            every_character_doctrine = { rite_filter = scope:lyd_c2_target_school
                save_scope_as = lyd_c2_snapshot_item
                scope:lyd_c2_target_school = {
                    add_to_variable_list = { name = lyd_c2_target_doctrines target = scope:lyd_c2_snapshot_item }
                    change_variable = { name = lyd_c2_target_doctrines_total add = 1 }
                }
            }
        }
    }
}
""")
    result.append("\n".join(lines))
    return "\n".join(result)


def refresh_terms() -> str:
    result = []
    for side in ("source",):
        rite, representative = side_references(side)
        lines = []
        for status in STATUSES:
            lines.append(f"""
set_variable = {{ name = lyd_c2_check_count value = 0 }}
{rite} = {{ every_rite_tenet = {{ status = {status} scope:lyd_c2_actor = {{ change_variable = {{ name = lyd_c2_check_count add = 1 }} }} }} }}
if = {{ limit = {{ var:lyd_c2_check_count != var:lyd_c2_{side}_{status}_total }} set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
every_in_list = {{
    variable = lyd_c2_{side}_{status}
    save_scope_as = lyd_c2_snapshot_item
    if = {{
        limit = {{ scope:lyd_c2_actor.{rite} = {{ NOT = {{ any_rite_tenet = {{ status = {status} this = scope:lyd_c2_snapshot_item }} }} }} }}
        scope:lyd_c2_actor = {{ set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
    }}
}}
""")
        lines.append(f"""
set_variable = {{ name = lyd_c2_check_count value = 0 }}
{representative} = {{ every_character_doctrine = {{ rite_filter = scope:lyd_c2_actor.{rite} scope:lyd_c2_actor = {{ change_variable = {{ name = lyd_c2_check_count add = 1 }} }} }} }}
if = {{ limit = {{ var:lyd_c2_check_count != var:lyd_c2_{side}_doctrines_total }} set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
every_in_list = {{
    variable = lyd_c2_{side}_doctrines
    save_scope_as = lyd_c2_snapshot_item
    if = {{
        limit = {{ scope:lyd_c2_actor.{rite} = {{ NOT = {{ rite_has_doctrine = scope:lyd_c2_snapshot_item }} }} }}
        scope:lyd_c2_actor = {{ set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
    }}
}}
""")
        result.append(guarded_side(side, "\n".join(lines)))
    lines = ["""
if = { limit = { var:lyd_c2_kind = 1 }
    every_in_list = { variable = lyd_c2_target_rites
        save_scope_as = lyd_c2_target_school
        if = { limit = { OR = {
            faith != scope:lyd_c2_actor.var:lyd_c2_target_faith
            rite_counties != var:lyd_c2_snapshot_counties
        } } scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } } }
        if = { limit = { has_variable = lyd_c2_snapshot_holder }
            if = { limit = { OR = { NOT = { exists = head_of_rite } NOT = { head_of_rite = var:lyd_c2_snapshot_holder } } }
                scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
            }
        }
        else_if = { limit = { exists = head_of_rite } scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } } }
"""]
    for status in STATUSES:
        lines.append(f"""
        set_variable = {{ name = lyd_c2_check_count value = 0 }}
        every_rite_tenet = {{ status = {status} scope:lyd_c2_target_school = {{ change_variable = {{ name = lyd_c2_check_count add = 1 }} }} }}
        if = {{ limit = {{ var:lyd_c2_check_count != var:lyd_c2_target_{status}_total }} scope:lyd_c2_actor = {{ set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }} }}
        every_in_list = {{ variable = lyd_c2_target_{status}
            save_scope_as = lyd_c2_snapshot_item
            if = {{ limit = {{ scope:lyd_c2_target_school = {{ NOT = {{ any_rite_tenet = {{ status = {status} this = scope:lyd_c2_snapshot_item }} }} }} }}
                scope:lyd_c2_actor = {{ set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
            }}
        }}
""")
    lines.append("""
        set_variable = { name = lyd_c2_check_count value = 0 }
        scope:lyd_c2_actor.var:lyd_c2_target_rep = {
            every_character_doctrine = { rite_filter = scope:lyd_c2_target_school
                scope:lyd_c2_target_school = { change_variable = { name = lyd_c2_check_count add = 1 } }
            }
        }
        if = { limit = { var:lyd_c2_check_count != var:lyd_c2_target_doctrines_total }
            scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
        }
        every_in_list = { variable = lyd_c2_target_doctrines
            save_scope_as = lyd_c2_snapshot_item
            if = { limit = { scope:lyd_c2_target_school = { NOT = { rite_has_doctrine = scope:lyd_c2_snapshot_item } } }
                scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
            }
        }
    }
}
""")
    result.append("\n".join(lines))
    return "\n".join(result)


def refresh_electorates() -> str:
    result = ["set_variable = { name = lyd_c2_check_players value = 0 }"]
    for side in ("source",):
        rite, _ = side_references(side)
        faith = f"var:lyd_c2_{side}_faith"
        text = f"""
set_variable = {{ name = lyd_c2_check_count value = 0 }}
{faith} = {{
    every_faith_character = {{
        limit = {{ rite = scope:lyd_c2_actor.{rite} }}
        if = {{ limit = {{ lyd_c2_elector_trigger = yes }} scope:lyd_c2_actor = {{ change_variable = {{ name = lyd_c2_check_count add = 1 }} }} }}
        if = {{ limit = {{ is_ai = no is_alive = yes }} scope:lyd_c2_actor = {{ change_variable = {{ name = lyd_c2_check_players add = 1 }} }} }}
    }}
}}
if = {{ limit = {{ var:lyd_c2_check_count != var:lyd_c2_{side}_total }} set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
every_in_list = {{
    variable = lyd_c2_{side}_electors
    if = {{
                limit = {{ OR = {{ NOT = {{ lyd_c2_elector_trigger = yes }} rite != scope:lyd_c2_actor.{rite}
                    NOT = {{ has_variable = lyd_c2_elector_owner }}
                    NOT = {{ var:lyd_c2_elector_owner = scope:lyd_c2_actor }}
                    NOT = {{ var:lyd_c2_elector_serial = scope:lyd_c2_actor.var:lyd_c2_serial }}
                    NOT = {{ rite = var:lyd_c2_elector_rite }}
                }} }}
        scope:lyd_c2_actor = {{ set_variable = {{ name = lyd_c2_snapshot_valid value = 0 }} }}
    }}
}}
"""
        result.append(guarded_side(side, text))
    result.append("""
if = { limit = { var:lyd_c2_kind = 1 }
    set_variable = { name = lyd_c2_check_rites value = 0 }
    set_variable = { name = lyd_c2_active_receivers value = 0 }
    set_variable = { name = lyd_c2_mandated_receivers value = 0 }
    set_variable = { name = lyd_c2_unorganized_receivers value = 0 }
    var:lyd_c2_target_faith = { every_faith_rite = { scope:lyd_c2_actor = { change_variable = { name = lyd_c2_check_rites add = 1 } } } }
    if = { limit = { var:lyd_c2_check_rites != var:lyd_c2_target_rite_total } set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
    every_in_list = { variable = lyd_c2_target_rites
        save_scope_as = lyd_c2_target_school
        set_variable = { name = lyd_c2_check_count value = 0 }
        set_variable = { name = lyd_c2_check_followers value = 0 }
        scope:lyd_c2_actor.var:lyd_c2_target_faith = {
            every_faith_character = { limit = { rite = scope:lyd_c2_target_school }
                if = { limit = { is_alive = yes }
                    scope:lyd_c2_target_school = { change_variable = { name = lyd_c2_check_followers add = 1 } }
                }
                if = { limit = { lyd_c2_elector_trigger = yes }
                    scope:lyd_c2_target_school = { change_variable = { name = lyd_c2_check_count add = 1 } }
                }
                if = { limit = { is_ai = no is_alive = yes }
                    scope:lyd_c2_actor = { change_variable = { name = lyd_c2_check_players add = 1 } }
                }
            }
        }
        if = { limit = { OR = {
            var:lyd_c2_check_count != var:lyd_c2_target_total
            var:lyd_c2_check_followers != var:lyd_c2_target_followers
            faith != scope:lyd_c2_actor.var:lyd_c2_target_faith
        } } scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } } }
        if = { limit = { NOT = { lyd_c2_dormant_receiving_rite_trigger = yes } }
            scope:lyd_c2_actor = { change_variable = { name = lyd_c2_active_receivers add = 1 } }
            if = { limit = { lyd_c2_receiver_rite_quorum_trigger = { ACTOR = scope:lyd_c2_actor } }
                scope:lyd_c2_actor = { change_variable = { name = lyd_c2_mandated_receivers add = 1 } }
            }
            if = { limit = { var:lyd_c2_target_total = 0 NOT = { head_of_rite = { is_alive = yes is_adult = yes NOT = { has_trait = incapable } rite = scope:lyd_c2_target_school } } }
                scope:lyd_c2_actor = { change_variable = { name = lyd_c2_unorganized_receivers add = 1 } }
            }
        }
    }
    every_in_list = { variable = lyd_c2_target_electors
        if = { limit = { OR = {
            NOT = { lyd_c2_elector_trigger = yes }
            faith != scope:lyd_c2_actor.var:lyd_c2_target_faith
            NOT = { has_variable = lyd_c2_elector_owner }
            NOT = { var:lyd_c2_elector_owner = scope:lyd_c2_actor }
            NOT = { var:lyd_c2_elector_serial = scope:lyd_c2_actor.var:lyd_c2_serial }
            NOT = { rite = var:lyd_c2_elector_rite }
        } } scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } } }
    }
    every_in_list = { variable = lyd_c2_target_followers
        if = { limit = { OR = {
            is_alive = no
            faith != scope:lyd_c2_actor.var:lyd_c2_target_faith
            NOT = { has_variable = lyd_c2_follower_owner }
            NOT = { var:lyd_c2_follower_owner = scope:lyd_c2_actor }
            NOT = { var:lyd_c2_follower_serial = scope:lyd_c2_actor.var:lyd_c2_serial }
            NOT = { rite = var:lyd_c2_follower_rite }
        } } scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } } }
    }
}
if = { limit = { var:lyd_c2_check_players != var:lyd_c2_player_total } set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
every_in_list = {
    variable = lyd_c2_players
    if = {
        limit = {
            OR = {
                is_ai = yes is_alive = no
                NOR = {
                    rite = scope:lyd_c2_actor.var:lyd_c2_moving_rite
                    AND = { scope:lyd_c2_actor = { has_variable = lyd_c2_target_faith } faith = scope:lyd_c2_actor.var:lyd_c2_target_faith }
                }
                NOT = { has_variable = lyd_c2_affected_owner }
                NOT = { has_variable = lyd_c2_affected_serial }
                NOT = { var:lyd_c2_affected_owner = scope:lyd_c2_actor }
                NOT = { var:lyd_c2_affected_serial = scope:lyd_c2_actor.var:lyd_c2_serial }
                NOT = { rite = var:lyd_c2_affected_rite }
            }
        }
        scope:lyd_c2_actor = { set_variable = { name = lyd_c2_snapshot_valid value = 0 } }
    }
}
""")
    return "\n".join(result)


def native_admission(receipt_path: Path | None = None) -> dict:
    """Validate binding of a root attestation, never infer live success ourselves."""
    if receipt_path is None:
        return {"admitted": False, "status": NATIVE_PRIMITIVE_STATUS, "receipt": None}
    receipt_path = receipt_path.resolve()
    receipt_bytes = receipt_path.read_bytes()
    record = json.loads(receipt_bytes.decode("utf-8-sig"))
    from native_admission_portable import SCHEMA, validate_portable
    if record.get("schema") == SCHEMA:
        return validate_portable(receipt_path, record, CHECKOUT)
    raise ValueError("Native receipt must use the permanent tracked primitive-only admission schema")


def build_outputs(*, native_evidence: Path | None = None,
                  include_shared: bool = True) -> dict[str, bytes]:
    """Return BOM UTF-8 runtime bytes; an orchestrator can delegate shared C3 files.

    None deliberately closes native admission. Formal builds explicitly pass
    DEFAULT_NATIVE_EVIDENCE, as the standalone CLI does by default.
    """
    admission = native_admission(native_evidence)
    replacements = {
        "@MIN_LEARNING@": str(POLICY.min_learning),
        "@NATIVE_ADMITTED@": "yes" if admission["admitted"] else "no",
        "@PROPOSAL_DAYS@": str(POLICY.proposal_days), "@RETRY_DAYS@": str(POLICY.retry_days),
        "@TRANSITION_DAYS@": str(POLICY.transition_days),
        "@JOIN_GOLD@": str(POLICY.join_gold), "@JOIN_PIETY@": str(POLICY.join_piety),
        "@DETACH_GOLD@": str(POLICY.detach_gold), "@DETACH_PIETY@": str(POLICY.detach_piety),
        "@QUORUM_NUMERATOR@": str(POLICY.quorum_numerator), "@QUORUM_DENOMINATOR@": str(POLICY.quorum_denominator),
        "@NPC_YES_WEIGHT@": "60", "@NPC_NO_WEIGHT@": "40",
        "@CLEAR_ROUND_FIELDS@": "\n".join(f"remove_variable = lyd_c2_{field}" for field in ROUND_FIELDS),
        "@CLEAR_ROUND_LISTS@": "\n".join(f"clear_variable_list = lyd_c2_{field}" for field in ROUND_LISTS),
        "@CAPTURE_TERMS@": capture_terms(), "@REFRESH_TERMS@": refresh_terms(),
        "@REFRESH_ELECTORATES@": refresh_electorates(),
    }
    outputs = {}
    for path in sorted(SOURCE.rglob("*.txt")):
        relative = path.relative_to(SOURCE).as_posix()
        if not include_shared and relative in SHARED_PATHS:
            continue
        text = path.read_text(encoding="utf-8-sig")
        for old, new in replacements.items():
            text = text.replace(old, new)
        if re.search(r"@[A-Z_]+@", text):
            raise ValueError(f"Unrendered template input: {relative}")
        text = "# GENERATED FILE: edit mod_li_yu_dao/tools/school_consent_templates or tools/gen_school_consent.py.\n" + text
        outputs[relative] = ("\n".join(line.rstrip() for line in text.splitlines()) + "\n").encode("utf-8-sig")
    for language, column in (("simp_chinese", 0), ("english", 1)):
        rows = [f"l_{language}:", " # GENERATED FILE: edit tools/gen_school_consent.py."]
        for key, values in LOC.items():
            value = values[column].replace("\\", "\\\\").replace('"', '\\"')
            rows.append(f' {key}:0 "{value}"')
        outputs[f"localization/{language}/lyd_c2_consent_l_{language}.yml"] = ("\n".join(rows) + "\n").encode("utf-8-sig")
    return outputs


def generate(output_root: Path = DEFAULT_OUTPUT, *, check: bool = False,
             native_evidence: Path | None = None, include_shared: bool = True) -> dict:
    output_root = output_root.resolve()
    if output_root == CHECKOUT or (CHECKOUT in output_root.parents and output_root != ROOT):
        raise ValueError("School consent output must be the mod root or outside the checkout")
    if output_root == ROOT and include_shared:
        raise ValueError("C3 owns shared runtime files: use gen_runtime.py for the formal mod root")
    admission = native_admission(native_evidence)
    outputs = build_outputs(native_evidence=native_evidence, include_shared=include_shared)
    mismatches = []
    for relative, payload in outputs.items():
        destination = output_root / relative
        if check:
            if not destination.is_file() or destination.read_bytes() != payload:
                mismatches.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    result = {
        "component": "school-consent", "baseline_commit": BASELINE_COMMIT,
        "game_reference": GAME_VERSION, "result": "MISMATCH" if mismatches else "PASS_OFFLINE_RENDER",
        "mismatches": mismatches, "native_primitive": admission["status"],
        "native_admission_default": False, "native_admission": admission, "live": "NOT_RUN",
        "include_shared": include_shared,
        "files": {relative: hashlib.sha256(payload).hexdigest() for relative, payload in sorted(outputs.items())},
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--without-shared", action="store_true",
                        help="Compatibility option; shared files are already delegated by default")
    parser.add_argument("--with-legacy-shared", action="store_true",
                        help="Render historical C2-only shared templates in an external candidate directory")
    parser.add_argument("--native-evidence", type=Path, default=DEFAULT_NATIVE_EVIDENCE,
                        help="Permanent tracked primitive-only R0002 admission (default: tools/reference receipt)")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.without_shared and args.with_legacy_shared:
        parser.error("Shared output options are mutually exclusive")
    result = generate(args.output_root, check=args.check, native_evidence=args.native_evidence,
                      include_shared=args.with_legacy_shared)
    if args.report:
        report_path = args.report.resolve()
        if report_path == CHECKOUT or CHECKOUT in report_path.parents:
            parser.error("Reports must remain outside the frozen checkout")
        if report_path.exists():
            parser.error("Report exists; use another append-only attempt path")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result["mismatches"]))


if __name__ == "__main__":
    raise SystemExit(main())
