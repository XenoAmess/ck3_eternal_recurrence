#include "xar_bridge/ck3_12004_default_routes_mailbox.hpp"
#include "xar_bridge/ck3_12004_tactical_daily_sentinel.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

namespace native = xar::ck3_11906;
namespace actual4 = xar::ck3_12004;

constexpr std::int32_t kStartingDate = 53'288'448;
constexpr std::int32_t kDeadline = kStartingDate + 3 * 24;
constexpr std::int32_t kPublicUnitId = 0;

struct alignas(void *) MemoryRow {
  std::array<std::byte, 512> bytes{};

  void *data() noexcept { return bytes.data(); }

  template <class T> void put(std::size_t offset, T value) noexcept {
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
  }

  template <class T> T get(std::size_t offset) const noexcept {
    T value{};
    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return value;
  }
};

void *g_player = nullptr;
std::uint32_t g_pause_calls = 0;

void *__fastcall GetLocalPlayer(void *) noexcept { return g_player; }

void __fastcall SetPaused(void *jomini_state, bool paused,
                          std::int32_t player_id) noexcept {
  if (player_id != 1) {
    return;
  }
  const std::uint8_t value = paused ? 1 : 0;
  std::memcpy(static_cast<std::byte *>(jomini_state) + 0x20, &value,
              sizeof(value));
  ++g_pause_calls;
}

void Require(bool value, const char *message) {
  if (!value) {
    throw std::runtime_error(message);
  }
}

struct Fixture {
  MemoryRow game;
  MemoryRow jomini;
  MemoryRow player;
  MemoryRow unit;
  MemoryRow army;
  MemoryRow current;
  MemoryRow same_current;
  MemoryRow intermediate;
  MemoryRow target;
  MemoryRow unit_storage;
  MemoryRow army_storage;
  MemoryRow combat_storage;
  MemoryRow unit_slots;
  MemoryRow army_slots;
  void *game_root = game.data();
  void *jomini_root = jomini.data();
  void *unit_storage_root = unit_storage.data();
  void *army_storage_root = army_storage.data();
  void *combat_storage_root = combat_storage.data();
  native::Bindings bindings{};

  Fixture() {
    game.put<std::int32_t>(0x08, kStartingDate);
    jomini.put<std::uint8_t>(0x20, 1);
    player.put<std::int32_t>(0x70, 1);
    current.put<std::int32_t>(0x10, 2619);
    same_current.put<std::int32_t>(0x10, 2619);
    intermediate.put<std::int32_t>(0x10, 2618);
    target.put<std::int32_t>(0x10, 2615);
    unit.put<std::int32_t>(actual4::kTacticalSentinelUnitIdOffset12004,
                           kPublicUnitId);
    unit.put<std::int32_t>(actual4::kTacticalSentinelUnitKindOffset12004, 0);
    unit.put<void *>(actual4::kTacticalSentinelUnitCurrentProvinceOffset12004,
                      current.data());
    unit.put<void *>(actual4::kTacticalSentinelUnitDirectTargetOffset12004,
                      target.data());
    unit.put<std::int32_t>(actual4::kTacticalSentinelUnitInternalArmyIdOffset12004,
                           0);
    army.put<std::int32_t>(actual4::kTacticalSentinelInternalArmyIdOffset12004, 0);
    army.put<std::int32_t>(actual4::kTacticalSentinelInternalArmyUnitIdOffset12004,
                           kPublicUnitId);
    army.put<std::int32_t>(actual4::kTacticalSentinelInternalArmyCombatIdOffset12004,
                           -1);
    unit_storage.put<void *>(0x20, unit_slots.data());
    unit_storage.put<std::int32_t>(0x2C, 1);
    army_storage.put<void *>(0x20, army_slots.data());
    army_storage.put<std::int32_t>(0x2C, 1);
    unit_slots.put<void *>(0x08, unit.data());
    army_slots.put<void *>(0x08, army.data());

    // Use the admitted actual4 factory, replacing only its physical roots and
    // native callbacks with this fixture's declared memory graph.
    bindings = actual4::BindTacticalDailySentinelImage12004(
        0x10000000, actual4::kExecutableSha256);
    bindings.game_state_slot = &game_root;
    bindings.jomini_state_slot = &jomini_root;
    bindings.get_local_player = &GetLocalPlayer;
    bindings.army_storage_slot = &unit_storage_root;
    bindings.army_internal_storage_slot = &army_storage_root;
    bindings.combat_storage_slot = &combat_storage_root;
    g_player = player.data();
    g_pause_calls = 0;
    Require(actual4::InitializeTacticalDailySentinelFixture12004(
                bindings, actual4::kExecutableSha256, &SetPaused),
            "actual4 fixture initialization failed");
  }

  void tick(std::int32_t date_raw) {
    game.put<std::int32_t>(0x08, date_raw);
    native::ProcessTacticalDailySentinelAfterTickV1();
  }

