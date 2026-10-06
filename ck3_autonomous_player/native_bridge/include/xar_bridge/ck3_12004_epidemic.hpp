#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_epidemic_recovery.hpp"
#include "xar_bridge/ck3_12002_epidemic_treatment_presence.hpp"

namespace xar::ck3_12004 {

// These are caller-owned bindings/DTOs. The .4 builders never invoke either
// historical image binder and never substitute the .2 executable identity.
using EpidemicRecoveryBindings = ck3_12002::epidemic_recovery::Bindings;
using EpidemicTreatmentBindings = ck3_12002::TreatmentPresenceBindings12002;

struct EpidemicAbiProfile {
  bool actual4_operands_verified = false;
  std::uintptr_t title_store = 0;
  std::uintptr_t modifier_database = 0;
  std::uintptr_t stable_key_hash = 0;
  std::uintptr_t modifier_lookup = 0;
  std::uintptr_t modifier_fallback = 0;
  std::uintptr_t county_modifier_getter = 0;
  std::uintptr_t variable_context = 0;
  std::uintptr_t variable_identifier_table = 0;
  std::uintptr_t variable_identifier_lookup = 0;
  std::uintptr_t variable_identifier_name = 0;
};

// Sole mapper's actual .4 function/global/field receipt supplies this profile.
// A pending map leaves only this domain unavailable; it is not an old-hash alias.
const EpidemicAbiProfile &EpidemicProfile() noexcept;
EpidemicRecoveryBindings BindEpidemicRecoveryImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
EpidemicTreatmentBindings BindEpidemicTreatmentImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
