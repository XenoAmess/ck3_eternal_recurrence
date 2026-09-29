#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"
#include "xar_bridge/current_battle_knight_v1.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

namespace {

xar::game::Snapshot g_outer_snapshot{};
xar::game::BattleControlSnapshot g_native_result{};
xar::game::BattleControlSnapshotStatus g_native_status =
    xar::game::BattleControlSnapshotStatus::available;
std::uint32_t g_snapshot_reads = 0;
std::uint32_t g_battle_reads = 0;

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

bool Contains(std::string_view text, std::string_view needle) {
  return text.find(needle) != std::string_view::npos;
}

xar::game::BattleControlRegimentEntrySnapshot MainEntry(
    std::string bucket, std::int32_t index, std::int32_t regiment_id,
    const xar::game::BattleControlArmyIdentitySnapshot &army,
    std::int64_t starting, std::int64_t current, std::int64_t soft) {
  xar::game::BattleControlRegimentEntrySnapshot result{};
  result.bucket = std::move(bucket);
  result.bucket_index = index;
  result.regiment_id = regiment_id;
  result.native_carmy_id = army.native_carmy_id;
  result.public_cunit_id = army.public_cunit_id;
  result.owner_character_id = army.owner_character_id;
  result.starting_raw = starting;
  result.current_fighting_raw = current;
  result.soft_casualties_raw = soft;
  result.fights_in_main_phase = true;
  result.hard_casualties_available = true;
  result.hard_casualties_raw = starting - current - soft;
  result.effective_max_size = 100;
  result.effective_siege_raw = 10'000;
  result.effective_damage_raw = 20'000;
  result.effective_toughness_raw = 30'000;
  result.effective_pursuit_raw = 40'000;
  result.effective_screen_raw = 50'000;
  result.entry_strength_raw = 60'000;
  return result;
}

xar::game::BattleControlSnapshot CompleteBattle() {
  xar::game::BattleControlSnapshot result{};
  result.status = xar::game::BattleControlSnapshotStatus::available;
  result.snapshot_revision = 9;
  result.observed_date_raw = 53'178'264;
  result.subject_public_cunit_id = 83'886'341;
  result.subject_native_carmy_id = 67'108'900;
  result.combat_id = 335'544'325;
  result.province_id = 2'586;
  result.selected_public_cunit_id = result.subject_public_cunit_id;
  result.selected_native_carmy_id = result.subject_native_carmy_id;
  result.selected_owner_character_id = 100;
  result.combat_province_id = result.province_id;
  result.side_index = 0;
  result.side_scope = "full_side";
  result.affected_public_cunit_ids_in_stored_order = {
      result.subject_public_cunit_id};
  result.side_flags.disallow_retreat = false;
  result.side_flags.allow_early_retreat = false;
  result.side_flags.skip_pursuit = false;
  result.legality.status = "available";
  result.legality.native_boolean = true;
  result.legality.phase_raw = 1;
  result.legality.phase = "main";
  result.legality.retreat_elapsed_baseline_date_raw = 53'177'904;
  result.legality.elapsed_whole_days = 15;
  result.legality.minimum_elapsed_whole_days_exclusive = 14;
  result.legality.landless_gate_allows_retreat = true;
  result.legality.legal_now = true;
  result.legality.earliest_day_gate_date_raw = 53'178'264;
  result.phase = "main";
  result.phase_raw = 1;
  result.phase_day = 2;
  result.winner_side = "none";
  result.winner_raw = -1;
  result.forced_winner_side = "none";
  result.forced_winner_raw = -1;
  result.finalized = false;
  result.battle_result_id = -1;
  result.base_combat_width = 1'000;
  result.final_combat_width = 950;
  result.roll_cadence_counter = 3;
  result.base_advantage_raw = -5'000'000'000;
  result.resolved_advantage_raw = 6'000'000'000;

  result.attacker.side_index = 0;
  result.attacker.role = "attacker";
  result.attacker.primary_participant_character_id = 100;
  result.attacker.selected_commander_character_id = -1;
  result.attacker.current_roll_points = 11;
  const xar::game::BattleControlArmyIdentitySnapshot attacker_army{
      67'108'900, 83'886'341, 100, result.combat_id};
  result.attacker.ordered_armies.push_back(attacker_army);
  result.attacker.levy_entries.push_back(
      MainEntry("levy", 0, 400, attacker_army,
                1'000'000, 700'000, 100'000));
  auto reserve =
      MainEntry("men_at_arms", 0, 401, attacker_army,
                500'000, 0, 0);
  reserve.fights_in_main_phase = false;
  reserve.hard_casualties_available = false;
  reserve.hard_casualties_raw = 0;
  reserve.knight_character_id_raw = 2'130'706'429;
  result.attacker.men_at_arms_entries.push_back(reserve);
  result.attacker.stored_current_fighting_raw = 700'000;
  result.attacker.stored_levy_current_fighting_raw = 700'000;
  result.attacker.stored_terminal_loss_baseline_raw = 1'500'000;
  result.attacker.stored_current_matches_derived = true;
  result.attacker.stored_levy_current_matches_derived = true;
  result.attacker.derived_current_fighting_raw = 700'000;
  result.attacker.derived_soft_casualties_raw = 100'000;
  result.attacker.derived_main_fighting_entry_hard_casualties_raw = 200'000;
  result.attacker.non_main_start_minus_current_minus_soft_raw = 500'000;
  result.attacker.participant_hard_ledger.push_back({0, 100, 200'000});
  result.attacker.participant_hard_total_raw = 200'000;
  result.attacker.side_strength_raw = 129'975;

  result.defender.side_index = 1;
  result.defender.role = "defender";
  result.defender.primary_participant_character_id = 200;
  result.defender.selected_commander_character_id = 201;
  result.defender.current_roll_points = 7;
  const xar::game::BattleControlArmyIdentitySnapshot defender_army{
      67'108'901, 357, 200, result.combat_id};
  result.defender.ordered_armies.push_back(defender_army);
  result.defender.levy_entries.push_back(
      MainEntry("levy", 0, 500, defender_army,
                800'000, 500'000, 100'000));
  result.defender.stored_current_fighting_raw = 500'000;
  result.defender.stored_levy_current_fighting_raw = 500'000;
  result.defender.stored_terminal_loss_baseline_raw = 800'000;
  result.defender.stored_current_matches_derived = true;
  result.defender.stored_levy_current_matches_derived = true;
  result.defender.derived_current_fighting_raw = 500'000;
  result.defender.derived_soft_casualties_raw = 100'000;
  result.defender.derived_main_fighting_entry_hard_casualties_raw = 200'000;
  result.defender.non_main_start_minus_current_minus_soft_raw = 0;
  result.defender.participant_hard_ledger.push_back({0, 200, 200'000});
  result.defender.participant_hard_total_raw = 200'000;
  result.defender.side_strength_raw = 65'172;
  result.battle_control_ready = true;
  return result;
}

xar::game::Snapshot CompleteOuterSnapshot() {
  xar::game::Snapshot result{};
  result.map_ready = true;
  result.paused = true;
  result.date_raw = 53'178'264;
  result.has_played_character = true;
  result.played_character_alive = true;
  result.played_character_id = 100;
  xar::game::ArmySnapshot subject{};
  subject.army_id = 83'886'341;
  subject.owner_character_id = 100;
  subject.has_current_province = true;
  subject.current_province_id = 2'586;
  subject.in_combat = true;
  subject.controllable = true;
  result.player_armies.push_back(subject);
  return result;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  ++g_snapshot_reads;
  output = g_outer_snapshot;
  return true;
}

game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &, const game::BattleControlRequest &,
    game::BattleControlSnapshot &output) noexcept {
  ++g_battle_reads;
  output = g_native_result;
  return g_native_status;
}

bool ReadCurrentBattleKnightV1(
    const Bindings &, const game::Snapshot &,
    const game::BattleControlSnapshot &,
    const game::CurrentBattleKnightRequestV1 &,
    game::CurrentBattleKnightSnapshotV1 &output) noexcept {
  output = {};
  output.unavailable_reason = "offline_fixture_not_live";
  return false;
}

} // namespace xar::ck3_11906

int main() {
  using namespace xar;
  using namespace xar::ck3_11906;

  game::BattleControlRequest request{};
  if (!ParseBattleControlSnapshotV1Step(
          "query-battle-control-snapshot-v1-83886341", request) ||
      request.subject_public_cunit_id != 83'886'341 ||
      ParseBattleControlSnapshotV1Step(
          "query-battle-control-snapshot-v1-083886341", request) ||
      ParseBattleControlSnapshotV1Step(
          "query-battle-control-snapshot-v1-83886341-extra", request)) {
    return Fail("battle-control canonical step parser failed");
  }
  std::uint64_t revision = 0;
  if (!ParseBattleControlExpectedRevisionV1(
          "{\"expected_revision\":9}", revision) ||
      revision != 9 ||
      ParseBattleControlExpectedRevisionV1(
          "{\"expected_revision\":09}", revision) ||
      ParseBattleControlExpectedRevisionV1(
          "{\"expected_revision\":9,\"expected_revision\":10}",
          revision)) {
    return Fail("battle-control expected revision parser failed");
  }

  game::CurrentBattleKnightRequestV1 knight_request{};
  if (!ParseCurrentBattleKnightV1Step(
          "query-current-battle-knight-v1-18-34333-61",
          knight_request) ||
      knight_request.subject_public_cunit_id != 18 ||
      knight_request.character_id != 34333 ||
      knight_request.regiment_id != 61 ||
      ParseCurrentBattleKnightV1Step(
          "query-current-battle-knight-v1-18-034333-61",
          knight_request) ||
      !ParseCurrentBattleKnightV1Step(
          "query-current-battle-knight-v1-18-34333-61",
          knight_request)) {
    return Fail("current-knight canonical step parser failed");
  }
  const std::string expected = R"({"expected_native_revision": 3, "expected_snapshot_id": "native:3", "expected_played_character_id": 29829, "expected_war_id": 4, "expected_native_carmy_id": 18, "expected_combat_id": 16777218, "expected_province_id": 2633, "expected_date_raw": 53146368})";
  if (!ParseCurrentBattleKnightExpectedV1(expected, 3,
                                           knight_request) ||
      knight_request.expected_native_carmy_id != 18 ||
      knight_request.expected_combat_id != 16777218 ||
      ParseCurrentBattleKnightExpectedV1(expected, 4,
                                          knight_request) ||
      ParseCurrentBattleKnightExpectedV1(
          R"({"expected_native_revision": 3, "expected_snapshot_id": "native:4", "expected_played_character_id": 29829, "expected_war_id": 4, "expected_native_carmy_id": 18, "expected_combat_id": 16777218, "expected_province_id": 2633, "expected_date_raw": 53146368})",
          3, knight_request)) {
    return Fail("current-knight exact-frame parser failed");
  }
  game::BattleControlSnapshot scoped{};
  scoped.status = game::BattleControlSnapshotStatus::available;
  scoped.battle_control_ready = true;
  scoped.subject_public_cunit_id = 18;
  scoped.subject_native_carmy_id = 18;
  scoped.selected_owner_character_id = 29829;
  scoped.combat_id = 16777218;
  scoped.province_id = 2633;
  scoped.combat_province_id = 2633;
  scoped.observed_date_raw = 53146368;
  game::BattleControlRegimentEntrySnapshot target{};
  target.bucket = "men_at_arms";
  target.regiment_id = 61;
  target.native_carmy_id = 18;
  target.public_cunit_id = 18;
  target.owner_character_id = 29829;
  target.knight_character_id_raw = 34333;
  scoped.defender.men_at_arms_entries.push_back(target);
  std::string_view scope_failure;
  if (SelectCurrentBattleKnightEntryV1(scoped, knight_request,
                                       scope_failure) == nullptr ||
      !scope_failure.empty()) {
    return Fail("current-knight pair scope positive fixture failed");
  }
  scoped.attacker.men_at_arms_entries.push_back(target);
  if (SelectCurrentBattleKnightEntryV1(scoped, knight_request,
                                       scope_failure) != nullptr ||
      scope_failure != "regiment_duplicate_in_battle") {
    return Fail("current-knight duplicate regiment gate failed");
  }
  scoped.attacker.men_at_arms_entries.clear();
  scoped.defender.men_at_arms_entries[0].knight_character_id_raw = 34332;
  if (SelectCurrentBattleKnightEntryV1(scoped, knight_request,
                                       scope_failure) != nullptr ||
      scope_failure != "knight_regiment_pair_mismatch") {
    return Fail("current-knight exact CharacterID gate failed");
  }
  scoped.defender.men_at_arms_entries[0].knight_character_id_raw = 34333;
  knight_request.expected_province_id = 2634;
  if (SelectCurrentBattleKnightEntryV1(scoped, knight_request,
                                       scope_failure) != nullptr ||
      scope_failure != "battle_scope_invalid") {
    return Fail("current-knight exact province gate failed");
  }

  game::CurrentBattleKnightSnapshotV1 value{};
  value.available = true;
  value.unavailable_reason.clear();
  value.observed_date_raw = 53146368;
  value.combat_id = 16777218;
  value.province_id = 2633;
  value.subject_public_cunit_id = 18;
  value.native_carmy_id = 18;
  value.character_id = 34333;
  value.regiment_id = 61;
  value.effective_prowess = 11;
  value.fresh_damage_raw = 11000000;
  value.fresh_toughness_raw = 2200000;
  value.stored_entry_damage_raw = 15000000;
  value.stored_entry_toughness_raw = 3000000;
  const auto knight_wire = SerializeCurrentBattleKnightV1(value);
  if (!Contains(knight_wire, "\"current_effective_prowess\":11") ||
      !Contains(knight_wire, "\"province_evaluated_damage_raw\":11000000") ||
      !Contains(knight_wire, "\"stored_combat_entry_damage_raw\":15000000")) {
    return Fail("current-knight fresh/stored wire separation failed");
  }
  if (!CheckCurrentBattleKnightFormulaV1(
           100000, 11, 10, 2, 11000000, 2200000).empty() ||
      CheckCurrentBattleKnightFormulaV1(
          100000, 11, 10, 2, 15000000, 3000000) !=
          "fresh_stats_knight_crosscheck_failed" ||
      CheckCurrentBattleKnightFormulaV1(
          std::numeric_limits<std::int64_t>::max(), 11, 10, 2,
          0, 0) != "knight_effectiveness_overflow") {
    return Fail("current-knight fresh formula and overflow gates failed");
  }
  auto drifted = value;
  if (!CheckCurrentBattleKnightPairV1(value, value).empty()) {
    return Fail("current-knight identical double sample rejected");
  }
  drifted.effective_prowess = 12;
  if (CheckCurrentBattleKnightPairV1(value, drifted) !=
      "current_knight_double_sample_mismatch") {
    return Fail("current-knight double-sample drift gate failed");
  }
  drifted = value;
  drifted.available = false;
  drifted.unavailable_reason = "effective_stats_helper_failed";
  if (CheckCurrentBattleKnightPairV1(value, drifted) !=
      "effective_stats_helper_failed") {
    return Fail("current-knight helper failure typed unavailable failed");
  }

  auto complete = CompleteBattle();
  const auto encoded = SerializeBattleControlSnapshotV1(complete);
  const std::string_view json(encoded);
  if (encoded.empty() ||
      encoded.size() > kBattleControlSnapshotV1WireMaximumBytes ||
      !Contains(json, "\"contract_stage\":\"production_exact_ongoing_combat\"") ||
      !Contains(json, "\"base_advantage_raw\":-5000000000") ||
      !Contains(json, "\"resolved_advantage_raw\":6000000000") ||
      !Contains(json, "\"selected_commander_character_id\":null") ||
      !Contains(json, "\"hard_casualties_status\":\"available\"") ||
      !Contains(json, "\"hard_casualties_raw\":200000") ||
      !Contains(json, "\"hard_casualties_status\":\"unavailable\"") ||
      !Contains(json, "\"knight_character_id_raw\":2130706429") ||
      !Contains(json, "\"hard_casualties_raw\":null") ||
      !Contains(json, "\"hard_casualties_unavailable_reason\":\"non_main_reserve_not_distinguishable_from_hard\"") ||
      !Contains(json, "\"participant_hard_ledger\":[{") ||
      !Contains(json, "\"battle_result_id\":null") ||
      !Contains(json, "\"stored_current_matches_derived\":true") ||
      !Contains(json, "\"stored_levy_current_matches_derived\":true") ||
      !Contains(json, "\"selected_public_cunit_id\":83886341") ||
      !Contains(json, "\"selected_native_carmy_id\":67108900") ||
      !Contains(json, "\"selected_owner_character_id\":100") ||
      !Contains(json, "\"combat_province_id\":2586") ||
      !Contains(json, "\"side_index\":0") ||
      !Contains(json, "\"side_scope\":\"full_side\"") ||
      !Contains(json,
                "\"affected_public_cunit_ids_in_stored_order\":[83886341]") ||
      !Contains(json,
                "\"unaffected_same_side_public_cunit_ids_in_stored_order\":[]") ||
      !Contains(json,
                "\"side_flags\":{\"disallow_retreat\":false,"
                "\"allow_early_retreat\":false,\"skip_pursuit\":false}") ||
      !Contains(json,
                "\"legality\":{\"status\":\"available\","
                "\"native_boolean\":true,\"phase_raw\":1,"
                "\"phase\":\"main\","
                "\"retreat_elapsed_baseline_date_raw\":53177904,"
                "\"elapsed_whole_days\":15,"
                "\"minimum_elapsed_whole_days_exclusive\":14,"
                "\"landless_gate_allows_retreat\":true,"
                "\"legal_now\":true,"
                "\"reason_codes_in_native_order\":[],"
                "\"native_reason_keys_in_native_order\":[],"
                "\"earliest_day_gate_date_raw\":53178264}") ||
      !json.ends_with("\"battle_control_ready\":true}")) {
    return Fail("battle-control serializer omitted a frozen ABI field");
  }

  const auto resume_receipt = SerializeActiveCombatResumeInputsV1(complete);
  const std::string_view resume_json(resume_receipt);
  if (resume_receipt.empty() ||
      !Contains(resume_json, "\"status\":\"unavailable\"") ||
      !Contains(resume_json, "\"input_observation_ready\":false") ||
      !Contains(resume_json,
                "\"unavailable_reason\":\"same_frame_resume_operands_incomplete\"") ||
      !Contains(resume_json,
                "\"source\":{\"snapshot_revision\":9,"
                "\"observed_date_raw\":53178264,"
                "\"subject_public_cunit_id\":83886341,"
                "\"subject_native_carmy_id\":67108900,"
                "\"combat_id\":335544325,\"province_id\":2586}") ||
      !Contains(resume_json,
                "\"observed\":{\"phase\":\"main\",\"phase_day\":2,"
                "\"elapsed_whole_days\":15,\"roll_cadence_counter\":3,"
                "\"final_combat_width\":950,"
                "\"side_0_current_roll_points\":11") ||
      !Contains(resume_json,
                "\"side_0_selected_commander_character_id\":null") ||
      !Contains(resume_json,
                "\"side_0_selected_commander_next_roll_bounds\":{"
                "\"status\":\"unavailable\",\"effective_min_roll\":null,"
                "\"effective_max_roll\":null,\"unavailable_reason\":\"not_sampled\"}") ||
      !Contains(resume_json,
                "\"side_0_ordered_public_cunit_ids\":[83886341]") ||
      !Contains(resume_json, "\"side_0_entry_count\":2") ||
      !Contains(resume_json,
                "\"battle_side_mapping\":{\"status\":\"available\","
                "\"subject_side_index\":0,\"opposing_side_index\":1,"
                "\"subject_owner_character_id\":100,"
                "\"side_scope\":\"full_side\","
                "\"same_side_public_cunit_ids_in_stored_order\":[83886341],"
                "\"opposing_side_public_cunit_ids_in_stored_order\":[357],"
                "\"affected_public_cunit_ids_in_stored_order\":[83886341],"
                "\"unaffected_same_side_public_cunit_ids_in_stored_order\":[]}") ||
      Contains(resume_json, "\"active_coalition_side_mapping\"")) {
    return Fail("active resume receipt did not preserve typed unavailable and exact source");
  }
  auto empty_knight_slot = complete;
  empty_knight_slot.attacker.men_at_arms_entries[0].knight_character_id_raw = -1;
  if (!Contains(SerializeBattleControlSnapshotV1(empty_knight_slot),
                "\"knight_character_id_raw\":-1")) {
    return Fail("battle-control lost the empty retained MAA knight slot");
  }
  auto signed_knight_slot = complete;
  signed_knight_slot.attacker.men_at_arms_entries[0].knight_character_id_raw =
      -2'130'706'429;
  if (!Contains(SerializeBattleControlSnapshotV1(signed_knight_slot),
                "\"knight_character_id_raw\":-2130706429")) {
    return Fail("battle-control narrowed a signed full knight ID");
  }
  auto false_levy_knight = complete;
  false_levy_knight.attacker.levy_entries[0].knight_character_id_raw = 100;
  if (!SerializeBattleControlSnapshotV1(false_levy_knight).empty()) {
    return Fail("battle-control admitted a knight field on a levy entry");
  }
  auto accolade_link = complete;
  auto &linked_entry = accolade_link.attacker.men_at_arms_entries[0];
  linked_entry.accolade_link_status = "observed";
  linked_entry.accolade_id_raw = 77;
  const auto linked_json = SerializeBattleControlSnapshotV1(accolade_link);
  if (!Contains(linked_json,
                "\"accolade_source\":{\"link_status\":\"observed\","
                "\"accolade_id_raw\":77,\"rows_status\":\"unknown_not_observed\","
                "\"rows\":null,\"source_gate_status\":"
                "\"unknown_original_call_not_observed\"}")) {
    return Fail("battle-control claimed unseen accolade source rows");
  }
  linked_entry.accolade_id_raw = -1;
  if (!Contains(SerializeBattleControlSnapshotV1(accolade_link),
                "\"rows_status\":\"not_applicable_no_accolade\","
                "\"rows\":null,\"source_gate_status\":"
                "\"not_applicable_no_accolade\"")) {
    return Fail("battle-control failed the no-accolade link case");
  }
  linked_entry.accolade_link_status = "unavailable_character_generation";
  linked_entry.accolade_id_raw.reset();
  if (!Contains(SerializeBattleControlSnapshotV1(accolade_link),
                "\"link_status\":\"unavailable_character_generation\"")) {
    return Fail("battle-control lost unresolved knight link semantics");
  }
  linked_entry.accolade_link_status = "observed";
  if (!SerializeBattleControlSnapshotV1(accolade_link).empty()) {
    return Fail("battle-control accepted observed link without ID");
  }
  auto owner_subset = complete;
  owner_subset.attacker.ordered_armies.push_back(
      {67'108'902, 83'886'342, 101, complete.combat_id});
  owner_subset.side_scope = "owner_subset";
  owner_subset.unaffected_same_side_public_cunit_ids_in_stored_order =
      {83'886'342};
  const auto subset_receipt = SerializeActiveCombatResumeInputsV1(owner_subset);
  if (!Contains(subset_receipt,
                "\"side_scope\":\"owner_subset\","
                "\"same_side_public_cunit_ids_in_stored_order\":[83886341,83886342]") ||
      !Contains(subset_receipt,
                "\"unaffected_same_side_public_cunit_ids_in_stored_order\":[83886342]")) {
    return Fail("active resume coalition mapping lost the owner subset");
  }
  auto defender_subject = complete;
  defender_subject.subject_public_cunit_id = 357;
  defender_subject.subject_native_carmy_id = 67'108'901;
  defender_subject.selected_public_cunit_id = 357;
  defender_subject.selected_native_carmy_id = 67'108'901;
  defender_subject.selected_owner_character_id = 200;
  defender_subject.side_index = 1;
  defender_subject.affected_public_cunit_ids_in_stored_order = {357};
  const auto defender_receipt =
      SerializeActiveCombatResumeInputsV1(defender_subject);
  if (!Contains(defender_receipt,
                "\"subject_side_index\":1,\"opposing_side_index\":0,"
                "\"subject_owner_character_id\":200") ||
      !Contains(defender_receipt,
                "\"same_side_public_cunit_ids_in_stored_order\":[357],"
                "\"opposing_side_public_cunit_ids_in_stored_order\":[83886341]")) {
    return Fail("active resume coalition mapping assumed attacker is subject");
  }
  auto roll_bounds = complete;
  roll_bounds.attacker.selected_commander_next_roll_bounds = {true, 0, 0, ""};
  roll_bounds.defender.selected_commander_next_roll_bounds = {true, -1, 11, ""};
  const auto bounds_receipt = SerializeActiveCombatResumeInputsV1(roll_bounds);
  if (bounds_receipt.empty() ||
      !Contains(bounds_receipt,
                "\"side_0_selected_commander_next_roll_bounds\":{"
                "\"status\":\"available\",\"effective_min_roll\":0,"
                "\"effective_max_roll\":0,\"unavailable_reason\":null}") ||
      !Contains(bounds_receipt,
                "\"side_1_selected_commander_next_roll_bounds\":{"
                "\"status\":\"available\",\"effective_min_roll\":-1,"
                "\"effective_max_roll\":11,\"unavailable_reason\":null}") ||
      Contains(bounds_receipt,
               "\"selected_commander_next_roll_bounds\",")) {
    return Fail("actual-side roll bounds did not close only their own domain");
  }
  roll_bounds.defender.selected_commander_next_roll_bounds =
      {false, 0, 0, "commander_modifier_unavailable"};
  if (!Contains(SerializeActiveCombatResumeInputsV1(roll_bounds),
                "\"selected_commander_next_roll_bounds\",")) {
    return Fail("one unavailable side incorrectly closed roll bounds domain");
  }
  auto invalid_resume = complete;
  invalid_resume.combat_id = -1;
  if (!SerializeActiveCombatResumeInputsV1(invalid_resume).empty()) {
    return Fail("active resume receipt accepted an invalid battle-control frame");
  }

  auto active_counter = complete;
  auto &counter = active_counter.active_counter_inputs_v1;
  counter.attempted = true;
  counter.available = true;
  counter.unavailable_reason.clear();
  counter.source_combat_id = complete.combat_id;
  counter.source_target_province_id = complete.province_id;
  counter.class_count = 2;
  game::BattleControlCounterEntryV1 reserve_counter{};
  const auto &reserve_entry = complete.attacker.men_at_arms_entries[0];
  reserve_counter.bucket_index = reserve_entry.bucket_index;
  reserve_counter.regiment_id = reserve_entry.regiment_id;
  reserve_counter.native_carmy_id = reserve_entry.native_carmy_id;
  reserve_counter.current_fighting_raw = reserve_entry.current_fighting_raw;
  reserve_counter.status = game::CombatObservationStatus::available;
  reserve_counter.class_index = 1;
  reserve_counter.stack_size_soldiers = 100;
  reserve_counter.current_chunk_raw = 0;
  reserve_counter.targets.push_back({0, 25'000});
  counter.sides = {
      {0, 100, 12'000, -3'000, {reserve_counter}},
      {1, 200, 12'001, -3'001, {}}};
  // The defender commander is 201, while the native primary owner is 200.
  counter.contexts = {
      {0, 1, 100, 200, 150'000},
      {1, 0, 200, 100, 150'001}};
  const auto counter_encoded = SerializeBattleControlSnapshotV1(active_counter);
  if (counter_encoded.empty() ||
      !Contains(counter_encoded,
                "\"active_counter_inputs_v1\":{\"schema_version\":1,"
                "\"status\":\"available\","
                "\"operand_census_complete\":true") ||
      !Contains(counter_encoded, "\"regiment_id\":401") ||
      !Contains(counter_encoded, "\"stack_size_soldiers\":100") ||
      !Contains(counter_encoded, "\"context_scale_raw\":150000") ||
      !Contains(counter_encoded,
                "\"countered_primary_owner_character_id\":200,"
                "\"countering_primary_owner_character_id\":100")) {
    return Fail("active counter same-frame operands were not serialized");
  }
  const auto counter_resume = SerializeActiveCombatResumeInputsV1(active_counter);
  const auto counter_missing_pos =
      counter_resume.find("\"missing_required_domains\":");
  if (counter_resume.empty() ||
      !Contains(counter_resume,
                "\"active_counter_inputs_v1\":{\"schema_version\":1,"
                "\"status\":\"available\","
                "\"operand_census_complete\":true") ||
      counter_missing_pos == std::string::npos ||
      counter_resume.substr(counter_missing_pos).find(
          "active_regiment_counter_class_stack_context") == std::string::npos ||
      !Contains(counter_resume, "\"input_observation_ready\":false")) {
    return Fail("active resume lost current counter data or next-day gap");
  }
  auto wrong_counter = active_counter;
  wrong_counter.active_counter_inputs_v1.contexts[0]
      .countering_primary_owner_character_id = 201;
  if (!SerializeBattleControlSnapshotV1(wrong_counter).empty()) {
    return Fail("active counter accepted commander in place of primary owner");
  }
  wrong_counter = active_counter;
  wrong_counter.active_counter_inputs_v1.sides[0]
      .men_at_arms_entries[0].current_chunk_raw = 1;
  if (!SerializeBattleControlSnapshotV1(wrong_counter).empty()) {
    return Fail("active counter accepted wrong current chunk");
  }
  auto unavailable_counter = active_counter;
  unavailable_counter.active_counter_inputs_v1.available = false;
  unavailable_counter.active_counter_inputs_v1.unavailable_reason =
      "counter_regiment_generation_changed";
  unavailable_counter.active_counter_inputs_v1.class_count = 0;
  unavailable_counter.active_counter_inputs_v1.sides.clear();
  unavailable_counter.active_counter_inputs_v1.contexts.clear();
  if (!Contains(SerializeBattleControlSnapshotV1(unavailable_counter),
                "\"operand_census_complete\":false") ||
      !Contains(SerializeBattleControlSnapshotV1(unavailable_counter),
                "\"class_count\":null,\"sides\":null,"
                "\"contexts\":null")) {
    return Fail("active counter unavailable exposed partial operands");
  }
  const auto unavailable_resume =
      SerializeActiveCombatResumeInputsV1(unavailable_counter);
  const auto unavailable_missing_pos =
      unavailable_resume.find("\"missing_required_domains\":");
  if (!Contains(unavailable_resume,
                "\"active_counter_inputs_v1\":{\"schema_version\":1,"
                "\"status\":\"unavailable\","
                "\"operand_census_complete\":false") ||
      unavailable_missing_pos == std::string::npos ||
      unavailable_resume.substr(unavailable_missing_pos).find(
          "active_regiment_counter_class_stack_context") == std::string::npos) {
    return Fail("active resume hid an unavailable counter operand domain");
  }

  auto pursuit = complete;
  pursuit.pursuit_modifier_sides.attempted = true;
  pursuit.pursuit_modifier_sides.available = true;
  pursuit.pursuit_modifier_sides.source_combat_id = pursuit.combat_id;
  pursuit.pursuit_modifier_sides.source_target_province_id =
      pursuit.province_id;
  pursuit.pursuit_modifier_sides.sides = {
      {0, "attacker", 12'345, -6'789},
      {1, "defender", -1'234, 5'678}};
  const auto pursuit_encoded = SerializeBattleControlSnapshotV1(pursuit);
  if (!Contains(pursuit_encoded,
                "\"pursuit_modifier_sides\":{\"status\":\"available\"") ||
      !Contains(pursuit_encoded, "\"pursuit_efficiency_raw\":12345") ||
      !Contains(pursuit_encoded, "\"retreat_losses_raw\":5678")) {
    return Fail("battle-control pursuit modifier projection was not serialized");
  }
  pursuit.pursuit_modifier_sides.sides[1].side_index = 0;
  if (!SerializeBattleControlSnapshotV1(pursuit).empty()) {
    return Fail("battle-control pursuit modifier side order was accepted");
  }
  if (Contains(json, "\"actual_hard_casualty_sides\"")) {
    return Fail("battle-control changed the legacy frame without a readout");
  }
  auto actual_hard = complete;
  actual_hard.actual_hard_casualty_sides.attempted = true;
  actual_hard.actual_hard_casualty_sides.available = true;
  actual_hard.actual_hard_casualty_sides.source_combat_id =
      complete.combat_id;
  actual_hard.actual_hard_casualty_sides.source_target_province_id =
      complete.province_id;
  actual_hard.actual_hard_casualty_sides.sides = {
      {0, "attacker", {complete.subject_public_cunit_id}, -1,
       12'345, -6'789},
      {1, "defender", {357}, 201, -1'234, 5'678},
  };
  const auto actual_encoded =
      SerializeBattleControlSnapshotV1(actual_hard);
  if (actual_encoded.empty() ||
      !Contains(actual_encoded,
                "\"actual_hard_casualty_sides\":{\"status\":\"available\","
                "\"source_combat_id\":335544325,"
                "\"source_target_province_id\":2586,\"scale\":100000,"
                "\"sides\":[{\"side_index\":0,"
                "\"encounter_role\":\"attacker\","
                "\"ordered_army_ids\":[83886341],"
                "\"commander_character_id\":-1,"
                "\"own_modifier_raw\":12345,"
                "\"enemy_modifier_raw\":-6789}") ||
      !Contains(actual_encoded,
                "\"side_index\":1,\"encounter_role\":\"defender\","
                "\"ordered_army_ids\":[357],"
                "\"commander_character_id\":201,"
                "\"own_modifier_raw\":-1234,"
                "\"enemy_modifier_raw\":5678}]")) {
    return Fail("battle-control actual hard side readout lost raw or identity");
  }
  actual_hard.actual_hard_casualty_sides.available = false;
  actual_hard.actual_hard_casualty_sides.sides.clear();
  actual_hard.actual_hard_casualty_sides.unavailable_reason =
      "native_actual_hard_side_modifier_unreadable";
  const auto actual_failure =
      SerializeBattleControlSnapshotV1(actual_hard);
  if (actual_failure.empty() ||
      !Contains(actual_failure,
                "\"actual_hard_casualty_sides\":{\"status\":\"unavailable\"") ||
      !Contains(actual_failure,
                "\"sides\":null,\"unavailable_reason\":"
                "\"native_actual_hard_side_modifier_unreadable\"}")) {
    return Fail("battle-control fabricated hard raw after a failed read");
  }
  actual_hard.actual_hard_casualty_sides.source_combat_id = 99;
  if (!SerializeBattleControlSnapshotV1(actual_hard).empty()) {
    return Fail("battle-control admitted a mismatched hard readout combat");
  }

  // Full component IDs are signed dword bit patterns.  A generation byte
  // with its high bit set is negative in JSON but remains a valid identity;
  // only -1 denotes a missing ID.
  constexpr std::int32_t signed_generation_combat_id = -2'130'706'429;
  auto signed_combat = complete;
  signed_combat.combat_id = signed_generation_combat_id;
  signed_combat.attacker.ordered_armies[0].combat_backlink_id =
      signed_generation_combat_id;
  signed_combat.defender.ordered_armies[0].combat_backlink_id =
      signed_generation_combat_id;
  const auto signed_combat_encoded =
      SerializeBattleControlSnapshotV1(signed_combat);
  if (signed_combat_encoded.empty() ||
      !Contains(signed_combat_encoded,
                "\"combat_id\":-2130706429") ||
      !Contains(signed_combat_encoded,
                "\"combat_backlink_id\":-2130706429")) {
    return Fail("battle-control serializer rejected a signed full CombatID");
  }

  constexpr std::int32_t signed_generation_battle_result_id = -2'130'706'431;
  auto signed_battle_result = complete;
  signed_battle_result.battle_result_id =
      signed_generation_battle_result_id;
  const auto signed_battle_result_encoded =
      SerializeBattleControlSnapshotV1(signed_battle_result);
  if (signed_battle_result_encoded.empty() ||
      !Contains(signed_battle_result_encoded,
                "\"battle_result_id\":-2130706431")) {
    return Fail(
        "battle-control serializer rejected a signed full BattleResultID");
  }

  auto all_retreat_gates_closed = complete;
  all_retreat_gates_closed.side_flags.disallow_retreat = true;
  all_retreat_gates_closed.legality.native_boolean = false;
  all_retreat_gates_closed.phase = "pursuit";
  all_retreat_gates_closed.phase_raw = 2;
  all_retreat_gates_closed.legality.phase = "pursuit";
  all_retreat_gates_closed.legality.phase_raw = 2;
  all_retreat_gates_closed.legality.retreat_elapsed_baseline_date_raw =
      53'178'264;
  all_retreat_gates_closed.legality.elapsed_whole_days = 0;
  all_retreat_gates_closed.legality.landless_gate_allows_retreat = false;
  all_retreat_gates_closed.legality.legal_now = false;
  all_retreat_gates_closed.legality.reason_codes_in_native_order = {
      "disallowed", "too_early", "pursuit_or_done", "landless"};
  all_retreat_gates_closed.legality.native_reason_keys_in_native_order = {
      "COMBAT_NO_RETREAT_DISALLOWED", "COMBAT_NO_RETREAT_TOO_EARLY",
      "COMBAT_NO_RETREAT_PURSUIT", "COMBAT_NO_RETREAT_LANDLESS"};
  all_retreat_gates_closed.legality.earliest_day_gate_date_raw = 53'178'624;
  const auto all_gates_encoded =
      SerializeBattleControlSnapshotV1(all_retreat_gates_closed);
  if (all_gates_encoded.empty() ||
      !Contains(all_gates_encoded,
                "\"reason_codes_in_native_order\":[\"disallowed\","
                "\"too_early\",\"pursuit_or_done\",\"landless\"]") ||
      !Contains(all_gates_encoded,
                "\"native_reason_keys_in_native_order\":["
                "\"COMBAT_NO_RETREAT_DISALLOWED\","
                "\"COMBAT_NO_RETREAT_TOO_EARLY\","
                "\"COMBAT_NO_RETREAT_PURSUIT\","
                "\"COMBAT_NO_RETREAT_LANDLESS\"]")) {
    return Fail("battle-control serializer lost native retreat gate order");
  }
  std::swap(
      all_retreat_gates_closed.legality.reason_codes_in_native_order[0],
      all_retreat_gates_closed.legality.reason_codes_in_native_order[1]);
  if (!SerializeBattleControlSnapshotV1(all_retreat_gates_closed).empty()) {
    return Fail("battle-control serializer admitted reordered retreat gates");
  }

  auto wide_retreat_boundary = complete;
  wide_retreat_boundary.observed_date_raw = 2'147'483'647;
  wide_retreat_boundary.legality.native_boolean = false;
  wide_retreat_boundary.legality.retreat_elapsed_baseline_date_raw =
      2'147'483'647;
  wide_retreat_boundary.legality.elapsed_whole_days = 0;
  wide_retreat_boundary.legality.legal_now = false;
  wide_retreat_boundary.legality.reason_codes_in_native_order = {"too_early"};
  wide_retreat_boundary.legality.native_reason_keys_in_native_order = {
      "COMBAT_NO_RETREAT_TOO_EARLY"};
  wide_retreat_boundary.legality.earliest_day_gate_date_raw =
      2'147'484'000LL;
  const auto wide_retreat_encoded =
      SerializeBattleControlSnapshotV1(wide_retreat_boundary);
  if (wide_retreat_encoded.empty() ||
      !Contains(wide_retreat_encoded,
                "\"earliest_day_gate_date_raw\":2147484000")) {
    return Fail("battle-control serializer narrowed retreat date to int32");
  }

  auto invalid_retreat_scope = complete;
  invalid_retreat_scope.side_scope = "owner_subset";
  if (!SerializeBattleControlSnapshotV1(invalid_retreat_scope).empty()) {
    return Fail("battle-control serializer admitted a false retreat scope");
  }
  auto invalid_native_legality = complete;
  invalid_native_legality.legality.native_boolean = false;
  if (!SerializeBattleControlSnapshotV1(invalid_native_legality).empty()) {
    return Fail("battle-control serializer admitted a native gate mismatch");
  }
  auto stale_cache = complete;
  stale_cache.attacker.stored_current_fighting_raw = 699'999;
  stale_cache.attacker.stored_levy_current_fighting_raw = 699'998;
  stale_cache.attacker.stored_current_matches_derived = false;
  stale_cache.attacker.stored_levy_current_matches_derived = false;
  const auto stale_encoded =
      SerializeBattleControlSnapshotV1(stale_cache);
  if (stale_encoded.empty() ||
      !Contains(stale_encoded,
                "\"stored_current_fighting_raw\":699999") ||
      !Contains(stale_encoded,
                "\"stored_terminal_loss_baseline_raw\":1500000") ||
      !Contains(stale_encoded,
                "\"stored_levy_current_fighting_raw\":699998") ||
      !Contains(stale_encoded,
                "\"stored_current_matches_derived\":false") ||
      !Contains(stale_encoded,
                "\"stored_levy_current_matches_derived\":false")) {
    return Fail("battle-control serializer rejected a stable stale cache");
  }
  auto inconsistent_cache = stale_cache;
  inconsistent_cache.attacker.stored_current_matches_derived = true;
  if (!SerializeBattleControlSnapshotV1(inconsistent_cache).empty()) {
    return Fail("battle-control serializer admitted a false cache match");
  }
  auto invalid = complete;
  invalid.attacker.men_at_arms_entries[0].hard_casualties_available = true;
  if (!SerializeBattleControlSnapshotV1(invalid).empty()) {
    return Fail("battle-control serializer admitted fabricated non-main hard");
  }
  auto oversized = complete;
  for (std::int32_t index = 1; index <= 1'700; ++index) {
    oversized.attacker.levy_entries.push_back(
        MainEntry("levy", index, 10'000 + index,
                  oversized.attacker.ordered_armies.front(), 1, 1, 0));
    ++oversized.attacker.stored_current_fighting_raw;
    ++oversized.attacker.stored_levy_current_fighting_raw;
    ++oversized.attacker.derived_current_fighting_raw;
  }
  if (!SerializeBattleControlSnapshotV1(oversized).empty()) {
    return Fail("battle-control serializer exceeded the pipe wire budget");
  }

  g_outer_snapshot = CompleteOuterSnapshot();
  g_native_result = stale_cache;
  g_native_result.snapshot_revision = 0;
  g_native_status = game::BattleControlSnapshotStatus::available;
  g_snapshot_reads = 0;
  g_battle_reads = 0;

  MainThreadQueryMailboxV1 mailbox{};
  BattleControlSnapshotMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 17;
  query.request.subject_public_cunit_id = 83'886'341;
  query.expected_snapshot_revision = 9;
  query.expected_snapshot = g_outer_snapshot;
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(query.ticket.sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &ExecuteBattleControlSnapshotMailboxQueryV1;
  mailbox.executor_context = &query;

  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 3;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 2;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 3;
  stamp.game_state = 4;
  stamp.date_raw = g_outer_snapshot.date_raw;
  stamp.paused = true;
  if (!ExecuteBattleControlSnapshotMailboxQueryV1(&query, stamp) ||
      query.completion !=
          BattleControlSnapshotMailboxCompletionV1::available ||
      query.executor_invocations != 1 || g_snapshot_reads != 2 ||
      g_battle_reads != 1 || query.result.snapshot_revision != 9 ||
      query.result.attacker.stored_current_matches_derived ||
      query.result.attacker.stored_levy_current_matches_derived ||
      SerializeBattleControlSnapshotV1(query.result).empty()) {
    return Fail("battle-control application-main executor contract failed");
  }

  std::cout << "battle_control_snapshot_v1_mailbox_test: ok\n";
  return 0;
}
