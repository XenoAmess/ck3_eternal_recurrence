#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <vector>
#include "toast_owned_fixture_v1.hpp"
using namespace xar::ck3_1210;
using namespace xar::ck3_1210::toast_test;
namespace {
void AssertUncorrelated(const ToastObjectObservationV1 &out) {
  assert(!out.recipient_identity_available && !out.news_origin_available && !out.delivery_confirmed);
}
// Software-owned topology mirrors the installed vanilla default and
// contract branches; it is not a capture of the R31 process.
constexpr std::uintptr_t kContract=0x2E000000,kContractContent=0x2F000000;
constexpr std::uintptr_t kContractChildren=0x30000000,kToastBranches=0x30100000;
void ContractBranch(Fixture &f,std::uint8_t flags=8) {
  f.memory.add(kContract,0x600);f.memory.add(kContractContent,0x600);
  f.memory.add(kContractChildren,8);f.memory.add(kToastBranches,16);
  f.widget(kContract,Fixture::toast_widget,kContractChildren,1,"toast_background_contract");
  f.widget(kContractContent,kContract,0,0,"toast_content");
  f.memory.put(kContractChildren,kContractContent);
  f.memory.put<std::uint8_t>(kContract+0xD0,flags);
  f.memory.put(kToastBranches,Fixture::content);f.memory.put(kToastBranches+8,kContract);
  f.memory.put(Fixture::toast_widget+0xF0,kToastBranches);
  f.memory.put<std::int32_t>(Fixture::toast_widget+0xFC,2);
}
} // namespace
int main() {
  std::size_t checks=0;
  {Fixture f;ToastObjectObservationV1 out;assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible_pending_frame);AssertUncorrelated(out);
    assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible_pending_frame);f.advance();assert(f.read(out));
    assert(out.stage==ToastObjectStageV1::visible && out.title=="Test title" && out.description=="Test description");AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::int32_t>(Fixture::toast+0xD4,0);
    f.memory.fail_address=Fixture::toast+0x60;assert(f.read(out));assert(out.stage==ToastObjectStageV1::empty);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uint8_t>(Fixture::content+0xD0,8);assert(f.read(out));assert(out.stage==ToastObjectStageV1::hidden);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uint8_t>(Fixture::gui_root+0xD0,8);assert(f.read(out));assert(out.stage==ToastObjectStageV1::hidden);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uintptr_t>(Fixture::toast+0x98,Fixture::app);assert(!f.read(out));assert(!f.provider.has_previous);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::int32_t>(Fixture::toast+0xD4,65);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uint64_t>(Fixture::item+0x11C8+0x18,14);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uintptr_t>(Fixture::root_children,Fixture::content);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uintptr_t>(Fixture::toast_children,Fixture::toast_widget);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;assert(f.read(out));f.memory.put<std::uintptr_t>(Fixture::app+0x78,Fixture::root);assert(!f.read(out));assert(!f.provider.has_previous);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.change_address=Fixture::toast+0xD4;assert(!f.read(out));assert(out.unavailable_reason=="toast_capture_changed");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.scopes();assert(f.read(out));assert(out.saved_gui_scopes.size()==1 && out.saved_gui_scopes[0].name=="xfm_news_display_entry" && !out.saved_gui_scopes[0].identity_available && !out.saved_gui_scopes[0].identity && out.saved_gui_scopes[0].unavailable_reason=="scope_tag_not_admitted");AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.scopes(2);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_scopes();assert(f.read(out));
    assert(out.saved_script_scopes.size()==1 && out.saved_script_scopes[0].name=="xfm_news_display_entry" && !out.saved_script_scopes[0].identity_available && !out.saved_script_scopes[0].identity);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.scopes();f.memory.put<std::uint32_t>(Fixture::base+0x6B14640+0x48,1);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.bindings.exact_build_admitted=false;assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uint8_t>(Fixture::item+0x10,3);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.memory.put<std::uint8_t>(Fixture::item+0x11C8,0xFF);assert(!f.read(out));++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();assert(f.read(out));
    assert(out.saved_script_scopes.size()==2 && out.saved_script_scopes[0].identity=="50331650" &&
        out.saved_script_scopes[1].identity=="-2147483646" && out.saved_script_scopes[1].observed_tag==4);
    AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();
    f.memory.put<std::uint32_t>(Fixture::character_object+0x18,0);f.memory.put<std::uint32_t>(Fixture::character_storage+0x2C,1);
    f.memory.add(Fixture::character_slots+8,8);f.memory.put(Fixture::character_slots+8,Fixture::character_object);
    f.memory.put<std::array<std::byte,16>>(0x34000000+0x50,Fixture::token(4,0));assert(f.read(out));
    assert(out.saved_script_scopes[1].identity=="0");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();f.memory.change_address=Fixture::story_object+0x10;
    assert(!f.read(out));assert(out.stage==ToastObjectStageV1::unavailable && out.saved_script_scopes.empty() && !f.provider.has_previous);
    assert(out.unavailable_reason=="scope_canonical_object_unavailable");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();f.memory.change_address=Fixture::story_object+0x10;f.memory.change_on_hit=3;
    assert(!f.read(out));assert(out.saved_script_scopes.empty() && !f.provider.has_previous);
    assert(out.unavailable_reason=="scope_canonical_object_unavailable");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();f.scopes();
    f.text(0x32000000+0x60,"software_story");f.memory.put<std::array<std::byte,16>>(0x31000000+8,Fixture::token(22,0x03000002));
    assert(f.read(out));assert(out.saved_gui_scopes[0].identity==out.saved_script_scopes[0].identity);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();f.scopes();f.text(0x32000000+0x60,"software_story");
    assert(!f.read(out));assert(out.unavailable_reason=="toast_saved_scope_context_mismatch" && out.saved_gui_scopes.empty());++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_many(64);assert(f.read(out));assert(out.saved_script_scopes.size()==64);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_many(65);assert(!f.read(out));assert(out.saved_script_scopes.empty());++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_many(64);f.scopes();assert(!f.read(out));
    assert(out.unavailable_reason=="toast_saved_scope_total_budget_exhausted_or_unreadable");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.bindings.scope_identities.module_base+=8;
    assert(!f.read(out));assert(out.unavailable_reason=="toast_exact_scope_binding_unavailable");++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.script_typed_pair();
    //63 real reciprocal ancestors with4096-slot vectors consume just under the
    //4MiB aggregate across two captures; selected subtree reads cross it.
    std::uintptr_t child=Fixture::toast_widget;
    for(std::size_t i=0;i<63;++i) {
      const auto parent=i==62?Fixture::gui_root:std::uintptr_t{0x50000000}+i*0x1000;
      const auto children=std::uintptr_t{0x60000000}+i*0x10000;
      if(i!=62)f.memory.add(parent,0x600);f.memory.add(children,4096*8);
      f.widget(parent,0,children,4096,std::string(192,'a'));f.memory.put(children,child);f.memory.put(child+0xE8,parent);child=parent;
    }
    const std::uintptr_t selected=0x70000000;f.memory.add(selected,100*8);
    f.memory.put(Fixture::toast_widget+0xF0,selected);f.memory.put<std::int32_t>(Fixture::toast_widget+0xFC,100);
    f.memory.put(selected,Fixture::content);
    for(std::size_t i=1;i<100;++i) {const auto node=std::uintptr_t{0x71000000}+i*0x1000;
      f.memory.add(node,0x600);f.widget(node,Fixture::toast_widget,0,0,std::string(192,'b'));f.memory.put(selected+i*8,node);}
    assert(!f.read(out));assert(out.unavailable_reason=="toast_total_read_budget_exhausted");
    assert(f.memory.bytes_seen<=kToastObjectReadBudgetV1 && out.saved_script_scopes.empty());++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f);
    assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible_pending_frame && out.queue_count==1);
    f.advance();assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible);
    assert(f.provider.previous.subtree.size()==4 && out.title=="Test title");AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f,0);
    f.memory.put<std::uint8_t>(Fixture::content+0xD0,8);assert(f.read(out));
    f.advance();assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f);
    f.memory.put<std::uint8_t>(Fixture::content+0xD0,8);assert(f.read(out));
    assert(out.stage==ToastObjectStageV1::hidden && out.queue_count==1);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f,0);assert(!f.read(out));
    assert(out.unavailable_reason=="toast_ui_visible_content_ambiguous" && !f.provider.has_previous);
    assert(out.queue_count==0 && out.title.empty());AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;f.text(Fixture::content+0x1B8,"other_content");assert(!f.read(out));
    assert(out.unavailable_reason=="toast_ui_content_not_materialized");++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f);
    f.memory.put(kContractContent+0xE8,Fixture::toast_widget);assert(!f.read(out));
    assert(out.unavailable_reason=="toast_ui_subtree_source_unavailable_or_mismatched");++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f);assert(f.read(out));f.advance();assert(f.read(out));
    assert(out.stage==ToastObjectStageV1::visible);
    f.memory.put<std::uint8_t>(Fixture::content+0xD0,8);f.memory.put<std::uint8_t>(kContract+0xD0,0);
    f.advance();assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible_pending_frame);
    f.advance();assert(f.read(out));assert(out.stage==ToastObjectStageV1::visible);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f,0);
    f.memory.put<std::uint8_t>(Fixture::gui_root+0xD0,8);assert(f.read(out));
    assert(out.stage==ToastObjectStageV1::hidden);AssertUncorrelated(out);++checks;}
  {Fixture f;ToastObjectObservationV1 out;ContractBranch(f);
    f.memory.fail_address=kContractContent+0xD8;assert(!f.read(out));
    assert(out.unavailable_reason=="toast_ui_subtree_source_unavailable_or_mismatched");++checks;}
  std::cout<<"toast published object provider: "<<checks<<" checks; software-owned memory only; no public admission or delivery claim\n";
}
