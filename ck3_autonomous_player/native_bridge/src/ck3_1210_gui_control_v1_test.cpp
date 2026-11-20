#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_1210_gui_root_registry_v1.hpp"
#include <map>
#include <cstring>
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include <cassert>
#include <iostream>
#include <limits>

using namespace xar::ck3_1210;
namespace {
struct Fixture {
  GuiControlCaptureV1 value;
  int captures=0,dispatches=0;
  bool change=false,deny=false,unknown=false;
  Fixture() {
    value.played_character_id=42;value.date_raw=50000000;value.native_revision=7;value.connection_generation=3;
    value.logical_owner=1;value.application=2;value.context=3;value.gui_owner=3;value.global_root=4;
    value.root=5;value.shortcut_manager=6;value.root_name="xfm_market_entry";value.complete=true;
    GuiControlIdentityV1 root;root.widget=5;root.context=3;
    root.row={1,"xfm_market_entry","",0x500,true,true,false};value.widgets.push_back(root);
    GuiControlIdentityV1 button;button.widget=7;button.parent=5;button.context=3;
    button.row={2,"xfm_market_open","0",0x501,true,true,true};
    GuiControlCallbackV1 callback;callback.object=8;callback.vtable=9;callback.invoke=10;
    button.callbacks.push_back(callback);value.widgets.push_back(button);
  }
  static bool Capture(void *p,std::string_view,GuiControlCaptureV1 &out,std::string &) noexcept {
    auto &f=*static_cast<Fixture *>(p);out=f.value;++f.captures;
    if(f.change && f.captures%2==0)out.widgets[1].callbacks[0].binding[0]=std::byte{1};return true;
  }
  static bool Dispatch(void *p,const GuiControlCaptureV1 &,const GuiControlIdentityV1 &,bool &handled,bool &attempted) noexcept {
    auto &f=*static_cast<Fixture *>(p);++f.dispatches;attempted=!f.deny;handled=false;return !f.deny && !f.unknown;
  }
  GuiControlBackendV1 Backend() {return {this,&Capture,&Dispatch};}
};
GuiControlRequestV1 Query() {return {false,kGuiControlQueryStepV1,"xfm_market_entry",7,10000,0,0};}
GuiControlRequestV1 Action(std::uint64_t generation) {return {true,kGuiControlActivateStepV1,"xfm_market_entry",7,10000,generation,2};}
std::string Request() {
  return std::string{"{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"gui-1\",\"step\":\"query-scripted-widget-controls-v1\",\"expected_revision\":7,\"arguments\":{},\"gui_control_v1\":{\"schema\":\"ck3_1210_gui_control_v1\",\"game_version\":\"1.21.0\",\"executable_sha256\":\""}+
      kExecutableSha256+"\",\"adapter_id\":\"ck3-1.21.0-msvc-x64\",\"backend\":\""+kCoreBackendV1+
      "\",\"snapshot_id\":\"native:7\",\"native_revision\":7,\"deadline_unix_ms\":10000,\"root_name\":\"xfm_market_entry\",\"query_generation\":\"0\",\"widget_id\":\"0\"}}";
}
std::string Replace(std::string text,std::string_view from,std::string_view to) {
  const auto at=text.find(from);assert(at!=std::string::npos);text.replace(at,from.size(),to);return text;
}

struct RootRegistryFixture {
  static constexpr std::uintptr_t module=0x140000000ULL,context=0x7700,global=0x10000,root=0x10100,parent=0x10200,unrelated=0x10300;
  static constexpr std::uintptr_t manager=module+kGuiScriptedRootManagerRvaV1,data=0x20000,entry=0x30000;
  std::map<std::uintptr_t,std::vector<std::byte>> memory;
  std::map<std::uintptr_t,GuiControlIdentityV1> widgets;
  std::map<std::uintptr_t,unsigned> widget_reads;
  std::uintptr_t bad_widget=0;bool change_header=false;unsigned header_reads=0;
  template<class T> void Put(std::uintptr_t address,T value) {
    auto &bytes=memory[address];bytes.resize(sizeof(value));std::memcpy(bytes.data(),&value,sizeof(value));
  }
  void Array(std::uintptr_t address,std::initializer_list<std::uintptr_t> values) {
    auto &bytes=memory[address];bytes.resize(values.size()*8);std::size_t i=0;
    for(const auto value:values) {std::memcpy(bytes.data()+i*8,&value,8);++i;}
  }
  void Entry(std::uintptr_t object,std::uintptr_t widget) {
    Put(object,module+kGuiScriptedRootEntryVtableRvaV1);Put(object+0x60,widget);Put(object+0x68,context);
  }
  GuiControlIdentityV1 Widget(std::uintptr_t pointer,std::string name,std::uintptr_t owner,std::uintptr_t children=0,std::int32_t count=0) {
    GuiControlIdentityV1 w;w.widget=pointer;w.context=context;w.parent=owner;w.children=children;w.child_count=count;
    w.row.runtime_name=std::move(name);w.row.vtable_rva=0x500;w.row.effective_visible=true;w.row.enabled=true;return w;
  }
  RootRegistryFixture() {
    Put(manager,module+kGuiScriptedRootManagerVtableRvaV1);Put(manager+0x30,data);
    Put(manager+0x38,std::int32_t{1});Put(manager+0x3C,std::int32_t{1});Array(data,{entry});Entry(entry,root);
    widgets[root]=Widget(root,"xfma_observer_widget",parent);
    widgets[parent]=Widget(parent,"container",global,0x21000,1);Array(0x21000,{root});
    widgets[global]=Widget(global,"global",0,0x22000,2);Array(0x22000,{parent,unrelated});
    // No readable unrelated branch: the old full-tree search would visit it.
  }
  static bool Read(void *opaque,std::uintptr_t address,void *out,std::size_t size) noexcept {
    auto &f=*static_cast<RootRegistryFixture *>(opaque);
    if(address==manager && ++f.header_reads>1 && f.change_header) {std::memset(out,0,size);return true;}
    const auto at=f.memory.find(address);if(at==f.memory.end() || at->second.size()!=size)return false;
    std::memcpy(out,at->second.data(),size);return true;
  }
  static bool ReadWidget(void *opaque,std::uintptr_t pointer,GuiControlIdentityV1 &out) noexcept {
    try {auto &f=*static_cast<RootRegistryFixture *>(opaque);++f.widget_reads[pointer];
      const auto at=f.widgets.find(pointer);if(pointer==f.bad_widget || at==f.widgets.end())return false;
      out=at->second;out.row.effective_visible=(out.flags&0x18)==0;out.row.enabled=(out.flags&0x06)==0;return true;
    }catch(...) {return false;}
  }
  GuiControlRootReaderV1 Reader() {return {this,&Read,&ReadWidget};}
  bool Resolve(GuiControlRootNodeV1 &node,GuiControlScriptedRootWitnessV1 &source,std::string &reason) {
    return ResolveGuiScriptedRootV1(Reader(),module,context,global,"xfma_observer_widget",node,source,reason);
  }
};
bool TestScriptedRootRegistry() {
  unsigned cases=0;
  const auto reject=[&](RootRegistryFixture &f,std::string_view expected) {
    GuiControlRootNodeV1 node;GuiControlScriptedRootWitnessV1 source;std::string reason;
    ++cases;return !f.Resolve(node,source,reason) && reason==expected && node.p==0 && source.entries.empty();
  };
  {
    RootRegistryFixture f;GuiControlRootNodeV1 node;GuiControlScriptedRootWitnessV1 source;std::string reason;
    if(!f.Resolve(node,source,reason) || node.p!=f.root || node.parent!=f.parent || !node.visible || !node.enabled ||
        source.entries.size()!=1 || source.ancestry.size()!=3 || f.widget_reads[f.unrelated]!=0)return false;
    ++cases;
  }
  {
    RootRegistryFixture f;f.widgets[f.parent].flags=0x0A;
    GuiControlRootNodeV1 node;GuiControlScriptedRootWitnessV1 source;std::string reason;
    if(!f.Resolve(node,source,reason) || node.visible || node.enabled || source.ancestry[1].flags!=0x0A)return false;
    ++cases;
  }
  {RootRegistryFixture f;f.Put(f.entry+0x60,std::uintptr_t{0});if(!reject(f,"gui_root_not_materialized"))return false;}
  {RootRegistryFixture f;f.Put(f.manager,std::uintptr_t{0});if(!reject(f,"gui_scripted_registry_unavailable"))return false;}
  {RootRegistryFixture f;f.Put(f.manager+0x38,std::int32_t{4097});f.Put(f.manager+0x3C,std::int32_t{4097});if(!reject(f,"gui_scripted_registry_entry_budget_exhausted"))return false;}
  {RootRegistryFixture f;f.Put(f.manager+0x3C,std::int32_t{-1});if(!reject(f,"gui_scripted_registry_vector_invalid"))return false;}
  {RootRegistryFixture f;f.memory.erase(f.entry+0x60);if(!reject(f,"gui_scripted_registry_entry_invalid"))return false;}
  {RootRegistryFixture f;f.memory.erase(f.data);if(!reject(f,"gui_scripted_registry_entries_read_failed"))return false;}
  {RootRegistryFixture f;f.Array(f.data,{0});if(!reject(f,"gui_scripted_registry_null_entry"))return false;}
  {RootRegistryFixture f;f.Put(f.entry,std::uintptr_t{0});if(!reject(f,"gui_scripted_registry_entry_invalid"))return false;}
  {RootRegistryFixture f;f.Put(f.entry+0x68,std::uintptr_t{1});if(!reject(f,"gui_scripted_registry_context_mismatch"))return false;}
  {RootRegistryFixture f;f.widgets[f.root].context=1;if(!reject(f,"gui_scripted_registry_widget_invalid"))return false;}
  {RootRegistryFixture f;f.widgets[f.parent].context=1;if(!reject(f,"gui_root_parent_invalid"))return false;}
  {RootRegistryFixture f;f.Array(f.data,{f.entry,f.entry});f.Put(f.manager+0x38,std::int32_t{2});f.Put(f.manager+0x3C,std::int32_t{2});if(!reject(f,"gui_scripted_registry_duplicate_entry"))return false;}
  {RootRegistryFixture f;f.Entry(f.entry+0x100,f.root);f.Array(f.data,{f.entry,f.entry+0x100});f.Put(f.manager+0x38,std::int32_t{2});f.Put(f.manager+0x3C,std::int32_t{2});if(!reject(f,"gui_scripted_registry_duplicate_root"))return false;}
  {RootRegistryFixture f;f.Entry(f.entry+0x100,f.unrelated);f.widgets[f.unrelated]=f.Widget(f.unrelated,"xfma_observer_widget",f.global);f.Array(f.data,{f.entry,f.entry+0x100});f.Put(f.manager+0x38,std::int32_t{2});f.Put(f.manager+0x3C,std::int32_t{2});if(!reject(f,"gui_root_ambiguous"))return false;}
  {RootRegistryFixture f;f.widgets[f.parent].parent=f.root;if(!reject(f,"gui_root_parent_cycle_or_detached"))return false;}
  {RootRegistryFixture f;f.Array(0x21000,{0});if(!reject(f,"gui_root_parent_child_backref_invalid"))return false;}
  {RootRegistryFixture f;f.Array(0x21000,{f.root,f.root});f.widgets[f.parent].child_count=2;if(!reject(f,"gui_root_parent_child_backref_invalid"))return false;}
  {RootRegistryFixture f;f.bad_widget=f.parent;if(!reject(f,"gui_root_parent_invalid"))return false;}
  {RootRegistryFixture f;f.memory.erase(0x22000);if(!reject(f,"gui_global_parent_children_read_failed"))return false;}
  {RootRegistryFixture f;f.change_header=true;if(!reject(f,"gui_scripted_registry_changed"))return false;}
  {
    RootRegistryFixture f;f.widgets[f.root].parent=0x40000;
    for(std::uintptr_t i=0;i<66;++i)f.widgets[0x40000+i*0x100]=f.Widget(0x40000+i*0x100,"deep",0x40100+i*0x100);
    if(!reject(f,"gui_root_parent_depth_budget_exhausted"))return false;
  }
  {
    RootRegistryFixture f;GuiControlIdentityV1 w;w.children=0x50000;w.child_count=1;
    GuiControlRootNodeV1 n{f.root,0,0,{},true,true};
    std::vector<GuiControlRootNodeV1> nodes{n};std::unordered_set<std::uintptr_t> seen{n.p};
    if(AppendGuiControlChildrenV1(f.Reader(),n,w,nodes,seen,1)!=GuiControlChildrenResultV1::node_budget_exhausted)return false;
    n.depth=64;if(AppendGuiControlChildrenV1(f.Reader(),n,w,nodes,seen,2)!=GuiControlChildrenResultV1::depth_budget_exhausted)return false;
    n.depth=0;if(AppendGuiControlChildrenV1(f.Reader(),n,w,nodes,seen,2)!=GuiControlChildrenResultV1::child_pointer_read_failed)return false;
    f.Array(w.children,{f.root});if(AppendGuiControlChildrenV1(f.Reader(),n,w,nodes,seen,2)!=GuiControlChildrenResultV1::duplicate_or_cycle)return false;
    f.Array(w.children,{f.unrelated});w.row.effective_visible=false;w.row.enabled=false;
    if(AppendGuiControlChildrenV1(f.Reader(),n,w,nodes,seen,2)!=GuiControlChildrenResultV1::complete ||
        nodes.size()!=2 || nodes[1].visible || nodes[1].enabled || nodes[1].path!="0")return false;
    cases+=5;
  }
  std::cout<<cases<<" scripted-root registry/ancestry/child failure checks; unrelated global branch never traversed\n";
  return true;
}
} // namespace
int main(int argc,char **argv) {
  int cases=0;const auto check=[&](bool okay){assert(okay);++cases;};
  // A negative signed full generation ID is valid; None(-1) and legacy0 stay closed.
  for(const auto full_id:{std::int32_t{-16777215},std::int32_t{-2147483647}}) {
    Fixture signed_actor;signed_actor.value.played_character_id=full_id;
    GuiControlProviderV1 state;GuiControlResultV1 observed;
    if(!ApplyGuiControlV1(state,Query(),signed_actor.Backend(),observed) ||
        observed.status!=GuiControlStatusV1::available) {
      std::cerr<<"SIGNED_FULL_ID_QUERY_REJECTED "<<full_id<<"\n";return 2;
    }
    if(!ApplyGuiControlV1(state,Action(state.query_generation),signed_actor.Backend(),observed) ||
        observed.status!=GuiControlStatusV1::submitted || signed_actor.dispatches!=1) {
      std::cerr<<"SIGNED_FULL_ID_SOURCE_ACTION_REJECTED\n";return 3;
    }
    ++cases;
  }
  for(const auto invalid:{std::int32_t{-1},std::int32_t{0}}) {
    Fixture missing;missing.value.played_character_id=invalid;
    GuiControlProviderV1 state;GuiControlResultV1 observed;
    if(ApplyGuiControlV1(state,Query(),missing.Backend(),observed) || state.valid || missing.dispatches) return 4;
    ++cases;
  }
  {
    Fixture changed;changed.value.played_character_id=-16777215;
    GuiControlProviderV1 state;GuiControlResultV1 observed;
    if(!ApplyGuiControlV1(state,Query(),changed.Backend(),observed)) return 5;
    changed.value.played_character_id=-16777214;
    if(ApplyGuiControlV1(state,Action(state.query_generation),changed.Backend(),observed) || changed.dispatches || state.valid)return 6;
    ++cases;
  }
  check(TestScriptedRootRegistry());
  GuiControlRequestV1 parsed;const auto wire=Request();
  check(ParseGuiControlRequestV1(wire,parsed) && parsed.root_name=="xfm_market_entry" && parsed.native_revision==7);
  for(const auto &pair:std::initializer_list<std::pair<std::string,std::string>>{
      {"\"expected_revision\":7","\"expected_revision\":8"},
      {"\"native:7\"","\"native:8\""}, {"\"query_generation\":\"0\"","\"query_generation\":0"},
      {"\"query_generation\":\"0\"","\"query_generation\":\"00\""},
      {"\"widget_id\":\"0\"","\"widget_id\":true"},
      {"\"native_revision\":7","\"native_revision\":7.0"},
      {"\"root_name\":\"xfm_market_entry\"","\"root_name\":\"../unsafe\""},
      {"\"root_name\":\"xfm_market_entry\"","\"root_name\":\"1invalid\""},
      {"\"arguments\":{}","\"arguments\":{\"root\":1}"},
      {"\"widget_id\":\"0\"","\"widget_id\":\"0\",\"widget_id\":\"0\""},
      {"\"deadline_unix_ms\":10000","\"deadline_unix_ms\":0"}})
    check(!ParseGuiControlRequestV1(Replace(wire,pair.first,pair.second),parsed) && parsed.root_name.empty());
  auto action_wire=Replace(wire,"query-scripted-widget-controls-v1","activate-scripted-widget-control-v1");
  action_wire=Replace(action_wire,"\"query_generation\":\"0\"","\"query_generation\":\"18446744073709551615\"");
  action_wire=Replace(action_wire,"\"widget_id\":\"0\"","\"widget_id\":\"2\"");
  check(ParseGuiControlRequestV1(action_wire,parsed) && parsed.activate && parsed.query_generation==(std::numeric_limits<std::uint64_t>::max)());
  check(!ParseGuiControlRequestV1(Replace(action_wire,"18446744073709551615","18446744073709551616"),parsed));
  Fixture f;GuiControlProviderV1 provider;GuiControlResultV1 result;
  check(ApplyGuiControlV1(provider,Query(),f.Backend(),result) && result.status==GuiControlStatusV1::available && result.widgets.size()==2 && provider.valid);
  const auto generation=provider.query_generation;
  check(ApplyGuiControlV1(provider,Action(generation),f.Backend(),result) && result.status==GuiControlStatusV1::submitted && result.effect_attempted && result.verification_pending && !provider.valid && f.dispatches==1);
  check(!ApplyGuiControlV1(provider,Action(generation),f.Backend(),result) && !result.effect_attempted && f.dispatches==1);
  Fixture changed;GuiControlProviderV1 p2;check(ApplyGuiControlV1(p2,Query(),changed.Backend(),result));
  changed.value.widgets[1].callbacks[0].object=999;
  check(!ApplyGuiControlV1(p2,Action(p2.query_generation),changed.Backend(),result) && result.status==GuiControlStatusV1::stale_gui && changed.dispatches==0);
  Fixture scope;GuiControlProviderV1 p3;check(ApplyGuiControlV1(p3,Query(),scope.Backend(),result));
  scope.value.widgets[1].callbacks[0].binding[40]=std::byte{1};
  check(!ApplyGuiControlV1(p3,Action(p3.query_generation),scope.Backend(),result) && scope.dispatches==0);
  Fixture episode;GuiControlProviderV1 p4;check(ApplyGuiControlV1(p4,Query(),episode.Backend(),result));
  episode.value.connection_generation=4;
  check(!ApplyGuiControlV1(p4,Action(p4.query_generation),episode.Backend(),result) && episode.dispatches==0);
  Fixture disabled;disabled.value.widgets[1].row.clickable=false;GuiControlProviderV1 p5;
  check(ApplyGuiControlV1(p5,Query(),disabled.Backend(),result));
  check(!ApplyGuiControlV1(p5,Action(p5.query_generation),disabled.Backend(),result) && result.status==GuiControlStatusV1::disabled && disabled.dispatches==0);
  Fixture race;race.change=true;GuiControlProviderV1 p6;
  check(!ApplyGuiControlV1(p6,Query(),race.Backend(),result) && result.status==GuiControlStatusV1::stale_gui && !p6.valid);
  Fixture unknown;unknown.unknown=true;GuiControlProviderV1 p7;
  check(ApplyGuiControlV1(p7,Query(),unknown.Backend(),result));
  check(!ApplyGuiControlV1(p7,Action(p7.query_generation),unknown.Backend(),result) && result.status==GuiControlStatusV1::indeterminate && result.effect_attempted && !p7.valid);
  check(!ApplyGuiControlV1(p7,Action(p7.query_generation),unknown.Backend(),result) && unknown.dispatches==1);
  Fixture registry_source;GuiControlProviderV1 registry_provider;
  registry_source.value.scripted_root_source.manager=1;registry_source.value.scripted_root_source.data=2;
  check(ApplyGuiControlV1(registry_provider,Query(),registry_source.Backend(),result));
  registry_source.value.scripted_root_source.data=3;
  check(!ApplyGuiControlV1(registry_provider,Action(registry_provider.query_generation),registry_source.Backend(),result) &&
      result.status==GuiControlStatusV1::stale_gui && registry_source.dispatches==0);
  Fixture ancestry_source;GuiControlProviderV1 ancestry_provider;
  ancestry_source.value.scripted_root_source.ancestry.push_back(Fixture{}.value.widgets[0]);
  check(ApplyGuiControlV1(ancestry_provider,Query(),ancestry_source.Backend(),result));
  ancestry_source.value.scripted_root_source.ancestry[0].flags=8;
  check(!ApplyGuiControlV1(ancestry_provider,Action(ancestry_provider.query_generation),ancestry_source.Backend(),result) &&
      result.status==GuiControlStatusV1::stale_gui && ancestry_source.dispatches==0);
  Fixture hidden_ancestor;GuiControlProviderV1 hidden_provider;
  hidden_ancestor.value.scripted_root_source.ancestry.push_back(Fixture{}.value.widgets[0]);
  hidden_ancestor.value.scripted_root_source.ancestry[0].flags=8;
  hidden_ancestor.value.widgets[1].row.effective_visible=false;
  check(ApplyGuiControlV1(hidden_provider,Query(),hidden_ancestor.Backend(),result));
  check(!ApplyGuiControlV1(hidden_provider,Action(hidden_provider.query_generation),hidden_ancestor.Backend(),result) &&
      result.status==GuiControlStatusV1::disabled && hidden_ancestor.dispatches==0);
  Fixture overflow;GuiControlProviderV1 p8;p8.query_generation=(std::numeric_limits<std::uint64_t>::max)();
  check(!ApplyGuiControlV1(p8,Query(),overflow.Backend(),result) && !p8.valid);
  Fixture empty;empty.value.complete=false;GuiControlProviderV1 p9;
  check(!ApplyGuiControlV1(p9,Query(),empty.Backend(),result) && empty.dispatches==0);
  GuiControlResultV1 row_result;row_result.status=GuiControlStatusV1::available;row_result.query_generation=1;
  auto row=Fixture{}.value.widgets[1].row;row_result.widgets.push_back(row);
  const auto json=SerializeGuiControlCommandResultV1("gui-1",Query(),row_result);
  check(json.find("\"query_generation\":\"1\"")!=std::string::npos && json.find("\"widget_id\":\"2\"")!=std::string::npos && json.find("\"complete\":true")!=std::string::npos);
  if(argc==2 && std::string_view{argv[1]}=="query-fixture") {
    row_result.widgets.clear();for(const auto &w:Fixture{}.value.widgets)row_result.widgets.push_back(w.row);
    row_result.application_main_observed=true;row_result.full_snapshot_before_verified=true;row_result.source_abi_pins_verified=true;
    std::cout<<SerializeGuiControlCommandResultV1("software-gui-fixture",Query(),row_result)<<'\n';return 0;
  }
  if(argc==2 && std::string_view{argv[1]}.ends_with("-fixture-high")) {
    const std::string_view mode=argv[1];Fixture producer;producer.value.native_revision=11;
    GuiControlProviderV1 source;source.query_generation=9007199254740998ULL;
    auto request=Query();request.native_revision=11;
    GuiControlResultV1 emitted;
    if(!ApplyGuiControlV1(source,request,producer.Backend(),emitted))return 2;
    if(mode!="query-fixture-high") {
      request=Action(source.query_generation);request.native_revision=11;
      if(mode=="indeterminate-fixture-high")producer.unknown=true;
      if(mode=="oversized-widget-fixture-high")request.widget_id=9007199254741001ULL;
      ApplyGuiControlV1(source,request,producer.Backend(),emitted);
    }
    emitted.application_main_observed=true;emitted.full_snapshot_before_verified=true;emitted.source_abi_pins_verified=true;
    std::cout<<SerializeGuiControlCommandResultV1("software-gui-high-fixture",request,emitted)<<'\n';return 0;
  }
  std::cout<<cases<<" checks passed; no Game/native invocation\n";
}
