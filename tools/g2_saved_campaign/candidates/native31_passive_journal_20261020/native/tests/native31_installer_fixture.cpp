#ifdef NDEBUG
#undef NDEBUG
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#if !defined(_WIN64) || !defined(_M_X64)
#error Native31 installer fixture requires MSVC Win64 x64.
#endif
static_assert(sizeof(void*)==8);
#include <intrin.h>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <type_traits>
#include "xar_bridge/native_time_command_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

// This translation unit includes the production installer body unchanged.
// Compile the production core separately; never link the installer twice.
namespace fixture31 {
enum class Failure : std::uint8_t { none, allocation, pin, frequency, process_times };
struct ApiState {
 std::uint32_t alloc{},free{},protect{},flush{},pin{},frequency{},times{};
 std::array<std::uint32_t,2> fail_protect{},fail_flush{};
 Failure failure{Failure::none};
};
ApiState api{};
bool Hit(std::uint32_t n,const std::array<std::uint32_t,2>& values) noexcept {
 return (values[0]!=0 && values[0]==n)||(values[1]!=0 && values[1]==n);
}
}
static LPVOID WINAPI N31FixtureVirtualAlloc(LPVOID p,SIZE_T bytes,DWORD kind,DWORD protect) {
 ++fixture31::api.alloc;
 if(fixture31::api.failure==fixture31::Failure::allocation)return nullptr;
 return ::VirtualAlloc(p,bytes,kind,protect);
}
static BOOL WINAPI N31FixtureVirtualFree(LPVOID p,SIZE_T bytes,DWORD kind) {
 ++fixture31::api.free;return ::VirtualFree(p,bytes,kind);
}
static BOOL WINAPI N31FixtureVirtualProtect(LPVOID p,SIZE_T bytes,DWORD protect,PDWORD old) {
 const auto n=++fixture31::api.protect;
 if(fixture31::Hit(n,fixture31::api.fail_protect))return FALSE;
 return ::VirtualProtect(p,bytes,protect,old);
}
static BOOL WINAPI N31FixtureFlushInstructionCache(HANDLE process,LPCVOID p,SIZE_T bytes) {
 const auto n=++fixture31::api.flush;
 if(fixture31::Hit(n,fixture31::api.fail_flush))return FALSE;
 return ::FlushInstructionCache(process,p,bytes);
}
static BOOL WINAPI N31FixtureGetModuleHandleExW(DWORD flags,LPCWSTR name,HMODULE* module) {
 ++fixture31::api.pin;
 if(fixture31::api.failure==fixture31::Failure::pin)return FALSE;
 return ::GetModuleHandleExW(flags,name,module);
}
static BOOL WINAPI N31FixtureQueryPerformanceFrequency(LARGE_INTEGER* frequency) {
 ++fixture31::api.frequency;
 if(fixture31::api.failure==fixture31::Failure::frequency)return FALSE;
 return ::QueryPerformanceFrequency(frequency);
}
static BOOL WINAPI N31FixtureGetProcessTimes(HANDLE process,LPFILETIME creation,
 LPFILETIME exit,LPFILETIME kernel,LPFILETIME user) {
 ++fixture31::api.times;
 if(fixture31::api.failure==fixture31::Failure::process_times)return FALSE;
 return ::GetProcessTimes(process,creation,exit,kernel,user);
}
#define VirtualAlloc N31FixtureVirtualAlloc
#define VirtualFree N31FixtureVirtualFree
#define VirtualProtect N31FixtureVirtualProtect
#define FlushInstructionCache N31FixtureFlushInstructionCache
#define GetModuleHandleExW N31FixtureGetModuleHandleExW
#define QueryPerformanceFrequency N31FixtureQueryPerformanceFrequency
#define GetProcessTimes N31FixtureGetProcessTimes
#ifndef NATIVE31_INSTALLER_SOURCE
#define NATIVE31_INSTALLER_SOURCE "D:/codex-ck3-demos/2026-10-20-native31-passive-prepare01/source/ck3_autonomous_player/native_bridge/src/native_time_command_observer_12004_install.cpp"
#endif
#include NATIVE31_INSTALLER_SOURCE
#undef VirtualAlloc
#undef VirtualFree
#undef VirtualProtect
#undef FlushInstructionCache
#undef GetModuleHandleExW
#undef QueryPerformanceFrequency
#undef GetProcessTimes

