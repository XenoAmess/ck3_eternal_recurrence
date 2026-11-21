#include "xar_bridge/date_worker_access_layout131.hpp"
#include "legacy_date_fixture131.inc"
namespace {
struct Current131:Fixture {
 std::array<std::byte,0x700> access_bytes{};
 bool wrong_current_access=false;
 Current131(){
  bindings.core.image_build=ImageBuildV1::full11126785313;
  data.resize(0x46B00);ConfigureCurrentData();
  bindings.worker_fixture.scope=&Scope131;bindings.worker_fixture.with_game_access=&Access131;
 }
 void ConfigureCurrentData(){
  std::fill(data.begin(),data.end(),std::byte{});Put(game,0xA0,data.data());
  Put(data,0x26FB0,entries.data());Put(data,0x26FBC,std::int32_t{1});
 }
 void Reset(){Fixture::Reset();ConfigureCurrentData();}
 static bool Scope131(void *p,std::uint32_t &id,std::uint8_t &init,std::uint32_t &scope,std::uint8_t &access) noexcept {
  auto &f=*static_cast<Current131*>(p);id=GetCurrentThreadId();init=f.initialized;scope=f.command_scope;
  access=ReadDateWorkerAccessByte131(f.access_bytes.data(),f.bindings.core.image_build);return true;
 }
 static bool Access131(void *p,DateSentinelGameBodyV1 body,void *context) noexcept {
  auto &f=*static_cast<Current131*>(p);
  if(!f.access_allowed||GetCurrentThreadId()!=f.worker_thread_id.load())return false;
  const bool prior=f.game_access_active;f.game_access_active=true;++f.access_enters;
  // The old byte is deliberately opposite to current; production's shared
  // byte reader must select6E8. The actual DateSentinel controller is invoked.
  Put(f.access_bytes,0x6E0,std::uint8_t{1});Put(f.access_bytes,0x6E8,std::uint8_t(f.wrong_current_access?0:1));
  const bool result=body(context);Put(f.access_bytes,0x6E8,std::uint8_t{0});f.game_access_active=prior;++f.access_leaves;return result;
 }
};
}
int main(){
 Current131 f;
 Check(InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"actual DateSentinel current RAM initialization");
 const auto before=f.pauses;f.mailbox.owner_thread_id.store(GetCurrentThreadId()+1);
 Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable&&f.pauses==before,"wrong owner ARM zero effect");
 f.mailbox.owner_thread_id.store(GetCurrentThreadId());f.Start();const auto generation=ReadDateSentinelStatusV1(f.sentinel).generation;
 Check(CancelDateSentinelV1(f.sentinel,generation+1)==Cancel::generation_mismatch&&f.pauses==before,"wrong generation CANCEL zero effect");
 f.mailbox.owner_thread_id.store(GetCurrentThreadId()+1);
 Check(CancelDateSentinelV1(f.sentinel,generation)==Cancel::unavailable&&f.pauses==before,"wrong owner CANCEL zero effect");
 f.mailbox.owner_thread_id.store(GetCurrentThreadId());
 Check(CancelDateSentinelV1(f.sentinel,generation)==Cancel::canceled&&f.pauses==before,"same owner/generation paused CANCEL succeeds without clock write");
 f.Reset();f.Start();const auto second=ReadDateSentinelStatusV1(f.sentinel).generation;f.Date(24024);f.Post();
 auto status=ReadDateSentinelStatusV1(f.sentinel);
 Check(status.state==Phase::triggered&&status.generation==second&&status.trigger_date_raw==24024&&status.overshoot_days==0&&status.pause_observed&&f.last_post_pause_delta==1,"actual current owner6E8 exacttarget post pauses once");
 Check(f.access_enters==f.access_leaves&&f.native_close_attempts==0,"owned access cleanup/native handle preserved");
 f.Reset();f.Start();const auto third=ReadDateSentinelStatusV1(f.sentinel).generation;const auto zero=f.pauses;f.mono=f.sentinel.monotonic_deadline_ms;
 Check(CancelDateSentinelV1(f.sentinel,third)==Cancel::unavailable&&f.pauses==zero,"expired CANCEL zero effect");
 Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"valid owner can recover failed expiry separately");
 f.Reset();f.Start();const auto wrongbyte_pauses=f.pauses;f.wrong_current_access=true;f.Date(24024);f.Post();
 Check(f.pauses==wrongbyte_pauses&&ReadDateSentinelStatusV1(f.sentinel).state==Phase::failed,"old6E0 cannot impersonate current6E8, zero post pause");
 f.wrong_current_access=false;
 Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"valid owner cleanup after wrong worker access");
 Check(DateSentinelShutdownSafeV1(f.sentinel),"all actual model generations safely terminal");
 std::cout<<"CURRENT_SENTINEL131_OWNER_PASS real controller/core/kernel, ownRAM only\n";return 0;
}
