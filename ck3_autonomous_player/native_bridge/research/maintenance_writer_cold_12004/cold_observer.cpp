// Cold-only candidate derived from verified R06 source-a05 debug-register lifecycle.
// Default OFF. Cold mode accepts only sibling; future explicit actual4 mode additionally requires fresh-root admission metadata plus actual parent16B/image-size anchor. No CK3 mode has been executed in cold qualification.
// Four data-write/LEN8 slots are new qualification; old execution tests are not reused as credit.
#include <windows.h>
#include <tlhelp32.h>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>
namespace {
std::map<DWORD,std::array<DWORD64,6>> g_saved_debug;
constexpr DWORD kWaitSliceMs=50;
constexpr DWORD kBreakCleanupWaitMs=5000;
std::atomic<bool> g_stop_requested{false};
BOOL WINAPI OnConsoleControl(DWORD control) {
  if(control==CTRL_C_EVENT||control==CTRL_BREAK_EVENT||control==CTRL_CLOSE_EVENT){g_stop_requested.store(true);return TRUE;}return FALSE;
}
template<class T> bool Read(HANDLE p,DWORD64 address,T&value){SIZE_T n=0;return address&&ReadProcessMemory(p,reinterpret_cast<void*>(address),&value,sizeof value,&n)&&n==sizeof value;}
std::uint64_t Created(HANDLE p){FILETIME c{},e{},k{},u{};if(!GetProcessTimes(p,&c,&e,&k,&u))return 0;ULARGE_INTEGER v{};v.LowPart=c.dwLowDateTime;v.HighPart=c.dwHighDateTime;return v.QuadPart;}
std::string Hex(std::uint64_t value){std::ostringstream s;s<<"0x"<<std::hex<<value;return s.str();}
void DrJson(std::ofstream&o,const CONTEXT&c){o<<"["<<c.Dr0<<","<<c.Dr1<<","<<c.Dr2<<","<<c.Dr3<<","<<c.Dr6<<","<<c.Dr7<<"]";}
bool GetContext(HANDLE thread, CONTEXT &context) {
  context = CONTEXT{};
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER |
                         CONTEXT_DEBUG_REGISTERS;
  return GetThreadContext(thread, &context) != FALSE;
}

bool ArmThread(HANDLE thread, const std::array<DWORD64, 4> &sites) {
  alignas(16) CONTEXT context{};
  if (!GetContext(thread, context)) return false;
  // Do not overwrite another component's processor breakpoints.
  if (context.Dr0 || context.Dr1 || context.Dr2 || context.Dr3 ||
      (context.Dr7 & (0xFFULL | 0xFFFF0000ULL))) return false;
  if (context.EFlags & 0x100) return false; // Do not take over an existing TF step.
  g_saved_debug[GetThreadId(thread)]={context.Dr0,context.Dr1,context.Dr2,context.Dr3,context.Dr6,context.Dr7};
  context.Dr0 = sites[0];
  context.Dr1 = sites[1];
  context.Dr2 = sites[2];
  context.Dr3 = sites[3];
  context.Dr6 = 0;
  context.Dr7 |= 0x99990055ULL; // 4 local data-write breakpoints, RW=01 and LEN=10 (8B) each.
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_DEBUG_REGISTERS;
  if(!SetThreadContext(thread,&context))return false;
  alignas(16) CONTEXT actual{};
  return GetContext(thread,actual) && actual.Dr0==context.Dr0 && actual.Dr1==context.Dr1 &&
      actual.Dr2==context.Dr2 && actual.Dr3==context.Dr3 && actual.Dr7==context.Dr7 &&
      (actual.Dr6&0xF)==(context.Dr6&0xF);
}

bool ClearThread(HANDLE thread) {
  alignas(16) CONTEXT context{};
  if (!GetContext(thread, context)) return false;
  const auto saved=g_saved_debug.find(GetThreadId(thread));
  if(saved==g_saved_debug.end())return false;
  context.Dr0=saved->second[0];context.Dr1=saved->second[1];
  context.Dr2=saved->second[2];context.Dr3=saved->second[3];
  context.Dr6=saved->second[4];context.Dr7=saved->second[5];
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_DEBUG_REGISTERS;
  if(!SetThreadContext(thread,&context))return false;
  alignas(16) CONTEXT actual{};
  return GetContext(thread,actual) && actual.Dr0==context.Dr0 && actual.Dr1==context.Dr1 &&
      actual.Dr2==context.Dr2 && actual.Dr3==context.Dr3 && actual.Dr7==context.Dr7 &&
      (actual.Dr6&0xF)==(context.Dr6&0xF);
}

bool ClearAll(const std::map<DWORD, HANDLE> &threads,
              const std::set<DWORD> &armed_tids) {
  bool clean = true;
  for (const DWORD tid : armed_tids) {
    const auto item = threads.find(tid);
    if (item == threads.end()) { clean=false; continue; }
    clean = ClearThread(item->second) && clean;
  }
  return clean;
}

bool SuspendAndClearAll(const std::map<DWORD, HANDLE> &threads,
                        const std::set<DWORD> &armed_tids) {
  bool clean = true;
  for (const DWORD tid : armed_tids) {
    const auto item = threads.find(tid);
    if (item == threads.end()) { clean=false; continue; }
    const DWORD previous = SuspendThread(item->second);
    if (previous == static_cast<DWORD>(-1)) {
      clean = false;
      continue;
    }
    clean = ClearThread(item->second) && clean;
    if (ResumeThread(item->second) == static_cast<DWORD>(-1)) clean = false;
  }
  return clean;
}

struct Config {bool fixture=true,cold_stale_tid_guard=false,capture_copy_caller=false;std::uint64_t window=0,epoch=0,generation=0,revision=0;std::int64_t admission_date=0;std::string episode,packet_sha;DWORD pid=0,initial_tid=0;std::uint64_t created=0;DWORD64 character=0,secondary=0,base=0,module_size=0;std::uint32_t full_id=0;std::uint64_t expected_hits=0;DWORD timeout=0;std::filesystem::path raw,ready;std::string machine;};
constexpr std::array<DWORD64,4> kOffsets{0x2c0,0x2c8,0x28,0x30};
bool Identity(HANDLE p,const Config&x){DWORD64 a=0,b=0,death=0;std::uint32_t id=0,magic=0;return Read(p,x.character+0x18,id)&&Read(p,x.character+0x1c,magic)&&id==x.full_id&&magic==0x43686172&&Read(p,x.character+0x1d0,death)&&death==0&&Read(p,x.character+0x1c0,a)&&Read(p,x.character+0x1c0,b)&&a==b&&a==x.secondary;}
bool ExactActual4Anchor(HANDLE process,DWORD pid,DWORD64&base,DWORD64&size){
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,pid);
  if(snapshot==INVALID_HANDLE_VALUE)return false;MODULEENTRY32W entry{};entry.dwSize=sizeof(entry);bool found=false;
  if(Module32FirstW(snapshot,&entry)){do{if(_wcsicmp(entry.szModule,L"ck3.exe")==0){base=reinterpret_cast<DWORD64>(entry.modBaseAddr);size=entry.modBaseSize;found=true;break;}}while(Module32NextW(snapshot,&entry));}CloseHandle(snapshot);
  if(!found||size!=102518784ULL)return false;
  constexpr std::array<std::uint8_t,16> expected{0x48,0x8b,0xc4,0x53,0x55,0x48,0x81,0xec,0x98,0,0,0,0x4c,0x89,0x70,0xe0};
  std::array<std::uint8_t,16> actual{};SIZE_T read=0;
  return ReadProcessMemory(process,reinterpret_cast<void*>(base+0x28f7840),actual.data(),actual.size(),&read)&&read==actual.size()&&actual==expected;
}

