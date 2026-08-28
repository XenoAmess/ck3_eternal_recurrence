#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>

namespace {

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &storage, std::size_t offset,
           Value value) {
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename Value, std::size_t Size>
Value Load(const std::array<std::byte, Size> &storage, std::size_t offset) {
  Value value{};
  std::memcpy(&value, storage.data() + offset, sizeof(value));
  return value;
}

struct ComponentStorageFixture {
  std::array<std::byte, 0x40> header{};
  std::array<std::byte, 0x100> slots{};
  void *pointer = header.data();

  ComponentStorageFixture() {
    Store(header, 0x20, static_cast<void *>(slots.data()));
    Store(header, 0x2C, std::int32_t{8});
  }

  void Set(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, static_cast<std::size_t>(index) * 0x10 + 0x08, object);
  }
};

struct WorldFixture {
  static constexpr std::int32_t kSecondPublicCunitId = 0x02000002;
  static constexpr std::int32_t kSecondInternalArmyId = 0x03000002;

  std::array<std::byte, 0x100> game_state{};
  std::array<std::byte, 0x100> jomini{};
  std::array<std::byte, 0x100> player{};
  std::array<std::byte, 0x220> unit{};
  std::array<std::byte, 0x220> second_unit{};
  std::array<std::byte, 0x180> internal_army{};
  std::array<std::byte, 0x180> second_internal_army{};
  std::array<std::byte, 0x20> province_a{};
  std::array<std::byte, 0x20> province_b{};
  std::array<std::byte, 0x20> no_direct_target{};
  std::array<std::byte, 0x800> combat{};
  std::array<std::int32_t, 4> attacker_ids{1, 0, 0, 0};
  std::array<std::int32_t, 4> defender_ids{2, 0, 0, 0};
  ComponentStorageFixture units;
  ComponentStorageFixture internal_armies;
  ComponentStorageFixture combats;
  void *game_state_pointer = game_state.data();
  void *jomini_pointer = jomini.data();
  xar::ck3_11906::Bindings bindings{};

