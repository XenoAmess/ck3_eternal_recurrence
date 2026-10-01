#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/player_epidemic_treatment_presence_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::size_t kTreatmentCharacterExtensionOffset12002 = 0x1B0;
inline constexpr std::size_t kTreatmentModifierRowsOffset12002 = 0x188;
inline constexpr std::size_t kTreatmentModifierCountOffset12002 = 0x194;
inline constexpr std::size_t kTreatmentModifierRowStride12002 = 0x48;
inline constexpr std::size_t kTreatmentModifierRowDefinitionOffset12002 = 0x00;
inline constexpr std::uintptr_t kTreatmentModifierDatabaseRva12002 = 0x8FD4E0;
inline constexpr std::uintptr_t kTreatmentStableKeyHashRva12002 = 0x3F7E240;
inline constexpr std::uintptr_t kTreatmentModifierLookupRva12002 = 0xAB8D20;
inline constexpr std::uintptr_t kTreatmentModifierFallbackSlotRva12002 = 0x5D1E0B0;
inline constexpr std::size_t kTreatmentModifierDefinitionKeyOffset12002 = 0x18;

using TreatmentModifierDatabaseGetter12002 = void *(*)();
using TreatmentModifierKeyHash12002 = std::uint32_t (*)(void *, const char *, std::uint32_t);
using TreatmentModifierLookup12002 = void *(*)(void *, std::int32_t);

struct TreatmentPresenceBindings12002 {
  bool enabled = false;
  CoreBindings core{};
  TreatmentModifierDatabaseGetter12002 get_modifier_database = nullptr;
  TreatmentModifierKeyHash12002 hash_stable_key = nullptr;
  TreatmentModifierLookup12002 lookup_modifier = nullptr;
  void **fallback_definition_slot = nullptr;
};

// Only calculates addresses from the frozen image identity; no process lookup.
TreatmentPresenceBindings12002 BindTreatmentPresenceImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Uses actual current-process reads. Null extension and zero count are known
// empty sets; failed definition/row reads remain unavailable.
bool ScanTreatmentModifierRows12002(const void *extension, const void *definition,
                                   bool &present) noexcept;

// Run under the existing paused application-main owner. The subject must be
// the currently played character resolved from CoreBindings. DTO/selector/key
// and remaining_days semantics remain the established v1 wire contract.
ck3_11906::PlayerEpidemicTreatmentPresenceV1 ReadPlayerEpidemicTreatmentPresence12002(
    const TreatmentPresenceBindings12002 &bindings,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::int32_t played_character_id) noexcept;

} // namespace xar::ck3_12002
