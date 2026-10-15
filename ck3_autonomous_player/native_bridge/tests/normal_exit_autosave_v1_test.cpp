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
    if(argc==2) {
      std::filesystem::path output{argv[1]};std::filesystem::create_directories(output);
      std::ofstream(output/"disable-request.json",std::ios::binary)<<request;
      std::ofstream(output/"autosave-observation.json",std::ios::binary)<<wire;
    }
    std::cout<<"normal-exit autosave policy/parser/serializer PASS checks="<<checks<<'\n';
    return 0;
  } catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 1;}
}
