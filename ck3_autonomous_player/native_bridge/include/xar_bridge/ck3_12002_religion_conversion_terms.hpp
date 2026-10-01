#pragma once

#include "xar_bridge/ck3_12002_religion_conversion_cost.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

namespace xar::ck3_12002::religion_conversion::terms {

struct Bindings {
  religion_conversion_rite::Bindings rite;
  religion::conversion_cost::Bindings cost;
};

enum class Failure { none, final_gate_unavailable, cost_unavailable, state_changed };

struct Terms {
  bool available = false;
  Failure failure = Failure::final_gate_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  religion_conversion_rite::Preview final_gate;
  religion::conversion_cost::Cost cost;
  // Includes the native conversion entry's target != current identity check.
  // A sufficient balance alone never sets this result.
  std::optional<bool> can_convert;
};

Bindings BindReligionConversionTermsImage12002(std::uintptr_t module_base,
                                              std::string_view executable_sha256) noexcept;
// Existing paused owner only. No GUI, Submit/Execute or conversion action.
bool ReadPlayedReligionConversionTerms12002(const Bindings &, std::uint32_t target_rite_id,
                                          std::uint64_t capture_epoch, Terms &) noexcept;
const char *ReligionConversionTermsFailureKey(Failure) noexcept;
std::string SerializeReligionConversionTerms12002(const Terms &);

} // namespace xar::ck3_12002::religion_conversion::terms
