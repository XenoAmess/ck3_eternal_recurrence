// Seven new FIRST cases: six whole production wires and one real reader
// identity rejection with both actual serializers returning empty.
// Synthetic memory only. Source preparation 2026-10-07; NOTRUN by this lane.
#include "xar_bridge/battle_current_warscore_caps_v1.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"
#include "xar_bridge/ck3_12002_battle.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using namespace xar::game;

template <std::size_t N> using Bytes = std::array<std::byte, N>;
void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}
template <typename T, std::size_t N>
void Put(Bytes<N> &bytes, std::size_t offset, T value) {
  Require(offset + sizeof(T) <= N, "fixture byte span");
  std::memcpy(bytes.data() + offset, &value, sizeof(T));
}
template <std::size_t N>
void Header(Bytes<N> &bytes, std::size_t offset, const void *data,
            std::int32_t count) {
  Put(bytes, offset, data);
  Put(bytes, offset + 8, count);
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

constexpr std::string_view kExactSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::int32_t kCombat = 0x01000003;
constexpr std::int32_t kResult = 0x01000004;
constexpr std::int32_t kProvince = 2640;
constexpr std::array<std::int32_t, 2> kUnits{0x01000011, 0x01000012};
constexpr std::array<std::int32_t, 2> kArmies{0x01000001, 0x01000002};
constexpr std::array<std::int32_t, 2> kOwners{29829, 0x01000022};
constexpr std::array<std::int32_t, 2> kRegiments{0x01000005, 0x01000006};
constexpr std::array<std::size_t, 2> kSideOffsets{0x20, 0x368};

enum class SourceCase { present, identity_mismatch, wrong_sha, missing_defender };
struct CaseDefinition {
  const char *filename;
  const char *name;
  std::int64_t attacker_cap;
  std::int64_t defender_cap;
  std::int32_t native_winner;
  bool conditional_winner_is_war_attacker;
  SourceCase source;
};
constexpr std::array<CaseDefinition, 7> kCases{{
    {"case-distinct.json", "distinct_loaded_caps", 2'300'000, 1'700'000,
     1, true, SourceCase::present},
    {"case-zero.json", "real_zero_attacker_cap", 0, 1'900'000,
     0, true, SourceCase::present},
    {"case-negative.json", "signed_negative_caps_preserved", -12'345, -67'890,
     0, false, SourceCase::present},
    {"case-large64.json", "signed64_caps_preserved",
     (std::int64_t{1} << 50) + 123, -((std::int64_t{1} << 49) + 77),
     1, false, SourceCase::present},
    {"case-identity-mismatch.json", "full_combat_generation_mismatch",
     2'300'000, 1'700'000, 0, true, SourceCase::identity_mismatch},
    {"case-wrong-sha.json", "wrong_exact_sha_keeps_optional_unavailable",
     2'300'000, 1'700'000, 0, true, SourceCase::wrong_sha},
    {"case-missing-source.json", "one_cap_source_missing_keeps_pair_unavailable",
     2'300'000, 1'700'000, 1, true, SourceCase::missing_defender},
}};

struct Fixture {
  Bytes<0xA8> game_state{};
  Bytes<0x28> jomini_state{};
  Bytes<0x860> province{};
  Bytes<0x730> combat{};
  Bytes<0xD8> result{};
  std::array<Bytes<0x200>, 2> units{};
  std::array<Bytes<0x148>, 2> armies{};
  std::array<Bytes<0x220>, 2> characters{};
  std::array<Bytes<0x150>, 2> regiments{};
  std::array<Bytes<0xA20>, 2> types{};
  std::array<Bytes<0x60>, 2> entries{};
  // The two loaded qwords are eight bytes apart at their actual .3 RVAs.
  Bytes<16> loaded_caps{};
  Store unit_store, army_store, character_store, regiment_store, combat_store,
      result_store;
  void *game_state_root = game_state.data();
  void *jomini_state_root = jomini_state.data();
  void *result_fallback_root = result.data();
  std::int32_t minimum_retreat_days = 14;
  BattleBindings bindings{};
  Snapshot scope{};
  std::uint64_t native_revision = 0;

  static void *ResolveProvince(void *context, std::int32_t id) {
    auto &fixture = *static_cast<Fixture *>(context);
    return id == kProvince ? fixture.province.data() : nullptr;
  }
  static std::int32_t Strength(void *) { return 9; }
  static void *RuleState(void *) { return nullptr; }
  static bool Retreat(void *, void *, void *) { return false; }

  Fixture(const CaseDefinition &definition, std::uint64_t revision) {
    native_revision = revision; // Explicit application-producer fixture metadata.
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = kOwners[0];
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put<std::int32_t>(game_state, 8, scope.date_raw);
    Put<std::uint8_t>(jomini_state, 0x20, 1);
    Put(province, 0x10, kProvince);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76U);
    Put(combat, 8, kCombat);
    Put<std::uint32_t>(combat, 0x0C, 0x436F6D62U);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 3);
    Put<std::int32_t>(combat, 0x6B4, 0);
    Put(combat, 0x6E0, definition.native_winner);
    Put<std::int32_t>(combat, 0x700, -1);
    Put(combat, 0x708, kResult);
    Put<std::int32_t>(combat, 0x6C0, 100);
    Put<std::int32_t>(combat, 0x6C4, 100);
    Put(result, 8, kResult);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    combat_store.Set(kCombat, combat.data());
    result_store.Set(kResult, result.data());

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
      const auto offset = kSideOffsets[side];
      Header(combat, offset + 0x10, &kArmies[side], 1);
      Header(combat, offset + 0x28, entries[side].data(), 1);
      Put(combat, offset + 0xB8, combat.data());
      Put(combat, offset + 0x70, kOwners[side]);
      Put<std::int32_t>(combat, offset + 0x74, -1);
      Put<std::int64_t>(combat, offset + 0x98, 800'000);
      Put<std::int64_t>(combat, offset + 0xA0, 800'000);
      Put<std::int64_t>(combat, offset + 0xA8, 1'000'000);
    }

    ArmySnapshot subject{};
    subject.army_id = kUnits[0];
    subject.controllable = true;
    subject.in_combat = true;
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

    Put<std::int64_t>(loaded_caps, 0, definition.defender_cap);
    Put<std::int64_t>(loaded_caps, 8, definition.attacker_cap);
    const auto image_base = reinterpret_cast<std::uintptr_t>(loaded_caps.data()) -
                            kBattleWarDefenderWinnerCap12003Rva;
    bindings.current_warscore_caps = BindBattleCurrentWarscoreCaps12003(
        image_base, definition.source == SourceCase::wrong_sha
                        ? std::string_view{"wrong_exact_sha"} : kExactSha);
    if (definition.source == SourceCase::missing_defender)
      bindings.current_warscore_caps.war_defender_winner_cap = nullptr;
    if (definition.source == SourceCase::identity_mismatch)
      Put<std::int32_t>(combat, 8, kCombat + 0x01000000);
  }
};

