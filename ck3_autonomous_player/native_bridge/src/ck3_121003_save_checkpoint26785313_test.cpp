#include "xar_bridge/ck3_121003_save_checkpoint26785313_v1.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <stdexcept>

using namespace xar::ck3_121003::build26785313;
using Status=SaveCheckpointStatus267V1;
using Decision=SaveCheckpointClaimDecision267V1;
namespace {
SaveCheckpointRequest267V1 Request(std::string_view id,std::int32_t date=100) {
  SaveCheckpointRequest267V1 r;
  r.control.operation=xar::ck3_1210::CoreControlOperationV1::save;r.control.step=kSaveCheckpointStep267V1;
  r.control.deadline_unix_ms=9999999999999ULL;
  r.control.expected={{date,1,true},7,true,true,42,true};
  assert(id.size()<=96);std::copy(id.begin(),id.end(),r.request_id.begin());
  r.request_id_size=static_cast<std::uint8_t>(id.size());return r;
}
SaveCheckpointSource267V1 Source() {return {0x10000,0x20000,0x30000,1};}
std::string Wire() {
  return R"({"type":"execute_step","protocol_version":1,"request_id":"e1","step":"save-checkpoint","expected_revision":0,"core_checkpoint_save":{"schema":"ck3_121003_core_checkpoint_save_v1","game_version":"1.21.0.3","executable_sha256":"859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28","adapter_id":"ck3-1.21.0.3-26785313-msvc-x64","backend":"ck3-1.21.0.3-native-headless-main-thread","date_raw":100,"speed":1,"paused":true,"local_player_id":7,"map_ready":true,"has_played_character":true,"played_character_id":42,"played_character_alive":true},"core_control_deadline_unix_ms":9999999999999,"arguments":{}})";
}
std::string Replace(std::string text,std::string_view from,std::string_view to) {
  const auto at=text.find(from);assert(at!=std::string::npos);text.replace(at,from.size(),to);return text;
}
void Claims() {
  SaveCheckpointSession267V1 session;auto source=Source();auto e1=Request("e1");std::uint64_t sequence=99;
  assert(InspectSaveCheckpointClaim267V1(session,e1,source)==Decision::ready);
  assert(session.claim_count()==0); // Check alone is not consumed or submitted.
  assert(ClaimSaveCheckpoint267V1(session,e1,source,sequence)==Decision::ready&&sequence==1);
  assert(session.claim_count()==1);
  assert(InspectSaveCheckpointClaim267V1(session,Request("e2",101),source)==Decision::consumed);
  FinishSaveCheckpointClaim267V1(session,1,Status::submitted);
  assert(InspectSaveCheckpointClaim267V1(session,e1,source)==Decision::consumed);
  assert(InspectSaveCheckpointClaim267V1(session,Request("new-id-same-core"),source)==Decision::consumed);
  source.connection_generation=2;
  assert(InspectSaveCheckpointClaim267V1(session,Request("reconnect-same-core"),source)==Decision::consumed);
  auto e2=Request("e2",101);
  assert(ClaimSaveCheckpoint267V1(session,e2,source,sequence)==Decision::ready&&sequence==2);
  FinishSaveCheckpointClaim267V1(session,2,Status::submitted);
  assert(InspectSaveCheckpointClaim267V1(session,Request("e1",102),source)==Decision::consumed);
  assert(InspectSaveCheckpointClaim267V1(session,Request("old-date",99),source)==Decision::consumed);
  auto changed=source;changed.game_state++;
  assert(InspectSaveCheckpointClaim267V1(session,Request("changed-source",102),changed)==Decision::source_changed);
  auto actor=Request("changed-actor",102);actor.control.expected.played_character_id++;
  assert(InspectSaveCheckpointClaim267V1(session,actor,source)==Decision::source_changed);
}
void Unknown() {
  SaveCheckpointSession267V1 session;std::uint64_t sequence=0;auto source=Source();
  assert(ClaimSaveCheckpoint267V1(session,Request("unknown"),source,sequence)==Decision::ready);
  FinishSaveCheckpointClaim267V1(session,sequence,Status::indeterminate);assert(session.unknown_blocked());
  source.connection_generation=3;
  assert(InspectSaveCheckpointClaim267V1(session,Request("changed-id",101),source)==Decision::consumed);
  SaveCheckpointSession267V1 clone_fault;BlockSaveCheckpointUnknown267V1(clone_fault);
  assert(InspectSaveCheckpointClaim267V1(clone_fault,Request("new-after-clone-fault"),source)==Decision::consumed);
}
void Capacity() {
  SaveCheckpointSession267V1 session;std::uint64_t sequence=0;const auto source=Source();
  for(std::size_t i=0;i<kSaveCheckpointRetainedClaims267V1;++i) {
    const auto id=std::string("save-")+std::to_string(i);
    assert(ClaimSaveCheckpoint267V1(session,Request(id,100+static_cast<std::int32_t>(i)),source,sequence)==Decision::ready);
    FinishSaveCheckpointClaim267V1(session,sequence,Status::submitted);
  }
  assert(InspectSaveCheckpointClaim267V1(session,Request("no-eviction",200),source)==Decision::capacity_exhausted);
}
void ParsingAndWire() {
  SaveCheckpointRequest267V1 parsed;const auto wire=Wire();assert(ParseSaveCheckpointRequest267V1(wire,parsed));
  assert(parsed.id()=="e1"&&parsed.control.expected.clock.date_raw==100);
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"expected_revision\":0","\"expected_revision\":1"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"paused\":true","\"paused\":false"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"speed\":1","\"speed\":6"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"arguments\":{}","\"arguments\":{\"save_name\":\"other\"}"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"core_checkpoint_save","core_clock_control"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"1.21.0.3","1.21.0.0"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"859F0D38","259F0D38"),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"request_id\":\"e1\"","\"request_id\":\"e1\",\"request_id\":\"e2\""),parsed));
  assert(!ParseSaveCheckpointRequest267V1(Replace(wire,"\"date_raw\":100","\"date_raw\":2147483648"),parsed));
  SaveCheckpointResult267V1 r;r.status=Status::submitted;r.effect_attempted=true;r.submission_sequence=1;r.observed=Request("source").control.expected;
  const auto out=SerializeSaveCheckpointResult267V1("e1",r);
  assert(out.find("\"ok\":true")!=std::string::npos);
  assert(out.find("\"physical_save_confirmed\":false")!=std::string::npos);
  assert(out.find("xar_checkpoint.ck3")!=std::string::npos);
  assert(out.find("\"submission\":{\"sequence\":1")!=std::string::npos);
  r.status=Status::indeterminate;
  const auto unknown=SerializeSaveCheckpointResult267V1("e1",r);
  assert(unknown.find("\"ok\":false")!=std::string::npos&&unknown.find("\"submission\":")==std::string::npos);
  r.status=Status::submitted;r.submission_sequence=0;
  const auto incomplete=SerializeSaveCheckpointResult267V1("e1",r);
  assert(incomplete.find("\"queue_status\":\"indeterminate\"")!=std::string::npos);
  assert(incomplete.find("\"ok\":false")!=std::string::npos);
}
} // namespace
int main(int argc,char**argv) {
  Claims();Unknown();Capacity();ParsingAndWire();
  SaveCheckpointContext267V1 off;const xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  assert(ExecuteSaveCheckpointOnOwner267V1(&off,stamp));
  assert(off.result.status==Status::unavailable&&!off.result.effect_attempted);

  if(argc==3&&std::string_view(argv[1])=="--emit-save-fixtures") {
    const std::filesystem::path dir=argv[2];std::filesystem::create_directories(dir);
    const auto write=[&](const char*name,const std::string&data){std::ofstream out(dir/name,std::ios::binary);if(!out)throw std::runtime_error("producer open");out<<data<<'\n';if(!out)throw std::runtime_error("producer write");};
    const auto request=Replace(Wire(),"\"date_raw\":100","\"date_raw\":53144400");
    const auto request2=Replace(Replace(request,"\"request_id\":\"e1\"","\"request_id\":\"e2\""),"\"date_raw\":53144400","\"date_raw\":53144424");
    SaveCheckpointRequest267V1 parsed;assert(ParseSaveCheckpointRequest267V1(request,parsed));
    SaveCheckpointResult267V1 result;result.status=Status::submitted;result.effect_attempted=true;result.submission_sequence=1;result.observed=parsed.control.expected;
    write("request.json",request);write("submitted.json",SerializeSaveCheckpointResult267V1("e1",result));
    result.status=Status::indeterminate;write("indeterminate.json",SerializeSaveCheckpointResult267V1("e1",result));
    result.status=Status::rejected;write("rejected.json",SerializeSaveCheckpointResult267V1("e1",result));
    write("unavailable.json",SerializeSaveCheckpointResult267V1("e1",{}));
    assert(ParseSaveCheckpointRequest267V1(request2,parsed));result.status=Status::submitted;result.effect_attempted=true;result.submission_sequence=2;result.observed=parsed.control.expected;
    write("request-e2.json",request2);write("submitted-e2.json",SerializeSaveCheckpointResult267V1("e2",result));
    write("qualifier.json",R"({"scope":"Actual C++ production parser/serializer and claim-state tests, SYNTHETIC DATA / NoGame. Synthetic actor42/local7; dates match planned E1/E2+24 only and are not live observations.","producer_source":"ck3_121003_save_checkpoint26785313_wire_v1.cpp","production_handler_ON_owner_Bridge":"NOT_QUALIFIED_BY_THIS_OFF_TARGET","NativeCommand_MainOwner_actualSAVE_physicalSAVE":"NOT_RUN","physical_save_confirmed":false})");
  }else assert(argc==1);

  std::cout<<"synthetic claim/parser/wire only; no native command, owner, or physical SAVE\n";
}