  WorldFixture() {
    Store(game_state, 0x08, std::int32_t{1'000});
    Store(jomini, 0x20, std::uint8_t{1});
    Store(player, 0x70, std::int32_t{7});
    Store(province_a, 0x10, std::int32_t{101});
    Store(province_b, 0x10, std::int32_t{102});
    Store(unit, 0x10, std::int32_t{1});
    Store(unit, 0x18, std::int32_t{0});
    Store(unit, 0x30, static_cast<void *>(province_a.data()));
    Store(unit, 0x170, std::int32_t{0});
    Store(unit, 0x178, std::int32_t{1});
    Store(internal_army, 0x10, std::int32_t{1});
    Store(internal_army, 0x124, std::int32_t{1});
    Store(internal_army, 0x128, std::int32_t{-1});
    units.Set(1, unit.data());
    internal_armies.Set(1, internal_army.data());
    bindings.enabled = true;
    bindings.game_state_slot = &game_state_pointer;
    bindings.jomini_state_slot = &jomini_pointer;
    bindings.army_storage_slot = &units.pointer;
    bindings.army_internal_storage_slot = &internal_armies.pointer;
    bindings.combat_storage_slot = &combats.pointer;
    bindings.get_local_player = &GetLocalPlayer;
    active = this;
  }

  void AddCombat() {
    Store(internal_army, 0x128, std::int32_t{1});
    Store(combat, 0x08, std::int32_t{1});
    Store(combat, 0x6B0, std::int32_t{1});
    Store(combat, 0x6B4, std::int32_t{4});
    Store(combat, 0x6E0, std::int32_t{-1});
    Store(combat, 0x704, std::uint8_t{0});
    Store(combat, 0x705, std::uint8_t{0});
    auto *const attacker_side = combat.data() + 0x20;
    auto *const defender_side = combat.data() + 0x368;
    auto *const attacker_data = attacker_ids.data();
    auto *const defender_data = defender_ids.data();
    std::memcpy(attacker_side + 0x10, &attacker_data, sizeof(void *));
    std::memcpy(defender_side + 0x10, &defender_data, sizeof(void *));
    const std::int32_t capacity = 4;
    const std::int32_t count = 1;
    std::memcpy(attacker_side + 0x18, &capacity, sizeof(capacity));
    std::memcpy(attacker_side + 0x1C, &count, sizeof(count));
    std::memcpy(defender_side + 0x18, &capacity, sizeof(capacity));
    std::memcpy(defender_side + 0x1C, &count, sizeof(count));
    void *combat_pointer = combat.data();
    std::memcpy(attacker_side + 0xB8, &combat_pointer, sizeof(combat_pointer));
    std::memcpy(defender_side + 0xB8, &combat_pointer, sizeof(combat_pointer));
    combats.Set(1, combat.data());
  }

  void AddIdleRegularArmyWithNonPositiveDirectTarget() {
    Store(second_unit, 0x10, kSecondPublicCunitId);
    Store(second_unit, 0x18, std::int32_t{0});
    Store(second_unit, 0x30, static_cast<void *>(no_direct_target.data()));
    Store(second_unit, 0x170, std::int32_t{0});
    Store(second_unit, 0x178, kSecondInternalArmyId);
    Store(second_internal_army, 0x10, kSecondInternalArmyId);
    Store(second_internal_army, 0x124, kSecondPublicCunitId);
    Store(second_internal_army, 0x128, std::int32_t{-1});
    units.Set(kSecondPublicCunitId, second_unit.data());
    internal_armies.Set(kSecondInternalArmyId, second_internal_army.data());
  }

  void AdvanceDate() {
    const auto current = Load<std::int32_t>(game_state, 0x08);
    Store(game_state, 0x08, static_cast<std::int32_t>(current + 24));
  }

  static void *GetLocalPlayer(void *) { return active->player.data(); }
  static WorldFixture *active;
};

WorldFixture *WorldFixture::active = nullptr;
int pause_calls = 0;
int original_calls = 0;
std::int32_t pause_player_id = -1;

void __fastcall SetPaused(void *jomini_state, bool paused,
                          std::int32_t player_id) {
  ++pause_calls;
  pause_player_id = player_id;
  std::uint8_t value = paused ? 1 : 0;
  std::memcpy(static_cast<std::byte *>(jomini_state) + 0x20, &value,
              sizeof(value));
}

void __fastcall OriginalDailyFinalStage() {
  ++original_calls;
  WorldFixture::active->AdvanceDate();
}

xar::ck3_11906::TacticalDailySentinelArmRequestV1
Request(std::int32_t speed, std::int32_t target = 1'072) {
  xar::ck3_11906::TacticalDailySentinelArmRequestV1 request{};
  request.starting_date_raw = 1'000;
  request.target_date_raw = target;
  request.speed = speed;
  request.army_count = 1;
  request.army_ids[0] = 1;
  return request;
}

bool TestParser() {
  using namespace xar::ck3_11906;
  TacticalDailySentinelArmRequestV1 parsed{};
  std::uint64_t cancel_generation = 0;
  if (!ParseTacticalDailySentinelArmStepV1(
          "research-arm-tactical-daily-sentinel-v1-1000-to-1072-speed-3-a-2-1-"
          "2",
          parsed) ||
      parsed.starting_date_raw != 1'000 || parsed.target_date_raw != 1'072 ||
      parsed.speed != 3 || parsed.army_count != 2 || parsed.army_ids[0] != 1 ||
      parsed.army_ids[1] != 2) {
    return false;
  }
  if (!ParseTacticalDailySentinelArmStepV1(
          "research-arm-tactical-daily-sentinel-v1-1000-to-1072-speed-5-mode-"
          "terminal-a-1-1",
          parsed) ||
      parsed.mode != TacticalDailySentinelModeV1::terminal_or_sentinel ||
      parsed.speed != 5 || parsed.army_count != 1 || parsed.army_ids[0] != 1) {
    return false;
  }
  const auto long_arm_step = [](std::size_t army_count) {
    std::string step{kTacticalDailySentinelArmPrefixV1};
    step += "2000000000-to-2000001080-speed-5-mode-terminal-a-";
    step += std::to_string(army_count);
    for (std::size_t index = 0; index < army_count; ++index) {
      step += '-';
      step += std::to_string(1'000'000'000U + index);
    }
    return step;
  };
  const auto six_armies = long_arm_step(6U);
  if (six_armies.size() <= 128U ||
      !ParseTacticalDailySentinelArmStepV1(six_armies, parsed) ||
      parsed.army_count != 6 || parsed.army_ids[5] != 1'000'000'005) {
    return false;
  }
  const auto maximum =
      long_arm_step(kTacticalDailySentinelMaximumArmiesV1);
  if (!ParseTacticalDailySentinelArmStepV1(maximum, parsed) ||
      maximum.size() != kTacticalDailySentinelMaximumArmStepBytesV1 ||
      parsed.army_count != 64 ||
      parsed.army_ids[63] != 1'000'000'063) {
    return false;
  }
  return ParseTacticalDailySentinelCancelStepV1(
             "research-cancel-tactical-daily-sentinel-v1-generation-"
             "18446744073709551615",
             cancel_generation) &&
         cancel_generation == std::numeric_limits<std::uint64_t>::max() &&
         !ParseTacticalDailySentinelCancelStepV1(
             "research-cancel-tactical-daily-sentinel-v1-generation-01",
             cancel_generation) &&
         !ParseTacticalDailySentinelCancelStepV1(
             "research-cancel-tactical-daily-sentinel-v1-generation-0",
             cancel_generation) &&
         !ParseTacticalDailySentinelCancelStepV1(
             "research-cancel-tactical-daily-sentinel-v1-generation-1-x",
             cancel_generation) &&
         !ParseTacticalDailySentinelArmStepV1(
             "research-arm-tactical-daily-sentinel-v1-1000-to-1072-speed-6-a-1-"
             "1",
             parsed) &&
         !ParseTacticalDailySentinelArmStepV1(
             "research-arm-tactical-daily-sentinel-v1-1000-to-1071-speed-3-a-1-"
             "1",
             parsed) &&
         !ParseTacticalDailySentinelArmStepV1(
             "research-arm-tactical-daily-sentinel-v1-1000-to-1072-speed-3-a-2-"
             "1-1",
             parsed) &&
         !ParseTacticalDailySentinelArmStepV1(
             "research-arm-tactical-daily-sentinel-v1-1000-to-1072-speed-5-"
             "mode-unknown-a-1-1",
             parsed);
}

bool TestGenerationBoundPausedCancelDisarmsAndAllowsNextArm() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(Request(3)) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  const auto armed = ReadTacticalDailySentinelStatusV1();
  if (armed.state != TacticalDailySentinelStateV1::armed ||
      armed.generation != 1) {
    return false;
  }

  Store(world.jomini, 0x20, std::uint8_t{0});
  if (CancelTacticalDailySentinelV1(armed.generation) !=
          TacticalDailySentinelCancelStatusV1::requires_paused ||
      ReadTacticalDailySentinelStatusV1().state !=
          TacticalDailySentinelStateV1::armed) {
    return false;
  }
  Store(world.jomini, 0x20, std::uint8_t{1});
  if (CancelTacticalDailySentinelV1(armed.generation + 1) !=
          TacticalDailySentinelCancelStatusV1::generation_mismatch ||
      ReadTacticalDailySentinelStatusV1().state !=
          TacticalDailySentinelStateV1::armed ||
      CancelTacticalDailySentinelV1(armed.generation) !=
          TacticalDailySentinelCancelStatusV1::canceled) {
    return false;
  }
  const auto canceled = ReadTacticalDailySentinelStatusV1();
  if (canceled.state != TacticalDailySentinelStateV1::idle ||
      canceled.generation != armed.generation ||
      canceled.starting_date_raw != armed.starting_date_raw ||
      canceled.target_date_raw != armed.target_date_raw ||
      canceled.last_observed_date_raw != armed.last_observed_date_raw ||
      canceled.speed != armed.speed || canceled.mode != armed.mode ||
      canceled.army_count != armed.army_count ||
      canceled.combat_count != armed.combat_count ||
      canceled.completed_daily_ticks != 0 || canceled.trigger_flags != 0 ||
      CancelTacticalDailySentinelV1(armed.generation) !=
          TacticalDailySentinelCancelStatusV1::not_armed) {
    return false;
  }
  if (ArmTacticalDailySentinelV1(Request(5)) !=
      TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  const auto rearmed = ReadTacticalDailySentinelStatusV1();
  return rearmed.state == TacticalDailySentinelStateV1::armed &&
         rearmed.generation == armed.generation + 1 && rearmed.speed == 5;
}

bool TestPausedRearmReplacesStaleArm() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(Request(2, 1'120)) !=
          TacticalDailySentinelArmStatusV1::armed ||
      ArmTacticalDailySentinelV1(Request(5, 1'072)) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  const auto status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::armed &&
         status.generation == 2 && status.speed == 5 &&
         status.target_date_raw == 1'072;
}

bool TestAllFiveSpeedsExactDeadline() {
  using namespace xar::ck3_11906;
  for (std::int32_t speed = 1; speed <= 5; ++speed) {
    WorldFixture world;
    pause_calls = 0;
    original_calls = 0;
    pause_player_id = -1;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused,
                                                  &OriginalDailyFinalStage) ||
        ArmTacticalDailySentinelV1(Request(speed)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    XarTacticalDailySentinelHookV1();
    XarTacticalDailySentinelHookV1();
    if (ReadTacticalDailySentinelStatusV1().state !=
        TacticalDailySentinelStateV1::armed) {
      return false;
    }
    XarTacticalDailySentinelHookV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::triggered ||
        status.speed != speed || status.trigger_date_raw != 1'072 ||
        status.last_observed_date_raw != 1'072 ||
        status.completed_daily_ticks != 3 || status.overshoot_days != 0 ||
        status.signed_date_delta_from_target_raw != 0 ||
        status.trigger_flags != tactical_daily_trigger_date_deadline ||
        !status.pause_wrapper_called || !status.pause_observed ||
        status.intermediate_pause_count != 0 || status.terminal_observed ||
        status.abnormal || pause_calls != 1 || original_calls != 3 ||
        pause_player_id != 7 || Load<std::uint8_t>(world.jomini, 0x20) != 1) {
      return false;
    }
  }
  return true;
}

bool TestZeroPlayerIdIsValid() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  Store(world.player, 0x70, std::int32_t{0});
  return InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) &&
         ArmTacticalDailySentinelV1(Request(3)) ==
             TacticalDailySentinelArmStatusV1::armed;
}

bool TestNonPositiveDirectTargetIsAbsentInFullWatch() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  world.AddIdleRegularArmyWithNonPositiveDirectTarget();
  auto request = Request(3, 1'120);
  request.army_count = 2;
  request.army_ids[1] = WorldFixture::kSecondPublicCunitId;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(request) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  auto status = ReadTacticalDailySentinelStatusV1();
  if (status.army_count != 2 || status.combat_count != 0) {
    return false;
  }
  Store(world.jomini, 0x20, std::uint8_t{0});
  world.AdvanceDate();
  ProcessTacticalDailySentinelAfterTickV1();
  status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::armed &&
         status.completed_daily_ticks == 1 &&
         status.trigger_flags == tactical_daily_trigger_none;
}

bool TestArmReportsMissingCombatPrecisely() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  world.AddCombat();
  world.combats.Set(1, nullptr);
  return InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) &&
         ArmTacticalDailySentinelV1(Request(3)) ==
             TacticalDailySentinelArmStatusV1::combat_unavailable;
}

bool TestContactAndRouteEpochs() {
  using namespace xar::ck3_11906;
  {
    WorldFixture world;
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.internal_army, 0x128, std::int32_t{1});
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::triggered ||
        (status.trigger_flags & tactical_daily_trigger_combat_transition) ==
            0 ||
        status.trigger_date_raw != 1'024 || status.overshoot_days != 0) {
      return false;
    }
  }
  {
    WorldFixture world;
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(4, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.unit, 0x30, static_cast<void *>(world.province_b.data()));
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::triggered ||
        (status.trigger_flags & tactical_daily_trigger_route_target_changed) ==
            0 ||
        status.trigger_date_raw != 1'024) {
      return false;
    }
  }
  return true;
}

