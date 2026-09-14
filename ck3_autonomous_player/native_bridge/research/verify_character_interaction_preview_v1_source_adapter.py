"""Verify the private exact-build interaction preview source adapter."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
PRIVATE_KEY = 'character_interaction_preview_v1_source_adapter'
UPSTREAM_KEY = 'character_interaction_preview_v1'
BASELINE = '24f14db60c887e4a6e04bc2f8e47e6ca95346b18'
EXE_SHA256 = '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
EXE_SIZE = 95206008

def load_json(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as stream:
        return json.load(stream)

def require_tokens(text: str, tokens: tuple[str, ...], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if not not missing:
        raise RuntimeError(f'{label} missing required tokens: {missing}')

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, help='optional frozen 1.19.0.6 executable to hash without launching')
    args = parser.parse_args()
    native_root = Path(__file__).resolve().parents[1]
    header_path = native_root / 'include/xar_bridge/character_interaction_preview_v1_source_adapter.hpp'
    source_path = native_root / 'src/character_interaction_preview_v1_source_adapter.cpp'
    test_path = native_root / 'src/character_interaction_preview_v1_source_adapter_test.cpp'
    abi_path = native_root / 'research/character_interaction_preview_v1_source_adapter_abi.json'
    upstream_abi_path = native_root / 'research/character_interaction_preview_v1_abi.json'
    contract_path = native_root / 'research/fixtures/character_interaction_preview_v1_source_adapter_contract.json'
    available_path = native_root / 'research/fixtures/character_interaction_preview_v1_source_adapter_available.json'
    header = header_path.read_text(encoding='utf-8')
    source = source_path.read_text(encoding='utf-8')
    test = test_path.read_text(encoding='utf-8')
    abi = load_json(abi_path)
    upstream = load_json(upstream_abi_path)
    contract = load_json(contract_path)
    available = load_json(available_path)
    if not abi['schema_version'] == 1:
        raise RuntimeError('source-contract check failed')
    if not abi['private_key'] == PRIVATE_KEY:
        raise RuntimeError('source-contract check failed')
    if not abi['upstream'] == {'private_key': UPSTREAM_KEY, 'baseline_commit': BASELINE, 'wire_status': 'private-core-only'}:
        raise RuntimeError('source-contract check failed')
    if not abi['exact_build']['executable_size'] == EXE_SIZE:
        raise RuntimeError('source-contract check failed')
    if not abi['exact_build']['executable_sha256'] == EXE_SHA256:
        raise RuntimeError('source-contract check failed')
    if not upstream['private_key'] == UPSTREAM_KEY:
        raise RuntimeError('source-contract check failed')
    if not upstream['exact_build']['executable_sha256'] == EXE_SHA256:
        raise RuntimeError('source-contract check failed')
    if not contract['schema_version'] == 1:
        raise RuntimeError('source-contract check failed')
    if not contract['private_key'] == PRIVATE_KEY:
        raise RuntimeError('source-contract check failed')
    if not contract['upstream_private_key'] == UPSTREAM_KEY:
        raise RuntimeError('source-contract check failed')
    if not contract['upstream_baseline_commit'] == BASELINE:
        raise RuntimeError('source-contract check failed')
    if not contract['exact_build']['executable_sha256'] == EXE_SHA256:
        raise RuntimeError('source-contract check failed')
    if not len(contract['required_source_semantics']) == 13:
        raise RuntimeError('source-contract check failed')
    if not len(contract['native_test_cases']) == 9:
        raise RuntimeError('source-contract check failed')
    if not len(contract['forbidden_surfaces']) == 6:
        raise RuntimeError('source-contract check failed')
    expected_entries = {'character_storage_slot_rva': '0x570C130', 'definition_database_getter_rva': '0x831890', 'stable_key_hash_rva': '0x3B8B000', 'loaded_definition_lookup_rva': '0x997930', 'construct_two_role_context_rva': '0x2C3EE50', 'refresh_context_rva': '0x2C40950', 'finalize_context_rva': '0x2C40B20', 'final_can_send_rva': '0x2C43F00', 'generic_cost_evaluator_rva': '0x2CDB7B0', 'auto_accept_trigger_evaluator_rva': '0x334C510', 'intermediary_raw_rva': '0x2C44220', 'recipient_raw_rva': '0x2C44320', 'outer_final_answer_rva': '0x2C43B40', 'human_player_predicate_rva': '0x28BCEB0', 'destroy_context_rva': '0x2C3F380'}
    if not abi['native_entries'] == expected_entries:
        raise RuntimeError('source-contract check failed')
    upstream_entries = upstream['native_entry_contract']
    for key, value in expected_entries.items():
        if key != 'human_player_predicate_rva':
            if not upstream_entries[key] == value:
                raise RuntimeError('source-contract check failed')
    surface = abi['surface']
    if not all((surface[key] is False for key in ('shared_cmake_modified', 'bridge_registration_modified', 'public_schema_modified', 'mcp_modified', 'action_or_command_surface_present', 'ck3_process_required_for_static_tests'))):
        raise RuntimeError('source-contract check failed')
    readiness = abi['readiness']
    if not all((readiness[key] is True for key in ('private_source_adapter_implemented', 'canonical_definition_lookup_wired', 'generation_bearing_roles_wired', 'owned_context_lifecycle_wired', 'final_can_send_wired', 'generic_costs_wired', 'final_acceptance_wired', 'same_frame_double_sample_inherited'))):
        raise RuntimeError('source-contract check failed')
    if not readiness['public_capability_registered'] is False:
        raise RuntimeError('source-contract check failed')
    if not readiness['production_query_live'] is False:
        raise RuntimeError('source-contract check failed')
    if not available['private_build'] is True:
        raise RuntimeError('source-contract check failed')
    if not available['read_only'] is True:
        raise RuntimeError('source-contract check failed')
    if not available['advertised'] is False:
        raise RuntimeError('source-contract check failed')
    if not available['action_surface_present'] is False:
        raise RuntimeError('source-contract check failed')
    if not available['status'] == 'available':
        raise RuntimeError('source-contract check failed')
    if not available['definition']['canonical_key'] == 'gift_interaction':
        raise RuntimeError('source-contract check failed')
    if not available['roles'] == {'actor_character_id': 16777218, 'recipient_character_id': 33554435}:
        raise RuntimeError('source-contract check failed')
    if not available['can_send'] is True:
        raise RuntimeError('source-contract check failed')
    if not len(available['costs']['entries']) == 10:
        raise RuntimeError('source-contract check failed')
    if not available['acceptance']['kind'] == 'ai_final':
        raise RuntimeError('source-contract check failed')
    if not available['acceptance']['outer_final_status_raw'] == 0:
        raise RuntimeError('source-contract check failed')
    if not available['readiness']['same_frame_ready'] is True:
        raise RuntimeError('source-contract check failed')
    require_tokens(header, ('"character_interaction_preview_v1_source_adapter"', 'kCharacterInteractionPreviewHumanPlayerPredicateRvaV1 = 0x28BCEB0', 'CharacterInteractionPreviewSourceOperationsV1', 'CharacterInteractionPreviewSourceStateV1', 'active_owned_context', 'terminal_cleanup_failure', 'BindCharacterInteractionPreviewSourceAdapterV1', 'ReadCharacterInteractionPreviewFromSourceAdapterV1'), 'header')
    require_tokens(source, ('kDefinitionAutoAcceptTriggerOffset = 0x2580', 'kDefinitionAutoAcceptScalarOffset = 0x2A48', 'kDefinitionCostBlockOffset = 0x38', 'kContextEventTargetScopeOffset = 0x08', 'database, data, size', 'recipient_character_id, nullptr, true', 'interaction_context, true', 'interaction_context, 1, 0, nullptr, nullptr', 'output.final_status_raw < 0 || output.final_status_raw > 2', 'state->terminal_cleanup_failure = true', 'ReadCharacterInteractionPreviewV1(state.core_environment'), 'source')
    require_tokens(test, ('TestAvailableFixture', 'TestAcceptanceBranchesAreNativeFinal', 'TestGenerationAndSampleDriftStayRed', 'TestCleanupFailureIsTerminal', 'TestBindingGateAndExactAddresses', 'state.completed_context_count == 2', 'fixture.destroy_calls == 2'), 'native test')
    combined_code = header + '\n' + source
    forbidden = ('SubmitCommand', 'submit_command', 'ConstructSendCharacterInteractionCommand', 'construct_send_character_interaction_command', 'ExecuteEffect', 'execute_effect')
    present = [token for token in forbidden if token in combined_code]
    if not not present:
        raise RuntimeError(f'forbidden action tokens present: {present}')
    if args.exe is not None:
        executable = args.exe.resolve()
        if not executable.is_file():
            raise RuntimeError(f'missing executable: {executable}')
        if not executable.stat().st_size == EXE_SIZE:
            raise RuntimeError('source-contract check failed')
        digest = hashlib.sha256(executable.read_bytes()).hexdigest().upper()
        if not digest == EXE_SHA256:
            raise RuntimeError('source-contract check failed')
    print('character_interaction_preview_v1 source contract: GREEN')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