std::string ExpectedCaps(const CaseDefinition &definition) {
  if (definition.source != SourceCase::present) return "null";
  return "{\"source_combat_id\":" + std::to_string(kCombat) +
      ",\"war_attacker_winner_cap_raw_q100000\":" +
      std::to_string(definition.attacker_cap) +
      ",\"war_defender_winner_cap_raw_q100000\":" +
      std::to_string(definition.defender_cap) + "}";
}

std::string Scene(const CaseDefinition &definition, std::uint64_t revision) {
  Fixture fixture(definition, revision);
  BattleControlSnapshot frame{};
  const BattleControlRequest request{kUnits[0]};
  const auto status = ReadBattleControlSnapshot(
      fixture.bindings, fixture.scope, request, frame);
  const bool identity_rejected = definition.source == SourceCase::identity_mismatch;
  Require(status == (identity_rejected ? BattleControlSnapshotStatus::state_changed
                                      : BattleControlSnapshotStatus::available),
          "actual whole reader status differs");
  const auto native_status = status == BattleControlSnapshotStatus::available
                                 ? "available" : "state_changed";
  Require(frame.battle_control_ready == !identity_rejected,
          "actual control readiness differs");
  if (!identity_rejected) {
    Require(frame.winner_raw == definition.native_winner,
            "actual native winner was not observed");
    // The application owner supplies revision after the actual native read.
    frame.snapshot_revision = fixture.native_revision;
  }
  const auto expected_caps = ExpectedCaps(definition);
  Require(frame.current_warscore_caps_v1.has_value() ==
              (definition.source == SourceCase::present),
          "actual optional cap availability differs");
  if (frame.current_warscore_caps_v1) {
    const auto &caps = *frame.current_warscore_caps_v1;
    Require(caps.source_combat_id == kCombat &&
                caps.war_attacker_winner_cap_raw_q100000 == definition.attacker_cap &&
                caps.war_defender_winner_cap_raw_q100000 == definition.defender_cap,
            "loaded cap signed64 pair or same Combat identity differs");
  }

  // Both real production serializers consume this one actual reader result.
  const auto control = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
  const auto resume = xar::ck3_11906::SerializeActiveCombatResumeInputsV1(frame);
  if (identity_rejected) {
    Require(control.empty() && resume.empty(),
            "identity-rejected real frame unexpectedly serialized");
  } else {
    Require(!control.empty() && !resume.empty(), "actual whole serializer failed");
    const auto fragment = "\"current_warscore_caps_v1\":" + expected_caps;
    Require(control.find(fragment) != std::string::npos &&
                resume.find(fragment) != std::string::npos,
            "actual main/resume cap mirror differs");
  }
  const bool cap_available = definition.source == SourceCase::present;
  const auto selected = definition.conditional_winner_is_war_attacker
                            ? definition.attacker_cap : definition.defender_cap;
  return "{\"name\":\"" + std::string(definition.name) +
      "\",\"battle_control_snapshot\":" + (control.empty() ? "null" : control) +
      ",\"active_combat_resume_inputs_v1\":" + (resume.empty() ? "null" : resume) +
      ",\"native_control_status\":\"" + native_status + "\"" +
      ",\"fixture_snapshot_context\":{\"native_revision\":" +
      std::to_string(fixture.native_revision) + ",\"date_raw\":" +
      std::to_string(fixture.scope.date_raw) + ",\"subject_public_cunit_id\":" +
      std::to_string(request.subject_public_cunit_id) + "}" +
      ",\"expected_current_warscore_caps_v1\":" + expected_caps +
      ",\"conditional_winner_is_war_attacker\":" +
      (definition.conditional_winner_is_war_attacker ? "true" : "false") +
      ",\"membership_source\":\"explicit_same_invocation_fixture_condition\"" +
      ",\"expected_native_winner_raw\":" +
      (identity_rejected ? "null" : std::to_string(definition.native_winner)) +
      ",\"expected_selected_cap_raw_q100000\":" +
      (cap_available ? std::to_string(selected) : "null") +
      ",\"expected_control_status\":\"" +
      (identity_rejected ? "state_changed" : "available") +
      "\",\"expected_serializer_output_empty\":" +
      (identity_rejected ? "true" : "false") +
      ",\"expected_cap_selection_status\":\"" +
      (identity_rejected ? "not_reached" : cap_available ? "ready" : "partial") +
      "\",\"expected_unknown_membership_status\":\"partial\"}\n";
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture <new output directory>");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    for (std::size_t index = 0; index != kCases.size(); ++index) {
      const auto &definition = kCases[index];
      std::ofstream wire(output / definition.filename, std::ios::binary);
      wire << Scene(definition, 201 + static_cast<std::uint64_t>(index));
      Require(wire.good(), "write current cap FIRST packet");
    }
    std::cout << "Seven new cap FIRST cases GREEN: six actual whole wires and "
                 "one reader identity rejection with two empty serializers\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
