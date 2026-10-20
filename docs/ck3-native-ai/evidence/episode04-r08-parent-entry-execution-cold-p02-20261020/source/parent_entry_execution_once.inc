// Independent default-OFF parent-entry execution breakpoint. Source-only candidate.
// A08 data Probe/Arm and the 3F90A6F dispatch ABI are not this mode.
constexpr DWORD64 kParentEntryRva=0x28f7840;
constexpr std::array<std::uint8_t,16> kParentPrefix{0x48,0x8b,0xc4,0x53,0x55,0x48,0x81,0xec,0x98,0,0,0,0x4c,0x89,0x70,0xe0};
constexpr char kParentPrefixSha[]="d44f03f2855791f5fb4ee339dc21b28917e981d419df5cb4f1ecb89ba20aa517";
struct ParentOptions {
 Config x;DWORD64 entry=0,clock_pointer=0;unsigned foreign_limit=4096;
 std::string admission_id,fault="none";std::wstring cancel_name,release_name;
};
struct ParentClock {DWORD64 state=0;std::uint32_t date=0,day=0;};
std::uint64_t ParentThreadCreated(HANDLE h){FILETIME c{},e{},k{},u{};if(!GetThreadTimes(h,&c,&e,&k,&u))return 0;ULARGE_INTEGER v{};v.LowPart=c.dwLowDateTime;v.HighPart=c.dwHighDateTime;return v.QuadPart;}
bool ParentReadClock(HANDLE p,const ParentOptions&o,ParentClock&v){
 if(o.x.fixture)return Read(p,o.clock_pointer,v.state)&&Read(p,o.clock_pointer+8,v.date)&&Read(p,o.clock_pointer+12,v.day);
 DWORD64 date=0;return Read(p,o.x.base+0x5c68c50,v.state)&&Read(p,v.state+8,date)&&Read(p,v.state+0x9c,v.day)&&(v.date=static_cast<std::uint32_t>(date),true);
}
bool ParentSource(HANDLE p,const ParentOptions&o){
 std::array<std::uint8_t,16>b{};SIZE_T n=0;
 return ReadProcessMemory(p,reinterpret_cast<void*>(o.entry),b.data(),b.size(),&n)&&n==b.size()&&b==kParentPrefix;
}
bool ParentSession(HANDLE p,const ParentOptions&o){
 ParentClock a{},b{};return Created(p)==o.x.created&&ParentReadClock(p,o,a)&&ParentReadClock(p,o,b)&&
 a.state==b.state&&a.state==o.x.game_state&&a.date==b.date&&a.day==b.day&&
 a.date>=o.x.admission_date&&a.date<=static_cast<std::uint64_t>(o.x.admission_date)+24&&a.day>=o.x.absolute_day&&a.day<=o.x.absolute_day+1;
}
bool ParentArm(HANDLE h,DWORD64 site){
 CONTEXT c{};if(!GetContext(h,c)||c.Dr0||c.Dr1||c.Dr2||c.Dr3||(c.Dr7&(0xffULL|0xffff0000ULL))||(c.EFlags&0x100))return false;
 g_saved_debug[GetThreadId(h)]={c.Dr0,c.Dr1,c.Dr2,c.Dr3,c.Dr6,c.Dr7};
 c.Dr0=site;c.Dr1=c.Dr2=c.Dr3=c.Dr6=0;c.Dr7|=1;
 c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
 if(!SetThreadContext(h,&c))return false;
 CONTEXT a{};return GetContext(h,a)&&a.Dr0==site&&!a.Dr1&&!a.Dr2&&!a.Dr3&&a.Dr7==c.Dr7&&(a.Dr6&15)==0;
}
bool ParentCapture(std::ofstream&out,HANDLE p,const ParentOptions&o,const CONTEXT&c,DWORD tid,unsigned gen,std::uint64_t birth){
 std::uint32_t id1=0,id2=0,magic1=0,magic2=0;DWORD64 death1=0,death2=0,ctx1=0,ctx2=0,ret1=0,ret2=0;
 ParentClock ca{},cb{};
 const bool first=Read(p,c.Rdx+0x18,id1)&&Read(p,c.Rdx+0x1c,magic1)&&Read(p,c.Rdx+0x1d0,death1)&&Read(p,c.Rdx+0x1c0,ctx1)&&Read(p,c.Rsp,ret1)&&ParentReadClock(p,o,ca);
 const bool second=Read(p,c.Rdx+0x18,id2)&&Read(p,c.Rdx+0x1c,magic2)&&Read(p,c.Rdx+0x1d0,death2)&&Read(p,c.Rdx+0x1c0,ctx2)&&Read(p,c.Rsp,ret2)&&ParentReadClock(p,o,cb);
 const bool object=first&&second&&id1==o.x.full_id&&id2==id1&&magic1==0x43686172&&magic2==magic1&&!death1&&!death2;
 const bool context=first&&second&&ctx1==ctx2&&ctx1==o.x.secondary;
 const bool clock=first&&second&&ca.state==cb.state&&ca.state==o.x.game_state&&ca.date==cb.date&&ca.day==cb.day&&
 ca.date>=o.x.admission_date&&ca.date<=static_cast<std::uint64_t>(o.x.admission_date)+24&&ca.day>=o.x.absolute_day&&ca.day<=o.x.absolute_day+1;
 const bool source=ParentSource(p,o);const bool qualified=object&&clock&&source&&Created(p)==o.x.created;
 LARGE_INTEGER q{};QueryPerformanceCounter(&q);
 out<<"{\"kind\":\"parent_entry\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<gen<<",\"thread_created\":"<<birth<<",\"RIP\":"<<c.Rip
 <<",\"RDX\":"<<c.Rdx<<",\"RCX\":"<<c.Rcx<<",\"R8\":"<<c.R8<<",\"R9\":"<<c.R9<<",\"RSP\":"<<c.Rsp
 <<",\"DR6\":"<<c.Dr6<<",\"qpc\":"<<q.QuadPart<<",\"first_read_complete\":"<<(first?"true":"false")
 <<",\"second_read_complete\":"<<(second?"true":"false")<<",\"full_id_before\":"<<id1<<",\"full_id_after\":"<<id2
 <<",\"magic_before\":"<<magic1<<",\"magic_after\":"<<magic2<<",\"death_before\":"<<death1<<",\"death_after\":"<<death2
 <<",\"context_before\":"<<ctx1<<",\"context_after\":"<<ctx2<<",\"admitted_context_unchanged\":"<<(context?"true":"false")
 <<",\"return_before\":"<<ret1<<",\"return_after\":"<<ret2<<",\"state_before\":"<<ca.state<<",\"state_after\":"<<cb.state
 <<",\"date_before\":"<<ca.date<<",\"date_after\":"<<cb.date<<",\"day_before\":"<<ca.day<<",\"day_after\":"<<cb.day
 <<",\"source_anchor_matches\":"<<(source?"true":"false")<<",\"entry_owner_clock_qualified\":"<<(qualified?"true":"false")
 <<",\"parent_return_observed\":false,\"paid_maintenance_raw\":null,\"payer\":null,\"cadence\":null}\n";out.flush();return qualified;
}
DWORD64 ParentRemoteNtdllExport(DWORD pid,const char*name){
 HMODULE local=GetModuleHandleW(L"ntdll.dll");auto fn=GetProcAddress(local,name);if(!local||!fn)return 0;
 const auto rva=reinterpret_cast<DWORD64>(fn)-reinterpret_cast<DWORD64>(local);
 HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,pid);if(s==INVALID_HANDLE_VALUE)return 0;
 MODULEENTRY32W e{};e.dwSize=sizeof(e);DWORD64 result=0;
 if(Module32FirstW(s,&e)){do{if(_wcsicmp(e.szModule,L"ntdll.dll")==0&&rva<e.modBaseSize){result=reinterpret_cast<DWORD64>(e.modBaseAddr)+rva;break;}}while(Module32NextW(s,&e));}CloseHandle(s);return result;
}
int ParentProbe(ParentOptions o){
 auto&x=o.x;
 if(x.timeout<500||x.timeout>30000||!x.pid||!x.created||!x.character||!x.secondary||!x.full_id||
 x.character>0x7fffffffee00ULL||x.secondary>0x7ffffffff000ULL||x.secondary%8||!o.entry||
 std::filesystem::exists(x.raw)||std::filesystem::exists(x.ready))return 2;
 HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ|PROCESS_CREATE_THREAD|SYNCHRONIZE,FALSE,x.pid);
 if(!process)return 2;
 std::array<wchar_t,32768>image{},own{};DWORD n=DWORD(image.size()),m=GetModuleFileNameW(nullptr,own.data(),DWORD(own.size()));
 bool image_ok=QueryFullProcessImageNameW(process,0,image.data(),&n)!=FALSE;
 const auto path=std::filesystem::path(std::wstring(image.data(),n));const auto admitted_base=x.base,admitted_size=x.module_size;
 image_ok=image_ok&&(x.fixture?(path.filename()==L"maintenance_parent_entry_cold_target.exe"&&path.parent_path()==std::filesystem::path(std::wstring(own.data(),m)).parent_path()):(_wcsicmp(path.filename().c_str(),L"ck3.exe")==0&&ExactActual4Anchor(process,x.pid,x.base,x.module_size)));
 if(!x.fixture){image_ok=image_ok&&x.base==admitted_base&&x.module_size==admitted_size;o.entry=x.base+kParentEntryRva;}
 ParentClock initial{};
 if(x.fixture&&!ParentReadClock(process,o,initial)){CloseHandle(process);return 2;}
 BOOL debugger=FALSE;
 if(!image_ok||o.entry<x.base||x.module_size<16||o.entry-x.base>x.module_size-16||Created(process)!=x.created||!Identity(process,x)||!ParentSession(process,o)||!ParentSource(process,o)||
 !CheckRemoteDebuggerPresent(process,&debugger)||debugger){CloseHandle(process);return 2;}
 const DWORD64 breakin=ParentRemoteNtdllExport(x.pid,"DbgUiRemoteBreakin"),breakpoint=ParentRemoteNtdllExport(x.pid,"DbgBreakPoint");
 if(!breakin||!breakpoint){CloseHandle(process);return 2;}
 HANDLE cancel=OpenEventW(SYNCHRONIZE,FALSE,o.cancel_name.c_str());
 HANDLE release=nullptr;if(o.fault!="none")release=OpenEventW(SYNCHRONIZE,FALSE,o.release_name.c_str());
 if(!cancel||(o.fault!="none"&&!release)){if(cancel)CloseHandle(cancel);CloseHandle(process);return 2;}
 std::ofstream out(x.raw,std::ios::binary);if(!out){CloseHandle(cancel);if(release)CloseHandle(release);CloseHandle(process);return 2;}
 out<<"{\"kind\":\"start\",\"schema\":\"xar.maintenance.parent_entry.raw.v1\",\"mode\":\"parent-entry-execution-once-v1\",\"machine_id\":\""<<x.machine
 <<"\",\"synthetic\":"<<(x.fixture?"true":"false")<<",\"pid\":"<<x.pid<<",\"created\":"<<x.created<<",\"entry\":"<<o.entry
 <<",\"module_base\":"<<x.base<<",\"module_size\":"<<x.module_size<<",\"character\":"<<x.character<<",\"full_id\":"<<x.full_id<<",\"context\":"<<x.secondary<<",\"local_player_id\":"<<x.local_player
 <<",\"game_state\":"<<x.game_state<<",\"date_raw\":"<<x.admission_date<<",\"absolute_day\":"<<x.absolute_day
 <<",\"admission_id\":\""<<o.admission_id<<"\",\"prefix_sha256\":\""<<kParentPrefixSha<<"\",\"foreign_limit\":"<<o.foreign_limit
 <<",\"capture_ms\":"<<x.timeout<<",\"target_record_limit\":1,\"owner_binding\":"<<(x.fixture?"null":OwnerJson(x))<<"}\n";out.flush();
 bool attached=DebugActiveProcess(x.pid)!=FALSE,kill_off=false,pending=false,ready=false,exited=false,detached=false,cleared=false,admission_complete=true,hold_logged=false,fault_used=false;
 bool qualified=false;unsigned captures=0,foreign=0;std::uint64_t events=0;
 std::string reason=attached?"none":"attach_failed";DEBUG_EVENT event{};DWORD disposition=DBG_CONTINUE;
 std::map<DWORD,HANDLE>threads;std::set<DWORD>armed,restored,restore_attempted,unarmed_reported;std::map<DWORD,unsigned>generations;std::map<DWORD,DWORD64>thread_starts,thread_birth;
 bool break_attempted=false,break_request_inflight=false,cleanup_new_event=false,cleanup_owned_reported=false,pending_owned_proven=false;
 DWORD pending_owned_tid=0;unsigned pending_owned_generation=0;
 auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(30000);
 SetConsoleCtrlHandler(OnConsoleControl,TRUE);
 if(attached){kill_off=DebugSetProcessKillOnExit(FALSE)!=FALSE;if(!kill_off)reason="kill_on_exit_disable_failed";}
 auto log_hold=[&](){if(!hold_logged){out<<"{\"kind\":\"unresolved_cleanup_hold\",\"Popen_must_remain_retained\":true,\"cleanup_complete\":false,\"no_more_capture\":true}\n";out.flush();hold_logged=true;}};
 auto fault=[&](const char*name){if(o.fault!=name||fault_used)return false;fault_used=true;log_hold();return true;};
 auto release_ready=[&](){return !fault_used||!release||WaitForSingleObject(release,0)==WAIT_OBJECT_0;};
 auto arm=[&](DWORD tid,HANDLE borrowed){
  if(threads.size()>=256||!BeginThreadOwnership(tid,threads,armed))return false;
  HANDLE h=nullptr;if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
  threads[tid]=h;++generations[tid];thread_birth[tid]=ParentThreadCreated(h);restored.erase(tid);restore_attempted.erase(tid);bool ok=thread_birth[tid]&&ParentArm(h,o.entry);
  if(g_saved_debug.contains(tid))armed.insert(tid);
  CONTEXT c{};bool got=GetContext(h,c);
  out<<"{\"kind\":\"arm\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<thread_birth[tid]<<",\"success\":"<<(ok?"true":"false")<<",\"saved_debug\":[";
  auto it=g_saved_debug.find(tid);if(it!=g_saved_debug.end())for(unsigned i=0;i<6;++i){if(i)out<<',';out<<it->second[i];}
  out<<"],\"armed_debug\":";DrJson(out,c);out<<",\"readback\":"<<(got?"true":"false")<<"}\n";out.flush();return ok;
 };
 auto retire=[&](DWORD tid){
  auto it=threads.find(tid);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}
  if(armed.erase(tid))out<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<"}\n";
  restored.erase(tid);restore_attempted.erase(tid);g_saved_debug.erase(tid);thread_starts.erase(tid);thread_birth.erase(tid);unarmed_reported.erase(tid);
 };
 auto restore_all=[&](){
  bool ok=true;
  for(DWORD tid:armed){
   if(restored.contains(tid))continue;
   auto h=threads.find(tid);auto s=g_saved_debug.find(tid);
   if(h==threads.end()||s==g_saved_debug.end()){ok=false;continue;}
   CONTEXT c{};if(!GetContext(h->second,c)){ok=false;continue;}
   const bool already_original=restore_attempted.contains(tid)&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr6==s->second[4]&&c.Dr7==s->second[5];
   c.Dr0=s->second[0];c.Dr1=s->second[1];c.Dr2=s->second[2];c.Dr3=s->second[3];c.Dr6=s->second[4];c.Dr7=s->second[5];c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
   if(!already_original){restore_attempted.insert(tid);if(fault("restore")||!SetThreadContext(h->second,&c)){ok=false;continue;}}
   CONTEXT a{};const bool got=GetContext(h->second,a);
   const bool equal=got&&a.Dr0==c.Dr0&&a.Dr1==c.Dr1&&a.Dr2==c.Dr2&&a.Dr3==c.Dr3&&a.Dr6==c.Dr6&&a.Dr7==c.Dr7;
   if(fault("readback")){ok=false;continue;}
   if(equal)restored.insert(tid);else{ok=false;continue;} // failed attempts do not duplicate a success proof row.
   out<<"{\"kind\":\"restore\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<thread_birth[tid]<<",\"readback\":"<<(got?"true":"false")<<",\"equal_original\":"<<(equal?"true":"false")<<",\"debug\":";DrJson(out,a);out<<"}\n";
  }out.flush();return ok&&restored.size()==armed.size();
 };
 auto owned=[&](CONTEXT&c){
  auto it=threads.find(event.dwThreadId);
  if(event.dwDebugEventCode!=EXCEPTION_DEBUG_EVENT||event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_SINGLE_STEP||
   it==threads.end()||!armed.contains(event.dwThreadId)||!GetContext(it->second,c)||c.Rip!=o.entry||
   reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress)!=o.entry||(c.EFlags&0x100))return false;
  const bool same_proven_event=pending_owned_proven&&pending_owned_tid==event.dwThreadId&&pending_owned_generation==generations[event.dwThreadId];
  if(!restored.contains(event.dwThreadId)){
   auto s=g_saved_debug.find(event.dwThreadId);
   if(same_proven_event&&restore_attempted.contains(event.dwThreadId)&&s!=g_saved_debug.end()&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr6==s->second[4]&&c.Dr7==s->second[5])return true;
   return !(c.Dr6&0xe000)&&((c.Dr6&15)==1||(same_proven_event&&(c.Dr6&15)==0))&&c.Dr0==o.entry&&!c.Dr1&&!c.Dr2&&!c.Dr3&&(c.Dr7&0xffff00ffULL)==1;
  }
  // A queued event may arrive after this same generation was restored.
  auto s=g_saved_debug.find(event.dwThreadId);
  return s!=g_saved_debug.end()&&(c.Dr6==s->second[4]||c.Dr6==(s->second[4]|1ULL))&&c.Dr0==s->second[0]&&c.Dr1==s->second[1]&&c.Dr2==s->second[2]&&c.Dr3==s->second[3]&&c.Dr7==s->second[5];
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
  const auto birth=ParentThreadCreated(borrowed);if(!birth)return false;
  if(threads.contains(tid)&&thread_birth[tid]!=birth)return false;
  if(!threads.contains(tid)){
   if(threads.size()>=256)return false;HANDLE h=nullptr;
   if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
   threads[tid]=h;++generations[tid];thread_birth[tid]=birth;thread_starts[tid]=start;
  }
  CONTEXT c{};if(!GetContext(threads.at(tid),c)||c.Dr0||c.Dr1||c.Dr2||c.Dr3||(c.Dr7&(0xffULL|0xffff0000ULL)))return false;
  if(unarmed_reported.insert(tid).second){out<<"{\"kind\":\"cleanup_thread_unarmed\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"thread_created\":"<<birth<<",\"readback\":true,\"debug\":";DrJson(out,c);out<<"}\n";out.flush();}return true;
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
     ready=census()&&ParentSession(process,o)&&ParentSource(process,o);
     if(ready){std::ofstream f(x.ready,std::ios::binary);f<<"{\"ready\":true,\"mode\":\"parent-entry-execution-once-v1\",\"armed_thread_count\":"<<armed.size()<<",\"census_complete\":true}\n";f.flush();ready=f.good();}
     if(!ready){admission_complete=false;reason="ready_failed";}else{deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(x.timeout);out<<"{\"kind\":\"ready\",\"census_complete\":true}\n";out.flush();}
     break;
    }
    CONTEXT c{};if(!owned(c)){
     const bool possible_owned=code==EXCEPTION_SINGLE_STEP&&armed.contains(event.dwThreadId)&&reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress)==o.entry;
     reason=possible_owned?"owned_site_context_unknown":"unrelated_exception";
     disposition=possible_owned?DBG_CONTINUE:DBG_EXCEPTION_NOT_HANDLED;break;
    }
    pending_owned_proven=true;pending_owned_tid=event.dwThreadId;pending_owned_generation=generations[event.dwThreadId];
    if(c.Rdx==x.character){++captures;qualified=ParentCapture(out,process,o,c,event.dwThreadId,generations[event.dwThreadId],thread_birth[event.dwThreadId]);reason=qualified?"target_captured":"target_read_incomplete";break;}
    ++foreign;
    if(foreign>=o.foreign_limit){reason="foreign_limit";break;}
    // Pre-instruction fault: retain DR0, unchanged RIP/args, RF for one instruction, never TF.
    const DWORD64 rip=c.Rip;c.Dr6=0;c.EFlags=(c.EFlags|0x10000)&~0x100;c.ContextFlags=CONTEXT_CONTROL|CONTEXT_DEBUG_REGISTERS;
    if(!SetThreadContext(threads.at(event.dwThreadId),&c)){reason="foreign_resume_failed";break;}
    CONTEXT a{};if(!GetContext(threads.at(event.dwThreadId),a)||a.Rip!=rip||a.Dr0!=o.entry||(a.Dr7&0xffff00ffULL)!=1||!(a.EFlags&0x10000)||(a.EFlags&0x100)){reason="foreign_resume_readback_failed";break;}
    if(foreign==1){out<<"{\"kind\":\"foreign_resume\",\"count\":1,\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<",\"thread_created\":"<<thread_birth[event.dwThreadId]<<",\"RCX\":"<<c.Rcx<<",\"RDX\":"<<c.Rdx<<",\"R8\":"<<c.R8<<",\"R9\":"<<c.R9<<",\"RIP_unchanged\":true,\"DR0_retained\":true,\"RF_once\":true,\"TF\":false}\n";out.flush();}
    break;
   }
   default:break;
  }
  if(reason!="none"||exited)break; // pending real event retained until all vectors restored.
  pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)==FALSE;
  if(pending){reason="continue_failed";break;}
 }
 }catch(...){reason="observer_throw";}
 // Capture is closed. No call to ParentCapture or foreign resume is reachable below.
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
   if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode==EXCEPTION_SINGLE_STEP&&reinterpret_cast<DWORD64>(event.u.Exception.ExceptionRecord.ExceptionAddress)==o.entry){
    CONTEXT c{};if(!owned(c)){log_hold();Sleep(kWaitSliceMs);continue;} // retry context/classification; keep pending, never detach on unknown.
    pending_owned_proven=true;pending_owned_tid=event.dwThreadId;pending_owned_generation=generations[event.dwThreadId];
    disposition=DBG_CONTINUE;
    if(cleanup_new_event&&!cleanup_owned_reported){out<<"{\"kind\":\"cleanup_owned_execution\",\"owned_late_event\":true,\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<",\"thread_created\":"<<thread_birth[event.dwThreadId]<<",\"RIP\":"<<c.Rip<<",\"restored_generation\":"<<(restored.contains(event.dwThreadId)?"true":"false")<<",\"debug\":";DrJson(out,c);out<<"}\n";out.flush();cleanup_owned_reported=true;}
   }
   cleared=restore_all();if(!cleared){log_hold();Sleep(kWaitSliceMs);continue;}
   if(!release_ready())continue;
   if(fault("continue"))continue;
   pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)==FALSE;
   if(pending){log_hold();Sleep(kWaitSliceMs);continue;}
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
int ParentEntryMain(int argc,wchar_t**argv){
 if((argc!=13&&argc!=15)||std::wstring(argv[2])!=L"--admission-meta"||std::wstring(argv[4])!=L"--timeout-ms"||
 std::wstring(argv[6])!=L"--raw"||std::wstring(argv[8])!=L"--ready"||std::wstring(argv[10])!=L"--machine-id"||std::wstring(argv[12])!=L"--explicit-execution-breakpoint-v1")return 2;
 const bool cold=std::wstring(argv[1])==L"--enable-parent-entry-execution-cold";
 if(!cold&&std::wstring(argv[1])!=L"--enable-ck3-12004-parent-entry-once")return 2;
 if(argc==15&&(!cold||std::wstring(argv[13])!=L"--cold-fault"))return 2;
 try{
  if(std::filesystem::file_size(std::filesystem::path(argv[3]))>32768)return 2;
  std::ifstream f{std::filesystem::path(argv[3])};if(!f)return 2;std::map<std::string,std::string>m;std::string line;
  while(std::getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto p=line.find('=');if(p==std::string::npos||!m.emplace(line.substr(0,p),line.substr(p+1)).second)return 2;}
  const std::set<std::string>cold_keys{"parent_schema","pid","tid","created","full_id","local_player_id","character","context","module_base","module_size","parent_entry","clock_pointer","game_state","date_raw","absolute_day_raw","absolute_day","foreign_limit","go_event","cancel_event","audit_event","finish_event","fault_release_event"};
  const std::set<std::string>live_keys{"parent_schema","pid","tid","created","character","context","full_id","module_base","module_size","parent_mode_qualified","prefix_sha256","qualified_exe_sha256","game_version","steam_build_id","controlled_window_id","payment_epoch","connection_generation","native_revision","date_raw","source_cash_sha256","admission_id","foreign_limit","cancel_event","owner_binding_schema","owner_binding_mode","episode_projection","episode_is_null","episode_id","original_episode_key_present","game_state_identity_witness","local_player_id","absolute_day_raw","callsite_anchor_rva"};
  std::set<std::string>keys;for(const auto&item:m)keys.insert(item.first);if(keys!=(cold?cold_keys:live_keys))return 2;
  auto v=[&](const char*k){const auto&s=m.at(k);if(s.empty()||s.front()=='-')throw std::invalid_argument("unsigned metadata");std::size_t used=0;auto n=std::stoull(s,&used,0);if(used!=s.size())throw std::invalid_argument("suffix");return n;};
  ParentOptions o;auto&x=o.x;x.fixture=cold;x.ordinary_null=!cold;
  if(m.at("parent_schema")!=(cold?"xar.maintenance.parent_entry.cold-meta.v1":"xar.maintenance.parent_entry.admission.v1"))return 2;
  const auto pid=v("pid"),id=v("full_id");if(!pid||pid>0xffffffffULL||!id||id>=0xffffffffULL)return 2;
  const auto tid=v("tid");if(tid>0xffffffffULL)return 2;
  x.pid=DWORD(pid);x.full_id=std::uint32_t(id);x.initial_tid=DWORD(tid);x.created=v("created");x.character=v("character");x.secondary=v("context");x.base=v("module_base");x.module_size=v("module_size");x.local_player=v("local_player_id");
  if(!x.local_player||x.local_player>0xffffffffULL||(cold&&(!x.base||!x.module_size)))return 2;
  const std::wstring timeout_text=argv[5];std::size_t timeout_used=0;const auto timeout=std::stoull(timeout_text,&timeout_used);if(timeout_used!=timeout_text.size()||timeout<500||timeout>30000)return 2;
  x.timeout=DWORD(timeout);x.raw=argv[7];x.ready=argv[9];std::wstring machine=argv[11];
  if(machine.empty()||machine.find_first_not_of(L"abcdefghijklmnopqrstuvwxyz0123456789-")!=std::wstring::npos)return 2;x.machine.assign(machine.begin(),machine.end());
  auto wide=[](const std::string&s){if(s.empty()||s.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.\\")!=std::string::npos)throw std::invalid_argument("event name");return std::wstring(s.begin(),s.end());};
  o.cancel_name=wide(m.at("cancel_event"));const auto limit=v("foreign_limit");if(limit!=4096&&!(cold&&limit==512))return 2;o.foreign_limit=unsigned(limit);
  if(cold){o.entry=v("parent_entry");o.clock_pointer=v("clock_pointer");if(o.clock_pointer>0x7ffffffff000ULL-16||!o.clock_pointer)return 2;o.release_name=wide(m.at("fault_release_event"));o.admission_id="synthetic-cold";x.game_state=v("game_state");x.admission_date=std::stoll(m.at("date_raw"));x.absolute_day=v("absolute_day");if(x.absolute_day!=v("absolute_day_raw"))return 2;}
  else{
   if(v("parent_mode_qualified")!=1||m.at("prefix_sha256")!=kParentPrefixSha||m.at("qualified_exe_sha256")!="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"||m.at("game_version")!="1.20.0.4"||v("steam_build_id")!=25734779||v("episode_is_null")!=1||!m.at("episode_id").empty()||m.at("episode_projection")!="native_campaign"||v("callsite_anchor_rva")!=kParentEntryRva||v("original_episode_key_present")>1||m.at("owner_binding_schema")!="xar.maintenance.writer_pc.owner-binding.v2"||m.at("owner_binding_mode")!="native_campaign_owned_no_load_v2")return 2;
   o.entry=x.base+kParentEntryRva;x.game_state=v("game_state_identity_witness");x.window=v("controlled_window_id");x.epoch=v("payment_epoch");x.generation=v("connection_generation");x.revision=v("native_revision");x.admission_date=std::stoll(m.at("date_raw"));x.absolute_day=v("absolute_day_raw");x.episode_key_present=v("original_episode_key_present")==1;x.packet_sha=m.at("source_cash_sha256");o.admission_id=m.at("admission_id");
   if(!x.window||!x.epoch||!x.generation||!x.revision||o.admission_id.size()!=64||x.packet_sha.size()!=64||o.admission_id.find_first_not_of("0123456789abcdef")!=std::string::npos||x.packet_sha.find_first_not_of("0123456789abcdef")!=std::string::npos)return 2;
  }
  if(!x.game_state||x.game_state>0x7ffffffff000ULL||x.admission_date<0||x.admission_date>=0xffffffffLL-24||x.absolute_day>=0xffffffffULL||!x.base||x.base>0x7ffffffff000ULL-x.module_size)return 2;
  if(argc==15){std::wstring a=argv[14];o.fault.assign(a.begin(),a.end());if(o.fault!="none"&&o.fault!="restore"&&o.fault!="readback"&&o.fault!="continue")return 2;}
  return ParentProbe(o);
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
