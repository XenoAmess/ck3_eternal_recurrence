#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "ck3_12002_campaign_test_support.hpp"

namespace {
bool AllReadiness(const xar::game::CampaignRootReadinessV1 &value,
                  bool expected) {
  return value.player_identity_ready == expected &&
         value.player_monthly_gold_income_ready == expected &&
         value.player_health_ready == expected &&
         value.player_domain_ready == expected &&
         value.player_targeting_factions_ready == expected &&
         value.primary_title_ready == expected &&
         value.primary_title_succession_ready == expected &&
         value.held_title_partition_ready == expected &&
         value.capital_ready == expected &&
         value.lieges_ready == expected &&
         value.direct_landed_vassals_ready == expected &&
         value.adjacent_external_province_holders_ready == expected &&
         value.related_character_contexts_ready == expected &&
         value.government_ready == expected &&
         value.selected_game_rule_tokens_ready == expected &&
         value.same_frame_ready == expected && value.ready == expected;
}

bool ClearedUnavailable(const xar::game::CampaignRootContextV1 &value,
                        std::string_view reason) {
  return value.status ==
             xar::game::CampaignRootContextStatusV1::unavailable &&
         value.snapshot_revision == 41 && value.date_raw == 12'345 &&
         !value.local_player_id && !value.player_character_id &&
         !value.player_character_alive && !value.primary_title &&
         !value.player_monthly_gold_income &&
         !value.player_health &&
         !value.player_domain_size && !value.player_domain_limit &&
         !value.player_targeting_faction_count &&
         !value.council &&
         value.primary_title_succession_character_ids.empty() &&
         value.held_title_partition.empty() &&
          !value.capital_province_id && !value.immediate_liege_character_id &&
         !value.top_liege_character_id && !value.independent &&
         value.direct_landed_vassal_character_ids.empty() &&
         value.adjacent_external_province_holder_character_ids.empty() &&
         value.related_character_contexts.empty() &&
         !value.government && value.selected_game_rule_tokens.empty() &&
         value.native_selected_game_rule_token_count == 0 &&
         AllReadiness(value.readiness, false) &&
         value.unavailable_reason == reason;
}

bool TestAvailableAndSerializer() {
  Fixture fixture;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  const std::vector<xar::game::CampaignRootRelatedCharacterV1>
      expected_related{
          {Fixture::kDirectVassalId,
           "direct_landed_vassal",
           {Fixture::kDirectVassalTitleId, 6, "hegemony"},
           7,
           Fixture::kPlayerCharacterId,
           Fixture::kTopLiegeId,
           false},
          {Fixture::kExternalProvinceHolderId,
           "adjacent_external_province_holder",
           {Fixture::kExternalProvinceHolderTitleId, 6, "hegemony"},
           6,
           std::nullopt,
           Fixture::kExternalProvinceHolderId,
           true}};
  const std::vector<xar::game::CampaignRootHeldTitleSuccessionV1>
      expected_partition{
          {{Fixture::kPrimaryTitleId, 6, "hegemony"},
           Fixture::kFirstSuccessorId,
           std::nullopt,
           true},
          {{Fixture::kSecondaryTitleId, 2, "county"},
           Fixture::kSecondSuccessorId,
           5,
           false}};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.status != xar::game::CampaignRootContextStatusV1::available ||
      result.snapshot_revision != 41 || result.date_raw != 12'345 ||
      result.local_player_id != 7 ||
      result.player_character_id != Fixture::kPlayerCharacterId ||
      result.player_character_alive != true ||
      result.player_monthly_gold_income !=
          xar::game::FixedPointValue{570'772, 100'000} ||
      fixture.monthly_income_calls != 2 ||
      result.player_health != xar::game::FixedPointValue{275'000, 100'000} ||
      !result.player_legitimacy_v1 ||
      result.player_legitimacy_v1->value !=
          xar::game::FixedPointValue{8'000'000, 100'000} ||
      !result.player_legitimacy_v1->unavailable_reason.empty() ||
      fixture.health_calls != 2 || result.player_domain_size != 6 ||
      result.player_domain_limit != 7 || fixture.domain_size_calls != 2 ||
      fixture.domain_limit_calls != 2 ||
      result.player_targeting_faction_count != 2 || !result.council ||
      result.council->status !=
          xar::game::CampaignRootCouncilStatusV1::available ||
      result.council->owner_character_id != Fixture::kPlayerCharacterId ||
      result.council->coverage_key !=
          "standard_landed_non_nomadic_core_v1" ||
      result.council->auxiliary_vacancies_complete ||
      result.council->positions.size() != 5 ||
      fixture.council_value_current_calls != 2 ||
      fixture.council_value_maximum_calls != 2 ||
      !result.readiness.council_ready || !result.primary_title ||
      result.primary_title->title_id != Fixture::kPrimaryTitleId ||
      result.primary_title->tier_raw != 6 ||
      result.primary_title->tier_key != "hegemony" ||
      result.primary_title_succession_character_ids !=
          std::vector<std::int32_t>{Fixture::kFirstSuccessorId,
                                    Fixture::kSecondSuccessorId} ||
      result.held_title_partition != expected_partition ||
      result.capital_province_id != 5 ||
      result.immediate_liege_character_id != Fixture::kImmediateLiegeId ||
      result.top_liege_character_id != Fixture::kTopLiegeId ||
      result.independent != false || !result.government ||
      result.direct_landed_vassal_character_ids !=
          std::vector<std::int32_t>{Fixture::kDirectVassalId} ||
      result.adjacent_external_province_holder_character_ids !=
          std::vector<std::int32_t>{Fixture::kExternalProvinceHolderId} ||
      result.related_character_contexts != expected_related ||
      result.government->key != "feudal_government" ||
      result.government->native_flag_count != 4 ||
      result.native_selected_game_rule_token_count != 4 ||
      !AllReadiness(result.readiness, true) ||
      !result.unavailable_reason.empty()) {
    return false;
  }
  const std::vector<std::string> expected_flags{
      "a_flag", "a_flag", std::string("\xC3\xA9", 2) + "_flag",
      NonAsciiFlag()};
  const std::vector<std::string> expected_rules{
      "a_rule", "a_rule", "z_rule", NonAsciiRule()};
  if (result.government->flags != expected_flags ||
      result.selected_game_rule_tokens != expected_rules) {
    return false;
  }
  const auto &council = result.council->positions;
  if (council[0].position_key != "councillor_chancellor" ||
      council[0].incumbent_character_id != Fixture::kDirectVassalId ||
      council[0].task_key != "task_foreign_affairs" ||
      council[0].task_type !=
          xar::game::CampaignRootCouncilTaskTypeV1::general ||
      council[0].target.has_value() || council[0].frozen != false ||
      !council[0].progress ||
      council[0].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::infinite ||
      council[0].progress->current.has_value() ||
      council[0].progress->maximum.has_value() ||
      council[1].position_key != "councillor_court_chaplain" ||
      council[1].incumbent_character_id.has_value() ||
      council[2].position_key != "councillor_marshal" ||
      council[2].incumbent_character_id.has_value() ||
      council[3].position_key != "councillor_spymaster" ||
      !council[3].target ||
      council[3].target->character_id !=
          Fixture::kExternalProvinceHolderId ||
      !council[3].progress ||
      council[3].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::percentage ||
      council[3].progress->current !=
          xar::game::FixedPointValue{5'000'000, 100'000} ||
      council[3].progress->maximum !=
          xar::game::FixedPointValue{10'000'000, 100'000} ||
      council[4].position_key != "councillor_steward" ||
      !council[4].target || council[4].target->province_id != 5 ||
      council[4].frozen != true || !council[4].progress ||
      council[4].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::value ||
      council[4].progress->current !=
          xar::game::FixedPointValue{4'200'000, 100'000} ||
      council[4].progress->maximum !=
          xar::game::FixedPointValue{10'000'000, 100'000}) {
    return false;
  }

  const auto json =
      xar::ck3_12002::SerializeCampaignRootContextV1(result);
  const std::string expected =
      "{\"schema_version\":1,\"status\":\"available\","
      "\"snapshot_revision\":41,\"date_raw\":12345,"
      "\"local_player_id\":7,\"player_character_id\":33554433,"
      "\"player_character_alive\":true,"
      "\"player_monthly_gold_income\":{\"raw\":570772,"
      "\"scale\":100000},\"player_monthly_piety_v1\":{"
      "\"status\":\"unavailable\",\"value\":null,"
      "\"unavailable_reason\":\"monthly_piety_unavailable\"},"
      "\"player_health\":{\"raw\":275000,"
      "\"scale\":100000},\"player_legitimacy_v1\":{"
      "\"status\":\"available\",\"value\":{\"raw\":8000000,"
      "\"scale\":100000},\"unavailable_reason\":null},"
      "\"player_max_monthly_gold_maintenance_v1\":{"
      "\"status\":\"unavailable\",\"value\":null,"
      "\"unavailable_reason\":\"getter_unavailable\"},"
      "\"player_domain_size\":6,"
      "\"player_domain_limit\":7,"
      "\"player_targeting_faction_count\":2,\"council\":{"
      "\"status\":\"available\",\"coverage_key\":"
      "\"standard_landed_non_nomadic_core_v1\","
      "\"owner_character_id\":33554433,\"positions\":[{"
      "\"position_key\":\"councillor_chancellor\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_foreign_affairs\",\"task_type\":\"general\","
      "\"target\":null,\"frozen\":false,\"progress\":{"
      "\"kind\":\"infinite\",\"current\":null,\"maximum\":null},"
      "\"task_owner_monthly_piety_v1\":{\"status\":\"unavailable\","
      "\"value\":null,\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}},{"
      "\"position_key\":\"councillor_court_chaplain\","
      "\"incumbent_character_id\":null,\"task_key\":null,"
      "\"task_type\":null,\"target\":null,\"frozen\":null,"
      "\"progress\":null,\"task_owner_monthly_piety_v1\":{"
      "\"status\":\"unavailable\",\"value\":null,"
      "\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}},{"
      "\"position_key\":\"councillor_marshal\","
      "\"incumbent_character_id\":null,\"task_key\":null,"
      "\"task_type\":null,\"target\":null,\"frozen\":null,"
      "\"progress\":null,\"task_owner_monthly_piety_v1\":{"
      "\"status\":\"unavailable\",\"value\":null,"
      "\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}},{"
      "\"position_key\":\"councillor_spymaster\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_find_secrets\",\"task_type\":\"court\",\"target\":{"
      "\"kind\":\"character\",\"character_id\":167772167},"
      "\"frozen\":false,\"progress\":{\"kind\":\"percentage\","
      "\"current\":{\"raw\":5000000,\"scale\":100000},"
      "\"maximum\":{\"raw\":10000000,\"scale\":100000}},"
      "\"task_owner_monthly_piety_v1\":{\"status\":\"unavailable\","
      "\"value\":null,\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}},{"
      "\"position_key\":\"councillor_steward\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_develop_county\",\"task_type\":\"county\",\"target\":{"
      "\"kind\":\"province\",\"province_id\":5},\"frozen\":true,"
      "\"progress\":{\"kind\":\"value\",\"current\":{"
      "\"raw\":4200000,\"scale\":100000},\"maximum\":{"
      "\"raw\":10000000,\"scale\":100000}},"
      "\"task_owner_monthly_piety_v1\":{\"status\":\"unavailable\","
      "\"value\":null,\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}}],"
      "\"auxiliary_vacancies_complete\":false,"
      "\"unavailable_reason\":null},\"primary_title\":{"
      "\"title_id\":83886081,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},"
      "\"primary_title_succession_character_ids\":[201326600,218103817],"
      "\"held_title_partition\":[{\"title\":{\"title_id\":83886081,"
      "\"tier_raw\":6,\"tier_key\":\"hegemony\"},"
      "\"first_heir_character_id\":201326600,"
      "\"capital_province_id\":null,\"primary\":true},{"
      "\"title\":{\"title_id\":234881028,\"tier_raw\":2,"
      "\"tier_key\":\"county\"},\"first_heir_character_id\":"
      "218103817,\"capital_province_id\":5,\"primary\":false}],"
      "\"capital_province_id\":5,"
      "\"immediate_liege_character_id\":50331650,"
      "\"top_liege_character_id\":67108867,\"independent\":false,"
      "\"direct_landed_vassal_character_ids\":[100663300],"
      "\"adjacent_external_province_holder_character_ids\":[167772167],"
      "\"related_character_contexts\":[{\"character_id\":100663300,"
      "\"relationship_role\":\"direct_landed_vassal\","
      "\"primary_title\":{\"title_id\":150994946,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},\"capital_province_id\":7,"
      "\"immediate_liege_character_id\":33554433,"
      "\"top_liege_character_id\":67108867,\"independent\":false},{"
      "\"character_id\":167772167,\"relationship_role\":"
      "\"adjacent_external_province_holder\",\"primary_title\":{"
      "\"title_id\":184549379,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},\"capital_province_id\":6,"
      "\"immediate_liege_character_id\":null,"
      "\"top_liege_character_id\":167772167,\"independent\":true}],"
      "\"government\":{\"key\":\"feudal_government\",\"flags\":["
      "\"a_flag\",\"a_flag\",\"" +
      std::string("\xC3\xA9", 2) + "_flag\",\"" + NonAsciiFlag() +
      "\"],\"native_flag_count\":4},"
      "\"selected_game_rule_tokens\":[\"a_rule\",\"a_rule\","
      "\"z_rule\",\"" + NonAsciiRule() +
      "\"],\"native_selected_game_rule_token_count\":4,"
      "\"readiness\":{\"player_identity_ready\":true,"
      "\"player_monthly_gold_income_ready\":true,"
      "\"player_health_ready\":true,"
      "\"player_domain_ready\":true,"
      "\"player_targeting_factions_ready\":true,"
      "\"primary_title_ready\":true,"
      "\"primary_title_succession_ready\":true,"
      "\"held_title_partition_ready\":true,"
      "\"council_ready\":true,"
      "\"capital_ready\":true,"
      "\"lieges_ready\":true,\"direct_landed_vassals_ready\":true,"
      "\"adjacent_external_province_holders_ready\":true,"
      "\"related_character_contexts_ready\":true,"
      "\"government_ready\":true,"
      "\"selected_game_rule_tokens_ready\":true,"
      "\"same_frame_ready\":true,\"ready\":true},"
      "\"unavailable_reason\":null,\"provenance\":{"
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":"
      "\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\","
      "\"backend_id\":\"ck3-1.20.0.2-native-campaign-root-context-v1\","
      "\"monthly_gold_income_rva\":\"0x2BCA960\","
      "\"character_health_rva\":\"0x28C6500\","
      "\"domain_size_rva\":\"0x28B7200\","
      "\"domain_limit_rva\":\"0x28B71D0\","
      "\"has_targeting_faction_trigger_rva\":\"0x2B250D0\","
      "\"council_position_lookup_rva\":\"0x2684F00\","
      "\"council_active_task_ids_enumerator_rva\":\"0x2916CE0\","
      "\"council_active_task_storage_slot_rva\":\"0x5D1DEA0\","
      "\"council_value_progress_current_rva\":\"0x31AB520\","
      "\"council_value_progress_maximum_rva\":\"0x31AB840\","
      "\"primary_title_rva\":\"0x289DA30\","
      "\"held_title_ids_offset\":\"0x1E0\","
      "\"title_province_rva\":\"0x230F900\","
      "\"capital_province_rva\":\"0x28B1CD0\","
      "\"immediate_liege_rva\":\"0x28BFC70\","
      "\"top_liege_rva\":\"0x28BFDA0\","
      "\"government_rva\":\"0x28C2E10\","
      "\"province_holder_character_id_rva\":\"0x247D030\","
      "\"selected_game_rule_service_slot_rva\":\"0x5CB3D78\"}}";
  if (json != expected) {
    return false;
  }
  auto unsorted = result;
  std::swap(unsorted.selected_game_rule_tokens.front(),
            unsorted.selected_game_rule_tokens.back());
  if (!xar::ck3_12002::SerializeCampaignRootContextV1(unsorted).empty()) {
    return false;
  }

  constexpr std::array<std::string_view, 5> tier_keys{
      "county", "duchy", "kingdom", "empire", "hegemony"};
  for (std::int32_t tier = 2; tier <= 6; ++tier) {
    Put(fixture.title_template, 0x64, tier);
    fixture.capture_calls = 0;
    result = {};
    if (xar::ck3_12002::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::available ||
        !result.primary_title || result.primary_title->tier_raw != tier ||
        result.primary_title->tier_key !=
            tier_keys[static_cast<std::size_t>(tier - 2)]) {
      return false;
    }
  }
  return true;
}

bool TestLegitimateAbsenceAndGovernmentPointerSlot() {
  Fixture fixture;
  fixture.resolved_primary_title = Address(fixture.title_fallback);
  const std::int32_t no_held_titles = 0;
  Put(fixture.player_land_state, 0x1EC, no_held_titles);
  fixture.resolved_capital = nullptr;
  fixture.resolved_immediate_liege = Address(fixture.character_fallback);
  fixture.resolved_top_liege = Address(fixture.player_character);
  fixture.resolved_government = Address(fixture.government_fallback);
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::available &&
         !result.primary_title && !result.capital_province_id &&
         result.primary_title_succession_character_ids.empty() &&
         result.held_title_partition.empty() &&
         !result.immediate_liege_character_id &&
         result.top_liege_character_id == Fixture::kPlayerCharacterId &&
         result.independent == true && !result.government &&
         result.council.has_value() &&
         result.council->status ==
             xar::game::CampaignRootCouncilStatusV1::unavailable &&
         !result.readiness.council_ready &&
         AllReadiness(result.readiness, true) &&
         !xar::ck3_12002::SerializeCampaignRootContextV1(result).empty();
}

bool TestMissingLegitimacyNeverBecomesZero() {
  Fixture fixture;
  void *no_legitimacy_data = nullptr;
  Put(fixture.player_character, 0x1C8, no_legitimacy_data);
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      !result.player_legitimacy_v1 ||
      result.player_legitimacy_v1->value.has_value() ||
      result.player_legitimacy_v1->unavailable_reason != "data_absent" ||
      !result.readiness.ready) {
    return false;
  }
  return xar::ck3_12002::SerializeCampaignRootContextV1(result).find(
             "\"player_legitimacy_v1\":{\"status\":\"unavailable\","
             "\"value\":null,\"unavailable_reason\":\"data_absent\"}") !=
         std::string::npos;
}

bool TestTypedUnavailableClearsPartialObservation() {
  Fixture fixture;
  fixture.frame.played_character_id = Fixture::kPlayerCharacterId +
                                      0x01000000;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result,
                          "player_character_generation_mismatch")) {
    return false;
  }
  const auto json =
      xar::ck3_12002::SerializeCampaignRootContextV1(result);
  return !json.empty() &&
         json.find("\"local_player_id\":null") != std::string::npos &&
         json.find("\"selected_game_rule_tokens\":[]") !=
             std::string::npos &&
         json.find("\"unavailable_reason\":"
                   "\"player_character_generation_mismatch\"") !=
             std::string::npos;
}

bool TestMalformedSuccessionIsTypedUnavailable() {
  Fixture fixture;
  fixture.primary_title_successors[1] = 0x0E00000A;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result,
                            "primary_title_succession_unavailable");
}

bool TestMalformedHeldTitlePartitionIsTypedUnavailable() {
  Fixture fixture;
  Put(fixture.secondary_title, 0x128, Fixture::kTopLiegeId);
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result, "held_title_partition_unavailable")) {
    return false;
  }

  Fixture missing_county_capital;
  missing_county_capital.title_province_available = false;
  const auto missing_environment = Environment(missing_county_capital);
  const auto missing_access = Access(missing_county_capital);
  result = {};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             missing_environment, missing_access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "held_title_partition_unavailable");
}

