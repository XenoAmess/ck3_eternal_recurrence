#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

template <typename T, std::size_t Size>
void Store(std::array<std::byte, Size> &storage, std::size_t offset,
           T value) {
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename T>
void Store(void *storage, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(storage) + offset, &value,
              sizeof(value));
}

bool Fail(std::string_view reason) {
  std::cerr << reason << '\n';
  return false;
}

bool Has(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

struct Fixture {
  static constexpr std::int32_t kCombatId = 0x01000001;
  static constexpr std::int32_t kBattleResultId = 0x01000002;
  static constexpr std::array<std::int32_t, 2> kArmyIds{11, 21};
  static constexpr std::array<std::int32_t, 2> kRegimentIds{31, 41};
  static constexpr std::array<std::int32_t, 2> kCharacterIds{101, 201};
  static constexpr std::int32_t kAccoladeId = 51;

  std::array<std::byte, 0x720> combat{};
  std::array<std::array<std::byte, 0x130>, 2> armies{};
  std::array<std::array<std::byte, 0x150>, 2> regiments{};
  std::array<std::array<std::byte, 0x1D0>, 2> characters{};
  std::array<std::array<std::byte, 0x100>, 2> character_links{};
  std::array<std::byte, 0x570> accolade_link{};
  std::array<std::byte, 0xB8> accolade{};
  std::array<std::int64_t, 3> accolade_rank_thresholds{
      100'000, 500'000, 1'000'000};
  std::uintptr_t accolade_rank_threshold_data_slot = 0;
  std::int32_t accolade_rank_threshold_count_slot = 3;
  std::array<std::array<std::byte, 0x60>, 2> knight_entries{};
  std::array<std::array<std::byte, 0x10>, 2> schedule_rows{};
  std::array<std::int32_t, 2> side_army_ids{kArmyIds};
  std::array<std::byte, 0x1B0> battle_result{};
  std::array<std::array<std::byte, 0x38>, 2> battle_rows{};
  std::array<std::byte, 0x10> date_object{};
  std::array<std::byte, 0x18> rng_wrapper{};
  std::array<std::byte, 0x18> rng_state{};
  std::array<std::byte, 8> event_database{};
  std::array<std::byte, 8> battle_event_vtable{};
  std::uintptr_t date_slot = 0;
  std::uintptr_t rng_wrapper_slot = 0;
  std::uintptr_t event_database_slot = 0;
  std::array<std::uint32_t, 2> schedule_rng{700, 0};
  CombatPhaseEventTraceCapturePlanV1 plan{};

  Fixture() {
    const auto combat_pointer =
        reinterpret_cast<std::uintptr_t>(combat.data());
    const std::array<std::uintptr_t, 2> side_pointers{
        combat_pointer + 0x20, combat_pointer + 0x368};
    Store(combat, 0x08, kCombatId);
    Store(combat, 0x6B0, std::int32_t{1});
    Store(combat, 0x6B4, std::int32_t{4});
    Store(combat, 0x6C8, std::int64_t{300'000});
    Store(combat, 0x6D0, std::int32_t{2});
    Store(combat, 0x6D4, std::int32_t{5});
    Store(combat, 0x6E0, std::int32_t{-1});
    Store(combat, 0x708, kBattleResultId);
    Store(combat, 0x710, std::int64_t{600'000});

    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      auto *const side = reinterpret_cast<void *>(side_pointers[side_index]);
      Store(side, 0x10,
            reinterpret_cast<std::uintptr_t>(&side_army_ids[side_index]));
      Store(side, 0x18, std::int32_t{1});
      Store(side, 0x1C, std::int32_t{1});
      Store(side, 0x40,
            reinterpret_cast<std::uintptr_t>(
                knight_entries[side_index].data()));
      Store(side, 0x48, std::int32_t{1});
      Store(side, 0x4C, std::int32_t{1});
      Store(side, 0x74, kCharacterIds[side_index]);
      Store(side, 0x98,
            std::int64_t{1'000'000 +
                         static_cast<std::int64_t>(side_index) * 200'000});
      Store(side, 0xA0,
            std::int64_t{500'000 +
                         static_cast<std::int64_t>(side_index) * 100'000});
      Store(side, 0xB8, combat_pointer);
      Store(side, 0xD8,
            reinterpret_cast<std::uintptr_t>(
                schedule_rows[side_index].data()));
      Store(side, 0xE0, std::int32_t{1});
      Store(side, 0xE4, std::int32_t{0});
      Store(side, 0xF0,
            reinterpret_cast<std::uintptr_t>(event_database.data()) +
                side_index + 1);

      Store(armies[side_index], 0x10, kArmyIds[side_index]);
      Store(armies[side_index], 0x120, kCharacterIds[side_index]);
      Store(armies[side_index], 0x128, kCombatId);
      Store(knight_entries[side_index], 0x08,
            kRegimentIds[side_index]);
      Store(regiments[side_index], 0x10, kRegimentIds[side_index]);
      Store(regiments[side_index], 0x140, kArmyIds[side_index]);
      Store(regiments[side_index], 0x148, kCharacterIds[side_index]);
      Store(characters[side_index], 0x18, kCharacterIds[side_index]);
      Store(characters[side_index], 0xD8,
            std::int32_t{10 + static_cast<std::int32_t>(side_index)});
      Store(characters[side_index], 0xE4,
            std::int32_t{8 + static_cast<std::int32_t>(side_index)});
      Store(characters[side_index], 0xE8,
            std::int32_t{15 + static_cast<std::int32_t>(side_index)});
      Store(character_links[side_index], 0xF8,
            kRegimentIds[side_index]);
      Store(characters[side_index], 0x1B0,
            reinterpret_cast<std::uintptr_t>(
                character_links[side_index].data()));
    }
    Store(accolade_link, 0x568, kAccoladeId);
    Store(characters[0], 0x1A8,
          reinterpret_cast<std::uintptr_t>(accolade_link.data()));
    Store(accolade, 0x08, kAccoladeId);
    Store(accolade, 0x70, std::int32_t{901});
    Store(accolade, 0xB0, std::int64_t{600'000});
    accolade_rank_threshold_data_slot =
        reinterpret_cast<std::uintptr_t>(accolade_rank_thresholds.data());

    Store(battle_result, 0x08, kBattleResultId);
    Store(battle_result, 0x188,
          reinterpret_cast<std::uintptr_t>(battle_rows.data()));
    Store(battle_result, 0x190, std::int32_t{2});
    Store(battle_result, 0x194, std::int32_t{0});
    Store(date_object, 0x08, std::int32_t{53'175'816});
    Store(rng_wrapper, 0x00,
          reinterpret_cast<std::uintptr_t>(rng_state.data()));
    Store(rng_state, 0x08, std::uint32_t{100});
    Store(rng_state, 0x0C, std::uint32_t{0x12345678});
    Store(rng_state, 0x10, std::uint32_t{77});
    date_slot = reinterpret_cast<std::uintptr_t>(date_object.data());
    rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(rng_wrapper.data());
    event_database_slot =
        reinterpret_cast<std::uintptr_t>(event_database.data());

    plan.managed_daily_sequence_token = 9;
    plan.module_base = 0x0000000140000000ULL;
    plan.combat_id = kCombatId;
    plan.combat = combat_pointer;
    plan.sides = side_pointers;
    plan.phase_event_database_slot =
        reinterpret_cast<std::uintptr_t>(&event_database_slot);
    plan.expected_phase_event_database = event_database_slot;
    plan.current_date_slot = reinterpret_cast<std::uintptr_t>(&date_slot);
    plan.expected_current_date_object = date_slot;
    plan.global_rng_wrapper_slot =
        reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot);
    plan.expected_global_rng_wrapper = rng_wrapper_slot;
    plan.expected_global_rng_state =
        reinterpret_cast<std::uintptr_t>(rng_state.data());
    plan.battle_result_id = kBattleResultId;
    plan.battle_result =
        reinterpret_cast<std::uintptr_t>(battle_result.data());
    plan.expected_battle_event_vtable =
        reinterpret_cast<std::uintptr_t>(battle_event_vtable.data());
    plan.army_count = 2;
    plan.regiment_count = 2;
    plan.character_count = 2;
    for (std::size_t index = 0; index < 2; ++index) {
      plan.armies[index] = {
          kArmyIds[index],
          reinterpret_cast<std::uintptr_t>(armies[index].data())};
      plan.regiments[index] = {
          kRegimentIds[index],
          reinterpret_cast<std::uintptr_t>(regiments[index].data())};
      plan.characters[index] = {
          kCharacterIds[index],
          reinterpret_cast<std::uintptr_t>(characters[index].data())};
    }
    plan.accolade_rank_threshold_data_slot =
        reinterpret_cast<std::uintptr_t>(
            &accolade_rank_threshold_data_slot);
    plan.expected_accolade_rank_threshold_data =
        accolade_rank_threshold_data_slot;
    plan.accolade_rank_threshold_count_slot =
        reinterpret_cast<std::uintptr_t>(
            &accolade_rank_threshold_count_slot);
    plan.accolade_rank_threshold_count = 3;
    std::copy(accolade_rank_thresholds.begin(),
              accolade_rank_thresholds.end(),
              plan.accolade_rank_thresholds_raw.begin());
    plan.accolade_count = 1;
    plan.accolades[0] = {
        kAccoladeId,
        reinterpret_cast<std::uintptr_t>(accolade.data()),
        901,
        kCharacterIds[0],
        reinterpret_cast<std::uintptr_t>(characters[0].data())};
  }

  void SetSchedule(std::size_t side_index) {
    Store(schedule_rows[side_index], 0x00,
          reinterpret_cast<std::uintptr_t>(event_database.data()) +
              0x100 + side_index);
    Store(schedule_rows[side_index], 0x08,
          kRegimentIds[side_index]);
    Store(reinterpret_cast<void *>(plan.sides[side_index]), 0xE4,
          std::int32_t{1});
  }

  void SetBattleRow(std::size_t index, std::string_view key,
                    std::int32_t type, bool side0) {
    auto &row = battle_rows[index];
    Store(row, 0x00, plan.expected_battle_event_vtable);
    Store(row, 0x08, kCharacterIds[0]);
    Store(row, 0x0C, kCharacterIds[1]);
    std::memcpy(row.data() + 0x10, key.data(), key.size());
    Store(row, 0x20, key.size());
    Store(row, 0x28, std::size_t{15});
    Store(row, 0x30, type);
    Store(row, 0x34, static_cast<std::uint8_t>(side0 ? 1 : 0));
    Store(row, 0x35, std::uint8_t{1});
    Store(battle_result, 0x194,
          static_cast<std::int32_t>(index + 1));
  }
};

bool CaptureSevenRecordFixture() {
  Fixture fixture;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  auto drain = std::make_unique<CombatPhaseEventTraceRingDrainV1>();
  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("arm failed");
  }
  const auto schedule0_return =
      fixture.plan.module_base + kCombatPhaseEventScheduleSide0ReturnRva;
  const auto schedule1_return =
      fixture.plan.module_base + kCombatPhaseEventScheduleSide1ReturnRva;
  const auto fire0_return =
      fixture.plan.module_base + kCombatPhaseEventFireSide0ReturnRva;
  const auto fire1_return =
      fixture.plan.module_base + kCombatPhaseEventFireSide1ReturnRva;

  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(), schedule0_return)) {
    return Fail("before schedule capture failed");
  }
  fixture.SetSchedule(0);
  fixture.SetSchedule(1);
  fixture.schedule_rng = {703, 3};
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side1_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[1]),
          fixture.schedule_rng.data(), schedule1_return)) {
    return Fail("after schedule capture failed");
  }

  Store(fixture.combat, 0x6B4, std::int32_t{5});
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]), nullptr,
          fire0_return)) {
    return Fail("before side0 fire capture failed");
  }
  Store(fixture.rng_state, 0x08, std::uint32_t{101});
  Store(fixture.characters[0], 0xE8, std::int32_t{16});
  Store(fixture.characters[0], 0x1C8, std::uintptr_t{1});
  Store(fixture.accolade, 0xB0, std::int64_t{1'100'000});
  fixture.SetBattleRow(0, "phase.hit", 2, true);
  Store(reinterpret_cast<void *>(fixture.plan.sides[0]), 0x98,
        std::int64_t{900'000});
  Store(fixture.combat, 0x710, std::int64_t{700'000});
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]), nullptr,
          fire0_return)) {
    return Fail("after side0 fire capture failed");
  }
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[1]), nullptr,
          fire1_return)) {
    return Fail("before side1 fire capture failed");
  }
  Store(fixture.rng_state, 0x08, std::uint32_t{102});
  fixture.SetBattleRow(1, "phase.reply", 3, false);
  Store(reinterpret_cast<void *>(fixture.plan.sides[1]), 0x98,
        std::int64_t{1'000'000});
  Store(fixture.combat, 0x710, std::int64_t{500'000});
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[1]), nullptr,
          fire1_return)) {
    return Fail("after side1 fire capture failed");
  }
  if (!CompleteAndDrainCombatPhaseEventTraceRingV1(*ring, *drain)) {
    return Fail("complete/drain failed");
  }

  const auto &records = drain->records;
  if (drain->record_count != 7 || !drain->exact_boundary_sequence ||
      !drain->same_full_generation_combat || !drain->same_native_date ||
      !drain->same_loaded_event_table ||
      !drain->side_and_return_site_identity ||
      !drain->schedule_phase_day_then_single_increment ||
      !drain->bounded_capture_complete ||
      drain->full_mutable_transition_bundle_complete ||
      drain->production_trace_ready) {
    return Fail("drain gates mismatch");
  }
  if (!records[0].schedule_local_rng_present ||
      records[0].schedule_local_rng_word0 != 700 ||
      records[1].schedule_local_rng_word0 != 703 ||
      records[1].schedule_local_rng_word1 != 3 ||
      records[2].schedule_local_rng_present ||
      records[0].sides[0].scheduled_knight_count != 0 ||
      records[1].sides[0].scheduled_knight_count != 1 ||
      records[1].sides[1].scheduled_knight_count != 1) {
    return Fail("schedule/local RNG delta mismatch");
  }
  if (records[2].battle_event_count != 0 ||
      records[3].battle_event_count != 1 ||
      records[5].battle_event_count != 2 ||
      records[6].battle_event_count != 2 ||
      records[3].battle_events[0].stable_key_size != 9 ||
      std::memcmp(records[3].battle_events[0].stable_key.data(),
                  "phase.hit", 9) != 0 ||
      records[5].battle_events[1].stable_key_size != 11 ||
      std::memcmp(records[5].battle_events[1].stable_key.data(),
                  "phase.reply", 11) != 0) {
    return Fail("battle ledger delta mismatch");
  }
  if (records[2].global_rng_counter != 100 ||
      records[3].global_rng_counter != 101 ||
      records[5].global_rng_counter != 102 ||
      records[2].characters[0].prowess != 15 ||
      records[3].characters[0].prowess != 16 ||
      records[2].characters[0].death_marker_present ||
      !records[3].characters[0].death_marker_present ||
      records[2].sides[0].current_fighting_total_raw != 1'000'000 ||
      records[3].sides[0].current_fighting_total_raw != 900'000 ||
      records[2].resolved_advantage_raw != 600'000 ||
      records[3].resolved_advantage_raw != 700'000 ||
      records[5].resolved_advantage_raw != 500'000 ||
      records[2].accolade_count != 1 ||
      records[2].accolades[0].accolade_id != Fixture::kAccoladeId ||
      records[2].accolades[0].glory_raw != 600'000 ||
      records[2].accolades[0].rank_native_mirror != 2 ||
      records[3].accolades[0].glory_raw != 1'100'000 ||
      records[3].accolades[0].rank_native_mirror != 3 ||
      !records[3].accolades[0].participant_link_identity_matches) {
    return Fail("mutable core/strength/RNG delta mismatch");
  }
  return true;
}

