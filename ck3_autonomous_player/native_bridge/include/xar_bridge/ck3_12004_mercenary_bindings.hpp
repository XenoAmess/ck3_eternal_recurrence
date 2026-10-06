#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_mercenary_candidates.hpp"
#include "xar_bridge/ck3_12003_mercenary_composition.hpp"
#include "xar_bridge/ck3_12003_mercenary_final_terms.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"
#include "xar_bridge/ck3_12003_mercenary_position.hpp"

namespace xar::ck3_12004::mercenary {

// Software DTO reuse is backed by the actual .4 member/ABI ledger. These
// binders admit only the frozen .4 SHA and never call an old image binder.
ck3_12003::mercenary::CandidateBindings BindMercenaryCandidatesImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12003::mercenary::FinalTermsBindings BindMercenaryFinalTermsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12003::mercenary::CompositionBindings BindMercenaryCompositionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12003::mercenary::HireActionBindings BindMercenaryHireActionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12003::MercenaryPositionBindingsV1 BindMercenaryPositionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004::mercenary
