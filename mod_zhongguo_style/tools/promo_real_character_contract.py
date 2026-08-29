#!/usr/bin/env python3
"""Frozen real-character allowlist for the ZhongGuo 361 promo capture.

The live fixture may select the previous review's actual tail at runtime, but
it may never manufacture or fall back to an anonymous character.  This module
is the shared Python-side contract used by both the CK3 recorder and the
release-manifest projector: a final capture resolves to exactly one manager
and one reviewed official from this frozen 1066 Song history set.
"""

from __future__ import annotations

from typing import Final


BOOKMARK: Final[dict[str, str]] = {
    "id": "1066_song",
    "start_date": "1066.9.15",
}

MANAGER_HISTORY_ID: Final[str] = "han_8052"
MANAGER_CONTRACT: Final[dict[str, object]] = {
    "subject_id": "song_emperor_zhao_shu",
    "history_id": MANAGER_HISTORY_ID,
    "display_name": "赵曙",
    "roles": ("manager", "emperor"),
    "title_id": "h_china",
    "holder_date": "1063.4.30",
}


def _official(
    display_name: str,
    title_id: str,
    holder_date: str,
    title_role: str,
    *,
    liege_title_id: str = "h_china",
    liege_holder_date: str = "1063.4.30",
) -> dict[str, object]:
    return {
        "display_name": display_name,
        "roles": ("reviewed_official", title_role),
        "title_id": title_id,
        "holder_date": holder_date,
        "liege_title_id": liege_title_id,
        "liege_holder_id": MANAGER_HISTORY_ID,
        "liege_holder_date": liege_holder_date,
    }


# Exact historical members of the 23-person runtime cohort: 18 provincial
# governors plus three historical prefects whose immediate title liege,
# d_biansong, is held by Zhao Shu. The two remaining members are game-generated
# city officials and are intentionally excluded from public provenance.
HISTORICAL_COHORT_CONTRACT: Final[dict[str, dict[str, object]]] = {
    "han_6875": _official("唐介", "k_hedong", "1066.1.1", "hedong_governor"),
    "han_6747": _official("赵承亮", "k_jiangxi", "1066.1.1", "jiangxi_governor"),
    "han_6442": _official("曾公亮", "k_shannan", "1066.1.1", "shannan_governor"),
    "han_5253": _official("吕居简", "k_hunan", "1066.1.1", "hunan_governor"),
    "han_6680": _official("程瑜", "k_xichuan", "1066.1.1", "xichuan_governor"),
    "han_6071": _official("陈贯", "k_xingyuan", "1066.1.1", "xingyuan_governor"),
    "han_6762": _official("范纯诚", "k_dongchuan", "1066.1.1", "dongchuan_governor"),
    "han_90011": _official("张诜", "k_kuizhou", "1066.1.1", "kuizhou_governor"),
    "han_6444": _official("石待用", "k_lingnan", "1066.1.1", "lingnan_governor"),
    "han_6162": _official("杨完", "k_lingxi", "1066.1.1", "lingxi_governor"),
    "han_6465": _official("王端", "k_jiangdong", "1066.1.1", "jiangdong_governor"),
    "han_6963": _official("蔡襄", "k_liangzhe", "1066.1.1", "liangzhe_governor"),
    "han_6547": _official("韩纲", "k_fujian", "1066.1.1", "fujian_governor"),
    "han_6443": _official("梁适", "k_huainan", "1066.1.1", "huainan_governor"),
    "han_20000": _official("卢士宗", "k_qingxu", "1066.1.1", "qingxu_governor"),
    "han_6774": _official("晁宗恪", "k_hebei", "1066.1.1", "hebei_governor"),
    "han_50001": _official("李参", "k_guannei", "1066.1.1", "guannei_governor"),
    "han_6318": _official("赵从诲", "k_henan", "1066.1.1", "henan_governor"),
    "han_7247": _official(
        "陆琪",
        "c_shanzhou",
        "1066.1.1",
        "shanzhou_prefect",
        liege_title_id="d_biansong",
        liege_holder_date="1066.1.1",
    ),
    "han_6928": _official(
        "施辩",
        "c_bozhou",
        "1066.1.1",
        "bozhou_prefect",
        liege_title_id="d_biansong",
        liege_holder_date="1066.1.1",
    ),
    "han_6927": _official(
        "吴中复",
        "c_yingzhou",
        "1066.1.1",
        "yingzhou_prefect",
        liege_title_id="d_biansong",
        liege_holder_date="1066.1.1",
    ),
}

# Counts and barons are assessed-only in the shipped product.  The continuous
# promo take later demonstrates manager-only policy cards as its reviewed
# subject, so that subject must be one of the 18 historical duke+ governors.
PROMO_REVIEWED_HISTORY_IDS: Final[tuple[str, ...]] = (
    "han_6875",
    "han_6747",
    "han_6442",
    "han_5253",
    "han_6680",
    "han_6071",
    "han_6762",
    "han_90011",
    "han_6444",
    "han_6162",
    "han_6465",
    "han_6963",
    "han_6547",
    "han_6443",
    "han_20000",
    "han_6774",
    "han_50001",
    "han_6318",
)
REVIEWED_OFFICIAL_CONTRACT: Final[dict[str, dict[str, object]]] = {
    history_id: HISTORICAL_COHORT_CONTRACT[history_id]
    for history_id in PROMO_REVIEWED_HISTORY_IDS
}

TARGET_DATA_MARKER_PREFIX: Final[str] = (
    "ZGA: DATA historical_personal_result_target "
)
TARGET_PASS_MARKER: Final[str] = (
    "ZGA: TEST PASS historical_personal_result_target"
)


def reviewed_official(history_id: str) -> dict[str, object]:
    """Return a detached canonical record for one allowed reviewed official."""

    try:
        raw = REVIEWED_OFFICIAL_CONTRACT[history_id]
    except KeyError as exc:
        raise ValueError(
            f"reviewed history id is outside the frozen allowlist: {history_id!r}"
        ) from exc
    return {
        "subject_id": f"song_reviewed_official_{history_id}",
        "history_id": history_id,
        "display_name": str(raw["display_name"]),
        "roles": list(raw["roles"]),
        "title_id": str(raw["title_id"]),
        "holder_date": str(raw["holder_date"]),
        "liege_title_id": str(raw["liege_title_id"]),
        "liege_holder_id": str(raw["liege_holder_id"]),
        "liege_holder_date": str(raw["liege_holder_date"]),
    }


def manager() -> dict[str, object]:
    """Return a detached canonical record for Zhao Shu."""

    return {
        **MANAGER_CONTRACT,
        "roles": list(MANAGER_CONTRACT["roles"]),
    }
