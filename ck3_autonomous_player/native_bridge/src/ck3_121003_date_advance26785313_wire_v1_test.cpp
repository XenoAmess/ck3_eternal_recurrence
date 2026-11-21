#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <initializer_list>
#include <string>
namespace f=xar::ck3_121003::build26785313;
void Require(bool value,const char*message){if(!value){std::cerr<<message<<'\n';std::exit(1);}}
std::string Replace(std::string s,std::string_view before,std::string_view after){const auto at=s.find(before);Require(at!=std::string::npos,"test source anchor exists");s.replace(at,before.size(),after);return s;}
std::string Request(){
 return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"date-synthetic-1","step":"advance-date-one-day-v1","expected_revision":0,"arguments":{},"date_advance":{"schema":"ck3.current_date_advance_request.v1","game_version":"1.21.0.3","executable_sha256":")")+
 f::kExecutableSha256+R"(","adapter_id":"ck3-1.21.0.3-26785313-msvc-x64","backend":"ck3-1.21.0.3-native-headless-main-thread","deadline_unix_ms":4102444800000,"operation_id":"synthetic-e1","expected_core":{"date_raw":53144376,"speed":1,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":36423,"played_character_alive":true}}})";
}
f::DateAdvanceResult267V1 Synthetic(const f::DateAdvanceRequest267V1&r,bool complete){
 f::DateAdvanceResult267V1 result;result.status=complete?f::DateAdvanceStatus267V1::completed:f::DateAdvanceStatus267V1::submitted;
 result.claim_found=true;result.owner_before_verified=true;result.arm_attempted=true;result.resume_attempted=true;result.resume_submitted=true;
 result.claim_sequence=1;result.generation=1;result.connection_generation=7;result.ticket_sequence=8;result.pump_epoch=9;result.thread_id=10;
 result.core_before=r.expected_core;auto&s=result.sentinel;s.generation=1;s.mode=xar::ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel;
 s.starting_date_raw=r.expected_core.clock.date_raw;s.target_date_raw=s.starting_date_raw+24;s.speed=r.expected_core.clock.speed;
 s.state=complete?xar::ck3_11906::TacticalDailySentinelStateV1::triggered:xar::ck3_11906::TacticalDailySentinelStateV1::armed;
 s.last_observed_date_raw=complete?s.target_date_raw:s.starting_date_raw;s.trigger_date_raw=complete?s.target_date_raw:0;
 s.completed_daily_ticks=complete?1:0;s.trigger_flags=complete?xar::ck3_11906::tactical_daily_trigger_date_deadline:0;
 s.overshoot_days=0;s.pause_wrapper_called=complete;s.pause_observed=complete;
 result.exact_day_confirmed=complete;result.shutdown_safe=complete;result.armed=!complete;return result;
}
void Write(const std::filesystem::path&p,const std::string&bytes){Require(!std::filesystem::exists(p),"golden output must be new");std::ofstream out(p,std::ios::binary);out<<bytes;Require(bool(out),"golden bytes written");}
int main(int argc,char**argv){
 const auto input=Request();f::DateAdvanceRequest267V1 request;
 Require(f::ParseDateAdvanceRequest267V1(input,request)&&!request.status_query&&request.expected_core.clock.date_raw==53144376,"actual strict producer parser positive DATA");
 const auto queryInput=Replace(input,f::kDateAdvanceStep267V1,f::kDateAdvanceStatusStep267V1);f::DateAdvanceRequest267V1 query;
 Require(f::ParseDateAdvanceRequest267V1(queryInput,query)&&query.status_query&&query.operation()==request.operation(),"status retains original body and deadline");
 for(const auto&bad:std::initializer_list<std::string>{
  Replace(input,"\"paused\":true","\"paused\":1"),Replace(input,"\"map_ready\":true","\"map_ready\":false"),
  Replace(input,"\"played_character_id\":36423","\"played_character_id\":-1"),Replace(input,"\"speed\":1","\"speed\":6"),
  Replace(input,"53144376","2147483624"),Replace(input,"53144376","0"),Replace(input,"\"expected_revision\":0","\"expected_revision\":1"),
  Replace(input,"4102444800000","0"),Replace(input,"4102444800000","18446744073709551616"),
  Replace(input,"\"operation_id\":\"synthetic-e1\"","\"operation_id\":\"synthetic-e1\",\"operation_id\":\"another\""),
  Replace(input,"\"arguments\":{}","\"arguments\":{\"target_date_raw\":53144400}"),
  Replace(input,"\"date_raw\":53144376","\"date_raw\":53144376,\"date_raw\":53144376"),
  Replace(input,"\"schema\":\"ck3.current_date_advance_request.v1\"","\"schema\":\"ck3_1210_core_clock_control_v1\""),
  Replace(input,"\"backend\":\"ck3-1.21.0.3-native-headless-main-thread\"","\"backend\":\"ck3-1.21.0-native-headless-main-thread\""),
  Replace(input,"\"expected_core\":{","\"unknown\":true,\"expected_core\":{")}){
   auto failed=request;Require(!f::ParseDateAdvanceRequest267V1(bad,failed)&&failed.id().empty()&&failed.operation().empty(),"mistyped duplicate unknown legacy overflow request rejected and cleared");
 }
 // Production session cannot be opened by a caller state, fake Core, fixture,
 // boolean completion receipt or changed ID. No OS/Game dispatch occurs here.
 f::DateAdvanceSession267V1 session;xar::ck3_1210::DateSentinelStateV1 inactive;
 Require(!f::BindDateAdvanceSession267V1(session,inactive)&&!f::DateAdvanceRuntimeMatches267V1(session,inactive),"uninitialized source cannot bind production session");
 inactive.initialized.store(true);inactive.fixture_only=true;
 Require(!f::BindDateAdvanceSession267V1(session,inactive),"fixture runtime cannot bind production session");
 inactive.fixture_only=false;inactive.bindings.runtime_profile=xar::ck3_1210::DateSentinelRuntimeProfileV1::current26785313;
 Require(!f::BindDateAdvanceSession267V1(session,inactive),"profile enum without fixed actual access context cannot bind");
 auto noClaim=Synthetic(request,false);Require(!f::ClaimDateAdvance267V1(session,request,{1,2,3},noClaim),"fake source cannot claim unbound production session");
 Require(!f::QueryDateAdvance267V1(session,query,inactive).claim_found,"unbound status cannot manufacture claim");
 const auto completed=Synthetic(query,true);const auto good=f::SerializeDateAdvanceResult267V1(query.id(),query,completed);
 Require(good.find("\"exact_day_confirmed\":true")!=std::string::npos&&good.find("\"core_after\":null")!=std::string::npos,"serializer exposes exact SYNTHETIC DATA without fresh Core or Save");
 auto bad=completed;bad.sentinel.terminal_observed=true;
 Require(f::SerializeDateAdvanceResult267V1(query.id(),query,bad).find("\"exact_day_confirmed\":false")!=std::string::npos,"combat terminal cannot masquerade as date completion");
 bad=completed;bad.access_cleanup_unknown=true;Require(f::SerializeDateAdvanceResult267V1(query.id(),query,bad).find("\"status\":\"indeterminate\"")!=std::string::npos,"unknown cleanup refuses completion");
 bad=completed;bad.sentinel.last_observed_date_raw+=24;Require(f::SerializeDateAdvanceResult267V1(query.id(),query,bad).find("\"exact_day_confirmed\":false")!=std::string::npos,"overshoot refuses completion");
 bad=completed;bad.thread_id=0;Require(f::SerializeDateAdvanceResult267V1(query.id(),query,bad).find("\"owner_before_verified\":false")!=std::string::npos,"no zero thread witness");
 if(argc==3&&std::string_view(argv[1])=="--emit-date-advance-fixtures"){
  const auto dir=std::filesystem::path(argv[2]);Require(std::filesystem::create_directories(dir),"new owned fixture directory required");
  Write(dir/"request-advance-v1.json",input);Write(dir/"request-status-v1.json",queryInput);
  Write(dir/"submitted-SYNTHETIC-DATA.json",f::SerializeDateAdvanceResult267V1(request.id(),request,Synthetic(request,false)));
  Write(dir/"completed-SYNTHETIC-DATA.json",good);
  Write(dir/"unavailable-NoGame.json",f::SerializeDateAdvanceResult267V1(request.id(),request,{}));
  bad=Synthetic(request,false);bad.status=f::DateAdvanceStatus267V1::indeterminate;bad.resume_submitted=false;bad.access_cleanup_unknown=true;
  Write(dir/"indeterminate-SYNTHETIC-DATA.json",f::SerializeDateAdvanceResult267V1(request.id(),request,bad));
  Write(dir/"qualifier.json",R"({"machine_id":"desktop-3fevhd2-1c74096080","producer":"C++ wire DATA only","game":"NOT_RUN","owner":"NOT_RUN","postday":"NOT_RUN","physicalSave":"NOT_RUN"})");
 }else Require(argc==1,"only finite QA fixture emission option is supported");
 std::cout<<"PASS finite strict parser/serializer DATA; production binding and actual clock/PostDay/physicalSave NOT_RUN\n";
}
