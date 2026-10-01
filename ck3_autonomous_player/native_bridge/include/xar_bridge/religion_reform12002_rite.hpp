#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform::rite {

inline constexpr std::uintptr_t kRiteIsMainRva = 0x24F7E40;
inline constexpr std::uintptr_t kRiteDivergenceToMainRva = 0x2BDFBA0;
inline constexpr std::uintptr_t kFaithHeresyThresholdRva = 0x2440920;
inline constexpr std::size_t kRiteFounderCharacterIdOffset = 0x4BC;
inline constexpr std::size_t kRiteHeadCharacterIdOffset = 0x4C0;

using IsMainGetter = bool (*)(void *);
// Native ABI: output first, current Rite second, optional tooltip third.
// Passing a null tooltip reads the actual current divergence to the main Rite.
using DivergenceGetter = std::int64_t *(*)(std::int64_t *, void *, void *);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  religion::ObjectGetter character_rite = nullptr;
  religion::ObjectGetter rite_faith = nullptr;
  religion::ObjectGetter faith_main_rite = nullptr;
  IsMainGetter rite_is_main = nullptr;
  DivergenceGetter divergence_to_main = nullptr;
  religion::FixedPointGetter faith_heresy_threshold = nullptr;
};

enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  rite_unavailable, faith_unavailable, main_rite_unavailable,
  divergence_unavailable, threshold_unavailable, state_changed,
};

struct Model {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id, faith_id, faith_main_rite_id;
  // These are full opaque Character refs; they do not imply alive or playable.
  std::optional<std::uint32_t> founder_character_id, head_character_id;
  std::optional<bool> current_is_main;
  std::optional<std::int64_t> divergence_to_main_raw, faith_heresy_threshold_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindRiteModelImage12002(std::uintptr_t module_base,
                               std::string_view executable_sha256) noexcept;
// Existing paused application-main owner only. Reads present model values;
// does not create/edit a Rite, construct a command draft or predict a split.
bool ReadPlayedRiteModel12002(const Bindings &, std::uint64_t capture_epoch,
                             Model &output) noexcept;
std::string SerializePlayedRiteModel12002(const Model &);
const char *RiteModelFailureKey(Failure) noexcept;

} // namespace xar::ck3_12002::religion_reform::rite
