#include "xar_bridge/scripted_widget_control12004.hpp"
#include <cassert>
#include <iostream>
#include <limits>

using namespace xar::ck3_11906;
namespace {
struct Fixture {
  ScriptedWidgetCapture12004 source{};
  int captures = 0, calls = 0;
  bool capture_ok = true, dispatch_ok = true, attempted = true, handled = false, change_second = false;
  Fixture() {
    source.frame = {321,1234,867,17,9,0x1000,0x2000,true,true,true};
    source.root_name="custom_mod_window"; source.root=0x3000; source.complete=true;
    ScriptedWidgetIdentity12004 root{}, button{};
    root.row={0,"custom_mod_window","",0x4100000,true,true,false}; root.widget=0x3000;root.vtable=0x144100000;
    root.context=0x1000; root.ancestors={0x3000}; root.ancestor_flags={0};
    button.row={0,"unnamed_button","0/2",0x4100100,true,true,true};
    button.widget=0x4000;button.vtable=0x144100100;button.context=0x1000;
    button.ancestors={0x3000,0x3500,0x4000};button.ancestor_flags={0,0,0};
    button.callback_data=0x5000;button.callback_group=0x3F8;
    ScriptedWidgetCallback12004 callback{};callback.object=0x6000;callback.receiver=0x7000;
    callback.chain_user_data={0x7100};button.callbacks.push_back(callback);
    source.widgets={root,button};
  }
  static bool Capture(void *opaque,std::string_view root,ScriptedWidgetCapture12004 &out,std::string &why) noexcept {
    auto &f=*static_cast<Fixture *>(opaque);++f.captures;
    try {out=f.source;if(f.change_second&&f.captures==2)++out.root;
      if(!f.capture_ok||root!=out.root_name){why="fixture_capture_unavailable";return false;}return true;
    }catch(...){return false;}
  }
  static bool Dispatch(void *opaque,const ScriptedWidgetIdentity12004 &,bool &handled,bool &attempted) noexcept {
    auto &f=*static_cast<Fixture *>(opaque);++f.calls;handled=f.handled;attempted=f.attempted;return f.dispatch_ok;
  }
  ScriptedWidgetBackend12004 backend(){return {this,Capture,Dispatch};}
};
void Query(Fixture &f,ScriptedWidgetProvider12004 &p,ScriptedWidgetResult12004 &r) {
  assert(QueryScriptedWidgetControls12004(p,f.backend(),"custom_mod_window",r));
  assert(r.available&&r.complete&&!r.truncated&&r.query_generation>0&&r.widgets.size()==2&&r.widgets[0].child_path.empty());
}
void IdentityChanges() {
  // Production reducer must reject changes in the actual receiver, bindings,
  // ancestors, source/frame, order, and state before entering native dispatch.
  for(int kind=0;kind<12;++kind) {
    Fixture f;ScriptedWidgetProvider12004 p;ScriptedWidgetResult12004 r;Query(f,p,r);
    auto &b=f.source.widgets[1];
    switch(kind) {
      case 0:++b.widget;break;case 1:++b.vtable;break;case 2:++b.context;break;
      case 3:++b.callbacks[0].object;break;case 4:++b.callbacks[0].receiver;break;
      case 5:++b.callbacks[0].chain_user_data[0];break;case 6:++b.ancestors[1];break;
      case 7:b.ancestor_flags[0]=8;break;case 8:++f.source.frame.date_raw;break;
      case 9:++f.source.frame.connection_generation;break;case 10:++b.callback_data;break;
      case 11:b.row.enabled=false;break;
    }
    assert(ActivateScriptedWidgetControl12004(p,f.backend(),r.query_generation,2,r));
    assert(!r.available&&!r.dispatch_attempted&&f.calls==0);
  }
}
}
int main(int argc, char **argv) {
  if (argc == 2 && std::string_view(argv[1]) == "--wire-fixtures") {
    Fixture f; ScriptedWidgetProvider12004 p; ScriptedWidgetResult12004 r; Query(f,p,r);
    std::cout << SerializeScriptedWidgetControl12004(r) << '\n';
    assert(ActivateScriptedWidgetControl12004(p,f.backend(),r.query_generation,2,r) && r.available);
    std::cout << SerializeScriptedWidgetControl12004(r) << '\n';
    Query(f,p,r); f.dispatch_ok=false;
    assert(ActivateScriptedWidgetControl12004(p,f.backend(),r.query_generation,2,r) && r.dispatch_attempted && !r.available);
    std::cout << SerializeScriptedWidgetControl12004(r) << '\n';
    return 0;
  }
  assert(ScriptedWidgetRootName12004("rrf_fusion_window"));assert(!ScriptedWidgetRootName12004("../window"));
  assert(!ScriptedWidgetRootName12004(""));assert(!ScriptedWidgetRootName12004("0root"));
  std::uint64_t id=0;assert(ParseScriptedWidgetOpaqueId12004("18446744073709551615",id)&&id==UINT64_MAX);
  for(auto s:{"0","01","-1","+1","1.0","true","18446744073709551616","1 "})assert(!ParseScriptedWidgetOpaqueId12004(s,id));
  Fixture f;ScriptedWidgetProvider12004 p;ScriptedWidgetResult12004 r;Query(f,p,r);
  const auto gen=r.query_generation;
  assert(ActivateScriptedWidgetControl12004(p,f.backend(),gen+1,2,r)&&!r.available&&f.calls==0);
  assert(ActivateScriptedWidgetControl12004(p,f.backend(),gen,0,r)&&!r.available&&f.calls==0);
  assert(ActivateScriptedWidgetControl12004(p,f.backend(),gen,1,r)&&!r.available&&f.calls==0);
  assert(ActivateScriptedWidgetControl12004(p,f.backend(),gen,2,r)&&r.available&&r.dispatch_invoked&&r.dispatch_attempted&&r.verification_pending&&!r.native_handled&&f.calls==1);
  assert(ActivateScriptedWidgetControl12004(p,f.backend(),gen,2,r)&&!r.available&&f.calls==1);
  Query(f,p,r);const auto newer=r.query_generation;assert(newer>gen);
  f.dispatch_ok=false;assert(ActivateScriptedWidgetControl12004(p,f.backend(),newer,2,r)&&!r.available&&r.dispatch_attempted&&r.verification_pending);
  assert(r.unavailable_reason=="scripted_widget_dispatch_unknown_no_retry");
  const auto calls=f.calls;assert(ActivateScriptedWidgetControl12004(p,f.backend(),newer,2,r)&&!r.available&&f.calls==calls);
  Fixture unstable;unstable.change_second=true;assert(QueryScriptedWidgetControls12004(p,unstable.backend(),"custom_mod_window",r)&&!r.available&&!p.valid&&r.widgets.empty()&&r.query_generation==0);
  Fixture truncated;truncated.source.truncated=true;assert(QueryScriptedWidgetControls12004(p,truncated.backend(),"custom_mod_window",r)&&!r.available&&r.truncated&&r.widgets.empty()&&r.query_generation==0);
  Fixture failed;failed.capture_ok=false;assert(QueryScriptedWidgetControls12004(p,failed.backend(),"custom_mod_window",r)&&!r.available&&r.frame.game_pid==321&&r.widgets.empty());
  p.query_generation=UINT64_MAX;assert(QueryScriptedWidgetControls12004(p,f.backend(),"custom_mod_window",r)&&!r.available&&r.query_generation==0&&!p.valid);
  IdentityChanges();
  ScriptedWidgetResult12004 wire{};wire.action=true;wire.query_generation=UINT64_MAX;wire.widget_id=9007199254740993ULL;
  const auto json=SerializeScriptedWidgetControl12004(wire);
  assert(json.find("\"query_generation\":\"18446744073709551615\"")!=std::string::npos);
  assert(json.find("\"widget_id\":\"9007199254740993\"")!=std::string::npos);
  assert(json.find("\"postcondition_verified\":false")!=std::string::npos);
  assert(json.find("\"step\":\"activate-scripted-widget-control-v1\"")!=std::string::npos);
  std::cout<<"scripted widget production reducer and wire regressions passed\n";
}