bool FailureCases() {
  Fixture fixture;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  const auto schedule0_return =
      fixture.plan.module_base + kCombatPhaseEventScheduleSide0ReturnRva;

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("sequence fixture arm failed");
  }
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side1_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[1]),
          fixture.schedule_rng.data(),
          fixture.plan.module_base +
              kCombatPhaseEventScheduleSide1ReturnRva) ||
      (ring->failure_flags.load() & trace_capture_failure_sequence) == 0) {
    return Fail("out-of-order boundary did not fail closed");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("identity fixture arm failed");
  }
  Store(fixture.combat, 0x08, Fixture::kCombatId + 1);
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(), schedule0_return) ||
      (ring->failure_flags.load() & trace_capture_failure_identity) == 0) {
    return Fail("CombatID mutation did not fail closed");
  }
  Store(fixture.combat, 0x08, Fixture::kCombatId);
  CancelCombatPhaseEventTraceRingV1(*ring);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("capacity fixture arm failed");
  }
  Store(fixture.battle_result, 0x190,
        static_cast<std::int32_t>(
            kCombatPhaseEventTraceRingV1MaximumBattleEvents + 1));
  Store(fixture.battle_result, 0x194,
        static_cast<std::int32_t>(
            kCombatPhaseEventTraceRingV1MaximumBattleEvents + 1));
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(), schedule0_return) ||
      (ring->failure_flags.load() & trace_capture_failure_capacity) == 0) {
    return Fail("capacity overflow did not fail closed");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  return true;
}

