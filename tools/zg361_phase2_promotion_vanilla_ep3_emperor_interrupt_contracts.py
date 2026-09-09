#!/usr/bin/env python3
"""Exact vanilla Roads-to-Power emperor interrupts on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_emperor_yearly.2170": {
        # CK3 1.19.0.6 low-control county response. Both authored routes
        # install a 50-year county modifier, so there is no inert dismissal.
        # Route B additionally installs a 25-year character flag that raises
        # governor efficiency by five points. Route A avoids that persistent
        # cross-system character state and only adds influence when the
        # current government exposes that resource. R287 observed the exact
        # one-title/two-option frame on the switched manager lineage.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "our_county": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("our_county",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_emperor_yearly.2211": {
        # CK3 1.19.0.6 response to a vassal's claimed appointment prophecy.
        # Authored option A is hidden in the R250 frame, leaving B/D/C at
        # native indices 1/2/3. R355 has A and D hidden, leaving B/C at 1/3.
        # Those are the two exact vanilla projections for the observed ruler:
        # A/B depend on personality/superstition, while D additionally admits
        # a faith mismatch with the requesting vassal. B creates a favor hook
        # (or grants influence), D installs a 25-year modifier, and both A/B
        # alter appointment investment. Authored option C is the bounded
        # terminal route: it only transfers minor influence in opposite
        # directions and schedules no follow-up event, hook, modifier, or
        # appointment mutation. The .2210 caller saves its dynamic root as
        # vassal before sending .2211 to the liege, so bind that source
        # relation instead of one seed ID. Since independent vassals enter
        # .2210 through the vanilla yearly pool and own its cooldown, multiple
        # requests to the same liege remain valid within the product window.
        "date_raw": 53206512,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "vassal": (32904,),
        },
        "scope_types": {
            "potential_title": "landed_title",
            "liege": "character",
            "vassal": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "potential_title",
            "liege",
            "vassal",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 3,
                "native_option_indices": (1, 2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 2,
                "native_option_indices": (1, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_powerful_families.8012": {
        # CK3 1.19.0.6 response to a powerful family's offer to enter the
        # liege's losing war. The .8010 caller binds the offering character,
        # liege, and selected war, then installs a 15-year liege-wide flag.
        # Native0 accepts and adds the offering family to the war; native1
        # declines, grants only minor influence to that family, and schedules
        # no follow-up. R366 observed this exact three-scope/two-option frame.
        # Source SHA-256:
        # CA19D38CD1C45783E32CF59E21A212642EA407B2DDD8EDE2467DF50ED9F7BC7A.
        "date_raw": 53328600,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "generous_family": (32904,),
        },
        "scope_types": {
            "generous_family": "character",
            "liege": "character",
            "war": "war",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("generous_family", "liege", "war"),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
