#include "xar_bridge/military_reinforcement_action_12004.hpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_11906;
namespace {
void Require(bool value,const char *why){if(!value)throw std::runtime_error(why);}
NamedGuiTreeInspectionV1 SourceTree() {
  NamedGuiTreeInspectionV1 t{};t.scope_root_name="military_view";t.root_available=true;
  t.standard_click_bindings_12004=t.callback_thunk_3aa30e0_pin_verified=true;
  t.expression_layout_3a9f960_pin_verified=t.receiver_candidate_source_pins_verified=true;
  for(const char *path:{"","0","0/0","0/0/0","0/0/0/2","0/0/0/2/3","0/0/0/2/3/0","0/0/0/2/3/0/0","0/0/0/2/3/0/0/0"}) {
    NamedGuiWidgetInspectionV1 row{};row.child_path=path;row.effective_visible=row.enabled=true;row.vtable_rva=0x4900000;
    if(row.child_path.empty())row.runtime_name="military_view";
    if(row.child_path=="0/0/0/2")row.runtime_name="tab_your_armies";
    if(row.child_path=="0/0/0/2/3")row.runtime_name="footer";
    t.widgets.push_back(row);
  }
  auto &row=t.widgets.back();auto &binding=row.standard_click_binding_12004;
  binding.button_base_slot13=true;binding.primary_group=true;
  NamedGuiStandardClickCallback12004V1 cb{};cb.callback_slot2_rva=0x3AA30E0;
  cb.indirect_target_3aa30e0=cb.receiver_f0_present=cb.expression_descriptor_3a9f960=true;cb.native_target_8_rva=0x3A9F960;
  auto &ex=cb.expression_3a9f960;ex.final_kind_34_raw=3;ex.final_target_38_rva=0x1303D40;
  ex.final_user_data_40_present=true;ex.receiver_type_id_48=635U;
  ex.receiver_entry_candidates_12004.emplace();
  auto &candidate=*ex.receiver_entry_candidates_12004;
  candidate.definition_frontier_continuation_depth8_12.emplace();
  auto &continuation=*candidate.definition_frontier_continuation_depth8_12;
  continuation.status="available";continuation.stable_double_read=true;
  continuation.static_direct_owner_switch_12004.emplace();auto &v=*continuation.static_direct_owner_switch_12004;
  v.status="available";v.unavailable_reason.clear();v.ancestor_depth=8U;v.owner_full_id=31254;
  v.military_component_present=true;v.raw_byte_4a9=1;v.enabled=true;v.value_basis="raw_military_byte";v.stable_double_read=true;
  binding.callbacks.push_back(cb);t.widget_count=t.widgets.size();return t;
}
MilitaryReinforcementResult12004 Result() {
  MilitaryReinforcementResult12004 out{};out.native_revision=109;out.connection_generation=1;out.game_pid=29000;
  out.played_character_id=31254;out.date_raw=53148960;out.accepted=true;
  out.owner_thread_verified=out.frame_verified=out.source_abi_pins_verified=out.gui_owner_binding_verified=true;
  out.source_profile_verified=out.current_tree_complete=out.no_blocking_modal_verified=true;return out;
}
}
int main() {
  try {
    auto tree=SourceTree();MilitaryReinforcementSource12004 source{};
    Require(SelectMilitaryReinforcementSource12004(tree,31254,source),"actual fixed source profile was rejected");
    auto wrong_owner=tree;auto &wrong=*wrong_owner.widgets.back().standard_click_binding_12004.callbacks[0].expression_3a9f960.receiver_entry_candidates_12004;
    wrong.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004->owner_full_id=31255;
    MilitaryReinforcementSource12004 rejected{};
    Require(!SelectMilitaryReinforcementSource12004(wrong_owner,31254,rejected),"foreign source owner was admitted");
    auto hidden=tree;hidden.widgets.back().effective_visible=false;
    Require(!SelectMilitaryReinforcementSource12004(hidden,31254,rejected),"hidden callback was admitted");
    auto no_source=tree;no_source.widgets.back().standard_click_binding_12004.callbacks[0].expression_3a9f960.final_target_38_rva=0;
    Require(!SelectMilitaryReinforcementSource12004(no_source,31254,rejected),"wrong final callback was admitted");
    std::cout<<"{\"case\":\"fixed_source_owner_and_visibility\",\"passed\":true}\n";
    int dispatches=0;auto same=Result();
    ApplyMilitaryReinforcementDecision12004(source,true,[&](bool&){++dispatches;return true;},same);
    Require(dispatches==0&&!same.dispatch_attempted&&same.status=="noaction_already_desired","already desired dispatched");
    std::cout<<SerializeMilitaryReinforcementAction12004(same)<<'\n';
    auto changed=Result();
    ApplyMilitaryReinforcementDecision12004(source,false,[&](bool &handled){++dispatches;handled=false;return true;},changed);
    Require(dispatches==1&&changed.dispatch_attempted&&changed.dispatch_invoked&&!changed.native_handled&&
        changed.status=="acknowledged_verification_pending","one dispatch or ACK diagnostic handling failed");
    const auto wire=SerializeMilitaryReinforcementAction12004(changed);
    Require(wire.find("\"postcondition_verified\":false")!=std::string::npos,"ACK was promoted to toggle");
    std::cout<<wire<<'\n';
    auto unknown=Result();
    ApplyMilitaryReinforcementDecision12004(source,false,[&](bool&){++dispatches;return false;},unknown);
    Require(dispatches==2&&unknown.dispatch_attempted&&!unknown.dispatch_invoked&&unknown.status=="unavailable",
        "unknown dispatch lost attempted marker");
    std::cout<<"{\"case\":\"unknown_dispatch_no_internal_retry\",\"passed\":true}\n";
    return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
