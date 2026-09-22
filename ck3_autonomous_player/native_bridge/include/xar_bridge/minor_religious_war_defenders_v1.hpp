#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {

// Exact CK3 1.19.0.6 no-UI counterpart of the declare-war preview's
// defender_faith_can_join collector. The native vector contains Character*
// rows; this reader generation-resolves every pointer before publishing an
// ID. Private and read-only; it does not describe voluntary allies or predict
// final war strength beyond the explicitly named current power leaves.
inline constexpr std::uintptr_t kMinorReligiousDefenderCollectorRvaV1 =
    0x2901960;
inline constexpr std::uintptr_t kMinorReligiousDefenderAllocatorRvaV1 =
    0x4FEB018;

struct NativeCharacterPointerVectorV1 {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};
static_assert(sizeof(NativeCharacterPointerVectorV1) == 0x18);

using MinorReligiousDefenderCollectorV1 = void (*)(
    void *actor, void *primary_defender, NativeCharacterPointerVectorV1 *out);
using MinorReligiousDefenderFreeV1 = void (*)(void *allocator, void *data,
                                              std::uint64_t element_size);
using MinorReligiousDefenderReadV1 = bool (*)(
    void *context, const void *address, void *output, std::size_t size) noexcept;

struct MinorReligiousDefenderEnvironmentV1 {
  std::uintptr_t module_base = 0;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void *allocator = nullptr;
  MinorReligiousDefenderCollectorV1 collector = nullptr;
  // Only the focused offline fixture may replace exact executable functions.
  MinorReligiousDefenderFreeV1 fixture_free = nullptr;
  bool offline_fixture_overrides = false;
};

struct MinorReligiousDefenderAccessV1 {
  void *context = nullptr;
  MinorReligiousDefenderReadV1 read_memory = nullptr;
  bool application_main_paused = false;
};

enum class MinorReligiousDefenderFailureV1 {
  none,
  boundary,
  environment,
  character,
  collector,
  vector,
  identity,
  power,
  cleanup,
};

struct MinorReligiousDefenderRowV1 {
  std::int32_t character_id = -1;
  std::int64_t base_power_raw = 0;
};

struct MinorReligiousDefenderReadbackV1 {
  MinorReligiousDefenderFailureV1 failure =
      MinorReligiousDefenderFailureV1::environment;
  std::int32_t actor_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int64_t actor_base_power_raw = 0;
  std::int64_t primary_defender_base_power_raw = 0;
  std::vector<MinorReligiousDefenderRowV1> prospective_joiners;
  std::int64_t prospective_joiner_base_power_raw = 0;
  std::int64_t primary_plus_joiner_base_power_raw = 0;
};

MinorReligiousDefenderEnvironmentV1 BindMinorReligiousDefenderEnvironmentV1(
    std::uintptr_t module_base) noexcept;
MinorReligiousDefenderReadbackV1 ReadMinorReligiousDefendersV1(
    const MinorReligiousDefenderEnvironmentV1 &environment,
    const MinorReligiousDefenderAccessV1 &access, std::int32_t actor_id,
    std::int32_t primary_defender_id) noexcept;

}  // namespace xar::ck3_11906
