"""External iteration-2 proposal policy, not native or live acceptance."""

from dataclasses import dataclass

BASELINE_COMMIT = "588492d3dbf473226664220b722a04b66ae54bae"
GAME_VERSION = "1.20.0.3"
NATIVE_PRIMITIVE_STATUS = "NOT_YET_LIVE_VERIFIED"


@dataclass(frozen=True)
class ConsentPolicy:
    proposal_days: int = 365
    retry_days: int = 365
    transition_days: int = 1825
    min_learning: int = 15
    quorum_numerator: int = 2
    quorum_denominator: int = 3
    join_gold: int = 300
    join_piety: int = 1500
    detach_gold: int = 200
    detach_piety: int = 1000


POLICY = ConsentPolicy()
SAMPLE_RITES = (
    "lyd_rite_kongmen", "lyd_rite_mengzi", "lyd_rite_xunzi",
    "lyd_rite_zhengxuan", "lyd_rite_wangsu", "lyd_rite_jingshu",
    "lyd_rite_zhuxi", "lyd_rite_lujiuyuan",
)

# Kept as explicit contracts until native prototype observations allow admission.
# No controller may silently clear an old HoF title, change core tenets, or replace
# the receiving main rite to make one of these constraints pass.
NATIVE_CONTRACTS = (
    "same religion: confucianism_religion",
    "preserve receiving main rite",
    "do not detach a current main/sole rite",
    "core tenets and head rules remain subject to native validation",
    "cross-faith pair divergence below 100 before and after migration",
    "no land/government/political-independence mutation",
    "only explicitly authorized, captured mod-owned HoF title retirement or temporal HoF provisioning; no rival-head helper",
)

STATE_FIELDS = {
    "rite": ("proposal_owner", "proposal_serial", "transition_until", "retry_until"),
    "proposal": (
        "actor", "moving_rite", "source_faith", "source_main", "source_head",
        "receiving_faith", "receiving_main", "receiving_head", "kind",
        "terms_revision", "deadline", "phase", "electorates", "mandates",
        "representative_signatures", "affected_players", "player_consents",
        "source_head_consent", "receiving_head_consent", "old_faith_permission",
        "dormant_receivers", "holder_endorsements", "target_rites",
    ),
}
