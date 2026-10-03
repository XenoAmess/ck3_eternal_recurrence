#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}

constexpr std::int32_t kMaximumStorageCapacity = 1'000'000;
using ReleaseVector = void (*)(void *, void *, std::uint64_t);

void *ResolveCharacter(void **slot, std::int32_t id) noexcept {
  if (id == -1 || slot == nullptr || *slot == nullptr) return nullptr;
  void *objects = Load<void *>(*slot, 0x20);
  const auto capacity = Load<std::int32_t>(*slot, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
  if (objects == nullptr || capacity < 0 ||
      capacity > kMaximumStorageCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *object = Load<void *>(objects, index * 0x10ULL + 8);
  return object != nullptr && Load<std::int32_t>(object, 0x18) == id &&
                 Load<std::uint32_t>(object, 0x1C) == 0x43686172U
             ? object : nullptr;
}

ReleaseVector VectorRelease(void *allocator) noexcept {
  if (allocator == nullptr) return nullptr;
  void *vtable = Load<void *>(allocator, 0);
  return vtable == nullptr ? nullptr : Load<ReleaseVector>(vtable, 0x10);
}

struct OwnedCandidateVector {
  CommanderPointerVector value{};
  ReleaseVector release = nullptr;
  ~OwnedCandidateVector() {
    if (value.data != nullptr && release != nullptr)
      release(value.allocator, value.data, 8);
  }
};

bool ArmyIdentityUnchanged(const CommanderBindings &bindings, void *unit,
                           void *army,
                           const ArmyCommanderCandidatesSnapshot &output) {
  return ck3_12002::ResolveArmyUnit(bindings.armies, output.army_id) == unit &&
      ck3_12002::ResolveInternalArmy(bindings.armies, output.native_carmy_id) ==
          army &&
      Load<std::int32_t>(unit, 0x178) == output.native_carmy_id &&
      Load<std::int32_t>(unit, 0x174) == output.owner_character_id &&
      Load<std::int32_t>(army, 0x124) == output.army_id &&
      Load<std::int32_t>(army, 0x120) == output.current_commander_character_id;
}

} // namespace

CommanderBindings BindCommanderImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CommanderBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  // These existing .2 army/storage helpers are byte-identical in the reviewed
  // .3 spans; only this exact .3 entry point admits the new candidate getters.
  result.armies = ck3_12002::BindArmyImage(image_base,
                                         ck3_12002::kExecutableSha256);
  result.character_storage_slot = reinterpret_cast<void **>(
      image_base + ck3_12002::kCharacterStorageSlotRva);
  result.vector_allocator = reinterpret_cast<void *>(image_base + 0x54DEBB8);
  result.collect_candidates = reinterpret_cast<decltype(result.collect_candidates)>(
      image_base + 0x2C11C10);
  result.can_set_commander = reinterpret_cast<decltype(result.can_set_commander)>(
      image_base + 0x2971510);
  result.get_native_ai_base_quality = reinterpret_cast<decltype(result.get_native_ai_base_quality)>(
      image_base + 0x2C0B270);
  result.get_generic_advantage = reinterpret_cast<decltype(result.get_generic_advantage)>(
      image_base + 0xC6DED0);
  result.get_army_commander = reinterpret_cast<decltype(result.get_army_commander)>(
      image_base + 0x24E9ED0);
  return result;
}

