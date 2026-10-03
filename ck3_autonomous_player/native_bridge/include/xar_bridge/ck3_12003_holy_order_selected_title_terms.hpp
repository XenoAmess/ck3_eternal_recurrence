#pragma once

#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"
#include "xar_bridge/ck3_12003_holy_order_selected_parameters.hpp"
#include "xar_bridge/ck3_12003_holy_order_selected_candidates.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::holy_order::selected_title_terms {

inline constexpr std::string_view kSchema =
    "ck3_12003_holy_order_selected_title_terms_v1";
inline constexpr std::int64_t kRawScale = 100000;
inline constexpr std::array<std::string_view, 3> kDecisionIds{
    "create_holy_order_decision", "cancel_holy_order_lease_decision",
    "create_holy_order_monastic_decision"};

struct Bindings {
  bool enabled = false;
  mystical_communion::Bindings decision{};
  selected_parameters::Bindings parameters{};
  selected_candidates::Bindings candidates{};
};

struct TitleTerms {
  std::uint32_t title_id = UINT32_MAX;
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<bool> title_valid, can_take, can_afford;
  std::optional<std::array<std::int64_t, 10>> resource_costs_raw;
  bool can_take_reasons_available = false;
  std::optional<std::string> can_take_reason_literal;
  bool can_afford_reasons_available = false;
  std::optional<std::string> can_afford_reason_literal;
};
struct DecisionTerms {
  std::string decision_id;
  std::string selected_scope_name;
  std::int32_t selected_title_tier = -1;
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<bool> is_shown;
  bool candidates_available = false;
  std::vector<TitleTerms> candidates;
};
struct Context {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::vector<DecisionTerms> decisions;
};

Bindings BindHolyOrderSelectedTitleTermsImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
bool ReadHolyOrderSelectedTitleTerms12003(const Bindings &, void *actual_player,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializeHolyOrderSelectedTitleTerms12003(const Context &);

} // namespace xar::ck3_12003::religion::holy_order::selected_title_terms
