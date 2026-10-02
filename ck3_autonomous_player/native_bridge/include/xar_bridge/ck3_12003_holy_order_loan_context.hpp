#pragma once

#include "xar_bridge/ck3_12002_phase_definitions.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::loan {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kQueryStep =
    "query-player-holy-order-loan-context-v1";
inline constexpr std::string_view kSchema = "ck3_12003_holy_order_loan_context_v1";
inline constexpr std::string_view kDomain = "player_holy_order_loan_context_v1";

using DecisionHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using DecisionLookup = const void *(*)(void *, std::uint32_t);
using RootConstruct = void *(*)(void *);
using RootDestroy = void (*)(void *);
using DecisionShown = bool (*)(const void *, void *);
using DecisionCanTake = bool (*)(const void *, void *, void *, const void *, void *);
using DecisionCost = const void *(*)(const void *);
using CostEvaluate = std::int64_t *(*)(const void *, void *, std::int64_t *);
using CostAffordable = bool (*)(const void *, void *, void *, void *);
using AmountEvaluate = bool (*)(std::uintptr_t, void *, std::int64_t &) noexcept;

struct Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::PhaseDefinitionBindings variable_identifiers{};
  void **character_store = nullptr;
  void **character_fallback = nullptr;
  void **decision_database = nullptr;
  const void **decision_fallback = nullptr;
  DecisionHash decision_hash = nullptr;
  DecisionLookup decision_lookup = nullptr;
  RootConstruct root_construct = nullptr;
  RootDestroy root_destroy = nullptr;
  DecisionShown decision_shown = nullptr;
  DecisionCanTake decision_can_take = nullptr;
  DecisionCost decision_cost = nullptr;
  CostEvaluate cost_evaluate = nullptr;
  CostAffordable cost_affordable = nullptr;
  AmountEvaluate amount_evaluate = nullptr;
};

struct ResourceCost {
  std::int64_t gold = 0, treasury = 0, prestige = 0, piety = 0;
};
struct Decision {
  std::string_view decision_id;
  bool is_shown = false, can_take = false, affordable = false;
  ResourceCost costs_raw{};
};
struct Context {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::int64_t> loan_amount_quote_raw;
  bool loan_amount_owed_present = false;
  std::optional<std::int64_t> loan_amount_owed_raw;
  bool loan_holder_present = false;
  std::optional<std::int32_t> loan_holder_character_id;
  bool loan_holder_resolved = false;
  bool borrower_years_present = false;
  std::optional<std::int64_t> borrower_years_raw;
  bool lender_years_present = false;
  std::optional<std::int64_t> lender_years_raw;
  Decision borrow_decision{"borrow_from_holy_order_decision"};
  Decision repay_decision{"repay_loan_decision"};
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindHolyOrderLoanImage12003(std::uintptr_t module_base,
                                    std::string_view executable_sha256) noexcept;

// The existing application-main mailbox supplies the resolved current player,
// paused date and capture epoch. Only copied observations leave this function.
// It contains no decision submission, event option or resource effect.
bool ReadHolyOrderLoanContext12003(const Bindings &bindings, void *played_character,
                                 std::int32_t played_character_id,
                                 std::int32_t date_raw, std::uint64_t capture_epoch,
                                 Context &output) noexcept;
std::string SerializeHolyOrderLoanContext12003(const Context &context);

} // namespace xar::ck3_12003::religion::loan
