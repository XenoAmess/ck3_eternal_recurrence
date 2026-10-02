#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

namespace xar::ck3_12002::religion::fulfillment_progress12003 {

inline constexpr std::uintptr_t kDatabaseSlotRva = 0x5D1F6D0;
inline constexpr std::uintptr_t kTypeForCharacterRva = 0x3181BF0;
inline constexpr std::uintptr_t kLevelForValueRva = 0x3181370;
inline constexpr std::uintptr_t kProgressWithinLevelRva = 0x1870020;
inline constexpr std::uintptr_t kMinimumSlotRva = 0x5C68E00;
inline constexpr std::uintptr_t kMaximumSlotRva = 0x5C68DF8;
inline constexpr std::size_t kTypeLevelRowsOffset = 0x58;
inline constexpr std::size_t kTypeLevelCountOffset = 0x64;
inline constexpr std::size_t kLevelStride = 0x218;
inline constexpr std::size_t kLevelLowerBoundOffset = 0x1E0;
inline constexpr std::size_t kLevelUpperBoundOffset = 0x1E8;
inline constexpr std::size_t kLevelIndexOffset = 0x210;

using TypeForCharacter = void *(*)(void *database, void *character);
using LevelForValue = void *(*)(void *type, std::int64_t current_raw);
using ProgressWithinLevel = std::int64_t *(*)(std::int64_t *out,
    std::int64_t current_raw, std::int64_t lower_raw, std::int64_t upper_raw);
struct Bindings {
  bool enabled = false;
  void **database_slot = nullptr;
  TypeForCharacter type_for_character = nullptr;
  LevelForValue level_for_value = nullptr;
  ProgressWithinLevel progress_within_level = nullptr;
  const std::int64_t *minimum = nullptr;
  const std::int64_t *maximum = nullptr;
};
enum class Failure {
  none, bindings_unavailable, current_context_unavailable,
  played_character_mismatch, database_unavailable, type_unavailable,
  levels_unavailable, level_unavailable, progress_unavailable,
};
struct Progress {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::int64_t> current_fulfillment_raw;
  std::optional<std::int32_t> active_level_index;
  std::optional<std::int32_t> level_count;
  std::optional<std::int64_t> level_lower_bound_raw;
  std::optional<std::int64_t> level_upper_bound_raw;
  std::optional<std::int64_t> progress_percent_raw;
  std::optional<bool> highest_level;
  std::optional<std::int64_t> runtime_minimum_raw;
  std::optional<std::int64_t> runtime_maximum_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};
Bindings BindSpiritualFulfillmentProgressImage12003(
    std::uintptr_t module_base, const game::AdapterDescriptor &) noexcept;
// Existing paused application-main owner only. The pointer is the actual played
// actor resolved by that owner; no public actor or GUI-window selector is added.
// The already-read current Context is reused, rather than sampling it again.
bool ReadPlayerSpiritualFulfillmentProgress12003(const Bindings &,
    void *actual_played_character, const religion::Context &current, Progress &) noexcept;
std::string SerializeSpiritualFulfillmentProgress12003(const Progress &);
const char *SpiritualFulfillmentProgressFailureName12003(Failure) noexcept;

} // namespace xar::ck3_12002::religion::fulfillment_progress12003
