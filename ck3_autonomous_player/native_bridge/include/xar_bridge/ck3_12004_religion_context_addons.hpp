#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_hostility.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_terms.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_faith.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_reasons.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"
#include "xar_bridge/ck3_12003_conversion_fervor_inputs.hpp"
#include "xar_bridge/conversion_outcome12002_query.hpp"

namespace xar::ck3_12004::religion {

// Software DTOs/readers are reused only with independently proved .4 image
// pointers. Each existing addon retains its own availability and native result.
struct ContextAddonBindings {
  ck3_12002::religion::fulfillment_progress12003::Bindings progress_bindings{};
  ck3_12003::religion::mystical_communion::Bindings mystical_communion_bindings{};
  ck3_12003::religion::pilgrimage::Bindings pilgrimage_bindings{};
  ck3_12003::religion::pilgrimage_activity_terms::Bindings pilgrimage_activity_bindings{};
  ck3_12003::religion::pilgrimage_route::Bindings pilgrimage_route_bindings{};
  ck3_12003::religion::confession::Bindings confession_bindings{};
  ck3_12003::religion::confession_permission::Bindings confession_permission_bindings{};
  ck3_12003::religion::church_income::Bindings church_income_bindings{};
  ck3_12003::religion::church_tax_inputs::Bindings church_tax_bindings{};
  ck3_12002::religion::devotion_profile12003::Bindings devotion_bindings{};
  ck3_12002::religion::rite_virtue_sin_profile12003::Bindings rite_virtue_sin_bindings{};
  ck3_12003::religion::vow_of_poverty_terms12003::Bindings vow_of_poverty_bindings{};
};
using HostilityBindings = ck3_12002::religion::doctrine12002::HostilityBindings;
struct ConversionBindings {
  ck3_12002::religion_conversion_rite::Bindings rite{};
  ck3_12002::religion_conversion::faith::Bindings faith{};
  ck3_12002::religion::conversion_cost::Bindings cost{};
  ck3_12002::religion_conversion::terms::Bindings terms{};
  ck3_12002::religion_conversion::reasons::Bindings reasons{};
  ck3_12002::religion::conversion_gates::Bindings gates{};
  ck3_12002::religion_conversion_ai_inputs::Bindings prediction{};
  ck3_12002::religion_conversion::outcome::Bindings outcome{};
};

ContextAddonBindings BindReligionContextAddonsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
HostilityBindings BindHostilityImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ConversionBindings BindReligionConversionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12002::religion_conversion::outcome::Bindings BindConversionOutcomeImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Caller-owned readonly native value. This factory is never submitted and
// explicitly supplies the .4 constructor's primary and secondary vptrs.
ck3_12002::religion_conversion_rite::FaithAndRiteConversionCommand
MakeReadOnlyConvertRiteValue12004(std::uintptr_t image_base,
    std::int32_t actor_id, std::uint32_t target_rite_id, bool pay_piety) noexcept;

bool ReadPlayedHostilityTowardsRite12004(const HostilityBindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion::doctrine12002::HostilityObservation &) noexcept;
bool ReadPlayedReligionConversionTerms12004(
    const ck3_12002::religion_conversion::terms::Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion_conversion::terms::Terms &) noexcept;
bool ReadPlayedFaithConversionChoices12004(
    const ck3_12002::religion_conversion::faith::Bindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_conversion::faith::Choices &) noexcept;
bool ReadCurrentFaithRites12004(
    const ck3_12002::religion_conversion_rite::Bindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_conversion_rite::FaithRites &) noexcept;
bool ReadPlayedReligionConversionReasons12004(
    const ck3_12002::religion_conversion::reasons::Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion_conversion::reasons::Reasons &) noexcept;
bool ReadPlayedReligionConversionGates12004(
    const ck3_12002::religion::conversion_gates::Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion::conversion_gates::Context &) noexcept;
bool ReadExpectedRiteFulfillment12004(
    const ck3_12002::religion_conversion_ai_inputs::Bindings &,
    std::uint64_t capture_epoch, std::uint32_t target_rite_id,
    ck3_12002::religion_conversion_ai_inputs::FulfillmentInput &) noexcept;
bool ReadPlayedConversionFervorInputs12004(
    const ck3_12002::religion::conversion_gates::Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion::conversion_fervor::Context &) noexcept;
bool ReadPlayedConversionOutcome12004(
    const ck3_12002::religion_conversion::outcome::Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch,
    ck3_12002::religion_conversion::outcome::Context &) noexcept;

} // namespace xar::ck3_12004::religion
