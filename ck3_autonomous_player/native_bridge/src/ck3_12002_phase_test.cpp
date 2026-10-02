#include "xar_bridge/ck3_12002_phase.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include <array>
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <iostream>

namespace {
using namespace xar;
template <typename T> void Write(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(T));
}
template <typename T> T Read(const void *p, std::size_t offset) {
  T v{}; std::memcpy(&v, static_cast<const std::byte *>(p) + offset, sizeof(T)); return v;
}
struct Fixture {
  std::array<std::array<std::byte, 0x130>, 2> armies{};
  std::array<std::array<std::byte, 0x20>, 16> characters{};
  std::array<std::array<std::byte, 0x150>, 15> regiments{};
  std::array<std::byte, 0x40> maa_type{};
  std::array<std::byte, 0x20> target{};
  std::array<std::uintptr_t, 3> allocator_vtable{};
  void *allocator = nullptr;
  int constructed = 0;
  int destroyed = 0;
  int population_allocated = 0;
  int population_freed = 0;
  bool inject_source_mismatch = false;
  bool inject_gathering_failure = false;
  bool inject_regiment_header_failure = false;
  bool inject_regiment_identity_failure = false;
  bool inject_knight_unmatched = false;
};
Fixture *active = nullptr;
void Release(void *, void *p, std::size_t alignment) {
  assert(alignment == 8); ++active->population_freed; std::free(p);
}
void *Construct(void *side, void *shell) {
  assert(Read<std::uint32_t>(shell, 0x0C) == 0x436F6D62);
  assert(Read<std::int32_t>(shell, 0x18) == -1);
  ++active->constructed;
  Write<std::uint32_t>(side, 0x340, 0x436F5369);
  Write<std::int32_t>(side, 8, -1);
  Write<std::int32_t>(side, 0x70, -1);
  Write<void *>(side, 0xB8, shell);
  Write<void *>(side, 0x10, std::calloc(8, 4));
  Write<std::int32_t>(side, 0x18, 8);
  Write<void *>(side, 0x40, std::calloc(16, 0x60));
  Write<std::int32_t>(side, 0x48, 16);
  Write<void *>(side, 0x50, &active->allocator);
  return side;
}
void Populate(void *side, void *army) {
  const auto native_id = Read<std::int32_t>(army, 0x10);
  auto count = Read<std::int32_t>(side, 0x1C);
  Write<std::int32_t>(Read<void *>(side, 0x10), static_cast<std::size_t>(count) * 4,
                      native_id + (active->inject_source_mismatch ? 1 : 0));
  Write<std::int32_t>(side, 0x1C, count + 1);
  Write<std::int32_t>(side, 0x70, native_id == 101 ? 501 : 502);
  Write<std::int64_t>(side, 0xA8, native_id == 101 ? 50'000'000 : 40'000'000);
  void *local = Read<void *>(side, 0xC8);
  Write<void *>(local, 0x38, std::calloc(1, 0x50)); ++active->population_allocated;
  Write<std::int32_t>(local, 0x40, 1);
  Write<std::int32_t>(local, 0x44, 1);
  if (native_id == 101) {
    // Frozen Populate 0x264E065 stores MAA and knights together; the native
    // source helper reads +8 and advances by 0x60, skipping regiment +148=-1.
    // The first live army has 14 knights (2751..2764) and ordinary pikemen.
    for (std::size_t i = 0; i < active->regiments.size(); ++i) {
      auto id = Read<std::int32_t>(active->regiments[i].data(), 0x10);
      if (active->inject_knight_unmatched && i == 1) id = 2999;
      Write<std::int32_t>(Read<void *>(side, 0x40), i * 0x60, -123);
      Write<std::int32_t>(Read<void *>(side, 0x40), i * 0x60 + 8, id);
    }
    Write<std::int32_t>(side, 0x4C, 15);
    if (active->inject_regiment_header_failure)
      Write<std::int32_t>(side, 0x48, 14);
  }
}
void *Commander(void *side) {
  auto id = Read<std::int32_t>(Read<void *>(side, 0x10), 0);
  return active->characters[id == 101 ? 0 : 1].data();
}
void Refresh(void *) {}
std::int32_t Strength(void *side) {
  return Read<std::int32_t>(Read<void *>(side, 0x10), 0) == 101 ? 500 : 400;
}
void Destroy(void *side) {
  ++active->destroyed;
  assert(Read<std::uint32_t>(side, 0x340) == 0x436F5369);
  std::free(Read<void *>(side, 0x10)); std::free(Read<void *>(side, 0x40));
  Write<std::uint32_t>(side, 0x340, 0x446C7464);
}
std::int64_t *Dynamic(void *shell, std::int64_t *out, std::int32_t side, void *) {
  assert(Read<std::int32_t>(shell, 0x6D0) == 0);
  assert(Read<std::int32_t>(shell, 0x6D4) == 0);
  auto object = static_cast<std::byte *>(shell) + (side == 0 ? 0x20 : 0x368);
  assert(Read<std::uint32_t>(object, 0x340) == 0x436F5369);
  assert(Read<std::uint8_t>(object, 0x344) == (side == 0 ? 1 : 0));
  *out = side == 0 ? 2'000'000 : 500'000; return out;
}
void Resolve(void *shell) {
  assert(Read<std::int64_t>(shell, 0x6C8) == 0);
  std::int64_t left = 0, right = 0;
  Dynamic(shell, &left, 0, nullptr); Dynamic(shell, &right, 1, nullptr);
  Write<std::int64_t>(shell, 0x710, left - right);
}
bool HasHolding(void *) { return true; }
void *Army(void *context, std::int32_t id) {
  auto &f = *static_cast<Fixture *>(context);
  return id == 101 ? f.armies[0].data() : id == 102 ? f.armies[1].data() : nullptr;
}
void *Character(void *context, std::int32_t id) {
  auto &f = *static_cast<Fixture *>(context);
  return id >= 201 && id <= 216 ? f.characters[static_cast<std::size_t>(id - 201)].data() : nullptr;
}
void *Regiment(void *context, std::int32_t id) {
  auto &f = *static_cast<Fixture *>(context);
  if (f.inject_regiment_identity_failure && id == 67109785) return nullptr;
  // This synthetic unmatched ID resolves to a real knight not present in v2.
  if (id == 2999 && f.inject_knight_unmatched) {
    Write<std::int32_t>(f.regiments[1].data(), 0x10, 2999);
    return f.regiments[1].data();
  }
  for (auto &row : f.regiments)
    if (Read<std::int32_t>(row.data(), 0x10) == id) return row.data();
  return nullptr;
}
void *Province(void *context, std::int32_t id) {
  return id == 1 ? static_cast<Fixture *>(context)->target.data() : nullptr;
}
bool Gathering(void *context, std::int32_t id, bool &out) {
  out = id == 101;
  return !static_cast<Fixture *>(context)->inject_gathering_failure;
}
} // namespace