// Synthetic named family county: its Null capital is not its preferred-capital
// county. Keep the title and its separate heir in the complete partition.
void ConfigureLandlessFamilyCounty(Fixture &fixture) {
  fixture.family_county_null = true;
  Put(fixture.null_county_province, 0x10, std::int32_t{0});
  Put(fixture.null_county_province, 0x85C, std::uint32_t{0x4E756C6C});
  Put(fixture.secondary_title, 0x30, std::uint8_t{1});
  Put(fixture.secondary_title, 0x32, std::uint8_t{1});
  Put(fixture.secondary_title, 0x11C, std::int32_t{0});
  fixture.native_strings[Address(fixture.secondary_title_template, 0x18)] =
      "c_fixture_family";
}

bool TestLandlessFamilyCountyPreservesPartitionAndWire() {
  Fixture fixture;
  ConfigureLandlessFamilyCounty(fixture);
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          Environment(fixture), Access(fixture), {41}, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      !AllReadiness(result.readiness, true) ||
      result.held_title_partition.size() != 2 || result.capital_province_id != 5) {
    return false;
  }
  const auto &primary = result.held_title_partition[0];
  const auto &family = result.held_title_partition[1];
  const auto wire = xar::ck3_12002::SerializeCampaignRootContextV1(result);
  return primary.title.title_id == Fixture::kPrimaryTitleId && primary.primary &&
         !primary.landless_noble_family_no_province &&
         primary.native_title_key.empty() &&
         primary.first_heir_character_id == Fixture::kFirstSuccessorId &&
         family.title.title_id == Fixture::kSecondaryTitleId &&
         family.title.tier_raw == 2 && family.title.tier_key == "county" &&
         family.first_heir_character_id == Fixture::kSecondSuccessorId &&
         !family.primary && !family.capital_province_id &&
         family.landless_noble_family_no_province &&
         family.native_title_key == "c_fixture_family" &&
         wire.find("\"capital_province_id\":null,\"capital_province_kind\":"
                   "\"landless_noble_family_no_province\",\"title_key\":"
                   "\"c_fixture_family\",\"primary\":false") != std::string::npos;
}

