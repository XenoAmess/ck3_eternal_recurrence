#include "xar_bridge/battle_terminal_journal_v1.hpp"
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {

template <typename Value>
void Store(void *base, std::size_t offset, const Value &value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value,
              sizeof(value));
}

struct FakeStorage {
  std::array<std::byte, 0x40> object{};
  std::vector<std::array<std::byte, 0x10>> slots;
  void *pointer = object.data();

  explicit FakeStorage(std::size_t capacity) : slots(capacity) {
    void *const data = slots.data();
    Store(object.data(), 0x20, data);
    Store(object.data(), 0x2C, static_cast<std::int32_t>(capacity));
  }

  void Put(std::int32_t id, void *value) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots[index].data(), 0x08, value);
  }
};

xar::game::Snapshot g_snapshot{};
xar::game::BattleTerminalTransitionSnapshotV1 g_native_result{};

bool FakeProtect(void *, void *, std::size_t, DWORD, DWORD &old) noexcept {
  old = PAGE_READWRITE;
  return true;
}

bool FakeFlush(void *, const void *, std::size_t) noexcept { return true; }

xar::game::BattleTerminalTransitionSnapshotV1 CompleteResult() {
  xar::game::BattleTerminalTransitionSnapshotV1 result{};
  result.status = xar::game::BattleTerminalTransitionStatusV1::available;
  result.battle_terminal_transition_ready = true;
  result.snapshot_revision = 9;
  result.observed_date_raw = 1234;
  result.prior_combat_id = 5;
  result.subject_public_cunit_id = 3;
  result.terminal_journal.oldest_available_sequence = 1;
  result.terminal_journal.latest_sequence = 2;
  result.terminal_journal.event_sequence = 2;
  result.terminal_journal.event_status =
      xar::game::BattleTerminalJournalEventStatusV1::observed;
  result.prior.combat_id = 5;
  result.prior.terminal_kind = xar::game::BattleTerminalKindV1::normal_result;
  result.prior.suppress_normal_result_envelopes = false;
  result.prior.phase_raw = 3;
  result.prior.winner_raw = 0;
  result.prior.finalized_before = false;
  result.prior.daily_guard_raw = std::uint8_t{1};
  result.prior.province_id = 7;
  result.prior.battle_result_id = 6;
  result.prior.wipe_raw = false;
  result.prior.attacker_primary_participant_character_id = 101;
  result.prior.defender_primary_participant_character_id = 102;
  result.prior.attacker_public_cunit_ids_in_stored_order =
      std::vector<std::int32_t>{3};
  result.prior.defender_public_cunit_ids_in_stored_order =
      std::vector<std::int32_t>{4};
  result.prior.battle_warscore.status =
      xar::game::BattleTerminalWarscoreStatusV1::not_recorded_by_native;
  result.removal.prior_combat_strictly_resolves = false;
  result.removal.prior_province_strictly_resolves = true;
  result.removal.prior_province_contains_prior_combat_id = false;
  result.removal.result_strictly_resolves = true;
  result.removal.result_relevant_player_count = 0;
  result.subject.exists = true;
  result.subject.current_province_id = 7;
  result.subject.native_carmy_id = 1;
  // Native -1 is deliberately represented by an absent optional backlink.
  result.subject.movement_or_retreat_state_raw = 0;
  result.subject.route_province_ids_in_stored_order =
      std::vector<std::int32_t>{};
  result.subject.ai_membership_status =
      xar::game::BattleTerminalAiMembershipStatusV1::none;
  result.subject.blocked_by_active_combat = false;
  result.successor.state =
      xar::game::BattleTerminalSuccessorStateV1::no_successor;
  return result;
}

