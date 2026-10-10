#include "xar_bridge/conception_modifier_context_12004.hpp"
#include <bit>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kExactSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uintptr_t kDefaultGuard = 0x5D67B80;
constexpr std::uintptr_t kDefaultContext = 0x5D67B90;
template<class T> bool Read(const ConceptionModifierContextBindings12004 &b,
                           std::uintptr_t base, std::size_t offset, T &out) {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  return b.read_memory(b.read_context, base + offset, &out, sizeof(out));
}
bool Container(const ConceptionModifierContextBindings12004 &b,
               std::uintptr_t context, std::size_t offset,
               ConceptionModifierContainerStamp12004 &out) {
  return Read(b, context, offset, out.pointer) &&
      Read(b, context, offset + 8, out.capacity_raw) &&
      Read(b, context, offset + 12, out.count_raw) && out.pointer != 0 &&
      out.capacity_raw > 0 && out.count_raw >= 0 &&
      out.count_raw <= out.capacity_raw;
}
} // namespace

ConceptionModifierContextBindings12004 BindConceptionModifierContext12004(
    std::uintptr_t base, std::string_view version, std::string_view sha,
    ConceptionModifierContextRead12004 read, void *context) noexcept {
  ConceptionModifierContextBindings12004 result;
  if (base == 0 || version != "1.20.0.4" || sha != kExactSha || read == nullptr)
    return result;
  result.enabled = true;
  result.module_base = base;
  result.read_memory = read;
  result.read_context = context;
  return result;
}

namespace {
ConceptionModifierContextObservation12004 ResolveModifierContext(
    const ConceptionModifierContextBindings12004 &b,
    std::uintptr_t character, std::int32_t full_id,
    bool allow_source_qualified_fallback) {
  ConceptionModifierContextObservation12004 result;
  auto fail = [&](const char *reason) {
    result.reason = reason;
    return result;
  };
  result.module_base = b.module_base;
  result.character_address = character;
  result.full_character_id = full_id;
  if (!b.enabled || b.read_memory == nullptr || character == 0 ||
      (full_id == -1 && !allow_source_qualified_fallback))
    return fail("modifier_context_binding_or_character_unavailable");
  std::int32_t actual_id = -1;
  if (!Read(b, character, 0x18, actual_id) || actual_id != full_id)
    return fail("modifier_context_character_full_id_mismatch");
  if (!Read(b, character, 0x1B0, result.extension_address))
    return fail("modifier_context_extension_unavailable");
  if (result.extension_address != 0) {
    if (!Read(b, result.extension_address, 0x258, result.model_address))
      return fail("modifier_context_model_unavailable");
    if (result.model_address != 0) {
      std::uintptr_t owner = 0;
      if (!Read(b, result.model_address, 8, owner))
        return fail("modifier_context_model_owner_unavailable");
      if (owner == character) {
        if (result.model_address > std::numeric_limits<std::uintptr_t>::max() - 0x10)
          return fail("modifier_context_owned_address_unavailable");
        result.context_address = result.model_address + 0x10;
        result.source = ConceptionModifierContextSource12004::OwnedCharacter;
        result.ready = true;
        return result;
      }
    }
  }
  if (!Read(b, b.module_base, kDefaultGuard, result.default_guard))
    return fail("modifier_default_guard_unavailable");
  if (result.default_guard == 0 || result.default_guard == -1)
    return fail("modifier_default_not_initialized");
  if (b.module_base > std::numeric_limits<std::uintptr_t>::max() - kDefaultContext)
    return fail("modifier_default_address_unavailable");
  result.context_address = b.module_base + kDefaultContext;
  if (!Container(b, result.context_address, 0x68, result.keys_stamp) ||
      !Container(b, result.context_address, 0xD0, result.values_stamp))
    return fail("modifier_default_storage_unavailable");
  std::int32_t after = 0;
  if (!Read(b, b.module_base, kDefaultGuard, after) || after != result.default_guard)
    return fail("modifier_default_guard_changed");
  result.source = ConceptionModifierContextSource12004::InitializedDefault;
  result.ready = true;
  return result;
}

bool CompareModifierContext(
    const ConceptionModifierContextObservation12004 &observation,
    const ConceptionModifierContextObservation12004 &now,
    std::string &reason) {
  if (!now.ready) { reason = now.reason; return false; }
  if (now.source != observation.source ||
      now.context_address != observation.context_address ||
      now.extension_address != observation.extension_address ||
      now.model_address != observation.model_address ||
      (now.source == ConceptionModifierContextSource12004::InitializedDefault &&
       (now.default_guard != observation.default_guard ||
        !(now.keys_stamp == observation.keys_stamp) ||
        !(now.values_stamp == observation.values_stamp)))) {
    reason = "modifier_context_changed_during_read";
    return false;
  }
  return true;
}
} // namespace

ConceptionModifierContextObservation12004 ResolveConceptionModifierContext12004(
    const ConceptionModifierContextBindings12004 &b,
    std::uintptr_t character, std::int32_t full_id) {
  return ResolveModifierContext(b, character, full_id, false);
}

bool CheckConceptionModifierContextStillCurrent12004(
    const ConceptionModifierContextBindings12004 &b,
    const ConceptionModifierContextObservation12004 &observation,
    std::string &reason) {
  reason.clear();
  if (!observation.ready || observation.module_base != b.module_base) {
    reason = "modifier_context_observation_unavailable";
    return false;
  }
  return CompareModifierContext(observation, ResolveConceptionModifierContext12004(
      b, observation.character_address, observation.full_character_id), reason);
}

ConceptionModifierContextObservation12004 ResolveRawCharacterModifierContext12004(
    const ConceptionModifierContextBindings12004 &b,
    std::uintptr_t character, std::uint32_t physical_id,
    bool source_qualified_fallback) {
  if (physical_id == 0xFFFFFFFFu && !source_qualified_fallback) {
    ConceptionModifierContextObservation12004 result;
    result.module_base = b.module_base;
    result.character_address = character;
    result.full_character_id = std::bit_cast<std::int32_t>(physical_id);
    result.reason = "modifier_context_fallback_receiver_unqualified";
    return result;
  }
  return ResolveModifierContext(b, character,
      std::bit_cast<std::int32_t>(physical_id), source_qualified_fallback);
}

bool CheckRawCharacterModifierContextStillCurrent12004(
    const ConceptionModifierContextBindings12004 &b,
    const ConceptionModifierContextObservation12004 &observation,
    std::uint32_t physical_id, bool source_qualified_fallback,
    std::string &reason) {
  reason.clear();
  if (!observation.ready || observation.module_base != b.module_base ||
      std::bit_cast<std::uint32_t>(observation.full_character_id) != physical_id) {
    reason = "modifier_context_observation_unavailable";
    return false;
  }
  return CompareModifierContext(observation, ResolveRawCharacterModifierContext12004(
      b, observation.character_address, physical_id, source_qualified_fallback), reason);
}
} // namespace xar::ck3_12004