  void resume() noexcept { jomini.put<std::uint8_t>(0x20, 0); }
};

struct Packets {
  std::string armed;
  std::string stopped;
};

Packets Arm(Fixture &fixture) {
  (void)fixture;
  const std::string step =
      "research-arm-tactical-daily-sentinel-v1-" +
      std::to_string(kStartingDate) + "-to-" + std::to_string(kDeadline) +
      "-speed-3-mode-terminal-a-1-0";
  native::TacticalDailySentinelArmRequestV1 request{};
  Require(native::ParseTacticalDailySentinelArmStepV1(step, request),
          "three-day watched step was not parsed");
  const auto outcome = native::ArmTacticalDailySentinelV1(request);
  Require(outcome == native::TacticalDailySentinelArmStatusV1::armed,
          "three-day watched arm was not admitted");
  const auto status = native::ReadTacticalDailySentinelStatusV1();
  Require(status.army_count == 1 && status.combat_count == 0,
          "watched noncombat scope was not retained");
  return {actual4::SerializeTacticalDailySentinelArmResult12004(
              "position-witness-arm", step, outcome, status),
          {}};
}

Packets PositionChangeCase() {
  Fixture fixture;
  auto packets = Arm(fixture);
  fixture.resume();
  // An equivalent Province row must not stop the sentinel: compare actual
  // ProvinceID rather than the row address.
  fixture.unit.put<void *>(
      actual4::kTacticalSentinelUnitCurrentProvinceOffset12004,
      fixture.same_current.data());
  fixture.tick(kStartingDate + 24);
  const auto first = native::ReadTacticalDailySentinelStatusV1();
  Require(first.state == native::TacticalDailySentinelStateV1::armed &&
              first.trigger_flags == native::tactical_daily_trigger_none &&
              first.completed_daily_ticks == 1 && g_pause_calls == 0,
          "unchanged physical ProvinceID stopped the first day");

  // The real position changes at an intermediate arrival while the final
  // direct target stays 2615. The position witness must stop this second day.
  fixture.unit.put<void *>(
      actual4::kTacticalSentinelUnitCurrentProvinceOffset12004,
      fixture.intermediate.data());
  fixture.tick(kStartingDate + 48);
  const auto stopped = native::ReadTacticalDailySentinelStatusV1();
  Require(stopped.state == native::TacticalDailySentinelStateV1::triggered &&
              stopped.trigger_flags ==
                  native::tactical_daily_trigger_army_position_changed &&
              stopped.trigger_date_raw == kStartingDate + 48 &&
              stopped.completed_daily_ticks == 2 && stopped.overshoot_days == 0 &&
              stopped.pause_observed && stopped.pause_wrapper_called &&
              g_pause_calls == 1 && fixture.jomini.get<std::uint8_t>(0x20) == 1,
          "intermediate physical arrival did not stop before the deadline");
  packets.stopped = actual4::SerializeTacticalDailySentinelResult12004(
      "position-witness-stopped",
      native::kTacticalDailySentinelStatusStepV1, stopped);
  return packets;
}

Packets DeadlineCase() {
  Fixture fixture;
  auto packets = Arm(fixture);
  fixture.resume();
  fixture.tick(kStartingDate + 24);
  fixture.tick(kStartingDate + 48);
  Require(native::ReadTacticalDailySentinelStatusV1().state ==
              native::TacticalDailySentinelStateV1::armed,
          "unchanged three-day route stopped before its deadline");
  fixture.tick(kDeadline);
  const auto stopped = native::ReadTacticalDailySentinelStatusV1();
  Require(stopped.state == native::TacticalDailySentinelStateV1::triggered &&
              stopped.trigger_flags == native::tactical_daily_trigger_date_deadline &&
              stopped.trigger_date_raw == kDeadline &&
              stopped.completed_daily_ticks == 3 && stopped.overshoot_days == 0 &&
              stopped.pause_observed && g_pause_calls == 1,
          "unchanged route did not preserve the three-day date deadline");
  packets.stopped = actual4::SerializeTacticalDailySentinelResult12004(
      "position-deadline-stopped",
      native::kTacticalDailySentinelStatusStepV1, stopped);
  return packets;
}

} // namespace

int main() {
  try {
    const auto position = PositionChangeCase();
    const auto deadline = DeadlineCase();
    std::cout << "{\"schema\":\"xar.actual4-route-position-witness-fixture.v1\","
                 "\"status\":\"GREEN\",\"position_case\":{\"armed\":"
              << position.armed << ",\"stopped\":" << position.stopped
              << "},\"deadline_case\":{\"armed\":" << deadline.armed
              << ",\"stopped\":" << deadline.stopped << "}}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "route-position witness fixture failed: " << error.what()
              << '\n';
    return 1;
  }
}
