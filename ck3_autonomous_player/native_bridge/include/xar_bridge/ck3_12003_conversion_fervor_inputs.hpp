#pragma once

#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12002::religion::conversion_fervor {

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  actor_rite_unavailable,
  actor_faith_unavailable,
  target_rite_unavailable,
  target_faith_unavailable,
  actor_fervor_unavailable,
  target_fervor_unavailable,
  state_changed,
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = kAbsentReference;
  std::uint32_t requested_target_rite_id = kAbsentReference;
  std::optional<std::uint32_t> actor_faith_id;
  std::optional<std::uint32_t> target_faith_id;
  std::optional<std::int64_t> actor_fervor_raw;
  std::optional<std::int64_t> target_fervor_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

// The reviewed .3 mailbox supplies its existing bindings and owning paused
// callback. The target is its existing complete-generation Rite reference;
// this reader adds neither an actor selector nor an independent endpoint.
bool ReadPlayedConversionFervorInputs12003(
    const conversion_gates::Bindings &, std::uint32_t target_rite_id,
    std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializeConversionFervorInputs12003(const Context &);
const char *ConversionFervorInputsFailureKey(Failure) noexcept;

} // namespace xar::ck3_12002::religion::conversion_fervor
