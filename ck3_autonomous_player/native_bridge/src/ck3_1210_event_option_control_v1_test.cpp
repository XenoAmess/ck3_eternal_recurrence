#include "xar_bridge/ck3_1210_event_option_control_v1.hpp"
#include <cstdlib>
#include <iostream>
namespace {
using namespace xar::ck3_1210;
void Require(bool v,const char *s){if(!v){std::cerr<<"FAIL "<<s<<'\n';std::exit(1);}}
std::string Request(std::string_view step="select-event-option-2",std::string_view event_id="42") {
  return "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"event-option-test\",\"step\":\""+
      std::string(step)+"\",\"expected_revision\":7,\"event_option_control\":{\"schema\":\""+
      kEventOptionClaimSchemaV1+"\",\"game_version\":\""+kGameVersion+"\",\"executable_sha256\":\""+
      kExecutableSha256+"\",\"adapter_id\":\""+kAdapterId+"\",\"backend\":\""+kCoreBackendV1+
      "\",\"snapshot_id\":\"native:7\",\"native_revision\":7,\"deadline_unix_ms\":2000},\"arguments\":{\"event_instance_id\":"+
      std::string(event_id)+"}}";
}
void Replace(std::string &s,std::string_view from,std::string_view to){
  const auto pos=s.find(from);Require(pos!=std::string::npos,"test mutation target");s.replace(pos,from.size(),to);
}
std::uint64_t Clock(void *p)noexcept{return *static_cast<std::uint64_t *>(p);}
}
int main(int argc,char **argv){
  using namespace xar::ck3_1210;EventOptionRequestV1 out{};
  auto source=Request();Require(ParseEventOptionRequestV1(source,out)&&out.select&&out.native_revision==7&&
      out.event_instance_id==42&&out.native_option_index==1,"public one-based step maps exact zero-based native identity");
  auto query=Request(kEventOptionsQueryStepV1);Require(ParseEventOptionRequestV1(query,out)&&!out.select&&out.native_option_index==-1,"query parsed");
  for(const auto step:{"select-event-option--1","select-event-option-0","select-event-option-02","select-event-option-513","select-event-option-2x","select-event-option-2.0"}){
    auto bad=Request(step);Require(!ParseEventOptionRequestV1(bad,out),"invalid index closed");
  }
  {auto limit=Request("select-event-option-512");Require(ParseEventOptionRequestV1(limit,out)&&out.native_option_index==511,"inclusive public bound");}
  for(const auto event:{"true","0","-1","42.0","2147483648","null","\"42\""}){
    auto bad=Request("select-event-option-2",event);Require(!ParseEventOptionRequestV1(bad,out),"event full int32 required");
  }
  for(const auto pair:{std::pair{"\"native_revision\":7","\"native_revision\":8"},
      std::pair{"\"snapshot_id\":\"native:7\"","\"snapshot_id\":\"native:07\""},
      std::pair{"\"expected_revision\":7","\"expected_revision\":true"},
      std::pair{"\"event_instance_id\":42","\"event_instance_id\":42,\"unused\":1"},
      std::pair{"\"event_instance_id\":42","\"event_instance_id\":42,\"event_instance_id\":42"},
      std::pair{"ck3_1210_event_option_control_v1","ck3_1210_full_snapshot_clock_control_v1"}}){
    auto bad=Request();Replace(bad,pair.first,pair.second);Require(!ParseEventOptionRequestV1(bad,out),"duplicate/unknown/false claim closed");
  }
  EventOptionControlContextV1 c{};std::uint64_t clock=1000;c.wall_clock=&Clock;c.monotonic_clock=&Clock;c.clock_context=&clock;
  c.request.deadline_unix_ms=2000;ArmEventOptionDeadlineV1(c);Require(c.monotonic_deadline_ms==2000,"bounded original deadline");
  c.request.deadline_unix_ms=1000;ArmEventOptionDeadlineV1(c);Require(c.monotonic_deadline_ms==0,"expired deadline not refreshed");
  Require(!ExecuteEventOptionControlMailboxV1(nullptr,{}),"missing context never dispatches");
  Require(ExecuteEventOptionControlMailboxV1(&c,{})&&!c.result.effect_attempted&&!c.result.application_main_observed,"missing custody zero dispatch");
  source=Request();Require(ParseEventOptionRequestV1(source,out),"select reparsed");
  EventOptionResultV1 result{};result.status=EventOptionStatusV1::submitted;result.application_main_observed=true;
  result.full_snapshot_before_verified=true;result.effect_attempted=true;result.unavailable_reason={};
  result.observation.count=2;result.observation.rows[0]={0,true};result.observation.rows[1]={1,true};
  const auto emitted=SerializeEventOptionCommandResultV1("event-option-test",out,result);
  Require(emitted.find("\"native_revision\":7")!=std::string::npos &&
      emitted.find("\"event_instance_id\":42")!=std::string::npos &&
      emitted.find("\"effect_attempted\":true")!=std::string::npos,"wire retains claimed correlation");
  if(argc==2&&std::string_view(argv[1])=="--emit-cases") {
    Replace(source,"\"expected_revision\":7","\"expected_revision\":11");
    Replace(source,"\"native_revision\":7","\"native_revision\":11");
    Replace(source,"native:7","native:11");
    Require(ParseEventOptionRequestV1(source,out),"original signed Full revision11 select");
    std::cout<<SerializeEventOptionCommandResultV1("event-option-test",out,result)<<'\n';
    query=source;Replace(query,"select-event-option-2",kEventOptionsQueryStepV1);
    Require(ParseEventOptionRequestV1(query,out),"query reparsed");
    result.status=EventOptionStatusV1::available;result.effect_attempted=false;
    std::cout<<SerializeEventOptionCommandResultV1("event-option-test",out,result)<<'\n';
    Require(ParseEventOptionRequestV1(source,out),"disabled select reparsed");
    result.status=EventOptionStatusV1::option_disabled;result.unavailable_reason="option_disabled";
    std::cout<<SerializeEventOptionCommandResultV1("event-option-test",out,result)<<'\n';return 0;
  }
  result.status=EventOptionStatusV1::stale_full_snapshot;result.effect_attempted=false;result.unavailable_reason="stale_full_snapshot";
  Require(SerializeEventOptionCommandResultV1("event-option-test",out,result).find("\"options\":[]")!=std::string::npos,"failure cannot retain options");
  std::cout<<"PASS exact event option wire, expiry, zero-dispatch and producer serialization\n";
}
