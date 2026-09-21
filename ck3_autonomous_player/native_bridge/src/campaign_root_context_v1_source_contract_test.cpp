#include "xar_bridge/campaign_root_context_v1.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) {
      std::cerr << "missing source-contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 12) {
    std::cerr << "expected eleven source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto reader = ReadAll(argv[2]);
  const auto serializer = ReadAll(argv[3]);
  const auto query_mailbox = ReadAll(argv[4]);
  const auto common_mailbox_header = ReadAll(argv[5]);
  const auto common_mailbox_source = ReadAll(argv[6]);
  const auto adapter = ReadAll(argv[7]);
  const auto game_adapter = ReadAll(argv[8]);
  const auto bridge = ReadAll(argv[9]);
  const auto abi = ReadAll(argv[10]);
  const auto fixture = ReadAll(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      query_mailbox.empty() || common_mailbox_header.empty() ||
      common_mailbox_source.empty() || adapter.empty() ||
      game_adapter.empty() || bridge.empty() || abi.empty() ||
      fixture.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kCampaignRootContextV1Capability !=
          "game.command.query-campaign-root-context-v1" ||
      kCampaignRootContextV1Step != "query-campaign-root-context-v1" ||
      kCampaignRootContextV1GameVersion != "1.19.0.6" ||
      kCampaignRootContextV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      kCampaignRootContextV1BackendId !=
          "ck3-1.19.0.6-native-campaign-root-context-v1" ||
      kCampaignRootGovernmentFallbackSlotRva != 0x570CB50 ||
      kCampaignRootActiveCouncilTaskStorageSlotRva != 0x570C778 ||
      kCampaignRootActiveCouncilTaskFallbackSlotRva != 0x570C6D8 ||
      kCampaignRootGameRuleSelectionServiceSlotRva != 0x5754B48 ||
      kCampaignRootMonthlyGoldIncomeRva != 0x28DBE90 ||
      kCampaignRootHealthRva != 0x2619AD0 ||
      kCampaignRootDomainSizeRva != 0x260BA50 ||
      kCampaignRootDomainLimitRva != 0x260BA20 ||
      kCampaignRootHasTargetingFactionTriggerRva != 0x283FAE0 ||
      kCampaignRootCouncilPositionLookupRva != 0x23F7800 ||
      kCampaignRootCouncilActiveTaskIdsEnumeratorRva != 0x2666CD0 ||
      kCampaignRootCouncilValueProgressCurrentRva != 0x2D650A0 ||
      kCampaignRootCouncilValueProgressMaximumRva != 0x2D65390 ||
      kCampaignRootPrimaryTitleRva != 0x25F3350 ||
      kCampaignRootTitleProvinceRva != 0x20B6B20 ||
      kCampaignRootCapitalProvinceRva != 0x2606760 ||
      kCampaignRootImmediateLiegeRva != 0x2613480 ||
      kCampaignRootTopLiegeRva != 0x2613600 ||
      kCampaignRootGovernmentRva != 0x26165B0 ||
      kCampaignRootProvinceHolderCharacterIdRva != 0x220C3F0) {
    std::cerr << "compiled exact-build binding drifted\n";
    return 1;
  }

  if (!ContainsAll(header,
                   {"void **government_fallback_slot",
                    "NativeCampaignRootMonthlyGoldIncomeV1",
                    "NativeCampaignRootCharacterFixedPointV1",
                    "NativeCampaignRootCharacterInt32V1",
                    "CampaignRootCouncilPositionV1",
                    "CampaignRootCouncilStatusV1",
                    "auxiliary_vacancies_complete",
                    "NativeCampaignRootCouncilValueProgressV1",
                    "std::optional<std::int32_t> capital_province_id",
                    "NativeCampaignRootCharacterResolverV1 title_province",
                    "game.command.query-campaign-root-context-v1",
                    "ck3-1.19.0.6-native-campaign-root-context-v1"}) ||
      !ContainsAll(reader,
                   {"ReadSlot(access, environment.government_fallback_slot",
                    "Utf8BytewiseLess",
                    "static_cast<unsigned char>(left_byte)",
                    "std::sort(government.flags.begin(),",
                    "Utf8BytewiseLess);",
                    "std::sort(output.selected_game_rule_tokens.begin(),",
                    "selected_rule_tokens_native_order",
                    "selected_game_rule_tokens_available =",
                    "ReadSelectedRuleTokens(environment, access, output)",
                    "if (!output.selected_game_rule_tokens_available)",
                    "output.selected_game_rule_tokens.clear()",
                    "output.native_selected_game_rule_token_count = 0",
                    "output.readiness.selected_game_rule_tokens_ready =",
                    "output.readiness.ready = "
                    "first.selected_game_rule_tokens_available",
                    "ReadDirectLandedVassals",
                    "direct_landed_vassals_unavailable",
                    "ReadAdjacentExternalProvinceHolders",
                    "adjacent_external_province_holders_unavailable",
                    "ReadRelatedCharacterContexts",
                    "related_character_contexts_unavailable",
                    "ReadPrimaryTitleSuccession",
                    "primary_title_succession_unavailable",
                    "ReadHeldTitlePartition",
                    "environment.title_province",
                    "kCampaignRootTitleProvinceRva",
                    "base + kCampaignRootTitleProvinceRva",
                    "held_title_partition_unavailable",
                    "ReadCouncil",
                    "council_unavailable",
                    "government_is_celestial",
                    "player_monthly_gold_income_unavailable",
                    "player_health_unavailable",
                    "player_domain_unavailable",
                    "player_targeting_factions_unavailable",
                    "kCampaignRootDomainSizeRva",
                    "kCampaignRootDomainLimitRva",
                    "kCharacterLandStateOffset = 0x1B8",
                    "kLandStateTargetingFactionsCountOffset = 0x12C",
                    "kCampaignRootMonthlyGoldIncomeRva",
                    "kCampaignRootHealthRva",
                    "kLandedTitleSuccessionDataOffset = 0x278",
                    "kLandStateHeldTitleIdsOffset = 0x1E0",
                    "kLandStateActiveCouncilTaskIdsOffset = 0x230",
                    "kLandStateActiveCouncilTaskCountOffset = 0x23C",
                    "kActiveCouncilTaskScopesOffset = 0x38",
                    "kCouncilScopesTargetTagOffset = 0x08",
                    "kCouncilScopesTargetValueOffset = 0x10",
                    "kCouncilTaskTypeKeyOffset = 0x18",
                    "kCouncilTaskTypePositionTypeOffset = 0x38",
                    "ResolveCouncilProvinceTarget",
                    "InvokeCouncilValueProgress",
                    "kCoreCouncilPositionKeys",
                    "auxiliary_vacancies_complete = false",
                    "kLandedTitleHolderCharacterIdOffset = 0x258",
                    "CharacterBelongsToPlayerSubrealm",
                    "observed_id != full_id",
                    "second != first"}) ||
      !ContainsAll(serializer,
                   {"std::is_sorted(values.begin(), values.end(), "
                    "Utf8BytewiseLess)",
                    "\\\"schema_version\\\":1",
                    "\\\"selected_game_rule_tokens\\\"",
                    "\\\"native_selected_game_rule_token_count\\\"",
                    "ValidAvailableReadiness",
                    "value.ready == value.selected_game_rule_tokens_ready",
                    "!context.readiness.selected_game_rule_tokens_ready",
                    "!context.selected_game_rule_tokens.empty()",
                    "\\\"direct_landed_vassal_character_ids\\\"",
                    "\\\"adjacent_external_province_holder_character_ids\\\"",
                    "\\\"related_character_contexts\\\"",
                    "\\\"primary_title_succession_character_ids\\\"",
                    "\\\"held_title_partition\\\"",
                    "AppendOptionalInt32(output, row.capital_province_id)",
                    "\\\"title_province_rva\\\":\\\"0x20B6B20\\\"",
                    "\\\"held_title_partition_ready\\\"",
                    "\\\"council\\\"",
                    "\\\"council_ready\\\"",
                    "\\\"auxiliary_vacancies_complete\\\"",
                    "\\\"council_active_task_ids_enumerator_rva\\\"",
                    "\\\"council_value_progress_current_rva\\\"",
                    "\\\"player_monthly_gold_income\\\"",
                    "\\\"player_health\\\"",
                    "\\\"player_domain_size\\\"",
                    "\\\"player_domain_limit\\\"",
                    "\\\"player_targeting_faction_count\\\"",
                    "\\\"domain_size_rva\\\"",
                    "\\\"domain_limit_rva\\\"",
                    "\\\"has_targeting_faction_trigger_rva\\\"",
                    "\\\"monthly_gold_income_rva\\\"",
                    "\\\"character_health_rva\\\"",
                    "\\\"relationship_role\\\"",
                    "\\\"unavailable_reason\\\"",
                    "\\\"provenance\\\""}) ||
      !ContainsAll(query_mailbox,
                   {"ExecuteCampaignRootContextMailboxQueryV1",
                    "ReadCampaignRootContextV1(",
                    "typed_available",
                    "typed_unavailable"}) ||
      !ContainsAll(common_mailbox_header,
                   {"permitted_frontend_executor", "permitted_executor_nonary",
                    "permitted_executor_duodenary",
                    "permitted_executor_sexvigintary"}) ||
      !ContainsAll(common_mailbox_source,
                   {"environment.permitted_executor_nonary",
                    "mailbox.permitted_executor_nonary"}) ||
      !ContainsAll(adapter,
                   {"game.command.query-campaign-root-context-v1"}) ||
      !ContainsAll(game_adapter,
                   {"ParseCampaignRootContextV1Step",
                    "kCampaignRootContextV1Capability"}) ||
      !ContainsAll(bridge,
                   {"ExecuteCampaignRootContextMailboxQueryV1",
                    "permitted_executor_nonary",
                    "CampaignRootContextResultFrame",
                    "\\\"campaign_root_context\\\"",
                    "\\\"backend_id\\\":\\\"native-headless\\\"",
                    "ParseCampaignRootContextExpectedRevisionV1",
                    "completion_snapshot_stable"}) ||
      !ContainsAll(abi,
                   {"\"government_fallback_slot_rva\": \"0x570CB50\"",
                    "\"kind\": \"pointer_slot\"",
                    "\"instruction_rva\": \"0x2616664\"",
                    "mov rax, qword ptr [rip+0x30F64E5]",
                    "\"resolved_rva\": \"0x570CB50\"",
                    "\"province_holder_character_id_rva\": \"0x220C3F0\"",
                    "\"monthly_gold_income_rva\": \"0x28DBE90\"",
                    "\"health_rva\": \"0x2619AD0\"",
                    "\"domain_size_rva\": \"0x260BA50\"",
                    "\"domain_limit_rva\": \"0x260BA20\"",
                    "\"has_targeting_faction_trigger_rva\": \"0x283FAE0\"",
                    "531558C7064BA9F24F2FDE278F2A5FEF7F495664F0437A0EF528E04FC8CAB8D8",
                    "\"row_stride\": \"0x30\"",
                    "\"related_character_contexts\"",
                    "\"primary_title_succession\"",
                    "\"held_title_partition\"",
                    "\"title_province_rva\": \"0x20B6B20\"",
                    "\"published_field\": "
                    "\"held_title_partition[].capital_province_id\"",
                    "9A2A89B5B17FC268A799098790F099E970858C84E86D8D539D50AD916AFD820B",
                    "D7C6700177B5401E712DA7913FE46468C7868450A12488422005E5CBAAFB19A9",
                    "8D3696555ADB3F338244D1E8872C3721707D7B90EEE7E6AD95DD38020195EEA2",
                    "\"council\"",
                    "\"coverage_key\": \"standard_landed_non_nomadic_core_v1\"",
                    "\"data_offset\": \"0x230\"",
                    "\"count_offset\": \"0x23C\"",
                    "\"storage_slot_rva\": \"0x570C778\"",
                    "\"fallback_slot_rva\": \"0x570C6D8\"",
                    "E386DB4C0D6E816CF72A82F44C61D3438BCC689C247DB59EF8D447178E5DDEBB",
                    "1AF11F60D6173AAC65266C116B11C7F6E82FEC74F8AAC6974ADEBD657ABB0FD0",
                    "B09B2952F63E29621504B4B3CC333AF2C20A5F9521D737052834A285D3654497",
                    "D132CBD9FEC317C0FE88437D1AC1E232E90483CD3FF42FBAD1F08C4DDF9612DD",
                    "A35A4A73FF93C7B818D433558AD2F288016575AC2B2E3398DC779B1A1A97FA7E",
                    "4A555E79AEC9F4A4448B66E618A05A15A851111D29D76D64420284B7DB44D60E",
                    "D12BA93AA4CBFC6382DECBCA92B4BEED8CB02754CEE821D2B441A0320AF56ABF",
                    "\"player_monthly_gold_income\"",
                    "\"player_health\"",
                    "\"player_domain_capacity\"",
                    "\"player_targeting_factions\"",
                    "\"character_land_state_offset\": \"0x1B8\"",
                    "\"land_state_targeting_faction_count_offset\": \"0x12C\"",
                    "7A4C1EED3FF52B5573AD7598350DB3270954E38FB0F1CF872080851D4C00ECEE",
                    "\"data_offset\": \"0x278\"",
                    "\"direct_vassal_invariant\"",
                    "unsigned_utf8_bytewise_lexicographical",
                    "\"preserve_multiplicity\": true"}) ||
      !ContainsAll(fixture,
                   {"\"command_result_key\": \"campaign_root_context\"",
                    "\"mailbox_executor_slot\": "
                    "\"permitted_executor_nonary\"",
                    "\"all_or_nothing_readiness\": false",
                    "\"required_root_readiness_fields\"",
                    "\"optional_component_readiness_fields\"",
                    "\"aggregate_ready_semantics\": "
                    "\"selected_game_rule_tokens_ready_when_required_root_fields_are_ready\"",
                    "\"direct_landed_vassal_order\": "
                    "\"ascending_full_generation_character_id\"",
                    "\"adjacent_external_province_holder_order\": "
                    "\"ascending_full_generation_character_id_duplicate_free\"",
                    "\"related_character_context_order\": "
                    "\"ascending_full_generation_character_id_duplicate_free\"",
                    "\"related_character_context_all_or_nothing\": true",
                    "\"primary_title_succession_order\": "
                    "\"native_title_succession_order\"",
                    "\"held_title_partition_order\": "
                    "\"ascending_full_generation_landed_title_id\"",
                    "\"held_title_partition_all_or_nothing\": true",
                    "\"council_coverage_key\": "
                    "\"standard_landed_non_nomadic_core_v1\"",
                    "\"council_active_task_list_offsets\"",
                    "\"council_active_task_storage_slot_rva\": "
                    "\"0x570C778\"",
                    "\"council_active_task_fallback_slot_rva\": "
                    "\"0x570C6D8\"",
                    "\"council_all_materialized_positions_published\": true",
                    "\"council_auxiliary_vacancies_complete\": false",
                    "\"council_outside_scope_is_component_unavailable\": true",
                    "\"council_outside_scope_preserves_root_ready\": true",
                    "\"selected_game_rule_tokens_optional_component\": true",
                    "\"selected_game_rule_tokens_failure_root_status\": "
                    "\"available\"",
                    "\"selected_game_rule_tokens_failure_values\"",
                    "\"selected_game_rule_tokens\": []",
                    "\"native_selected_game_rule_token_count\": 0",
                    "\"selected_game_rule_tokens_ready\": false",
                    "\"ready\": false",
                    "\"unavailable_reason\": \"\"",
                    "\"selected_game_rule_tokens_same_frame\": "
                    "\"component_availability_and_complete_token_vector_count_two_sample_equality\"",
                    "\"player_monthly_gold_income_scale\": 100000",
                    "\"player_health_scale\": 100000",
                    "\"player_health_rva\": \"0x2619AD0\"",
                    "\"player_domain_size_minimum\": 0",
                    "\"player_domain_limit_minimum\": 1",
                    "\"player_targeting_faction_count_minimum\": 0",
                    "\"player_targeting_faction_trigger_rva\": \"0x283FAE0\"",
                    "\"government_fallback_kind\": \"pointer_slot\""})) {
    return 1;
  }

  if (Contains(reader, "WriteProcessMemory") ||
      Contains(reader, "SubmitPause") || Contains(reader, "SubmitMove") ||
      Contains(reader, "SubmitDeclare")) {
    std::cerr << "reader contains a mutator surface\n";
    return 1;
  }

  std::cout << "campaign-root-context-v1 source contract passed\n";
  return 0;
}