namespace fixture31 {
namespace observer=xar::ck3_12004::time_observer31;
constexpr std::uintptr_t kImageBytes=0x6000000;
constexpr std::uintptr_t kClone=0x2987CE0,kDelete=0x86BF20,kExecute=0x2987950;
constexpr std::uintptr_t kAppend=0x880340,kWrapper=0x383E3E0;
constexpr std::uintptr_t kPrimary=0x476C8A8,kSecondary=0x476C878,kManager=0x5CC1240;
constexpr std::uintptr_t kCallerA=0x37F0794,kCallerB=0x37F07AD;
constexpr std::array<std::uint8_t,15> kAppendPrefix{
 0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c,0x24,0x20};
constexpr std::array<std::uint8_t,20> kExecuteBytes{
 0x44,0x8b,0x41,0x08,0x0f,0xb6,0x51,0x0c,0x48,0x8b,0x0d,0xc1,0x2b,0x2e,0x03,
 0xe9,0x7c,0x6a,0xeb,0x00};
struct Page {
 std::uintptr_t rva{};DWORD protection{};
 std::array<std::uint8_t,4096> original{};
};
struct PauseObject {
 void* primary{};
 std::uint8_t flags{8};std::array<std::uint8_t,3> padding9{};
 std::uint32_t sequence{0x1234};std::uint64_t padding10{};
 void* secondary{};std::int32_t player{};std::uint8_t paused{1};
 std::array<std::uint8_t,3> padding25{};
};
static_assert(sizeof(PauseObject)==0x28 && offsetof(PauseObject,sequence)==0xC &&
 offsetof(PauseObject,secondary)==0x18 && offsetof(PauseObject,player)==0x20 &&
 offsetof(PauseObject,paused)==0x24);
struct Container {
 void** array{};std::uint32_t capacity{8},size{};void* allocator{};
};
static_assert(offsetof(Container,size)==0xC);
enum class ThrowKind : std::uint8_t { none,clone,erase,execute,append };
struct NativeSignal { ThrowKind kind; };
struct Counts { std::uint32_t clone{},erase{},execute{},append{}; };
struct World {
 std::uint8_t* image{};std::array<Page,9> pages{};std::size_t page_count{};
 std::array<RUNTIME_FUNCTION,2> functions{};bool unwind_registered{};
 std::array<std::uint8_t,0x100> game{},jomini{};
 PauseObject source{},clone{};std::array<void*,8> array{};Container container{};
 Counts calls{};ThrowKind throwing{ThrowKind::none};bool native_arguments_valid{true};
 ~World() noexcept {
  if(unwind_registered)RtlDeleteFunctionTable(functions.data());
  if(image)::VirtualFree(image,0,MEM_RELEASE);
 }
};
World* world{};
const char* error{};
bool Check(bool value,const char* message) noexcept {
 if(!value && error==nullptr)error=message;
 return value;
}
void** FakeClone(const void* source,void** storage) {
 ++world->calls.clone;
 if(world->throwing==ThrowKind::clone)throw NativeSignal{ThrowKind::clone};
 world->clone=*static_cast<const PauseObject*>(source);
 *storage=&world->clone;return storage;
}
void* FakeDelete(void* object,std::uint32_t flags) {
 ++world->calls.erase;
 world->native_arguments_valid=world->native_arguments_valid &&
  object==&world->clone && flags==1;
 if(world->throwing==ThrowKind::erase)throw NativeSignal{ThrowKind::erase};
 return object;
}
void FakeExecute(void* jomini,std::uint32_t paused,std::uint32_t player) {
 ++world->calls.execute;
 world->native_arguments_valid=world->native_arguments_valid &&
  jomini==world->jomini.data() && paused==1 && player==0;
 if(world->throwing==ThrowKind::execute)throw NativeSignal{ThrowKind::execute};
 world->jomini[xar::ck3_12004::kJominiPausedOffset]=static_cast<std::uint8_t>(paused);
}
void** FakeAppend(void* container,void** source) {
 ++world->calls.append;
 world->native_arguments_valid=world->native_arguments_valid &&
  container==&world->container && source!=nullptr && *source==&world->clone;
 if(world->throwing==ThrowKind::append)throw NativeSignal{ThrowKind::append};
 auto* c=static_cast<Container*>(container);
 if(c->size>=c->capacity)throw NativeSignal{ThrowKind::append};
 c->array[c->size]=*source;return &c->array[c->size++];
}
void AbsoluteJump(std::uint8_t* out,const void* destination) noexcept {
 out[0]=0xff;out[1]=0x25;std::memset(out+2,0,4);
 std::memcpy(out+6,&destination,sizeof(destination));
}
template<class T>void Put(World& w,std::uintptr_t rva,const T& value) noexcept {
 static_assert(std::is_trivially_copyable_v<T>);
 std::memcpy(w.image+rva,&value,sizeof(value));
}
std::uintptr_t Address(World& w,std::uintptr_t rva) noexcept {
 return reinterpret_cast<std::uintptr_t>(w.image)+rva;
}
bool AddPage(World& w,std::uintptr_t rva,DWORD protection) noexcept {
 rva&=~std::uintptr_t{4095};
 for(std::size_t i=0;i<w.page_count;++i)if(w.pages[i].rva==rva)return true;
 if(w.page_count==w.pages.size())return Check(false,"page_capacity");
 auto* allocated=::VirtualAlloc(w.image+rva,4096,MEM_COMMIT,PAGE_READWRITE);
 if(allocated!=w.image+rva)return Check(false,"commit_page");
 auto& page=w.pages[w.page_count++];page.rva=rva;page.protection=protection;
 return true;
}
DWORD Protection(const void* p) noexcept {
 MEMORY_BASIC_INFORMATION m{};
 return VirtualQuery(p,&m,sizeof(m))==sizeof(m)?m.Protect:0;
}
void MakeCaller(World& w,std::size_t index,std::uintptr_t return_rva) noexcept {
 const auto start=return_rva-16;
 auto* code=w.image+start;
 const std::array<std::uint8_t,4> subtract{0x48,0x83,0xec,0x28};
 std::memcpy(code,subtract.data(),subtract.size());
 code[4]=0x48;code[5]=0xb8;
 const auto target=Address(w,kAppend);std::memcpy(code+6,&target,8);
 code[14]=0xff;code[15]=0xd0;
 const std::array<std::uint8_t,5> finish{0x48,0x83,0xc4,0x28,0xc3};
 std::memcpy(code+16,finish.data(),finish.size());
 const auto unwind=std::uintptr_t{0x37F0F00}+index*8;
 // Version 1; 4-byte prologue; UWOP_ALLOC_SMALL 40; no handler/chaining.
 const std::array<std::uint8_t,8> info{1,4,1,0,4,0x42,0,0};
 std::memcpy(w.image+unwind,info.data(),info.size());
 w.functions[index]={static_cast<DWORD>(start),static_cast<DWORD>(start+21),
  static_cast<DWORD>(unwind)};
}
bool Prepare(World& w,std::string_view mode) noexcept {
 w.image=static_cast<std::uint8_t*>(
  ::VirtualAlloc(nullptr,kImageBytes,MEM_RESERVE,PAGE_NOACCESS));
 if(!w.image)return Check(false,"reserve_image");
 for(auto rva:{kClone,kDelete,kExecute,kAppend,kWrapper,kCallerA,kPrimary,kManager})
  if(!AddPage(w,rva,rva==kPrimary||rva==kManager?PAGE_READONLY:PAGE_EXECUTE_READ))return false;
 if(!AddPage(w,xar::ck3_12004::kGameStateSlotRva,PAGE_READONLY) ||
    !AddPage(w,xar::ck3_12004::kJominiStateSlotRva,PAGE_READONLY))return false;
 AbsoluteJump(w.image+kClone,reinterpret_cast<const void*>(&FakeClone));
 AbsoluteJump(w.image+kDelete,reinterpret_cast<const void*>(&FakeDelete));
 std::memcpy(w.image+kExecute,kExecuteBytes.data(),kExecuteBytes.size());
 AbsoluteJump(w.image+kWrapper,reinterpret_cast<const void*>(&FakeExecute));
 std::memcpy(w.image+kAppend,kAppendPrefix.data(),kAppendPrefix.size());
 AbsoluteJump(w.image+kAppend+15,reinterpret_cast<const void*>(&FakeAppend));
 Put(w,kPrimary+0x40,Address(w,kClone));Put(w,kPrimary,Address(w,kDelete));
 Put(w,kSecondary+8,Address(w,kExecute));
 MakeCaller(w,0,kCallerA);MakeCaller(w,1,kCallerB);
 w.container.array=w.array.data();
 Put(w,kManager+0x3D0,reinterpret_cast<std::uintptr_t>(&w.container));
 Put(w,xar::ck3_12004::kGameStateSlotRva,
  reinterpret_cast<std::uintptr_t>(w.game.data()));
 Put(w,xar::ck3_12004::kJominiStateSlotRva,
  reinterpret_cast<std::uintptr_t>(w.jomini.data()));
 const std::int32_t date=53274624;
 std::memcpy(w.game.data()+xar::ck3_12004::kGameStateDateOffset,&date,sizeof(date));
 w.source.primary=w.image+kPrimary;w.source.secondary=w.image+kSecondary;
 if(mode=="slot-clone")Put(w,kPrimary+0x40,Address(w,kClone)+1);
 if(mode=="slot-delete")Put(w,kPrimary,Address(w,kDelete)+1);
 if(mode=="slot-execute")Put(w,kSecondary+8,Address(w,kExecute)+1);
 if(mode=="append-prefix")w.image[kAppend]^=1;
 if(mode=="execute-bytes")w.image[kExecute+11]^=1;
 for(std::size_t i=0;i<w.page_count;++i) {
  auto& p=w.pages[i];std::memcpy(p.original.data(),w.image+p.rva,4096);
  DWORD old{};
  if(!::VirtualProtect(w.image+p.rva,4096,p.protection,&old))return Check(false,"seal_page");
  if(!::FlushInstructionCache(GetCurrentProcess(),w.image+p.rva,4096))
   return Check(false,"seal_flush");
 }
 w.unwind_registered=RtlAddFunctionTable(w.functions.data(),
  static_cast<DWORD>(w.functions.size()),reinterpret_cast<DWORD64>(w.image))!=FALSE;
 return Check(w.unwind_registered,"register_unwind");
}
bool ImageUnchanged(const World& w,bool check_bytes=true) noexcept {
 bool valid=true;
 for(std::size_t i=0;i<w.page_count;++i) {
  const auto& p=w.pages[i];
  if(check_bytes)valid=Check(std::memcmp(p.original.data(),w.image+p.rva,4096)==0,
    "image_bytes_changed")&&valid;
  valid=Check(Protection(w.image+p.rva)==p.protection,"page_protection_changed")&&valid;
 }
 return valid;
}
template<class Fn>Fn SlotAt(World& w,std::uintptr_t rva) noexcept {
 Fn value{};std::memcpy(&value,w.image+rva,sizeof(value));return value;
}
bool ActivePatch(World& w) noexcept {
 bool valid=ImageUnchanged(w,false);
 valid=Check(std::memcmp(w.image+kExecute,kExecuteBytes.data(),20)==0,"execute_rewritten")&&valid;
 valid=Check(w.image[kAppend]==0xff && w.image[kAppend+1]==0x25 &&
  w.image[kAppend+14]==0x90,"detour_encoding")&&valid;
 valid=Check(SlotAt<observer::CloneNative>(w,kPrimary+0x40)!=
  reinterpret_cast<observer::CloneNative>(w.image+kClone),"clone_slot_not_installed")&&valid;
 valid=Check(SlotAt<observer::DeleteNative>(w,kPrimary)!=
  reinterpret_cast<observer::DeleteNative>(w.image+kDelete),"delete_slot_not_installed")&&valid;
 valid=Check(SlotAt<observer::ExecuteNative>(w,kSecondary+8)!=
  reinterpret_cast<observer::ExecuteNative>(w.image+kExecute),"execute_slot_not_installed")&&valid;
 for(std::size_t i=0;i<w.page_count;++i) {
  auto expected=w.pages[i].original;
  const auto page=w.pages[i].rva;
  for(auto rva:{kPrimary+0x40,kPrimary,kSecondary+8})
   if((rva&~std::uintptr_t{4095})==page)
    std::memcpy(expected.data()+(rva-page),w.image+rva,sizeof(void*));
  if((kAppend&~std::uintptr_t{4095})==page)
   std::memcpy(expected.data()+(kAppend-page),w.image+kAppend,15);
  valid=Check(std::memcmp(expected.data(),w.image+page,4096)==0,
   "unexpected_image_write")&&valid;
 }
 return valid;
}
bool SameIdentity(const observer::Environment& identity,World& w) noexcept {
 FILETIME creation{},exit{},kernel{},user{};
 const bool times=::GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)!=FALSE;
 const auto birth=(static_cast<std::uint64_t>(creation.dwHighDateTime)<<32)|creation.dwLowDateTime;
 LARGE_INTEGER frequency{};
 const bool qpc=::QueryPerformanceFrequency(&frequency)!=FALSE;
 return Check(identity.image_base==Address(w,0) && identity.process_id==GetCurrentProcessId() &&
  times && identity.process_birth==birth && qpc &&
  identity.qpc_frequency==static_cast<std::uint64_t>(frequency.QuadPart) &&
  identity.exact_build_admitted,"identity_readback");
}
std::uint32_t Count(const observer::Dump& dump,observer::Kind kind) noexcept {
 std::uint32_t count{};
 for(std::uint32_t i=0;i<dump.count;++i)if(dump.events[i].kind==kind)++count;
 return count;
}

