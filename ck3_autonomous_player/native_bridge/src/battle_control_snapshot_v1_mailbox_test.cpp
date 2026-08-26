#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
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
  result.attacker.men_at_arms_entries.push_back(reserve);
  result.attacker.stored_current_fighting_raw = 700'000;
  result.attacker.stored_levy_current_fighting_raw = 700'000;
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
