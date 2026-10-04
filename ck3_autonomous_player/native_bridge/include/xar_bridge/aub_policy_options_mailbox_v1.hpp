#pragma once
#include "xar_bridge/aub_policy_options_v1.hpp"
#include "xar_bridge/ingame_decision_item_v1.hpp"
namespace xar::ck3_12003 {
inline constexpr std::string_view kAubPolicyQueryV1Step="query-aub-policy-options-v1";
inline constexpr std::string_view kAubPolicyQueryV1Capability="game.command.query-aub-policy-options-v1";
inline constexpr std::string_view kAubPolicySelectV1Step="select-aub-policy-option-v1";
inline constexpr std::string_view kAubPolicySelectV1Capability="game.command.select-aub-policy-option-v1";
enum class AubPolicyMailboxActionV1 { query, select };
struct AubPolicyMailboxContextV1 {
  ck3_11906::IngameDecisionItemContextV1 observation{};
  AubPolicyMailboxActionV1 action=AubPolicyMailboxActionV1::query;
  std::string expected_selected_key, desired_key;
  AubPolicyOptionsObservationV1 query_result{};
  AubPolicySelectionResultV1 select_result{};
  ck3_11906::IngameDecisionItemResultV1 keyed_owner_before{},keyed_owner_after{};
};
// To be registered as a fixed native transport operation only behind its new
// OFF-by-default build flag. Public inputs are semantic policy keys plus normal
// episode/revision stamps; no root/path/pointer/row index or callback is public.
// For select the Python caller must durably consume its request claim FIRST.
bool ExecuteAubPolicyOptionsMailboxV1(AubPolicyMailboxContextV1 &,
    ck3_11906::MainThreadQueryMailboxV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &) noexcept;
std::string SerializeAubPolicyMailboxV1(const AubPolicyMailboxContextV1 &);
} // namespace xar::ck3_12003
