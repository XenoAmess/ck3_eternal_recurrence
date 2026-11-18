#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
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
} // namespace
int main(int argc,char **argv) {
  int cases=0;const auto check=[&](bool okay){assert(okay);++cases;};
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