bool TestBattlePhaseRosterAndTerminalEpochs() {
  using namespace xar::ck3_11906;
  {
    WorldFixture world;
    world.AddCombat();
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.combat, 0x6B0, std::int32_t{2});
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.combat_count != 1 ||
        status.state != TacticalDailySentinelStateV1::armed ||
        status.trigger_flags != tactical_daily_trigger_none ||
        status.completed_daily_ticks != 1 || status.pause_wrapper_called ||
        status.pause_observed || pause_calls != 0) {
      return false;
    }
  }
  {
    WorldFixture world;
    world.AddCombat();
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(4, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    world.attacker_ids[1] = 3;
    const std::int32_t count = 2;
    std::memcpy(world.combat.data() + 0x20 + 0x1C, &count, sizeof(count));
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::triggered ||
        status.trigger_flags != tactical_daily_trigger_combat_roster_changed ||
        !status.pause_wrapper_called || !status.pause_observed ||
        status.terminal_observed || pause_calls != 1) {
      return false;
    }
  }
  {
    WorldFixture world;
    world.AddCombat();
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.combat, 0x6B0, std::int32_t{2});
    Store(world.combat, 0x6E0, std::int32_t{1});
    Store(world.combat, 0x704, std::uint8_t{1});
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::triggered ||
        status.trigger_flags != tactical_daily_trigger_combat_terminal ||
        !status.pause_wrapper_called || !status.pause_observed ||
        !status.terminal_observed || pause_calls != 1) {
      return false;
    }
  }
  {
    WorldFixture world;
    world.AddCombat();
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(5, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.internal_army, 0x128, std::int32_t{-1});
    Store(world.unit, 0x170, std::int32_t{1});
    world.combats.Set(1, nullptr);
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    constexpr std::uint32_t terminal_group =
        tactical_daily_trigger_combat_transition |
        tactical_daily_trigger_retreat_transition |
        tactical_daily_trigger_combat_unavailable |
        tactical_daily_trigger_combat_terminal;
    if (status.trigger_flags != terminal_group ||
        status.state != TacticalDailySentinelStateV1::triggered ||
        !status.pause_wrapper_called || !status.pause_observed ||
        !status.terminal_observed || pause_calls != 1) {
      return false;
    }
  }
  {
    WorldFixture world;
    world.AddCombat();
    pause_calls = 0;
    if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
        ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
            TacticalDailySentinelArmStatusV1::armed) {
      return false;
    }
    Store(world.jomini, 0x20, std::uint8_t{0});
    world.AdvanceDate();
    Store(world.combat, 0x6E0, std::int32_t{1});
    ProcessTacticalDailySentinelAfterTickV1();
    const auto status = ReadTacticalDailySentinelStatusV1();
    if (status.state != TacticalDailySentinelStateV1::armed ||
        status.trigger_flags != tactical_daily_trigger_none ||
        status.completed_daily_ticks != 1 || status.pause_wrapper_called ||
        status.pause_observed || status.terminal_observed || pause_calls != 0) {
      return false;
    }
  }
  return true;
}