bool TestUnprovenNullCountyFailsClosed() {
  for (int failure = 0; failure < 16; ++failure) {
    Fixture fixture;
    ConfigureLandlessFamilyCounty(fixture);
    switch (failure) {
    case 0: Put(fixture.secondary_title, 0x30, std::uint8_t{0}); break;
    case 1: Put(fixture.secondary_title, 0x32, std::uint8_t{0}); break;
    case 2: Put(fixture.secondary_title, 0x30, std::uint8_t{2}); break;
    case 3: Put(fixture.secondary_title, 0x32, std::uint8_t{2}); break;
    case 4: Put(fixture.secondary_title, 0x11C, std::int32_t{1}); break;
    case 5: Put(fixture.secondary_title, 0x11C, std::int32_t{-1}); break;
    case 6: Put(fixture.null_county_province, 0x85C, std::uint32_t{0x50726F76}); break;
    case 7: Put(fixture.null_county_province, 0x85C, std::uint32_t{0}); break;
    case 8: Put(fixture.null_county_province, 0x10, std::int32_t{-1}); break;
    case 9: fixture.native_strings[Address(fixture.secondary_title_template, 0x18)] = ""; break;
    case 10: fixture.native_strings[Address(fixture.secondary_title_template, 0x18)] = "d_fixture_family"; break;
    case 11: fixture.native_strings[Address(fixture.secondary_title_template, 0x18)] = "c_bad key"; break;
    case 12: fixture.failed_read_address = Address(fixture.secondary_title, 0x30); break;
    case 13: fixture.failed_read_address = Address(fixture.secondary_title, 0x32); break;
    case 14: fixture.failed_read_address = Address(fixture.secondary_title, 0x11C); break;
    case 15: fixture.native_strings.erase(Address(fixture.secondary_title_template, 0x18)); break;
    }
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_12002::ReadCampaignRootContextV1(
            Environment(fixture), Access(fixture), {41}, result) !=
            xar::game::ReadCampaignRootContextResultV1::unavailable ||
        !ClearedUnavailable(result, "held_title_partition_unavailable")) {
      std::cerr << "unproven Null county case " << failure << " failed\n";
      return false;
    }
  }
  Fixture changed;
  ConfigureLandlessFamilyCounty(changed);
  changed.family_key_changes_between_samples = true;
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             Environment(changed), Access(changed), {41}, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "state_changed");
}

