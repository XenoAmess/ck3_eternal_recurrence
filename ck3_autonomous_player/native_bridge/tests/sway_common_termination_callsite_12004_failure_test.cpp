#include "xar_bridge/sway_common_termination_callsite_observer_12004.hpp"
#include "xar_bridge/sway_end_invocation_12004.hpp"
#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/sway_completion_causal_observer_12004.hpp"
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <windows.h>
namespace xar::ck3_12004 {
SwayEndInvocationBindings12004 SwayFixtureBindEndImage12004(std::uintptr_t,std::string_view) noexcept;
}
namespace {
namespace native=xar::ck3_12002;
namespace actual4=xar::ck3_12004;
int checks=0,failures=0,abort_calls=0;
[[noreturn]]void NotExercised() noexcept {++abort_calls;std::abort();}
void Check(bool b,const char *s){++checks;if(!b){++failures;std::cerr<<"FAIL "<<s<<'\n';}}
template<class T>void Put(void *p,std::size_t offset,T value){std::memcpy(static_cast<std::byte *>(p)+offset,&value,sizeof(value));}
struct World {
 std::array<std::byte,0x40> type{},scheme{};
 World(std::int32_t actor,std::int32_t target){
  std::memcpy(type.data()+0x18,"sway",5);Put(type.data(),0x28,std::uint64_t{4});Put(type.data(),0x30,std::uint64_t{15});Put(type.data(),0x38,std::uint32_t{0x4744624F});
  Put(scheme.data(),0x10,std::uint32_t{0});Put(scheme.data(),0x14,std::uint32_t{0x5363686D});Put(scheme.data(),0x20,type.data());Put(scheme.data(),0x28,std::int32_t{0});Put(scheme.data(),0x2C,std::bit_cast<std::uint32_t>(actor));Put(scheme.data(),0x30,std::uint32_t{0});Put(scheme.data(),0x34,std::bit_cast<std::uint32_t>(target));
 }
};
actual4::SwayEndInvocationBindings12004 *current_end_binding=nullptr;
actual4::SwayCommonTerminationCallsiteBeforeAtSite12004 real_before=nullptr;
actual4::SwayCommonTerminationCallsiteAfter12004 real_after=nullptr;
int end_bind_calls=0,owned_original_calls=0,before_calls=0,after_calls=0;
World *active_world=nullptr;std::uint64_t expected_rdx=0,last_rdx=0,last_rax=0;
actual4::SwayCommonTerminationSite12004 expected_site=actual4::SwayCommonTerminationSite12004::call_2a48c7b;
constexpr std::uint64_t owned_return=0xFEDCBA9876543210ULL;
void BeforeMonitor(void *context,std::uintptr_t receiver,std::uint64_t rdx,actual4::SwayCommonTerminationSite12004 site)noexcept{
 ++before_calls;last_rdx=rdx;Check(active_world&&receiver==reinterpret_cast<std::uintptr_t>(active_world->scheme.data())&&rdx==expected_rdx&&site==expected_site,"installed state-bound before callback preserves actual receiver/full RDX/site");real_before(context,receiver,rdx,site);
}
void AfterMonitor(void *context,std::uint64_t rax)noexcept{++after_calls;last_rax=rax;Check(rax==owned_return,"actual after callback receives unmodified returned RAX bits without assigning semantics");real_after(context,rax);}
std::uint64_t OwnedOriginal(const void *receiver,std::uint64_t rdx){
 ++owned_original_calls;Check(active_world&&receiver==active_world->scheme.data()&&rdx==expected_rdx,"exactly forwarded owned original receives actual RCX/RDX unchanged");
 Put(active_world->scheme.data(),0x28,std::int32_t{1});Put(active_world->scheme.data(),0x2C,std::uint32_t{0xFFFFFFFF});return owned_return;
}
struct OwnedCode{
 void *reservation=nullptr;std::uintptr_t base=0;
 static constexpr std::size_t extent=0x2A50000;
 OwnedCode(){
  reservation=VirtualAlloc(nullptr,extent,MEM_RESERVE,PAGE_NOACCESS);if(!reservation)throw std::runtime_error("owned image reservation");base=reinterpret_cast<std::uintptr_t>(reservation);
  for(const auto rva:{0x1000u,0x2A48000u,0x2A4A000u})if(!VirtualAlloc(reinterpret_cast<void *>(base+rva),0x1000,MEM_COMMIT,PAGE_READWRITE))throw std::runtime_error("owned code commit");
  constexpr std::array<std::uint8_t,20> primary{0x48,0x8B,0xCF,0xE8,0x90,0x68,0,0,0x40,0x0F,0xB6,0xD6,0x48,0x8B,0xCF,0xE8,0x74,0x25,0,0};
  std::memcpy(reinterpret_cast<void *>(base+0x2A48868),primary.data(),primary.size());
  // Reviewed current4 anchor2A48C76, retained as fixture bytes, no Game file.
  constexpr std::array<std::uint8_t,10> second{0xB2,0x01,0x48,0x8B,0xCE,0xE8,0x70,0x21,0,0};
  std::memcpy(reinterpret_cast<void *>(base+0x2A48C76),second.data(),second.size());
  // Owned native target is an argument-preserving jump to the typed original.
  std::array<std::uint8_t,12> target{0x48,0xB8};const auto native=reinterpret_cast<std::uintptr_t>(&OwnedOriginal);std::memcpy(target.data()+2,&native,sizeof(native));target[10]=0xFF;target[11]=0xE0;std::memcpy(reinterpret_cast<void *>(base+0x2A4ADF0),target.data(),target.size());
  // Enter second site's actual MOV DL,1 / MOV RCX,RSI / CALL with the original
  // call-boundary stack alignment. The return epilogue is entirely fixture code.
  std::array<std::uint8_t,22> secondary_entry{0x56,0x48,0x83,0xEC,0x20,0x48,0x8B,0xF1,0x48,0xB8};auto anchor=base+0x2A48C76;std::memcpy(secondary_entry.data()+10,&anchor,sizeof(anchor));secondary_entry[18]=0xFF;secondary_entry[19]=0xE0;std::memcpy(reinterpret_cast<void *>(base+0x1000),secondary_entry.data(),20);
  constexpr std::array<std::uint8_t,6> second_continue{0x48,0x83,0xC4,0x20,0x5E,0xC3};std::memcpy(reinterpret_cast<void *>(base+0x2A48C80),second_continue.data(),second_continue.size());
  std::array<std::uint8_t,16> primary_entry{0x48,0x83,0xEC,0x28,0x48,0xB8};auto call=base+0x2A48877;std::memcpy(primary_entry.data()+6,&call,sizeof(call));primary_entry[14]=0xFF;primary_entry[15]=0xE0;std::memcpy(reinterpret_cast<void *>(base+0x1040),primary_entry.data(),primary_entry.size());
  constexpr std::array<std::uint8_t,5> primary_continue{0x48,0x83,0xC4,0x28,0xC3};std::memcpy(reinterpret_cast<void *>(base+0x2A4887C),primary_continue.data(),primary_continue.size());
  for(const auto rva:{0x1000u,0x2A48000u,0x2A4A000u}){DWORD previous{};if(!VirtualProtect(reinterpret_cast<void *>(base+rva),0x1000,PAGE_EXECUTE_READ,&previous))throw std::runtime_error("owned execute permission");}
  if(!FlushInstructionCache(GetCurrentProcess(),reservation,extent))throw std::runtime_error("owned cache flush");
 }
 ~OwnedCode(){if(reservation)VirtualFree(reservation,0,MEM_RELEASE);}
 std::uint64_t Run(bool second,const void *scheme,std::uint64_t rdx)const{return reinterpret_cast<std::uint64_t(*)(const void *,std::uint64_t)>(base+(second?0x1000:0x1040))(scheme,rdx);}
};
std::uintptr_t failed_patch_target=0;bool fail_patch_flush=false,flush_was_failed=false,rollback_was_failed=false;
void Reset(World &world,std::int32_t actor,std::int32_t status){Put(world.scheme.data(),0x28,status);Put(world.scheme.data(),0x2C,std::bit_cast<std::uint32_t>(actor));}
void Rebase(World &world,const actual4::SwayEndInvocationBindings12004 &binding,std::uintptr_t base){Put(world.type.data(),0,base+binding.state.type_vtable_rva);Put(world.scheme.data(),0,base+binding.state.instance_vtable_rva);}
void CodeByte(std::uintptr_t address,std::uint8_t value){DWORD previous{};if(!VirtualProtect(reinterpret_cast<void *>(address),1,PAGE_EXECUTE_READWRITE,&previous))throw std::runtime_error("owned code byte writable");Put(reinterpret_cast<void *>(address),0,value);DWORD ignored{};if(!FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void *>(address),1)||!VirtualProtect(reinterpret_cast<void *>(address),1,previous,&ignored))throw std::runtime_error("owned byte restored protection");}
void Wire(native::SwayTerminationRecorder12002 &recorder,std::int32_t actor,std::int32_t target,const std::string &name,std::size_t expected_rows,bool available,const std::filesystem::path &out){
 native::SwayTerminationQuery12002 request{std::bit_cast<std::uint32_t>(actor),std::bit_cast<std::uint32_t>(target),0,0};native::SwayTerminationQueryResult12002 result{};
 Check(recorder.Query(request,result)&&result.available&&result.common_native_end&&result.common_native_end->available==available&&result.common_native_end->records.size()==expected_rows,"actual recorder/query retains only eligible current-session rows");
 const auto body=native::SerializeSwayCompletionTermination12002(result);
 const bool second=name=="second-success";Check(body.find(second?"actual_2a48877_2a48c7b_2a4adf0_v2":"actual_2a48877_2a4adf0_v1")!=std::string::npos,"actual bare serializer family follows filtered records");
 if(result.common_native_end)for(const auto &row:result.common_native_end->records){const auto &o=row.observation;
  Check(o.entry.scheme_header_observed&&o.entry.scheme_full_id_observed&&o.entry.scheme_full_id_raw_u32==0&&o.entry.owner_character_full_id_raw_u32==std::bit_cast<std::uint32_t>(actor)&&o.entry.target_character_full_id_raw_u32==std::bit_cast<std::uint32_t>(target)&&o.returned.owner_character_full_id_raw_u32==0xFFFFFFFF,"actual field readers preserve full32 and raw owner clearance");
  Check(o.original_forwarded_once&&o.original_returned&&!o.stamp.incoming_return_address_observed&&!o.entry.core_frame_observed&&!o.returned.core_frame_observed,"actual return supplies no borrowed native stack/Core provenance");
 }
 std::ofstream file(out/(name+".json"),std::ios::binary);file<<body<<'\n';Check(file.good(),"retain actual bare serializer output");
}
}
// Test-only native API seam. Every non-targeted operation uses the actual OS.
// The target E9 is successfully written and protected/executable; only its
// instruction-cache acknowledgement and subsequent rollback-writable step fail.
BOOL WINAPI SwayFixtureVirtualProtect(LPVOID address,SIZE_T size,DWORD protection,PDWORD previous){
 if(fail_patch_flush&&flush_was_failed&&!rollback_was_failed&&reinterpret_cast<std::uintptr_t>(address)==failed_patch_target&&protection==PAGE_EXECUTE_READWRITE){rollback_was_failed=true;SetLastError(ERROR_ACCESS_DENIED);return FALSE;}
 return ::VirtualProtect(address,size,protection,previous);
}
BOOL WINAPI SwayFixtureFlushInstructionCache(HANDLE process,LPCVOID address,SIZE_T size){
 if(fail_patch_flush&&!flush_was_failed&&reinterpret_cast<std::uintptr_t>(address)==failed_patch_target){flush_was_failed=true;SetLastError(ERROR_INVALID_FUNCTION);return FALSE;}
 return ::FlushInstructionCache(process,address,size);
}
namespace xar::ck3_12004 {
// Command construction is outside this CommonEnd fixture. Keep an explicit
// aborting acquisition boundary rather than linking an unrelated adapter.
ck3_12002::CommandBindings BindCommandImage12004(std::uintptr_t,std::string_view)noexcept{NotExercised();}
SwayEndInvocationBindings12004 BindSwayEndInvocationImage12004(std::uintptr_t base,std::string_view sha)noexcept{
 ++end_bind_calls;if(!current_end_binding||base!=current_end_binding->image_base||sha!=kExecutableSha256)NotExercised();return *current_end_binding;
}
}
int main(int argc,char **argv){try{
 if(argc!=2)throw std::runtime_error("artifact directory");const std::filesystem::path output(argv[1]);std::filesystem::create_directories(output);OwnedCode code;
 constexpr std::int32_t actor=-2,target=0;World world(actor,target);auto binding=actual4::SwayFixtureBindEndImage12004(code.base,actual4::kExecutableSha256);current_end_binding=&binding;active_world=&world;Rebase(world,binding,code.base);
 const auto first_session=actual4::BeginSwayCausalObserverSession12004();native::SwayTerminationRecorder12002 old_recorder;actual4::SwayCommonTerminationCallsiteObserver12004Environment environment{};
 Check(native::BuildSwayCommonTerminationObserverEnvironment12004(code.base,actual4::kExecutableSha256,old_recorder,environment)&&environment.before_at_site&&environment.after,"actual first-session environment");
 real_before=environment.before_at_site;real_after=environment.after;environment.before_at_site=&BeforeMonitor;environment.after=&AfterMonitor;environment.primary_thread_suspended_proven=true;
 actual4::SwayCommonTerminationCallsiteObserver12004State failed_primary{},second{};
 failed_patch_target=code.base+0x2A48877;fail_patch_flush=true;const bool primary_result=actual4::InstallSwayCommonTerminationCallsiteObserver12004(failed_primary,environment);fail_patch_flush=false;
 Check(!primary_result&&failed_primary.installed.load()&&failed_primary.stub&&flush_was_failed&&rollback_was_failed,"actual production WritePatch reaches restore_unproven with retained executable stub and failed Install result");
 Check(*reinterpret_cast<const std::uint8_t *>(failed_patch_target)==0xE9&&(failed_primary.failure_flags.load()&actual4::sway_common_observer_failure_restore)!=0,"uncertain backing retains actual already-written E9 and restore failure flag");
 environment.site=actual4::SwayCommonTerminationSite12004::call_2a48c7b;CodeByte(code.base+0x2A48C76,0xB3);
 Check(!actual4::InstallSwayCommonTerminationCallsiteObserver12004(second,environment)&&!second.installed.load()&&!second.stub&&failed_primary.installed.load(),"bad second anchor leaves retained other-site owner/backing untouched");CodeByte(code.base+0x2A48C76,0xB2);
 const bool second_result=actual4::InstallSwayCommonTerminationCallsiteObserver12004(second,environment);Check(second_result,"other site independently succeeds after exact anchor restoration");
 old_recorder.SetObserverAttached(true);old_recorder.SetCommonNativeEndObserverAttached12004(primary_result||second_result);
 expected_site=actual4::SwayCommonTerminationSite12004::call_2a48877;expected_rdx=0x123456789ABCDE02ULL;Reset(world,actor,0);
 Check(code.Run(false,world.scheme.data(),expected_rdx)==owned_return&&owned_original_calls==1,"failed retained site's real stub still forwards its original exactly once and returns");
 const auto failed_diag=actual4::ReadSwayCommonTerminationCallsiteObserver12004Diagnostics(failed_primary);
 Check(failed_diag.before_count==1&&failed_diag.returned_count==1&&before_calls==0&&after_calls==0,"retained failed-site thunk diagnostics count actual return but do not invoke recorder callbacks");
 Wire(old_recorder,actor,target,"failed-primary-filtered",0,true,output);
 expected_site=actual4::SwayCommonTerminationSite12004::call_2a48c7b;expected_rdx=0xFEDCBA9876543201ULL;Reset(world,actor,1);
 Check(code.Run(true,world.scheme.data(),0xFEDCBA98765432FFULL)==owned_return&&owned_original_calls==2,"successful second site remains admitted and forwarded once");Wire(old_recorder,actor,target,"second-success",1,true,output);
 actual4::EndSwayCausalObserverSession12004(first_session);const auto next_session=actual4::BeginSwayCausalObserverSession12004();Check(next_session!=0&&next_session!=first_session,"real observer session identity changes while both site stubs remain owned");
 Reset(world,actor,1);Check(code.Run(true,world.scheme.data(),0xFEDCBA98765432FFULL)==owned_return&&owned_original_calls==3,"old-session successful stub still forwards actual original once after session change");Wire(old_recorder,actor,target,"session-rotated",0,false,output);
 Check(actual4::UninstallSwayCommonTerminationCallsiteObserver12004(failed_primary,true)&&failed_primary.stub==nullptr&&second.installed.load(),"proved restoration reclaims only uncertain site's backing while independent site remains installed");
 Check(actual4::UninstallSwayCommonTerminationCallsiteObserver12004(second,true)&&second.stub==nullptr,"other site independently restores/releases after old session");
 native::SwayTerminationRecorder12002 fresh;actual4::SwayCommonTerminationCallsiteObserver12004Environment fresh_environment{};Check(native::BuildSwayCommonTerminationObserverEnvironment12004(code.base,actual4::kExecutableSha256,fresh,fresh_environment),"new recorder binds actual new current session");
 real_before=fresh_environment.before_at_site;real_after=fresh_environment.after;fresh_environment.before_at_site=&BeforeMonitor;fresh_environment.after=&AfterMonitor;fresh_environment.primary_thread_suspended_proven=true;
 actual4::SwayCommonTerminationCallsiteObserver12004State fresh_primary{},fresh_second{};Check(actual4::InstallSwayCommonTerminationCallsiteObserver12004(fresh_primary,fresh_environment),"fresh primary installs after complete prior-owner restoration");fresh_environment.site=actual4::SwayCommonTerminationSite12004::call_2a48c7b;Check(actual4::InstallSwayCommonTerminationCallsiteObserver12004(fresh_second,fresh_environment),"fresh second site simultaneously installs under new session");
 fresh.SetObserverAttached(true);fresh.SetCommonNativeEndObserverAttached12004(true);Reset(world,actor,1);expected_site=actual4::SwayCommonTerminationSite12004::call_2a48877;expected_rdx=0x123456789ABCDE02ULL;
 Check(code.Run(false,world.scheme.data(),expected_rdx)==owned_return&&owned_original_calls==4,"fresh primary-only observation is eligible in current session");Wire(fresh,actor,target,"recovered-primary",1,true,output);Wire(fresh,actor,1,"filtered-empty",0,true,output);
 const bool second_restored=actual4::UninstallSwayCommonTerminationCallsiteObserver12004(fresh_second,true);const bool primary_restored=actual4::UninstallSwayCommonTerminationCallsiteObserver12004(fresh_primary,true);
 Check(second_restored&&primary_restored&&fresh_second.stub==nullptr&&fresh_primary.stub==nullptr,"fresh dual backing reclaimed after last new observation");actual4::EndSwayCausalObserverSession12004(next_session);
 Check(owned_original_calls==4&&before_calls==3&&after_calls==3&&end_bind_calls==6&&abort_calls==0&&actual4::CurrentSwayCausalObserverSession12004()==0,"all new original calls return once; only successful/current captures read native fields; session clean");
 std::cout<<"PERSISTENT_COMMON_FAILURE CHECKS "<<checks<<" FAILED "<<failures<<" ORIGINAL "<<owned_original_calls<<" CALLBACK_BEFORE "<<before_calls<<" CALLBACK_AFTER "<<after_calls<<" END_BIND "<<end_bind_calls<<" FLUSH_FAULT "<<flush_was_failed<<" ROLLBACK_FAULT "<<rollback_was_failed<<" ABORT "<<abort_calls<<"; actual restore_unproven+other-site success+session rotation; repository actual source; no Game/cause credit\n";return failures?1:0;
 }catch(const std::exception &e){std::cerr<<"ERROR "<<e.what()<<'\n';return 2;}}