bool TestSkippedDateFailsClosed() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  Store(world.jomini, 0x20, std::uint8_t{0});
  Store(world.game_state, 0x08, std::int32_t{1'048});
  ProcessTacticalDailySentinelAfterTickV1();
  const auto status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::failed &&
         (status.trigger_flags &
          tactical_daily_trigger_date_sequence_failure) != 0 &&
         status.pause_observed;
}

bool TestEvaluationFaultCannotHideBehindTacticalTrigger() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  world.AddCombat();
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  Store(world.jomini, 0x20, std::uint8_t{0});
  world.AdvanceDate();
  Store(world.unit, 0x30, static_cast<void *>(world.province_b.data()));
  world.combats.Set(1, reinterpret_cast<void *>(1));
  ProcessTacticalDailySentinelAfterTickV1();
  const auto status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::failed &&
         (status.trigger_flags &
          tactical_daily_trigger_route_target_changed) != 0 &&
         (status.trigger_flags & tactical_daily_trigger_evaluation_failure) !=
             0 &&
         status.abnormal && status.pause_observed;
}

bool TestTerminalModeRunsThroughNonDecisionPhases() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  world.AddCombat();
  pause_calls = 0;
  auto request = Request(5, 1'240);
  request.mode = TacticalDailySentinelModeV1::terminal_or_sentinel;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(request) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  Store(world.jomini, 0x20, std::uint8_t{0});
  world.AdvanceDate();
  Store(world.combat, 0x6B0, std::int32_t{2});
  Store(world.combat, 0x6E0, std::int32_t{1});
  ProcessTacticalDailySentinelAfterTickV1();
  auto status = ReadTacticalDailySentinelStatusV1();
  if (status.state != TacticalDailySentinelStateV1::armed ||
      status.mode != TacticalDailySentinelModeV1::terminal_or_sentinel ||
      status.completed_daily_ticks != 1 || pause_calls != 0) {
    return false;
  }
  world.AdvanceDate();
  Store(world.combat, 0x704, std::uint8_t{1});
  ProcessTacticalDailySentinelAfterTickV1();
  status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::triggered &&
         status.trigger_flags == tactical_daily_trigger_combat_terminal &&
         status.trigger_date_raw == 1'048 && status.pause_observed &&
         status.intermediate_pause_count == 0 && status.terminal_observed &&
         !status.abnormal && pause_calls == 1;
}