bool TestParserAndSerializer() {
  using namespace xar::ck3_11906;
  xar::game::BattleTerminalTransitionRequestV1 request{};
  if (!ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-5-3-0", request) ||
      request.prior_combat_id != 5 || request.subject_public_cunit_id != 3 ||
      request.after_terminal_sequence.has_value() ||
      !ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-5-3-42", request) ||
      request.after_terminal_sequence != 42 ||
      ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-05-3-0", request) ||
      ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-5-03-0", request) ||
      ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-5-3-00", request) ||
      ParseBattleTerminalTransitionV1Step(
          "query-battle-terminal-transition-v1-5-3-0-extra", request)) {
    return false;
  }
  std::uint64_t revision = 0;
  if (!ParseBattleTerminalTransitionExpectedRevisionV1(
          "{\"expected_revision\":9}", revision) || revision != 9) {
    return false;
  }
  const auto complete = CompleteResult();
  const auto json = SerializeBattleTerminalTransitionV1(complete);
  if (json.find("\"contract_stage\":\"production_exact_battle_terminal_transition\"") ==
          std::string::npos ||
      json.find("\"battle_terminal_transition_ready\":true") ==
          std::string::npos ||
      json.find("\"terminal_kind\":\"normal_result\"") ==
          std::string::npos ||
      json.find("\"ai_membership_status\":\"none\"") ==
          std::string::npos ||
      json.find("\"combat_backlink_id\":null") == std::string::npos ||
      json.find("\"attacker_primary_participant_character_id\":101") ==
          std::string::npos) {
    return false;
  }
  auto observed_membership = complete;
  observed_membership.subject.ai_membership_status =
      xar::game::BattleTerminalAiMembershipStatusV1::observed;
  observed_membership.subject.coordinator_id = 17;
  observed_membership.subject.unit_stack_stored_index = 1;
  observed_membership.subject.subunit_stored_index = 2;
  observed_membership.successor.state =
      xar::game::BattleTerminalSuccessorStateV1::subject_assignment_reopened;
  const auto observed_json =
      SerializeBattleTerminalTransitionV1(observed_membership);
  if (observed_json.find("\"ai_membership_status\":\"observed\"") ==
          std::string::npos ||
      observed_json.find("\"coordinator_id\":17") == std::string::npos) {
    return false;
  }
  auto partial_membership = complete;
  partial_membership.subject.ai_membership_status =
      xar::game::BattleTerminalAiMembershipStatusV1::unavailable;
  partial_membership.successor.state =
      xar::game::BattleTerminalSuccessorStateV1::unavailable;
  const auto partial_json =
      SerializeBattleTerminalTransitionV1(partial_membership);
  if (partial_json.find(
          "\"ai_membership_status\":\"unavailable\"") ==
          std::string::npos) {
    return false;
  }
  partial_membership.successor.state =
      xar::game::BattleTerminalSuccessorStateV1::no_successor;
  if (!SerializeBattleTerminalTransitionV1(partial_membership).empty()) {
    return false;
  }
  auto unblocked_residual = complete;
  unblocked_residual.subject.active_combat_id = 8;
  unblocked_residual.successor.state =
      xar::game::BattleTerminalSuccessorStateV1::residual_new_combat;
  unblocked_residual.successor.matching_combat_ids_in_native_order = {8};
  unblocked_residual.successor.selected_successor_combat_id = 8;
  unblocked_residual.successor
      .participant_overlap_public_cunit_ids_in_prior_order = {3};
  if (!SerializeBattleTerminalTransitionV1(unblocked_residual).empty()) {
    return false;
  }
  auto unavailable = xar::game::BattleTerminalTransitionSnapshotV1{};
  unavailable.status =
      xar::game::BattleTerminalTransitionStatusV1::unavailable;
  unavailable.unavailable_reason = "journal_gap";
  unavailable.snapshot_revision = 10;
  unavailable.observed_date_raw = 1234;
  unavailable.prior_combat_id = 5;
  unavailable.subject_public_cunit_id = 3;
  unavailable.terminal_journal.requested_after_sequence = 1;
  unavailable.terminal_journal.oldest_available_sequence = 8;
  unavailable.terminal_journal.latest_sequence = 4103;
  const auto unavailable_json =
      SerializeBattleTerminalTransitionV1(unavailable);
  return unavailable_json.find("\"unavailable_reason\":\"journal_gap\"") !=
             std::string::npos &&
         unavailable_json.find(
             "\"prior\":null,\"removal\":null,\"subject\":null,\"successor\":null") !=
             std::string::npos;
}

