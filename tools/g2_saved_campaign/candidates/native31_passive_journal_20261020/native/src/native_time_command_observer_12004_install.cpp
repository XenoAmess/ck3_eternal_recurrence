#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <intrin.h>
#include <array>
#include <cstring>
#include "xar_bridge/native_time_command_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004::time_observer31 {
namespace {
using CloneFn=CloneNative;
using DeleteFn=DeleteNative;
using ExecuteFn=ExecuteNative;
using AppendFn=AppendNative;
Environment environment{};
std::atomic<bool> attached{};
CloneFn clone_original{};
DeleteFn delete_original{};
ExecuteFn execute_original{};
AppendFn append_original{};
constexpr std::array<std::uint8_t,15> prologue{
 0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c,0x24,0x20};
template<class T>bool Read(std::uintptr_t p,T& out) noexcept {
 if(!p)return false;
 __try {std::memcpy(&out,reinterpret_cast<const void*>(p),sizeof(T));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
std::uintptr_t Rva(const void* pc) noexcept {
 const auto address=reinterpret_cast<std::uintptr_t>(pc);
 return address>=environment.image_base?address-environment.image_base:0;
}
void** __fastcall CloneHook(const void* source,void** storage) {
 return ForwardClone(clone_original,source,storage,Rva(_ReturnAddress()));
}
void* __fastcall DeleteHook(void* object,std::uint32_t flags) {
 return ForwardDelete(delete_original,object,flags,Rva(_ReturnAddress()));
}
void __fastcall ExecuteHook(void* secondary) {
 ForwardExecute(execute_original,secondary,Rva(_ReturnAddress()));
}
void** __fastcall AppendHook(void* container,void** source) {
 return ForwardAppend(append_original,container,source,Rva(_ReturnAddress()));
}
bool Slot(void** slot,void* expected,void* replacement,bool& changed,DWORD& original_protection) noexcept {
 changed=false;DWORD old{};
 if(!VirtualProtect(slot,sizeof(*slot),PAGE_READWRITE,&old))return false;
 original_protection=old;
 const auto found=InterlockedCompareExchangePointer(
   reinterpret_cast<void* volatile*>(slot),replacement,expected);
 changed=found==expected;
 DWORD ignored{};const bool restored=VirtualProtect(slot,sizeof(*slot),old,&ignored)!=FALSE;
 return changed&&restored;
}
void Jump(std::uint8_t* out,const void* target) noexcept {
 out[0]=0xff;out[1]=0x25;std::memset(out+2,0,4);
 std::memcpy(out+6,&target,8);
}
bool Patch(void* target,const std::array<std::uint8_t,15>& expected,
           const std::array<std::uint8_t,15>& replacement,bool& changed,DWORD& original_protection) noexcept {
 changed=false;std::array<std::uint8_t,15> current{};
 if(!Read(reinterpret_cast<std::uintptr_t>(target),current)||current!=expected)return false;
 DWORD old{};if(!VirtualProtect(target,15,PAGE_EXECUTE_READWRITE,&old))return false;
 original_protection=old;
 std::memcpy(target,replacement.data(),15);changed=true;
 DWORD ignored{};const bool restored=VirtualProtect(target,15,old,&ignored)!=FALSE;
 const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,15)!=FALSE;
 return restored&&flushed;
}
}
bool ReadPointer(const void* address,void*& out) noexcept {
 return Read(reinterpret_cast<std::uintptr_t>(address),out);
}
bool ExpectedContainer(const void* container) noexcept {
 std::uintptr_t expected{};return Read(environment.image_base+0x5CC1240+0x3D0,expected)&&
  expected==reinterpret_cast<std::uintptr_t>(container);
}
bool Attached() noexcept {return attached.load(std::memory_order_acquire);}
Environment Identity() noexcept {return environment;}
std::uint64_t Clock() noexcept {
 LARGE_INTEGER value{};return QueryPerformanceCounter(&value)?
   static_cast<std::uint64_t>(value.QuadPart):0;
}
std::uint32_t Thread() noexcept {return GetCurrentThreadId();}
bool IsPauseObject(const void* object) noexcept {
 if(!Attached())return false;
 std::uintptr_t primary{},secondary{};
 return Read(reinterpret_cast<std::uintptr_t>(object),primary)&&
   Read(reinterpret_cast<std::uintptr_t>(object)+0x18,secondary)&&
   primary==environment.image_base+0x476C8A8&&secondary==environment.image_base+0x476C878;
}
bool ReadPayload(const void* object,std::int32_t& player,std::uint8_t& paused,std::uint32_t& sequence) noexcept {
 if(!object)return false;
 return Read(reinterpret_cast<std::uintptr_t>(object)+0x0C,sequence)&&
   Read(reinterpret_cast<std::uintptr_t>(object)+0x20,player)&&
   Read(reinterpret_cast<std::uintptr_t>(object)+0x24,paused);
}
Scalar ReadScalar() noexcept {
 Scalar out{};if(!Attached())return out;
 std::uintptr_t game_again{},jomini_again{};
 const auto base=environment.image_base;
 out.valid=Read(base+kGameStateSlotRva,out.game)&&out.game&&
   Read(base+kJominiStateSlotRva,out.jomini)&&out.jomini&&
   Read(out.game+kGameStateDateOffset,out.date)&&
   Read(out.jomini+kJominiPausedOffset,out.paused)&&
   Read(base+kGameStateSlotRva,game_again)&&game_again==out.game&&
   Read(base+kJominiStateSlotRva,jomini_again)&&jomini_again==out.jomini?1:0;
 if(!out.valid)GapFlag(unreadable);
 return out;
}
InstallResult Install(const Environment& input,std::string_view sha,bool suspended) noexcept {
 // One startup-only installation; no hot patch/unload path is offered.
 if(attached.load(std::memory_order_acquire)||environment.image_base||
    !suspended||!input.exact_build_admitted||input.image_base==0||sha!=kExecutableSha256)return InstallResult::unavailable_clean;
 const auto base=input.image_base;
 std::array<void**,3> slots{
  reinterpret_cast<void**>(base+0x476C8A8+0x40),
  reinterpret_cast<void**>(base+0x476C8A8),
  reinterpret_cast<void**>(base+0x476C878+8)};
 std::array<void*,3> originals{
  reinterpret_cast<void*>(base+0x2987CE0),
  reinterpret_cast<void*>(base+0x86BF20),
  reinterpret_cast<void*>(base+0x2987950)};
 const std::array<void*,3> wrappers{
  reinterpret_cast<void*>(&CloneHook),reinterpret_cast<void*>(&DeleteHook),
  reinterpret_cast<void*>(&ExecuteHook)};
 for(std::size_t i=0;i<slots.size();++i){void* current{};
   if(!Read(reinterpret_cast<std::uintptr_t>(slots[i]),current)||current!=originals[i])return InstallResult::unavailable_clean;}
 const auto target=reinterpret_cast<void*>(base+0x880340);
 std::array<std::uint8_t,15> current{};
 if(!Read(reinterpret_cast<std::uintptr_t>(target),current)||current!=prologue)return InstallResult::unavailable_clean;
 // Execute bytes are checked without rewriting its RIP-relative operand.
 std::array<std::uint8_t,20> actual_execute{};
 constexpr std::array<std::uint8_t,20> expected_execute{
 0x44,0x8b,0x41,0x08,0x0f,0xb6,0x51,0x0c,0x48,0x8b,0x0d,0xc1,0x2b,0x2e,0x03,
 0xe9,0x7c,0x6a,0xeb,0x00};
 if(!Read(base+0x2987950,actual_execute)||actual_execute!=expected_execute)return InstallResult::unavailable_clean;
 auto* memory=static_cast<std::uint8_t*>(VirtualAlloc(nullptr,4096,
    MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
 if(!memory)return InstallResult::unavailable_clean;
 std::memcpy(memory,prologue.data(),15);
 Jump(memory+15,reinterpret_cast<void*>(base+0x88034F));
 DWORD old{};
 if(!VirtualProtect(memory,4096,PAGE_EXECUTE_READ,&old)||
    !FlushInstructionCache(GetCurrentProcess(),memory,29)){
  VirtualFree(memory,0,MEM_RELEASE);return InstallResult::unavailable_clean;}
 HMODULE pinned{};
 if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
     reinterpret_cast<LPCWSTR>(reinterpret_cast<void*>(&Install)),&pinned)){
  VirtualFree(memory,0,MEM_RELEASE);return InstallResult::unavailable_clean;}
 environment=input;
 LARGE_INTEGER frequency{};
 if(!QueryPerformanceFrequency(&frequency)||frequency.QuadPart<=0){
  environment={};VirtualFree(memory,0,MEM_RELEASE);return InstallResult::unavailable_clean;}
 environment.qpc_frequency=static_cast<std::uint64_t>(frequency.QuadPart);
 environment.process_id=GetCurrentProcessId();
 FILETIME creation{},exit{},kernel{},user{};
 if(!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)){
  environment={};VirtualFree(memory,0,MEM_RELEASE);return InstallResult::unavailable_clean;}
 environment.process_birth=(static_cast<std::uint64_t>(creation.dwHighDateTime)<<32)|
   creation.dwLowDateTime;
 clone_original=reinterpret_cast<CloneFn>(originals[0]);
 delete_original=reinterpret_cast<DeleteFn>(originals[1]);
 execute_original=reinterpret_cast<ExecuteFn>(originals[2]);
 append_original=reinterpret_cast<AppendFn>(memory);
 std::array<std::uint8_t,15> patch{};Jump(patch.data(),reinterpret_cast<void*>(&AppendHook));
 patch[14]=0x90;
 std::array<bool,3> changed{};std::array<DWORD,3> initial_protections{};
 DWORD initial_code_protection{};bool code_changed=false;bool installed=true;
 for(std::size_t i=0;i<slots.size();++i)if(!Slot(slots[i],originals[i],wrappers[i],changed[i],initial_protections[i])){
   installed=false;break;}
 if(installed)installed=Patch(target,prologue,patch,code_changed,initial_code_protection);
 if(!installed) {
  bool safe=true,rolled=false;
  if(code_changed){
   DWORD previous{};
   safe=Patch(target,patch,prologue,rolled,previous)&&rolled;
   const bool protected_again=VirtualProtect(target,15,initial_code_protection,&previous)!=FALSE;
   safe=protected_again&&safe;
  }
  for(std::size_t i=slots.size();i-->0;)if(changed[i]){
   bool restored=false;DWORD previous{};
   const bool ok=Slot(slots[i],wrappers[i],originals[i],restored,previous);
   const bool protected_again=VirtualProtect(slots[i],sizeof(*slots[i]),initial_protections[i],&previous)!=FALSE;
   safe=ok&&restored&&protected_again&&safe;
  }
  // Original pointers and trampoline deliberately remain pinned even on failure.
  // The producer launch gate requires Install==true; rollback failure is RED.
  GapFlag(identity_drift);return safe?InstallResult::unavailable_clean:InstallResult::rollback_unsafe;
 }
 attached.store(true,std::memory_order_release);return InstallResult::active;
}
} // namespace xar::ck3_12004::time_observer31
