#include "xar_bridge/ck3_12002_event_window_context_v2.hpp"
#include "support/event_window_owned_fixture_v2.hpp"
#include <fstream>
#include <cstdlib>
extern unsigned g_unused_outer_calls90;
namespace {
#include "support/event_window_stock_gui_code_v2.hpp"
bool g_owning90=true;
unsigned g_ambiguous_gate_calls90=0;
bool AmbiguousGate90(const void*,const void*) {
  ++g_ambiguous_gate_calls90;return true;
}
bool Owning90(void *context) noexcept {return context==&g_owning90&&g_owning90;}
bool Prefix90(const xar::ck3_12002::EventWindowBindings&,
              xar::game::Snapshot& out) noexcept {
  out={};out.date_raw=741221;out.paused=true;out.map_ready=true;
  out.player_id=0;out.has_played_character=true;
  out.played_character_id=kCharacterId;out.played_character_alive=true;
  out.has_active_event=true;out.active_event_instance_id=kEventId;
  return true;
}
std::string g_packet_root;
void Write90(const char *name,const char *suffix,const std::string& text){
  Require90(!text.empty(),"serializerempty");
  if(g_packet_root.empty())return;
  std::ofstream file(g_packet_root+"/"+name+suffix,std::ios::binary);
  file<<text;Require90(file.good(),"artifactwrite");
}
void ObserveV290(const Stock90& stock,const char* name,double timer,
                 bool callback_accept,bool enabled,bool fallback,
                 bool expected_stock,int unobserved=0){
  Fixture fixture;fixture.InitializeOption(0,0,enabled,fallback);
  fixture.bindings.read_observation_prefix=&Prefix90;
  Store<void*>(fixture.option_items.data(),0x88,nullptr);
  Store<std::int32_t>(fixture.option_items.data(),0x90,0);
  Store<std::int32_t>(fixture.option_items.data(),0x94,0);
  auto *owner=fixture.window.data()+0xB8;Store<double>(owner,8,timer);
  std::array<std::uintptr_t,4> vptr{};
  vptr[3]=reinterpret_cast<std::uintptr_t>(&Predicate90);
  Callback90 callback{&vptr,callback_accept,0};Pair90 pair{&callback,nullptr};
  Store<void*>(owner,0x730,&pair);Store<std::int32_t>(owner,0x738,1);
  Store<std::int32_t>(owner,0x73C,1);
  xar::game::EventWindowContextV1 legacy;
  Require90(xar::ck3_12002::ReadEventWindowContextV1(fixture.bindings,kRevision,kEventId,legacy)==xar::game::ReadEventWindowContextResultV1::available,"realv1reader");
  Require90(callback.calls==0,"legacycalledGUI");
  const auto v1=xar::ck3_12002::SerializeEventWindowContextV1(legacy);
  Require90(v1.find("current-event-window-context-v1")!=std::string::npos&&v1.find("\"schema_version\":1")!=std::string::npos,"realv1wire");
  Require90(v1.find("gui_availability")==std::string::npos,"v1guiadded");
  xar::ck3_12002::EventWindowGuiBindingsV2 bindings{};
  bindings.presentation=fixture.bindings;
  bindings.read_owner_gate=unobserved==1?nullptr:
      reinterpret_cast<xar::ck3_12002::EventGuiOwnerGateV2>(stock.code);
  g_owning90=unobserved!=2;
  xar::ck3_12002::EventWindowGuiAccessV2 access{&g_owning90,&Owning90};
  xar::game::EventWindowContextV2 result;
  const auto actual=xar::ck3_12002::ReadEventWindowContextV2(
      bindings,access,kRevision,kEventId,result);
  Require90(actual==xar::game::ReadEventWindowContextResultV1::available&&
      result.presentation==legacy&&result.gui_observations.size()==1,
      "actualv2fullreader");
  const auto& observation=result.gui_observations.front();
  Require90(observation.rendered_index==0&&observation.native_option_index==0,
      "observationbinding");
  if(unobserved==0){
    const auto *value=std::get_if<xar::game::EventGuiAvailabilityObservedV2>(
        &observation.gui_availability);
    Require90(value&&value->is_valid==expected_stock,"observedvalidity");
    const unsigned observed_calls=callback.calls;callback.calls=0;
    Require90(stock.Invoke(fixture.option_items.data())==value->is_valid,
        "originalstockadaptermismatch");
    Require90(observed_calls==callback.calls,"stockshortcircuitcalls");
  }else{
    const auto *value=std::get_if<xar::game::EventGuiAvailabilityUnobservedV2>(
        &observation.gui_availability);
    const auto reason=unobserved==1?
        xar::game::EventGuiAvailabilityFailureV2::native_binding_unavailable:
        xar::game::EventGuiAvailabilityFailureV2::native_read_unavailable;
    Require90(value&&value->reason==reason&&callback.calls==0,"unobservedcalledGUI");
  }
  Require90(result.presentation.options.front().enabled==enabled&&
      result.presentation.options.front().fallback==fallback&&
      g_unused_outer_calls90==0,"rawflagsorunusedseams");
  Require90(xar::ck3_12002::SerializeEventWindowContextV1(result.presentation)==v1,"samepresentationv1bytes");
  const auto v2=xar::ck3_12002::SerializeEventWindowContextV2(result);
  Require90(v2.find("current-event-window-context-v2")!=std::string::npos&&
      v2.find("\"schema_version\":2")!=std::string::npos,"version2");
  Write90(name,".v1.json",v1);Write90(name,".v2.json",v2);
  auto malformed=result;malformed.gui_observations.clear();
  Require90(xar::ck3_12002::SerializeEventWindowContextV2(malformed).empty(),"missingobservationaccepted");
  malformed=result;malformed.gui_observations.front().native_option_index=1;
  Require90(xar::ck3_12002::SerializeEventWindowContextV2(malformed).empty(),"wrongrowaccepted");
  std::cout<<"{\"case\":\""<<name<<"\",\"full_candidate_reader\":true,\"v1_baseline_equal\":true,\"raw_enabled\":"<<(enabled?"true":"false")
      <<",\"fallback\":"<<(fallback?"true":"false")<<",\"observation\":\""<<(unobserved?"unobserved":"observed")<<"\",\"is_valid\":";
  if(unobserved)std::cout<<"null";else std::cout<<(expected_stock?"true":"false");
  std::cout<<",\"unused_outer_calls\":0}\n";
}
void AmbiguousV290(){
  Fixture fixture;fixture.InitializeOption(0,0,true,false);
  fixture.bindings.read_observation_prefix=&Prefix90;
  fixture.windows[1]=fixture.window.data();
  Store<std::int32_t>(fixture.manager.data(),0x24,2);
  xar::ck3_12002::EventWindowGuiBindingsV2 bindings{};
  bindings.presentation=fixture.bindings;bindings.read_owner_gate=&AmbiguousGate90;
  g_owning90=true;g_ambiguous_gate_calls90=0;
  xar::ck3_12002::EventWindowGuiAccessV2 access{&g_owning90,&Owning90};
  xar::game::EventWindowContextV2 result;
  const auto actual=xar::ck3_12002::ReadEventWindowContextV2(
      bindings,access,kRevision,kEventId,result);
  Require90(actual==xar::game::ReadEventWindowContextResultV1::unavailable&&
      result.presentation.unavailable_reason=="event_window_ambiguous"&&
      result.gui_observations.empty()&&g_ambiguous_gate_calls90==0,
      "ambiguouscalledGUI");
  xar::game::EventWindowContextV1 baseline;
  xar::ck3_12002::ReadEventWindowContextV1(
      fixture.bindings,kRevision,kEventId,baseline);
  Require90(result.presentation==baseline,"ambiguouslegacychanged");
  Write90("ambiguous-no-native-gate",".v2.json",
      xar::ck3_12002::SerializeEventWindowContextV2(result));
  std::cout<<"{\"case\":\"ambiguous-no-native-gate\",\"full_candidate_reader\":true,\"status\":\"unavailable\",\"native_gate_calls\":0,\"v1_baseline_equal\":true}\n";
}
void *g_named_rows=nullptr;
bool g_mutate_named=false;
unsigned g_named_gate_calls=0;
bool NamedGate04(const void*,const void* reason){
  Require90(reason==nullptr,"namedgatereason");++g_named_gate_calls;
  if(g_mutate_named)Store<std::uint64_t>(g_named_rows,0x10,44);
  return true;
}
void NamedScope04(bool mutate){
  Fixture fixture;fixture.InitializeOption(0,0,true,false);
  fixture.bindings.read_observation_prefix=&Prefix90;
  Store<std::uint64_t>(fixture.saved_scope_rows.data(),0x10,43);
  xar::game::EventWindowContextV1 v1;
  Require90(xar::ck3_12002::ReadEventWindowContextV1(fixture.bindings,kRevision,kEventId,v1)==xar::game::ReadEventWindowContextResultV1::available,"publishednamedscopev1");
  Require90(v1.saved_scopes.size()==2&&!v1.saved_scopes[0].scope.typed_identity.available&&
      !v1.saved_scopes[0].scope.typed_identity.character_id.has_value()&&
      v1.saved_scopes[0].scope.typed_identity.unavailable_reason=="character_scope_identity_unavailable","publishednamedidentityretained");
  const auto old=xar::ck3_12002::SerializeEventWindowContextV1(v1);
  Require90(old.find("character_scope_identity_unavailable")!=std::string::npos,"publishednamedserializer");
  xar::ck3_12002::EventWindowGuiBindingsV2 bindings{fixture.bindings,&NamedGate04};
  g_named_rows=fixture.saved_scope_rows.data();g_mutate_named=mutate;
  g_named_gate_calls=0;g_owning90=true;
  xar::ck3_12002::EventWindowGuiAccessV2 access{&g_owning90,&Owning90};
  xar::game::EventWindowContextV2 result;
  const auto read=xar::ck3_12002::ReadEventWindowContextV2(bindings,access,kRevision,kEventId,result);
  Require90(g_named_gate_calls==1&&g_unused_outer_calls90==0,"namedgatecallcount");
  const char *name=mutate?"named-character-token-drift":"named-character-identity-unavailable";
  if(mutate){
    Require90(read==xar::game::ReadEventWindowContextResultV1::unavailable&&
      result.presentation.unavailable_reason=="event_scope_changed"&&result.gui_observations.empty(),"publishedrawtokencomparison");
  }else{
    Require90(read==xar::game::ReadEventWindowContextResultV1::available&&result.presentation==v1&&
      xar::ck3_12002::SerializeEventWindowContextV1(result.presentation)==old,"publishednamedpresentation");
    Require90(std::get<xar::game::EventGuiAvailabilityObservedV2>(result.gui_observations.front().gui_availability).is_valid,"namedguiobserved");
    Write90(name,".v1.json",old);
  }
  Write90(name,".v2.json",xar::ck3_12002::SerializeEventWindowContextV2(result));
  std::cout<<"{\"case\":\""<<name<<"\",\"named_identity_retained\":true,\"raw_token_drift_rejected\":"<<(mutate?"true":"false")<<"}\n";
}
}
int main(int argc,char**argv){try{
  Require90(argc==1||argc==2,"optionalpacketdirectory");if(argc==2)g_packet_root=argv[1];
  const Stock90 stock;
  ObserveV290(stock,"timer-equal-raw-enabled",0.5,true,true,false,false);
  ObserveV290(stock,"callback-false-raw-enabled",1.0,false,true,false,false);
  ObserveV290(stock,"gate-passes-control",1.0,true,true,false,true);
  ObserveV290(stock,"raw-disabled-fallback-valid",1.0,true,false,true,true);
  ObserveV290(stock,"native-binding-unavailable",1.0,true,true,false,true,1);
  ObserveV290(stock,"native-read-unavailable",1.0,true,true,false,true,2);
  AmbiguousV290();
  NamedScope04(false);NamedScope04(true);
  std::cout<<"{\"paired_gate_cases\":4,\"unobserved_cases\":2,\"outer_unavailable_cases\":1,\"total_new_candidate_cases\":9,\"legacy_gui_calls\":0,\"original_engine_calls\":0,\"game_calls\":0}\n";
  return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
