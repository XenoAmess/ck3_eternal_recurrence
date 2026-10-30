#include "xar_bridge/normal_exit_map_v1.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

using namespace xar::ck3_12003;
namespace {
int checks=0;
void Check(bool value,const char *why) {
  ++checks;if(!value) throw std::runtime_error(why);
}
NormalExitAutosaveV1 Ready(bool save) {
  NormalExitAutosaveV1 value{};value.state_available=true;
  value.control_visible=true;value.control_enabled=true;value.should_save=save;
  return value;
}
}
bool ClaimedByBridge(const NormalExitMapObservationV1 &observation) {
  return NormalExitMapClaimLatchedV1(observation);
}
void AutosaveClaimPropagation() {
  bool all=true;
  const auto verify=[&](bool value,const char *name) {
    ++checks;if(!value){all=false;std::cerr<<"claim_boundary_failure: "<<name<<'\n';}
  };
  for(int failure=0;failure<3;++failure) {
    auto state=Ready(true),expected=state;std::atomic<bool> claim{false};
    int calls=0,reads=0;NormalExitAutosaveV1 out{};
    const auto read=[&](auto &value){value=state;++reads;return failure!=1 || reads==1;};
    const auto toggle=[&]{++calls;if(failure==2)state.should_save=false;return failure!=0;};
    const bool disabled=DisableNormalExitAutosaveV1(claim,expected,read,toggle,out);
    verify(claim.load() && out.disable_claimed && out.dispatch_invoked && calls==1,"actual toggle producer claims before dispatch");
    verify(disabled==(failure==2),"producer distinguishes successful readback");
    NormalExitMapObservationV1 observation{};
    observation.action=NormalExitMapActionV1::disable_exit_autosave;observation.exit_autosave=out;
    observation.status=disabled?NormalExitMapStatusV1::autosave_disabled:NormalExitMapStatusV1::dispatch_unknown_claimed;
    const bool classified=ClaimedByBridge(observation);
    std::cout<<"autosave_case="<<failure<<" producer_claimed="<<out.disable_claimed<<" bridge_claimed="<<classified<<'\n';
    verify(classified,"lost mailbox/final-frame completion retains autosave UNKNOWN");
    const auto wire=SerializeNormalExitMapObservationV1(observation);
    verify(wire.find("\"autosave_verified\":false")!=std::string::npos &&
        wire.find("\"orderly_exit_verified\":false")!=std::string::npos,"no save or exit proof from claim");
    verify(!DisableNormalExitAutosaveV1(claim,expected,read,toggle,out) && calls==1,"unknown/no changed stale expected cannot replay");
  }
  {
    auto state=Ready(false);std::atomic<bool> claim{false};NormalExitMapObservationV1 observation{};
    observation.action=NormalExitMapActionV1::disable_exit_autosave;int calls=0;
    verify(DisableNormalExitAutosaveV1(claim,state,[&](auto &out){out=state;return true;},
        [&]{++calls;return true;},observation.exit_autosave),"already false freshly observed");
    verify(calls==0 && !ClaimedByBridge(observation),"no invocation does not invent a mutation claim");
  }
  {
    auto state=Ready(true);std::atomic<bool> claim{true};NormalExitMapObservationV1 observation{};
    observation.action=NormalExitMapActionV1::disable_exit_autosave;int calls=0;
    verify(!DisableNormalExitAutosaveV1(claim,state,[&](auto &out){out=state;return true;},
        [&]{++calls;return true;},observation.exit_autosave),"retained consumed claim refuses dispatch");
    verify(calls==0 && ClaimedByBridge(observation),"retained unknown is still reported without replay");
    observation.action=NormalExitMapActionV1::query_context;
    verify(!ClaimedByBridge(observation),"read-only query is not a newly claimed mutation");
  }
  for(std::size_t stage=0;stage<3;++stage) {
    NormalExitMapObservationV1 observation{};observation.dispatches[stage].claim_latched=true;
    verify(ClaimedByBridge(observation),"existing stage claim remains represented");
  }
  {
    NormalExitMapObservationV1 observation{};observation.action=NormalExitMapActionV1::disable_exit_autosave;
    observation.exit_autosave.dispatch_invoked=true;
    verify(!ClaimedByBridge(observation),"dispatch flag without claim is not custody");
  }
  Check(all,"actual Native autosave producer to bridge claim boundary");
}

