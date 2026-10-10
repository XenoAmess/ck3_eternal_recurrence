#include "xar_bridge/army_position_selected_actor_12004.hpp"

#include "xar_bridge/army_position_2c09280_12004.hpp"
#include "xar_bridge/army_position_relation_28bc250_12004.hpp"
#include "xar_bridge/army_position_same_war_side_12004.hpp"
#include "xar_bridge/ck3_12004_person_first_title_vector.hpp"

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kCharacterRegistrySlot = 0x5C67568;
constexpr std::uintptr_t kCharacterFallbackSlot = 0x5C67570;

template <typename T>
std::optional<T> Read(const ArmyRegularCoreReadonlyAccess12004 &a,
                      std::uintptr_t address) noexcept {
  T value{};
  if (!a.read || !a.read(a.read_context, address, &value, sizeof(value)))
    return std::nullopt;
  return value;
}

struct ReceiverShim {
  const ArmyRegularCoreReadonlyAccess12004 *access;
};

bool ReadReceiverMemory(void *context, const void *address, void *output,
                        std::size_t size) noexcept {
  const auto &a = *static_cast<ReceiverShim *>(context)->access;
  return a.read && a.read(a.read_context,
      reinterpret_cast<std::uintptr_t>(address), output, size);
}

std::optional<std::uintptr_t> ReadFallback(
    const ArmyRegularCoreReadonlyAccess12004 &a,
    std::string &reason) noexcept {
  const auto result = Read<std::uintptr_t>(a, a.image_base + kCharacterFallbackSlot);
  if (!result) reason = "selected_actor_character_fallback_unread";
  return result;
}

std::optional<std::uintptr_t> ReadNext(
    const ArmyRegularCoreReadonlyAccess12004 &a, std::uintptr_t current,
    std::string &reason) noexcept {
  if (!current) { reason = "selected_actor_path_character_null"; return std::nullopt; }
  // Actual2C0FEF0/FEFA load both before the context branch.
  const auto context = Read<std::uintptr_t>(a, current + 0x1C0);
  const auto link = Read<std::uintptr_t>(a, current + 0x1B8);
  if (!context || !link) {
    reason = "selected_actor_path_context_or_link_unread"; return std::nullopt;
  }
  if (*context) {
    const auto context_link = Read<std::uintptr_t>(a, *context + 0x1C0);
    if (!context_link || !*context_link) {
      reason = "selected_actor_path_context_link_unavailable"; return std::nullopt;
    }
    const auto candidate = Read<std::uintptr_t>(a, *context_link + 0x28);
    if (!candidate || !*candidate) {
      reason = "selected_actor_path_context_candidate_unavailable"; return std::nullopt;
    }
    const auto magic = Read<std::uint32_t>(a, *candidate + 0x1C);
    if (!magic) { reason = "selected_actor_path_candidate_magic_unread"; return std::nullopt; }
    // Actual2C0FF18/FF1E retain RBX=current on native rejection.
    if (*magic != 0x43686172U) return current;
    const auto full = Read<std::uint32_t>(a, *candidate + 0x18);
    if (!full) { reason = "selected_actor_path_candidate_id_unread"; return std::nullopt; }
    return *full != 0xFFFFFFFFU ? *candidate : current;
  }
  if (!*link) return ReadFallback(a, reason);
  const auto registry = Read<std::uintptr_t>(a, a.image_base + kCharacterRegistrySlot);
  if (!registry) { reason = "selected_actor_character_registry_unread"; return std::nullopt; }
  if (!*registry) return ReadFallback(a, reason);
  const auto full = Read<std::uint32_t>(a, *link + 0xC8);
  const auto count = Read<std::uint32_t>(a, *registry + 0x2C);
  if (!full || !count) { reason = "selected_actor_path_registry_input_unread"; return std::nullopt; }
  const auto index = *full & 0xFFFFFFU;
  if (index >= *count) return ReadFallback(a, reason);
  const auto slots = Read<std::uintptr_t>(a, *registry + 0x20);
  if (!slots || !*slots) { reason = "selected_actor_character_slots_unavailable"; return std::nullopt; }
  const auto candidate = Read<std::uintptr_t>(a, *slots + static_cast<std::uintptr_t>(index) * 16 + 8);
  if (!candidate) { reason = "selected_actor_character_candidate_unread"; return std::nullopt; }
  if (!*candidate) return ReadFallback(a, reason);
  const auto candidate_full = Read<std::uint32_t>(a, *candidate + 0x18);
  if (!candidate_full) { reason = "selected_actor_character_candidate_id_unread"; return std::nullopt; }
  return *candidate_full == *full ? candidate : ReadFallback(a, reason);
}
} // namespace

