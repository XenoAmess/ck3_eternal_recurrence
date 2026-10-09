// AUTHOR_NOT_RUN: one new connected production-observer -> whole V2 packet.
#include "xar_bridge/ck3_12004_combat.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/combat_simulation_inputs_v2_wire.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
namespace native = xar::ck3_12004;
namespace game = xar::game;
constexpr std::uintptr_t kImage = 0x140000000ULL;
constexpr std::int32_t kDate = 53236632;
constexpr std::uint32_t kLinked = 0x03000001;
constexpr std::uint32_t kSelectedA = 0x04000002;
constexpr std::uint32_t kSelectedB = 0x05000003;
constexpr std::int32_t kRegiment = 0x06000004;
constexpr std::int32_t kAttacker = 0x01000001;
constexpr std::int32_t kDefender = 0x01000002;
constexpr std::int32_t kWar = 0x01000001;
constexpr std::int32_t kTarget = 101;
constexpr std::uintptr_t kWrapperReturn = 0x2634509;
constexpr std::array<std::size_t, 6> kSkillOffsets{0xEC, 0xD8, 0xE4, 0xE8, 0xDC, 0xE0};
constexpr std::array<std::int32_t, 6> kSkills{-2, -3, 0, 4, -5, 6};
constexpr std::array<std::int64_t, 9> kOperands{
    100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000};
constexpr std::array<std::int64_t, 9> kMainModifiers{
    -25000, 0, 0, -10000, 0, 0, 0, 0, 0};
constexpr std::uintptr_t kCountReturn = 0xF123456700000000ULL;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <typename Pointer>
std::uintptr_t Identity(Pointer value) noexcept {
  return reinterpret_cast<std::uintptr_t>(value);
}
void *Offset(void *value, std::size_t offset) noexcept {
  return static_cast<std::byte *>(value) + offset;
}

