#include "xar_bridge/ck3_12002_religion_conversion_terms.hpp"

namespace xar::ck3_12002::religion_conversion::terms {

Bindings BindReligionConversionTermsImage12002(std::uintptr_t base,
                                              std::string_view sha) noexcept {
  return {religion_conversion_rite::BindRiteConversionImage12002(base, sha),
          religion::conversion_cost::BindReligionConversionCostImage12002(base, sha)};
}

bool ReadPlayedReligionConversionTerms12002(const Bindings &b, std::uint32_t target,
                                          std::uint64_t epoch, Terms &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.target_rite_id = target;
  const bool gate_read = religion_conversion_rite::ReadRitePreview12002(
      b.rite, epoch, target, out.final_gate);
  out.date_raw = out.final_gate.date_raw;
  out.played_character_id = out.final_gate.played_character_id;
  if (!gate_read) return false;
  if (!religion::conversion_cost::ReadPlayedReligionConversionCost12002(
          b.cost, target, epoch, out.cost)) {
    out.failure = Failure::cost_unavailable;
    return false;
  }
  const auto &gate = out.final_gate;
  const auto &cost = out.cost;
  if (gate.played_character_id != cost.played_character_id || gate.date_raw != cost.date_raw ||
      gate.target_rite_id != cost.target_rite_id ||
      !cost.target_faith_id || gate.target_faith_id != *cost.target_faith_id ||
      !cost.same_faith || gate.same_faith != *cost.same_faith) {
    out.failure = Failure::state_changed;
    return false;
  }
  out.can_convert = gate.different_from_current_rite && gate.validator_with_payment;
  out.available = true; out.failure = Failure::none;
  return true;
}

const char *ReligionConversionTermsFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::final_gate_unavailable: return "final_gate_unavailable";
  case Failure::cost_unavailable: return "cost_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "final_gate_unavailable";
}

std::string SerializeReligionConversionTerms12002(const Terms &t) {
  return std::string{"{\"schema\":\"ck3_12002_religion_conversion_terms_v1\","}
      + "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" + kExecutableSha256
      + "\",\"read_only\":true,\"available\":" + (t.available ? "true" : "false")
      + ",\"unavailable_reason\":" + (t.available ? std::string{"null"}
          : std::string{"\""} + ReligionConversionTermsFailureKey(t.failure) + "\"")
      + ",\"capture_epoch\":" + std::to_string(t.capture_epoch)
      + ",\"date_raw\":" + std::to_string(t.date_raw)
      + ",\"played_character_id\":" + std::to_string(t.played_character_id)
      + ",\"target_rite_id\":" + std::to_string(t.target_rite_id)
      + ",\"can_convert\":" + (t.can_convert ? (*t.can_convert ? "true" : "false") : "null")
      + ",\"native_blocker_text_available\":false,\"final_gate\":"
      + religion_conversion_rite::SerializeRitePreview12002(t.final_gate)
      + ",\"cost\":" + religion::conversion_cost::SerializeReligionConversionCost12002(t.cost)
      + "}";
}

} // namespace xar::ck3_12002::religion_conversion::terms