bool TestMonthlyIncomeFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.monthly_income_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(
             result, "player_monthly_gold_income_unavailable");
}

bool TestHealthFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.health_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "player_health_unavailable");
}

bool TestDomainFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.domain_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "player_domain_unavailable");
}

bool TestCouncilDynamicPositionAndFailureBoundaries() {
  {
    Fixture fixture;
    fixture.native_strings[Address(fixture.chancellor_position_type, 0x18)] =
        "modded_councillor";
    const auto environment = Environment(fixture);
    const auto access = Access(fixture);
    const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_12002::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::available ||
        !result.council || result.council->positions.size() != 6 ||
        std::none_of(result.council->positions.begin(),
                     result.council->positions.end(),
                     [](const auto &position) {
                       return position.position_key == "modded_councillor" &&
                              position.incumbent_character_id.has_value();
                     }) ||
        std::none_of(result.council->positions.begin(),
                     result.council->positions.end(),
                     [](const auto &position) {
                       return position.position_key ==
                                  "councillor_chancellor" &&
                              !position.incumbent_character_id.has_value();
                     })) {
      return false;
    }
  }
  for (const int failure_case : {0, 1}) {
    Fixture fixture;
    if (failure_case == 0) {
      const std::uint16_t wrong_target_tag = 4;
      Put(fixture.steward_active_task, 0x48, wrong_target_tag);
    } else {
      fixture.active_task_ids[0] += 0x01000000;
    }
    const auto environment = Environment(fixture);
    const auto access = Access(fixture);
    const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_12002::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::unavailable ||
        !ClearedUnavailable(result, "council_unavailable")) {
      return false;
    }
  }
  Fixture drift;
  drift.council_value_progress_changes_between_samples = true;
  const auto environment = Environment(drift);
  const auto access = Access(drift);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "state_changed");
}