bool TestNativePauseIsDecisionEpoch() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  pause_calls = 0;
  if (!InitializeTacticalDailySentinelFixtureV1(world.bindings, &SetPaused) ||
      ArmTacticalDailySentinelV1(Request(3, 1'120)) !=
          TacticalDailySentinelArmStatusV1::armed) {
    return false;
  }
  world.AdvanceDate();
  // CK3 events and other native stop reasons can pause before the final
  // daily-stage hook.  The sentinel must publish that epoch without issuing
  // a redundant pause call.
  Store(world.jomini, 0x20, std::uint8_t{1});
  ProcessTacticalDailySentinelAfterTickV1();
  const auto status = ReadTacticalDailySentinelStatusV1();
  return status.state == TacticalDailySentinelStateV1::triggered &&
         status.trigger_flags == tactical_daily_trigger_native_pause &&
         status.pause_observed && !status.pause_wrapper_called &&
         status.intermediate_pause_count == 1 && !status.terminal_observed &&
         !status.abnormal && pause_calls == 0;
}

bool TestInstallAnchor() {
  using namespace xar::ck3_11906;
  WorldFixture world;
  void *code = VirtualAlloc(nullptr, 0x1000, MEM_RESERVE | MEM_COMMIT,
                            PAGE_EXECUTE_READWRITE);
  if (code == nullptr) {
    return false;
  }
  constexpr std::array<std::uint8_t, 15> prologue{0x48, 0x89, 0x5C, 0x24, 0x08,
                                                  0x48, 0x89, 0x74, 0x24, 0x10,
                                                  0x57, 0x48, 0x83, 0xEC, 0x20};
  std::memcpy(code, prologue.data(), prologue.size());
  TacticalDailySentinelDetourStateV1 state{};
  TacticalDailySentinelInstallEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 1;
  environment.bindings = world.bindings;
  environment.final_stage_target_override =
      reinterpret_cast<std::uintptr_t>(code);
  environment.set_paused_override = &SetPaused;
  const bool installed = InstallTacticalDailySentinelV1(state, environment);
  const auto *bytes = static_cast<const std::uint8_t *>(code);
  const bool patch_ok = installed && state.installed.load() == 1 &&
                        bytes[0] == 0xFF && bytes[1] == 0x25 &&
                        TacticalDailySentinelInstalledV1();
  VirtualFree(code, 0, MEM_RELEASE);
  return patch_ok;
}

} // namespace