int main() {
  using namespace xar;
  auto wrong = ck3_12002::BindPhaseImage(0x140000000, "old-build");
  assert(!wrong.enabled && !wrong.construct_side);
  auto bound = ck3_12002::BindPhaseImage(0x140000000, ck3_12002::kExecutableSha256);
  assert(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.construct_side) == 0x14264CA60);
  Fixture f{}; active = &f;
  f.allocator_vtable[2] = reinterpret_cast<std::uintptr_t>(&Release);
  f.allocator = f.allocator_vtable.data();
  for (std::size_t i = 0; i < 2; ++i) {
    Write<std::int32_t>(f.armies[i].data(), 0x10, static_cast<std::int32_t>(101 + i));
    Write<std::int32_t>(f.armies[i].data(), 0x120, static_cast<std::int32_t>(201 + i));
    Write<std::int32_t>(f.armies[i].data(), 0x124, static_cast<std::int32_t>(1 + i));
  }
  for (std::size_t i = 0; i < f.characters.size(); ++i)
    Write<std::int32_t>(f.characters[i].data(), 0x18, static_cast<std::int32_t>(201 + i));
  Write<std::uint32_t>(f.maa_type.data(), 0x38, 0x4744624F);
  for (std::size_t i = 0; i < f.regiments.size(); ++i) {
    Write<std::int32_t>(f.regiments[i].data(), 0x10,
                        i == 0 ? 67109785 : static_cast<std::int32_t>(2750 + i));
    Write<std::uint32_t>(f.regiments[i].data(), 0x14, 0x41725267);
    Write<void *>(f.regiments[i].data(), 0x18, f.maa_type.data());
    Write<std::int32_t>(f.regiments[i].data(), 0x148,
                        i == 0 ? -1 : static_cast<std::int32_t>(202 + i));
  }
  ck3_12002::PhaseBindings bindings{true, Construct, Populate, Commander, Refresh,
                                   Strength, Destroy, Resolve, Dynamic, HasHolding};
  ck3_12002::PhaseEnvironment env{&f, Army, Character, Province, Gathering, Regiment};
  game::Snapshot scope{}; scope.paused = true; scope.has_played_character = true;
  scope.played_character_alive = true;
  game::CombatSimulationInputsSnapshot base{}; base.input_observation_ready = true;
  base.target_province_id = 1; base.target_province.available = true;
  base.target_province.defender_context.available = true;
  base.target_province.defender_context.holding_defender_status = game::CombatObservationStatus::available;
  base.target_province.defender_context.holding_defender = true;
  base.scenario.attacker_army_ids = {1}; base.scenario.defender_army_ids = {2};
  for (int i = 0; i < 2; ++i) {
    game::CombatArmyInputsSnapshot row{}; row.available = true; row.army_id = i + 1;
    row.native_carmy_id_observable = true; row.native_carmy_id = i + 101;
    row.commander.status = game::CombatObservationStatus::available;
    row.commander.character_id = i + 201; row.knights.available = true;
    row.encounter_role = i == 0 ? "attacker" : "defender";
    if (i == 0) {
      for (std::int32_t index = 0; index < 14; ++index) {
        game::CombatKnightSnapshot knight{}; knight.eligible = true;
        knight.character_id = 203 + index; knight.source_regiment_id = 2751 + index;
        knight.army_id = 101; knight.participant_army_membership_verified = true;
        row.knights.members.push_back(knight);
      }
    }
    base.armies.push_back(std::move(row));
  }
  ck3_12002::NativeCombatPhase out{};
  using Status = ck3_12002::ReadNativeCombatPhaseResult;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::available);
  assert(out.available && out.sides[0].strength_raw == 500 && out.sides[1].strength_raw == 400);
  assert(out.dynamic_advantage_at_zero_roll_raw == 1'500'000);
  assert(out.sides[0].ordered_candidates.size() == 15);
  assert(out.sides[0].ordered_candidates[0].role == "commander");
  assert(out.sides[0].ordered_candidates[1].source_regiment_id == 2751);
  assert(out.sides[0].ordered_candidates.back().source_regiment_id == 2764);
  assert(out.sides[0].ordered_candidates[1].source_army_id == 1);
  assert(out.sides[0].source_vector_equivalence);
  assert(f.constructed == 2 && f.destroyed == 2 && f.population_freed == 2);
  game::CombatPhaseInputsV3 full{};
  assert(ck3_12002::ReadCombatPhaseInputs(bindings, env, scope, base, full) ==
         game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable);
  assert(!full.available && full.sides.size() == 2 && !full.unavailable_reason.empty());
  assert(full.characters.size() == 16);
  assert(full.sides[0].candidate_source_proof.source_vector_equivalence);
  assert(full.sides[0].candidate_source_proof.sequence_sha256.size() == 64);
  auto diagnostic = ck3_12002::SerializeCombatPhaseInputsV3(full);
  assert(diagnostic.find("1.20.0.2") != std::string::npos);
  assert(diagnostic.find("81_exact_native") == std::string::npos);
  assert(diagnostic.find("91EDCEED") == std::string::npos);
  assert(diagnostic.find("\"side_strength_raw\":500") != std::string::npos);
  assert(diagnostic.find("\"source_regiment_id\":2751") != std::string::npos);
  assert(diagnostic.find("\"source_regiment_id\":67109785") == std::string::npos);
  assert(diagnostic.find("\"faith\"") == std::string::npos);
  assert(diagnostic.find("\"death_is_glory\"") == std::string::npos);
  assert(diagnostic.find("nonreligious_fields_ready\":false") != std::string::npos);
  game::CombatPhaseInputsV3 values{};
  values.unavailable_reason = "phase_religion_and_rites_implementation_pending";
  values.characters.push_back({});
  values.characters.back().martial = 23;
  values.characters.back().government_is_nomadic = true;
  game::CombatResolvedDynamicSideV3TestOnly dynamic_row{};
  dynamic_row.commander_dynamic_raw = 700'000;
  values.advantage_model.resolved_dynamic.sides.push_back(dynamic_row);
  values.advantage_model.base_static_accumulator_raw = 1'250'000;
  diagnostic = ck3_12002::SerializeCombatPhaseInputsV3(values);
  assert(diagnostic.find("\"martial\":23") != std::string::npos);
  assert(diagnostic.find("\"government_is_nomadic\":true") != std::string::npos);
  assert(diagnostic.find("\"commander_dynamic_raw\":700000") != std::string::npos);
  assert(diagnostic.find("\"base_static_accumulator_raw\":1250000") != std::string::npos);
  assert(diagnostic.find("native_0x264D790") != std::string::npos);
  assert(diagnostic.find("native_0x23C8A60") == std::string::npos);
  std::cout << "PHASE_DIAGNOSTIC_JSON=" << diagnostic << '\n';
  f.inject_source_mismatch = true;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(!out.available && f.constructed == f.destroyed && f.population_allocated == f.population_freed);
  assert(ck3_12002::ReadCombatPhaseInputs(bindings, env, scope, base, full) ==
         game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable);
  assert(full.unavailable_reason ==
         "phase_nonreligious_operand_unavailable:native_sides:phase_native_candidate_source_unavailable:side=0:army_id:index=0:observed=102:expected=101");
  diagnostic = ck3_12002::SerializeCombatPhaseInputsV3(full);
  assert(diagnostic.find("native_sides:phase_native_candidate_source_unavailable") != std::string::npos);
  assert(diagnostic.find("nonreligious_fields_ready\":false") != std::string::npos);
  assert(f.constructed == f.destroyed && f.population_allocated == f.population_freed);
  f.inject_source_mismatch = false;
  base.armies[0].knights.members[0].army_id = 1;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(out.unavailable_reason.find("knight_membership:regiment=2751:army=1:expected=101") != std::string::npos);
  base.armies[0].knights.members[0].army_id = 101;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::available);
  f.inject_regiment_header_failure = true;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(out.unavailable_reason.find("regiment_header:count=15:capacity=14:data_present=1") != std::string::npos);
  f.inject_regiment_header_failure = false;
  f.inject_regiment_identity_failure = true;
  assert(ck3_12002::ReadCombatPhaseInputs(bindings, env, scope, base, full) ==
         game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable);
  assert(full.unavailable_reason.find("regiment_identity:index=0:regiment=67109785:observed=-1:rows=15") != std::string::npos);
  f.inject_regiment_identity_failure = false;
  Write<std::int32_t>(f.armies[0].data(), 0x120, 999);
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(out.unavailable_reason.find("commander:army=1:observed=999:expected=201") != std::string::npos);
  Write<std::int32_t>(f.armies[0].data(), 0x120, 201);
  f.inject_knight_unmatched = true;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(out.unavailable_reason.find("knight_unmatched:index=1:regiment=2999:character=203:rows=15") != std::string::npos);
  f.inject_knight_unmatched = false;
  Write<std::int32_t>(f.regiments[1].data(), 0x10, 2751);
  Write<std::int32_t>(f.regiments[1].data(), 0x148, 999);
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::native_phase_unavailable);
  assert(out.unavailable_reason.find("knight_character:regiment=2751:observed=999:expected=203") != std::string::npos);
  Write<std::int32_t>(f.regiments[1].data(), 0x148, 203);
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::available);
  assert(f.constructed == f.destroyed && f.population_allocated == f.population_freed);
  f.inject_gathering_failure = true;
  auto before_gathering_failure = f.constructed;
  assert(ck3_12002::ReadCombatPhaseInputs(bindings, env, scope, base, full) ==
         game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable);
  assert(full.unavailable_reason ==
         "phase_nonreligious_operand_unavailable:native_sides:phase_gathering_unavailable");
  assert(!full.available && f.constructed == before_gathering_failure);
  f.inject_gathering_failure = false;
  scope.paused = false;
  auto allocation_count = f.constructed;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::requires_paused);
  assert(f.constructed == allocation_count);
  scope.paused = true; scope.played_character_alive = false;
  assert(ck3_12002::ReadNativeCombatPhase(bindings, env, scope, base, out) == Status::no_played_character);
  std::cout << "CK3 1.20.0.2 native phase fixtures passed\n";
}