// Complete exact4 source [28A63E0,28A6697), raw SHA ffebf7d9...a47dede.
// Five pushes then RBP=entryRSP-78h and RSP=entryRSP-178h.
bool KnownCopyPrologue(HANDLE process,const Config&x){
  constexpr std::array<std::uint8_t,36> expected{0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c,0x24,0x20,0x55,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x8d,0x6c,0x24,0xb0,0x48,0x81,0xec,0x50,0x01,0x00,0x00};
  std::array<std::uint8_t,36> actual{};SIZE_T n=0;
  return ReadProcessMemory(process,reinterpret_cast<void*>(x.base+0x28a63e0),actual.data(),actual.size(),&n)&&n==actual.size()&&actual==expected;
}
void KnownCopyCallerJson(std::ofstream&o,HANDLE process,const Config&x,const CONTEXT&c,unsigned slot,bool anchor,unsigned&count){
  o<<",\"known_copy_caller_v1\":";
  const bool selected=!x.fixture&&((slot==0&&c.Rip==x.base+0x28a645b)||(slot==1&&c.Rip==x.base+0x28a6466));
  if(!selected||count>=8){o<<"null";return;}++count;
  const bool object=c.R9==x.secondary&&c.Rsi==x.character;
  const bool frame=c.Rsp<=UINT64_MAX-0x178&&c.Rbp<=UINT64_MAX-0x78&&c.Rsp+0x178==c.Rbp+0x78;
  const DWORD64 address=frame?c.Rsp+0x178:0;
  DWORD64 before=0,after=0;bool rb=false,ra=false,identity=false;
  if(anchor&&object&&frame){rb=Read(process,address,before);ra=Read(process,address,after);identity=Identity(process,x);}
  const bool stable=anchor&&object&&frame&&rb&&ra&&identity&&before==after&&before!=0;
  o<<"{\"source_entry_rva\":\"28A63E0\",\"source_raw_sha256\":\"ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede\",\"capture_ordinal\":"<<count<<",\"admission_generation\":"<<x.generation<<",\"prologue_matches\":"<<(anchor?"true":"false")<<",\"frame_relation_matches\":"<<(frame?"true":"false")<<",\"register_context_matches\":"<<(object?"true":"false")<<",\"identity_after\":"<<(identity?"true":"false")<<",\"return_slot_address\":"<<(frame?std::to_string(address):"null")<<",\"read_before_complete\":"<<(rb?"true":"false")<<",\"read_after_complete\":"<<(ra?"true":"false")<<",\"return_before\":"<<(rb?std::to_string(before):"null")<<",\"return_after\":"<<(ra?std::to_string(after):"null")<<",\"return_stable\":"<<(stable?"true":"false")<<",\"candidate_return_absolute\":"<<(stable?std::to_string(before):"null")<<",\"candidate_return_rva\":"<<(stable&&before>=x.base&&before-x.base<x.module_size?std::to_string(before-x.base):"null")<<"}";
}

