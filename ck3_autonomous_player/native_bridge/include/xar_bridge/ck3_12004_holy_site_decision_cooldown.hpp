#pragma once
#include "xar_bridge/ck3_12004_holy_site_adoption_detail.hpp"
#include "xar_bridge/ck3_12003_mystical_communion_decision_terms.hpp"

namespace xar::ck3_12004::religion::holy_site {
inline constexpr std::string_view kDecisionCooldownQueryStep="query-player-holy-site-decision-cooldown-v1";
struct DecisionCooldownBindings {
  bool enabled=false;
  std::uintptr_t image_base=0;
  AdoptionDetailBindings native{};
  void **decision_database=nullptr;
  const void **decision_fallback=nullptr;
  ck3_12003::religion::mystical_communion::DecisionHash decision_hash=nullptr;
  ck3_12003::religion::mystical_communion::DecisionLookup decision_lookup=nullptr;
};
struct DecisionCooldownSnapshot {
  bool available=false;
  DecisionAction action=DecisionAction::adopt;
  std::uint64_t capture_epoch=0;
  std::int32_t date_raw=0,played_character_id=-1;
  DecisionCooldownObservation cooldown{};
  std::string unavailable_reason;
};
DecisionCooldownBindings BindHolySiteDecisionCooldownImage12004(std::uintptr_t,std::string_view) noexcept;
bool ReadHolySiteDecisionCooldown12004(const DecisionCooldownBindings &,
    const ck3_12002::religion::Context &,DecisionAction,DecisionCooldownSnapshot &) noexcept;
std::string SerializeHolySiteDecisionCooldown12004(const DecisionCooldownSnapshot &);
std::string SerializeHolySiteDecisionCooldownCommand12004(const DecisionCooldownSnapshot &,
    std::string_view request_id,std::uint64_t snapshot_revision,std::int64_t date_raw);
}
