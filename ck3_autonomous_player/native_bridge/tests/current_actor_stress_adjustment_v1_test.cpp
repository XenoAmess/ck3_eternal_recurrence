// Offline fixtures only. All callable overrides below belong to this test.
// No CK3 image instructions, game process, native endpoint, or mutator executes.
#include "xar_bridge/current_actor_stress_adjustment_v1.hpp"
#include "xar_bridge/current_actor_stress_adjustment_v1_pins.hpp"
#include "xar_bridge/current_actor_stress_adjustment_v1_mailbox.hpp"
#include "current_actor_stress_adjustment_fixture_adapter.hpp"
#include <windows.h>
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using namespace xar::ck3_12003;
namespace {
unsigned checks=0;
template<class T> void Put(void *p, std::size_t at, T v) {
  std::memcpy(static_cast<std::byte *>(p)+at,&v,sizeof(v));
}
struct Fixture {
  std::array<std::byte,0x40> storage{};
  std::array<std::byte,0x40> slots{};
  std::array<std::byte,0x200> actor{};
  std::array<std::byte,0x320> resources{};
  std::array<std::byte,0x100> aggregate{};
  void *storage_pointer=storage.data();
  xar::game::Snapshot frame{};
  int frame_calls=0, owner_calls=0, adjuster_calls=0, reader_calls=0;
  int change_frame_call=0, lose_owner_call=0;
  bool pins=true, bad_out=false, no_aggregator=false;
  int mutate_sample=0;
  std::int64_t gain=-25000,loss=120000;
  std::int32_t delta=4,last_base=999;
  Fixture() {
    frame.paused=true;frame.map_ready=true;frame.has_played_character=true;
    frame.played_character_alive=true;frame.played_character_id=0x01000002;
    frame.played_character_stress_points=27;frame.date_raw=53146848;
    // The getter is also allowed while a real paused product event is active.
    frame.has_active_event=true;frame.active_event_instance_id=901;
    Put(storage.data(),0x20,static_cast<void *>(slots.data()));
    Put(storage.data(),0x2C,std::int32_t(4));
    Put(slots.data(),2*0x10+8,static_cast<void *>(actor.data()));
    Put(actor.data(),0x18,frame.played_character_id);
    Put(actor.data(),0x1C,std::uint32_t(0x43686172));
    Put(actor.data(),0x1B0,static_cast<void *>(resources.data()));
    Put(resources.data(),0x2F8,std::int32_t(27));
  }
};
Fixture *fixture=nullptr;
bool Pins(std::uintptr_t) noexcept {return fixture->pins;}
void *Aggregate(void *actor) {
  assert(actor==fixture->actor.data());
  return fixture->no_aggregator?nullptr:fixture->aggregate.data();
}
std::int64_t *Modifier(void *map,std::int64_t *out,std::int32_t index) {
  assert(map==fixture->aggregate.data()+0x68);
  assert(index==(fixture->reader_calls%2==0?143:144));
  ++fixture->reader_calls;
  *out=index==143?fixture->gain:fixture->loss;
  return fixture->bad_out?nullptr:out;
}
std::int32_t Adjust(void *actor,std::int32_t base) {
  assert(actor==fixture->actor.data());
  fixture->last_base=base;++fixture->adjuster_calls;
  if(fixture->adjuster_calls==fixture->mutate_sample) {
    ++fixture->gain;
  }
  return fixture->delta;
}
bool Frame(void *ctx,xar::game::Snapshot &out) noexcept {
  auto &f=*static_cast<Fixture *>(ctx);++f.frame_calls;out=f.frame;
  if(f.frame_calls==f.change_frame_call)++out.date_raw;
  return true;
}
bool Owner(void *ctx) noexcept {
  auto &f=*static_cast<Fixture *>(ctx);++f.owner_calls;
  return f.owner_calls!=f.lose_owner_call;
}
CurrentActorStressAdjustmentRequestV1 Request() {
  return {5,7,0x01000002,991,2};
}
CurrentActorStressAdjustmentNativeBindingsV1 Bindings(Fixture &f) {
  fixture=&f;CurrentActorStressAdjustmentNativeBindingsV1 b{};
  b.enabled=true;b.image_base=1;b.executable_sha256=kExecutableSha256;
  b.character_storage_slot=&f.storage_pointer;b.verify_code_pins=&Pins;
  b.get_character_modifier_aggregator=&Aggregate;
  b.read_character_modifier=&Modifier;b.read_adjusted_stress_delta=&Adjust;
  return b;
}
CurrentActorStressAdjustmentObservationV1 Observation() {
  CurrentActorStressAdjustmentObservationV1 o{};
  o.owner_thread_verified=true;o.tls_verified=true;
  o.owner_thread_id=GetCurrentThreadId();o.owner_pump_epoch=19;return o;
}
bool Read(Fixture &f,CurrentActorStressAdjustmentObservationV1 &o,
          CurrentActorStressAdjustmentRequestV1 r=Request()) {
  auto b=Bindings(f);return ReadCurrentActorStressAdjustmentV1(
      b,{&f,&Frame,&Owner},r,f.frame,o);
}
void Nulls(const CurrentActorStressAdjustmentObservationV1 &o) {
  assert(!o.available&&!o.current_stress_points&&!o.stress_gain_modifier_raw&&
      !o.stress_loss_modifier_raw&&!o.adjusted_delta_points&&!o.frame_verified&&
      !o.unavailable_reason.empty());
  const auto wire=SerializeCurrentActorStressAdjustmentV1(o,1);
  for(auto key:{"current_stress_points","stress_gain_modifier_raw",
      "stress_loss_modifier_raw","adjusted_delta_points"})
    assert(wire.find(std::string("\"")+key+"\":null")!=std::string::npos);
}
std::string Wire(std::string_view base="5") {
  return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,"
      "\"request_id\":\"step-1-offline\",\"step\":\"query-current-actor-stress-adjustment-v1\","
      "\"expected_revision\":7,\"base_amount\":")+std::string(base)+
      ",\"expected_player_character_id\":16777218,\"expected_game_pid\":991,"
      "\"expected_connection_generation\":2}";
}
void ParserTests() {
  CurrentActorStressAdjustmentRequestV1 r{};
  for(auto base:{"-300","-15","-0","0","5","300"}) {
    assert(ParseCurrentActorStressAdjustmentRequestV1(Wire(base),r));++checks;
  }
  for(auto base:{"-301","301","true","false","null","5.0","1e2","\"5\"",
      "[5]","{\"x\":5}","05","+5","2147483648","-2147483649"}) {
    assert(!ParseCurrentActorStressAdjustmentRequestV1(Wire(base),r));++checks;
  }
  const auto valid=Wire();
  const std::array<std::pair<std::string,std::string>,15> bad{{
    {"\"expected_revision\":7","\"expected_revision\":0"},
    {"\"expected_revision\":7","\"expected_revision\":-1"},
    {"\"expected_revision\":7","\"expected_revision\":18446744073709551616"},
    {"\"expected_player_character_id\":16777218","\"expected_player_character_id\":2147483648"},
    {"\"expected_player_character_id\":16777218","\"expected_player_character_id\":0"},
    {"\"expected_game_pid\":991","\"expected_game_pid\":4294967296"},
    {"\"expected_connection_generation\":2","\"expected_connection_generation\":0"},
    {"\"base_amount\":5","\"base_amount\":5,\"base_amount\":5"},
    {"\"base_amount\":5","\"base_amount\":5,\"actor_address\":1"},
    {"\"base_amount\":5","\"base_amount\":5,\"native_index\":143"},
    {"\"base_amount\":5","\"base_amount\":5,\"option_index\":0"},
    {"\"base_amount\":5,",""},
    {"\"protocol_version\":1","\"protocol_version\":2"},
    {"\"type\":\"execute_step\"","\"type\":\"command\""},
    {"\"step\":\"query-current-actor-stress-adjustment-v1\"","\"step\":\"pause-map\""}
  }};
  for(const auto &pair:bad) {
    auto s=valid;const auto at=s.find(pair.first);assert(at!=std::string::npos);
    s.replace(at,pair.first.size(),pair.second);
    assert(!ParseCurrentActorStressAdjustmentRequestV1(s,r));++checks;
  }
  for(auto s:{std::string(""),std::string("{}"),valid+"x",valid+",",std::string(4097,' ')}) {
    assert(!ParseCurrentActorStressAdjustmentRequestV1(s,r));++checks;
  }
  assert(ParseCurrentActorStressAdjustmentRequestV1(" \n"+valid+"\t ",r));++checks;
  std::cout<<"FIXTURE_REQUEST "<<valid<<'\n';
}
void ProviderTests() {
  for(auto base:{-300,-15,0,5,300}) {
    Fixture f{};f.delta=base==5?4:-77;auto o=Observation();auto r=Request();r.base_amount=base;
    assert(Read(f,o,r)&&o.available&&o.frame_verified&&o.actor_binding_verified&&
        o.source_code_pins_verified&&o.owner_thread_verified&&o.tls_verified&&
        *o.current_stress_points==27&&*o.stress_gain_modifier_raw==-25000&&
        *o.stress_loss_modifier_raw==120000&&*o.adjusted_delta_points==f.delta&&
        f.last_base==base&&f.adjuster_calls==2&&f.reader_calls==4&&f.frame_calls==3);
    ++checks;
    if(base==5)std::cout<<"FIXTURE_AVAILABLE "<<SerializeCurrentActorStressAdjustmentV1(o,41)<<'\n';
  }
  {Fixture f{};f.gain=9007199254740993LL;f.loss=-9007199254740993LL;
    auto o=Observation();assert(Read(f,o));auto s=SerializeCurrentActorStressAdjustmentV1(o,42);
    assert(s.find("\"stress_gain_modifier_raw\":9007199254740993")!=std::string::npos&&
        s.find("\"stress_loss_modifier_raw\":-9007199254740993")!=std::string::npos);++checks;}
  for(int variant=0;variant<28;++variant) {
    Fixture f{};auto o=Observation();auto r=Request();auto b=Bindings(f);
    switch(variant) {
      case 0:b.enabled=false;break;
      case 1:b.executable_sha256="wrong";break;
      case 2:f.pins=false;break;
      case 3:o.owner_thread_verified=false;break;
      case 4:o.tls_verified=false;break;
      case 5:o.owner_thread_id=0;break;
      case 6:o.owner_pump_epoch=0;break;
      case 7:f.lose_owner_call=1;break;
      case 8:f.lose_owner_call=2;break;
      case 9:f.lose_owner_call=3;break;
      case 10:f.change_frame_call=1;break;
      case 11:f.change_frame_call=2;break;
      case 12:f.change_frame_call=3;break;
      case 13:Put(f.actor.data(),0x18,std::int32_t(2));break;
      case 14:Put(f.actor.data(),0x1C,std::uint32_t(0));break;
      case 15:Put(f.actor.data(),0x1D0,reinterpret_cast<void *>(1));break;
      case 16:Put(f.actor.data(),0x1B0,static_cast<void *>(nullptr));break;
      case 17:Put(f.storage.data(),0x2C,std::int32_t(2));break;
      case 18:Put(f.resources.data(),0x2F8,std::int32_t(-1));break;
      case 19:f.bad_out=true;break;
      case 20:f.no_aggregator=true;break;
      case 21:f.mutate_sample=1;break;
      case 22:r.expected_player_character_id=2;break;
      case 23:f.frame.played_character_stress_points=26;break;
      case 24:f.frame.played_character_stress_points=-1;break;
      case 25:f.frame.paused=false;break;
      case 26:f.frame.map_ready=false;break;
      case 27:f.frame.played_character_alive=false;break;
    }
    assert(!ReadCurrentActorStressAdjustmentV1(b,{&f,&Frame,&Owner},r,f.frame,o));
    Nulls(o);++checks;
    if(variant==2)std::cout<<"FIXTURE_UNAVAILABLE "<<SerializeCurrentActorStressAdjustmentV1(o,43)<<'\n';
  }
  {Fixture f{};auto o=Observation();assert(Read(f,o));o.tls_verified=false;
    auto s=SerializeCurrentActorStressAdjustmentV1(o,44);
    assert(s.find("\"adjusted_delta_points\":null")!=std::string::npos&&
        s.find("typed_result_inconsistent")!=std::string::npos);++checks;}
  {Fixture f{};auto o=Observation();assert(Read(f,o));
    auto s=SerializeCurrentActorStressAdjustmentV1(o,0);
    assert(s.find("\"status\":\"unavailable\"")!=std::string::npos);++checks;}
  // Access violations are caught by the actual provider's SEH boundary.
  {Fixture f{};auto o=Observation();auto b=Bindings(f);
    b.character_storage_slot=reinterpret_cast<void **>(1);
    assert(!ReadCurrentActorStressAdjustmentV1(b,{&f,&Frame,&Owner},Request(),f.frame,o));
    Nulls(o);++checks;}
}
void PinTests() {
  const auto highest=kCurrentActorStressAdjustmentCodePinsV1[1].rva+0x1000;
  std::vector<std::uint8_t> image(highest);
  for(const auto &pin:kCurrentActorStressAdjustmentCodePinsV1)
    std::memcpy(image.data()+pin.rva,pin.bytes,pin.length);
  const auto base=reinterpret_cast<std::uintptr_t>(image.data());
  assert(VerifyCurrentActorStressAdjustmentCodePinsV1(base));++checks;
  for(const auto &pin:kCurrentActorStressAdjustmentCodePinsV1) {
    image[pin.rva+pin.length-1]^=1;
    assert(!VerifyCurrentActorStressAdjustmentCodePinsV1(base));++checks;
    image[pin.rva+pin.length-1]^=1;
  }
  assert(!VerifyCurrentActorStressAdjustmentCodePinsV1(0));++checks;
  assert(!VerifyCurrentActorStressAdjustmentCodePinsV1(1));++checks;
  auto bound=BindCurrentActorStressAdjustmentImageV1(base,kExecutableSha256);
  assert(bound.enabled&&reinterpret_cast<std::uintptr_t>(bound.read_adjusted_stress_delta)==base+0x28BC800&&
      reinterpret_cast<std::uintptr_t>(bound.get_character_modifier_aggregator)==base+0x28C3AE0&&
      reinterpret_cast<std::uintptr_t>(bound.read_character_modifier)==base+0x2303700);++checks;
  assert(!BindCurrentActorStressAdjustmentImageV1(base,"wrong").enabled);++checks;
}
bool OtherExecutor(void *,const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept {return false;}
void MailboxTests() {
  using namespace xar::ck3_11906;
  // Execute the production admission code over a test-local mailbox. No pump
  // hook is installed and no posted GUI action/native function is invoked.
  MainThreadQueryMailboxV1 m{};m.state.store(MainThreadQueryMailboxStateV1::idle);
  m.executor_submission_enabled=true;m.owner_thread_id.store(GetCurrentThreadId());
  m.paused_owner_verified_pump_epochs.store(2);
  m.permitted_executor_current_actor_stress_adjustment12003=&ExecuteCurrentActorStressAdjustmentMailboxV1;
  MainThreadQueryTicketV1 ticket{};int dummy=1;
  assert(TrySubmitMainThreadQueryV1(m,&OtherExecutor,&dummy,ticket)==MainThreadQuerySubmitResultV1::invalid_request);++checks;
  m.paused_owner_verified_pump_epochs.store(1);
  assert(TrySubmitMainThreadQueryV1(m,&ExecuteCurrentActorStressAdjustmentMailboxV1,&dummy,ticket)==MainThreadQuerySubmitResultV1::paused_main_thread_not_observed);++checks;
  m.paused_owner_verified_pump_epochs.store(2);
  assert(TrySubmitMainThreadQueryV1(m,&ExecuteCurrentActorStressAdjustmentMailboxV1,&dummy,ticket)==MainThreadQuerySubmitResultV1::submitted&&ticket.sequence>0);++checks;
  assert(CancelMainThreadQueryV1(m,ticket)==MainThreadQueryCancelResultV1::cancelled);
  assert(ReclaimMainThreadQueryV1(m,ticket)==MainThreadQueryReclaimResultV1::reclaimed);
  FixtureAdapter adapter{};Fixture f{};adapter.frame=f.frame;
  for(int variant=0;variant<18;++variant) {
    CurrentActorStressAdjustmentMailboxContextV1 q{};
    q.request=Request();q.request.expected_game_pid=GetCurrentProcessId();
    q.envelope.game=&adapter;q.envelope.mailbox=&m;q.envelope.typed_context=&q;
    q.envelope.expected_snapshot=f.frame;q.envelope.expected_snapshot_revision=7;
    q.envelope.ticket.sequence=77;
    m.state.store(MainThreadQueryMailboxStateV1::executing);m.published_sequence.store(77);
    m.owner_thread_id.store(GetCurrentThreadId());m.failure_flags.store(0);m.stop_requested.store(false);
    m.executor=&ExecuteCurrentActorStressAdjustmentMailboxV1;m.executor_context=&q.envelope;
    adapter.frame=f.frame;adapter.admitted=true;
    MainThreadExecutionStampV1 stamp{};stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=19;
    stamp.paused=true;stamp.date_raw=f.frame.date_raw;stamp.tls_initialized=1;
    stamp.tls_main_thread_marker=1;stamp.tls_context=1;stamp.tls_initialized_flag_address=1;
    stamp.jomini_state=1;stamp.game_state=1;
    switch(variant) {
      case 1:stamp.tls_initialized=0;break;
      case 2:stamp.tls_main_thread_marker=0;break;
      case 3:stamp.tls_context=0;break;
      case 4:stamp.tls_initialized_flag_address=0;break;
      case 5:stamp.pump_epoch=0;break;
      case 6:++stamp.thread_id;break;
      case 7:stamp.paused=false;break;
      case 8:stamp.jomini_state=0;break;
      case 9:stamp.game_state=0;break;
      case 10:++stamp.date_raw;break;
      case 11:++q.request.expected_revision;break;
      case 12:++q.request.expected_game_pid;break;
      case 13:adapter.admitted=false;break;
      case 14:m.published_sequence.store(78);break;
      case 15:m.failure_flags.store(1);break;
      case 16:m.stop_requested.store(true);break;
      case 17:++adapter.frame.played_character_stress_points;break;
    }
    const bool result=ExecuteCurrentActorStressAdjustmentMailboxV1(&q.envelope,stamp);
    if(variant==0) {
      assert(result&&q.completed&&q.envelope.frame_stable&&!q.observation.available&&
          q.observation.owner_thread_verified&&q.observation.tls_verified&&
          q.observation.owner_thread_id==GetCurrentThreadId());
      Nulls(q.observation);
    } else assert(!result&&!q.completed&&!q.observation.available);
    ++checks;
  }
}
} // namespace
int main() {
  ParserTests();ProviderTests();PinTests();MailboxTests();
  std::cout<<"OFFLINE_FOCUSED_CHECKS "<<checks<<" PASS; no CK3 function or process invoked\n";
}