bool BeginThreadOwnership(DWORD tid,const std::map<DWORD,HANDLE>&threads,const std::set<DWORD>&armed){
  if(threads.contains(tid)||armed.contains(tid))return false;
  g_saved_debug.erase(tid); // Never reuse a saved state from another thread generation.
  return true;
}
int QualifyOwnershipUnit(){
  std::map<DWORD,HANDLE> threads;std::set<DWORD> armed;constexpr DWORD tid=123;
  g_saved_debug[tid]={0xdead0000,0,0,0,0,0};
  if(!BeginThreadOwnership(tid,threads,armed)||g_saved_debug.contains(tid))return 1;
  g_saved_debug[tid]={0xbeef0000,0,0,0,0,0};threads[tid]=nullptr;
  if(BeginThreadOwnership(tid,threads,armed)||g_saved_debug[tid][0]!=0xbeef0000)return 1;
  threads.clear();armed.insert(tid);
  if(BeginThreadOwnership(tid,threads,armed)||g_saved_debug[tid][0]!=0xbeef0000)return 1;
  armed.clear();if(!BeginThreadOwnership(tid,threads,armed)||g_saved_debug.contains(tid))return 1;
  std::cout<<"{\"kind\":\"cold_thread_ownership_unit\",\"passed_checks\":4,\"actual_OS_TID_reuse\":false,\"debug_attach\":false,\"known_producer\":false}\n";return 0;
}
bool PreflightDebugFree(DWORD pid){
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snapshot==INVALID_HANDLE_VALUE)return false;
  THREADENTRY32 entry{};entry.dwSize=sizeof(entry);bool ok=true;unsigned count=0;
  if(!Thread32First(snapshot,&entry))ok=false;
  else do{if(entry.th32OwnerProcessID!=pid)continue;if(++count>256){ok=false;break;}
    HANDLE thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_LIMITED_INFORMATION,FALSE,entry.th32ThreadID);
    if(!thread){ok=false;break;}DWORD previous=SuspendThread(thread);if(previous==DWORD(-1)){CloseHandle(thread);ok=false;break;}
    CONTEXT c{};bool clean=GetContext(thread,c)&&!c.Dr0&&!c.Dr1&&!c.Dr2&&!c.Dr3&&!(c.Dr7&(0xffULL|0xffff0000ULL))&&!(c.EFlags&0x100);
    if(ResumeThread(thread)==DWORD(-1))clean=false;CloseHandle(thread);if(!clean){ok=false;break;}
  }while(Thread32Next(snapshot,&entry));CloseHandle(snapshot);return ok&&count>0;
}
int Probe(Config x){
  if(x.expected_hits>128||!x.pid||!x.created||!x.character||!x.secondary||x.character>0x7ffffffff000ULL||x.secondary>0x7ffffffff000ULL||!x.full_id||x.secondary%8||x.timeout<500||x.timeout>30000||std::filesystem::exists(x.raw)||std::filesystem::exists(x.ready))return 2;
  HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ|PROCESS_CREATE_THREAD,FALSE,x.pid);
  if(!process)return 2;
  std::array<wchar_t,32768> image{},own{};DWORD n=DWORD(image.size());DWORD m=GetModuleFileNameW(nullptr,own.data(),DWORD(own.size()));
  bool image_ok=QueryFullProcessImageNameW(process,0,image.data(),&n)!=FALSE;
  const auto image_path=std::filesystem::path(std::wstring(image.data(),n));
  image_ok=image_ok&&(x.fixture?(image_path.filename()==L"maintenance_writer_cold_target.exe"&&image_path.parent_path()==std::filesystem::path(std::wstring(own.data(),m)).parent_path()):(_wcsicmp(image_path.filename().c_str(),L"ck3.exe")==0&&ExactActual4Anchor(process,x.pid,x.base,x.module_size)));
  BOOL debugger=FALSE;
  if(!image_ok||Created(process)!=x.created||!Identity(process,x)||!CheckRemoteDebuggerPresent(process,&debugger)||debugger){CloseHandle(process);return 2;}
  const bool copy_anchor=x.capture_copy_caller&&!x.fixture&&KnownCopyPrologue(process,x);unsigned copy_count=0;
  std::array<DWORD64,4> sites{};std::array<std::int64_t,4> last{};
  for(unsigned i=0;i<4;++i){sites[i]=x.secondary+kOffsets[i];if(sites[i]%8||!Read(process,sites[i],last[i])){CloseHandle(process);return 2;}}
  if(!Identity(process,x)||!PreflightDebugFree(x.pid)){CloseHandle(process);std::cerr<<"context changed or occupied debug state before attach\n";return 2;}
  std::ofstream output(x.raw,std::ios::binary);if(!output){CloseHandle(process);return 2;}
  output<<"{\"kind\":\"start\",\"schema\":\"xar.maintenance.writer_pc.cold.v1\",\"synthetic\":"<<(x.fixture?"true":"false")<<",\"CK3_observed\":"<<(x.fixture?"false":"true")<<",\"maintenance_attribution\":\"unclosed\",\"machine_id\":\""<<x.machine<<"\",\"pid\":"<<x.pid<<",\"created\":"<<x.created<<",\"full_id\":"<<x.full_id<<",\"character\":"<<x.character<<",\"context\":"<<x.secondary<<",\"admission_window_id\":"<<x.window<<",\"admission_payment_epoch\":"<<x.epoch<<",\"admission_generation\":"<<x.generation<<",\"admission_native_revision\":"<<x.revision<<",\"admission_date_raw\":"<<x.admission_date<<",\"actual_writer_game_date\":null,\"admission_episode\":\""<<x.episode<<"\",\"admission_cash_packet_sha256\":\""<<x.packet_sha<<"\",\"module_base\":"<<x.base<<",\"module_size\":"<<x.module_size<<",\"DR7_write_len8_mask\":2576941141,\"field_offsets\":[704,712,40,48],\"initial_values\":["<<last[0]<<","<<last[1]<<","<<last[2]<<","<<last[3]<<"]}\n";output.flush();
  bool attached=DebugActiveProcess(x.pid)!=FALSE,kill_off=false,cleared=false,detached=false,exited=false,pending=false,ready=false;
  DEBUG_EVENT event{};DWORD pending_disposition=DBG_CONTINUE;std::string reason=attached?"none":"attach_failed";
  std::map<DWORD,HANDLE> threads;std::set<DWORD> armed;std::uint64_t hits=0,data_events=0;std::set<DWORD> writer_tids;bool observation_admission_complete=true;unsigned created_threads=0,restored_threads=0;
  SetConsoleCtrlHandler(OnConsoleControl,TRUE);
  if(attached){kill_off=DebugSetProcessKillOnExit(FALSE)!=FALSE;if(!kill_off)reason="kill_on_exit_disable_failed";}
  auto restore_all=[&](){bool ok=ClearAll(threads,armed);for(DWORD tid:armed){auto it=threads.find(tid);if(it==threads.end())continue;CONTEXT c{};bool got=GetContext(it->second,c);output<<"{\"kind\":\"restore\",\"thread_id\":"<<tid<<",\"readback\":"<<(got?"true":"false")<<",\"debug\":";DrJson(output,c);output<<"}\n";if(got)++restored_threads;}output.flush();return ok;};
  auto arm=[&](DWORD tid,HANDLE borrowed){
    if(!Identity(process,x))return false; // At actual debugger stop, before any watch install.
    const bool seeded=false;
    const bool stale_cleared=g_saved_debug.contains(tid);
    if(!BeginThreadOwnership(tid,threads,armed))return false;
    HANDLE thread=nullptr;if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&thread,0,FALSE,DUPLICATE_SAME_ACCESS))return false;threads[tid]=thread;bool ok=ArmThread(thread,sites);if(g_saved_debug.contains(tid))armed.insert(tid);CONTEXT c{};GetContext(thread,c);output<<"{\"kind\":\"arm\",\"thread_id\":"<<tid<<",\"success\":"<<(ok?"true":"false")<<",\"cold_stale_map_seeded\":"<<(seeded?"true":"false")<<",\"prior_saved_entry_erased\":"<<(stale_cleared?"true":"false")<<",\"saved_debug\":[";auto it=g_saved_debug.find(tid);if(it!=g_saved_debug.end()){for(unsigned i=0;i<6;++i){if(i)output<<',';output<<it->second[i];}}output<<"],\"armed_debug\":";DrJson(output,c);output<<"}\n";output.flush();return ok;};
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(x.timeout);
  try {while(attached&&kill_off&&reason=="none"){
    if(g_stop_requested.load()){reason="cancel";break;}
    if(std::chrono::steady_clock::now()>=deadline){reason="timeout";break;}
    event={};if(!WaitForDebugEvent(&event,kWaitSliceMs)){if(GetLastError()==ERROR_SEM_TIMEOUT)continue;reason="wait_failed";break;}
    pending=true;DWORD disposition=DBG_CONTINUE;
    switch(event.dwDebugEventCode){
      case CREATE_PROCESS_DEBUG_EVENT:if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);/* hProcess/hThread from debug events are borrowed; never close them. */if(!arm(event.dwThreadId,event.u.CreateProcessInfo.hThread)){observation_admission_complete=false;reason="cannot_arm_existing_thread";}break;
      case CREATE_THREAD_DEBUG_EVENT:++created_threads;if(!arm(event.dwThreadId,event.u.CreateThread.hThread)){observation_admission_complete=false;reason="cannot_arm_new_thread";}break;
      case EXIT_THREAD_DEBUG_EVENT:{auto it=threads.find(event.dwThreadId);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}armed.erase(event.dwThreadId);g_saved_debug.erase(event.dwThreadId);output<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<event.dwThreadId<<"}\n";break;}
      case LOAD_DLL_DEBUG_EVENT:if(event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);break;
      case EXIT_PROCESS_DEBUG_EVENT:exited=true;reason="process_exited";break;
      case EXCEPTION_DEBUG_EVENT:{DWORD code=event.u.Exception.ExceptionRecord.ExceptionCode;
        if(code==EXCEPTION_BREAKPOINT&&!ready){ready=x.fixture?armed.contains(x.initial_tid):!armed.empty();if(ready){std::ofstream f(x.ready);f<<"{\"ready\":true,\"armed_thread_count\":"<<armed.size()<<"}\n";f.flush();ready=f.good();}if(!ready)reason="ready_failed";break;}
        if(code!=EXCEPTION_SINGLE_STEP){disposition=DBG_EXCEPTION_NOT_HANDLED;reason="unexpected_exception";break;}
        auto it=threads.find(event.dwThreadId);CONTEXT c{};
        if(it==threads.end()||!armed.contains(event.dwThreadId)||!GetContext(it->second,c)){reason="unarmed_data_exception";break;}
        ++data_events;const DWORD64 hitmask=c.Dr6&0xf; if(!hitmask||(c.Dr6&0x4000)){disposition=DBG_EXCEPTION_NOT_HANDLED;reason="unrelated_single_step";break;}
        const bool identity=Identity(process,x);if(!identity){reason="context_identity_changed";break;}
        LARGE_INTEGER qpc{};QueryPerformanceCounter(&qpc);
        for(unsigned slot=0;slot<4;++slot){if(!(hitmask&(1ULL<<slot)))continue;std::int64_t value=0;bool read=Read(process,sites[slot],value);const bool stable_after=Identity(process,x);++hits;writer_tids.insert(event.dwThreadId);
          output<<"{\"kind\":\"raw_field_write_trap\",\"event_ordinal\":"<<data_events<<",\"slot_hit_ordinal\":"<<hits<<",\"thread_id\":"<<event.dwThreadId<<",\"qpc\":"<<qpc.QuadPart<<",\"slot\":"<<slot<<",\"offset\":"<<kOffsets[slot]<<",\"address\":"<<sites[slot]<<",\"full_id\":"<<x.full_id<<",\"character\":"<<x.character<<",\"context\":"<<x.secondary<<",\"context_identity_stable\":"<<(stable_after?"true":"false")<<",\"before_raw\":"<<last[slot]<<",\"before_basis\":\"last_observed_sample_not_atomic_preinstruction\",\"after_raw\":"<<value<<",\"after_read_complete\":"<<(read?"true":"false")<<",\"same_value_write\":"<<(value==last[slot]?"true":"false")<<",\"RIP_after\":"<<c.Rip<<",\"RIP_after_rva\":"<<(c.Rip>=x.base&&c.Rip<x.base+x.module_size?std::to_string(c.Rip-x.base):"null")<<",\"writer_instruction_start\":null,\"DR6\":"<<c.Dr6<<",\"registers\":{\"rax\":"<<c.Rax<<",\"rbx\":"<<c.Rbx<<",\"rcx\":"<<c.Rcx<<",\"rdx\":"<<c.Rdx<<",\"r8\":"<<c.R8<<",\"r9\":"<<c.R9<<",\"r10\":"<<c.R10<<",\"r11\":"<<c.R11<<",\"rsi\":"<<c.Rsi<<",\"rdi\":"<<c.Rdi<<",\"rbp\":"<<c.Rbp<<",\"rsp\":"<<c.Rsp<<"},\"synthetic\":"<<(x.fixture?"true":"false")<<",\"known_producer\":false,\"military_attribution\":\"unclosed\"";if(x.capture_copy_caller)KnownCopyCallerJson(output,process,x,c,slot,copy_anchor,copy_count);output<<"}\n";
          if(!read)reason="field_read_failed";else if(!stable_after)reason="context_identity_changed_after_read";else last[slot]=value;
        }output.flush();
        // Data traps are post-instruction. Clear only DR status; do not set RF/TF, rewind RIP, or emulate a store.
        c.Dr6=0;c.ContextFlags=CONTEXT_DEBUG_REGISTERS;if(!SetThreadContext(it->second,&c))reason="clear_status_failed";
        if(reason=="none"&&hits>=x.expected_hits&&x.expected_hits)reason=x.fixture?"complete":"hit_limit_partial";
        break;}
      default:break;
    }
    if(reason!="none"){cleared=restore_all();if(!cleared&&reason=="complete")reason="restore_failed";}
    pending_disposition=disposition;bool continued=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)!=FALSE;
    if(!continued){reason="continue_failed";cleared=restore_all();continued=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)!=FALSE;}pending=!continued;
  }}catch(...){reason="observer_throw";}
  // Reused R06 finite cleanup: obtain a stop before restoration, with suspend/restore fallback.
  if(attached&&!exited&&!pending&&!cleared&&!armed.empty()){
    if(DebugBreakProcess(process)){
      auto cleanup_deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(kBreakCleanupWaitMs);
      while(std::chrono::steady_clock::now()<cleanup_deadline){event={};if(!WaitForDebugEvent(&event,kWaitSliceMs))continue;pending=true;
        if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT){HANDLE owned=nullptr;if(DuplicateHandle(GetCurrentProcess(),event.u.CreateThread.hThread,GetCurrentProcess(),&owned,0,FALSE,DUPLICATE_SAME_ACCESS))threads[event.dwThreadId]=owned;else reason="cleanup_thread_duplicate_failed";}
        if(event.dwDebugEventCode==EXIT_THREAD_DEBUG_EVENT){auto it=threads.find(event.dwThreadId);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}armed.erase(event.dwThreadId);g_saved_debug.erase(event.dwThreadId);}
        if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT&&event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
        if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT)exited=true;
        bool stop=event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode==EXCEPTION_BREAKPOINT;
        if(stop||exited)cleared=exited||restore_all();
        DWORD d=event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_BREAKPOINT?DBG_EXCEPTION_NOT_HANDLED:DBG_CONTINUE;pending_disposition=d;
        pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,d)==FALSE;if(pending){reason="cleanup_continue_failed";break;}if(cleared)break;
      }
    }
    if(!cleared&&!exited)cleared=SuspendAndClearAll(threads,armed);
  }
  if(pending&&!exited){cleared=restore_all();if(ContinueDebugEvent(event.dwProcessId,event.dwThreadId,pending_disposition))pending=false;}
  if(armed.empty())cleared=true;
  if(attached&&!exited)detached=DebugActiveProcessStop(x.pid)!=FALSE;else if(exited)detached=true;
  if(pending)reason="pending_event_unresolved";
  for(auto [tid,h]:threads){(void)tid;if(h)CloseHandle(h);}
  const bool clean=cleared&&detached&&!pending;
  output<<"{\"kind\":\"terminal\",\"reason\":\""<<reason<<"\",\"restored\":"<<(cleared?"true":"false")<<",\"detached\":"<<(detached?"true":"false")<<",\"pending_event\":"<<(pending?"true":"false")<<",\"cleanup_complete\":"<<(clean?"true":"false")<<",\"hit_count\":"<<hits<<",\"data_event_count\":"<<data_events<<",\"writer_thread_count\":"<<writer_tids.size()<<",\"created_thread_events\":"<<created_threads<<",\"restore_readback_rows\":"<<restored_threads<<",\"process_exited\":"<<(exited?"true":"false")<<",\"observation_thread_admission_complete\":"<<(observation_admission_complete?"true":"false")<<",\"full_window_all_writes_covered\":false,\"CK3_observed\":"<<(!x.fixture&&attached?"true":"false")<<",\"known_producer\":false,\"military_attribution\":\"unclosed\"}\n";output.flush();CloseHandle(process);SetConsoleCtrlHandler(OnConsoleControl,FALSE);
  return clean&&reason=="complete"?0:1;
}
}
int wmain(int argc,wchar_t**argv){
  if(argc==2&&std::wstring(argv[1])==L"--qualify-cold-thread-ownership")return QualifyOwnershipUnit();
  // Default OFF. Runtime mode requires the separate strict freshcash admission adapter; no raw old callback pointer is an admission.
  if((argc!=14&&argc!=15)||(argc==15&&std::wstring(argv[14])!=L"--capture-known-copy-caller")||(std::wstring(argv[1])!=L"--enable-cold-fixture"&&std::wstring(argv[1])!=L"--enable-ck3-12004-data-watch")||std::wstring(argv[2])!=L"--fixture-meta"||std::wstring(argv[4])!=L"--timeout-ms"||std::wstring(argv[6])!=L"--raw"||std::wstring(argv[8])!=L"--ready"||std::wstring(argv[10])!=L"--expected-hits"||std::wstring(argv[12])!=L"--machine-id")return 2;
  try {std::ifstream input{std::filesystem::path(argv[3])};std::map<std::string,std::string> meta;std::string line;while(std::getline(input,line)){auto p=line.find('=');if(p!=std::string::npos)meta.emplace(line.substr(0,p),line.substr(p+1));}
    auto v=[&](const char*k){return std::stoull(meta.at(k),nullptr,0);};Config x;x.capture_copy_caller=argc==15;x.fixture=std::wstring(argv[1])==L"--enable-cold-fixture";if(!x.fixture){if(meta.at("qualified_exe_sha256")!="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"||meta.at("game_version")!="1.20.0.4"||v("steam_build_id")!=25734779||!v("controlled_window_id")||!v("payment_epoch")||!v("connection_generation")||meta.at("source_observation_kind")!="paused_current_raw_context")return 2;}if(!x.fixture){x.window=v("controlled_window_id");x.epoch=v("payment_epoch");x.generation=v("connection_generation");x.revision=v("native_revision");x.admission_date=std::stoll(meta.at("date_raw"));x.episode=meta.at("episode_id");x.packet_sha=meta.at("source_cash_sha256");if(x.packet_sha.size()!=64||x.packet_sha.find_first_not_of("0123456789abcdef")!=std::string::npos||x.episode.empty()||x.episode.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")!=std::string::npos)return 2;}x.pid=DWORD(v("pid"));x.initial_tid=DWORD(v("tid"));if(x.fixture)x.cold_stale_tid_guard=v("cold_stale_tid_guard")!=0;x.created=v("created");x.character=v("character");x.secondary=v("context");x.full_id=std::uint32_t(v("full_id"));x.base=v("module_base");x.module_size=v("module_size");x.timeout=DWORD(std::stoul(argv[5]));x.raw=argv[7];x.ready=argv[9];x.expected_hits=std::stoull(argv[11]);const std::wstring machine=argv[13];if(machine.empty()||machine.find_first_not_of(L"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")!=std::wstring::npos)return 2;x.machine.assign(machine.begin(),machine.end());return Probe(x);
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
