#include "xar_bridge/conversion_outcome12002_query.hpp"

namespace xar::ck3_12002::religion_conversion::outcome {
Bindings BindConversionOutcomeImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  return {actor::BindConversionOutcomeActorImage12002(base, sha),
          state::BindConversionOutcomeStateImage12002(base, sha)};
}
bool ReadPlayedConversionOutcome12002(const Bindings &b, std::uint32_t target,
                                     std::uint64_t epoch, Context &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.target_rite_id = target;
  out.actor.capture_epoch = out.state.capture_epoch = epoch;
  out.actor.current_religion.capture_epoch = epoch;
  out.state.requested_target_rite_id = target;
  if (target == religion::kAbsentReference) { out.failure = Failure::invalid_target; return false; }
  (void)actor::ReadPlayedConversionOutcomeActor12002(b.actor, epoch, out.actor);
  (void)state::ReadPlayedConversionOutcomeState12002(b.state, target, epoch, out.state);
  if (out.actor.available) {
    out.date_raw = out.actor.date_raw;
    out.played_character_id = out.actor.played_character_id;
    if (out.actor.current_religion.rite_id)
      out.target_reached = *out.actor.current_religion.rite_id == target;
  } else if (out.state.available) {
    out.date_raw = out.state.date_raw;
    out.played_character_id = static_cast<std::int32_t>(out.state.played_character_id);
  }
  if (out.actor.available && out.state.available) {
    if (out.actor.date_raw != out.state.date_raw ||
        static_cast<std::uint32_t>(out.actor.played_character_id) != out.state.played_character_id ||
        out.state.requested_target_rite_id != target || out.state.target_rite_id != target ||
        out.actor.current_religion.spiritual_fulfillment_raw != out.state.spiritual_fulfillment_raw ||
        out.actor.capture_epoch != epoch || out.state.capture_epoch != epoch) {
      out.target_reached.reset(); out.failure = Failure::state_changed; return false;
    }
    out.available = true; out.failure = Failure::none; return true;
  }
  out.failure = out.actor.available ? Failure::state_unavailable :
      out.state.available ? Failure::actor_unavailable : Failure::actor_and_state_unavailable;
  return false;
}
const char *ConversionOutcomeFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::invalid_target: return "invalid_target";
  case Failure::actor_unavailable: return "actor_unavailable";
  case Failure::state_unavailable: return "state_unavailable";
  case Failure::actor_and_state_unavailable: return "actor_and_state_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "actor_and_state_unavailable";
}
std::string SerializeConversionOutcome12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_conversion_outcome_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\",\"read_only\":true,"
      "\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? std::string("null") :
          std::string("\"") + ConversionOutcomeFailureKey(c.failure) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"target_rite_id\":" + std::to_string(c.target_rite_id) +
      ",\"target_reached\":" + (c.target_reached ? (*c.target_reached ? "true" : "false") : "null") +
      ",\"target_reached_is_identity_only\":true,\"conversion_causality_inferred\":false,"
      "\"actor\":" + actor::SerializeConversionOutcomeActor12002(c.actor) +
      ",\"state\":" + state::SerializePlayedConversionOutcomeState12002(c.state) + "}";
}
} // namespace xar::ck3_12002::religion_conversion::outcome