bool SourceContract(std::string_view path) {
  std::ifstream stream{std::string(path), std::ios::binary};
  const std::string contents{std::istreambuf_iterator<char>(stream),
                             std::istreambuf_iterator<char>()};
  constexpr std::array<std::string_view, 13> required{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x23C8750",
      "0x23C9900",
      "0x27FB594",
      "0x27FB5AC",
      "0x2309EF7",
      "0x2309EFF",
      "managed_query_owned_fixed_width_ring",
      "atomic_fail_closed_no_truncation",
      "component_store_resolution",
      "detour_installer_ready\": true",
      "full_mutable_transition_bundle_ready\": false",
      "production_capability_must_remain_closed\": true",
  };
  if (!stream && contents.empty()) {
    return Fail("source contract fixture could not be read");
  }
  for (const auto token : required) {
    if (!Has(contents, token)) {
      return Fail("source contract fixture token missing");
    }
  }
  return true;
}

bool SourceCodeContract(std::string_view path) {
  std::ifstream stream{std::string(path), std::ios::binary};
  const std::string contents{std::istreambuf_iterator<char>(stream),
                             std::istreambuf_iterator<char>()};
  constexpr std::array<std::string_view, 19> required{
      "kCombatPhaseEventScheduleSide0ReturnRva",
      "kCombatPhaseEventScheduleSide1ReturnRva",
      "kCombatPhaseEventFireSide0ReturnRva",
      "kCombatPhaseEventFireSide1ReturnRva",
      "CaptureCombatPhaseEventTraceBoundaryV1",
      "CaptureWithFaultBoundary",
      "schedule_local_rng_word0",
      "global_rng_counter",
      "kSideScheduledKnightHeaderOffset",
      "kBattleEventHeaderOffset",
      "kCharacterDeathMarkerOffset",
      "kCharacterAccoladeLinkOffset",
      "kCharacterLinkAccoladeIdOffset",
      "kAccoladeGloryOffset",
      "MirrorAccoladeRank",
      "accolade_rank_threshold_count",
      "kSideCurrentFightingTotalOffset",
      "kCombatResolvedAdvantageOffset",
      "production_trace_ready",
  };
  constexpr std::array<std::string_view, 11> forbidden{
      "std::vector",
      "std::string",
      "operator new",
      "malloc(",
      "ReadSnapshot",
      "SetPaused",
      "bridge::",
      "service::",
      "0x356A0A0",
      "EvaluateTrigger",
      "EvaluateValue",
  };
  if (!stream && contents.empty()) {
    return Fail("ring source could not be read");
  }
  for (const auto token : required) {
    if (!Has(contents, token)) {
      return Fail("ring source required token missing");
    }
  }
  for (const auto token : forbidden) {
    if (Has(contents, token)) {
      return Fail("ring source contains forbidden capture-path token");
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  static_assert(std::is_trivially_copyable_v<
                CombatPhaseEventTraceRingRecordV1>);
  static_assert(std::is_trivially_copyable_v<
                CombatPhaseEventTraceCapturePlanV1>);
  if (argc != 3 || !SourceContract(argv[1]) ||
      !SourceCodeContract(argv[2]) ||
      !CaptureSevenRecordFixture() || !FailureCases() ||
      BindCombatPhaseEventTraceOriginalTrampolinesV1(nullptr, nullptr)) {
    return 1;
  }
  return 0;
}
