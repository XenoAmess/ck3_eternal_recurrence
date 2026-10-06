// Two new FIRST scenes: whole production control reader -> both serializers.
// Synthetic memory only. NOTRUN until Root integrates a coherent source freeze.
#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/battle_current_finalizer_manager_inputs_reader_12003.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using namespace xar::game;
template<std::size_t N> using Bytes = std::array<std::byte, N>;
void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}
template<class T, std::size_t N>
void Put(Bytes<N> &bytes, std::size_t offset, T value) {
  Require(offset + sizeof(T) <= N, "fixture byte span");
  std::memcpy(bytes.data() + offset, &value, sizeof(T));
}
template<std::size_t N>
void Header(Bytes<N> &bytes, std::size_t offset, const void *data,
            std::int32_t count) {
  Put(bytes, offset, data); Put(bytes, offset + 8, count);
  Put(bytes, offset + 12, count);
}
struct Store {
  Bytes<0x38> header{};
  std::vector<std::byte> rows;
  void *root = header.data();
  void Set(std::int32_t id, void *value) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto offset = static_cast<std::size_t>(index) * 16 + 8;
    if (rows.size() < offset + sizeof(value)) rows.resize(offset + sizeof(value));
    std::memcpy(rows.data() + offset, &value, sizeof(value));
    Put(header, 0x20, rows.data());
    Put(header, 0x2C, static_cast<std::int32_t>((rows.size() + 15) / 16));
  }
};
constexpr std::uintptr_t kImageBase = 0x140000000ULL;
constexpr std::string_view kExactSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::int32_t kCombat = 0x01000003, kResult = 0x01000004;
constexpr std::int32_t kProvince = 2640;
constexpr std::array<std::int32_t, 2> kUnits{0x01000011, 0x01000012};
constexpr std::array<std::int32_t, 2> kArmies{0x01000001, 0x01000002};
constexpr std::array<std::int32_t, 2> kOwners{29829, 0x01000022};
constexpr std::array<std::int32_t, 2> kRegiments{0x01000005, 0x01000006};
constexpr std::array<std::size_t, 2> kSideOffsets{0x20, 0x368};

struct Fixture {
  Bytes<0xA8> game_state{};
  Bytes<0x28> jomini_state{};
  // Actual embedded CombatManager root plus separate nearby-offset decoys.
  Bytes<0x2EA40> domain{};
  Bytes<0x860> province{};
  Bytes<0x730> combat{};
  Bytes<0xD8> result{};
  std::array<Bytes<0x200>, 2> units{};
  std::array<Bytes<0x148>, 2> armies{};
  std::array<Bytes<0x220>, 2> characters{};
  std::array<Bytes<0x150>, 2> regiments{};
  std::array<Bytes<0xA20>, 2> types{};
  std::array<Bytes<0x60>, 2> entries{};
  std::array<std::int32_t, 3> manager_ids{0x03000007, kCombat, 0x02000008};
  Store unit_store, army_store, character_store, regiment_store, combat_store,
      result_store;
  void *game_state_root = game_state.data();
  void *jomini_state_root = jomini_state.data();
  void *result_fallback_root = result.data();
  std::int32_t minimum_retreat_days = 14;
  BattleBindings bindings{};
  Snapshot scope{};

  static void *ResolveProvince(void *context, std::int32_t id) {
    auto &f = *static_cast<Fixture *>(context);
    return id == kProvince ? f.province.data() : nullptr;
  }
  static std::int32_t Strength(void *) { return 9; }
  static void *RuleState(void *) { return nullptr; }
  static bool Retreat(void *, void *, void *) { return false; }

