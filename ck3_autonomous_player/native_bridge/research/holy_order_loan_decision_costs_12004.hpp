#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::religion::loan_decision_costs {

inline constexpr std::string_view kSchema =
    "ck3_12004_holy_order_loan_decision_costs_v1";
inline constexpr std::size_t kResourceSlotCount = 10;
using DecisionBindings =
    ck3_12003::religion::mystical_communion::Bindings;

struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
  // Software function-pointer types only. The .4 addon factory supplies every
  // pointer; this provider never calls a .3 image factory or changes admission.
  DecisionBindings decisions{};
};

struct DecisionCosts {
  std::string_view decision_id;
  std::optional<bool> is_shown, can_take, affordable;
  std::optional<std::array<std::int64_t, kResourceSlotCount>> costs_raw_by_native_index;
};

struct Observation {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  DecisionCosts borrow{"borrow_from_holy_order_decision"};
  DecisionCosts repay{"repay_loan_decision"};
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindHolyOrderLoanDecisionCostsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Research leaf, not registered or linked into the live application mailbox.
// A future owner must call this only on application-main with its capture epoch.
// It resolves the actual paused player internally and returns only copied data.
// Availability covers decision gates/costs, never principal, debt or funding.
bool ReadPlayerHolyOrderLoanDecisionCosts12004(
    const Bindings &, std::uint64_t capture_epoch, Observation &) noexcept;
std::string SerializeHolyOrderLoanDecisionCosts12004(const Observation &);

} // namespace xar::ck3_12004::religion::loan_decision_costs
