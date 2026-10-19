#pragma once

#include "xar_bridge/ck3_12004_prisoner_named.hpp"
#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::religion::loan_principal {

inline constexpr std::string_view kValueKey = "holy_order_gold_value";

struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
  // Reused software signatures, populated only by the exact .4 factory.
  ck3_12003::religion::mystical_communion::Bindings root{};
  PrisonerNamedBindings12004 named{};
};

struct Observation {
  bool available = false;
  std::string_view unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::int64_t> prospective_principal_raw;
  bool owned_temporaries_released = false;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindHolyOrderLoanPrincipalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Candidate source, not linked/registered or qualified by native execution.
// Future application-main owner supplies its capture epoch. The reader resolves
// the actual paused player and constructs one fresh root; it accepts no borrowed
// interaction scope, actor override, lender, decision or event-option parameter.
// A quote is prospective only and never constitutes eligibility or funded cash.
bool ReadPlayerHolyOrderLoanPrincipal12004(
    const Bindings &, std::uint64_t capture_epoch, Observation &) noexcept;

} // namespace xar::ck3_12004::religion::loan_principal