class Memory {
  struct Block {
    std::unique_ptr<std::byte[]> data;
    std::size_t size = 0;
  };
  std::vector<Block> blocks_;
public:
  const void *refused_values = nullptr;
  std::size_t refused_reads = 0;
  std::size_t unexpected_reads = 0;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *address = data.get();
    blocks_.push_back({std::move(data), size});
    return address;
  }
  template <typename Value>
  void Put(void *base, std::size_t offset, Value value) {
    std::memcpy(Offset(base, offset), &value, sizeof(value));
  }
  template <typename Value>
  Value Get(const void *base, std::size_t offset = 0) const {
    Value result{};
    std::memcpy(&result, static_cast<const std::byte *>(base) + offset, sizeof(result));
    return result;
  }
  static bool Copy(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    if (address == memory.refused_values && memory.refused_values != nullptr) {
      ++memory.refused_reads;
      return false;
    }
    const auto requested = Identity(address);
    for (const auto &block : memory.blocks_) {
      const auto base = Identity(block.data.get());
      if (requested >= base && requested - base <= block.size &&
          size <= block.size - (requested - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    ++memory.unexpected_reads;
    return false;
  }
};

struct Context {
  void *model = nullptr;
  void *context = nullptr;
  void *keys = nullptr;
  void *values = nullptr;
};

struct World {
  Memory memory;
  void *linked = memory.Allocate(0x1D0);
  void *selected_a = memory.Allocate(0x1D0);
  void *selected_b = memory.Allocate(0x1D0);
  void *game_state = memory.Allocate(0x10);
  void *game_slot = memory.Allocate(sizeof(void *));
  void *damage_coefficient = memory.Allocate(sizeof(std::int32_t));
  void *toughness_coefficient = memory.Allocate(sizeof(std::int32_t));
  void *query_output = memory.Allocate(0x38);
  void *native_output = memory.Allocate(0x38);
  Context primary, alternate, second;
  std::size_t preparation_original_calls = 0;
  std::size_t preparation_append_calls = 0;
  std::size_t wrapper_original_calls = 0;
  std::size_t context_original_calls = 0;
  std::size_t active_wrapper = 0;
  std::size_t active_key = 0;
  bool abi_matches = true;
  std::array<std::uintptr_t, 18> actual_context_returns{};

  World() {
    memory.Put(linked, 0x18, kLinked);
    memory.Put(linked, 0xEC, std::int32_t{3});
    memory.Put(selected_a, 0x18, kSelectedA);
    memory.Put(selected_b, 0x18, kSelectedB);
    for (auto *selected : {selected_a, selected_b}) {
      memory.Put(selected, 0x1C0, static_cast<void *>(nullptr));
      for (std::size_t index = 0; index < kSkillOffsets.size(); ++index)
        memory.Put(selected, kSkillOffsets[index], kSkills[index]);
    }
    memory.Put(game_slot, 0, game_state);
    memory.Put(game_state, 0x08, kDate);
    memory.Put(damage_coefficient, 0, std::int32_t{100});
    memory.Put(toughness_coefficient, 0, std::int32_t{10});
    primary = MakeContext(selected_a, false);
    alternate = MakeContext(selected_a, true);
    second = MakeContext(selected_b, false);
  }

  Context MakeContext(void *owner, bool alternate_c5) {
    Context result;
    result.model = memory.Allocate(0x100);
    result.context = Offset(result.model, 0x10);
    result.keys = memory.Allocate(9 * sizeof(std::uint16_t));
    result.values = memory.Allocate(9 * sizeof(std::int64_t));
    memory.Put(result.model, 0x08, owner);
    auto *pc = Offset(result.context, 0x68);
    memory.Put(pc, 0x00, result.keys);
    memory.Put(pc, 0x0C, std::int32_t{9});
    memory.Put(pc, 0x68, result.values);
    for (std::size_t index = 0; index < 9; ++index) {
      memory.Put(result.keys, index * sizeof(std::uint16_t),
                 static_cast<std::uint16_t>(0xC1 + index));
      memory.Put(result.values, index * sizeof(std::int64_t),
                 alternate_c5 && index == 4 ? std::int64_t{15000}
                                            : kMainModifiers[index]);
    }
    return result;
  }
  Context &ReturnedContext() {
    if (active_wrapper == 1) return second;
    return active_key == 4 ? alternate : primary;
  }
};
World *active = nullptr;

std::uintptr_t __fastcall PreparationOriginal(
    void *character, void *context, std::uint32_t index) {
  auto &world = *active;
  world.abi_matches &= character == world.selected_a &&
      context == world.primary.context && index == world.preparation_original_calls;
  ++world.preparation_original_calls;
  return kCountReturn;
}
std::uintptr_t __fastcall PreparationAppendOriginal(void *, void *, std::int64_t) {
  ++active->preparation_append_calls;
  return 0xAABBCCDD12345678ULL;
}

void *__fastcall ContextOriginal(void *character) {
  auto &world = *active;
  ++world.context_original_calls;
  world.abi_matches &= character ==
      (world.active_wrapper == 0 ? world.selected_a : world.selected_b);
  auto &context = world.ReturnedContext();
  if (world.active_wrapper == 1 && world.active_key == 3)
    world.memory.refused_values = context.values;
  return context.context;
}

void *__fastcall WrapperOriginal(void *output, void *linked) {
  auto &world = *active;
  world.active_wrapper = world.wrapper_original_calls++;
  Require(world.active_wrapper < 2, "wrapper original replayed");
  world.abi_matches &= linked == world.linked && output ==
      (world.active_wrapper == 0 ? world.query_output : world.native_output);
  auto *selected = world.active_wrapper == 0 ? world.selected_a : world.selected_b;
  std::int64_t effectiveness = 100000;
  for (std::size_t index = 0; index < 9; ++index) {
    world.active_key = index;
    auto &expected = world.ReturnedContext();
    const auto calls_before = world.context_original_calls;
    auto *context = native::InvokeKnightStatContext12004(selected,
        kImage + native::kKnightStatContextReturns12004[index]);
    Require(world.context_original_calls == calls_before + 1 &&
                context == expected.context,
            "context dispatch changed original result or exact call count");
    world.actual_context_returns[world.active_wrapper * 9 + index] = Identity(context);
    world.memory.refused_values = nullptr;
    // Deterministic typed original target reads its real returned PC and
    // operand independently of the auxiliary guarded-copy failure.
    const auto modifier = world.memory.Get<std::int64_t>(
        expected.values, index * sizeof(std::int64_t));
    effectiveness += modifier * kOperands[index] / 100000;
  }
  const auto prowess = world.memory.Get<std::int32_t>(linked, 0xEC);
  const auto damage = world.memory.Get<std::int32_t>(world.damage_coefficient);
  const auto toughness = world.memory.Get<std::int32_t>(world.toughness_coefficient);
  const auto common = effectiveness * (prowess < 1 ? 1 : prowess);
  world.memory.Put(output, 0x08, std::int32_t{0});
  world.memory.Put(output, 0x10, std::int64_t{0});
  world.memory.Put(output, 0x18, common * damage);
  world.memory.Put(output, 0x20, common * toughness);
  world.memory.Put(output, 0x28, std::int64_t{0});
  world.memory.Put(output, 0x30, std::int64_t{0});
  return output;
}

void Configure(World &world) {
  auto bindings = native::BindKnightStatConsumptionImage12004(
      kImage, native::kExecutableSha256);
  Require(bindings.enabled && bindings.image_base == kImage &&
              Identity(bindings.game_state_slot) == kImage + 0x5C68C50 &&
              Identity(bindings.damage_multiplier) == kImage + 0x5C699A8 &&
              Identity(bindings.toughness_multiplier) == kImage + 0x5C699B0 &&
              !native::BindKnightStatConsumptionImage12004(kImage, "fixture-other-build").enabled,
          "actual4 knight observer factory lost its exact image/SHA binding");
  const auto combat = native::BindCombatImage12004(kImage, native::kExecutableSha256);
  Require(combat.enabled && Identity(combat.evaluate_regiment_stats_at_province) ==
              kImage + 0x26344A0 &&
              Identity(combat.get_character_modifier_aggregator) == kImage + 0x28C3AC0 &&
              Identity(combat.knight_damage_per_prowess) ==
                  Identity(bindings.damage_multiplier) &&
              Identity(combat.knight_toughness_per_prowess) ==
                  Identity(bindings.toughness_multiplier),
          "real actual4 Combat factory does not share the held stat/context/coefficient targets");
  bindings.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  bindings.damage_multiplier = static_cast<const std::int32_t *>(world.damage_coefficient);
  bindings.toughness_multiplier = static_cast<const std::int32_t *>(world.toughness_coefficient);
  bindings.read_context = &world.memory;
  bindings.read_memory = &Memory::Copy;
  native::PersonSixStageCaptureBindings12004 preparation;
  preparation.memory = native::BindPersonCarrierDirect12004(kImage,
      native::kGameVersion, native::kExecutableSha256, &Memory::Copy, &world.memory);
  preparation.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  Require(native::InitializePersonSixStageCaptureFixture12004(preparation,
              &PreparationOriginal, &PreparationAppendOriginal),
          "Native65 production PC-copy/preparation fixture initialization failed");
  for (std::uint32_t index = 0; index < 6; ++index) {
    const auto bits = native::InvokePersonSixStageCapture12004(world.selected_a,
        world.primary.context, index, kImage + native::kPersonSixStageReturnRva12004);
    Require(bits == kCountReturn && world.preparation_original_calls == index + 1,
            "new connected preparation setup changed original count or full return bits");
  }
  native::CompletePersonSixStageCapture12004(Identity(world.selected_a), kSelectedA,
                                            Identity(world.primary.context));
  const auto historical = native::ReadPersonSixStageCaptureForCharacter12004(
      Identity(world.selected_a), kSelectedA);
  Require(historical.capture_complete && historical.capture_sequence == 1 &&
              historical.preparation_model.ready &&
              historical.preparation_model.owner_matches_capture == true &&
              historical.post_six_aggregate.pc.ready &&
              historical.post_six_aggregate.pc.properties &&
              historical.post_six_aggregate.pc.properties->values_q64 ==
                  std::vector<std::int64_t>(kMainModifiers.begin(), kMainModifiers.end()),
          "connected preparation did not own the actual historical aggregate/postimage");
  Require(native::InitializeKnightStatConsumptionFixture12004(
              bindings, &WrapperOriginal, &ContextOriginal),
          "production knight wrapper/context fixture initialization failed");
}

void AssertQuery(const World &world, const native::KnightStatConsumptionQuery12004 &query) {
  Require(query.configured && !query.observer_installed && query.events.size() == 2 &&
              query.oldest_available_sequence == 1 && query.latest_sequence == 2 &&
              query.overwritten_events == 0 && query.build_version == native::kGameVersion &&
              query.executable_sha256 == native::kExecutableSha256,
          "owned actual4 wrapper query cardinality/build boundary changed");
  for (std::size_t event_index = 0; event_index < 2; ++event_index) {
    const auto &event = query.events[event_index];
    Require(event.sequence == event_index + 1 && event.contexts.size() == 9 &&
                event.linked_character_id == kLinked &&
                event.linked_character_identity == Identity(world.linked) &&
                event.linked_prowess_points == 3 && event.loaded_damage_multiplier == 100 &&
                event.loaded_toughness_multiplier == 10 && event.observed_date_raw == kDate &&
                event.wrapper_caller_return_rva == kWrapperReturn &&
                !event.entry_association_proven &&
                event.output_cache_identity == Identity(event_index == 0 ?
                    world.query_output : world.native_output) &&
                event.native_return_identity == event.output_cache_identity,
            "wrapper observation lost its actual owner, operands, return or honest Entry boundary");
    Require(event.origin == (event_index == 0 ? "bridge_query_scratch" :
                "native_wrapper_output_unclassified") &&
                (event_index == 0 ? event.regiment_id == kRegiment &&
                    event.target_province_id == kTarget :
                    !event.regiment_id && !event.target_province_id),
            "query scratch was promoted to a native physical Entry association");
    Require(event.observed_output.ready && event.observed_output.max_size == 0 &&
                event.observed_output.siege_value_raw == 0 &&
                event.observed_output.damage_raw == (event_index == 0 ? 15000000 : 28500000) &&
                event.observed_output.toughness_raw == (event_index == 0 ? 1500000 : 2850000) &&
                event.observed_output.pursuit_raw == 0 && event.observed_output.screen_raw == 0,
            "actual original output changed after an auxiliary PC read failure");
    for (std::size_t index = 0; index < 9; ++index) {
      const auto &context = event.contexts[index];
      const auto expected_context = event_index == 1 ? world.second.context :
          (index == 4 ? world.alternate.context : world.primary.context);
      const bool failed = event_index == 1 && index == 3;
      Require(context.property_key == 0xC1 + index &&
                  context.caller_return_rva == native::kKnightStatContextReturns12004[index] &&
                  context.selected_character_id == (event_index == 0 ? kSelectedA : kSelectedB) &&
                  context.selected_character_identity == Identity(event_index == 0 ?
                      world.selected_a : world.selected_b) &&
                  context.context_identity == Identity(expected_context) &&
                  context.operand_raw == kOperands[index] &&
                  context.consumed_pc.identity == Identity(expected_context) + 0x68 &&
                  context.consumed_pc.count_i32 == 9 &&
                  context.consumed_pc.ready == !failed && context.consumed_pc.properties &&
                  context.consumed_pc.properties->keys_u16 &&
                  static_cast<bool>(context.consumed_pc.properties->values_q64) == !failed,
              "per-Ci actual receiver/context/PC stage, signed operand or partial readiness changed");
      if (failed)
        Require(context.consumed_pc.reason == "pc_values_unread",
                "failed admitted PC values were replaced by known zero or empty");
      if (event_index == 0) {
        Require(context.preparation_capture_sequence == 1 &&
                    context.preparation_model_identity == Identity(world.primary.model) &&
                    context.preparation_context_identity == Identity(world.primary.context) &&
                    context.preparation_owner_character_id == kSelectedA &&
                    context.context_matches_preparation == (index != 4) &&
                    context.owner_matches_preparation == true &&
                    context.pc_matches_preparation_post == (index != 4),
                "historical preparation context/owner/PC association changed");
      } else {
        Require(!context.preparation_capture_sequence &&
                    !context.preparation_model_identity && !context.preparation_context_identity &&
                    !context.preparation_owner_character_id &&
                    !context.context_matches_preparation && !context.owner_matches_preparation &&
                    !context.pc_matches_preparation_post,
                "unobserved selected Character borrowed another historical preparation");
      }
    }
  }
}

game::CombatArmyInputsSnapshot Army(bool attacker) {
  game::CombatArmyInputsSnapshot row;
  row.available = true;
  row.army_id = attacker ? kAttacker : kDefender;
  row.native_carmy_id_observable = true;
  row.native_carmy_id = attacker ? 0x02000001 : 0x02000002;
  row.encounter_role = attacker ? "attacker" : "defender";
  row.scope_role = attacker ? game::ArmyStrengthScopeRole::player :
      game::ArmyStrengthScopeRole::active_war_enemy;
  row.war_ids = {kWar};
  row.current_province_observable = true;
  row.current_province_id = attacker ? 100 : 101;
  row.owner.status = game::CombatObservationStatus::available;
  row.owner.character_id = attacker ? 707 : 808;
  row.owner.unavailable_reason.clear();
  row.commander.status = game::CombatObservationStatus::absent;
  row.commander.unavailable_reason.clear();
  row.regiments_observable = true;
  row.knights.available = true;
  row.knights.unavailable_reason.clear();
  row.knights.loaded_damage_multiplier = 100;
  row.knights.loaded_toughness_multiplier = 10;
  if (attacker) {
    game::CombatRegimentSnapshot regiment;
    regiment.available = true;
    regiment.regiment_id = kRegiment;
    regiment.identity_valid = true;
    regiment.current_soldiers = regiment.maximum_soldiers = 1;
    regiment.maa_type.status = game::CombatObservationStatus::absent;
    regiment.maa_type.unavailable_reason.clear();
    regiment.kind.status = game::CombatObservationStatus::available;
    regiment.kind.value = "levy";
    regiment.kind.fights_in_main_phase = false;
    regiment.kind.unavailable_reason.clear();
    regiment.effective_stats.available = true;
    regiment.effective_stats.source_target_province_id = kTarget;
    regiment.effective_stats.damage_raw = 15000000;
    regiment.effective_stats.toughness_raw = 1500000;
    regiment.effective_stats.unavailable_reason.clear();
    regiment.counter.status = game::CombatObservationStatus::absent;
    regiment.counter.unavailable_reason.clear();
    row.regiments.push_back(regiment);
    game::CombatKnightSnapshot knight;
    knight.eligible = true;
    knight.character_id = static_cast<std::int32_t>(kLinked);
    knight.source_regiment_id = kRegiment;
    knight.army_id = row.native_carmy_id;
    knight.participant_army_membership_verified = true;
    knight.prowess = 3;
    knight.knight_effectiveness_raw = 50000;
    knight.effective_damage_raw = 15000000;
    knight.effective_toughness_raw = 1500000;
    row.knights.members.push_back(knight);
  }
  return row;
}

game::CombatSimulationInputsSnapshot Snapshot(native::KnightStatConsumptionQuery12004 query) {
  game::CombatSimulationInputsSnapshot snapshot;
  snapshot.target_province_id = kTarget;
  snapshot.scenario.attacker_entry_province_id = 100;
  snapshot.scenario.attacker_army_ids = {kAttacker};
  snapshot.scenario.defender_army_ids = {kDefender};
  snapshot.scenario.attacker_side = "player_or_allied";
  snapshot.scenario.defender_side = "enemy";
  snapshot.armies = {Army(true), Army(false)};
  snapshot.target_province.province_id = kTarget;
  snapshot.target_province.unavailable_reason = "fixture_target_context_unavailable";
  snapshot.target_province.terrain.unavailable_reason = "fixture_terrain_unavailable";
  for (const bool first : {true, false}) {
    game::CombatCounterResolutionSnapshot resolution;
    resolution.countered_side = first ? "player_or_allied" : "enemy";
    resolution.countering_side = first ? "enemy" : "player_or_allied";
    resolution.class_count = 1;
    resolution.unavailable_reason = "fixture_counter_resolution_unavailable";
    snapshot.counter_resolutions.push_back(resolution);
  }
  snapshot.missing_required_domains = {
      "target_terrain", "crossing", "attacker_defender_holding", "contact_combat_width",
      "commander_and_roll_bounds", "counter_resolutions",
      "damage_to_casualty_allocation", "pursuit_transition",
      "battle_end_and_retreat_transition", "phase_event_rng_and_effects"};
  snapshot.knight_stat_consumption_v1 = std::move(query);
  return snapshot;
}

void Write(const std::filesystem::path &path, std::string_view text) {
  Require(!std::filesystem::exists(path), "fresh whole fixture output already exists");
  std::ofstream stream(path, std::ios::binary);
  stream << text << '\n';
  Require(static_cast<bool>(stream), "cannot persist new whole knight consumption packet");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: xar_knight_stat_consumption_12004_whole <fresh output directory>");
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    World world;
    active = &world;
    Configure(world);
    {
      native::KnightStatBridgeQueryScope12004 scope(world.query_output, kRegiment, kTarget);
      const auto returned = native::InvokeKnightStatWrapper12004(
          world.query_output, world.linked, kImage + kWrapperReturn);
      Require(returned == world.query_output && world.wrapper_original_calls == 1 &&
                  world.context_original_calls == 9,
              "bridge scratch wrapper changed its actual original result/call count");
    }
    const auto returned = native::InvokeKnightStatWrapper12004(
        world.native_output, world.linked, kImage + kWrapperReturn);
    Require(returned == world.native_output && world.wrapper_original_calls == 2 &&
                world.context_original_calls == 18 && world.preparation_original_calls == 6 &&
                world.preparation_append_calls == 0 && world.abi_matches &&
                world.memory.refused_reads == 1 && world.memory.unexpected_reads == 0,
            "native unclassified wrapper or failed auxiliary PC copy changed actual execution");
    const std::array regiment_ids{kRegiment};
    const std::array linked_ids{static_cast<std::int32_t>(kLinked)};
    auto query = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(query.has_value(), "configured actual4 knight query family absent");
    AssertQuery(world, *query);
    // These already captured stages are immutable when later source data moves.
    world.memory.Put(world.primary.values, 0, std::int64_t{999999});
    world.memory.Put(world.selected_a, 0x18, std::uint32_t{0x07000002});
    const auto later = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(later && *later == *query && world.wrapper_original_calls == 2 &&
                world.context_original_calls == 18,
            "query reread current source or replayed original callbacks instead of owned stages");
    const auto snapshot = Snapshot(std::move(*query));
    const auto body = xar::bridge::SerializeCombatSimulationInputsV2(snapshot);
    Require(body.find("\"knight_stat_consumption_v1\":{") != std::string::npos &&
                body.find(native::kKnightStatConsumptionSchema12004) != std::string::npos,
            "literal integrated production V2 serializer omitted new typed observer family");
    const std::string packet =
        "{\"type\":\"command_result\",\"protocol_version\":1,"
        "\"request_id\":\"knight-stat-consumption-12004-whole\",\"ok\":true,"
        "\"result\":{\"step\":\"query-combat-simulation-inputs-v2-101-100-a-1-16777217-d-1-16777218\","
        "\"accepted\":true,\"status\":\"partial\",\"query_sequence\":1,"
        "\"combat_simulation_inputs\":" + body + "}}";
    Write(directory / "knight-stat-consumption-12004-whole.json", packet);
    Write(directory / "knight-stat-consumption-12004-fixture-receipt.json",
        "{\"status\":\"PASS\",\"original_target_kind\":\"typed_fixture_callbacks\","
        "\"native_EXE_invoked\":false,\"entry_installer_executed\":false,"
        "\"old_fixture_replayed\":false,\"wrapper_calls\":2,\"wrapper_original_calls\":2,"
        "\"context_calls\":18,\"context_original_calls\":18,"
        "\"connected_preparation_count_original_calls\":6,\"append_original_calls\":0,"
        "\"actual4_observer_factory_bound\":true,\"actual4_combat_factory_bound\":true,"
        "\"original_results_preserved\":true,\"one_auxiliary_PC_values_copy_refused\":true,"
        "\"source_mutation_did_not_replace_owned_stages\":true,"
        "\"entry_association_proven\":false,\"native_revision\":49,"
        "\"public_revision\":97,\"date_raw\":53236632}");
    active = nullptr;
    std::cout << "one actual4 knight consumption whole packet: typed originals 2/18, one PC read failure\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