int main() {
  if (!TestParser()) {
    std::cerr << "tactical daily sentinel parser fixture failed\n";
    return 1;
  }
  if (!TestPausedRearmReplacesStaleArm()) {
    std::cerr << "tactical daily sentinel paused rearm fixture failed\n";
    return 1;
  }
  if (!TestGenerationBoundPausedCancelDisarmsAndAllowsNextArm()) {
    std::cerr << "tactical daily sentinel cancel fixture failed\n";
    return 1;
  }
  if (!TestAllFiveSpeedsExactDeadline()) {
    std::cerr << "tactical daily sentinel 1-5 deadline fixture failed\n";
    return 1;
  }
  if (!TestZeroPlayerIdIsValid()) {
    std::cerr << "tactical daily sentinel zero player-id fixture failed\n";
    return 1;
  }
  if (!TestNonPositiveDirectTargetIsAbsentInFullWatch()) {
    std::cerr << "tactical daily sentinel idle direct-target fixture failed\n";
    return 1;
  }
  if (!TestArmReportsMissingCombatPrecisely()) {
    std::cerr << "tactical daily sentinel missing-combat fixture failed\n";
    return 1;
  }
  if (!TestContactAndRouteEpochs()) {
    std::cerr << "tactical daily sentinel contact/route fixture failed\n";
    return 1;
  }
  if (!TestBattlePhaseRosterAndTerminalEpochs()) {
    std::cerr << "tactical daily sentinel battle fixture failed\n";
    return 1;
  }
  if (!TestSkippedDateFailsClosed()) {
    std::cerr << "tactical daily sentinel skipped-date fixture failed\n";
    return 1;
  }
  if (!TestEvaluationFaultCannotHideBehindTacticalTrigger()) {
    std::cerr << "tactical daily sentinel evaluation-fault fixture failed\n";
    return 1;
  }
  if (!TestTerminalModeRunsThroughNonDecisionPhases()) {
    std::cerr << "tactical daily sentinel terminal mode fixture failed\n";
    return 1;
  }
  if (!TestNativePauseIsDecisionEpoch()) {
    std::cerr << "tactical daily sentinel native-pause fixture failed\n";
    return 1;
  }
  if (!TestInstallAnchor()) {
    std::cerr << "tactical daily sentinel install fixture failed\n";
    return 1;
  }
  return 0;
}
