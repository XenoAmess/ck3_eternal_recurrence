#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12002::religion::devotion_profile12003 {

inline constexpr std::uintptr_t kEffectiveLevelRva = 0x28BE0D0;
inline constexpr std::uintptr_t kProgressPercentRva = 0x2BB08B0;
inline constexpr std::uintptr_t kEffectiveCapRva = 0x2696670;
inline constexpr std::uintptr_t kThresholdProgressRva = 0x26979F0;
inline constexpr std::uintptr_t kThresholdVectorRva = 0x2696750;
inline constexpr std::size_t kCharacterIdOffset = 0x18;
inline constexpr std::size_t kCharacterValuesOffset = 0x1B0;
inline constexpr std::size_t kDevotionTotalOffset = 0x118;
inline constexpr std::size_t kThresholdDataOffset = 0;
inline constexpr std::size_t kThresholdCountOffset = 0x0C;
inline constexpr std::size_t kThresholdStride = sizeof(std::int64_t);

// Exact PlayerValueItem scope consumed by the native cap/threshold getters.
// Tag zero selects the actual Character's piety/devotion values.
struct PlayerValueItemScope {
  void *character = nullptr;
  std::uint8_t tag = 0;
  std::uint8_t reserved[7]{};
};
static_assert(offsetof(PlayerValueItemScope, character) == 0);
static_assert(offsetof(PlayerValueItemScope, tag) == 8);
static_assert(sizeof(PlayerValueItemScope) == 16);

using EffectiveLevel = std::int32_t (*)(void *character);
using ProgressPercent = std::int64_t *(*)(std::int64_t *out, void *character);
using EffectiveCap = std::int32_t (*)(PlayerValueItemScope *scope);
using ThresholdProgress = void (*)(PlayerValueItemScope *scope,
    std::int64_t *numerator_out, std::int64_t *denominator_out);
using ThresholdVector = const void *(*)(PlayerValueItemScope *scope);

struct Bindings {
  bool enabled = false;
  EffectiveLevel effective_level = nullptr;
  ProgressPercent progress_percent = nullptr;
  EffectiveCap effective_cap = nullptr;
  ThresholdProgress threshold_progress = nullptr;
  ThresholdVector threshold_vector = nullptr;
};

enum class Failure {
  none, bindings_unavailable, current_context_unavailable,
  played_character_mismatch, character_values_unavailable,
  thresholds_unavailable, progress_unavailable,
};

struct Profile {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::int64_t> current_devotion_total_raw;
  std::optional<std::int32_t> effective_level;
  std::optional<std::int32_t> effective_cap;
  std::optional<std::int64_t> progress_percent_raw;
  std::optional<std::int64_t> progress_numerator_raw;
  std::optional<std::int64_t> progress_denominator_raw;
  std::optional<std::int32_t> runtime_threshold_count;
  std::optional<std::int64_t> level_lower_threshold_raw;
  std::optional<std::int64_t> level_upper_threshold_raw;
  std::optional<bool> native_terminal_threshold_branch;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindPlayerDevotionProfileImage12003(
    std::uintptr_t module_base, const game::AdapterDescriptor &) noexcept;
// Application-main, paused owner only. Reuse its current Context's identity,
// date and epoch and its actual played actor; no selector or new query owner.
bool ReadPlayerDevotionProfile12003(const Bindings &,
    void *actual_played_character, const religion::Context &current, Profile &) noexcept;
std::string SerializePlayerDevotionProfile12003(const Profile &);
const char *PlayerDevotionProfileFailureName12003(Failure) noexcept;

} // namespace xar::ck3_12002::religion::devotion_profile12003
