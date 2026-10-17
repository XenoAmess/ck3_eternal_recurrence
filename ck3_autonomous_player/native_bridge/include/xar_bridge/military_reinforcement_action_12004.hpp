#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <optional>
#include <string>
#include <string_view>

#ifndef XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004
#define XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004 0
#endif

namespace xar::ck3_11906 {
inline constexpr std::string_view kMilitaryReinforcementEnable12004Step="enable-military-reinforcement-v1";
inline constexpr std::string_view kMilitaryReinforcementDisable12004Step="disable-military-reinforcement-v1";
inline constexpr std::string_view kMilitaryReinforcementEnable12004Capability="game.command.enable-military-reinforcement-v1";
inline constexpr std::string_view kMilitaryReinforcementDisable12004Capability="game.command.disable-military-reinforcement-v1";
inline constexpr std::string_view kMilitaryReinforcementSourceGuiSha12004="4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac";

struct MilitaryReinforcementSource12004 {
  std::string child_path;
  std::uint64_t vtable_rva=0;
  game::GuiRefillStaticOwnerSwitch12004V1 owner_switch;
};
// A private fixed source profile. The caller never supplies a widget/path or a
// type635 pointer. This selects the original clickable outer group, not its
// checkbox display child, and makes no native-selected-receiver claim.
inline bool SelectMilitaryReinforcementSource12004(
    const NamedGuiTreeInspectionV1 &tree,std::int32_t actor,
    MilitaryReinforcementSource12004 &out) {
  out={};
  if(actor<=0||tree.scope_root_name!="military_view"||!tree.root_available||tree.truncated||
      tree.widget_count!=tree.widgets.size()||!tree.standard_click_bindings_12004||
      !tree.callback_thunk_3aa30e0_pin_verified||!tree.expression_layout_3a9f960_pin_verified||
      !tree.receiver_candidate_source_pins_verified)return false;
  const NamedGuiWidgetInspectionV1 *found=nullptr;
  for(const auto &row:tree.widgets) {
    if(row.child_path!="0/0/0/2/3/0/0/0"&&row.child_path!="0/0/0/3/5/0/0/0")continue;
    if(!row.effective_visible||!row.enabled||!row.standard_click_binding_12004.button_base_slot13||
        row.standard_click_binding_12004.callbacks.size()!=1)continue;
    if(!row.runtime_name.empty())return false;
    const auto &cb=row.standard_click_binding_12004.callbacks.front();
    const auto &ex=cb.expression_3a9f960;
    if(!cb.indirect_target_3aa30e0||cb.callback_slot2_rva!=0x3AA30E0||
        cb.native_target_8_rva!=0x3A9F960||!cb.receiver_f0_present||!cb.expression_descriptor_3a9f960||
        ex.chain_count_24_raw!=0||ex.final_kind_34_raw!=3||ex.final_target_38_rva!=0x1303D40||
        !ex.final_user_data_40_present||ex.receiver_type_id_48!=635U||ex.receiver_flag_4c_raw!=0||
        !ex.receiver_entry_candidates_12004)continue;
    const bool regular=row.child_path=="0/0/0/2/3/0/0/0";
    const std::string_view tab_path=regular?"0/0/0/2":"0/0/0/3";
    const std::string_view footer_path=regular?"0/0/0/2/3":"0/0/0/3/5";
    const NamedGuiWidgetInspectionV1 *tab=nullptr,*footer=nullptr;
    for(const auto &parent:tree.widgets) {
      if(parent.child_path==tab_path){if(tab)return false;tab=&parent;}
      if(parent.child_path==footer_path){if(footer)return false;footer=&parent;}
    }
    if(!tab||!footer||footer->runtime_name!="footer"||
        tab->runtime_name!=(regular?"tab_your_armies":"imperial_armies_ra_uses_this"))return false;
    const auto &candidate=*ex.receiver_entry_candidates_12004;
    if(!candidate.definition_frontier_continuation_depth8_12)return false;
    const auto &continuation=*candidate.definition_frontier_continuation_depth8_12;
    if(continuation.status!="available"||!continuation.stable_double_read||
        !continuation.static_direct_owner_switch_12004)return false;
    const auto &value=*continuation.static_direct_owner_switch_12004;
    if(value.status!="available"||!value.stable_double_read||value.owner_full_id!=actor||
        !value.enabled.has_value()||!value.military_component_present.has_value())return false;
    if(*value.military_component_present) {
      if(!value.raw_byte_4a9||value.value_basis!="raw_military_byte"||
          *value.enabled!=(*value.raw_byte_4a9!=0))return false;
    } else if(value.raw_byte_4a9||*value.enabled||value.value_basis!="native_null_military_zero")return false;
    if(found)return false;
    found=&row;out={row.child_path,row.vtable_rva,value};
  }
  return found!=nullptr;
}

struct MilitaryReinforcementResult12004 {
  std::string game_version="1.20.0.4";
  std::string executable_sha256="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  std::uint64_t native_revision=0,connection_generation=0;
  std::uint32_t game_pid=0;
  std::int32_t played_character_id=-1,date_raw=0;
  bool accepted=false,desired_enabled=false,owner_thread_verified=false,frame_verified=false;
  bool source_abi_pins_verified=false,gui_owner_binding_verified=false;
  bool source_profile_verified=false,current_tree_complete=false,no_blocking_modal_verified=false;
  bool dispatch_attempted=false,dispatch_invoked=false,native_handled=false;
  bool native_after_tree_complete=false,before_after_same_source=false;
  std::string source_child_path,status="unavailable",unavailable_reason;
  game::GuiRefillStaticOwnerSwitch12004V1 before_switch;
  std::optional<game::GuiRefillStaticOwnerSwitch12004V1> native_after_switch;
};
// This is the actual action decision boundary used below by the native owner
// executor. Fixtures replace only dispatch I/O; ACK never verifies a switch.
template<class Dispatch> inline void ApplyMilitaryReinforcementDecision12004(
    const MilitaryReinforcementSource12004 &source,bool desired,Dispatch dispatch,
    MilitaryReinforcementResult12004 &out) noexcept {
  out.desired_enabled=desired;out.source_child_path=source.child_path;out.before_switch=source.owner_switch;
  if(source.owner_switch.status!="available"||!source.owner_switch.enabled.has_value()) {
    out.unavailable_reason="source_switch_unavailable";return;
  }
  if(*source.owner_switch.enabled==desired){out.status="noaction_already_desired";return;}
  out.dispatch_attempted=true;
  try {
    out.dispatch_invoked=dispatch(out.native_handled);
    out.status=out.dispatch_invoked?"acknowledged_verification_pending":"unavailable";
    if(!out.dispatch_invoked)out.unavailable_reason="native_shortcut_dispatch_failed_no_retry";
  } catch(...) {out.unavailable_reason="native_shortcut_dispatch_exception_no_retry";}
}

struct MilitaryReinforcementActionContext12004 {
  const game::GameAdapter *game=nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0,connection_generation=0;
  bool desired_enabled=false;
  MilitaryReinforcementResult12004 result{};
};
bool ExecuteMilitaryReinforcementAction12004(MilitaryReinforcementActionContext12004 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch_environment) noexcept;
std::string SerializeMilitaryReinforcementAction12004(const MilitaryReinforcementResult12004 &result);
} // namespace xar::ck3_11906
