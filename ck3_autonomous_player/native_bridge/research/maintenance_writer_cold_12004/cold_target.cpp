#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
extern "C" void SyntheticWrite(void*,std::uint64_t);
extern "C" unsigned char SyntheticWriteStart,SyntheticWriteAfter;
namespace {
alignas(16) std::array<std::uint8_t,0x300> character{},context{},other_context{};
constexpr std::array<unsigned,4> offsets{0x2c0,0x2c8,0x28,0x30};
std::array<std::uint64_t,4> initial{500974,0,218610,0};
std::filesystem::path prefix;std::wstring mode;
HANDLE go_event=nullptr,audit_event=nullptr,finish_event=nullptr,initial_done=nullptr,worker_written=nullptr,main_thread=nullptr,worker_thread=nullptr;
DWORD main_tid=0,worker_tid=0;volatile LONG writes=0;
std::filesystem::path File(const wchar_t*s){return prefix.wstring()+s;}
template<class T>void Put(auto&o,unsigned offset,T value){std::memcpy(o.data()+offset,&value,sizeof value);}
bool AuditThread(std::ofstream&o,HANDLE thread,DWORD tid){if(SuspendThread(thread)==DWORD(-1))return false;CONTEXT c{};c.ContextFlags=CONTEXT_DEBUG_REGISTERS;bool ok=GetThreadContext(thread,&c)!=FALSE;if(ResumeThread(thread)==DWORD(-1))ok=false;o<<"{\"thread_id\":"<<tid<<",\"ok\":"<<(ok?"true":"false")<<",\"debug\":["<<c.Dr0<<","<<c.Dr1<<","<<c.Dr2<<","<<c.Dr3<<","<<c.Dr6<<","<<c.Dr7<<"]}";return ok;}
DWORD WINAPI Auditor(void*){
  if(mode==L"stale-tid-occupied"){
    if(SuspendThread(main_thread)==DWORD(-1))return 10;
    CONTEXT occupied{};occupied.ContextFlags=CONTEXT_DEBUG_REGISTERS;
    bool ok=GetThreadContext(main_thread,&occupied)!=FALSE;
    occupied.Dr0=0x12345000;occupied.Dr7=(occupied.Dr7&~0x3ULL)|1ULL;
    if(ok)ok=SetThreadContext(main_thread,&occupied)!=FALSE;
    CONTEXT actual{};actual.ContextFlags=CONTEXT_DEBUG_REGISTERS;
    if(ok)ok=GetThreadContext(main_thread,&actual)!=FALSE&&actual.Dr0==0x12345000&&(actual.Dr7&3)==1;
    std::ofstream seed(File(L".occupied-seed-readback.json"));seed<<"{\"api_and_readback_ok\":"<<(ok?"true":"false")<<",\"Dr0\":"<<actual.Dr0<<",\"Dr7\":"<<actual.Dr7<<"}\n";
    if(ResumeThread(main_thread)==DWORD(-1))ok=false;
    if(!ok)return 11;
  }
  std::ofstream initial_out(File(L".initial-debug.json"));initial_out<<"[";bool ok=AuditThread(initial_out,main_thread,main_tid);initial_out<<"]\n";initial_out.close();SetEvent(initial_done);if(!ok||WaitForSingleObject(audit_event,30000)!=WAIT_OBJECT_0)return 1;std::ofstream after(File(L".after-debug.json"));after<<"[";ok=AuditThread(after,main_thread,main_tid);if(worker_thread){after<<",";ok=AuditThread(after,worker_thread,worker_tid)&&ok;}after<<"]\n";return ok?0:2;}
void WriteFields(){for(unsigned i=0;i<4;++i){SyntheticWrite(context.data()+offsets[i],mode==L"same-value"?initial[i]:initial[i]+10+i);InterlockedIncrement(&writes);}}
DWORD WINAPI Worker(void*){WriteFields();SetEvent(worker_written);return WaitForSingleObject(finish_event,30000)==WAIT_OBJECT_0?0:1;}
std::uint64_t Created(){FILETIME c{},e{},k{},u{};GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u);ULARGE_INTEGER v{};v.LowPart=c.dwLowDateTime;v.HighPart=c.dwHighDateTime;return v.QuadPart;}
}
int wmain(int argc,wchar_t**argv){if(argc!=5||std::wstring(argv[1])!=L"--mode"||std::wstring(argv[3])!=L"--prefix")return 2;mode=argv[2];prefix=argv[4];main_tid=GetCurrentThreadId();for(unsigned i=0;i<4;++i)Put(context,offsets[i],initial[i]);Put(character,0x18,std::uint32_t(31254));Put(character,0x1c,std::uint32_t(0x43686172));Put(character,0x1c0,reinterpret_cast<std::uintptr_t>(context.data()));
  auto name=L"Local\\XarMaintenanceWriter"+std::to_wstring(GetCurrentProcessId());go_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Go").c_str());audit_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Audit").c_str());finish_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Finish").c_str());initial_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);worker_written=CreateEventW(nullptr,TRUE,FALSE,nullptr);main_thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_LIMITED_INFORMATION,FALSE,main_tid);if(!go_event||!audit_event||!finish_event||!initial_done||!worker_written||!main_thread)return 3;HANDLE auditor=CreateThread(nullptr,0,Auditor,nullptr,0,nullptr);if(!auditor||WaitForSingleObject(initial_done,5000)!=WAIT_OBJECT_0)return 4;
  auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+dos->e_lfanew);
  std::ofstream meta(File(L".meta.txt"));meta<<"pid="<<GetCurrentProcessId()<<"\ntid="<<main_tid<<"\ncreated="<<Created()<<"\nfull_id=31254\ncharacter="<<reinterpret_cast<std::uintptr_t>(character.data())<<"\ncontext="<<reinterpret_cast<std::uintptr_t>(context.data())<<"\ncold_stale_tid_guard="<<(mode==L"stale-tid-occupied"?1:0)<<"\nmodule_base="<<base<<"\nmodule_size="<<nt->OptionalHeader.SizeOfImage<<"\nwriter_start="<<reinterpret_cast<std::uintptr_t>(&SyntheticWriteStart)<<"\nwriter_after="<<reinterpret_cast<std::uintptr_t>(&SyntheticWriteAfter)<<"\ngo_event="<<std::string(name.begin(),name.end())<<"Go\naudit_event="<<std::string(name.begin(),name.end())<<"Audit\nfinish_event="<<std::string(name.begin(),name.end())<<"Finish\n";meta.close();if(WaitForSingleObject(go_event,30000)!=WAIT_OBJECT_0)return 5;
  if(mode==L"changed-context")Put(character,0x1c0,reinterpret_cast<std::uintptr_t>(other_context.data()));
  if(mode!=L"timeout"&&mode!=L"default-off"){
    if(mode==L"new-worker"){worker_thread=CreateThread(nullptr,0,Worker,nullptr,0,&worker_tid);if(!worker_thread||WaitForSingleObject(worker_written,10000)!=WAIT_OBJECT_0)return 6;}
    else WriteFields();
  }
  std::ofstream result(File(L".writes.json"));result<<"{\"synthetic\":true,\"actual_store_count\":"<<writes<<",\"main_tid\":"<<main_tid<<",\"worker_tid\":"<<worker_tid<<",\"values\":[";for(unsigned i=0;i<4;++i){std::uint64_t v=0;std::memcpy(&v,context.data()+offsets[i],8);if(i)result<<',';result<<v;}result<<"]}\n";result.close();if(WaitForSingleObject(finish_event,30000)!=WAIT_OBJECT_0)return 7;WaitForSingleObject(auditor,5000);CloseHandle(auditor);if(worker_thread){if(WaitForSingleObject(worker_thread,5000)!=WAIT_OBJECT_0)return 8;CloseHandle(worker_thread);}for(HANDLE h:{go_event,audit_event,finish_event,initial_done,worker_written,main_thread})CloseHandle(h);return 0;}
