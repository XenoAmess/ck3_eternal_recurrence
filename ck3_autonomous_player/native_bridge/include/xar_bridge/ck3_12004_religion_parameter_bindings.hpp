#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/religion_doctrine12002_numeric_final.hpp"
#include "xar_bridge/religion_doctrine12002_personal_parameters.hpp"

namespace xar::ck3_12004::religion {

using NumericSpecialBindings =
    ck3_12002::religion::doctrine12002::NumericSpecialBindings;
using NumericSpecialContext =
    ck3_12002::religion::doctrine12002::NumericSpecialContext;
using FaithNumericFinalBindings =
    ck3_12002::religion::doctrine12002::FaithNumericFinalBindings;
using FaithNumericFinalContext =
    ck3_12002::religion::doctrine12002::FaithNumericFinalContext;
using PersonalParameterBindings =
    ck3_12002::religion::doctrine12002::PersonalParameterBindings;
using PersonalParameterContext =
    ck3_12002::religion::doctrine12002::PersonalParameterContext;

NumericSpecialBindings BindNumericSpecialParametersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
FaithNumericFinalBindings BindFaithNumericFinalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
PersonalParameterBindings BindPersonalParametersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

bool ReadPlayedNumericSpecialParameters12004(const ContextBindings &,
    const NumericSpecialBindings &, std::uint64_t capture_epoch,
    NumericSpecialContext &) noexcept;
bool ReadPlayedFaithNumericFinal12004(const ContextBindings &,
    const NumericSpecialBindings &, const FaithNumericFinalBindings &,
    std::uint64_t capture_epoch, FaithNumericFinalContext &) noexcept;
bool ReadPlayedPersonalParameters12004(const ContextBindings &,
    const PersonalParameterBindings &, std::uint64_t capture_epoch,
    PersonalParameterContext &) noexcept;

// Fresh software DTO serialization also publishes the actual .4 native
// threshold getter provenance; old captured packets are never retagged.
std::string SerializeFaithNumericFinal12004(const FaithNumericFinalContext &);

} // namespace xar::ck3_12004::religion