bool TestStoredVacantCouncilTasksPreserveRoot() {
  Fixture fixture;
  const std::int32_t absent_incumbent = -1;
  const std::int32_t zero_incumbent = 0;
  Put(fixture.steward_active_task, 0x40, absent_incumbent);
  Put(fixture.spymaster_active_task, 0x40, zero_incumbent);
  fixture.native_strings[Address(fixture.spymaster_position_type, 0x18)] =
      "councillor_spouse";
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      !result.council || result.council->positions.size() != 6 ||
      !AllReadiness(result.readiness, true)) {
    return false;
  }
  const auto vacant = [&result](std::string_view key) {
    return std::any_of(
        result.council->positions.begin(), result.council->positions.end(),
        [key](const auto &position) {
          return position.position_key == key &&
                 !position.incumbent_character_id.has_value() &&
                 !position.task_key.has_value() &&
                 !position.task_type.has_value() &&
                 !position.target.has_value() &&
                 !position.frozen.has_value() &&
                 !position.progress.has_value();
        });
  };
  if (!vacant("councillor_steward") || !vacant("councillor_spouse") ||
      xar::ck3_12002::SerializeCampaignRootContextV1(result).empty()) {
    return false;
  }
  Fixture malformed;
  const std::int32_t malformed_incumbent = -2;
  Put(malformed.steward_active_task, 0x40, malformed_incumbent);
  const auto malformed_environment = Environment(malformed);
  const auto malformed_access = Access(malformed);
  xar::game::CampaignRootContextV1 malformed_result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          malformed_environment, malformed_access, request,
          malformed_result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(malformed_result, "council_unavailable")) {
    return false;
  }
  Fixture wrong_owner;
  Put(wrong_owner.steward_active_task, 0x40, absent_incumbent);
  Put(wrong_owner.steward_active_task, 0x44, Fixture::kTopLiegeId);
  const auto wrong_owner_environment = Environment(wrong_owner);
  const auto wrong_owner_access = Access(wrong_owner);
  xar::game::CampaignRootContextV1 wrong_owner_result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             wrong_owner_environment, wrong_owner_access, request,
             wrong_owner_result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(wrong_owner_result, "council_unavailable");
}