  explicit Fixture(std::uint8_t raw) {
    scope.paused = true; scope.map_ready = true;
    scope.has_played_character = true; scope.played_character_id = kOwners[0];
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put<std::int32_t>(game_state, 8, scope.date_raw);
    Put(game_state, 0xA0, domain.data());
    Put<std::uint8_t>(jomini_state, 0x20, 1);
    Put<std::uintptr_t>(domain, 0x2E9D0 + 8, kImageBase + 0x477F178);
    Header(domain, 0x2E9D0 + 0x28, manager_ids.data(),
           static_cast<std::int32_t>(manager_ids.size()));
    Put(domain, 0x2E9D0 + 0x60, raw);
    const std::uint8_t decoy = raw == 0 ? 7 : 0;
    Put(domain, 0x2E9D0 + 0x58, decoy);
    Put(domain, 0x2E9D0 + 0x68, decoy);
    Put(province, 0x10, kProvince);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76U);
    Put(combat, 8, kCombat);
    Put<std::uint32_t>(combat, 0x0C, 0x436F6D62U);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 3);
    Put<std::int32_t>(combat, 0x6B4, 0);
    Put<std::int32_t>(combat, 0x6E0, 0);
    Put<std::int32_t>(combat, 0x700, -1);
    Put(combat, 0x708, kResult);
    Put<std::int32_t>(combat, 0x6C0, 100);
    Put<std::int32_t>(combat, 0x6C4, 100);
    Put(result, 8, kResult);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    combat_store.Set(kCombat, combat.data()); result_store.Set(kResult, result.data());
    for (std::size_t side = 0; side != 2; ++side) {
      Put(characters[side], 0x18, kOwners[side]);
      Put<std::uint32_t>(characters[side], 0x1C, 0x43686172U);
      character_store.Set(kOwners[side], characters[side].data());
      Put(units[side], 0x10, kUnits[side]);
      Put(units[side], 0x174, kOwners[side]);
      Put(units[side], 0x178, kArmies[side]);
      Put(units[side], 0x20, province.data());
      unit_store.Set(kUnits[side], units[side].data());
      Put(armies[side], 0x10, kArmies[side]);
      Put(armies[side], 0x124, kUnits[side]);
      Put(armies[side], 0x128, kCombat);
      Header(armies[side], 0x38, &kRegiments[side], 1);
      army_store.Set(kArmies[side], armies[side].data());
      Put(regiments[side], 0x10, kRegiments[side]);
      Put(regiments[side], 0x18, types[side].data());
      Put(regiments[side], 0x140, kArmies[side]);
      Put<std::int32_t>(regiments[side], 0x38, 9);
      Put<std::uint8_t>(types[side], 0x98A, 1);
      regiment_store.Set(kRegiments[side], regiments[side].data());
      Put(entries[side], 8, kRegiments[side]);
      Put<std::int64_t>(entries[side], 0x10, 1'000'000);
      Put<std::int64_t>(entries[side], 0x18, 800'000);
      Put<std::int64_t>(entries[side], 0x20, 100'000);
      Put<std::int32_t>(entries[side], 0x30, 10);
      Put<std::int64_t>(entries[side], 0x40, 100'000);
      Put<std::int64_t>(entries[side], 0x48, 100'000);
      const auto off = kSideOffsets[side];
      Header(combat, off + 0x10, &kArmies[side], 1);
      Header(combat, off + 0x28, entries[side].data(), 1);
      Put(combat, off + 0xB8, combat.data());
      Put(combat, off + 0x70, kOwners[side]);
      Put<std::int32_t>(combat, off + 0x74, -1);
      Put<std::int64_t>(combat, off + 0x98, 800'000);
      Put<std::int64_t>(combat, off + 0xA0, 800'000);
      Put<std::int64_t>(combat, off + 0xA8, 1'000'000);
    }
    ArmySnapshot subject{}; subject.army_id = kUnits[0];
    subject.controllable = true; subject.in_combat = true;
    scope.player_armies.push_back(subject);
    bindings.enabled = true;
    bindings.game_state_slot = &game_state_root;
    bindings.jomini_state_slot = &jomini_state_root;
    bindings.army_storage_slot = &unit_store.root;
    bindings.army_internal_storage_slot = &army_store.root;
    bindings.character_storage_slot = &character_store.root;
    bindings.regiment_storage_slot = &regiment_store.root;
    bindings.combat_storage_slot = &combat_store.root;
    bindings.battle_result_storage_slot = &result_store.root;
    bindings.battle_result_fallback_slot = &result_fallback_root;
    bindings.province_context = this;
    bindings.resolve_province = ResolveProvince;
    bindings.get_combat_side_strength = Strength;
    bindings.get_combat_regiment_strength = Strength;
    bindings.get_combat_retreat_rule_state = RuleState;
    bindings.can_order_combat_retreat = Retreat;
    bindings.minimum_days_before_manual_retreat = &minimum_retreat_days;
    EnableBattleFullBacking12003(bindings, kImageBase, kExactSha);
    EnableBattleCurrentFinalizerManagerInputs12003(bindings, kImageBase, kExactSha);
  }
};

std::string Scene(std::uint8_t raw, std::string_view name) {
  Fixture f(raw);
  const auto before_domain = f.domain;
  const auto before_combat = f.combat;
  BattleControlSnapshot frame{};
  Require(ReadBattleControlSnapshot(f.bindings, f.scope, {kUnits[0]}, frame) ==
              BattleControlSnapshotStatus::available && frame.battle_control_ready,
          "whole production control read unavailable");
  Require(frame.current_finalizer_manager_inputs_v1.has_value(),
          "new optional manager source was not sampled");
  const auto &input = *frame.current_finalizer_manager_inputs_v1;
  Require(input.source_combat_id == kCombat && input.combat_manager_row_admitted &&
              input.pending_suppression_sweep_raw == raw &&
              input.pending_suppression_sweep == (raw != 0),
          "actual manager base60, raw nonzero, or full Combat binding differs");
  Require(f.domain == before_domain && f.combat == before_combat,
          "readonly source changed manager or Combat memory");
  Require(frame.full_backing_inputs_v1.has_value(),
          "new source erased existing full backing input");
  frame.snapshot_revision = raw == 0 ? 101 : 102;
  const auto control = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
  const auto resume = xar::ck3_11906::SerializeActiveCombatResumeInputsV1(frame);
  Require(!control.empty() && !resume.empty(), "whole production serializer failed");
  const auto boolean = raw == 0 ? "false" : "true";
  const auto branch = raw == 0 ? "normal" : "suppressed";
  return "{\"name\":\"" + std::string(name) + "\",\"battle_control_snapshot\":" +
      control + ",\"active_combat_resume_inputs_v1\":" + resume +
      ",\"expected_current_finalizer_manager_inputs_v1\":{\"source_combat_id\":" +
      std::to_string(kCombat) + ",\"combat_manager_row_admitted\":true," +
      "\"pending_suppression_sweep_raw\":" + std::to_string(raw) +
      ",\"pending_suppression_sweep\":" + boolean + "}," +
      "\"expected_dispatch_branch\":\"" + branch + "\","
      "\"conditional_side_baseline_raw_by_side\":[1000000,1000000],"
      "\"conditional_captured_maximum_per_regiment\":10," +
      "\"expected_normal_survivors_raw_by_side\":[900000,900000]}\n";
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture <new output directory>");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    std::ofstream zero(output / "case-zero.json", std::ios::binary);
    zero << Scene(0, "native_base60_zero_unlocks_normal");
    Require(zero.good(), "write zero whole wire");
    std::ofstream nonzero(output / "case-nonzero.json", std::ios::binary);
    nonzero << Scene(7, "native_base60_nonzero_sweep_precedence");
    Require(nonzero.good(), "write nonzero whole wire");
    std::cout << "Two new whole-control FIRST scenes GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
