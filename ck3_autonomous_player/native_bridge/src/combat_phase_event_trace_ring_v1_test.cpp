#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <windows.h>

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
  static constexpr std::array<std::int32_t, 2> kLevyRegimentIds{32, 42};
  static constexpr std::array<std::int32_t, 2> kCharacterIds{101, 201};
  static constexpr std::int32_t kAccoladeId = 51;

  std::array<std::byte, 0x720> combat{};
  std::array<std::array<std::byte, 0x130>, 2> armies{};
  std::array<std::array<std::byte, 0x150>, 2> regiments{};
  std::array<std::array<std::byte, 0x150>, 2> levy_regiments{};
  std::array<std::array<std::byte, 0xA10>, 2> combat_types{};
  std::array<std::array<std::byte, 0xA10>, 2> levy_combat_types{};
  std::array<std::array<std::byte, 0x1D0>, 2> characters{};
  std::array<std::array<std::byte, 0x100>, 2> character_links{};
  std::array<std::byte, 0x570> accolade_link{};
  std::array<std::byte, 0xB8> accolade{};
  std::array<std::int64_t, 3> accolade_rank_thresholds{
      100'000, 500'000, 1'000'000};
  std::uintptr_t accolade_rank_threshold_data_slot = 0;
  std::int32_t accolade_rank_threshold_count_slot = 3;
  std::array<std::array<std::byte, 0x60>, 2> knight_entries{};
  std::array<std::array<std::byte, 0x60>, 2> levy_entries{};
  std::array<std::array<std::byte, 0x18>, 2> hard_owner_rows{};
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
      Store(side, 0x28,
            reinterpret_cast<std::uintptr_t>(
                levy_entries[side_index].data()));
      Store(side, 0x30, std::int32_t{1});
      Store(side, 0x34, std::int32_t{1});
      Store(side, 0x40,
            reinterpret_cast<std::uintptr_t>(
                knight_entries[side_index].data()));
      Store(side, 0x48, std::int32_t{1});
      Store(side, 0x4C, std::int32_t{1});
      Store(side, 0x58,
            reinterpret_cast<std::uintptr_t>(
                hard_owner_rows[side_index].data()));
      Store(side, 0x60, std::int32_t{1});
      Store(side, 0x64, std::int32_t{1});
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
      Store(knight_entries[side_index], 0x10, std::int64_t{1'000'000});
      Store(knight_entries[side_index], 0x18, std::int64_t{1'000'000});
      Store(knight_entries[side_index], 0x40, std::int64_t{200'000});
      Store(knight_entries[side_index], 0x48, std::int64_t{150'000});
      Store(levy_entries[side_index], 0x08,
            kLevyRegimentIds[side_index]);
      Store(levy_entries[side_index], 0x10, std::int64_t{500'000});
      Store(levy_entries[side_index], 0x18, std::int64_t{0});
      Store(levy_entries[side_index], 0x40, std::int64_t{80'000});
      Store(levy_entries[side_index], 0x48, std::int64_t{60'000});
      Store(hard_owner_rows[side_index], 0x08,
            kCharacterIds[side_index]);
      Store(hard_owner_rows[side_index], 0x10, std::int64_t{0});
      Store(regiments[side_index], 0x10, kRegimentIds[side_index]);
      Store(regiments[side_index], 0x18,
            reinterpret_cast<std::uintptr_t>(
                combat_types[side_index].data()));
      Store(regiments[side_index], 0x140, kArmyIds[side_index]);
      Store(regiments[side_index], 0x148, kCharacterIds[side_index]);
      Store(levy_regiments[side_index], 0x10,
            kLevyRegimentIds[side_index]);
      Store(levy_regiments[side_index], 0x18,
            reinterpret_cast<std::uintptr_t>(
                levy_combat_types[side_index].data()));
      Store(levy_regiments[side_index], 0x140, kArmyIds[side_index]);
      Store(combat_types[side_index], 0xA0A, std::uint8_t{1});
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
    Store(rng_state, 0x10, std::uint32_t{GetCurrentThreadId()});
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
    plan.battle_result_id = kBattleResultId;
    plan.battle_result =
        reinterpret_cast<std::uintptr_t>(battle_result.data());
    plan.expected_battle_event_vtable =
        reinterpret_cast<std::uintptr_t>(battle_event_vtable.data());
    plan.army_count = 2;
    plan.regiment_count = 4;
    plan.character_count = 2;
    for (std::size_t index = 0; index < 2; ++index) {
      plan.armies[index] = {
          kArmyIds[index],
          reinterpret_cast<std::uintptr_t>(armies[index].data())};
      plan.regiments[index * 2] = {
          kRegimentIds[index],
          reinterpret_cast<std::uintptr_t>(regiments[index].data())};
      plan.regiments[index * 2 + 1] = {
          kLevyRegimentIds[index],
          reinterpret_cast<std::uintptr_t>(levy_regiments[index].data())};
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

bool CaptureSevenRecordFixture(std::int32_t date_delta = 24) {
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

  Store(fixture.date_object, 0x08,
        std::int32_t{53'175'816 + date_delta});
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
  Store(fixture.knight_entries[0], 0x18, std::int64_t{900'000});
  Store(fixture.knight_entries[0], 0x20, std::int64_t{50'000});
  Store(fixture.hard_owner_rows[0], 0x10, std::int64_t{50'000});
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
  Store(fixture.knight_entries[1], 0x18, std::int64_t{850'000});
  Store(fixture.knight_entries[1], 0x20, std::int64_t{100'000});
  Store(fixture.hard_owner_rows[1], 0x10, std::int64_t{50'000});
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
  const std::int64_t side0_damage_raw = 310'000;
  const std::int64_t side1_damage_raw = 280'000;
  constexpr std::int64_t side0_attack_raw = 10'333'333;
  constexpr std::int64_t side1_attack_raw = 6'222'222;
  CaptureCombatPostCounterAttackV1(
      reinterpret_cast<void *>(fixture.plan.sides[0]),
      side0_attack_raw, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if (!CaptureCombatOutgoingDamageV1(
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          reinterpret_cast<void *>(fixture.plan.sides[1]),
          &side0_damage_raw,
          fixture.plan.module_base +
              kCombatOutgoingDamageSide0ReturnRva)) {
    return Fail("side0 outgoing damage capture failed");
  }
  CaptureCombatPostCounterAttackV1(
      reinterpret_cast<void *>(fixture.plan.sides[1]), side1_attack_raw,
      fixture.plan.sides[1],
      fixture.plan.module_base + kCombatOutgoingDamageSide1ReturnRva);
  if (!CaptureCombatOutgoingDamageV1(
          reinterpret_cast<void *>(fixture.plan.sides[1]),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          &side1_damage_raw,
          fixture.plan.module_base +
              kCombatOutgoingDamageSide1ReturnRva)) {
    return Fail("pre-casualty outgoing damage pair capture failed");
  }
  const bool captured = CompleteAndDrainCombatPhaseEventTraceRingV1(*ring, *drain);
  if (captured != (date_delta == 24)) {
    return Fail("one-day date split admission mismatch");
  }
  if (date_delta != 24) {
    return drain->record_count == 7 &&
           !drain->expected_one_day_date_split &&
           !drain->bounded_capture_complete &&
           drain->failure_flags == trace_capture_failure_none;
  }

  const auto &records = drain->records;
  if (drain->record_count != 7 || !drain->exact_boundary_sequence ||
      !drain->same_full_generation_combat || drain->same_native_date ||
      !drain->expected_one_day_date_split ||
      !drain->same_loaded_event_table ||
      !drain->side_and_return_site_identity ||
      !drain->schedule_phase_day_then_single_increment ||
      !drain->bounded_capture_complete ||
      !drain->outgoing_damage_pair_complete ||
      !drain->post_counter_attack_pair_complete ||
      drain->outgoing_damage_count != 2 ||
      drain->post_counter_attack_count != 2 ||
      drain->outgoing_damage_raw[0] != side0_damage_raw ||
      drain->outgoing_damage_raw[1] != side1_damage_raw ||
      drain->post_counter_attack_raw[0] != side0_attack_raw ||
      drain->post_counter_attack_raw[1] != side1_attack_raw ||
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
      records[2].sides[0].regiment_count != 2 ||
      records[2].sides[0].regiments[0].regiment_id !=
          Fixture::kLevyRegimentIds[0] ||
      records[2].sides[0].regiments[0].hard_casualties_available ||
      records[2].sides[0].regiments[1].regiment_id !=
          Fixture::kRegimentIds[0] ||
      records[2].sides[0].regiments[1].current_fighting_raw !=
          1'000'000 ||
      records[3].sides[0].regiments[1].current_fighting_raw !=
          900'000 ||
      records[3].sides[0].regiments[1].soft_casualties_raw !=
          50'000 ||
      records[3].sides[0].regiments[1].hard_casualties_raw !=
          50'000 ||
      records[2].sides[0].hard_owners[0].hard_casualties_raw != 0 ||
      records[3].sides[0].hard_owners[0].hard_casualties_raw !=
          50'000 ||
      records[5].sides[1].regiments[1].hard_casualties_raw !=
          50'000 ||
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
    return Fail("regiment identity fixture arm failed");
  }
  Store(fixture.levy_regiments[0], 0x10,
        Fixture::kLevyRegimentIds[0] + 1);
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(), schedule0_return) ||
      (ring->failure_flags.load() & trace_capture_failure_identity) == 0) {
    return Fail("retained levy generation mutation did not fail closed");
  }
  Store(fixture.levy_regiments[0], 0x10,
        Fixture::kLevyRegimentIds[0]);
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

  Store(fixture.battle_result, 0x190, std::int32_t{2});
  Store(fixture.battle_result, 0x194, std::int32_t{0});
  Store(fixture.rng_wrapper, 0x00, std::uintptr_t{0});
  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan) ||
      !CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(), schedule0_return) ||
      !CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::after_side1_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[1]),
          fixture.schedule_rng.data(),
          fixture.plan.module_base +
              kCombatPhaseEventScheduleSide1ReturnRva)) {
    return Fail("scoped RNG fixture could not record nullable schedule");
  }
  Store(fixture.rng_wrapper, 0x00,
        reinterpret_cast<std::uintptr_t>(fixture.rng_state.data()));
  Store(fixture.rng_state, 0x10,
        std::uint32_t{GetCurrentThreadId() + 1});
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]), nullptr,
          fixture.plan.module_base +
              kCombatPhaseEventFireSide0ReturnRva) ||
      (ring->failure_flags.load() & trace_capture_failure_rng_scope) == 0) {
    return Fail("foreign-thread RNG was admitted at original fire");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  Fixture unknown_schedule_fixture;
  unknown_schedule_fixture.SetSchedule(1);
  if (!ArmCombatPhaseEventTraceRingV1(*ring,
                                      unknown_schedule_fixture.plan)) {
    return Fail("unknown schedule identity fixture arm failed");
  }
  Store(unknown_schedule_fixture.schedule_rows[1], 0x08,
        Fixture::kRegimentIds[1] + 1000);
  if (CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          unknown_schedule_fixture.combat.data(),
          reinterpret_cast<void *>(unknown_schedule_fixture.plan.sides[0]),
          unknown_schedule_fixture.schedule_rng.data(),
          unknown_schedule_fixture.plan.module_base +
              kCombatPhaseEventScheduleSide0ReturnRva) ||
      (ring->failure_flags.load() & trace_capture_failure_identity) == 0) {
    return Fail("unknown scheduled regiment identity did not fail");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  return true;
}

bool StaleScheduledKnightCase() {
  Fixture fixture;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  fixture.SetSchedule(1);
  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("retained schedule fixture arm failed");
  }
  // The killed knight has left the live side, while its scheduled event still
  // names the regiment. Its prearmed component pointer has been reused.
  Store(reinterpret_cast<void *>(fixture.plan.sides[1]), 0x4C,
        std::int32_t{0});
  Store(fixture.regiments[1], 0x10, Fixture::kRegimentIds[1] + 1);
  Store(fixture.characters[1], 0x1B0, std::uintptr_t{0});
  if (!CaptureCombatPhaseEventTraceBoundaryV1(
          CombatPhaseEventTraceBoundaryV1::before_side0_schedule,
          fixture.combat.data(),
          reinterpret_cast<void *>(fixture.plan.sides[0]),
          fixture.schedule_rng.data(),
          fixture.plan.module_base +
              kCombatPhaseEventScheduleSide0ReturnRva) ||
      ring->committed_count.load() != 1 ||
      ring->failure_flags.load() != trace_capture_failure_none ||
      ring->records[0].sides[1].knight_count != 0 ||
      ring->records[0].sides[1].scheduled_knight_count != 1 ||
      ring->records[0].sides[1].scheduled_knights[0].regiment_id !=
          Fixture::kRegimentIds[1] ||
      ring->records[0].sides[1].scheduled_knights[0].current_character_id !=
          -1) {
    return Fail("retained schedule after knight removal was not captured");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  return true;
}

bool OutgoingDamageCaptureCases() {
  Fixture fixture;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  const std::int64_t side0_damage_raw = 310'000;
  const std::int64_t side1_damage_raw = 280'000;
  const auto side0_return = fixture.plan.module_base +
                            kCombatOutgoingDamageSide0ReturnRva;
  const auto side1_return = fixture.plan.module_base +
                            kCombatOutgoingDamageSide1ReturnRva;
  auto *const side0 = reinterpret_cast<void *>(fixture.plan.sides[0]);
  auto *const side1 = reinterpret_cast<void *>(fixture.plan.sides[1]);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("outgoing damage fixture arm failed");
  }
  ring->committed_count.store(6);
  if (CaptureCombatOutgoingDamageV1(reinterpret_cast<void *>(3), side1,
                                    &side0_damage_raw, side0_return) ||
      ring->failure_flags.load() != trace_capture_failure_none ||
      CaptureCombatOutgoingDamageV1(side1, side0, &side1_damage_raw,
                                    side1_return) ||
      (ring->failure_flags.load() &
       trace_capture_failure_outgoing_damage) == 0) {
    return Fail("outgoing damage side order was accepted");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("outgoing damage identity fixture arm failed");
  }
  ring->committed_count.store(6);
  if (CaptureCombatOutgoingDamageV1(side0, side1, &side0_damage_raw,
                                    side0_return - 1) ||
      ring->failure_flags.load() != trace_capture_failure_none ||
      !CaptureCombatOutgoingDamageV1(side0, side1,
                                     &side0_damage_raw, side0_return) ||
      CaptureCombatOutgoingDamageV1(side0, side1, &side0_damage_raw,
                                    side0_return) ||
      (ring->failure_flags.load() &
       trace_capture_failure_outgoing_damage) == 0) {
    return Fail("outgoing damage return site or duplicate was accepted");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("outgoing damage CombatID fixture arm failed");
  }
  ring->committed_count.store(6);
  Store(fixture.combat, 0x08, Fixture::kCombatId + 1);
  if (CaptureCombatOutgoingDamageV1(side0, side1, &side0_damage_raw,
                                    side0_return) ||
      (ring->failure_flags.load() &
       trace_capture_failure_outgoing_damage) == 0) {
    return Fail("outgoing damage changed CombatID was accepted");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  return true;
}

bool PostCounterAttackCaptureCases() {
  Fixture fixture;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  auto *const side0 = reinterpret_cast<void *>(fixture.plan.sides[0]);
  auto *const side1 = reinterpret_cast<void *>(fixture.plan.sides[1]);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("post-counter fixture arm failed");
  }
  ring->committed_count.store(6);
  CaptureCombatPostCounterAttackV1(
      reinterpret_cast<void *>(3), 91'000, 3,
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if (ring->post_counter_attack_count.load() != 0 ||
      ring->failure_flags.load() != trace_capture_failure_none) {
    return Fail("foreign combat post-counter attack was captured");
  }
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva - 1);
  if (ring->post_counter_attack_count.load() != 0 ||
      ring->failure_flags.load() != trace_capture_failure_none) {
    return Fail("foreign calculator return was captured");
  }
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[1],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if (ring->post_counter_attack_count.load() != 0 ||
      ring->failure_flags.load() != trace_capture_failure_none) {
    return Fail("mismatched outer side was captured");
  }
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if (ring->post_counter_attack_count.load() != 1 ||
      ring->post_counter_attack_raw[0] != 310'000 ||
      ring->failure_flags.load() != trace_capture_failure_none) {
    return Fail("first post-counter attack was not captured");
  }
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if ((ring->failure_flags.load() &
       trace_capture_failure_post_counter_attack) == 0) {
    return Fail("duplicate post-counter attack was accepted");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("post-counter changed CombatID fixture arm failed");
  }
  ring->committed_count.store(6);
  Store(fixture.combat, 0x08, Fixture::kCombatId + 1);
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  if (ring->post_counter_attack_count.load() != 0 ||
      (ring->failure_flags.load() &
       trace_capture_failure_post_counter_attack) == 0) {
    return Fail("changed CombatID post-counter attack was accepted");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);

  Store(fixture.combat, 0x08, Fixture::kCombatId);
  if (!ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan)) {
    return Fail("post-counter pair fixture arm failed");
  }
  ring->committed_count.store(6);
  CaptureCombatPostCounterAttackV1(
      side0, 310'000, fixture.plan.sides[0],
      fixture.plan.module_base + kCombatOutgoingDamageSide0ReturnRva);
  ring->outgoing_damage_count.store(1);
  CaptureCombatPostCounterAttackV1(
      side1, 280'000, fixture.plan.sides[1],
      fixture.plan.module_base + kCombatOutgoingDamageSide1ReturnRva);
  if (ring->post_counter_attack_count.load() != 2 ||
      ring->post_counter_attack_raw[0] != 310'000 ||
      ring->post_counter_attack_raw[1] != 280'000 ||
      ring->failure_flags.load() != trace_capture_failure_none) {
    return Fail("post-counter attack pair was not captured in order");
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  return true;
}

std::uintptr_t DummySchedule(void *, std::uint32_t *, void *) { return 0; }
std::uintptr_t DummyFire(void *) { return 0; }
std::uintptr_t DummyOutgoingDamage(void *side, std::int64_t *output,
                                   std::int32_t width,
                                   std::int64_t multiplier_raw,
                                   void *opposite_side) {
  if (side != reinterpret_cast<void *>(1) ||
      opposite_side != reinterpret_cast<void *>(2) || width != 73 ||
      multiplier_raw != 150'000) {
    return 0;
  }
  *output = 42'000;
  return reinterpret_cast<std::uintptr_t>(output);
}

bool OutgoingDamageHookAbi() {
  if (!BindCombatPhaseEventTraceOriginalTrampolinesV1(
          &DummySchedule, &DummyFire, &DummyOutgoingDamage)) {
    return Fail("outgoing damage trampoline binding failed");
  }
  std::int64_t output = 0;
  const auto result = XarCombatOutgoingDamageHookV1(
      reinterpret_cast<void *>(1), &output, 73, 150'000,
      reinterpret_cast<void *>(2));
  return result == reinterpret_cast<std::uintptr_t>(&output) &&
                 output == 42'000
             ? true
             : Fail("outgoing damage hook changed original ABI/result");
}

std::uintptr_t DummyOutgoingWithPostCounter(void *side,
                                            std::int64_t *output,
                                            std::int32_t,
                                            std::int64_t,
                                            void *) {
  XarCaptureCombatPostCounterAttackV1(side, 123'456);
  *output = 654'321;
  return reinterpret_cast<std::uintptr_t>(output);
}

bool OuterCallerContextTransport() {
  // The executable stub gives the outer hook a known, real Win64 return
  // address. The fake original invokes the inner callback before returning.
  constexpr std::array<std::uint8_t, 31> stub_bytes{
      0x48, 0x83, 0xEC, 0x28,             // sub rsp, 0x28
      0x48, 0x8B, 0x44, 0x24, 0x50,       // fifth argument
      0x48, 0x89, 0x44, 0x24, 0x20,       // pass fifth argument
      0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, // mov rax, hook
      0xFF, 0xD0,                         // call rax
      0x48, 0x83, 0xC4, 0x28, 0xC3};     // add rsp, 0x28; ret
  auto *const page = static_cast<std::uint8_t *>(
      VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
  if (page == nullptr) {
    return Fail("outer caller stub allocation failed");
  }
  std::memcpy(page, stub_bytes.data(), stub_bytes.size());
  const auto hook = reinterpret_cast<std::uintptr_t>(
      &XarCombatOutgoingDamageHookV1);
  std::memcpy(page + 16, &hook, sizeof(hook));
  DWORD old_protection = 0;
  if (!VirtualProtect(page, 4096, PAGE_EXECUTE_READ, &old_protection) ||
      !FlushInstructionCache(GetCurrentProcess(), page, stub_bytes.size())) {
    VirtualFree(page, 0, MEM_RELEASE);
    return Fail("outer caller stub preparation failed");
  }

  Fixture fixture;
  fixture.plan.module_base = reinterpret_cast<std::uintptr_t>(page + 26) -
                             kCombatOutgoingDamageSide0ReturnRva;
  auto ring = std::make_unique<CombatPhaseEventTraceRingV1>();
  bool valid = ArmCombatPhaseEventTraceRingV1(*ring, fixture.plan) &&
               BindCombatPhaseEventTraceOriginalTrampolinesV1(
                   &DummySchedule, &DummyFire,
                   &DummyOutgoingWithPostCounter);
  if (valid) {
    ring->committed_count.store(6);
    using Stub = std::uintptr_t(__fastcall *)(
        void *, std::int64_t *, std::int32_t, std::int64_t, void *);
    auto *const call = reinterpret_cast<Stub>(page);
    std::int64_t output = 0;
    const auto result = call(
        reinterpret_cast<void *>(fixture.plan.sides[0]), &output, 73,
        150'000, reinterpret_cast<void *>(fixture.plan.sides[1]));
    valid = result == reinterpret_cast<std::uintptr_t>(&output) &&
            output == 654'321 &&
            ring->post_counter_attack_count.load() == 1 &&
            ring->post_counter_attack_raw[0] == 123'456 &&
            ring->outgoing_damage_count.load() == 1 &&
            ring->outgoing_damage_raw[0] == 654'321 &&
            ring->failure_flags.load() == trace_capture_failure_none;
    XarCaptureCombatPostCounterAttackV1(
        reinterpret_cast<void *>(fixture.plan.sides[0]), 999'999);
    valid = valid && ring->post_counter_attack_count.load() == 1 &&
            ring->failure_flags.load() == trace_capture_failure_none;
  }
  CancelCombatPhaseEventTraceRingV1(*ring);
  VirtualFree(page, 0, MEM_RELEASE);
  return valid ? true : Fail("outer caller context was not transported/restored");
}

bool SourceContract(std::string_view path) {
  std::ifstream stream{std::string(path), std::ios::binary};
  const std::string contents{std::istreambuf_iterator<char>(stream),
                             std::istreambuf_iterator<char>()};
  constexpr std::array<std::string_view, 22> required{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x23C8750",
      "0x23C9900",
      "0x27FB594",
      "0x27FB5AC",
      "0x2309EF7",
      "0x2309EFF",
      "0x23CB1D0",
      "mov_RBP_RCX_where_entry_RCX_is_CCombatSide",
      "original_main_tick_caller_held_in_thread_local_outer_hook_context",
      "0x23CB435",
      "2441EEAB92DBB31B35C9A770D83FFE5E553834E503DAEFAB91C230D4E6A9966B",
      "0x2309F98",
      "0x2309FB4",
      "0x2309FE8",
      "180B53838F1B7CA3FD5ECD62C76C322312BF64147622F178619D52F160BAFBA0",
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
  constexpr std::array<std::string_view, 21> required{
      "kCombatPhaseEventScheduleSide0ReturnRva",
      "kCombatPhaseEventScheduleSide1ReturnRva",
      "kCombatPhaseEventFireSide0ReturnRva",
      "kCombatPhaseEventFireSide1ReturnRva",
      "kCombatOutgoingDamageSide0ReturnRva",
      "kCombatOutgoingDamageSide1ReturnRva",
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
      !CaptureSevenRecordFixture() ||
      !CaptureSevenRecordFixture(0) ||
      !CaptureSevenRecordFixture(23) ||
      !CaptureSevenRecordFixture(48) ||
      !FailureCases() ||
      !StaleScheduledKnightCase() ||
      !OutgoingDamageCaptureCases() || !PostCounterAttackCaptureCases() ||
      !OutgoingDamageHookAbi() || !OuterCallerContextTransport() ||
      BindCombatPhaseEventTraceOriginalTrampolinesV1(nullptr, nullptr,
                                                      nullptr)) {
    return 1;
  }
  return 0;
}