bool TestCelestialCouncilIsOutsideStandardScope() {
  Fixture fixture;
  const auto identifier = fixture.identifier_names.find(20);
  if (identifier == fixture.identifier_names.end()) {
    return false;
  }
  fixture.native_strings[&identifier->second] = "government_is_celestial";
  // A celestial ministry does not use the standard five-seat council layout.
  // Keep an invalid standard task behind the scope gate to prove that the
  // reader does not dereference the incompatible representation.
  fixture.active_task_ids[0] += 0x01000000;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::available &&
         result.government.has_value() &&
         std::find(result.government->flags.begin(),
                   result.government->flags.end(),
                   "government_is_celestial") !=
             result.government->flags.end() &&
         result.council.has_value() &&
         result.council->status ==
             xar::game::CampaignRootCouncilStatusV1::unavailable &&
         result.council->unavailable_reason ==
             "outside_standard_landed_non_nomadic_core_scope" &&
         !result.readiness.council_ready &&
         AllReadiness(result.readiness, true);
}

bool TestUnavailableRuleTokensPreserveRootObservation() {
  Fixture fixture;
  fixture.resolved_selected_rule_set = nullptr;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.status !=
          xar::game::CampaignRootContextStatusV1::available ||
      !result.selected_game_rule_tokens.empty() ||
      result.native_selected_game_rule_token_count != 0 ||
      result.readiness.selected_game_rule_tokens_ready ||
      result.readiness.ready || !result.readiness.same_frame_ready ||
      !result.unavailable_reason.empty()) {
    return false;
  }
  auto complete_readiness = result.readiness;
  complete_readiness.selected_game_rule_tokens_ready = true;
  complete_readiness.ready = true;
  return AllReadiness(complete_readiness, true) &&
         !xar::ck3_12002::SerializeCampaignRootContextV1(result).empty();
}

