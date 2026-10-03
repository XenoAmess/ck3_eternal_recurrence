#pragma once

#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"

namespace xar::ck3_12003::religion::confession {

inline constexpr std::string_view kDecisionId = "pam_decision_confession";
inline constexpr std::string_view kSchema = "ck3_12003_confession_decision_terms_v1";

// Reuse the v27 exact-build final-decision ABI and nullable output structure.
// This is a separate fixed decision reader; it never invokes the communion reader.
using Bindings = mystical_communion::Bindings;
using ResourceCost = mystical_communion::ResourceCost;
using Terms = mystical_communion::Terms;

Bindings BindPlayerConfessionDecisionTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool ReadPlayerConfessionDecisionTerms12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializePlayerConfessionDecisionTerms12003(const Terms &);

} // namespace xar::ck3_12003::religion::confession
