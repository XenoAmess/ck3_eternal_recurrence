// NO-GAME STATE FIXTURE ONLY. The corrected a04 core file is included without
// edits. This private test TU can seed its internal owner state; it does not
// qualify real installation, prefix writing, global quiescence or restoration.
#include "fixture_shared.hpp"
#include <cstring>
#include "../candidate-a04/parent_entry_opportunity_12004.cpp"
namespace xar::ck3_12004::parent_entry {
namespace {
alignas(16) unsigned char fake_character[0x200]{};
alignas(16) unsigned char fake_context[0x500]{};
alignas(16) unsigned char fake_state[0x100]{};
bool fixture_read_failure=false;
volatile LONG64 fixture_reads=0;
volatile LONG64 fixture_prefix_reads=0;
bool FixtureRead(void*,std::uintptr_t p,void*out,std::size_t n) noexcept {
  InterlockedIncrement64(&fixture_reads);
  if(fixture_read_failure)return false;
  if(p==owner.module_base+kEntryRva&&n==16){InterlockedIncrement64(&fixture_prefix_reads);std::memcpy(out,patch.data(),16);return true;}
  if(p==owner.module_base+0x5C68C50&&n==8){std::memcpy(out,&owner.game_state,8);return true;}
  const bool range=(p>=reinterpret_cast<std::uintptr_t>(fake_character)&&p+n<=reinterpret_cast<std::uintptr_t>(fake_character)+sizeof fake_character)||
    (p>=reinterpret_cast<std::uintptr_t>(fake_state)&&p+n<=reinterpret_cast<std::uintptr_t>(fake_state)+sizeof fake_state);
  if(!range)return false;
  std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;
}
}
extern "C" bool ParentFixtureSeed(std::uint64_t target) {
  if(Atomic(XarParentEntryState12004.enabled)||Atomic(XarParentEntryState12004.active_thunks))return false;
  std::memset(&XarParentEntryState12004,0,sizeof XarParentEntryState12004);
  owner={};owner.machine_id="NO_GAME_SYNTHETIC_FIXTURE";owner.executable_sha256=std::string(kExeSha);
  owner.module_base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  owner.character=target;owner.context=reinterpret_cast<std::uintptr_t>(fake_context);
  owner.game_state=reinterpret_cast<std::uintptr_t>(fake_state);
  owner.pid=GetCurrentProcessId();owner.full_id=33388;owner.local_player_id=1;
  FILETIME c{},e{},k{},u{};if(!GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u))return false;
  owner.process_create_time_100ns=(std::uint64_t(c.dwHighDateTime)<<32)|c.dwLowDateTime;
  owner.generation=owner.window=owner.payment_epoch=1;owner.date_raw=53149056;owner.absolute_day=2214544;
  owner.ordinary_null_owner=true;owner.explicit_entry_hook_admission=true;
  environment={};environment.read=&FixtureRead;
  // The injected reader supplies only this fixture's declared Character fields.
  // Target points to fake_character, so the actual ASM RDX remains owned memory.
  if(target!=reinterpret_cast<std::uintptr_t>(fake_character))return false;
  std::uint32_t id=33388,magic=0x43686172,day=static_cast<std::uint32_t>(owner.absolute_day);
  std::memcpy(fake_character+0x18,&id,4);std::memcpy(fake_character+0x1c,&magic,4);
  std::memcpy(fake_character+0x1c0,&owner.context,8);
  std::memcpy(fake_state+8,&owner.date_raw,8);std::memcpy(fake_state+0x9c,&day,4);
  patch.fill(0x90);owned=true;patch_may_be_present=true;armed_once=false;identity_before=false;
  fixture_read_failure=false;
  auto&w=XarParentEntryState12004;w.target_character=target;w.admitted_full_id=33388;
  w.epoch=w.generation=w.window=1;w.admission_date=owner.date_raw;w.admission_absolute_day=owner.absolute_day;
  return true;
}
extern "C" std::uint64_t ParentFixtureTarget(){return reinterpret_cast<std::uintptr_t>(fake_character);}
extern "C" void ParentFixtureReadFailure(bool fail){fixture_read_failure=fail;}
extern "C" bool ParentFixtureAdmissionGuardTest(){
  if(!ParentFixtureSeed(reinterpret_cast<std::uintptr_t>(fake_character)))return false;
  auto a=owner;auto e=environment;e.all_reachable_threads_quiescent=true;
  owned=false;patch_may_be_present=false;
  InterlockedExchange64(&fixture_reads,0);InterlockedExchange64(&fixture_prefix_reads,0);a.local_player_id=0;
  if(Install(a,e)||Atomic(fixture_reads)!=0)return false;
  a.local_player_id=1;
  // Prefix reader deliberately returns NOPs. A legitimate1/33388 pair must
  // reach Identity reads then reject the fake prefix BEFORE any pin/write.
  if(Install(a,e)||Atomic(fixture_reads)==0||Atomic(fixture_prefix_reads)==0||owned||patch_may_be_present)return false;
  return true;
}
}
