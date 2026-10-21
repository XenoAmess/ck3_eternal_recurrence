#include "pointer_read_decimal64.hpp"
// Independent default-OFF parent-entry execution breakpoint. Source-only candidate.
// A08 data Probe/Arm and the 3F90A6F dispatch ABI are not this mode.
constexpr DWORD64 kPointerEntryRva=0x28f7840;
constexpr std::array<std::uint8_t,26> kPointerPrefix{0x48,0x8b,0xc4,0x53,0x55,0x48,0x81,0xec,0x98,0x0,0x0,0x0,0x4c,0x89,0x70,0xe0,0x48,0x8b,0xea,0x48,0x8b,0x92,0xc0,0x1,0x0,0x0};
constexpr char kPointerPrefixSha[]="1df1ff739200e1970c772c4fa83df59ff36219925f0c1d2c3d9897bfaca8c19a";
struct PointerOptions {
 Config x;DWORD64 entry=0,post_pc=0,watch=0,clock_pointer=0;unsigned foreign_limit=4096;
 std::string admission_id,fault="none";std::wstring cancel_name,release_name;
};
struct PointerClock {DWORD64 state=0;std::uint32_t date=0,day=0;};
std::uint64_t PointerThreadCreated(HANDLE h){FILETIME c{},e{},k{},u{};if(!GetThreadTimes(h,&c,&e,&k,&u))return 0;ULARGE_INTEGER v{};v.LowPart=c.dwLowDateTime;v.HighPart=c.dwHighDateTime;return v.QuadPart;}
bool PointerReadClock(HANDLE p,const PointerOptions&o,PointerClock&v){
 if(o.x.fixture)return Read(p,o.clock_pointer,v.state)&&Read(p,o.clock_pointer+8,v.date)&&Read(p,o.clock_pointer+12,v.day);
 DWORD64 date=0;return Read(p,o.x.base+0x5c68c50,v.state)&&Read(p,v.state+8,date)&&Read(p,v.state+0x9c,v.day)&&(v.date=static_cast<std::uint32_t>(date),true);
}
bool PointerSource(HANDLE p,const PointerOptions&o){
 std::array<std::uint8_t,26>b{};SIZE_T n=0;
 return ReadProcessMemory(p,reinterpret_cast<void*>(o.entry),b.data(),b.size(),&n)&&n==b.size()&&b==kPointerPrefix;
}
bool PointerSession(HANDLE p,const PointerOptions&o){
 PointerClock a{},b{};return Created(p)==o.x.created&&PointerReadClock(p,o,a)&&PointerReadClock(p,o,b)&&
 a.state==b.state&&a.state==o.x.game_state&&a.date==b.date&&a.day==b.day&&
 a.date>=o.x.admission_date&&a.date<=static_cast<std::uint64_t>(o.x.admission_date)+24&&a.day>=o.x.absolute_day&&a.day<=o.x.absolute_day+1;
}
bool PointerArm(HANDLE h,DWORD64 site){
 CONTEXT c{};if(!GetContext(h,c)||c.Dr0||c.Dr1||c.Dr2||c.Dr3||(c.Dr7&(0xffULL|0xffff0000ULL))||(c.EFlags&0x100))return false;
 g_saved_debug[GetThreadId(h)]={c.Dr0,c.Dr1,c.Dr2,c.Dr3,c.Dr6,c.Dr7};
 c.Dr0=site;c.Dr1=c.Dr2=c.Dr3=c.Dr6=0;c.Dr7|=0xb0001ULL;
 c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
 if(!SetThreadContext(h,&c))return false;
 CONTEXT a{};return GetContext(h,a)&&a.Dr0==site&&!a.Dr1&&!a.Dr2&&!a.Dr3&&a.Dr7==c.Dr7&&(a.Dr6&15)==0;
}
#include "parent_pointer_read_capture.inc"