int main(int argc,char **argv) {
  try {
    for(bool initial:{false,true}) {
      auto state=Ready(initial);const auto expected=state;
      std::atomic<bool> claim{false};int calls=0;NormalExitAutosaveV1 out{};
      auto read=[&](auto &value){value=state;return true;};
      auto toggle=[&]{++calls;state.should_save=!state.should_save;return true;};
      Check(DisableNormalExitAutosaveV1(claim,expected,read,toggle,out),"disable readback");
      Check(!out.should_save && out.postcondition_observed,"actual false");
      Check(calls==(initial?1:0),"false never toggles true");
      Check(claim.load()==initial,"claim only a native toggle");
      Check(DisableNormalExitAutosaveV1(claim,state,read,toggle,out),"idempotent fresh false");
      Check(calls==(initial?1:0) && !state.should_save,"idempotent no toggle");
    }
    for(int defect=0;defect<5;++defect) {
      auto state=Ready(true),expected=state;
      std::atomic<bool> claim{false};int calls=0;NormalExitAutosaveV1 out{};
      if(defect==0)state.state_available=false;
      if(defect==1)state.control_visible=false;
      if(defect==2)state.control_enabled=false;
      if(defect==3)state.should_save=false;
      auto read=[&](auto &value){value=state;return defect!=4;};
      Check(!DisableNormalExitAutosaveV1(claim,expected,read,[&]{++calls;return true;},out),"drift/unavailable rejected");
      Check(calls==0 && !claim.load(),"no mutation before admission");
    }
    for(int defect=0;defect<3;++defect) {
      auto state=Ready(true),expected=state;
      std::atomic<bool> claim{false};int calls=0,reads=0;NormalExitAutosaveV1 out{};
      auto read=[&](auto &value){value=state;return !(defect==1 && ++reads>1);};
      auto toggle=[&]{++calls;return defect!=0;}; // no actual false readback
      Check(!DisableNormalExitAutosaveV1(claim,expected,read,toggle,out),"unknown not success");
      Check(claim.load() && calls==1 && !out.postcondition_observed,"unknown claim retained");
      Check(!DisableNormalExitAutosaveV1(claim,expected,read,toggle,out),"unknown cannot replay");
      Check(calls==1,"no second native invocation");
    }
    const std::string request=R"({"type":"execute_step","protocol_version":1,"request_id":"exit-disable-1","step":"normal-exit-map-v1","action":"disable_exit_autosave","expected_revision":72,"expected_player_character_id":9301,"expected_game_pid":43,"expected_connection_generation":8,"expected_process_creation_filetime_100ns":133000000000000043,"request_nonce":"nonce-1","source_inventory_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","expected_exit_context_signature":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"})";
    NormalExitMapRequestV1 parsed{};std::string reason;
    Check(ParseNormalExitMapRequestV1(request,parsed,reason),"new production wire parsed");
    Check(parsed.action==NormalExitMapActionV1::disable_exit_autosave,"semantic action exact");
    auto forged=request;forged.insert(forged.size()-1,",\"should_save\":true");
    Check(!ParseNormalExitMapRequestV1(forged,parsed,reason),"caller setting forbidden");
    NormalExitMapObservationV1 observation{};
    observation.action=NormalExitMapActionV1::disable_exit_autosave;
    observation.status=NormalExitMapStatusV1::autosave_disabled;
    observation.exit_autosave=Ready(false);observation.exit_autosave.postcondition_observed=true;
    const auto wire=SerializeNormalExitMapObservationV1(observation);
    Check(wire.find("\"status\":\"autosave_disabled\"")!=std::string::npos,"serializer status");
    Check(wire.find("\"should_save\":false")!=std::string::npos,"serializer false");
    Check(wire.find("\"autosave_verified\":false")!=std::string::npos,"no save integrity credit");
    AutosaveClaimPropagation();
    if(argc==2) {
      std::filesystem::path output{argv[1]};std::filesystem::create_directories(output);
      std::ofstream(output/"disable-request.json",std::ios::binary)<<request;
      std::ofstream(output/"autosave-observation.json",std::ios::binary)<<wire;
    }
    std::cout<<"normal-exit autosave policy/parser/serializer PASS checks="<<checks<<'\n';
    return 0;
  } catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 1;}
}
