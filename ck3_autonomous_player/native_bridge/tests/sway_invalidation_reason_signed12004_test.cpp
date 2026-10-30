// Actual production reader/recorder/handler/mailbox/serializer route. Only native memory I/O is owned.
// NativeAdapter seam is the real non-WorkerAdapter result; no WorkerAdapter is instantiated.
// Timeline core-frame seam aborts and must remain uncalled by this full-snapshot reason query.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include <atomic>
#include <bit>
#include <chrono>
#include <limits>
#include <thread>
#include <windows.h>

#include "sway_invalidation_reason_signed_world.inc"

namespace {
namespace native=xar::ck3_12002;
namespace actual4=xar::ck3_12004;
namespace api=xar::ck3_11906;
#include "sway_invalidation_reason_signed_frame_adapter.inc"
std::int32_t current_actor=0,current_target=0;
void *reason_tls_context=nullptr;
unsigned unexpected_calls=0;
void *__fastcall ReasonTls() noexcept{return reason_tls_context;}
bool SignedCore(const native::CoreBindings &,native::CoreSnapshotPrefix &output) noexcept{
  output={};output.clock.date_raw=53220000;output.clock.paused=true;
  output.map_ready=output.has_played_character=output.played_character_alive=true;
  output.played_character_id=current_actor;return true;
}
struct ReasonPump {
  std::array<std::byte,0x28> tls{},jomini{};std::array<std::byte,0x18> state{};
  std::uint8_t initialized=1;void *jomini_pointer=jomini.data(),*state_pointer=state.data();std::uintptr_t rng=0;
  explicit ReasonPump(api::MainThreadQueryMailboxV1 &mailbox){
    tls[0x20]=std::byte{1};jomini[0x20]=std::byte{1};Put(state.data(),8,std::int32_t{53220000});reason_tls_context=tls.data();
    mailbox.global_rng_wrapper_slot=reinterpret_cast<std::uintptr_t>(&rng);mailbox.jomini_state_slot=reinterpret_cast<std::uintptr_t>(&jomini_pointer);
    mailbox.game_state_slot=reinterpret_cast<std::uintptr_t>(&state_pointer);mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);mailbox.tls_context_getter=&ReasonTls;
    mailbox.executor_submission_enabled=true;mailbox.offline_fixture=true;mailbox.iat_hook_installed=true;mailbox.state=api::MainThreadQueryMailboxStateV1::idle;
    mailbox.permitted_executor_sway_completion_invalidation_reason12002=&native::ExecuteSwayCompletionInvalidationReasonMailboxV1;
    for(int i=0;i<2;++i)(void)api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
  }
  ~ReasonPump(){reason_tls_context=nullptr;}
};
struct ReasonRouteResult{bool success=false,drained=false;std::string wire,failure;};
ReasonRouteResult PublicReason(FrameAdapter &adapter,const native::SwayInvalidationReasonRecorder12002 &recorder,std::string_view payload,std::string_view request_id,bool expected){
  api::MainThreadQueryMailboxV1 mailbox{};ReasonPump pump(mailbox);ReasonRouteResult result{};std::atomic<bool> done=false;adapter.reads=0;
  std::thread worker([&]{result.success=native::HandleSwayCompletionInvalidationReasonV1(adapter,mailbox,recorder,adapter.frame,7,native::kSwayCompletionInvalidationReasonStepV1,payload,request_id,result.wire,result.failure);done.store(true,std::memory_order_release);});
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
  while(!done.load(std::memory_order_acquire)&&std::chrono::steady_clock::now()<deadline){
    if(mailbox.state==api::MainThreadQueryMailboxStateV1::queued)result.drained|=api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  std::cout<<"PUBLIC_REASON success="<<result.success<<" drained="<<result.drained<<" executed="<<mailbox.executed_requests<<" failure="<<result.failure<<'\n';
  Check(result.drained==expected,"new public reason ingress queues exactly the admitted request");
  Check(mailbox.state==api::MainThreadQueryMailboxStateV1::idle,"new public reason ingress reclaims original ticket");
  Check(mailbox.executed_requests==(expected?1U:0U)&&mailbox.failure_flags==0,"original reason executor completion and mailbox fault flags");
  if(expected)Check(mailbox.executor_started_requests==1&&mailbox.completed_sequence==mailbox.published_sequence&&adapter.reads==2,"real reason Enter/Finish and native ticket identity");
  else Check(mailbox.next_sequence==0,"reason parser/frame rejection creates no action/query ticket");
  return result;
}
std::string Request(std::int32_t actor_id,std::int32_t target_id,std::uint64_t cursor){
  return "{\"expected_revision\":7,\"actor_character_id\":"+std::to_string(actor_id)+",\"target_character_id\":"+std::to_string(target_id)+",\"scheme_instance_id\":134217986,\"after_sequence\":"+std::to_string(cursor)+"}";
}
void Write(const std::filesystem::path &out,const std::string &file,const std::string &value){
  std::ofstream stream(out/file,std::ios::binary);stream<<value;stream.close();Check(static_cast<bool>(stream),"write actual reason producer bytes");
}
void SignedReasonCase(std::int32_t actor_id,std::int32_t target_id,int pair,const std::filesystem::path &out){
  current_actor=actor_id;current_target=target_id;ReasonFixture fixture;
  auto &parent=fixture.parent;parent.bindings.read_core_snapshot=&SignedCore;
  parent.root=Token(4,std::bit_cast<std::uint32_t>(actor_id));parent.owner=parent.root;parent.target_token=Token(4,std::bit_cast<std::uint32_t>(target_id));
  Put(parent.rows.data(),8,parent.owner);Put(parent.rows.data(),0x20,parent.target_token);
  FrameAdapter adapter;adapter.frame.paused=adapter.frame.map_ready=adapter.frame.has_played_character=adapter.frame.played_character_alive=true;
  adapter.frame.played_character_id=actor_id;adapter.frame.date_raw=53220000;
  native::SwayInvalidationReasonRecorder12002 recorder;recorder.SetObserverAttached(true);
  const std::array<std::string_view,3> keys{"sway_invalidated_dead","sway_invalidated_war","scheme_target_not_in_diplomatic_range"};
  const std::array<std::string_view,3> labels{"dead","war","range"};
  for(std::size_t i=0;i<keys.size();++i){
    fixture.Select(i==2,keys[i]);native::SwayInvalidationReasonSource12002 captured;
    Check(fixture.Capture(captured)==native::SwayInvalidationReasonCapture12002::captured,"actual current4 reader admits new signed role scope");
    Check(captured.actor_character_id==std::bit_cast<std::uint32_t>(actor_id)&&captured.target_character_id==std::bit_cast<std::uint32_t>(target_id)&&captured.scheme_id==scheme&&
      SameToken(captured.root,parent.root)&&SameToken(captured.owner,parent.owner)&&SameToken(captured.target,parent.target_token)&&SameToken(captured.scheme,parent.scheme_token),"raw32 identity plus full Token16 high bits/subtype/reserved retained");
    Check(recorder.Append(captured),"real reason recorder Append accepts real signed capture");
    const auto prefix="pair-"+std::to_string(pair)+"-"+std::string(labels[i]);const auto payload=Request(actor_id,target_id,i);Write(out,prefix+".request.json",payload);
    native::SwayInvalidationReasonQueryResult12002 before;
    Check(recorder.Query({std::bit_cast<std::uint32_t>(actor_id),std::bit_cast<std::uint32_t>(target_id),scheme,i},before)&&before.records.size()==1,"real reason Query matches exact raw32 roles before public ingress");
    Write(out,prefix+".captured-before-handler.json",native::SerializeSwayCompletionInvalidationReasonCommandResultV1(before,7,53220000,"captured-before-handler",actual4::kGameVersion,actual4::kExecutableSha256));
    auto result=PublicReason(adapter,recorder,payload,"reason-"+prefix,true);
    Check(result.success&&result.failure.empty(),"public reason handler admits actual4 canonical role request");
    Check(result.wire.find("\"actor_character_id\":"+std::to_string(actor_id))!=std::string::npos&&result.wire.find("\"target_character_id\":"+std::to_string(target_id))!=std::string::npos,"bare body and retained source role output is canonical signed");
    Check(result.wire.find("\"source_branch\"")!=std::string::npos&&result.wire.find("\"authored_reason_key\":\""+std::string(keys[i])+"\"")!=std::string::npos,"public handler serializes exact captured reason key");
    Check(result.wire.find("\"native_end_cause_observed\":true")==std::string::npos&&result.wire.find("\"native_terminal_state_observed\":true")==std::string::npos&&result.wire.find("\"material_effect_observed\":true")==std::string::npos,"new signed notification input supplies no material/terminal/cause");
    Write(out,prefix+".response.json",result.wire);
  }
  // A real captured different-generation target remains outside this original query.
  parent.target_token=Token(4,std::bit_cast<std::uint32_t>(target_id)^0x01000000U);Put(parent.rows.data(),0x20,parent.target_token);
  native::SwayInvalidationReasonSource12002 other;fixture.Select(false,keys[0]);
  Check(fixture.Capture(other)==native::SwayInvalidationReasonCapture12002::captured&&recorder.Append(other),"real reader produces distinct target-generation negative control");
  auto unrelated=PublicReason(adapter,recorder,Request(actor_id,target_id,3),"reason-unrelated-target",true);
  Check(unrelated.success&&unrelated.wire.find("\"records\":[]")!=std::string::npos,"Query does not combine signed/unsigned alternatives or foreign full generation");
}
void NewIngressRejections(){
  FrameAdapter adapter;adapter.frame.paused=adapter.frame.map_ready=adapter.frame.has_played_character=adapter.frame.played_character_alive=true;adapter.frame.played_character_id=0;adapter.frame.date_raw=53220000;
  native::SwayInvalidationReasonRecorder12002 recorder;recorder.SetObserverAttached(true);
  for(std::string token:{"-1","-0","4294967294"}){
    const auto payload="{\"expected_revision\":7,\"actor_character_id\":0,\"target_character_id\":"+token+",\"scheme_instance_id\":0,\"after_sequence\":0}";
    auto result=PublicReason(adapter,recorder,payload,"reason-new-ingress-reject",false);Check(!result.success&&result.wire.empty(),"new reason entry rejects sentinel/noncanonical/raw unsigned alias");
  }
  adapter.identity.game_version="1.20.0.2";adapter.identity.executable_sha256=native::kExecutableSha256;
  auto legacy=PublicReason(adapter,recorder,Request(0,2,0),"legacy-positive-domain-retained",false);Check(!legacy.success&&legacy.wire.empty(),"legacy reason request keeps original positive role domain");
}
}
namespace xar::ck3_12002 {const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter)noexcept{return adapter;}}
namespace xar::game {bool ReadCk3_12002TimelineCoreSnapshot(const GameAdapter &,Snapshot &)noexcept{++unexpected_calls;std::abort();}}
int main(int argc,char **argv){try{
  if(argc!=2)throw std::runtime_error("expected output directory");std::filesystem::path out(argv[1]);std::filesystem::create_directories(out);checks=0;
  SignedReasonCase(-2,0,0,out);SignedReasonCase(0,INT32_MAX,1,out);SignedReasonCase(INT32_MIN,INT32_MAX,2,out);NewIngressRejections();
  Check(unexpected_calls==0,"unexercised Timeline seam never used");
  std::cout<<"PASS "<<checks<<" new signed-reason public handler/queue/pump/real reader/recorder/serializer checks; original46 NOT_RUN; Game NOT_RUN\n";return 0;
}catch(const std::exception &error){std::cerr<<"FAIL "<<error.what()<<'\n';return 1;}}
