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
      kCampaignRootGameRuleSelectionServiceSlotRva != 0x5754B48 ||
      kCampaignRootMonthlyGoldIncomeRva != 0x28DBE90 ||
      kCampaignRootDomainSizeRva != 0x260BA50 ||
      kCampaignRootDomainLimitRva != 0x260BA20 ||
      kCampaignRootPrimaryTitleRva != 0x25F3350 ||
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
                    "NativeCampaignRootCharacterInt32V1",
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
                    "ReadDirectLandedVassals",
                    "direct_landed_vassals_unavailable",
                    "ReadAdjacentExternalProvinceHolders",
                    "adjacent_external_province_holders_unavailable",
                    "ReadRelatedCharacterContexts",
                    "related_character_contexts_unavailable",
                    "ReadPrimaryTitleSuccession",
                    "primary_title_succession_unavailable",
                    "player_monthly_gold_income_unavailable",
                    "player_domain_unavailable",
                    "kCampaignRootDomainSizeRva",
                    "kCampaignRootDomainLimitRva",
                    "kCampaignRootMonthlyGoldIncomeRva",
                    "kLandedTitleSuccessionDataOffset = 0x278",
                    "CharacterBelongsToPlayerSubrealm",
                    "observed_id != full_id",
                    "second != first"}) ||
      !ContainsAll(serializer,
                   {"std::is_sorted(values.begin(), values.end(), "
                    "Utf8BytewiseLess)",
                    "\\\"schema_version\\\":1",
                    "\\\"selected_game_rule_tokens\\\"",
                    "\\\"native_selected_game_rule_token_count\\\"",
                    "\\\"direct_landed_vassal_character_ids\\\"",
                    "\\\"adjacent_external_province_holder_character_ids\\\"",
                    "\\\"related_character_contexts\\\"",
                    "\\\"primary_title_succession_character_ids\\\"",
                    "\\\"player_monthly_gold_income\\\"",
                    "\\\"player_domain_size\\\"",
                    "\\\"player_domain_limit\\\"",
                    "\\\"domain_size_rva\\\"",
                    "\\\"domain_limit_rva\\\"",
                    "\\\"monthly_gold_income_rva\\\"",
                    "\\\"relationship_role\\\"",
                    "\\\"unavailable_reason\\\"",
                    "\\\"provenance\\\""}) ||
      !ContainsAll(query_mailbox,
                   {"ExecuteCampaignRootContextMailboxQueryV1",
                    "ReadCampaignRootContextV1(",
                    "typed_available",
                    "typed_unavailable"}) ||
      !ContainsAll(common_mailbox_header,
                   {"twenty-nine fixed slots", "permitted_executor_nonary",
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
                    "\"domain_size_rva\": \"0x260BA50\"",
                    "\"domain_limit_rva\": \"0x260BA20\"",
                    "531558C7064BA9F24F2FDE278F2A5FEF7F495664F0437A0EF528E04FC8CAB8D8",
                    "\"row_stride\": \"0x30\"",
                    "\"related_character_contexts\"",
                    "\"primary_title_succession\"",
                    "\"player_monthly_gold_income\"",
                    "\"player_domain_capacity\"",
                    "\"data_offset\": \"0x278\"",
                    "\"direct_vassal_invariant\"",
                    "unsigned_utf8_bytewise_lexicographical",
                    "\"preserve_multiplicity\": true"}) ||
      !ContainsAll(fixture,
                   {"\"command_result_key\": \"campaign_root_context\"",
                    "\"mailbox_executor_slot\": "
                    "\"permitted_executor_nonary\"",
                    "\"all_or_nothing_readiness\": true",
                    "\"direct_landed_vassal_order\": "
                    "\"ascending_full_generation_character_id\"",
                    "\"adjacent_external_province_holder_order\": "
                    "\"ascending_full_generation_character_id_duplicate_free\"",
                    "\"related_character_context_order\": "
                    "\"ascending_full_generation_character_id_duplicate_free\"",
                    "\"related_character_context_all_or_nothing\": true",
                    "\"primary_title_succession_order\": "
                    "\"native_title_succession_order\"",
                    "\"player_monthly_gold_income_scale\": 100000",
                    "\"player_domain_size_minimum\": 0",
                    "\"player_domain_limit_minimum\": 1",
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