bool TestJournalAndDetourAnchors() {
  using namespace xar::ck3_11906;
  std::array<std::byte, 0x20> game_state{};
  void *game_state_pointer = game_state.data();
  Store(game_state.data(), 0x08, std::int32_t{1234});
  FakeStorage public_units(16);
  FakeStorage internal_armies(16);
  FakeStorage results(16);
  std::array<std::byte, 0x720> combat{};
  std::array<std::byte, 0x30> province{};
  std::array<std::byte, 0x200> attacker_unit{};
  std::array<std::byte, 0x200> defender_unit{};
  std::array<std::byte, 0x140> attacker_army{};
  std::array<std::byte, 0x140> defender_army{};
  std::array<std::byte, 0x80> result{};
  std::array<std::int32_t, 1> attacker_ids{1};
  std::array<std::int32_t, 1> defender_ids{2};
  Store(combat.data(), 0x08, std::int32_t{5});
  Store(combat.data(), 0x6B0, std::int32_t{3});
  Store(combat.data(), 0x6B8, static_cast<void *>(province.data()));
  Store(combat.data(), 0x6E0, std::int32_t{0});
  Store(combat.data(), 0x704, std::uint8_t{0});
  Store(combat.data(), 0x705, std::uint8_t{1});
  Store(combat.data(), 0x708, std::int32_t{6});
  Store(province.data(), 0x10, std::int32_t{7});
  const auto initialize_side = [&](std::size_t side, void *ids,
                                   std::int32_t primary) {
    Store(combat.data(), side + 0x10, ids);
    Store(combat.data(), side + 0x18, std::int32_t{1});
    Store(combat.data(), side + 0x1C, std::int32_t{1});
    Store(combat.data(), side + 0x70, primary);
    Store(combat.data(), side + 0xB8, static_cast<void *>(combat.data()));
  };
  initialize_side(0x20, attacker_ids.data(), 101);
  initialize_side(0x368, defender_ids.data(), 102);
  Store(attacker_army.data(), 0x10, std::int32_t{1});
  Store(attacker_army.data(), 0x124, std::int32_t{3});
  Store(attacker_army.data(), 0x128, std::int32_t{5});
  Store(defender_army.data(), 0x10, std::int32_t{2});
  Store(defender_army.data(), 0x124, std::int32_t{4});
  Store(defender_army.data(), 0x128, std::int32_t{5});
  Store(attacker_unit.data(), 0x10, std::int32_t{3});
  Store(attacker_unit.data(), 0x178, std::int32_t{1});
  Store(defender_unit.data(), 0x10, std::int32_t{4});
  Store(defender_unit.data(), 0x178, std::int32_t{2});
  Store(result.data(), 0x08, std::int32_t{6});
  Store(result.data(), 0x28, std::uint8_t{0});
  public_units.Put(3, attacker_unit.data());
  public_units.Put(4, defender_unit.data());
  internal_armies.Put(1, attacker_army.data());
  internal_armies.Put(2, defender_army.data());
  results.Put(6, result.data());
  Bindings bindings{};
  bindings.enabled = true;
  bindings.game_state_slot = &game_state_pointer;
  bindings.army_storage_slot = &public_units.pointer;
  bindings.army_internal_storage_slot = &internal_armies.pointer;
  bindings.battle_result_storage_slot = &results.pointer;
  if (!InitializeBattleTerminalJournalStorageV1(bindings)) {
    std::cerr << "journal storage init failed\n";
    return false;
  }
  if (!CaptureBattleTerminalJournalEntryV1(combat.data(), false)) {
    const auto failed = LookupBattleTerminalJournalV1(5, 0);
    std::cerr << "normal capture failed flags="
              << failed.event.capture_failure_flags << " status="
              << static_cast<unsigned>(failed.status) << "\n";
    return false;
  }
  const auto normal = LookupBattleTerminalJournalV1(5, 0);
  if (normal.status != BattleTerminalJournalLookupStatusV1::observed ||
      normal.event.sequence != 1 ||
      normal.event.suppress_normal_result_envelopes ||
      normal.event.attacker_public_cunit_ids_in_stored_order[0] != 3 ||
      normal.event.defender_public_cunit_ids_in_stored_order[0] != 4) {
    std::cerr << "normal lookup mismatch status="
              << static_cast<unsigned>(normal.status) << " seq="
              << normal.event.sequence << " oldest="
              << normal.oldest_available_sequence << " latest="
              << normal.latest_sequence << "\n";
    return false;
  }
  if (!CaptureBattleTerminalJournalEntryV1(combat.data(), true)) {
    std::cerr << "no-normal capture failed\n";
    return false;
  }
  const auto no_normal = LookupBattleTerminalJournalV1(5, 1);
  if (no_normal.status != BattleTerminalJournalLookupStatusV1::observed ||
      no_normal.event.sequence != 2 ||
      !no_normal.event.suppress_normal_result_envelopes) {
    std::cerr << "no-normal lookup mismatch\n";
    return false;
  }
  if (!InitializeBattleTerminalJournalStorageV1(bindings)) {
    return false;
  }
  for (std::size_t index = 0; index < kBattleTerminalJournalCapacityV1;
       ++index) {
    if (!CaptureBattleTerminalJournalEntryV1(combat.data(), false)) {
      std::cerr << "overflow capture failed at " << index << "\n";
      return false;
    }
  }
  const auto exactly_full = LookupBattleTerminalJournalV1(5, 0);
  if (exactly_full.status !=
          BattleTerminalJournalLookupStatusV1::observed ||
      exactly_full.oldest_available_sequence != 1 ||
      exactly_full.latest_sequence != kBattleTerminalJournalCapacityV1 ||
      !CaptureBattleTerminalJournalEntryV1(combat.data(), false) ||
      LookupBattleTerminalJournalV1(5, 0).status !=
          BattleTerminalJournalLookupStatusV1::journal_gap ||
      LookupBattleTerminalJournalV1(5, 1).status !=
          BattleTerminalJournalLookupStatusV1::observed ||
      !CaptureBattleTerminalJournalEntryV1(combat.data(), false) ||
      LookupBattleTerminalJournalV1(5, 1).status !=
          BattleTerminalJournalLookupStatusV1::journal_gap) {
    std::cerr << "overflow gap mismatch exact="
              << static_cast<unsigned>(exactly_full.status)
              << " after0="
              << static_cast<unsigned>(LookupBattleTerminalJournalV1(5, 0).status)
              << " after1="
              << static_cast<unsigned>(LookupBattleTerminalJournalV1(5, 1).status)
              << "\n";
    return false;
  }

  constexpr std::array<std::uint8_t, 19> terminal_prologue{
      0x48, 0x8B, 0xC4, 0x88, 0x50, 0x10, 0x48, 0x89, 0x48, 0x08,
      0x53, 0x55, 0x48, 0x81, 0xEC, 0xC8, 0x00, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 16> warscore_prologue{
      0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x18,
      0x56, 0x57, 0x41, 0x54, 0x41, 0x56};
  auto terminal_target = terminal_prologue;
  auto warscore_target = warscore_prologue;
  BattleTerminalJournalDetourStateV1 state{};
  BattleTerminalJournalInstallEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 1;
  environment.bindings = bindings;
  environment.terminal_target_override =
      reinterpret_cast<std::uintptr_t>(terminal_target.data());
  environment.warscore_target_override =
      reinterpret_cast<std::uintptr_t>(warscore_target.data());
  environment.virtual_protect_override = &FakeProtect;
  environment.flush_instruction_cache_override = &FakeFlush;
  const bool installed = InstallBattleTerminalJournalV1(state, environment);
  if (!installed) {
    std::cerr << "detour install flags="
              << state.failure_flags.load(std::memory_order_acquire) << "\n";
  }
  const bool final_ok = kBattleTerminalFinalizerPatchBytesV1 == 19 &&
         kBattleWarscoreWriterPatchBytesV1 == 16 && installed &&
         state.installed.load(std::memory_order_acquire) == 1 &&
         terminal_target[0] == 0xFF && terminal_target[1] == 0x25 &&
         warscore_target[0] == 0xFF && warscore_target[1] == 0x25;
  if (!final_ok) {
    std::cerr << "detour final identity mismatch installed=" << installed
              << " state=" << state.installed.load() << " terminal="
              << static_cast<unsigned>(terminal_target[0]) << ","
              << static_cast<unsigned>(terminal_target[1]) << " warscore="
              << static_cast<unsigned>(warscore_target[0]) << ","
              << static_cast<unsigned>(warscore_target[1]) << "\n";
  }
  return final_ok;
}

bool TestMailboxExecution() {
  using namespace xar::ck3_11906;
  g_snapshot = {};
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.date_raw = 1234;
  g_native_result = CompleteResult();
  g_native_result.snapshot_revision = 0;
  MainThreadQueryMailboxV1 mailbox{};
  BattleTerminalTransitionMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.bindings.enabled = true;
  query.request.prior_combat_id = 5;
  query.request.subject_public_cunit_id = 3;
  query.expected_snapshot_revision = 9;
  query.expected_snapshot = g_snapshot;
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(1);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(2);
  mailbox.executor = &ExecuteBattleTerminalTransitionMailboxQueryV1;
  mailbox.executor_context = &query;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 2;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = 1234;
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 1;
  stamp.game_state = 1;
  return ExecuteBattleTerminalTransitionMailboxQueryV1(&query, stamp) &&
         query.completion ==
             BattleTerminalTransitionMailboxCompletionV1::completed &&
         query.executor_invocations == 1 &&
         query.result.snapshot_revision == 9 &&
         query.result.subject.combat_backlink_id == std::nullopt;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const Bindings &, const game::Snapshot &,
    const game::BattleTerminalTransitionRequestV1 &,
    game::BattleTerminalTransitionSnapshotV1 &output) noexcept {
  output = g_native_result;
  return output.status;
}

} // namespace xar::ck3_11906

int main() {
  if (!TestParserAndSerializer()) {
    std::cerr << "battle-terminal parser/serializer test failed\n";
    return 1;
  }
  if (!TestJournalAndDetourAnchors()) {
    std::cerr << "battle-terminal journal/detour test failed\n";
    return 1;
  }
  if (!TestMailboxExecution()) {
    std::cerr << "battle-terminal mailbox test failed\n";
    return 1;
  }
  return 0;
}
