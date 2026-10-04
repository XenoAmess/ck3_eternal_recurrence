#pragma once
#include "xar_bridge/ingame_decision_item_v1.hpp"
#include "xar_bridge/aub_policy_options_mailbox_v1.hpp"
#include "xar_bridge/ck3_12003_repentance_recovery_inputs.hpp"
#include <array>
#include <optional>

namespace xar::ck3_12003 {
inline constexpr std::string_view kAubBusinessStateQueryV1Step="query-aub-business-state-v1";
inline constexpr std::string_view kAubBusinessStateQueryV1Capability="game.command.query-aub-business-state-v1";
inline constexpr std::string_view kAubConfirmV1Step="confirm-aub-policy-v1";
inline constexpr std::string_view kAubConfirmV1Capability="game.command.confirm-aub-policy-v1";
inline constexpr std::array<std::string_view,4> kAubBusinessFlagKeysV1{
  "enable_auto_build","aub_funding_treasury_only","aub_funding_personal_only","aub_pause_when_over_domain_limit"};
inline constexpr std::array<std::string_view,6> kAubPolicyValueKeysV1{
  "aub_policy_treasury_only_pause_choice","aub_policy_treasury_only_continue_choice",
  "aub_policy_personal_only_pause_choice","aub_policy_personal_only_continue_choice",
  "aub_policy_treasury_first_pause_choice","aub_policy_treasury_first_continue_choice"};
struct AubBusinessFlagV1 {
  std::string key;
  bool available=false,atom_registered=false;
  std::optional<bool> present;
  std::string unavailable_reason;
  bool operator==(const AubBusinessFlagV1 &) const=default;
};
struct AubBusinessStateResultV1 {
  std::uint64_t native_revision=0,connection_generation=0;
  std::uint32_t game_pid=0;
  std::int32_t played_character_id=-1,date_raw=0;
  bool available=false,owner_thread_verified=false,frame_verified=false;
  bool source_abi_pins_verified=false,gui_owner_binding_verified=false,stable_two_pass_verified=false;
  bool detail_census_verified=false,detail_root_available=false,detail_tree_complete=false,detail_effectively_visible=false;
  std::array<AubBusinessFlagV1,4> flags{};
  std::string unavailable_reason;
};
struct AubFlagReadBindingsV1 {
  religion::repentance_recovery_inputs::ExistingAtomLookup existing_atom=nullptr;
  religion::repentance_recovery_inputs::ObjectGetter flag_collection=nullptr;
  void *atom_pool=nullptr;
};
// Fixed keys only. Offline function overrides require the explicit fixture environment.
bool ReadAubBusinessFlagsV1(const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &,
    const ck3_11906::ZhongguoScoreboardAccessV1 &,const AubFlagReadBindingsV1 &,
    void *actual_actor,std::int32_t expected_full_actor_id,std::array<AubBusinessFlagV1,4> &) noexcept;
struct AubBusinessStateContextV1 {
  ck3_11906::IngameDecisionItemContextV1 observation{};
  AubBusinessStateResultV1 result{};
};
bool ExecuteAubBusinessStateQueryV1(AubBusinessStateContextV1 &,
    ck3_11906::MainThreadQueryMailboxV1 &,const ck3_11906::MainThreadExecutionStampV1 &,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &) noexcept;
std::string SerializeAubBusinessStateV1(const AubBusinessStateResultV1 &);
bool AubFlagsMatchSelectedPolicyV1(std::string_view,const AubBusinessStateResultV1 &) noexcept;
struct AubConfirmResultV1 {
  ck3_11906::IngameDecisionItemResultV1 keyed_before{};
  AubPolicyOptionsObservationV1 policy_before{};
  AubBusinessStateResultV1 state_before{},state_after{};
  bool receiver_qualified=false,dispatch_attempted=false,dispatch_invoked=false,native_handled=false;
  bool selected_policy_revalidated=false,postcondition_verified=false;
  std::string selected_key,target_child_path,unavailable_reason;
};
struct AubConfirmContextV1 {
  ck3_11906::IngameDecisionItemContextV1 observation{};
  std::string expected_selected_key;
  AubConfirmResultV1 result{};
};
bool ExecuteAubConfirmV1(AubConfirmContextV1 &,ck3_11906::MainThreadQueryMailboxV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &,const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &,
    ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &) noexcept;
std::string SerializeAubConfirmV1(const AubConfirmResultV1 &);
} // namespace xar::ck3_12003
