#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {
using ConceptionModifierContextRead12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;
struct ConceptionModifierContextBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionModifierContextRead12004 read_memory = nullptr;
  void *read_context = nullptr;
};
enum class ConceptionModifierContextSource12004 {
  Unavailable, OwnedCharacter, InitializedDefault
};
struct ConceptionModifierContainerStamp12004 {
  std::uintptr_t pointer = 0;
  std::int32_t capacity_raw = 0;
  std::int32_t count_raw = 0;
  bool operator==(const ConceptionModifierContainerStamp12004 &) const = default;
};
struct ConceptionModifierContextObservation12004 {
  bool ready = false;
  std::string reason;
  ConceptionModifierContextSource12004 source =
      ConceptionModifierContextSource12004::Unavailable;
  std::uintptr_t module_base = 0;
  std::uintptr_t context_address = 0;
  std::uintptr_t character_address = 0;
  std::int32_t full_character_id = -1;
  std::uintptr_t extension_address = 0;
  std::uintptr_t model_address = 0;
  std::int32_t default_guard = 0;
  ConceptionModifierContainerStamp12004 keys_stamp;
  ConceptionModifierContainerStamp12004 values_stamp;
};
ConceptionModifierContextBindings12004 BindConceptionModifierContext12004(
    std::uintptr_t module_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionModifierContextRead12004 read_memory,
    void *read_context = nullptr) noexcept;

// Exact actual getter branch selection. Root supplies the current resolved
// Character/fullID from the owning application-thread query. No native call,
// TLS update, initialization or destruction occurs here.
ConceptionModifierContextObservation12004 ResolveConceptionModifierContext12004(
    const ConceptionModifierContextBindings12004 &bindings,
    std::uintptr_t character, std::int32_t full_character_id);

// Called after BF copy. A completed guard alone does not prove alive storage:
// the actual default destructor resets pointers/counts/capacities without
// clearing the guard. Default guard and both container stamps must be equal.
bool CheckConceptionModifierContextStillCurrent12004(
    const ConceptionModifierContextBindings12004 &bindings,
    const ConceptionModifierContextObservation12004 &observation,
    std::string &reason);

// Actual M4 callers may pass their source-selected default Character with
// physical ID FFFFFFFF. The caller owns that fallback route/pointer bookend.
// This raw entry does not read a CharacterDB slot or impose a tag/positive-ID
// gate. The +18 physical DWORD is copied solely to keep the receiver current.
// Existing signed M7 Resolve/Check above retain their -1 admission rule.
ConceptionModifierContextObservation12004 ResolveRawCharacterModifierContext12004(
    const ConceptionModifierContextBindings12004 &bindings,
    std::uintptr_t character, std::uint32_t physical_character_id,
    bool source_qualified_fallback);

bool CheckRawCharacterModifierContextStillCurrent12004(
    const ConceptionModifierContextBindings12004 &bindings,
    const ConceptionModifierContextObservation12004 &observation,
    std::uint32_t physical_character_id, bool source_qualified_fallback,
    std::string &reason);
} // namespace xar::ck3_12004
