#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/native_time_command_observer_12004.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <cstdio>
#include <stdexcept>
namespace obs=xar::ck3_12004::time_observer31;
namespace {
struct alignas(8) Object { std::array<std::byte,0x28> bytes{}; };
Object fixture_source{},pool[112]{};
std::size_t next_object{};
bool enabled=true,reads=true,reenter=false,fixture_paused=true;
std::uint64_t ticks{};
std::uint32_t clones{},deletes{},executes{},appends{},scalars{};
void* last_slot{};
void* wrong_slot=&fixture_source;
int fixture_container{};
bool Known(const void* p) noexcept {
 if(p==&fixture_source)return true;
 for(const auto& obj:pool)if(p==&obj)return true;
 return false;
}
template<class T> void Field(void* p,std::size_t offset,T value) {
 std::memcpy(static_cast<std::byte*>(p)+offset,&value,sizeof(value));
}
void** Clone(const void* input,void** out) {
 ++clones;assert(next_object<112);
 auto* result=&pool[next_object++];
 std::memcpy(result,input,sizeof(Object));*out=result;return out;
}
void* Delete(void* object,std::uint32_t) {++deletes;return object;}
void Execute(void*) {++executes;fixture_paused=false;}
void ExecuteThrows(void*) {++executes;throw std::runtime_error("native_fixture_exception");}
void** Append(void*,void** input) {++appends;last_slot=*input;return &last_slot;}
void** AppendNull(void*,void**) {++appends;return nullptr;}
void** AppendWrong(void*,void**) {++appends;return &wrong_slot;}
void** AppendThrows(void*,void**) {++appends;throw std::runtime_error("append_fixture_exception");}
void* Secondary(void* object) {return static_cast<std::byte*>(object)+0x18;}
void** AppendEarlyExecute(void*,void** input) {
 ++appends;last_slot=*input;
 obs::ForwardExecute(Execute,Secondary(*input),0x1234);
 return &last_slot;
}
void* BoundClone(std::uint64_t connection,const char* id) {
 void* storage{};obs::RequestScope request(connection,id,false);
 obs::BridgeCloneScope bound(&fixture_source);
 const auto count=clones;
 assert(obs::ForwardClone(Clone,&fixture_source,&storage,0)==&storage&&clones==count+1);
 return storage;
}
std::uint32_t Count(const obs::Dump& d,obs::Kind kind,obs::Token token) {
 std::uint32_t n=0;for(std::uint32_t i=0;i<d.count;++i)
   if(d.events[i].kind==kind&&d.events[i].token==token)++n;
 return n;
}
obs::Event Latest(obs::Kind kind,obs::Token token) {
 obs::Dump d{};assert(obs::ReadDump(d));
 for(std::uint32_t i=d.count;i>0;--i)
  if(d.events[i-1].kind==kind&&d.events[i-1].token==token)return d.events[i-1];
 assert(false);return {};
}
void UnqualifiedExecution(void* object) {
 const auto token=obs::Lookup(object).token;
 const auto count=executes;obs::ForwardExecute(Execute,Secondary(object),0x1234);
 assert(executes==count+1);
 const auto enter=Latest(obs::Kind::execute_enter,token);
 const auto done=Latest(obs::Kind::execute_return,token);
 assert(!enter.qualified&&!done.qualified&&enter.invocation==done.invocation);
}
}
namespace xar::ck3_12004::time_observer31 {
bool Attached() noexcept {return enabled;}
Environment Identity() noexcept {Environment e{};e.process_id=123;e.process_birth=456;
 e.qpc_frequency=1000;e.image_base=0x140000000;return e;}
bool IsPauseObject(const void* p) noexcept {return enabled&&Known(p);}
bool ReadPointer(const void* p,void*& out) noexcept {
 if(!reads||!p)return false;std::memcpy(&out,p,sizeof(out));return true;
}
bool ExpectedContainer(const void* p) noexcept {return p==&fixture_container;}
bool ReadPayload(const void* p,std::int32_t& player,std::uint8_t& desired,std::uint32_t& sequence) noexcept {
 if(!reads||!Known(p))return false;
 const auto* bytes=static_cast<const std::byte*>(p);
 std::memcpy(&player,bytes+0x20,sizeof(player));
 std::memcpy(&desired,bytes+0x24,sizeof(desired));
 std::memcpy(&sequence,bytes+0x0c,sizeof(sequence));return true;
}
Scalar ReadScalar() noexcept {++scalars;Scalar s{};s.game=100;s.jomini=200;s.date=42;
 s.paused=fixture_paused?1:0;s.valid=reads?1:0;return s;}
std::uint64_t Clock() noexcept {
 if(reenter){reenter=false;(void)Lookup(&fixture_source);}return ++ticks;
}
std::uint32_t Thread() noexcept {return 7;}
}
int main() {
 Field(&fixture_source,0x20,std::int32_t{23});Field(&fixture_source,0x24,std::uint8_t{0});
 const auto connection=obs::BeginConnection();
 void* storage=BoundClone(connection,"resume-fixture-1");
 const auto first=obs::Lookup(storage);assert(first.valid&&first.key.valid);
 assert(first.role==obs::Role::bridge_root&&first.key.desired_paused==0);
 // Native queue assigns a sequence after Clone and before its insertion call.
 Field(storage,0x0c,std::uint32_t{73});
 auto queue=obs::Enter(obs::Kind::queue_enter,storage,0,7,true);
 assert(obs::ForwardAppend(Append,&fixture_container,&storage,0x37F0794)==&last_slot);
 obs::Return(obs::Kind::queue_return,queue,0,true,true);
 assert(obs::Lookup(storage).inserted&&obs::Lookup(storage).native_sequence==73);
 obs::ForwardExecute(Execute,Secondary(storage),0x1234);
 assert(executes==1&&!fixture_paused&&appends==1);
 obs::Dump d{};assert(obs::ReadDump(d));
 assert(Count(d,obs::Kind::insert_return,first.token)==1);
 assert(Count(d,obs::Kind::execute_enter,first.token)==1);
 assert(Count(d,obs::Kind::execute_return,first.token)==1);
 const auto entry=Latest(obs::Kind::execute_enter,first.token);
 const auto done=Latest(obs::Kind::execute_return,first.token);
 assert(entry.qualified==1&&done.qualified==1&&done.key.valid);
 assert(done.invocation==entry.invocation&&done.invocation!=0);
 assert(done.native_sequence==73&&done.player==23&&done.command_paused==0);
 assert(done.scalar.paused==0&&done.scalar.date==42);
 obs::ForwardDelete(Delete,storage,1,0);
 assert(deletes==1&&!obs::Lookup(storage).valid);
 // Retired address is diagnostic only, never resurrection of an old Ticket.
 const auto retired_count=executes,scalar_count=scalars;
 obs::ForwardExecute(Execute,Secondary(storage),0x1234);
 assert(executes==retired_count+1&&scalars==scalar_count+2);
 auto retired=Latest(obs::Kind::execute_enter,{});
 auto retired_done=Latest(obs::Kind::execute_return,{});
 assert(retired.lookup_outcome==obs::LookupOutcome::retired_same_address);
 assert(retired_done.lookup_outcome==retired.lookup_outcome);
 assert(retired.observed_object==reinterpret_cast<std::uintptr_t>(storage));
 assert(retired.observed_secondary==reinterpret_cast<std::uintptr_t>(Secondary(storage)));
 assert(retired.retired_at_sequence&&retired.retired_at_sequence<retired.sequence);
 assert(!retired.qualified&&!retired_done.qualified&&!retired.key.valid&&!retired_done.key.valid);
 assert(!retired.token.address&&!retired.token.incarnation&&!retired.parent.address);
 assert(!retired_done.token.address&&retired_done.role==obs::Role::unknown);
 assert(retired.invocation==retired_done.invocation);
 assert(retired_done.payload_valid&&retired_done.native_sequence==73&&retired_done.player==23);
 assert(std::puts(obs::DiagnosticFrame("retired-fixture").c_str())>=0);
 // A different unregistered address records its actual payload and has no tombstone.
 auto* unknown=&pool[111];Field(unknown,0x20,std::int32_t{91});
 Field(unknown,0x24,std::uint8_t{1});Field(unknown,0x0c,std::uint32_t{501});
 const auto unknown_count=executes;
 obs::ForwardExecute(Execute,Secondary(unknown),0x1234);
 assert(executes==unknown_count+1);
 const auto missing=Latest(obs::Kind::execute_enter,{});
 const auto missing_done=Latest(obs::Kind::execute_return,{});
 assert(missing.lookup_outcome==obs::LookupOutcome::missing&&!missing.retired_at_sequence);
 assert(missing.observed_object==reinterpret_cast<std::uintptr_t>(unknown));
 assert(missing.observed_secondary==reinterpret_cast<std::uintptr_t>(Secondary(unknown)));
 assert(!missing.qualified&&!missing_done.qualified&&!missing.key.valid&&!missing_done.key.valid);
 assert(!missing_done.token.address&&!missing_done.parent.address&&!missing_done.identity_epoch);
 assert(missing_done.payload_valid&&missing_done.player==91&&missing_done.command_paused==1);
 assert(missing_done.native_sequence==501&&missing_done.invocation==missing.invocation);
 assert(std::puts(obs::DiagnosticFrame("missing-fixture").c_str())>=0);
 // Native exceptions still propagate; no fabricated Return event.
 const auto throw_count=executes;
 try{obs::ForwardExecute(ExecuteThrows,Secondary(unknown),0x1234);assert(false);}
 catch(const std::runtime_error&){}
 assert(executes==throw_count+1);
 assert(obs::ReadDump(d)&&d.events[d.count-1].kind==obs::Kind::execute_enter);
 // Same address after observed retirement is a distinct observed incarnation.
 next_object=0;void* reused=BoundClone(connection,"resume-fixture-2");
 const auto second=obs::Lookup(reused);
 assert(second.valid&&second.token.address==first.token.address);
 assert(second.token.incarnation>first.token.incarnation);
 void* recorder{};obs::ForwardClone(Clone,reused,&recorder,0x3808E9B);
 const auto copy=obs::Lookup(recorder);
 assert(copy.valid&&copy.parent==second.token&&copy.role==obs::Role::recorder_copy);
 assert(obs::ReadDump(d)&&Count(d,obs::Kind::execute_enter,copy.token)==0);
 const auto before_appends=appends;
 assert(obs::ForwardAppend(Append,nullptr,&reused,0x37F0794)==&last_slot);
 assert(appends==before_appends+1&&obs::ReadDump(d));
 assert(d.events[d.count-1].kind==obs::Kind::insert_return&&!d.events[d.count-1].qualified);
 const auto filtered_newest=d.newest;const auto filtered_count=appends;
 assert(obs::ForwardAppend(Append,&fixture_container,&reused,0x5555)==&last_slot);
 assert(appends==filtered_count+1&&obs::ReadDump(d)&&d.newest==filtered_newest);
 const auto before_executes=executes;
 try{obs::ForwardExecute(ExecuteThrows,Secondary(reused),0x1234);assert(false);}
 catch(const std::runtime_error&){}
 assert(executes==before_executes+1&&obs::ReadDump(d));
 assert(Count(d,obs::Kind::execute_enter,second.token)==1);
 assert(Count(d,obs::Kind::execute_return,second.token)==0);
 // Failed Append, including native throw, must never create insertion qualification.
 for(int mode=0;mode<3;++mode) {
  void* object=BoundClone(connection,"failed-insert");
  const auto count=appends;
  if(mode==0)assert(obs::ForwardAppend(AppendNull,&fixture_container,&object,0x37F0794)==nullptr);
  if(mode==1)assert(obs::ForwardAppend(AppendWrong,&fixture_container,&object,0x37F0794)==&wrong_slot);
  if(mode==2) {
   try{obs::ForwardAppend(AppendThrows,&fixture_container,&object,0x37F0794);assert(false);}
   catch(const std::runtime_error&){}
  }
  assert(appends==count+1&&!obs::Lookup(object).inserted);
  UnqualifiedExecution(object);
 }
 // Concurrent natural Execute before Append return is conservatively unqualified.
 void* early=BoundClone(connection,"early-execute");
 const auto early_token=obs::Lookup(early).token;
 const auto early_appends=appends,early_executes=executes;
 assert(obs::ForwardAppend(AppendEarlyExecute,&fixture_container,&early,0x37F07AD)==&last_slot);
 assert(appends==early_appends+1&&executes==early_executes+1);
 assert(!Latest(obs::Kind::execute_return,early_token).qualified);
 assert(!Latest(obs::Kind::insert_return,early_token).qualified);
 // Each post-insertion payload drift rejects attribution while forwarding once.
 for(int field=0;field<3;++field) {
  void* object=BoundClone(connection,"payload-drift");
  Field(object,0x0c,std::uint32_t{100});
  assert(obs::ForwardAppend(Append,&fixture_container,&object,0x37F0794)==&last_slot);
  assert(obs::Lookup(object).inserted);
  if(field==0)Field(object,0x0c,std::uint32_t{101});
  if(field==1)Field(object,0x20,std::int32_t{24});
  if(field==2)Field(object,0x24,std::uint8_t{1});
  UnqualifiedExecution(object);
 }
 // Diagnostic read failure never suppresses Clone or revives old identity.
 reads=false;void* unread{};
 const auto before_clones=clones;obs::ForwardClone(Clone,&fixture_source,&unread,0);
 reads=true;assert(clones==before_clones+1&&!obs::Lookup(reused).valid);
 void* tracked=BoundClone(connection,"busy-fixture");
 reenter=true;(void)obs::Enter(obs::Kind::execute_enter,tracked,1,0,true);
 assert(!obs::Lookup(tracked).valid&&obs::ReadDump(d)&&(d.gaps&obs::busy));
 assert(d.count&&d.events[d.count-1].key.valid==0);
 // Disabled observer must preserve all four original calls and return values.
 const auto newest=d.newest;
 const auto c0=clones,a0=appends,e0=executes,d0=deletes;
 enabled=false;void* disabled{};
 assert(obs::ForwardClone(Clone,&fixture_source,&disabled,0)==&disabled);
 assert(obs::ForwardAppend(Append,&fixture_container,&disabled,0x37F0794)==&last_slot);
 obs::ForwardExecute(Execute,Secondary(disabled),0);
 assert(obs::ForwardDelete(Delete,disabled,1,0)==disabled);
 enabled=true;
 assert(clones==c0+1&&appends==a0+1&&executes==e0+1&&deletes==d0+1);
 assert(obs::ReadDump(d)&&d.newest==newest);
 for(int i=0;i<70;++i) {
  void* value{};obs::RequestScope request(connection,"capacity-fixture",true);
  obs::BridgeCloneScope bound(&fixture_source);obs::ForwardClone(Clone,&fixture_source,&value,0);
 }
 assert(obs::ReadDump(d)&&(d.gaps&obs::full)&&(d.gaps&obs::event_overwrite));
 assert(d.count==obs::kDumpEvents&&d.live_registry<=obs::kRegistry);
 const auto frame=obs::DiagnosticFrame("journal-fixture");
 assert(frame.find("\"drain_fence\":false")!=std::string::npos);
 assert(frame.find("\"status\":\"passive_observation_only\"")!=std::string::npos);
 assert(std::puts(frame.c_str())>=0);
 return 0;
}

// Single-TU host qualification; no Windows installer or Game dependency.
#include "../src/native_time_command_observer_12004.cpp"
