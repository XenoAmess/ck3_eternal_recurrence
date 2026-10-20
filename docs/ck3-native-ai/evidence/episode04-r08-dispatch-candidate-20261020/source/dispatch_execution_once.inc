// Candidate only: independent execution-breakpoint mode, not a writer alias.
// The existing Probe/ArmThread data-write paths remain byte-for-byte unchanged.
constexpr DWORD64 kDispatchEntryRva = 0x3f909f0;
constexpr DWORD64 kDispatchCallRva = 0x3f90a6f;
constexpr char kDispatchSourceSha[] = "426e7b7c3e47980c4975bff0745518c9539d7bd06ae6f7f44d973789a7f3c11e";
constexpr std::array<std::uint8_t,253> kDispatchSource{0x48,0x89,0x5c,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x48,0x8b,0xfa,0xb9,0x1,0x0,0x0,0x0,0x33,0xc0,0xf0,0xf,0xb1,0x4b,0x60,0xf,0x85,0xc8,0x0,0x0,0x0,0x48,0x89,0x74,0x24,0x38,0xe8,0x94,0x13,0x29,0x0,0x48,0x8b,0xf0,0xe8,0xac,0x58,0x13,0x0,0x48,0x81,0xfe,0x80,0x96,0x98,0x0,0x75,0x6,0x48,0x6b,0xc0,0x64,0xeb,0x1e,0x48,0x99,0x48,0xf7,0xfe,0x48,0x8b,0xc8,0x48,0x69,0xc2,0x0,0xca,0x9a,0x3b,0x48,0x69,0xc9,0x0,0xca,0x9a,0x3b,0x48,0x99,0x48,0xf7,0xfe,0x48,0x3,0xc1,0x48,0x89,0x43,0x70,0xb8,0xff,0xff,0xff,0xff,0xf0,0xf,0xc1,0x7,0x48,0x8b,0x4b,0x38,0x48,0x8b,0x74,0x24,0x38,0x48,0x85,0xc9,0x74,0x7b,0x48,0x8b,0x1,0xff,0x50,0x10,0xb8,0x2,0x0,0x0,0x0,0x87,0x43,0x60,0xe8,0x31,0x13,0x29,0x0,0x48,0x8b,0xf8,0xe8,0x49,0x58,0x13,0x0,0x48,0x81,0xff,0x80,0x96,0x98,0x0,0x75,0x6,0x48,0x6b,0xc0,0x64,0xeb,0x1e,0x48,0x99,0x48,0xf7,0xff,0x48,0x8b,0xc8,0x48,0x69,0xc2,0x0,0xca,0x9a,0x3b,0x48,0x69,0xc9,0x0,0xca,0x9a,0x3b,0x48,0x99,0x48,0xf7,0xff,0x48,0x3,0xc1,0x48,0x2b,0x43,0x70,0xf,0x57,0xc0,0xf2,0x48,0xf,0x2a,0xc0,0xb0,0x1,0xf2,0xf,0x5e,0x5,0x5e,0x5d,0xa6,0x0,0xf2,0xf,0x11,0x43,0x68,0x48,0x8b,0x5c,0x24,0x40,0x48,0x83,0xc4,0x20,0x5f,0xc3,0x48,0x8b,0x5c,0x24,0x40,0x32,0xc0,0x48,0x83,0xc4,0x20,0x5f,0xc3,0xe8,0xc,0xfd,0x28,0x0,0xcc};

