#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_pilgrimage_activity_type_terms.hpp"
#include "xar_bridge/ck3_12003_pilgrimage_candidate_factory.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::pilgrimage_activity_terms {

inline constexpr std::string_view kActivityId = "activity_pilgrimage";
inline constexpr std::string_view kSchema =
    "ck3_12003_player_pilgrimage_headless_activity_terms_v1";
inline constexpr std::string_view kQuoteScope =
    "activity_host_phase_and_selected_options";

using ConfigInitialize = void *(*)(void *, const void *, std::int32_t);
using SelectedSpecial = const void *(*)(const void *);
using PhaseInsert = void *(*)(void *, std::int32_t, const void *);
using ConfigNormalize = void (*)(void *);
using ActivityCost = void (*)(const void *, std::int64_t *);
using ActivityAffordable = bool (*)(const std::int64_t *, void *, void *);
using Destroy = void (*)(void *);

struct Bindings {
  bool enabled = false;
  pilgrimage::Bindings activity_type;
  pilgrimage_candidate_factory::Bindings candidates;
  ConfigInitialize config_initialize = nullptr;
  SelectedSpecial selected_special = nullptr;
  PhaseInsert phase_insert = nullptr;
  ConfigNormalize config_normalize = nullptr;
  ActivityCost activity_cost = nullptr;
  ActivityAffordable activity_affordable = nullptr;
  Destroy config_destroy = nullptr, reason_destroy = nullptr;
};

struct PredicateTerms {
  bool value = false, reasons_available = false;
  std::optional<std::string> reasons;
};
struct DefaultOptionTerms {
  // Definition+8 native indices, not fabricated keys or full object references.
  std::int32_t category_definition_index = -1, option_definition_index = -1;
  bool selected_special = false;
};
struct ConfiguredPhaseTerms {
  std::optional<std::int32_t> phase_definition_index;
  std::int32_t province_id = 0;
  std::optional<bool> native_default_phase;
  std::optional<std::int32_t> native_phase_order_raw;
};
struct ActivityQuoteTerms {
  std::int32_t native_config_date_raw = 0;
  std::array<std::int64_t, 10> activity_cost_raw_slots{};
  bool affordable = false, affordability_reasons_available = false;
  std::optional<std::string> affordability_reasons;
  std::vector<DefaultOptionTerms> default_options_used;
  std::vector<ConfiguredPhaseTerms> configured_phases;
};
struct PhaseTerms {
  std::int32_t phase_definition_index = -1, province_id = -1;
  std::int32_t native_ai_choice_score_raw = 0;
  PredicateTerms shown, location;
  bool can_select_phase = false;
  std::optional<ActivityQuoteTerms> activity_quote;
  std::optional<std::string> quote_unavailable_reason;
};
struct CandidateTerms {
  std::uint32_t holy_site_id = 0xFFFFFFFFU, title_id = 0xFFFFFFFFU;
  std::int32_t province_id = -1;
  PredicateTerms location_predicate;
  std::int32_t same_province_phase_count = 0;
  bool same_province_cap_applies = false;
  std::optional<std::int32_t> same_province_phase_cap;
  bool same_province_cap_allows = true, total_cap_applies = false;
  std::optional<bool> total_cap_allows, can_select;
  // Default-only pilgrimage has no ordinary phase offers. Quote its genuine
  // existing predefined row after assigning this candidate's native location.
  std::optional<ActivityQuoteTerms> default_activity_quote;
  std::optional<std::string> default_quote_unavailable_reason;
  std::vector<PhaseTerms> phase_choices;
};
struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::uint32_t> rite_id, faith_id;
  std::optional<std::int32_t> native_filter, configured_phase_count,
      total_phase_cap, resolved_location_phase_count, selected_special_definition_index;
  std::optional<bool> single_location;
  std::vector<DefaultOptionTerms> default_options;
  std::vector<ConfiguredPhaseTerms> initial_configured_phases;
  std::vector<CandidateTerms> candidates;
  static constexpr std::int64_t gold_treasury_scale = 100'000;
};

Bindings BindPlayerPilgrimageActivityTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Actual owner/frame only. The factory discovers native Faith holy sites; this
// API accepts no target Province, actor override, planner or action request.
// Costs cover the stated native temporary activity configuration. Travel
// service/options and full journey scheduling are separate capabilities.
bool ReadPlayerPilgrimageActivityTerms12003(const Bindings &,
    void *actual_played_character, const ck3_12002::religion::Context &current_context,
    Terms &) noexcept;
std::string SerializePlayerPilgrimageActivityTerms12003(const Terms &);

} // namespace xar::ck3_12003::religion::pilgrimage_activity_terms