DWORD64 PointerRemoteNtdllExport(DWORD pid,const char*name){
 HMODULE local=GetModuleHandleW(L"ntdll.dll");auto fn=GetProcAddress(local,name);if(!local||!fn)return 0;
 const auto rva=reinterpret_cast<DWORD64>(fn)-reinterpret_cast<DWORD64>(local);
 HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,pid);if(s==INVALID_HANDLE_VALUE)return 0;
 MODULEENTRY32W e{};e.dwSize=sizeof(e);DWORD64 result=0;
 if(Module32FirstW(s,&e)){do{if(_wcsicmp(e.szModule,L"ntdll.dll")==0&&rva<e.modBaseSize){result=reinterpret_cast<DWORD64>(e.modBaseAddr)+rva;break;}}while(Module32NextW(s,&e));}CloseHandle(s);return result;
}
bool PointerIdentity(HANDLE process,const Config& x){
 std::uint32_t id=0,magic=0;DWORD64 death=1;
 return x.character&&Read(process,x.character+0x18,id)&&Read(process,x.character+0x1c,magic)&&Read(process,x.character+0x1d0,death)&&id==x.full_id&&magic==0x43686172&&!death;
}
void PointerDrJson(std::ostream& out,const CONTEXT& c){out<<'['<<PointerU64Json(c.Dr0)<<','<<PointerU64Json(c.Dr1)<<','<<PointerU64Json(c.Dr2)<<','<<PointerU64Json(c.Dr3)<<','<<PointerU64Json(c.Dr6)<<','<<PointerU64Json(c.Dr7)<<']';}
std::string PointerOwnerJson(const Config&x){
  std::ostringstream o;o<<"{\"schema\":\"xar.maintenance.parent_pointer_read.owner-binding.v2\",\"mode\":\"native_campaign_character_pointer_read_v1\",\"episode_projection\":\"native_campaign\",\"episode_run_id\":null,\"original_episode_key_present\":"<<(x.episode_key_present?"true":"false")
    <<",\"pid\":"<<x.pid<<",\"process_create_time_100ns\":"<<PointerU64Json(x.created)<<",\"connection_generation\":"<<PointerU64Json(x.generation)<<",\"player_character_full_id\":"<<x.full_id<<",\"local_player_id\":"<<x.local_player
    <<",\"game_state_identity_witness\":"<<PointerU64Json(x.game_state)<<",\"character\":"<<PointerU64Json(x.character)<<",\"context\":"<<PointerU64Json(x.secondary)<<",\"controlled_window_id\":"<<PointerU64Json(x.window)<<",\"payment_epoch\":"<<PointerU64Json(x.epoch)
    <<",\"native_revision\":"<<PointerU64Json(x.revision)<<",\"date_raw\":"<<x.admission_date<<",\"absolute_day_raw\":"<<x.absolute_day<<",\"callsite_anchor_rva\":\"42956864\"}";return o.str();
}
int PointerProbe(PointerOptions o){
 auto&x=o.x;
 if(x.timeout<500||x.timeout>30000||!x.pid||!x.created||!x.character||!x.full_id||
 x.character>0x7fffffffee00ULL||x.secondary>0x7ffffffff000ULL||x.secondary%8||!o.entry||
 std::filesystem::exists(x.raw)||std::filesystem::exists(x.ready))return 2;
 HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ|PROCESS_CREATE_THREAD|SYNCHRONIZE,FALSE,x.pid);
 if(!process)return 2;
 std::array<wchar_t,32768>image{},own{};DWORD n=DWORD(image.size()),m=GetModuleFileNameW(nullptr,own.data(),DWORD(own.size()));
 bool image_ok=QueryFullProcessImageNameW(process,0,image.data(),&n)!=FALSE;
 const auto path=std::filesystem::path(std::wstring(image.data(),n));const auto admitted_base=x.base,admitted_size=x.module_size;
 image_ok=image_ok&&(x.fixture?(path.filename()==L"maintenance_parent_pointer_read_cold_target.exe"&&path.parent_path()==std::filesystem::path(std::wstring(own.data(),m)).parent_path()):(_wcsicmp(path.filename().c_str(),L"ck3.exe")==0&&ExactActual4Anchor(process,x.pid,x.base,x.module_size)));
 if(!x.fixture){image_ok=image_ok&&x.base==admitted_base&&x.module_size==admitted_size;o.entry=x.base+kPointerEntryRva;o.post_pc=o.entry+26;o.watch=x.character+0x1c0;}
 PointerClock initial{};
 if(x.fixture&&!PointerReadClock(process,o,initial)){CloseHandle(process);return 2;}
 BOOL debugger=FALSE;
 if(!image_ok||o.entry<x.base||x.module_size<26||o.entry-x.base>x.module_size-26||Created(process)!=x.created||!PointerIdentity(process,x)||!PointerSession(process,o)||!PointerSource(process,o)||
 !CheckRemoteDebuggerPresent(process,&debugger)||debugger){CloseHandle(process);return 2;}
 const DWORD64 breakin=PointerRemoteNtdllExport(x.pid,"DbgUiRemoteBreakin"),breakpoint=PointerRemoteNtdllExport(x.pid,"DbgBreakPoint");
 if(!breakin||!breakpoint){CloseHandle(process);return 2;}
 HANDLE cancel=OpenEventW(SYNCHRONIZE,FALSE,o.cancel_name.c_str());
 HANDLE release=nullptr;if(o.fault!="none")release=OpenEventW(SYNCHRONIZE,FALSE,o.release_name.c_str());
 if(!cancel||(o.fault!="none"&&!release)){if(cancel)CloseHandle(cancel);CloseHandle(process);return 2;}
 std::ofstream out(x.raw,std::ios::binary);if(!out){CloseHandle(cancel);if(release)CloseHandle(release);CloseHandle(process);return 2;}
 out<<"{\"kind\":\"start\",\"schema\":\"xar.maintenance.parent_pointer_read.raw.v2\",\"mode\":\"player-parent-pointer-read-once-v1\",\"machine_id\":\""<<x.machine
 <<"\",\"synthetic\":"<<(x.fixture?"true":"false")<<",\"pid\":"<<x.pid<<",\"created\":"<<PointerU64Json(x.created)<<",\"entry\":"<<PointerU64Json(o.entry)
 <<",\"post_pc\":"<<PointerU64Json(o.post_pc)<<",\"watch_address\":"<<PointerU64Json(o.watch)<<",\"observation_kind\":\"post_parent_pointer_read\",\"entryExact\":false,\"module_base\":"<<PointerU64Json(x.base)<<",\"module_size\":"<<PointerU64Json(x.module_size)<<",\"character\":"<<PointerU64Json(x.character)<<",\"full_id\":"<<x.full_id<<",\"context\":"<<PointerU64Json(x.secondary)<<",\"local_player_id\":"<<x.local_player
 <<",\"game_state\":"<<PointerU64Json(x.game_state)<<",\"date_raw\":"<<x.admission_date<<",\"absolute_day\":"<<x.absolute_day
 <<",\"admission_id\":\""<<o.admission_id<<"\",\"prefix_sha256\":\""<<kPointerPrefixSha<<"\",\"foreign_limit\":"<<o.foreign_limit
 <<",\"capture_ms\":"<<x.timeout<<",\"target_record_limit\":1,\"owner_binding\":"<<(x.fixture?"null":PointerOwnerJson(x))<<"}\n";out.flush();
 bool attached=DebugActiveProcess(x.pid)!=FALSE,kill_off=false,pending=false,ready=false,exited=false,detached=false,cleared=false,admission_complete=true,hold_logged=false,fault_used=false;
 bool qualified=false;unsigned captures=0,foreign=0;std::uint64_t events=0;
 std::string reason=attached?"none":"attach_failed";DEBUG_EVENT event{};DWORD disposition=DBG_CONTINUE;
 std::map<DWORD,HANDLE>threads;std::set<DWORD>armed,restored,restore_attempted,unarmed_reported;std::map<DWORD,unsigned>generations;std::map<DWORD,DWORD64>thread_starts,thread_birth;
 bool break_attempted=false,break_request_inflight=false,cleanup_new_event=false,cleanup_owned_reported=false,pending_owned_proven=false;
 DWORD pending_owned_tid=0;unsigned pending_owned_generation=0;CONTEXT pending_owned_context{};DWORD64 pending_owned_exception=0;
 struct QueuedWitness{unsigned generation;DWORD64 birth,pc;};std::map<DWORD,QueuedWitness>queued_data;
 auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(30000);
 SetConsoleCtrlHandler(OnConsoleControl,TRUE);
 if(attached){kill_off=DebugSetProcessKillOnExit(FALSE)!=FALSE;if(!kill_off)reason="kill_on_exit_disable_failed";}
 auto log_hold=[&](){if(!hold_logged){out<<"{\"kind\":\"unresolved_cleanup_hold\",\"Popen_must_remain_retained\":true,\"cleanup_complete\":false,\"no_more_capture\":true}\n";out.flush();hold_logged=true;}};
 auto fault=[&](const char*name){if(o.fault!=name||fault_used)return false;fault_used=true;log_hold();return true;};
 auto release_ready=[&](){return !fault_used||!release||WaitForSingleObject(release,0)==WAIT_OBJECT_0;};
 auto arm=[&](DWORD tid,HANDLE borrowed){
  if(threads.size()>=256||!BeginThreadOwnership(tid,threads,armed))return false;
  HANDLE h=nullptr;if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
  threads[tid]=h;++generations[tid];thread_birth[tid]=PointerThreadCreated(h);restored.erase(tid);restore_attempted.erase(tid);bool ok=thread_birth[tid]&&PointerArm(h,o.watch);
  if(g_saved_debug.contains(tid))armed.insert(tid);
  CONTEXT c{};bool got=GetContext(h,c);
  out<<"{\"kind\":\"arm\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<PointerU64Json(thread_birth[tid])<<",\"success\":"<<(ok?"true":"false")<<",\"saved_debug\":[";
  auto it=g_saved_debug.find(tid);if(it!=g_saved_debug.end())for(unsigned i=0;i<6;++i){if(i)out<<',';out<<PointerU64Json(it->second[i]);}
  out<<"],\"armed_debug\":";PointerDrJson(out,c);out<<",\"readback\":"<<(got?"true":"false")<<"}\n";out.flush();return ok;
 };
 auto retire=[&](DWORD tid){
  auto it=threads.find(tid);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}
  if(armed.erase(tid))out<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<"}\n";
  restored.erase(tid);restore_attempted.erase(tid);queued_data.erase(tid);g_saved_debug.erase(tid);thread_starts.erase(tid);thread_birth.erase(tid);unarmed_reported.erase(tid);
 };
 auto restore_all=[&](){
  bool ok=true;
  for(DWORD tid:armed){
   if(restored.contains(tid))continue;
   auto h=threads.find(tid);auto s=g_saved_debug.find(tid);
   if(h==threads.end()||s==g_saved_debug.end()){ok=false;continue;}
   CONTEXT c{};if(!GetContext(h->second,c)){ok=false;continue;}
   CONTEXT witness=c;
   const bool same_pending=pending_owned_proven&&pending_owned_tid==tid&&pending_owned_generation==generations[tid]&&pending_owned_context.Rip==c.Rip;
   if(same_pending&&(c.Dr6&15)!=1)witness=pending_owned_context;
   if(!queued_data.contains(tid)&&!(witness.EFlags&0x100)&&!(witness.Dr6&0xe000)&&(witness.Dr6&15)==1&&witness.Dr0==o.watch&&!witness.Dr1&&!witness.Dr2&&!witness.Dr3&&(witness.Dr7&0xffff00ffULL)==0xb0001ULL){
    queued_data.emplace(tid,QueuedWitness{generations[tid],thread_birth[tid],witness.Rip});
    out<<"{\"kind\":\"queued_data_witness\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<PointerU64Json(thread_birth[tid])<<",\"RIP\":"<<PointerU64Json(witness.Rip)<<",\"eflags\":"<<witness.EFlags<<",\"debug\":";PointerDrJson(out,witness);out<<"}\n";out.flush();
   }
   const bool already_original=restore_attempted.contains(tid)&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr6==s->second[4]&&c.Dr7==s->second[5];
   c.Dr0=s->second[0];c.Dr1=s->second[1];c.Dr2=s->second[2];c.Dr3=s->second[3];c.Dr6=s->second[4];c.Dr7=s->second[5];c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
   if(!already_original){restore_attempted.insert(tid);if(fault("restore")||!SetThreadContext(h->second,&c)){ok=false;continue;}}
   CONTEXT a{};const bool got=GetContext(h->second,a);
   const bool equal=got&&a.Dr0==c.Dr0&&a.Dr1==c.Dr1&&a.Dr2==c.Dr2&&a.Dr3==c.Dr3&&a.Dr6==c.Dr6&&a.Dr7==c.Dr7;
   if(fault("readback")){ok=false;continue;}
   if(equal)restored.insert(tid);else{ok=false;continue;} // failed attempts do not duplicate a success proof row.
   out<<"{\"kind\":\"restore\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<PointerU64Json(thread_birth[tid])<<",\"readback\":"<<(got?"true":"false")<<",\"equal_original\":"<<(equal?"true":"false")<<",\"debug\":";PointerDrJson(out,a);out<<"}\n";
  }out.flush();return ok&&restored.size()==armed.size();
 };
 auto owned=[&](CONTEXT&c){
  auto it=threads.find(event.dwThreadId);
  if(event.dwDebugEventCode!=EXCEPTION_DEBUG_EVENT||event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_SINGLE_STEP||
   it==threads.end()||!armed.contains(event.dwThreadId)||!GetContext(it->second,c)||(c.EFlags&0x100))return false;
  const bool same_proven_event=pending_owned_proven&&pending_owned_tid==event.dwThreadId&&pending_owned_generation==generations[event.dwThreadId]&&pending_owned_context.Rip==c.Rip&&pending_owned_exception==reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress);
  if(!restored.contains(event.dwThreadId)){
   auto s=g_saved_debug.find(event.dwThreadId);
   if(same_proven_event&&restore_attempted.contains(event.dwThreadId)&&s!=g_saved_debug.end()&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr6==s->second[4]&&c.Dr7==s->second[5])return true;
   return !(c.Dr6&0xe000)&&((c.Dr6&15)==1||(same_proven_event&&(c.Dr6&15)==0))&&c.Dr0==o.watch&&!c.Dr1&&!c.Dr2&&!c.Dr3&&(c.Dr7&0xffff00ffULL)==0xb0001ULL;
  }
  // A queued event may arrive after this same generation was restored.
  auto s=g_saved_debug.find(event.dwThreadId);
  auto w=queued_data.find(event.dwThreadId);
   const bool queued=w!=queued_data.end()&&w->second.generation==generations[event.dwThreadId]&&w->second.birth==thread_birth[event.dwThreadId]&&w->second.pc==c.Rip&&w->second.pc==reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress);
   return (same_proven_event||queued)&&s!=g_saved_debug.end()&&(c.Dr6==s->second[4]||c.Dr6==(s->second[4]|1ULL))&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr7==s->second[5];
 };
 auto census=[&](){
  HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(s==INVALID_HANDLE_VALUE)return false;
  THREADENTRY32 t{};t.dwSize=sizeof(t);std::set<DWORD>ids;bool complete=false;
  if(Thread32First(s,&t)){for(;;){if(t.th32OwnerProcessID==x.pid)ids.insert(t.th32ThreadID);
   SetLastError(ERROR_SUCCESS);if(!Thread32Next(s,&t)){complete=GetLastError()==ERROR_NO_MORE_FILES;break;}}}
  CloseHandle(s);return complete&&!ids.empty()&&ids==armed&&ids.size()<=256;
 };
 auto own_break=[&](){
  return event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode==EXCEPTION_BREAKPOINT&&
   event.u.Exception.dwFirstChance&&breakpoint&&breakin&&thread_starts.contains(event.dwThreadId)&&
   thread_starts[event.dwThreadId]==breakin&&reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress)==breakpoint;
 };
 auto remember_unarmed=[&](DWORD tid,HANDLE borrowed,DWORD64 start){
  const auto birth=PointerThreadCreated(borrowed);if(!birth)return false;
  if(threads.contains(tid)&&thread_birth[tid]!=birth)return false;
  if(!threads.contains(tid)){
   if(threads.size()>=256)return false;HANDLE h=nullptr;
   if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
   threads[tid]=h;++generations[tid];thread_birth[tid]=birth;thread_starts[tid]=start;
  }
  CONTEXT c{};if(!GetContext(threads.at(tid),c)||c.Dr0||c.Dr1||c.Dr2||c.Dr3||(c.Dr7&(0xffULL|0xffff0000ULL)))return false;
  if(unarmed_reported.insert(tid).second){out<<"{\"kind\":\"cleanup_thread_unarmed\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<PointerU64Json(birth)<<",\"readback\":true,\"debug\":";PointerDrJson(out,c);out<<"}\n";out.flush();}return true;
 };
 try{
 while(attached&&kill_off&&reason=="none"){
  if(g_stop_requested.load()||WaitForSingleObject(cancel,0)==WAIT_OBJECT_0){reason="cancel";break;}
  if(std::chrono::steady_clock::now()>=deadline){reason=ready?"timeout":"ready_timeout";break;}
  if(events>16384||out.tellp()>512*1024){reason="event_or_raw_limit";break;}
  event={};if(!WaitForDebugEvent(&event,kWaitSliceMs)){if(GetLastError()==ERROR_SEM_TIMEOUT)continue;reason="wait_failed";break;}
  ++events;pending=true;pending_owned_proven=false;disposition=DBG_CONTINUE;
  switch(event.dwDebugEventCode){
   case CREATE_PROCESS_DEBUG_EVENT:thread_starts[event.dwThreadId]=reinterpret_cast<DWORD64>(event.u.CreateProcessInfo.lpStartAddress);if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);if(!arm(event.dwThreadId,event.u.CreateProcessInfo.hThread)){admission_complete=false;reason="arm_failed";}break;
   case CREATE_THREAD_DEBUG_EVENT:thread_starts[event.dwThreadId]=reinterpret_cast<DWORD64>(event.u.CreateThread.lpStartAddress);if(!arm(event.dwThreadId,event.u.CreateThread.hThread)){admission_complete=false;reason="arm_failed";}break;
   case EXIT_THREAD_DEBUG_EVENT:retire(event.dwThreadId);break;
   case LOAD_DLL_DEBUG_EVENT:if(event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);break;
   case EXIT_PROCESS_DEBUG_EVENT:exited=true;reason="process_exited";break;
   case EXCEPTION_DEBUG_EVENT:{
    const DWORD code=event.u.Exception.ExceptionRecord.ExceptionCode;
    if(code==EXCEPTION_BREAKPOINT&&!ready&&own_break()){
     ready=census()&&PointerSession(process,o)&&PointerSource(process,o);
     if(ready){std::ofstream f(x.ready,std::ios::binary);f<<"{\"ready\":true,\"mode\":\"player-parent-pointer-read-once-v1\",\"armed_thread_count\":"<<armed.size()<<",\"census_complete\":true}\n";f.flush();ready=f.good();}
     if(!ready){admission_complete=false;reason="ready_failed";}else{deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(x.timeout);out<<"{\"kind\":\"ready\",\"census_complete\":true}\n";out.flush();}
     break;
    }
    CONTEXT c{};if(!owned(c)){
     const bool possible_owned=code==EXCEPTION_SINGLE_STEP&&armed.contains(event.dwThreadId)&&([&](){CONTEXT z{};return !GetContext(threads.at(event.dwThreadId),z)||(z.Dr6&1ULL)!=0;})();
     reason=possible_owned?"owned_site_context_unknown":"unrelated_exception";
     disposition=possible_owned?DBG_CONTINUE:DBG_EXCEPTION_NOT_HANDLED;break;
    }
    if(!pending_owned_proven){pending_owned_context=c;pending_owned_exception=reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress);}
     pending_owned_proven=true;pending_owned_tid=event.dwThreadId;pending_owned_generation=generations[event.dwThreadId];
    if(c.Rip==o.post_pc&&reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress)==o.post_pc&&c.Rbp==x.character){++captures;qualified=PointerCapture(out,process,o,c,event.dwThreadId,generations[event.dwThreadId],thread_birth[event.dwThreadId],reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress));reason=qualified?"target_captured":"target_read_incomplete";break;}
    ++foreign;
    if(foreign>=o.foreign_limit){reason="foreign_limit";break;}
    // Post-access trap: clear only owned B0, preserve the entire stopped control state.
    const DWORD64 rip=c.Rip;const DWORD flags=c.EFlags;c.Dr6&=~1ULL;c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
    if(!SetThreadContext(threads.at(event.dwThreadId),&c)){reason="watch_resume_failed";break;}
    CONTEXT a{};if(!GetContext(threads.at(event.dwThreadId),a)||a.Rip!=rip||a.EFlags!=flags||a.Dr0!=o.watch||(a.Dr7&0xffff00ffULL)!=0xb0001ULL||(a.Dr6&15)){reason="watch_resume_readback_failed";break;}
    if(foreign==1){out<<"{\"kind\":\"watch_resume\",\"count\":1,\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<",\"thread_created\":"<<PointerU64Json(thread_birth[event.dwThreadId])<<",\"RIP\":"<<PointerU64Json(c.Rip)<<",\"exception_address\":"<<PointerU64Json(reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress))<<",\"RCX\":"<<PointerU64Json(c.Rcx)<<",\"RDX\":"<<PointerU64Json(c.Rdx)<<",\"R8\":"<<PointerU64Json(c.R8)<<",\"R9\":"<<PointerU64Json(c.R9)<<",\"flags_before\":"<<flags<<",\"flags_after\":"<<a.EFlags<<",\"RIP_unchanged\":true,\"DR0_retained\":true,\"RF_modified\":false,\"TF\":false}\n";out.flush();}
    break;
   }
   default:break;
  }
  if(reason!="none"||exited)break; // pending real event retained until all vectors restored.
  pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)==FALSE;
  if(pending){reason="continue_failed";break;}
 }
 }catch(...){reason="observer_throw";}
 // Capture is closed. No call to PointerCapture or foreign resume is reachable below.
 if(attached){
  while(!detached&&!exited){
   if(WaitForSingleObject(process,0)==WAIT_OBJECT_0){exited=true;break;}
   if(!release_ready()){log_hold();Sleep(kWaitSliceMs);continue;}
   if(!pending){
    if(cleared&&!break_request_inflight){detached=DebugActiveProcessStop(x.pid)!=FALSE;if(detached)break;log_hold();Sleep(kWaitSliceMs);continue;}
    if(!break_attempted){break_request_inflight=DebugBreakProcess(process)!=FALSE;break_attempted=break_request_inflight;if(!break_request_inflight){log_hold();Sleep(kWaitSliceMs);}} // retry only a known FALSE; an ACK stays in-flight across timeouts.
    event={};if(!WaitForDebugEvent(&event,kWaitSliceMs)){log_hold();continue;}pending=true;pending_owned_proven=false;cleanup_new_event=true;cleanup_owned_reported=false;disposition=DBG_CONTINUE;
    if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT&&event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
    if(event.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT&&event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);
    if(event.dwDebugEventCode==EXIT_THREAD_DEBUG_EVENT)retire(event.dwThreadId);
    if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT){exited=true;break;}
    if(own_break())break_request_inflight=false;
    if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&!own_break()){
     CONTEXT c{};if(!owned(c))disposition=DBG_EXCEPTION_NOT_HANDLED;
    }
   }
   if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT&&!remember_unarmed(event.dwThreadId,event.u.CreateThread.hThread,reinterpret_cast<DWORD64>(event.u.CreateThread.lpStartAddress))){log_hold();Sleep(kWaitSliceMs);continue;}
   if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode==EXCEPTION_SINGLE_STEP&&armed.contains(event.dwThreadId)&&threads.contains(event.dwThreadId)&&([&](){CONTEXT z{};return !GetContext(threads.at(event.dwThreadId),z)||(z.Dr6&1ULL)!=0||pending_owned_proven||queued_data.contains(event.dwThreadId);})()){
    CONTEXT c{};if(!owned(c)){log_hold();Sleep(kWaitSliceMs);continue;} // retry context/classification; keep pending, never detach on unknown.
    if(!pending_owned_proven){pending_owned_context=c;pending_owned_exception=reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress);}
     pending_owned_proven=true;pending_owned_tid=event.dwThreadId;pending_owned_generation=generations[event.dwThreadId];
    disposition=DBG_CONTINUE;
    if(cleanup_new_event&&!cleanup_owned_reported){out<<"{\"kind\":\"cleanup_owned_data\",\"owned_late_event\":true,\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<",\"thread_created\":"<<PointerU64Json(thread_birth[event.dwThreadId])<<",\"RIP\":"<<PointerU64Json(c.Rip)<<",\"exception_address\":"<<PointerU64Json(reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress))<<",\"restored_generation\":"<<(restored.contains(event.dwThreadId)?"true":"false")<<",\"debug\":";PointerDrJson(out,c);out<<"}\n";out.flush();cleanup_owned_reported=true;}
   }
   cleared=restore_all();if(!cleared){log_hold();Sleep(kWaitSliceMs);continue;}
   if(!release_ready())continue;
   if(fault("continue"))continue;
   pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)==FALSE;
   if(pending){log_hold();Sleep(kWaitSliceMs);continue;}
   queued_data.erase(event.dwThreadId); // Consume only after actual successful Continue for this event.
   cleanup_new_event=false;cleanup_owned_reported=false;
   if(!break_request_inflight){detached=DebugActiveProcessStop(x.pid)!=FALSE;if(!detached){log_hold();Sleep(kWaitSliceMs);}}
  }
 }
 if(exited&&pending){
  while(!ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)){log_hold();Sleep(kWaitSliceMs);}
  pending=false;
 }
 const bool clean=attached&&cleared&&detached&&!pending&&!exited;
 out<<"{\"kind\":\"terminal\",\"reason\":\""<<reason<<"\",\"capture_count\":"<<captures<<",\"foreign_count\":"<<foreign
 <<",\"restored\":"<<(cleared?"true":"false")<<",\"detached\":"<<(detached?"true":"false")<<",\"pending_event\":"<<(pending?"true":"false")
 <<",\"cleanup_complete\":"<<(clean?"true":"false")<<",\"process_exited\":"<<(exited?"true":"false")
 <<",\"observation_thread_admission_complete\":"<<(admission_complete&&ready?"true":"false")
 <<",\"window_complete\":false,\"full_R08\":false}\n";out.flush();
 for(auto [tid,h]:threads){(void)tid;if(h)CloseHandle(h);}
 CloseHandle(cancel);if(release)CloseHandle(release);CloseHandle(process);SetConsoleCtrlHandler(OnConsoleControl,FALSE);
 return clean&&qualified&&captures==1?0:1;
}
int PointerEntryMain(int argc,wchar_t**argv){
 if((argc!=13&&argc!=15)||std::wstring(argv[2])!=L"--admission-meta"||std::wstring(argv[4])!=L"--timeout-ms"||
 std::wstring(argv[6])!=L"--raw"||std::wstring(argv[8])!=L"--ready"||std::wstring(argv[10])!=L"--machine-id"||std::wstring(argv[12])!=L"--explicit-player-pointer-readwatch-v1")return 2;
 const bool cold=std::wstring(argv[1])==L"--enable-parent-pointer-read-cold";
 if(!cold&&std::wstring(argv[1])!=L"--enable-ck3-12004-player-pointer-read")return 2;
 if(argc==15&&(!cold||std::wstring(argv[13])!=L"--cold-fault"))return 2;
 try{
  if(std::filesystem::file_size(std::filesystem::path(argv[3]))>32768)return 2;
  std::ifstream f{std::filesystem::path(argv[3])};if(!f)return 2;std::map<std::string,std::string>m;std::string line;
  while(std::getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto p=line.find('=');if(p==std::string::npos||!m.emplace(line.substr(0,p),line.substr(p+1)).second)return 2;}
  const std::set<std::string>cold_keys{"parent_schema","pid","tid","created","full_id","local_player_id","character","context","module_base","module_size","parent_pointer_read","post_pc","watch_address","clock_pointer","game_state","date_raw","absolute_day_raw","absolute_day","foreign_limit","go_event","cancel_event","audit_event","finish_event","fault_release_event"};
  const std::set<std::string>live_keys{"post_pc","watch_address","parent_schema","pid","tid","created","character","context","full_id","module_base","module_size","parent_mode_qualified","prefix_sha256","qualified_exe_sha256","game_version","steam_build_id","controlled_window_id","payment_epoch","connection_generation","native_revision","date_raw","source_cash_sha256","admission_id","foreign_limit","cancel_event","owner_binding_schema","owner_binding_mode","episode_projection","episode_is_null","episode_id","original_episode_key_present","game_state_identity_witness","local_player_id","absolute_day_raw","callsite_anchor_rva"};
  std::set<std::string>keys;for(const auto&item:m)keys.insert(item.first);if(keys!=(cold?cold_keys:live_keys))return 2;
  auto v=[&](const char*k){const auto&s=m.at(k);if(s.empty()||s.front()=='-')throw std::invalid_argument("unsigned metadata");std::size_t used=0;auto n=std::stoull(s,&used,0);if(used!=s.size())throw std::invalid_argument("suffix");return n;};
  PointerOptions o;auto&x=o.x;x.fixture=cold;x.ordinary_null=!cold;
  if(m.at("parent_schema")!=(cold?"xar.maintenance.parent_pointer_read.cold-meta.v1":"xar.maintenance.parent_pointer_read.admission.v1"))return 2;
  const auto pid=v("pid"),id=v("full_id");if(!pid||pid>0xffffffffULL||!id||id>=0xffffffffULL)return 2;
  const auto tid=v("tid");if(tid>0xffffffffULL)return 2;
  x.pid=DWORD(pid);x.full_id=std::uint32_t(id);x.initial_tid=DWORD(tid);x.created=v("created");x.character=v("character");x.secondary=v("context");x.base=v("module_base");x.module_size=v("module_size");x.local_player=v("local_player_id");
  if(!x.local_player||x.local_player>0xffffffffULL||(cold&&(!x.base||!x.module_size)))return 2;
  const std::wstring timeout_text=argv[5];std::size_t timeout_used=0;const auto timeout=std::stoull(timeout_text,&timeout_used);if(timeout_used!=timeout_text.size()||timeout<500||timeout>30000)return 2;
  x.timeout=DWORD(timeout);x.raw=argv[7];x.ready=argv[9];std::wstring machine=argv[11];
  if(machine.empty()||machine.find_first_not_of(L"abcdefghijklmnopqrstuvwxyz0123456789-")!=std::wstring::npos)return 2;x.machine.assign(machine.begin(),machine.end());
  auto wide=[](const std::string&s){if(s.empty()||s.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.\\")!=std::string::npos)throw std::invalid_argument("event name");return std::wstring(s.begin(),s.end());};
  o.cancel_name=wide(m.at("cancel_event"));const auto limit=v("foreign_limit");if(limit!=4096&&!(cold&&limit==512))return 2;o.foreign_limit=unsigned(limit);
  if(cold){o.entry=v("parent_pointer_read");o.post_pc=v("post_pc");o.watch=v("watch_address");o.clock_pointer=v("clock_pointer");if(o.clock_pointer>0x7ffffffff000ULL-16||!o.clock_pointer)return 2;o.release_name=wide(m.at("fault_release_event"));o.admission_id="synthetic-cold";x.game_state=v("game_state");x.admission_date=std::stoll(m.at("date_raw"));x.absolute_day=v("absolute_day");if(x.absolute_day!=v("absolute_day_raw"))return 2;}
  else{
   if(v("post_pc")!=x.base+kPointerEntryRva+26||v("watch_address")!=x.character+0x1c0||v("parent_mode_qualified")!=1||m.at("prefix_sha256")!=kPointerPrefixSha||m.at("qualified_exe_sha256")!="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"||m.at("game_version")!="1.20.0.4"||v("steam_build_id")!=25734779||v("episode_is_null")!=1||!m.at("episode_id").empty()||m.at("episode_projection")!="native_campaign"||v("callsite_anchor_rva")!=kPointerEntryRva||v("original_episode_key_present")>1||m.at("owner_binding_schema")!="xar.maintenance.parent_pointer_read.owner-binding.v2"||m.at("owner_binding_mode")!="native_campaign_character_pointer_read_v1")return 2;
   o.entry=x.base+kPointerEntryRva;o.post_pc=o.entry+26;o.watch=x.character+0x1c0;x.game_state=v("game_state_identity_witness");x.window=v("controlled_window_id");x.epoch=v("payment_epoch");x.generation=v("connection_generation");x.revision=v("native_revision");x.admission_date=std::stoll(m.at("date_raw"));x.absolute_day=v("absolute_day_raw");x.episode_key_present=v("original_episode_key_present")==1;x.packet_sha=m.at("source_cash_sha256");o.admission_id=m.at("admission_id");
   if(!x.window||!x.epoch||!x.generation||!x.revision||o.admission_id.size()!=64||x.packet_sha.size()!=64||o.admission_id.find_first_not_of("0123456789abcdef")!=std::string::npos||x.packet_sha.find_first_not_of("0123456789abcdef")!=std::string::npos)return 2;
  }
  if(o.post_pc!=o.entry+26||o.watch!=x.character+0x1c0||o.watch%8||!x.game_state||x.game_state>0x7ffffffff000ULL||x.admission_date<0||x.admission_date>=0xffffffffLL-24||x.absolute_day>=0xffffffffULL||!x.base||x.base>0x7ffffffff000ULL-x.module_size)return 2;
  if(argc==15){std::wstring a=argv[14];o.fault.assign(a.begin(),a.end());if(o.fault!="none"&&o.fault!="restore"&&o.fault!="readback"&&o.fault!="continue")return 2;}
  return PointerProbe(o);
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
