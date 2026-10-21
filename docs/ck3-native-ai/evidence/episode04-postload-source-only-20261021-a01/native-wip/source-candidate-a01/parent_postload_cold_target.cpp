#include "pointer_read_decimal64.hpp"
// Synthetic declared ABI and owned memory only. Never loads or calls CK3.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <tlhelp32.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
extern "C" {
volatile LONG64 PointerColdBodyCalls=0;
volatile LONG64 PointerColdOtherAccessCalls=0;
std::uint64_t PointerColdLoadedContext=0,PointerColdPostFlags=0;
std::uint64_t PointerOtherRead(void*,void*);
std::uint64_t PointerOtherWrite(void*,void*,std::uint64_t);
extern unsigned char PointerEntryBody;
alignas(16) std::uint64_t PointerColdLastArgs[4]{};
std::uint64_t PointerEntryStart(void*,void*,std::uint64_t,std::uint64_t);
}
namespace {
// Fixture lifecycle includes attach/READY plus <=30s capture and audit. This
// never extends the observer capture bound or turns timeout into qualification.
constexpr DWORD kWait=120000;
alignas(16) std::array<unsigned char,0x200> character{},foreign_character{},context{},other_context{},game_state{},other_game_state{};
struct FixtureClock {std::uint64_t game_state;std::uint32_t date_raw,absolute_day;};
FixtureClock clock_value{};
std::wstring mode,prefix,event_base;
HANDLE go_event=nullptr,cancel_event=nullptr,audit_event=nullptr,finish_event=nullptr,fault_release_event=nullptr,initial_done=nullptr,audit_done=nullptr,worker_done=nullptr,warmup_event=nullptr,warmed_event=nullptr;
volatile LONG occupied_warmup_calls=0;
HANDLE main_thread=nullptr,auditor_thread=nullptr,worker_thread=nullptr;
DWORD main_tid=0,auditor_tid=0,worker_tid=0;
volatile LONG foreign_calls=0,target_calls=0,return_failures=0,audit_failures=0;
bool tf_held=false;
struct Debug {DWORD tid=0;std::uint64_t created=0,dr[6]{};DWORD eflags=0;bool complete=false;};
Debug initial_main{},initial_auditor{},after_main{},after_worker{};
std::vector<Debug> initial_peers,after_peers;
template<class T>void Put(std::array<unsigned char,0x200>&a,std::size_t offset,T v){std::memcpy(a.data()+offset,&v,sizeof(v));}
std::filesystem::path File(const wchar_t*s){return std::filesystem::path(prefix+s);}
std::uint64_t Created(HANDLE h){FILETIME c{},e{},k{},u{};if(!GetThreadTimes(h,&c,&e,&k,&u))return 0;return(std::uint64_t(c.dwHighDateTime)<<32)|c.dwLowDateTime;}
std::uint64_t ProcessCreated(){FILETIME c{},e{},k{},u{};if(!GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u))return 0;return(std::uint64_t(c.dwHighDateTime)<<32)|c.dwLowDateTime;}
bool ResumeOwnedPeer(HANDLE h,DWORD tid){
 if(ResumeThread(h)!=DWORD(-1))return true;
 InterlockedIncrement(&audit_failures);
 std::ofstream note(File(L".audit-resume-hold.json"));note<<"{\"thread_id\":"<<tid<<",\"created\":"<<PointerU64Json(Created(h))<<",\"owned_suspend_increment\":1,\"cleanup_complete\":false,\"no_additional_suspend\":true}\n";note.close();
 // Retain this exact peer handle and one increment. Never re-suspend or
 // restart the target; only return our own increment or observe its exit.
 for(;;){DWORD code=STILL_ACTIVE;if(GetExitCodeThread(h,&code)&&code!=STILL_ACTIVE)return false;if(ResumeThread(h)!=DWORD(-1))return true;Sleep(25);}
}
Debug Snapshot(HANDLE h,DWORD tid){
 Debug r{};r.tid=tid;r.created=Created(h);const DWORD prior=SuspendThread(h);if(prior==DWORD(-1))return r;
 CONTEXT c{};c.ContextFlags=CONTEXT_DEBUG_REGISTERS|CONTEXT_CONTROL;
 if(GetThreadContext(h,&c)){r.dr[0]=c.Dr0;r.dr[1]=c.Dr1;r.dr[2]=c.Dr2;r.dr[3]=c.Dr3;r.dr[4]=c.Dr6;r.dr[5]=c.Dr7;r.eflags=c.EFlags;r.complete=r.created!=0;}
 if(!ResumeOwnedPeer(h,tid))r.complete=false;
 if(!r.complete)InterlockedIncrement(&audit_failures);return r;
}
void DebugJson(std::ostream&o,const Debug&r){o<<"{\"tid\":"<<r.tid<<",\"created\":"<<PointerU64Json(r.created)<<",\"complete\":"<<(r.complete?"true":"false")<<",\"eflags\":"<<r.eflags<<",\"dr\":[";for(unsigned i=0;i<6;++i){if(i)o<<',';o<<PointerU64Json(r.dr[i]);}o<<"]}";}
void WriteDebug(const wchar_t*s,const std::vector<Debug>&rows){std::ofstream o(File(s));o<<'[';for(std::size_t i=0;i<rows.size();++i){if(i)o<<',';DebugJson(o,rows[i]);}o<<"]\n";}
std::vector<Debug> AuditPeers(){
 std::vector<Debug> result;HANDLE scan=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
 if(scan==INVALID_HANDLE_VALUE){InterlockedIncrement(&audit_failures);return result;}
 THREADENTRY32 entry{};entry.dwSize=sizeof(entry);BOOL more=Thread32First(scan,&entry);
 if(!more)InterlockedIncrement(&audit_failures);
 while(more){
  if(entry.th32OwnerProcessID==GetCurrentProcessId()&&entry.th32ThreadID!=GetCurrentThreadId()){
   HANDLE thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_LIMITED_INFORMATION,FALSE,entry.th32ThreadID);
   if(!thread){InterlockedIncrement(&audit_failures);Debug missing{};missing.tid=entry.th32ThreadID;result.push_back(missing);}
   else{if(GetProcessIdOfThread(thread)!=GetCurrentProcessId())InterlockedIncrement(&audit_failures);else result.push_back(Snapshot(thread,entry.th32ThreadID));CloseHandle(thread);}
  }
  more=Thread32Next(scan,&entry);
 }
 if(GetLastError()!=ERROR_NO_MORE_FILES)InterlockedIncrement(&audit_failures);
 CloseHandle(scan);return result;
}
void Meta(){
 auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));auto*dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);auto*nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+dos->e_lfanew);
 const auto ascii=[](const std::wstring&w){return std::string(w.begin(),w.end());};
 std::ofstream o(File(L".meta.txt"));
 o<<"parent_schema=xar.maintenance.parent_postload.cold-meta.v1\npid="<<GetCurrentProcessId()<<"\ntid="<<main_tid<<"\ncreated="<<ProcessCreated()<<"\nfull_id=33388\nlocal_player_id=1\ncharacter="<<reinterpret_cast<std::uintptr_t>(character.data())<<"\ncontext="<<(mode==L"null-admission"?0:reinterpret_cast<std::uintptr_t>(context.data()))<<"\nmodule_base="<<base<<"\nmodule_size="<<nt->OptionalHeader.SizeOfImage<<"\nparent_postload="<<reinterpret_cast<std::uintptr_t>(&PointerEntryStart)<<"\npost_pc="<<reinterpret_cast<std::uintptr_t>(&PointerEntryBody)<<"\nsubject_field_address="<<reinterpret_cast<std::uintptr_t>(character.data()+0x1c0)<<"\nclock_pointer="<<reinterpret_cast<std::uintptr_t>(&clock_value)<<"\ngame_state="<<clock_value.game_state<<"\ndate_raw="<<clock_value.date_raw<<"\nabsolute_day_raw="<<clock_value.absolute_day<<"\nabsolute_day="<<clock_value.absolute_day<<"\nforeign_limit="<<(mode==L"foreign4096_limit"||mode==L"cancel_late"?4096:512)<<"\ngo_event="<<ascii(event_base)<<"Go\ncancel_event="<<ascii(event_base)<<"Cancel\naudit_event="<<ascii(event_base)<<"Audit\nfinish_event="<<ascii(event_base)<<"Finish\nfault_release_event="<<ascii(event_base)<<"FaultRelease\n";
}
void Call(bool target,std::uint64_t index){
 void*ch=target?static_cast<void*>(character.data()):static_cast<void*>(foreign_character.data());const std::uint64_t cookie=0xc001d00d12345678ULL;
 const auto result=PointerEntryStart(context.data(),ch,index,cookie);
 if(result!=(index^0x5a5aULL)||PointerColdLastArgs[0]!=reinterpret_cast<std::uintptr_t>(context.data())||PointerColdLastArgs[1]!=reinterpret_cast<std::uintptr_t>(ch)||PointerColdLastArgs[2]!=index||PointerColdLastArgs[3]!=cookie)InterlockedIncrement(&return_failures);
 InterlockedIncrement(target?&target_calls:&foreign_calls);
}
DWORD WINAPI Worker(void*){Call(true,0x1234);SetEvent(worker_done);return WaitForSingleObject(finish_event,kWait)==WAIT_OBJECT_0?0:1;}
DWORD WINAPI Auditor(void*){
 if(mode==L"occupied-dr"||mode==L"occupied-tf"){
  if(SuspendThread(main_thread)==DWORD(-1))return 1;CONTEXT c{};c.ContextFlags=CONTEXT_DEBUG_REGISTERS|CONTEXT_CONTROL;bool ok=GetThreadContext(main_thread,&c)!=FALSE;
  if(ok){if(mode==L"occupied-dr"){// Intel SDM 253669-060US Fig17-1/17-2: DR7 bit10 is fixed1.
    // New fixture input only; not proof of the previous run's OS causality.
    c.Dr0=0x12345000;c.Dr6=0xffff0ff0ULL;c.Dr7=(c.Dr7&~3ULL)|0x401ULL;}else c.EFlags|=0x100;ok=SetThreadContext(main_thread,&c)!=FALSE;}
  if(!ok){ResumeOwnedPeer(main_thread,main_tid);return 2;}
  tf_held=mode==L"occupied-tf";
  if(!tf_held&&!ResumeOwnedPeer(main_thread,main_tid))return 3;
  if(mode==L"occupied-dr"){
   SetEvent(warmup_event);
   if(WaitForSingleObject(warmed_event,kWait)!=WAIT_OBJECT_0)return 6;
  }
 }
 initial_peers=AuditPeers();for(const auto&r:initial_peers)if(r.tid==main_tid)initial_main=r;
 if(tf_held){WriteDebug(L".initial-debug.json",initial_peers);Meta();}
 SetEvent(initial_done);
 if(WaitForSingleObject(audit_event,kWait)!=WAIT_OBJECT_0)return 4;
 after_peers=AuditPeers();for(const auto&r:after_peers){if(r.tid==main_tid)after_main=r;if(r.tid==worker_tid)after_worker=r;}
 if(tf_held){
  // This is the target's own pre-existing suspend/TF, never an observer action.
  // Record the still-held TF before removing it so the owned process can exit.
  CONTEXT c{};c.ContextFlags=CONTEXT_CONTROL;bool ok=GetThreadContext(main_thread,&c)!=FALSE;
  if(ok){c.EFlags&=~0x100UL;ok=SetThreadContext(main_thread,&c)!=FALSE;}
  if(!ok){InterlockedIncrement(&audit_failures);for(;;){Sleep(25);c={};c.ContextFlags=CONTEXT_CONTROL;if(GetThreadContext(main_thread,&c)){c.EFlags&=~0x100UL;if(SetThreadContext(main_thread,&c))break;}}}
  if(!ResumeOwnedPeer(main_thread,main_tid))InterlockedIncrement(&audit_failures);
 }
 SetEvent(audit_done);return WaitForSingleObject(finish_event,kWait)==WAIT_OBJECT_0?0:5;
}
void Results(const wchar_t*s=L".result.json"){std::ofstream o(File(s));o<<"{\"synthetic\":true,\"actual_body_calls\":"<<PointerU64Json(PointerColdBodyCalls)<<",\"other_access_calls\":"<<PointerU64Json(PointerColdOtherAccessCalls)<<",\"loaded_context\":"<<PointerU64Json(PointerColdLoadedContext)<<",\"post_arithmetic_flags\":"<<(PointerColdPostFlags&0x8d5ULL)<<",\"foreign_body_calls\":"<<foreign_calls<<",\"target_body_calls\":"<<target_calls<<",\"return_failures\":"<<return_failures<<",\"audit_failures\":"<<audit_failures<<",\"main_tid\":"<<main_tid<<",\"auditor_tid\":"<<auditor_tid<<",\"worker_tid\":"<<worker_tid<<",\"full_id_initial\":33388,\"local_player_id\":1,\"target_owned_TF_hold\":"<<(tf_held?"true":"false")<<",\"occupied_warmup_calls\":"<<occupied_warmup_calls<<",\"real_CK3_call\":false}\n";}
}
int wmain(int argc,wchar_t**argv){
 if(argc!=5||std::wstring(argv[1])!=L"--mode"||std::wstring(argv[3])!=L"--prefix")return 2;mode=argv[2];prefix=argv[4];
 const std::vector<std::wstring> modes={L"foreign257_then_target",L"created_thread",L"foreign4096_limit",L"timeout",L"cancel_late",L"occupied-dr",L"occupied-tf",L"context-drift",L"fullid-drift",L"magic-drift",L"session-drift",L"null-context",L"other-player-read",L"other-player-write",L"null-admission"};
 bool supported=false;for(const auto&m:modes)if(m==mode)supported=true;if(!supported)return 2;
 Put(character,0x18,std::uint32_t(33388));Put(character,0x1c,std::uint32_t(0x43686172));Put(character,0x1c0,reinterpret_cast<std::uintptr_t>(context.data()));Put(character,0x1d0,std::uint64_t(0));if(mode==L"null-admission")Put(character,0x1c0,std::uint64_t(0));
 Put(foreign_character,0x18,std::uint32_t(44444));Put(foreign_character,0x1c0,reinterpret_cast<std::uintptr_t>(context.data()));clock_value={reinterpret_cast<std::uintptr_t>(game_state.data()),53149056,2214544};
 event_base=L"Local\\XarPostloadCold"+std::to_wstring(GetCurrentProcessId());
 auto event=[&](const wchar_t*s){return CreateEventW(nullptr,TRUE,FALSE,(event_base+s).c_str());};
 go_event=event(L"Go");cancel_event=event(L"Cancel");audit_event=event(L"Audit");finish_event=event(L"Finish");fault_release_event=event(L"FaultRelease");initial_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);audit_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);worker_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);warmup_event=CreateEventW(nullptr,TRUE,FALSE,nullptr);warmed_event=CreateEventW(nullptr,TRUE,FALSE,nullptr);
 main_tid=GetCurrentThreadId();main_thread=OpenThread(THREAD_ALL_ACCESS,FALSE,main_tid);
 if(!go_event||!cancel_event||!audit_event||!finish_event||!fault_release_event||!initial_done||!audit_done||!worker_done||!warmup_event||!warmed_event||!main_thread)return 3;
 auditor_thread=CreateThread(nullptr,0,Auditor,nullptr,0,&auditor_tid);if(!auditor_thread)return 4;
 if(mode==L"occupied-dr"){
  if(WaitForSingleObject(warmup_event,kWait)!=WAIT_OBJECT_0)return 5;
  // An ordinary main-thread round trip, not PointerEntryStart or an observer action.
  InterlockedIncrement(&occupied_warmup_calls);SetEvent(warmed_event);
 }
 if(WaitForSingleObject(initial_done,kWait)!=WAIT_OBJECT_0)return 5;
 if(!tf_held){initial_auditor=Snapshot(auditor_thread,auditor_tid);auto rows=initial_peers;rows.push_back(initial_auditor);WriteDebug(L".initial-debug.json",rows);Meta();}
 HANDLE startup_events[]={go_event,cancel_event};const DWORD startup=WaitForMultipleObjects(2,startup_events,FALSE,kWait);
 if(startup!=WAIT_OBJECT_0&&startup!=WAIT_OBJECT_0+1)return 6;
 const bool aborted_before_go=startup==WAIT_OBJECT_0+1;
 if(aborted_before_go){}
 else if(mode==L"foreign257_then_target"){for(unsigned i=0;i<257;++i)Call(false,i);Call(true,257);}
 else if(mode==L"foreign4096_limit"){for(unsigned i=0;i<4096;++i)Call(false,i);Call(true,4096);}
 else if(mode==L"created_thread"){worker_thread=CreateThread(nullptr,0,Worker,nullptr,0,&worker_tid);if(!worker_thread||WaitForSingleObject(worker_done,kWait)!=WAIT_OBJECT_0)return 7;}
 else if(mode==L"cancel_late"){for(unsigned i=0;i<4096;++i)Call(false,i);Call(true,4096);}
 else if(mode==L"other-player-read"){for(unsigned i=0;i<4096;++i)PointerOtherRead(context.data(),character.data());Call(true,257);}
 else if(mode==L"other-player-write"){for(unsigned i=0;i<4096;++i)PointerOtherWrite(context.data(),character.data(),reinterpret_cast<std::uintptr_t>(context.data()));Call(true,257);}
 else if(mode==L"timeout"||mode==L"occupied-dr"||mode==L"occupied-tf"){}
 else{
  if(mode==L"null-context")Put(character,0x1c0,std::uint64_t(0));
  else if(mode==L"context-drift")Put(character,0x1c0,reinterpret_cast<std::uintptr_t>(other_context.data()));
  else if(mode==L"fullid-drift")Put(character,0x18,std::uint32_t(33389));
  else if(mode==L"magic-drift")Put(character,0x1c,std::uint32_t(0));
  else if(mode==L"session-drift")clock_value.game_state=reinterpret_cast<std::uintptr_t>(other_game_state.data());
  Call(true,42);
 }
 Results(L".calls.json");if(WaitForSingleObject(audit_done,kWait)!=WAIT_OBJECT_0)return 8;
 const Debug after_auditor=Snapshot(auditor_thread,auditor_tid);
 auto rows=after_peers;rows.push_back(after_auditor);WriteDebug(L".after-debug.json",rows);Results();
 if(WaitForSingleObject(finish_event,kWait)!=WAIT_OBJECT_0)return 9;
 if(WaitForSingleObject(auditor_thread,5000)!=WAIT_OBJECT_0)return 10;
 if(worker_thread&&WaitForSingleObject(worker_thread,5000)!=WAIT_OBJECT_0)return 11;
 DWORD ac=1,wc=0;GetExitCodeThread(auditor_thread,&ac);if(worker_thread)GetExitCodeThread(worker_thread,&wc);
 for(HANDLE h:{main_thread,auditor_thread,worker_thread,go_event,cancel_event,audit_event,finish_event,fault_release_event,initial_done,audit_done,worker_done,warmup_event,warmed_event})if(h)CloseHandle(h);
 return ac||wc||return_failures||audit_failures?12:0;
}
