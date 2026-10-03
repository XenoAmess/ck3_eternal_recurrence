#pragma once

#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"

#include <array>

namespace xar::ck3_12003::religion::repentance_petition {

inline constexpr std::string_view kHeadOfFaithDecisionId = "petition_head_of_faith_decision";
inline constexpr std::string_view kAntipopeDecisionId = "petition_antipope_decision";
inline constexpr std::string_view kSchema = "ck3_12003_repentance_petition_decision_terms_v1";

// These two fixed readers reuse the already-closed .3 final-decision ABI.
using Bindings = mystical_communion::Bindings;

struct DecisionTerms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::optional<bool> is_shown, can_take, affordable;
  std::optional<std::array<std::int64_t, 10>> costs_raw;
  bool reasons_available = false;
  std::optional<std::string> can_take_reasons;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  DecisionTerms head_of_faith, antipope;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindPlayerRepentancePetitionDecisionTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Actual current player only. Both native decisions use a newly constructed
// character root with no widget selection. These predicates observe the
// general petition decisions; they do not evaluate the named requires-petition
// trigger or the repentance widget item. An unselected cost is not a repentance
// quote, and successful CanTake is not permission to submit a selected petition.
bool ReadPlayerRepentancePetitionDecisionTerms12003(const Bindings &,
    void *actual_played_character, std::int32_t played_character_id,
    std::int32_t date_raw, std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializePlayerRepentancePetitionDecisionTerms12003(const Terms &);

} // namespace xar::ck3_12003::religion::repentance_petition