bool ProbeReads(World& w) noexcept {
 std::int32_t player{-1};std::uint8_t paused{};std::uint32_t sequence{};
 void* out{};
 return Check(observer::IsPauseObject(&w.source),"pause_object_readback") &&
  Check(observer::ReadPayload(&w.source,player,paused,sequence) &&
   player==0 && paused==1 && sequence==0x1234,"payload_readback") &&
  Check(observer::ExpectedContainer(&w.container) &&
   !observer::ExpectedContainer(&w.source),"container_readback") &&
  Check(!observer::ReadPointer(w.image,out),"uncommitted_pointer_read") &&
  Check(!observer::ReadPayload(nullptr,player,paused,sequence),"null_payload_read");
}
bool JournalSuccess(World& w,observer::Token first,observer::Token second) noexcept {
 observer::Dump dump{};
 bool valid=Check(observer::ReadDump(dump),"read_journal");
 valid=Check(dump.gaps==0 && dump.lost==0 && dump.live_registry==0,"journal_coverage")&&valid;
 valid=Check(first.address==second.address && first.incarnation!=0 &&
  second.incarnation>first.incarnation,"retired_pointer_reuse")&&valid;
 valid=Check(Count(dump,observer::Kind::request)==1 &&
  Count(dump,observer::Kind::clone)==2 &&
  Count(dump,observer::Kind::insert_enter)==2 &&
  Count(dump,observer::Kind::insert_return)==2 &&
  Count(dump,observer::Kind::execute_enter)==1 &&
  Count(dump,observer::Kind::execute_return)==1 &&
  Count(dump,observer::Kind::delete_enter)==2 &&
  Count(dump,observer::Kind::delete_return)==2,"journal_event_counts")&&valid;
 std::uint32_t caller_mask{},scalar_mask{};
 for(std::uint32_t i=0;i<dump.count;++i) {
  const auto& e=dump.events[i];
  valid=Check(e.key.valid==1 && e.key.connection==1 &&
   std::string_view(e.key.id.data())=="fixture:request-1" &&
   e.key.desired_paused==1,"request_binding")&&valid;
  if(e.kind==observer::Kind::request)continue;
  valid=Check(e.qualified==1 && e.payload_valid==1 &&
   e.player==0 && e.command_paused==1 && e.native_sequence==0x1234,
   "event_payload")&&valid;
  if(e.kind==observer::Kind::clone)
   valid=Check(e.role==observer::Role::bridge_root,"clone_root_role")&&valid;
  if(e.kind==observer::Kind::insert_enter) {
   valid=Check(e.token==first && e.aux==reinterpret_cast<std::uintptr_t>(&w.container),
    "insert_identity")&&valid;
   if(e.caller==kCallerA)caller_mask|=1;
   else if(e.caller==kCallerB)caller_mask|=2;
   else valid=Check(false,"insert_caller");
  }
  if(e.kind==observer::Kind::insert_return) {
   valid=Check(e.token==first && (e.aux==reinterpret_cast<std::uintptr_t>(&w.array[0]) ||
    e.aux==reinterpret_cast<std::uintptr_t>(&w.array[1])),"insert_slot_readback")&&valid;
  }
  if(e.kind==observer::Kind::execute_enter || e.kind==observer::Kind::execute_return) {
   valid=Check(e.token==first && e.scalar.valid==1 &&
    e.scalar.game==reinterpret_cast<std::uintptr_t>(w.game.data()) &&
    e.scalar.jomini==reinterpret_cast<std::uintptr_t>(w.jomini.data()) &&
    e.scalar.date==53274624,"execute_scalar_identity")&&valid;
   if(e.kind==observer::Kind::execute_enter && e.scalar.paused==0)scalar_mask|=1;
   if(e.kind==observer::Kind::execute_return && e.scalar.paused==1)scalar_mask|=2;
  }
 }
 return Check(caller_mask==3 && scalar_mask==3,"caller_and_scalar_readback")&&valid;
}
bool SuccessfulCalls(World& w) {
 const auto clone=SlotAt<observer::CloneNative>(w,kPrimary+0x40);
 const auto erase=SlotAt<observer::DeleteNative>(w,kPrimary);
 const auto execute=SlotAt<observer::ExecuteNative>(w,kSecondary+8);
 const auto caller_a=reinterpret_cast<observer::AppendNative>(w.image+kCallerA-16);
 const auto caller_b=reinterpret_cast<observer::AppendNative>(w.image+kCallerB-16);
 const auto unqualified=reinterpret_cast<observer::AppendNative>(w.image+kAppend);
 observer::Token first{},second{};
 bool valid=true;
 {
  observer::RequestScope request(observer::BeginConnection(),"fixture:request-1",true);
  observer::BridgeCloneScope bridge(&w.source);
  void* storage{};
  valid=Check(clone(&w.source,&storage)==&storage && storage==&w.clone,"clone_return_storage")&&valid;
  first=observer::Lookup(storage).token;
  valid=Check(caller_a(&w.container,&storage)==&w.array[0] &&
   storage==&w.clone && w.array[0]==storage,"append_caller_a")&&valid;
  valid=Check(caller_b(&w.container,&storage)==&w.array[1] &&
   storage==&w.clone && w.array[1]==storage,"append_caller_b")&&valid;
  valid=Check(unqualified(&w.container,&storage)==&w.array[2] &&
   storage==&w.clone && w.array[2]==storage,"append_unqualified_forward")&&valid;
  execute(&w.clone.secondary);
  valid=Check(erase(storage,1)==storage && !observer::Lookup(storage).valid,"delete_retire")&&valid;
  valid=Check(clone(&w.source,&storage)==&storage && storage==&w.clone,"reuse_clone_return")&&valid;
  second=observer::Lookup(storage).token;
  valid=Check(erase(storage,1)==storage && !observer::Lookup(storage).valid,"reuse_delete_retire")&&valid;
 }
 valid=Check(w.calls.clone==2 && w.calls.erase==2 && w.calls.execute==1 &&
  w.calls.append==3 && w.native_arguments_valid,"original_exactly_once")&&valid;
 return JournalSuccess(w,first,second)&&valid;
}
bool ExceptionCalls(World& w,ThrowKind wanted) {
 const auto clone=SlotAt<observer::CloneNative>(w,kPrimary+0x40);
 const auto erase=SlotAt<observer::DeleteNative>(w,kPrimary);
 const auto execute=SlotAt<observer::ExecuteNative>(w,kSecondary+8);
 const auto caller=reinterpret_cast<observer::AppendNative>(w.image+kCallerA-16);
 bool caught=false;
 try {
  observer::RequestScope request(observer::BeginConnection(),"fixture:exception-1",true);
  observer::BridgeCloneScope bridge(&w.source);
  void* storage{};
  if(wanted==ThrowKind::clone)w.throwing=wanted;
  clone(&w.source,&storage);
  if(wanted==ThrowKind::append)w.throwing=wanted;
  caller(&w.container,&storage);
  w.throwing=wanted;
  if(wanted==ThrowKind::execute)execute(&w.clone.secondary);
  else if(wanted==ThrowKind::erase)erase(storage,1);
 }catch(const NativeSignal& signal) {caught=signal.kind==wanted;}
 catch(...) {return Check(false,"wrong_native_exception");}
 bool valid=Check(caught && w.native_arguments_valid,"native_exception_propagation");
 observer::Dump dump{};
 valid=Check(observer::ReadDump(dump),"exception_journal")&&valid;
 if(wanted==ThrowKind::clone)
  valid=Check(w.calls.clone==1 && w.calls.append==0 && w.calls.execute==0 &&
   w.calls.erase==0 && Count(dump,observer::Kind::clone)==0,"clone_exception_once")&&valid;
 if(wanted==ThrowKind::append)
  valid=Check(w.calls.clone==1 && w.calls.append==1 && w.calls.execute==0 &&
   w.calls.erase==0 && Count(dump,observer::Kind::insert_enter)==1 &&
   Count(dump,observer::Kind::insert_return)==0,"append_exception_once")&&valid;
 if(wanted==ThrowKind::execute)
  valid=Check(w.calls.clone==1 && w.calls.append==1 && w.calls.execute==1 &&
   w.calls.erase==0 && Count(dump,observer::Kind::execute_enter)==1 &&
   Count(dump,observer::Kind::execute_return)==0,"execute_exception_once")&&valid;
 if(wanted==ThrowKind::erase)
  valid=Check(w.calls.clone==1 && w.calls.append==1 && w.calls.execute==0 &&
   w.calls.erase==1 && Count(dump,observer::Kind::delete_enter)==1 &&
   Count(dump,observer::Kind::delete_return)==0 &&
   !observer::Lookup(&w.clone).valid,"delete_exception_once")&&valid;
 return valid;
}
struct Case {
 std::string_view name;Failure failure{};
 std::array<std::uint32_t,2> vp{},flush{};
 observer::InstallResult expected{observer::InstallResult::unavailable_clean};
};
constexpr std::array<Case,31> cases{{
 {"success",Failure::none,{},{},observer::InstallResult::active},
 {"throw-clone",Failure::none,{},{},observer::InstallResult::active},
 {"throw-delete",Failure::none,{},{},observer::InstallResult::active},
 {"throw-execute",Failure::none,{},{},observer::InstallResult::active},
 {"throw-append",Failure::none,{},{},observer::InstallResult::active},
 {"not-suspended"},{"wrong-sha"},{"not-admitted"},{"zero-base"},
 {"slot-clone"},{"slot-delete"},{"slot-execute"},{"append-prefix"},{"execute-bytes"},
 {"allocation",Failure::allocation},{"pin",Failure::pin},
 {"frequency",Failure::frequency},{"process-times",Failure::process_times},
 {"vp-1",Failure::none,{1,0}},{"vp-2",Failure::none,{2,0}},
 {"vp-3",Failure::none,{3,0}},{"vp-4",Failure::none,{4,0}},
 {"vp-5",Failure::none,{5,0}},{"vp-6",Failure::none,{6,0}},
 {"vp-7",Failure::none,{7,0}},{"vp-8",Failure::none,{8,0}},
 {"vp-9",Failure::none,{9,0}},
 {"flush-1",Failure::none,{}, {1,0}},{"flush-2",Failure::none,{}, {2,0}},
 {"rollback-vp-unsafe",Failure::none,{3,4},{},observer::InstallResult::rollback_unsafe},
 {"rollback-flush-unsafe",Failure::none,{}, {2,3},observer::InstallResult::rollback_unsafe}
}};
bool RefusedCleanly(World& w,const Case& test) noexcept {
 bool valid=Check(!observer::Attached(),"refusal_attached")&&ImageUnchanged(w);
 valid=Check(w.calls.clone==0 && w.calls.erase==0 && w.calls.execute==0 &&
  w.calls.append==0,"refusal_called_original")&&valid;
 const auto name=test.name;
 const bool before_allocation=name=="not-suspended" || name=="wrong-sha" ||
  name=="not-admitted" || name=="zero-base" || name=="slot-clone" ||
  name=="slot-delete" || name=="slot-execute" || name=="append-prefix" ||
  name=="execute-bytes";
 if(before_allocation)
  valid=Check(api.alloc==0 && api.free==0 && api.protect==0 && api.flush==0 &&
   api.pin==0 && api.frequency==0 && api.times==0,"precondition_api_write")&&valid;
 if(name=="allocation")valid=Check(api.alloc==1 && api.free==0 && api.protect==0,
  "allocation_refusal")&&valid;
 if(name=="vp-1" || name=="flush-1" || name=="pin" ||
    name=="frequency" || name=="process-times")
  valid=Check(api.alloc==1 && api.free==1,"trampoline_release")&&valid;
 return valid;
}
bool UnsafeRollback(World& w,const Case& test) {
 bool valid=Check(!observer::Attached(),"unsafe_attached")&&ImageUnchanged(w,false);
 if(test.name=="rollback-flush-unsafe")return ImageUnchanged(w)&&valid;
 valid=Check(SlotAt<observer::CloneNative>(w,kPrimary+0x40)!=
  reinterpret_cast<observer::CloneNative>(w.image+kClone),"unsafe_fixture_not_reached")&&valid;
 valid=Check(std::memcmp(w.image+kAppend,kAppendPrefix.data(),15)==0,
  "unsafe_code_changed")&&valid;
 // A leftover wrapper still forwards exactly once while Attached()==false.
 void* storage{};
 auto clone=SlotAt<observer::CloneNative>(w,kPrimary+0x40);
 valid=Check(clone(&w.source,&storage)==&storage && storage==&w.clone &&
  w.calls.clone==1,"unsafe_wrapper_forward")&&valid;
 observer::Dump dump{};
 valid=Check(observer::ReadDump(dump) && dump.count==0,
  "unsafe_observer_emitted_events")&&valid;
 return valid;
}
bool SimpleMachineId(std::string_view id) noexcept {
 if(id.empty()||id.size()>95)return false;
 for(const unsigned char c:id)
  if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||
      c=='-'||c=='_'||c=='.'))return false;
 return true;
}
void Print(const Case& test,std::string_view machine,observer::InstallResult result,
 const World& w,bool valid) noexcept {
 SYSTEMTIME now{};GetSystemTime(&now);
 const auto identity=observer::Identity();
 std::printf("{\"schema\":\"xar.native31.installer-fixture/v1\",\"machine_id\":\"%.*s\","
  "\"observed_at_utc\":\"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ\","
  "\"source_sha256\":\"95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545\","
  "\"case\":\"%.*s\",\"passed\":%s,\"install_result\":%u,\"attached\":%s,"
  "\"reserved_bytes\":100663296,\"committed_image_bytes\":%llu,"
  "\"process_id\":%lu,\"process_birth\":\"%llu\",\"qpc_frequency\":\"%llu\","
  "\"api\":{\"alloc\":%u,\"free\":%u,\"protect\":%u,\"flush\":%u,\"pin\":%u,"
  "\"frequency\":%u,\"process_times\":%u},"
  "\"original_calls\":{\"clone\":%u,\"delete\":%u,\"execute\":%u,\"append\":%u},"
  "\"failure\":",
  static_cast<int>(machine.size()),machine.data(),
  static_cast<unsigned>(now.wYear),static_cast<unsigned>(now.wMonth),static_cast<unsigned>(now.wDay),
  static_cast<unsigned>(now.wHour),static_cast<unsigned>(now.wMinute),
  static_cast<unsigned>(now.wSecond),static_cast<unsigned>(now.wMilliseconds),
  static_cast<int>(test.name.size()),test.name.data(),valid?"true":"false",
  static_cast<unsigned>(result),observer::Attached()?"true":"false",
  static_cast<unsigned long long>(w.page_count*4096),
  static_cast<unsigned long>(GetCurrentProcessId()),
  static_cast<unsigned long long>(identity.process_birth),
  static_cast<unsigned long long>(identity.qpc_frequency),
  api.alloc,api.free,api.protect,api.flush,api.pin,api.frequency,api.times,
  w.calls.clone,w.calls.erase,w.calls.execute,w.calls.append);
 if(error)std::printf("\"%s\"",error);else std::printf("null");
 std::printf("}\n");
}
int Run(const Case& test,std::string_view machine) {
 World w{};world=&w;
 if(!Prepare(w,test.name)) {
  Print(test,machine,observer::InstallResult::unavailable_clean,w,false);return 2;
 }
 api.failure=test.failure;api.fail_protect=test.vp;api.fail_flush=test.flush;
 observer::Environment env{};env.image_base=Address(w,0);env.exact_build_admitted=true;
 if(test.name=="not-admitted")env.exact_build_admitted=false;
 if(test.name=="zero-base")env.image_base=0;
 const auto sha=test.name=="wrong-sha"?std::string_view{"bad-sha"}:
  std::string_view{xar::ck3_12004::kExecutableSha256};
 const auto result=observer::Install(env,sha,test.name!="not-suspended");
 bool valid=Check(result==test.expected,"install_result");
 if(result==observer::InstallResult::active) {
  valid=Check(observer::Attached(),"active_not_attached")&&valid;
  valid=ActivePatch(w)&&SameIdentity(observer::Identity(),w)&&ProbeReads(w)&&valid;
  if(test.name=="success")valid=SuccessfulCalls(w)&&valid;
  if(test.name=="throw-clone")valid=ExceptionCalls(w,ThrowKind::clone)&&valid;
  if(test.name=="throw-delete")valid=ExceptionCalls(w,ThrowKind::erase)&&valid;
  if(test.name=="throw-execute")valid=ExceptionCalls(w,ThrowKind::execute)&&valid;
  if(test.name=="throw-append")valid=ExceptionCalls(w,ThrowKind::append)&&valid;
  valid=Check(observer::Install(env,sha,true)==observer::InstallResult::unavailable_clean,
   "second_install_admitted")&&valid;
 }else if(result==observer::InstallResult::unavailable_clean)valid=RefusedCleanly(w,test)&&valid;
 else valid=UnsafeRollback(w,test)&&valid;
 Print(test,machine,result,w,valid);return valid?0:1;
}
} // namespace fixture31
int main(int argc,char** argv) {
 if(argc!=3 || !fixture31::SimpleMachineId(argv[2])) {
  std::fputs("usage: native31_installer_fixture CASE MACHINE_ID\n",stderr);return 64;
 }
 for(const auto& test:fixture31::cases)if(test.name==argv[1]) {
  try {return fixture31::Run(test,argv[2]);}
  catch(...) {std::fputs("fixture unexpected exception\n",stderr);return 3;}
 }
 std::fputs("unknown fixture case\n",stderr);return 64;
}