bool DispatchSource(HANDLE process, const Config &x) {
  std::array<std::uint8_t,253> actual{}; SIZE_T got=0;
  return x.base && ReadProcessMemory(process,reinterpret_cast<void*>(x.base+kDispatchEntryRva),
      actual.data(),actual.size(),&got) && got==actual.size() && actual==kDispatchSource;
}
bool ArmDispatchThread(HANDLE thread,DWORD64 site) {
  CONTEXT c{}; if(!GetContext(thread,c))return false;
  if(c.Dr0||c.Dr1||c.Dr2||c.Dr3||(c.Dr7&(0xffULL|0xffff0000ULL))||(c.EFlags&0x100))return false;
  g_saved_debug[GetThreadId(thread)]={c.Dr0,c.Dr1,c.Dr2,c.Dr3,c.Dr6,c.Dr7};
  c.Dr0=site;c.Dr1=c.Dr2=c.Dr3=c.Dr6=0;c.Dr7|=1; // L0=1, RW0=00, LEN0=00: execute only.
  c.ContextFlags=CONTEXT_CONTROL|CONTEXT_DEBUG_REGISTERS;
  if(!SetThreadContext(thread,&c))return false;
  CONTEXT a{};return GetContext(thread,a)&&a.Dr0==site&&!a.Dr1&&!a.Dr2&&!a.Dr3&&
    a.Dr7==c.Dr7&&(a.Dr6&15)==0;
}
bool CaptureDispatch(std::ofstream &o,HANDLE process,const Config &x,const CONTEXT &c,
                     DWORD tid,unsigned generation) {
  DWORD64 job1=0,job2=0,vptr1=0,vptr2=0,target1=0,target2=0,date1=0,date2=0,state1=0,state2=0;
  std::uint32_t day1=0,day2=0;
  const bool safe=c.Rbx&&c.Rbx<=0x7ffffffff000ULL-0x38&&c.Rcx&&c.Rcx<=0x7ffffffff000ULL&&
      c.Rax&&c.Rax<=0x7ffffffff000ULL-0x10;
  const bool clock1=Read(process,x.base+0x5c68c50,state1)&&state1==x.game_state&&
      Read(process,state1+8,date1)&&Read(process,state1+0x9c,day1);
  const bool source=DispatchSource(process,x);
  const bool first=safe&&Read(process,c.Rbx+0x38,job1)&&Read(process,c.Rcx,vptr1)&&Read(process,c.Rax+0x10,target1);
  const bool second=safe&&Read(process,c.Rbx+0x38,job2)&&Read(process,c.Rcx,vptr2)&&Read(process,c.Rax+0x10,target2);
  const bool clock2=Read(process,x.base+0x5c68c50,state2)&&state2==x.game_state&&
      Read(process,state2+8,date2)&&Read(process,state2+0x9c,day2);
  const bool owner=Identity(process,x);
  const bool stable=first&&second&&job1==job2&&job1==c.Rcx&&vptr1==vptr2&&vptr1==c.Rax&&target1==target2&&target1;
  const bool same_image=stable&&target1>=x.base&&target1-x.base<x.module_size;
  const bool clock=clock1&&clock2&&state1==state2&&date1==date2&&day1==day2;
  const bool qualified=source&&owner&&stable&&same_image&&clock;
  LARGE_INTEGER qpc{};QueryPerformanceCounter(&qpc);
  o<<"{\"kind\":\"dispatch_call_pre_instruction\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generation
    <<",\"RIP\":"<<c.Rip<<",\"RIP_rva\":"<<kDispatchCallRva<<",\"DR6\":"<<c.Dr6<<",\"qpc\":"<<qpc.QuadPart
    <<",\"registers\":{\"rbx\":"<<c.Rbx<<",\"rcx\":"<<c.Rcx<<",\"rax\":"<<c.Rax
    <<",\"rdx\":"<<c.Rdx<<",\"r8\":"<<c.R8<<",\"r9\":"<<c.R9<<",\"rsp\":"<<c.Rsp<<"}"
    <<",\"reads\":{\"job_plus38_first\":"<<job1<<",\"job_plus38_second\":"<<job2
    <<",\"dispatch_vptr_first\":"<<vptr1<<",\"dispatch_vptr_second\":"<<vptr2
    <<",\"vtable_plus10_first\":"<<target1<<",\"vtable_plus10_second\":"<<target2<<"}"
    <<",\"first_read_complete\":"<<(first?"true":"false")<<",\"second_read_complete\":"<<(second?"true":"false")
    <<",\"source_anchor_matches\":"<<(source?"true":"false")<<",\"owner_identity_stable\":"<<(owner?"true":"false")
    <<",\"target_same_image\":"<<(same_image?"true":"false")<<",\"target_rva\":"<<(same_image?std::to_string(target1-x.base):"null")
    <<",\"clock\":{\"read_complete\":"<<(clock1&&clock2?"true":"false")<<",\"state_before\":"<<state1<<",\"state_after\":"<<state2
    <<",\"date_before\":"<<date1<<",\"date_after\":"<<date2<<",\"day_before\":"<<day1<<",\"day_after\":"<<day2<<"}"
    <<",\"physical_dispatch_source_qualified\":"<<(qualified?"true":"false")
    <<",\"payer\":null,\"calendar_producer\":null,\"cadence\":null,\"paid_maintenance_raw\":null}\n";o.flush();
  return qualified;
}
int DispatchProbe(Config x) {
  if(x.fixture||!x.ordinary_null||x.timeout<500||x.timeout>30000||!x.pid||!x.created||
      !x.character||!x.secondary||x.character>0x7ffffffff000ULL||x.secondary>0x7ffffffff000ULL||
      !x.game_state||!x.full_id||std::filesystem::exists(x.raw)||std::filesystem::exists(x.ready))return 2;
  HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ|PROCESS_CREATE_THREAD,FALSE,x.pid);
  if(!process)return 2;
  BOOL debugger=FALSE;std::array<wchar_t,32768> image{};DWORD chars=DWORD(image.size());
  const bool image_ok=QueryFullProcessImageNameW(process,0,image.data(),&chars)&&
      _wcsicmp(std::filesystem::path(std::wstring(image.data(),chars)).filename().c_str(),L"ck3.exe")==0&&
      ExactActual4Anchor(process,x.pid,x.base,x.module_size);
  if(!image_ok||Created(process)!=x.created||!Identity(process,x)||!DispatchSource(process,x)||
      !CheckRemoteDebuggerPresent(process,&debugger)||debugger||!PreflightDebugFree(x.pid)){CloseHandle(process);return 2;}
  std::ofstream output(x.raw,std::ios::binary);if(!output){CloseHandle(process);return 2;}
  output<<"{\"kind\":\"start\",\"schema\":\"xar.maintenance.dispatch_call.v1\",\"mode\":\"single_pre_call_execution_breakpoint\",\"machine_id\":\""<<x.machine
    <<"\",\"pid\":"<<x.pid<<",\"created\":"<<x.created<<",\"module_base\":"<<x.base<<",\"module_size\":"<<x.module_size
    <<",\"callsite_rva\":"<<kDispatchCallRva<<",\"source_sha256\":\""<<kDispatchSourceSha<<"\",\"source_cash_sha256\":\""<<x.packet_sha<<"\",\"owner_binding\":"<<OwnerJson(x)
    <<",\"maximum_records\":1,\"DR7_execution_mask\":1,\"job_is_payer\":false}\n";output.flush();
  bool attached=DebugActiveProcess(x.pid)!=FALSE,kill_off=false,cleared=false,detached=false,exited=false,pending=false,ready=false;
  DEBUG_EVENT event{};DWORD pending_disposition=DBG_CONTINUE;std::string reason=attached?"none":"attach_failed";
  std::map<DWORD,HANDLE> threads;std::set<DWORD> armed;std::map<DWORD,unsigned> generations;
  unsigned captures=0;bool capture_qualified=false,admission_complete=true;
  SetConsoleCtrlHandler(OnConsoleControl,TRUE);
  if(attached){kill_off=DebugSetProcessKillOnExit(FALSE)!=FALSE;if(!kill_off)reason="kill_on_exit_disable_failed";}
  auto restore_all=[&](){bool ok=ClearAll(threads,armed);for(DWORD tid:armed){auto it=threads.find(tid);if(it==threads.end())continue;CONTEXT c{};const bool got=GetContext(it->second,c);output<<"{\"kind\":\"restore\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"readback\":"<<(got?"true":"false")<<",\"debug\":";DrJson(output,c);output<<"}\n";}output.flush();return ok;};
  auto arm=[&](DWORD tid,HANDLE borrowed){
    if(!Identity(process,x)||threads.size()>=256||!BeginThreadOwnership(tid,threads,armed))return false;
    HANDLE thread=nullptr;if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&thread,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
    threads[tid]=thread;++generations[tid];const bool ok=ArmDispatchThread(thread,x.base+kDispatchCallRva);
    if(g_saved_debug.contains(tid))armed.insert(tid);CONTEXT c{};GetContext(thread,c);
    output<<"{\"kind\":\"arm\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<generations[tid]<<",\"success\":"<<(ok?"true":"false")<<",\"saved_debug\":[";
    auto saved=g_saved_debug.find(tid);if(saved!=g_saved_debug.end())for(unsigned i=0;i<6;++i){if(i)output<<',';output<<saved->second[i];}
    output<<"],\"armed_debug\":";DrJson(output,c);output<<"}\n";output.flush();return ok;};
  auto owned_execution_event=[&](const DEBUG_EVENT &e){
    if(e.dwDebugEventCode!=EXCEPTION_DEBUG_EVENT||e.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_SINGLE_STEP)return false;
    auto it=threads.find(e.dwThreadId);CONTEXT c{};
    return it!=threads.end()&&armed.contains(e.dwThreadId)&&GetContext(it->second,c)&&
      (c.Dr6&15)==1&&!(c.Dr6&0xe000)&&c.Rip==x.base+kDispatchCallRva&&c.Dr0==c.Rip&&
      !c.Dr1&&!c.Dr2&&!c.Dr3&&(c.Dr7&0xffff00ffULL)==1;
  };
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(x.timeout);
  try{while(attached&&kill_off&&reason=="none"){
    if(g_stop_requested.load()){reason="cancel";break;}
    if(std::chrono::steady_clock::now()>=deadline){reason="timeout";break;}
    event={};if(!WaitForDebugEvent(&event,kWaitSliceMs)){if(GetLastError()==ERROR_SEM_TIMEOUT)continue;reason="wait_failed";break;}
    pending=true;DWORD disposition=DBG_CONTINUE;
    switch(event.dwDebugEventCode){
      case CREATE_PROCESS_DEBUG_EVENT:if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);if(!arm(event.dwThreadId,event.u.CreateProcessInfo.hThread)){admission_complete=false;reason="cannot_arm_existing_thread";}break;
      case CREATE_THREAD_DEBUG_EVENT:if(!arm(event.dwThreadId,event.u.CreateThread.hThread)){admission_complete=false;reason="cannot_arm_new_thread";}break;
      case EXIT_THREAD_DEBUG_EVENT:{auto it=threads.find(event.dwThreadId);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}armed.erase(event.dwThreadId);g_saved_debug.erase(event.dwThreadId);output<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<"}\n";break;}
      case LOAD_DLL_DEBUG_EVENT:if(event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);break;
      case EXIT_PROCESS_DEBUG_EVENT:exited=true;reason="process_exited";break;
      case EXCEPTION_DEBUG_EVENT:{const DWORD code=event.u.Exception.ExceptionRecord.ExceptionCode;
        if(code==EXCEPTION_BREAKPOINT&&!ready){ready=!armed.empty();if(ready){std::ofstream f(x.ready);f<<"{\"ready\":true,\"mode\":\"single_pre_call_execution_breakpoint\",\"armed_thread_count\":"<<armed.size()<<"}\n";f.flush();ready=f.good();}if(!ready)reason="ready_failed";break;}
        if(code!=EXCEPTION_SINGLE_STEP){disposition=DBG_EXCEPTION_NOT_HANDLED;reason="unexpected_exception";break;}
        auto it=threads.find(event.dwThreadId);CONTEXT c{};
        if(it==threads.end()||!armed.contains(event.dwThreadId)||!GetContext(it->second,c)||
            (c.Dr6&15)!=1||(c.Dr6&0xe000)||c.Rip!=x.base+kDispatchCallRva||c.Dr0!=c.Rip||
            c.Dr1||c.Dr2||c.Dr3||(c.Dr7&0xffff00ffULL)!=1){disposition=DBG_EXCEPTION_NOT_HANDLED;reason="unrelated_execution_exception";break;}
        ++captures;capture_qualified=CaptureDispatch(output,process,x,c,event.dwThreadId,generations[event.dwThreadId]);
        reason=capture_qualified?"complete":"capture_incomplete";
        // This is a PRE-instruction fault. Do not rewind RIP, set TF, emulate
        // CALL, read a guessed return slot, or skip the original instruction.
        // Restore all owned DR vectors while this debug event remains pending;
        // only then continue the actual CALL at the unchanged original RIP.
        break;}
      default:break;
    }
    if(reason!="none"){cleared=restore_all();if(!cleared){reason="restore_failed_pending_retained";break;}}
    pending_disposition=disposition;pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)==FALSE;
    if(pending){reason="continue_failed";break;}
  }}catch(...){reason="observer_throw";}
  // Same finite stop/restore/detach ownership as the original writer, without
  // treating suspend fallback alone as an independently witnessed restore.
  if(attached&&!exited&&!pending&&!cleared&&!armed.empty()){
    if(DebugBreakProcess(process)){
      const auto end=std::chrono::steady_clock::now()+std::chrono::milliseconds(kBreakCleanupWaitMs);
      while(std::chrono::steady_clock::now()<end){event={};if(!WaitForDebugEvent(&event,kWaitSliceMs))continue;pending=true;
        if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT){HANDLE h=nullptr;if(DuplicateHandle(GetCurrentProcess(),event.u.CreateThread.hThread,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))threads[event.dwThreadId]=h;else reason="cleanup_duplicate_failed";}
        if(event.dwDebugEventCode==EXIT_THREAD_DEBUG_EVENT){auto it=threads.find(event.dwThreadId);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}const bool was_armed=armed.erase(event.dwThreadId)!=0;g_saved_debug.erase(event.dwThreadId);if(was_armed)output<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<"}\n";}
        if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT&&event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
        if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT)exited=true;
        const bool owned=owned_execution_event(event);
        const bool stop=owned||(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode==EXCEPTION_BREAKPOINT);
        if(stop||exited)cleared=exited||restore_all();
        const DWORD d=event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_BREAKPOINT&&!owned?DBG_EXCEPTION_NOT_HANDLED:DBG_CONTINUE;
        pending_disposition=d;if(stop&&!cleared)break;
        pending=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,d)==FALSE;if(pending){reason="cleanup_continue_failed";break;}if(cleared)break;
      }
    }
    if(!cleared&&!exited)(void)SuspendAndClearAll(threads,armed); // remains unqualified without stopped readback rows.
  }
  if(pending&&!exited){cleared=restore_all();if(cleared&&ContinueDebugEvent(event.dwProcessId,event.dwThreadId,pending_disposition))pending=false;}
  if(armed.empty())cleared=true;
  if(attached&&!exited&&cleared&&!pending)detached=DebugActiveProcessStop(x.pid)!=FALSE;else if(exited)detached=true;
  // A failed OS restoration cannot be made finite by abandoning an armed
  // execution fault. Retain the original Popen/debug ownership, publish an
  // honest hold, and retry only idempotent restoration/readback/continuation.
  // This is NOT a cleanup success or an extension of capture/advancement.
  if(attached&&!exited&&(!cleared||pending||!detached)){
    output<<"{\"kind\":\"unresolved_cleanup_hold\",\"Popen_must_remain_retained\":true,\"cleanup_complete\":false,\"no_more_capture\":true}\n";output.flush();
    while(!exited&&(!cleared||pending||!detached)){
      if(WaitForSingleObject(process,0)==WAIT_OBJECT_0){exited=true;break;}
      if(pending){cleared=restore_all();if(cleared&&ContinueDebugEvent(event.dwProcessId,event.dwThreadId,pending_disposition))pending=false;}
      if(cleared&&!pending)detached=DebugActiveProcessStop(x.pid)!=FALSE;
      if(!cleared&&!pending){
        // No unsafe detach: request the same finite debugger stop again.
        if(DebugBreakProcess(process)&&WaitForDebugEvent(&event,kWaitSliceMs)){
          pending=true;const bool owned=owned_execution_event(event);
          if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT){HANDLE h=nullptr;if(DuplicateHandle(GetCurrentProcess(),event.u.CreateThread.hThread,GetCurrentProcess(),&h,0,FALSE,DUPLICATE_SAME_ACCESS))threads[event.dwThreadId]=h;}
          if(event.dwDebugEventCode==EXIT_THREAD_DEBUG_EVENT){auto it=threads.find(event.dwThreadId);if(it!=threads.end()){CloseHandle(it->second);threads.erase(it);}const bool was_armed=armed.erase(event.dwThreadId)!=0;g_saved_debug.erase(event.dwThreadId);if(was_armed)output<<"{\"kind\":\"thread_exited\",\"thread_id\":"<<event.dwThreadId<<",\"thread_generation\":"<<generations[event.dwThreadId]<<"}\n";}
          if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT&&event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
          if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT)exited=true;
          pending_disposition=event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT&&event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_BREAKPOINT&&!owned?DBG_EXCEPTION_NOT_HANDLED:DBG_CONTINUE;
        }
      }
      if(!detached)Sleep(kWaitSliceMs);
    }
  }
  if(pending)reason="pending_event_unresolved";
  for(auto [tid,h]:threads){(void)tid;if(h)CloseHandle(h);}
  const bool clean=cleared&&detached&&!pending&&!exited;
  output<<"{\"kind\":\"terminal\",\"reason\":\""<<reason<<"\",\"restored\":"<<(cleared?"true":"false")<<",\"detached\":"<<(detached?"true":"false")<<",\"pending_event\":"<<(pending?"true":"false")<<",\"process_exited\":"<<(exited?"true":"false")<<",\"cleanup_complete\":"<<(clean?"true":"false")<<",\"observation_thread_admission_complete\":"<<(admission_complete?"true":"false")<<",\"capture_count\":"<<captures<<",\"known_payer_or_cadence\":false}\n";output.flush();
  CloseHandle(process);SetConsoleCtrlHandler(OnConsoleControl,FALSE);return clean&&capture_qualified&&reason=="complete"?0:1;
}
int DispatchMain(int argc,wchar_t **argv) {
  if(argc!=13||std::wstring(argv[2])!=L"--admission-meta"||std::wstring(argv[4])!=L"--timeout-ms"||std::wstring(argv[6])!=L"--raw"||std::wstring(argv[8])!=L"--ready"||std::wstring(argv[10])!=L"--machine-id"||std::wstring(argv[12])!=L"--explicit-execution-breakpoint-v1")return 2;
  try{
    std::ifstream input{std::filesystem::path(argv[3])};std::map<std::string,std::string> meta;std::string line;
    while(std::getline(input,line)){const auto p=line.find('=');if(p==std::string::npos||!meta.emplace(line.substr(0,p),line.substr(p+1)).second)return 2;}
    auto v=[&](const char *key){const auto &s=meta.at(key);if(s.empty()||s.front()=='-')throw std::invalid_argument("unsigned admission required");std::size_t used=0;const auto n=std::stoull(s,&used,0);if(used!=s.size())throw std::invalid_argument("metadata suffix");return n;};
    if(meta.at("dispatch_schema")!="xar.maintenance.dispatch_call.admission.v1"||meta.at("dispatch_source_sha256")!=kDispatchSourceSha||v("dispatch_callsite_rva")!=kDispatchCallRva||v("dispatch_maximum_records")!=1||v("explicit_execution_breakpoint")!=1||v("r06_probe_concurrent")!=0||meta.at("qualified_exe_sha256")!="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"||meta.at("game_version")!="1.20.0.4"||v("steam_build_id")!=25734779||meta.at("owner_binding_schema")!="xar.maintenance.writer_pc.owner-binding.v2"||meta.at("owner_binding_mode")!="native_campaign_owned_no_load_v2"||meta.at("episode_projection")!="native_campaign"||v("episode_is_null")!=1||!meta.at("episode_id").empty())return 2;
    Config x;x.fixture=false;x.ordinary_null=true;
    const auto pid=v("pid"),id=v("full_id"),timeout=std::stoull(argv[5]);if(pid>0xffffffffULL||id>=0xffffffffULL||timeout<500||timeout>30000)return 2;
    x.pid=DWORD(pid);x.full_id=std::uint32_t(id);x.created=v("created");x.character=v("character");x.secondary=v("context");x.game_state=v("game_state_identity_witness");x.local_player=v("local_player_id");x.absolute_day=v("absolute_day_raw");x.window=v("controlled_window_id");x.epoch=v("payment_epoch");x.generation=v("connection_generation");x.revision=v("native_revision");x.admission_date=std::stoll(meta.at("date_raw"));
    const auto present=v("original_episode_key_present");if(!x.window||!x.epoch||!x.generation||!x.revision||!x.local_player||x.local_player>0xffffffffULL||x.game_state>0x7ffffffff000ULL||x.absolute_day>=0xffffffffULL||present>1||x.admission_date<0||static_cast<std::uint64_t>(x.admission_date)>=0xffffffffULL-24)return 2;
    x.episode_key_present=present!=0;x.timeout=DWORD(timeout);x.raw=argv[7];x.ready=argv[9];const std::wstring machine=argv[11];if(machine.empty()||machine.find_first_not_of(L"abcdefghijklmnopqrstuvwxyz0123456789-")!=std::wstring::npos)return 2;x.machine.assign(machine.begin(),machine.end());
    x.packet_sha=meta.at("source_cash_sha256");if(x.packet_sha.size()!=64||x.packet_sha.find_first_not_of("0123456789abcdef")!=std::string::npos)return 2;
    return DispatchProbe(x);
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 2;}
}
