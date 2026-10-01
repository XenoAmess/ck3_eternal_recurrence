#pragma once

#include "xar_bridge/conversion_outcome12002_actor.hpp"
#include "xar_bridge/conversion_outcome12002_state.hpp"

namespace xar::ck3_12002::religion_conversion::outcome {
struct Bindings {
  actor::Bindings actor{};
  state::Bindings state{};
};
enum class Failure {
  none,
  invalid_target,
  actor_unavailable,
  state_unavailable,
  actor_and_state_unavailable,
  state_changed,
};
struct Context {
  bool available = false;
  Failure failure = Failure::actor_and_state_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  std::optional<bool> target_reached;
  actor::Context actor{};
  state::Context state{};
};
Bindings BindConversionOutcomeImage12002(std::uintptr_t module_base,
                                        std::string_view executable_sha256) noexcept;
// Reads actual current state. target_reached compares full Rite identities;
// it does not establish a conversion's causal origin or completion of effects.
bool ReadPlayedConversionOutcome12002(const Bindings &, std::uint32_t target_rite_id,
                                     std::uint64_t capture_epoch, Context &) noexcept;
const char *ConversionOutcomeFailureKey(Failure) noexcept;
std::string SerializeConversionOutcome12002(const Context &);
} // namespace xar::ck3_12002::religion_conversion::outcome