ArmyPositionSelectedActor12004 ReadArmyPositionSelectedActor2C0FEC012004(
    const ArmyRegularCoreReadonlyAccess12004 &a,
    std::uintptr_t original_actor, std::uintptr_t holder,
    std::uintptr_t optional_war_identity) noexcept {
  ArmyPositionSelectedActor12004 result;
  if (!a.image_base || !a.read || !original_actor || !holder) {
    result.unavailable_reason = "selected_actor_binding_or_pair_unavailable";
    return result;
  }
  ReceiverShim shim{&a};
  PersonCarrierDirect12004Bindings b;
  b.enabled = true;
  b.module_base = a.image_base;
  b.read_memory = ReadReceiverMemory;
  b.read_context = &shim;
  // Reuse the existing pure receiver leaf; no Model/Title/PC prerequisite.
  const auto initial = ReadPersonFirstTitleVectorReceiverForCharacter12004(b, original_actor);
  if (!initial.ready || !initial.selected_identity) {
    result.unavailable_reason = "selected_actor_initial_receiver_unavailable:" + initial.reason;
    return result;
  }
  auto current = *initial.selected_identity;
  if (current == original_actor) {
    result.selected_actor_identity = ReadFallback(a, result.unavailable_reason);
    return result;
  }
  while (result.path_occurrences < a.maximum_occurrences) {
    ++result.path_occurrences;
    const auto next = ReadNext(a, current, result.unavailable_reason);
    if (!next) return result;
    const auto holder_id = Read<std::uint32_t>(a, holder + 0x18);
    const auto current_id = current ? Read<std::uint32_t>(a, current + 0x18) : std::nullopt;
    if (!holder_id || !current_id) {
      result.unavailable_reason = "selected_actor_acceptance_full_id_unread";
      return result;
    }
    if (*holder_id == *current_id) {
      result.selected_actor_identity = current; return result;
    }
    const auto same_side = ReadArmyPosition2C090D012004(a, holder, current, optional_war_identity);
    if (!same_side.value) {
      result.unavailable_reason = "selected_actor_same_war_side_unavailable:" + same_side.unavailable_reason;
      return result;
    }
    if (*same_side.value) {
      result.selected_actor_identity = current; return result;
    }
    // Actual2C0FF88..FF95 reload both IDs after the same-side call. Equal
    // reloaded IDs skip the pair gate and continue the rejection path.
    const auto relation_current_id = Read<std::uint32_t>(a, current + 0x18);
    const auto relation_holder_id = Read<std::uint32_t>(a, holder + 0x18);
    if (!relation_current_id || !relation_holder_id) {
      result.unavailable_reason = "selected_actor_relation_full_id_reload_unread";
      return result;
    }
    if (*relation_current_id != *relation_holder_id) {
      const auto relation = ReadArmyPositionRelation28BC25012004(a, holder, current);
      if (!relation.war_id) {
        result.unavailable_reason = "selected_actor_relation_war_id_unavailable:" + relation.unavailable_reason;
        return result;
      }
      if (*relation.war_id != -1) {
        const auto war_gate = ReadArmyPositionWarGate12004(a, *relation.war_id, optional_war_identity);
        if (!war_gate.value) {
          result.unavailable_reason = "selected_actor_war_gate_unavailable:" + war_gate.unavailable_reason;
          return result;
        }
        if (*war_gate.value) { result.selected_actor_identity = current; return result; }
      }
    }
    if (*next == current) {
      result.selected_actor_identity = ReadFallback(a, result.unavailable_reason);
      return result;
    }
    current = *next;
  }
  result.unavailable_reason = "selected_actor_path_occurrence_budget_exhausted";
  return result;
}
} // namespace xar::ck3_12004