CommanderCandidatesReadResult ReadArmyCommanderCandidates(
    const CommanderBindings &bindings, const game::Snapshot &paused_scope,
    std::int32_t army_id, ArmyCommanderCandidatesSnapshot &output) noexcept {
  output = {};
  output.army_id = army_id;
  if (!bindings.enabled || !bindings.armies.enabled ||
      bindings.character_storage_slot == nullptr ||
      bindings.collect_candidates == nullptr ||
      bindings.can_set_commander == nullptr ||
      bindings.get_native_ai_base_quality == nullptr ||
      bindings.get_generic_advantage == nullptr ||
      bindings.get_army_commander == nullptr) {
    output.unavailable_reason = "commander_bindings_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  if (!paused_scope.paused || !paused_scope.map_ready ||
      !paused_scope.has_played_character || !paused_scope.played_character_alive) {
    output.unavailable_reason = "paused_player_scope_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  const auto selected = std::find_if(
      paused_scope.player_armies.begin(), paused_scope.player_armies.end(),
      [army_id, &paused_scope](const auto &row) {
        return row.army_id == army_id && row.controllable &&
            row.owner_character_id == paused_scope.played_character_id;
      });
  if (selected == paused_scope.player_armies.end()) {
    output.unavailable_reason = "army_outside_current_player_scope";
    return CommanderCandidatesReadResult::unavailable;
  }
  void *unit = ck3_12002::ResolveArmyUnit(bindings.armies, army_id);
  if (unit == nullptr) {
    output.unavailable_reason = "public_cunit_not_found";
    return CommanderCandidatesReadResult::unavailable;
  }
  output.native_carmy_id = Load<std::int32_t>(unit, 0x178);
  output.owner_character_id = Load<std::int32_t>(unit, 0x174);
  void *army = ck3_12002::ResolveInternalArmy(bindings.armies,
                                            output.native_carmy_id);
  if (army == nullptr || Load<std::int32_t>(army, 0x124) != army_id ||
      output.owner_character_id != paused_scope.played_character_id) {
    output.unavailable_reason = "native_carmy_or_owner_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  void *owner = ResolveCharacter(bindings.character_storage_slot,
                                output.owner_character_id);
  if (owner == nullptr || Load<void *>(owner, 0x1D0) != nullptr) {
    output.unavailable_reason = "army_owner_character_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  output.current_commander_character_id = Load<std::int32_t>(army, 0x120);
  if (output.current_commander_character_id == -1) {
    output.current_commander_status = "absent";
    output.current_commander_unavailable_reason = {};
  } else {
    void *current = ResolveCharacter(bindings.character_storage_slot,
                                     output.current_commander_character_id);
    if (current != nullptr && bindings.get_army_commander(army) == current) {
      output.current_commander_status = "available";
      output.current_commander_unavailable_reason = {};
    } else {
      output.current_commander_unavailable_reason =
          "current_commander_identity_unavailable";
    }
  }

  OwnedCandidateVector native;
  native.value.allocator = bindings.vector_allocator;
  native.release = VectorRelease(native.value.allocator);
  if (native.release == nullptr) {
    output.unavailable_reason = "native_vector_allocator_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  // Match the actual player's GUI list semantics without instantiating a GUI.
  bindings.collect_candidates(owner, &native.value, false, true);
  if (native.value.allocator != bindings.vector_allocator ||
      native.value.capacity < 0 || native.value.count < 0 ||
      native.value.count > native.value.capacity ||
      native.value.capacity > kMaximumStorageCapacity ||
      (native.value.count > 0 && native.value.data == nullptr)) {
    output.unavailable_reason = "native_candidate_vector_unavailable";
    return CommanderCandidatesReadResult::unavailable;
  }
  output.candidate_collection_complete = true;
  output.candidate_source_count = native.value.count;
  output.candidates.reserve(static_cast<std::size_t>(native.value.count));
  bool partial = output.current_commander_status == "unavailable";
  for (std::int32_t index = 0; index < native.value.count; ++index) {
    CommanderCandidateSnapshot row{};
    void *candidate = native.value.data[index];
    if (candidate == nullptr) {
      row.unavailable_reason = "candidate_pointer_unavailable";
    } else {
      row.character_id = Load<std::int32_t>(candidate, 0x18);
      if (ResolveCharacter(bindings.character_storage_slot, row.character_id) !=
              candidate || Load<void *>(candidate, 0x1D0) != nullptr) {
        row.unavailable_reason = "candidate_identity_unavailable";
      } else {
        // Mode 1 is the formal player/manual eligibility predicate. Mode 2
        // requires an AI controller and would falsely reject Robert's army.
        row.can_assign = bindings.can_set_commander(1, candidate, army, nullptr);
        row.final_eligibility_observable = true;
        row.native_ai_base_quality =
            bindings.get_native_ai_base_quality(candidate);
        row.generic_advantage_points =
            bindings.get_generic_advantage(candidate, -1, false);
        row.quality_observable = true;
        row.available = true;
        row.unavailable_reason = {};
        if (ResolveCharacter(bindings.character_storage_slot, row.character_id) !=
                candidate || Load<void *>(candidate, 0x1D0) != nullptr) {
          row.available = false;
          row.final_eligibility_observable = false;
          row.quality_observable = false;
          row.unavailable_reason = "candidate_generation_changed";
        }
      }
    }
    partial = partial || !row.available;
    output.candidates.push_back(row);
  }
  if (!ArmyIdentityUnchanged(bindings, unit, army, output) ||
      ResolveCharacter(bindings.character_storage_slot,
                       output.owner_character_id) != owner) {
    output.unavailable_reason = "army_identity_changed";
    return CommanderCandidatesReadResult::unavailable;
  }
  output.unavailable_reason = {};
  return partial ? CommanderCandidatesReadResult::partial
                 : CommanderCandidatesReadResult::available;
}

} // namespace xar::ck3_12003
