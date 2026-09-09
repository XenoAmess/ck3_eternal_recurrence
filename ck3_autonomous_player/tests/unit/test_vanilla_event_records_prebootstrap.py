from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TOOLS = REPOSITORY_ROOT / "tools"
AUTOPLAYER_SOURCE = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SOURCE) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SOURCE))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_zg361_phase2_seed_capture as source
from xar_autoplayer.vanilla_events.records_prebootstrap import (
    PREBOOTSTRAP_VANILLA_OBSERVATION_METADATA,
    PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS,
)


def test_original_prebootstrap_contracts_normalize_without_project_ownership() -> None:
    hook_source = source.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
    no_secrets_source = source.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT

    assert set(PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS) == {
        hook_source["event_definition_key"],
        no_secrets_source["event_definition_key"],
    }
    assert PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS[
        hook_source["event_definition_key"]
    ] == {
        "date_raw": hook_source["date_raw"],
        "root_character_id": hook_source["root_character_id"],
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "character_to_hook": hook_source[
                "excluded_character_to_hook_ids"
            ],
        },
        "boolean_scopes": (),
        "option_count": hook_source["option_count"],
        "native_option_indices": tuple(range(hook_source["option_count"])),
        "selected_option_number": hook_source["selected_option_number"],
        "selected_native_option_index": hook_source[
            "selected_native_option_index"
        ],
        "max_occurrences": 1,
    }
    assert PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS[
        no_secrets_source["event_definition_key"]
    ] == {
        "date_raw": no_secrets_source["date_raw"],
        "root_character_id": no_secrets_source["root_character_id"],
        "character_scopes": {
            "councillor": no_secrets_source["councillor_character_id"],
            "councillor_liege": no_secrets_source[
                "councillor_liege_character_id"
            ],
            "target_character": no_secrets_source["target_character_id"],
        },
        "boolean_scopes": (no_secrets_source["required_boolean_scope"],),
        "option_count": no_secrets_source["option_count"],
        "native_option_indices": tuple(
            range(no_secrets_source["option_count"])
        ),
        "selected_option_number": no_secrets_source[
            "selected_option_number"
        ],
        "selected_native_option_index": no_secrets_source[
            "selected_native_option_index"
        ],
        "max_occurrences": 1,
    }

    for event_key, contract in PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS.items():
        assert event_key.startswith("spymaster_task.")
        assert "event_definition_key" not in contract
        assert "source_save_sha256" not in contract
        assert "source_save_sha256s" not in contract


def test_observation_metadata_preserves_source_save_provenance() -> None:
    hook_source = source.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
    no_secrets_source = source.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT

    assert PREBOOTSTRAP_VANILLA_OBSERVATION_METADATA == {
        hook_source["event_definition_key"]: {
            "source_save_sha256s": (hook_source["source_save_sha256"],),
        },
        no_secrets_source["event_definition_key"]: {
            "source_save_sha256s": no_secrets_source[
                "source_save_sha256s"
            ],
        },
    }
    assert no_secrets_source["source_save_sha256"] == (
        PREBOOTSTRAP_VANILLA_OBSERVATION_METADATA[
            no_secrets_source["event_definition_key"]
        ]["source_save_sha256s"][0]
    )