bool TestTargetingFactionCountSemantics() {
  Fixture normal;
  auto environment = Environment(normal);
  auto access = Access(normal);
  std::int32_t focused_count = -1;
  if (!xar::ck3_12002::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kPlayerCharacterId, focused_count) ||
      focused_count != 2 ||
      xar::ck3_12002::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kImmediateLiegeId, focused_count)) {
    return false;
  }

  Fixture no_land_state;
  void *null_land_state = nullptr;
  Put(no_land_state.player_character, 0x1C0, null_land_state);
  no_land_state.resolved_primary_title = Address(no_land_state.title_fallback);
  environment = Environment(no_land_state);
  access = Access(no_land_state);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.player_targeting_faction_count != 0) {
    return false;
  }
  if (!xar::ck3_12002::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kPlayerCharacterId, focused_count) ||
      focused_count != 0) {
    return false;
  }

  Fixture malformed;
  const std::int32_t negative_count = -1;
  Put(malformed.player_land_state, 0x12C, negative_count);
  environment = Environment(malformed);
  access = Access(malformed);
  result = {};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result,
                            "player_targeting_factions_unavailable") &&
         !xar::ck3_12002::ReadCampaignRootTargetingFactionCountV1(
             environment, access, Fixture::kPlayerCharacterId,
             focused_count);
}

bool TestStateChangedAndUnsupportedBuild() {
  Fixture changed_fixture;
  changed_fixture.change_frame_on_second_capture = true;
  auto environment = Environment(changed_fixture);
  auto access = Access(changed_fixture);
  const xar::ck3_12002::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_12002::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result, "state_changed")) {
    return false;
  }

  Fixture unsupported_fixture;
  environment = Environment(unsupported_fixture);
  environment.exact_build_admitted = false;
  access = Access(unsupported_fixture);
  result = {};
  return xar::ck3_12002::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "unsupported_build");
}

