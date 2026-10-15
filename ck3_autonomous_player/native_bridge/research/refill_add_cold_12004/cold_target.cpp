#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>

extern "C" void SyntheticAdd(void*,std::uint32_t,std::uint64_t);
extern "C" unsigned char SyntheticBefore,SyntheticAfter;
extern "C" { volatile LONG g_AddExecutedCount=0; }
namespace {
constexpr std::uint32_t kRegi=0x11000001,kArRg=0x12000001,kArmy=0x13000001;
alignas(16) std::array<std::uint8_t,0x180> regi{},worker_regi{},arrg{},army{};
std::array<std::uint8_t,0x40> arrg_registry{},army_registry{};
std::array<std::uintptr_t,4> arrg_table{},army_table{};
void *arrg_storage=arrg_registry.data(),*army_storage=army_registry.data();
std::array<std::array<std::uint32_t,4>,2> data{};
HANDLE go_event=nullptr,audit_event=nullptr,finish_event=nullptr,main_thread=nullptr,initial_done=nullptr;
std::filesystem::path prefix;
std::uint64_t Created() {FILETIME c{},e{},k{},u{};GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u);ULARGE_INTEGER v{};v.LowPart=c.dwLowDateTime;v.HighPart=c.dwHighDateTime;return v.QuadPart;}
template<class T> void Put(auto &object,std::size_t offset,T v){std::memcpy(object.data()+offset,&v,sizeof v);}
std::filesystem::path File(const wchar_t *suffix){return prefix.wstring()+suffix;}
bool Audit(const wchar_t *suffix) {
  if(SuspendThread(main_thread)==DWORD(-1))return false;
  CONTEXT c{};c.ContextFlags=CONTEXT_DEBUG_REGISTERS;
  bool ok=GetThreadContext(main_thread,&c)!=FALSE;
  if(ResumeThread(main_thread)==DWORD(-1))ok=false;
  std::ofstream o(File(suffix));o<<"{\"ok\":"<<(ok?"true":"false")<<",\"thread_id\":"<<GetThreadId(main_thread)
    <<",\"Dr0\":"<<c.Dr0<<",\"Dr1\":"<<c.Dr1<<",\"Dr2\":"<<c.Dr2<<",\"Dr3\":"<<c.Dr3
    <<",\"Dr6\":"<<c.Dr6<<",\"Dr7\":"<<c.Dr7<<"}\n";return ok&&o.good();
}
DWORD WINAPI Auditor(void*) {
  if(!Audit(L".initial-debug.json"))return 1;
  SetEvent(initial_done);
  if(WaitForSingleObject(audit_event,30000)!=WAIT_OBJECT_0)return 2;
  return Audit(L".after-debug.json")?0:3;
}
DWORD WINAPI OtherThread(void*){SyntheticAdd(worker_regi.data(),1,0);return 0;}
}
int wmain(int argc,wchar_t **argv) {
  if(argc!=5||std::wstring(argv[1])!=L"--mode"||std::wstring(argv[3])!=L"--prefix")return 2;
  const std::wstring mode=argv[2];prefix=argv[4];
  const bool wrap=mode==L"wrap",negative=mode==L"negative",zero=mode==L"zero";
  const auto before=wrap?0xFFFFFFFFU:negative?0U:80U;
  const auto q=wrap?1U:negative?0xFFFFFFFFU:zero?0U:10U;
  for(unsigned i=0;i<7;++i){const auto offset=0x18+i*0x24;
    Put(regi,offset,std::uint32_t(100));Put(regi,offset+4,before);Put(regi,offset+8,kRegi);
    Put(regi,offset+0xC,std::uint32_t(i));Put(regi,offset+0x10,std::int32_t(-1));}
  Put(regi,0x10,kRegi);Put(regi,0x14,std::uint32_t(0x52656769));
  Put(regi,0x28,kArRg);worker_regi=regi;Put(worker_regi,0x10,kRegi+1);
  Put(arrg,0x10,kArRg);Put(arrg,0x14,std::uint32_t(0x41725267));
  data[0]={0,0,kRegi,0};data[1]=data[0];Put(arrg,0x20,reinterpret_cast<std::uintptr_t>(data.data()));
  Put(arrg,0x2C,std::int32_t(2));Put(arrg,0x140,kArmy);
  Put(army,0x10,kArmy);Put(army,0x14,std::uint32_t(0x41726D79));
  arrg_table[3]=reinterpret_cast<std::uintptr_t>(arrg.data());army_table[3]=reinterpret_cast<std::uintptr_t>(army.data());
  Put(arrg_registry,0x20,reinterpret_cast<std::uintptr_t>(arrg_table.data()));Put(arrg_registry,0x2C,std::uint32_t(2));
  Put(army_registry,0x20,reinterpret_cast<std::uintptr_t>(army_table.data()));Put(army_registry,0x2C,std::uint32_t(2));
  const auto name=L"Local\\XarRefillCold"+std::to_wstring(GetCurrentProcessId());
  go_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Go").c_str());
  audit_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Audit").c_str());
  finish_event=CreateEventW(nullptr,TRUE,FALSE,(name+L"Finish").c_str());initial_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);
  main_thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_LIMITED_INFORMATION,FALSE,GetCurrentThreadId());
  if(!go_event||!audit_event||!finish_event||!initial_done||!main_thread)return 3;
  HANDLE auditor=CreateThread(nullptr,0,Auditor,nullptr,0,nullptr);
  if(!auditor||WaitForSingleObject(initial_done,5000)!=WAIT_OBJECT_0)return 4;
  std::ofstream meta(File(L".meta.txt"));
  meta<<"pid="<<GetCurrentProcessId()<<"\ntid="<<GetCurrentThreadId()<<"\ncreated="<<Created()
    <<"\nmodule_base="<<reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))
    <<"\nsite0="<<reinterpret_cast<std::uintptr_t>(&SyntheticBefore)<<"\nsite1="<<reinterpret_cast<std::uintptr_t>(&SyntheticAfter)
    <<"\nregiment="<<kRegi<<"\nslot=0\narrg_registry_slot="<<reinterpret_cast<std::uintptr_t>(&arrg_storage)
    <<"\narmy_registry_slot="<<reinterpret_cast<std::uintptr_t>(&army_storage)<<"\nq="<<q<<"\nbefore="<<before
    <<"\ngo_event="<<std::string(name.begin(),name.end())<<"Go\naudit_event="<<std::string(name.begin(),name.end())
    <<"Audit\nfinish_event="<<std::string(name.begin(),name.end())<<"Finish\n";meta.close();
  if(WaitForSingleObject(go_event,30000)!=WAIT_OBJECT_0)return 5;
  if(mode==L"exit-before-add")return 0;
  unsigned worker_count=0;
  if(mode==L"other-thread") {HANDLE worker=CreateThread(nullptr,0,OtherThread,nullptr,0,nullptr);if(!worker)return 6;
    const DWORD wait=WaitForSingleObject(worker,5000);DWORD worker_exit=STILL_ACTIVE;const BOOL exited=GetExitCodeThread(worker,&worker_exit);CloseHandle(worker);worker_count=unsigned(g_AddExecutedCount);if(wait!=WAIT_OBJECT_0||!exited||worker_exit!=0||worker_count!=1)return 6;InterlockedExchange(&g_AddExecutedCount,0);}
  const unsigned count=mode==L"finite-hit"?16U:1U;
  for(unsigned i=0;i<count;++i)SyntheticAdd(regi.data(),q,0);
  std::uint32_t after=0;std::memcpy(&after,regi.data()+0x1C,4);
  std::ofstream result(File(L".add.json"));result<<"{\"synthetic\":true,\"before_u32\":"<<before<<",\"q_u32\":"<<q
    <<",\"after_u32\":"<<after<<",\"main_ADD_execution_count\":"<<g_AddExecutedCount<<",\"worker_ADD_execution_count\":"<<worker_count<<"}\n";result.close();
  if(WaitForSingleObject(finish_event,30000)!=WAIT_OBJECT_0)return 7;
  WaitForSingleObject(auditor,5000);CloseHandle(auditor);
  for(HANDLE h:{go_event,audit_event,finish_event,main_thread,initial_done})CloseHandle(h);
  return 0;
}
