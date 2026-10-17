#pragma once
#include <cstdint>
#include <initializer_list>
#include <string_view>

namespace xar::ck3_12004::religion::holy_site {
// Public names are a finite capability contract, never arbitrary decision keys.
enum class DecisionAction : std::uint32_t { adopt=0,promote=1,demote=2,abandon=3 };
constexpr std::string_view DecisionActionName(DecisionAction action) noexcept {
 switch(action){case DecisionAction::adopt:return "adopt";case DecisionAction::promote:return "promote";
 case DecisionAction::demote:return "demote";case DecisionAction::abandon:return "abandon";}return {};
}
constexpr std::string_view DecisionKey(DecisionAction action) noexcept {
 switch(action){case DecisionAction::adopt:return "adopt_holy_site_decision";
 case DecisionAction::promote:return "elevate_holy_site_decision";
 case DecisionAction::demote:return "demote_holy_site_decision";
 case DecisionAction::abandon:return "abandon_holy_site_decision";}return {};
}
constexpr bool ParseDecisionAction(std::string_view value,DecisionAction &action) noexcept {
 for(const auto candidate:{DecisionAction::adopt,DecisionAction::promote,DecisionAction::demote,DecisionAction::abandon})
  if(value==DecisionActionName(candidate)){action=candidate;return true;}
 return false;
}
}