bool TestMonthlyPietyOnly(const char *wire_path) {
  Fixture fixture;
  auto environment = Environment(fixture);
  environment.monthly_piety = &ResolveMonthlyPiety;
  xar::game::CampaignRootContextV1 result{};
  const auto observed = xar::ck3_12002::ReadCampaignRootContextV1(
      environment, Access(fixture), {41}, result);
  // Distinct synthetic markers, not additional balance/fulfillment queries.
  constexpr std::int64_t piety_balance_marker = 8'123'456;
  constexpr std::int64_t spiritual_fulfillment_marker = 470'000;
  if (observed != xar::game::ReadCampaignRootContextResultV1::available ||
      !result.readiness.ready || result.snapshot_revision != 41 ||
      result.date_raw != 12'345 ||
      result.player_character_id != Fixture::kPlayerCharacterId ||
      result.player_monthly_piety_v1 !=
          xar::game::FixedPointValue{-125'000, 100'000} ||
      fixture.monthly_piety_calls != 2 || fixture.capture_calls != 2 ||
      !result.player_monthly_gold_income ||
      result.player_monthly_piety_v1->raw ==
          result.player_monthly_gold_income->raw ||
      result.player_monthly_piety_v1->raw == piety_balance_marker ||
      result.player_monthly_piety_v1->raw == spiritual_fulfillment_marker) {
    std::cerr << "monthly piety signed current actor production read failed\n";
    return false;
  }
  const xar::game::AdapterDescriptor descriptor{
      "ck3-1.20.0.3-msvc-x64", "1.20.0.3",
      xar::ck3_12003::kExecutableSha256, "fixture-only", {}};
  const auto wire = xar::game::RenderCrozierBuildIdentity(
      xar::ck3_12002::SerializeCampaignRootContextV1(result), descriptor);
  const std::string_view expected =
      "\"player_monthly_piety_v1\":{\"status\":\"available\","
      "\"value\":{\"raw\":-125000,\"scale\":100000},"
      "\"unavailable_reason\":null}";
  if (wire.empty() || wire.find(expected) == std::string::npos ||
      wire.find("1.20.0.3") == std::string::npos ||
      wire.find(xar::ck3_12003::kExecutableSha256) == std::string::npos) {
    std::cerr << "monthly piety production serializer/render wire failed\n";
    return false;
  }
  std::ofstream destination(wire_path, std::ios::binary);
  if (!destination) {
    return false;
  }
  destination << wire << '\n';
  if (!destination.good()) {
    return false;
  }
  std::cout << "monthly-piety-only signed production reader/wire passed\n";
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc == 3 && std::string_view(argv[1]) == "--monthly-piety-only") {
    return TestMonthlyPietyOnly(argv[2]) ? 0 : 1;
  }
  if (!TestAvailableAndSerializer()) {
    std::cerr << "available reader/serializer fixture failed\n";
    return 1;
  }
  if (!TestMissingLegitimacyNeverBecomesZero()) {
    std::cerr << "missing legitimacy material fixture failed\n";
    return 1;
  }
  if (!TestLegitimateAbsenceAndGovernmentPointerSlot()) {
    std::cerr << "legitimate absence/pointer-slot fixture failed\n";
    return 1;
  }
  if (!TestTypedUnavailableClearsPartialObservation()) {
    std::cerr << "typed unavailable fixture failed\n";
    return 1;
  }
  if (!TestMalformedSuccessionIsTypedUnavailable()) {
    std::cerr << "malformed succession fixture failed\n";
    return 1;
  }
  if (!TestMalformedHeldTitlePartitionIsTypedUnavailable()) {
    std::cerr << "malformed held-title partition fixture failed\n";
    return 1;
  }
  if (!TestLandlessFamilyCountyPreservesPartitionAndWire() ||
      !TestUnprovenNullCountyFailsClosed()) {
    std::cerr << "landless family county partition fixture failed\n";
    return 1;
  }
  if (!TestMonthlyIncomeFailureIsTypedUnavailable()) {
    std::cerr << "monthly income fixture failed\n";
    return 1;
  }
  if (!TestHealthFailureIsTypedUnavailable()) {
    std::cerr << "player health fixture failed\n";
    return 1;
  }
  if (!TestDomainFailureIsTypedUnavailable()) {
    std::cerr << "domain capacity fixture failed\n";
    return 1;
  }
  if (!TestCouncilDynamicPositionAndFailureBoundaries()) {
    std::cerr << "council dynamic/failure fixture failed\n";
    return 1;
  }
  if (!TestStoredVacantCouncilTasksPreserveRoot()) {
    std::cerr << "stored vacant council task fixture failed\n";
    return 1;
  }
  if (!TestCelestialCouncilIsOutsideStandardScope()) {
    std::cerr << "celestial council scope fixture failed\n";
    return 1;
  }
  if (!TestUnavailableRuleTokensPreserveRootObservation()) {
    std::cerr << "optional selected-rule-token fixture failed\n";
    return 1;
  }
  if (!TestTargetingFactionCountSemantics()) {
    std::cerr << "targeting faction count fixture failed\n";
    return 1;
  }
  if (!TestStateChangedAndUnsupportedBuild()) {
    std::cerr << "frame/build fixture failed\n";
    return 1;
  }
  if (argc == 3 && std::string_view(argv[1]) == "--emit-fixture") {
    Fixture fixture;
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_12002::ReadCampaignRootContextV1(
            Environment(fixture), Access(fixture), {41}, result) !=
        xar::game::ReadCampaignRootContextResultV1::available) {
      return 1;
    }
    const auto json = xar::ck3_12002::SerializeCampaignRootContextV1(result);
    std::ofstream destination(argv[2], std::ios::binary);
    if (!destination || json.empty()) {
      return 1;
    }
    destination << json << '\n';
    if (!destination.good()) {
      return 1;
    }
  }
  std::cout << "campaign-root-context-v1 reader fixture passed\n";
  return 0;
}
