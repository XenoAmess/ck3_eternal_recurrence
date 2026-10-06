#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/religion_reform12002_costs.hpp"
#include "xar_bridge/religion_reform12002_eligibility.hpp"

namespace xar::ck3_12004::religion {

// Actual .4 complete entry spans and their consumed member/RIP operands are
// recorded in adopted-restoration-1262/native-costs/SOURCE-READY.json.
// These factories reuse the published software DTOs and paused-window readers.
ck3_12002::religion_reform::CostBindings BindRiteCreationCostsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12002::religion_reform::EligibilityBindings BindEligibilityImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004::religion
