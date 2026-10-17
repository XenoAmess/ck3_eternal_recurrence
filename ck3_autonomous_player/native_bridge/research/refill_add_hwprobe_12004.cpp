// Candidate actual CK3 1.20.0.4 physical ADD hardware observer. DEFAULT OFF.
// Source-derived from war31_two_point_hwprobe.cpp; no injected target callback,
// target code/data write, instruction emulation, or target XSTATE modification.
// Shared debugger lifecycle has synthetic cold qualification; this production
// executable still requires its own frozen build/SYSTEM gate and Root live plan.
#ifndef XAR_ENABLE_REFILL_ADD_HWPROBE_12004
#define XAR_ENABLE_REFILL_ADD_HWPROBE_12004 0
#endif
// Hardware execute breakpoints change debugger/thread context, but never patch
// CK3 code or submit a gameplay action. Do not run without a coordinated,
// independently authorized action and an isolated attempt directory.
#include <windows.h>
#include <tlhelp32.h>

#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include "refill_add_live_12004/refill_stack_q_source_12004.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#if defined(XAR_REFILL_V3_COLD_BUILD) && XAR_ENABLE_REFILL_ADD_HWPROBE_12004
#error The cold adapter cannot enable the production CLI
#endif
namespace {

constexpr std::array<DWORD64, 2> kSiteRvas{0x2A98B88, 0x2A98B8B};
DWORD g_expected_tid=0;
std::array<std::uint8_t,3> g_verified_pre{};
std::array<std::uint8_t,6> g_verified_post{};
std::map<DWORD,std::array<DWORD64,6>> g_saved_debug;
std::uint32_t g_expected_regiment=0;
unsigned g_expected_slot=7;
std::uint64_t g_expected_created=0;
std::string g_machine;
std::uint64_t g_debug_hits=0;
constexpr std::array<std::uint8_t, 3> kSetupBytes{0x01,0x50,0xF4};
constexpr std::array<std::uint8_t, 6> kResolveBytes{0x8B,0x48,0xF4,0x3B,0x48,0xF0};
#if defined(XAR_REFILL_V3_COLD_BUILD)
DWORD64 g_fixture_base=0,g_fixture_arrg_slot=0,g_fixture_army_slot=0;
std::array<DWORD64,2> g_fixture_sites{};
std::uint64_t g_fixture_hit_limit=100000;
constexpr const char *kRawSchema="xar.ck3.refill_ADD_12004.shared_probe_cold.v1";
constexpr const char *kReadySchema="xar.ck3.refill_ADD_12004.shared_probe_cold_ready.v1";
constexpr const char *kSiteKey="synthetic_site_address";
constexpr const char *kBudgetKind="fixture_debug_budget";
std::uint64_t DebugHitLimit12004(){return g_fixture_hit_limit;}
DWORD64 HitSite12004(int site){return g_fixture_sites[site];}
#else
constexpr const char *kRawSchema="xar.ck3.refill_ADD_12004.hwprobe_raw.v3";
constexpr const char *kReadySchema="xar.ck3.refill_ADD_12004.hwprobe_ready.v2";
constexpr const char *kSiteKey="site_rva";
constexpr const char *kBudgetKind="debug_hit_budget";
constexpr std::uint64_t DebugHitLimit12004(){return 100000;}
DWORD64 HitSite12004(int site){return kSiteRvas[site];}
#endif
constexpr DWORD kResumeFlag = 0x10000;
constexpr DWORD kWaitSliceMs = 100;
constexpr DWORD kBreakCleanupWaitMs = 5000;
std::atomic<bool> g_stop_requested{false};

BOOL WINAPI OnConsoleControl(DWORD control) {
  if (control == CTRL_C_EVENT || control == CTRL_BREAK_EVENT ||
      control == CTRL_CLOSE_EVENT) {
    g_stop_requested.store(true, std::memory_order_release);
    return TRUE;
  }
  return FALSE;
}

std::string Hex(std::uint64_t value) {
  std::ostringstream stream;
  stream << "0x" << std::uppercase << std::hex << value;
  return stream.str();
}

bool ReadExact(HANDLE process, DWORD64 address, void *dest, std::size_t size) {
  SIZE_T read = 0;
  return address != 0 && ReadProcessMemory(
      process, reinterpret_cast<const void *>(address), dest, size, &read) &&
      read == size;
}

bool ExactAnchorsAt(HANDLE process, const std::array<DWORD64, 2> &sites) {
  std::array<std::uint8_t, kSetupBytes.size()> setup{};
  std::array<std::uint8_t, kResolveBytes.size()> resolve{};
  if (!ReadExact(process, sites[0], setup.data(), setup.size()) ||
      !ReadExact(process, sites[1], resolve.data(), resolve.size()) ||
      setup != kSetupBytes || resolve != kResolveBytes) return false;
  g_verified_pre = setup; g_verified_post = resolve; return true;
}

template<std::size_t N> std::string ByteHex(const std::array<std::uint8_t,N> &bytes) {
  constexpr char digits[]="0123456789abcdef"; std::string out; out.reserve(N*2);
  for (auto b:bytes) {out.push_back(digits[b>>4]);out.push_back(digits[b&15]);} return out;
}

DWORD64 ModuleBase(DWORD pid) {
  HANDLE snapshot = CreateToolhelp32Snapshot(
      TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
  if (snapshot == INVALID_HANDLE_VALUE) return 0;
  MODULEENTRY32W entry{};
  entry.dwSize = sizeof(entry);
  DWORD64 base = 0;
  if (Module32FirstW(snapshot, &entry)) {
    do {
      if (_wcsicmp(entry.szModule, L"ck3.exe") == 0) {
        base = reinterpret_cast<DWORD64>(entry.modBaseAddr);
        break;
      }
    } while (Module32NextW(snapshot, &entry));
  }
  CloseHandle(snapshot);
  return base;
}

bool IsCk3Image(HANDLE process) {
  std::array<wchar_t, 32768> path{};
  DWORD size = static_cast<DWORD>(path.size());
  if (!QueryFullProcessImageNameW(process, 0, path.data(), &size)) return false;
  const std::wstring name(path.data(), size);
  const auto slash = name.find_last_of(L"\\/");
  const auto basename = name.substr(slash == std::wstring::npos ? 0 : slash + 1);
  return _wcsicmp(basename.c_str(), L"ck3.exe") == 0;
}

std::uint64_t ProcessCreationTime(HANDLE process) {
  FILETIME created{}, exited{}, kernel{}, user{};
  if (!GetProcessTimes(process, &created, &exited, &kernel, &user)) return 0;
  ULARGE_INTEGER value{};
  value.LowPart = created.dwLowDateTime;
  value.HighPart = created.dwHighDateTime;
  return value.QuadPart;
}

bool GetContext(HANDLE thread, CONTEXT &context) {
  context = CONTEXT{};
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER |
                         CONTEXT_DEBUG_REGISTERS;
  return GetThreadContext(thread, &context) != FALSE;
}

bool ArmThread(HANDLE thread, const std::array<DWORD64, 2> &sites) {
  alignas(16) CONTEXT context{};
  if (!GetContext(thread, context)) return false;
  // Do not overwrite another component's processor breakpoints.
  if (context.Dr0 || context.Dr1 || context.Dr2 || context.Dr3 ||
      (context.Dr7 & (0xFFULL | 0xFFFF0000ULL))) return false;
  if (context.EFlags & 0x100) return false; // Do not take over an existing TF step.
  g_saved_debug[GetThreadId(thread)]={context.Dr0,context.Dr1,context.Dr2,context.Dr3,context.Dr6,context.Dr7};
  context.Dr0 = sites[0];
  context.Dr1 = sites[1];
  context.Dr6 = 0;
  context.Dr7 |= 0x5;  // local execute breakpoints 0 and 1, length 1.
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
    if (item != threads.end()) clean = ClearThread(item->second) && clean;
  }
  return clean;
}

bool SuspendAndClearAll(const std::map<DWORD, HANDLE> &threads,
                        const std::set<DWORD> &armed_tids) {
  bool clean = true;
  for (const DWORD tid : armed_tids) {
    const auto item = threads.find(tid);
    if (item == threads.end()) continue;
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


#include "refill_add_live_12004/debug_thread_ownership_12004.hpp"

struct Hit {
  int site=-1; DWORD tid=0; DWORD64 pointer=0,regi=0,rsp=0,iterator=0;
  std::uint64_t qpc=0,core_caller=0;
  std::uint32_t full_id=0,q_bits=0,current=0,maximum=0;
  std::int32_t q_index=0; unsigned slot=7;
  std::array<std::uint8_t,252> seven{};
  // Fixed stack window passed as [rsp+20,rsp+3C) at 2A98B3A/B3F.
  std::array<std::uint8_t,28> stack_q_window{};
  bool stack_q_source_complete=false;
  std::int32_t arrg_raw=-1,arrg_resolved=-1,army_raw=-1,army_resolved=-1;
  DWORD64 arrg_pointer=0,army_pointer=0;
  bool physical_complete=false,data_complete=false;
  std::int32_t data_count=-1;
  std::vector<std::array<std::uint32_t,4>> data;
};
template<class T> bool Read(HANDLE p,DWORD64 a,T &v) {return ReadExact(p,a,&v,sizeof v);}
DWORD64 Resolve(HANDLE p,DWORD64 base,DWORD64 registry_rva,DWORD64 fallback_rva,
                std::int32_t full,std::int32_t &resolved) {
  DWORD64 registry=0,table=0,object=0;std::uint32_t count=0,id=0;
  DWORD64 registry_slot=base+registry_rva;
#if defined(XAR_REFILL_V3_COLD_BUILD)
  if(registry_rva==0x5D1F340)registry_slot=g_fixture_arrg_slot;
  else if(registry_rva==0x5D1DE48)registry_slot=g_fixture_army_slot;
  else return 0;
#endif
  if(!Read(p,registry_slot,registry))return 0;
  const auto index=std::uint32_t(full)&0xFFFFFF;
  if(registry && Read(p,registry+0x2C,count) && index<count && count<=1000000 &&
      Read(p,registry+0x20,table) && table && Read(p,table+16ULL*index+8,object) &&
      object && Read(p,object+0x10,id) && id==std::uint32_t(full)) {
    resolved=static_cast<std::int32_t>(id);return object;
  }
#if defined(XAR_REFILL_V3_COLD_BUILD)
  return 0; // Synthetic registries do not fall through to game-shaped slots.
#endif
  // Keep actual fallback identity separately; it never becomes exact DATA credit.
  if(!Read(p,base+fallback_rva,object)||!object||!Read(p,object+0x10,id))return 0;
  resolved=static_cast<std::int32_t>(id);return object;
}
Hit ReadHit(HANDLE process,DWORD64 base,int site,DWORD tid,const CONTEXT &c) {
  Hit h;h.site=site;h.tid=tid;h.pointer=c.Rax;h.regi=c.Rsi;h.rsp=c.Rsp;h.iterator=c.Rbx;
  h.q_bits=static_cast<std::uint32_t>(c.Rdx);h.q_index=static_cast<std::int32_t>(c.Rcx);
  LARGE_INTEGER clock{};if(QueryPerformanceCounter(&clock))h.qpc=clock.QuadPart;
  if(!h.regi||h.regi>UINT64_MAX-0x200||h.pointer<h.regi+0x28)return h;
  const auto delta=h.pointer-h.regi-0x28;
  if(delta%0x24||delta/0x24>=7)return h;
  h.slot=static_cast<unsigned>(delta/0x24);
  std::uint32_t magic=0,iterator_id=0;
  if(!Read(process,h.regi+0x10,h.full_id)||!Read(process,h.regi+0x14,magic)||
      magic!=0x52656769||!Read(process,h.iterator,iterator_id)||iterator_id!=h.full_id||
      !ReadExact(process,h.regi+0x18,h.seven.data(),h.seven.size())||
      !Read(process,h.pointer-0xC,h.current)||!Read(process,h.pointer-0x10,h.maximum)||
      !Read(process,h.rsp+0x58,h.core_caller))return h;
  std::int32_t raw_index=0;
  if(!Read(process,h.pointer-4,raw_index)||raw_index!=h.q_index)return h;
  // Existing regular-core entry detour can make this an opaque wrapper return.
  // Preserve it as raw context; it is never a substitute for native parent TLS.
  h.physical_complete=true;
  const auto stack_q=xar::research::refill_stack_q_12004::ReadRefillStackQ12004(
      process,h.rsp,h.q_index,h.q_bits);
  h.stack_q_window=stack_q.bytes;
  h.stack_q_source_complete=stack_q.complete();
  if(!Read(process,h.pointer,h.arrg_raw))return h;
  if(h.arrg_raw==-1){h.data_count=0;h.data_complete=true;return h;}
  h.arrg_pointer=Resolve(process,base,0x5D1F340,0x5D1F338,h.arrg_raw,h.arrg_resolved);
  if(!h.arrg_pointer||h.arrg_raw!=h.arrg_resolved||
      !Read(process,h.arrg_pointer+0x14,magic)||magic!=0x41725267)return h;
  DWORD64 data=0;
  if(!Read(process,h.arrg_pointer+0x20,data)||!Read(process,h.arrg_pointer+0x2C,h.data_count)||
      h.data_count<0||h.data_count>64||(h.data_count&&!data)||
      !Read(process,h.arrg_pointer+0x140,h.army_raw))return h;
  h.army_pointer=Resolve(process,base,0x5D1DE48,0x5D1DE50,h.army_raw,h.army_resolved);
  if(!h.army_pointer||h.army_raw!=h.army_resolved||
      !Read(process,h.army_pointer+0x14,magic)||magic!=0x41726D79)return h;
  bool matching=false;
  for(std::int32_t i=0;i<h.data_count;++i) {
    std::array<std::uint32_t,4> record{};
    if(!Read(process,data+16ULL*i,record))return h;
    h.data.push_back(record);
    matching|=record[2]==h.full_id && record[3]==h.slot;
  }
  h.data_complete=matching;return h;
}
bool PairIsUnique(const std::vector<Hit> &hits) {
  if(hits.size()!=2)return false;
  const auto &a=hits[0],&b=hits[1];
  for(std::size_t i=0;i<a.seven.size();++i)
    if((i<a.slot*0x24+4||i>=a.slot*0x24+8)&&a.seven[i]!=b.seven[i])return false;
  return a.site==0&&b.site==1&&a.physical_complete&&b.physical_complete&&a.tid==b.tid&&
    a.regi==b.regi&&a.full_id==b.full_id&&a.slot==b.slot&&a.pointer==b.pointer&&
    a.rsp==b.rsp&&a.iterator==b.iterator&&a.q_bits==b.q_bits&&a.q_index==b.q_index&&
    a.maximum==b.maximum&&a.core_caller==b.core_caller&&a.qpc<b.qpc&&
    std::uint32_t(a.current+a.q_bits)==b.current;
}
void LogHit(std::ofstream &o,const Hit &h,DWORD pid,std::uint64_t ordinal) {
  o<<"{\"kind\":\"raw_ADD_boundary\",\"machine_id\":\""<<g_machine<<"\",\""<<kSiteKey<<"\":\""
   <<Hex(HitSite12004(h.site))<<"\",\"pid\":"<<pid<<",\"thread_id\":"<<h.tid
   <<",\"event_ordinal\":"<<ordinal<<",\"debug_event_ordinal\":"<<g_debug_hits<<",\"qpc\":"<<h.qpc<<",\"regi_pointer\":\""<<Hex(h.regi)
   <<"\",\"regi_full_id_u32\":"<<h.full_id<<",\"physical_slot\":"<<h.slot
   <<",\"rax_anchor\":\""<<Hex(h.pointer)<<"\",\"rsp\":\""<<Hex(h.rsp)<<"\",\"core_caller_raw\":\""<<Hex(h.core_caller)
   <<"\",\"manager_iterator\":\""<<Hex(h.iterator)<<"\",\"q_index\":"<<h.q_index
   <<",\"q_u32\":"<<h.q_bits<<",\"q_i32\":"<<static_cast<std::int32_t>(h.q_bits)
   <<",\"current_u32\":"<<h.current<<",\"maximum_u32\":"<<h.maximum
   <<",\"physical_complete\":"<<(h.physical_complete?"true":"false")
   <<",\"stack_q_source_complete\":"<<(h.stack_q_source_complete?"true":"false")
   <<",\"stack_q_window_28_hex\":\"";
  constexpr char q_digits[]="0123456789abcdef";
  for(auto b:h.stack_q_window)o<<q_digits[b>>4]<<q_digits[b&15];
  o<<"\",\"native_core_token\":null,\"natural_parent_token\":null,\"natural_attribution_ready\":false"
   <<",\"arrg_raw\":"<<h.arrg_raw<<",\"arrg_resolved\":"<<h.arrg_resolved
   <<",\"arrg_pointer\":\""<<Hex(h.arrg_pointer)<<"\",\"army_raw\":"<<h.army_raw
   <<",\"army_resolved\":"<<h.army_resolved<<",\"data_count\":"<<h.data_count
   <<",\"associated_ArRg_DATA_complete\":"<<(h.data_complete?"true":"false")<<",\"DATA\":[";
  for(std::size_t i=0;i<h.data.size();++i){if(i)o<<',';const auto &r=h.data[i];
    o<<"{\"stored_index\":"<<i<<",\"raw0\":"<<r[0]<<",\"raw4\":"<<r[1]
     <<",\"persistent_full_id_u32\":"<<r[2]<<",\"physical_ordinal_u32\":"<<r[3]<<'}';}
  o<<"],\"physical_seven_hex\":\"";
  constexpr char digits[]="0123456789abcdef";for(auto b:h.seven)o<<digits[b>>4]<<digits[b&15];
  o<<"\"}\n";o.flush();
}
bool WriteReady(const std::filesystem::path &path, DWORD pid, DWORD64 base) {
  if (std::filesystem::exists(path)) return false;
  std::ofstream ready(path, std::ios::binary | std::ios::out);
  if (!ready) return false;
  ready << "{\"schema\":\""<<kReadySchema<<"\","
        << "\"pid\":" << pid << ",\"module_base\":\"" << Hex(base)
        << "\",\"site_0\":\"" << Hex(HitSite12004(0))
        << "\",\"site_1\":\"" << Hex(HitSite12004(1))
        << "\",\"machine_id\":\"" << g_machine << "\",\"process_created_filetime\":" << g_expected_created
        << ",\"thread_id\":" << g_expected_tid << ",\"regi_full_id_u32\":" << g_expected_regiment
        << ",\"physical_slot\":" << g_expected_slot << "}\n";
  ready.flush();
  return ready.good();
}

void LogTerminal(std::ofstream &output, const std::string &status,
                 const std::string &reason, bool cleared, bool detached,
                 std::size_t hit_count) {
  output << "{\"kind\":\"terminal\",\"status\":\"" << status
         << "\",\"reason\":\"" << reason
         << "\",\"debug_registers_cleared\":"
         << (cleared ? "true" : "false") << ",\"detached\":"
         << (detached ? "true" : "false") << ",\"hit_count\":"
         << hit_count << "}\n";
  output.flush();
}

bool HasExpectedImageAndAnchors(HANDLE process, DWORD pid, DWORD64 &base) {
  if (!IsCk3Image(process)) return false;
  base = ModuleBase(pid);
  return base && ExactAnchorsAt(process,
                                {base + kSiteRvas[0], base + kSiteRvas[1]});
}

#if defined(XAR_REFILL_V3_COLD_BUILD)
bool ColdSiblingImage12004(HANDLE process,DWORD pid){
  std::array<wchar_t,32768> path{},own{};DWORD n=DWORD(path.size());
  if(!QueryFullProcessImageNameW(process,0,path.data(),&n)||!n||n>=path.size())return false;
  const DWORD own_n=GetModuleFileNameW(nullptr,own.data(),DWORD(own.size()));
  if(!own_n||own_n>=own.size())return false;
  std::error_code error;
  const auto actual=std::filesystem::weakly_canonical(std::filesystem::path(std::wstring(path.data(),n)),error);
  if(error)return false;
  const auto expected=std::filesystem::weakly_canonical(
      std::filesystem::path(std::wstring(own.data(),own_n)).parent_path()/L"refill_cold_target.exe",error);
  if(error||_wcsicmp(actual.c_str(),expected.c_str())!=0)return false;
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,pid);
  if(snapshot==INVALID_HANDLE_VALUE)return false;
  MODULEENTRY32W entry{};entry.dwSize=sizeof entry;DWORD64 base=0,size=0;
  if(Module32FirstW(snapshot,&entry))do{
    if(_wcsicmp(entry.szExePath,actual.c_str())==0){base=reinterpret_cast<DWORD64>(entry.modBaseAddr);size=entry.modBaseSize;break;}
  }while(Module32NextW(snapshot,&entry));
  CloseHandle(snapshot);
  if(!base||!size||base!=g_fixture_base||base>UINT64_MAX-size)return false;
  auto inside=[&](DWORD64 a,DWORD64 count){return a>=base&&count<=size&&a-base<=size-count;};
  return g_fixture_sites[0]<=UINT64_MAX-3&&g_fixture_sites[1]==g_fixture_sites[0]+3&&
      inside(g_fixture_sites[0],3)&&inside(g_fixture_sites[1],6)&&
      g_fixture_arrg_slot!=g_fixture_army_slot&&inside(g_fixture_arrg_slot,8)&&inside(g_fixture_army_slot,8);
}
#endif

bool AttachedIdentityMatches(HANDLE process,DWORD pid,DWORD64 base,bool fixture,
                             const std::array<DWORD64,2>&sites){
  if(ProcessCreationTime(process)!=g_expected_created)return false;
  if(fixture){
#if defined(XAR_REFILL_V3_COLD_BUILD)
    return base==g_fixture_base&&ColdSiblingImage12004(process,pid)&&ExactAnchorsAt(process,sites);
#else
    return false;
#endif
  }
  DWORD64 actual_base=0;
  return HasExpectedImageAndAnchors(process,pid,actual_base)&&actual_base==base;
}

int Probe(DWORD pid, DWORD timeout_ms, const std::filesystem::path &raw_path,
          const std::filesystem::path &ready_path,
          const std::array<DWORD64, 2> &fixture_sites = {}) {
  g_stop_requested.store(false, std::memory_order_release);
  if (pid == 0 || timeout_ms < 1000 || timeout_ms > 300000 ||
      std::filesystem::exists(raw_path) || std::filesystem::exists(ready_path)) {
    std::cerr << "invalid PID/timeout or attempt output already exists\n";
    return 2;
  }
  if(!g_expected_tid||!g_expected_created||g_expected_slot>=7)return 2;
  HANDLE process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ |
                               PROCESS_CREATE_THREAD, FALSE, pid);
  if (!process) {
    std::cerr << "cannot open explicit process\n";
    return 2;
  }
  DWORD64 base = 0;
  const std::uint64_t process_created = ProcessCreationTime(process);
  const bool fixture = fixture_sites[0] != 0 || fixture_sites[1] != 0;
#if !defined(XAR_REFILL_V3_COLD_BUILD)
  if (fixture) {
    CloseHandle(process);
    std::cerr << "fixture sites are unavailable in the production sampler\n";
    return 2;
  }
#endif
#if defined(XAR_REFILL_V3_COLD_BUILD)
  if(fixture)base=g_fixture_base;
#endif
  const bool image_ok = fixture ?
      (fixture_sites[0] != 0 && fixture_sites[1] != 0 &&
#if defined(XAR_REFILL_V3_COLD_BUILD)
        ColdSiblingImage12004(process,pid) &&
#endif
       ExactAnchorsAt(process, fixture_sites)) :
      HasExpectedImageAndAnchors(process, pid, base);
  if (!process_created || process_created!=g_expected_created || !image_ok) {
    CloseHandle(process);
    std::cerr << "process image or exact in-memory sites differ\n";
    return 2;
  }
  BOOL other_debugger=FALSE;
  if(!CheckRemoteDebuggerPresent(process,&other_debugger)||other_debugger){std::cerr<<"debugger-presence-check failed/occupied error="<<GetLastError()<<"\n";CloseHandle(process);return 2;}
  std::ofstream output(raw_path, std::ios::binary | std::ios::out);
  if (!output) {
    CloseHandle(process);
    std::cerr << "cannot create unique raw capture\n";
    return 2;
  }
  output << "{\"machine_id\":\"" << g_machine << "\",\"exact_exe_sha256_basis\":\"external-frozen-runtime-admission\",\"kind\":\"start\",\"schema\":"
         << "\""<<kRawSchema<<"\",\"pid\":" << pid
         << ",\"process_created_filetime\":" << process_created
         << ",\"module_base\":\"" << Hex(base)
         << "\",\"fixture\":" << (fixture ? "true" : "false")
         << ",\"thread_id\":" << g_expected_tid << ",\"regi_full_id_u32\":" << g_expected_regiment
         << ",\"physical_slot\":" << g_expected_slot << ",\"timeout_ms\":" << timeout_ms
         << ",\"verified_site_0_hex\":\"" << ByteHex(g_verified_pre)
         << "\",\"verified_site_1_hex\":\"" << ByteHex(g_verified_post) << "\"}\n";
  output.flush();

  (void)SetConsoleCtrlHandler(OnConsoleControl, TRUE);
  bool attached = DebugActiveProcess(pid) != FALSE;
  bool kill_on_exit_disabled = false;
  bool cleared = false;
  bool detached = false;
  bool process_exited = false;
  bool pending_event = false;
  DWORD pending_disposition=DBG_CONTINUE;
  DEBUG_EVENT event{};
  std::string reason = attached ? "none" : "debug_attach_failed";
  std::map<DWORD, HANDLE> threads;
  std::set<DWORD> armed_tids;
  std::vector<Hit> hits;
  bool ready = false;
  if (attached) {
    kill_on_exit_disabled = DebugSetProcessKillOnExit(FALSE) != FALSE;
    if (!kill_on_exit_disabled) reason = "kill_on_exit_disable_failed";
  }
  const std::array<DWORD64, 2> sites = fixture ? fixture_sites :
      std::array<DWORD64, 2>{base + kSiteRvas[0], base + kSiteRvas[1]};
  const auto deadline = std::chrono::steady_clock::now() +
                        std::chrono::milliseconds(timeout_ms);
  try { while (attached && kill_on_exit_disabled && reason == "none") {
    if (g_stop_requested.load(std::memory_order_acquire)) {
      reason = "control_cancel_requested";
      break;
    }
    if (std::chrono::steady_clock::now() >= deadline) {
      reason = "timeout_before_unique_pair";
      break;
    }
    event = DEBUG_EVENT{};
    if (!WaitForDebugEvent(&event, kWaitSliceMs)) {
      if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
      reason = "debug_event_wait_failed";
      break;
    }
    pending_event = true;
    DWORD disposition = DBG_CONTINUE;
    switch (event.dwDebugEventCode) {
      case CREATE_PROCESS_DEBUG_EVENT:
        if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);
        // Debug-event hProcess/hThread are borrowed; close only duplicated ownership.
        if(!AttachedIdentityMatches(process,pid,base,fixture,sites)){
          reason="attached_identity_changed";break;
        }
        if(!OwnDebugThread(event.dwThreadId,event.u.CreateProcessInfo.hThread,threads,armed_tids)){
          reason="cannot_own_process_thread";break;
        }
        if(event.dwThreadId!=g_expected_tid)break;
        if(!ArmThread(threads.at(event.dwThreadId),sites)){
          reason="cannot_arm_process_thread";
          if(g_saved_debug.contains(event.dwThreadId))armed_tids.insert(event.dwThreadId);
        }else armed_tids.insert(event.dwThreadId);
        break;
      case CREATE_THREAD_DEBUG_EVENT:
        if(!OwnDebugThread(event.dwThreadId,event.u.CreateThread.hThread,threads,armed_tids)){
          reason="cannot_own_new_thread";break;
        }
        if(event.dwThreadId!=g_expected_tid)break;
        if(!AttachedIdentityMatches(process,pid,base,fixture,sites)){
          reason="attached_identity_changed";break;
        }
        if(!ArmThread(threads.at(event.dwThreadId),sites)){
          reason="cannot_arm_new_thread";
          if(g_saved_debug.contains(event.dwThreadId))armed_tids.insert(event.dwThreadId);
        }else armed_tids.insert(event.dwThreadId);
        break;
      case EXIT_THREAD_DEBUG_EVENT:
        RetireDebugThread(event.dwThreadId,threads,armed_tids);
        // A reused numerical TID is a different thread generation. Never arm it
        // under the old owner binding after the selected thread has exited.
        if(event.dwThreadId==g_expected_tid)reason="selected_thread_exited_during_probe";
        break;
      case LOAD_DLL_DEBUG_EVENT:
        if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
        break;
      case EXIT_PROCESS_DEBUG_EVENT:
        process_exited = true;
        reason = "process_exited_during_probe";
        break;
      case EXCEPTION_DEBUG_EVENT: {
        const DWORD code = event.u.Exception.ExceptionRecord.ExceptionCode;
        if (code == EXCEPTION_BREAKPOINT && !ready) {
          ready = AttachedIdentityMatches(process,pid,base,fixture,sites) &&
              armed_tids.contains(g_expected_tid) && WriteReady(ready_path, pid, base);
          if (!ready) reason = "ready_receipt_failed";
          break;
        }
        if (code != EXCEPTION_SINGLE_STEP) {
          disposition = DBG_EXCEPTION_NOT_HANDLED;
          reason = "unexpected_target_exception";
          break;
        }
        auto iterator = threads.find(event.dwThreadId);
        alignas(16) CONTEXT context{};
        if (iterator == threads.end() || !GetContext(iterator->second, context)) {
          reason = "single_step_context_unavailable";
          break;
        }
        int site = -1;
        for (int index = 0; index < 2; ++index) {
          if (context.Rip == sites[index] &&
              (context.Dr6 & (1ULL << index))) site = index;
        }
        if (site < 0) {
          disposition = DBG_EXCEPTION_NOT_HANDLED;
          reason = "unrelated_single_step_exception";
          break;
        }
        if(++g_debug_hits>DebugHitLimit12004()){reason="debug_hit_budget_exhausted";break;}
        std::uint32_t candidate_id=0;
        const bool candidate=event.dwThreadId==g_expected_tid && context.Rsi &&
            Read(process,context.Rsi+0x10,candidate_id) && candidate_id==g_expected_regiment &&
            context.Rax==context.Rsi+0x28+g_expected_slot*0x24;
        auto hit=(candidate || (!hits.empty()&&site==1))?
            ReadHit(process,base,site,event.dwThreadId,context):Hit{};
        const bool selected=hit.physical_complete && hit.full_id==g_expected_regiment && hit.slot==g_expected_slot;
        if(selected || (!hits.empty() && site==1)) {
          if((hits.empty() && site!=0)||(!hits.empty() && site!=1))reason="unpaired_or_repeated_boundary";
          else {hits.push_back(hit);LogHit(output,hits.back(),pid,hits.size());}
        }
        // Intel RF suppresses immediate re-trigger at the same preinstruction
        // execute breakpoint. This changes debugger state, not game data.
        context.Dr6 = 0;
        context.EFlags |= kResumeFlag;
        context.ContextFlags=CONTEXT_CONTROL|CONTEXT_DEBUG_REGISTERS;
        if (!SetThreadContext(iterator->second, &context))
          reason = "cannot_restore_breakpoint_context";
        if (hits.size() >= 2) {
          if (PairIsUnique(hits)) reason = "paired";
          else reason = "ambiguous_or_cross_thread_pair";
        }
        break;
      }
      default:
        break;
    }
    if (reason != "none") {
      cleared = ClearAll(threads, armed_tids);
      if (!cleared && reason == "paired") reason = "debug_register_cleanup_failed";
    }
    pending_disposition=disposition;
    bool continued = ContinueDebugEvent(event.dwProcessId,
                                        event.dwThreadId, disposition) != FALSE;
    if (!continued) {
      reason = "continue_debug_event_failed";
      cleared = ClearAll(threads, armed_tids);
      continued = ContinueDebugEvent(event.dwProcessId,
                                     event.dwThreadId, disposition) != FALSE;
    }
    pending_event = !continued;
  }

  } catch(...) { reason="observer_throw"; }

  if (attached && !process_exited && !pending_event && !cleared &&
      !armed_tids.empty()) {
    // On timeout/wait failure obtain a debugger event so all target threads
    // are suspended before clearing DR0/DR1/DR7. Do not detach with armed DRs.
    if (DebugBreakProcess(process)) {
      const auto cleanup_deadline = std::chrono::steady_clock::now() +
                                    std::chrono::milliseconds(kBreakCleanupWaitMs);
      while (std::chrono::steady_clock::now() < cleanup_deadline) {
        event = DEBUG_EVENT{};
        if (!WaitForDebugEvent(&event, kWaitSliceMs)) continue;
        pending_event = true;
        if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT &&
            !OwnDebugThread(event.dwThreadId,event.u.CreateThread.hThread,threads,armed_tids))
          reason="cleanup_cannot_own_new_thread";
        if(event.dwDebugEventCode==EXIT_THREAD_DEBUG_EVENT){
          RetireDebugThread(event.dwThreadId,threads,armed_tids);
          if(event.dwThreadId==g_expected_tid)reason="selected_thread_exited_during_probe";
        }
        if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT && event.u.LoadDll.hFile)
          CloseHandle(event.u.LoadDll.hFile);
        if (event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) process_exited = true;
        const bool cleanup_break = event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
            event.u.Exception.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT;
        if (cleanup_break || process_exited)
          cleared = process_exited || ClearAll(threads, armed_tids);
        const DWORD disposition =
            event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
                    event.u.Exception.ExceptionRecord.ExceptionCode != EXCEPTION_BREAKPOINT
                ? DBG_EXCEPTION_NOT_HANDLED : DBG_CONTINUE;
        pending_disposition=disposition;
        const bool cleanup_continued=ContinueDebugEvent(event.dwProcessId,event.dwThreadId,disposition)!=FALSE;
        pending_event=!cleanup_continued;
        if(!cleanup_continued){reason="cleanup_continue_failed";break;}
        if (cleared) break;
      }
    }
    if (!cleared && !process_exited)
      cleared = SuspendAndClearAll(threads, armed_tids);
  }
  if (pending_event && !process_exited) {
    cleared = ClearAll(threads, armed_tids);
    if (ContinueDebugEvent(event.dwProcessId,event.dwThreadId,pending_disposition)) pending_event=false;
  }
  if (armed_tids.empty()) cleared = true;
  if (attached && !process_exited) {
    // DebugSetProcessKillOnExit(FALSE) ensures unexpected sampler exit detaches
    // rather than killing CK3. A RED cleanup remains explicit in the receipt.
    detached = DebugActiveProcessStop(pid) != FALSE;
  } else if (process_exited) {
    detached = true;
  }
  // Only duplicated handles are stored, including when the process has exited.
  for(const auto &[tid,handle]:threads){(void)tid;if(handle)CloseHandle(handle);}
  if (pending_event) reason = "pending_debug_event_cleanup_failed";
  if (reason == "paired" && (!cleared || !detached))
    reason = "cleanup_not_proven";
  if(PairIsUnique(hits)) {
    output<<"{\"kind\":\"physical_ADD_pair\",\"machine_id\":\""<<g_machine
      <<"\","
#if defined(XAR_REFILL_V3_COLD_BUILD)
      <<"\"fixture\":true,\"CK3_actual_ADD_observed\":false,\"synthetic_instruction_ADD_observed\":true,"
#else
      <<"\"actual_ADD_observed\":true,"
#endif
      <<"\"native_instruction_replayed_by_probe\":false,\"q_i32\":"
      <<static_cast<std::int32_t>(hits[0].q_bits)<<",\"before_current_u32\":"<<hits[0].current
      <<",\"after_current_u32\":"<<hits[1].current<<",\"DWORD_wrap_matches\":true"
      <<",\"associated_DATA_pair_complete\":"<<((hits[0].data_complete&&hits[1].data_complete&&
          hits[0].data==hits[1].data&&hits[0].arrg_pointer==hits[1].arrg_pointer&&hits[0].army_pointer==hits[1].army_pointer)?"true":"false")
      <<",\"natural_parent_token\":null,\"natural_attribution_ready\":false,\"full_window_coverage_ready\":false}\n";
    output.flush();
  }
#if defined(XAR_REFILL_V3_COLD_BUILD)
  if(PairIsUnique(hits)){
    auto bad=hits;bool refused=true;bad[1].tid+=1;refused&=!PairIsUnique(bad);
    bad=hits;bad[1].q_bits^=1;refused&=!PairIsUnique(bad);
    bad=hits;bad[1].pointer+=0x24;refused&=!PairIsUnique(bad);
    bad=hits;bad[1].current^=1;refused&=!PairIsUnique(bad);
    output<<"{\"kind\":\"fixture_mismatch_guard\",\"derived_from_actual_owned_hits\":true,"
      <<"\"cross_tid_q_pointer_current_all_refused\":"<<(refused?"true":"false")<<"}\n";
    if(!refused)reason="mismatch_guard_failed";
  }
#endif
  output << "{\"kind\":\""<<kBudgetKind<<"\",\"debug_hits\":" << g_debug_hits << ",\"limit\":"<<DebugHitLimit12004()<<"}\n";
  LogTerminal(output, reason == "paired" ? "paired" : "red", reason,
              cleared || process_exited, detached, hits.size());
  CloseHandle(process);
  (void)SetConsoleCtrlHandler(OnConsoleControl, FALSE);
  return reason == "paired" ? 0 : 1;
}

} // namespace

int wmain(int argc,wchar_t **argv) {
#if !XAR_ENABLE_REFILL_ADD_HWPROBE_12004
  std::cerr<<"default OFF: no process opened or debugger attached\n";return 3;
#else
  // Unique, explicit source/runtime admission is supplied by the cold-window owner.
  if(argc!=20||std::wstring(argv[1])!=L"--enable")return 2;
  std::map<std::wstring,std::wstring> values;
  for(int i=2;i<argc;i+=2)if(!values.emplace(argv[i],argv[i+1]).second)return 2;
  const std::array<std::wstring,9> keys{L"--pid",L"--thread",L"--regiment",L"--slot",L"--created",L"--timeout-ms",L"--raw",L"--ready",L"--machine-id"};
  if(values.size()!=keys.size())return 2;for(const auto &key:keys)if(!values.contains(key))return 2;
  try {
    const auto &machine=values[L"--machine-id"];if(machine.empty()||machine.size()>128)return 2;
    for(auto c:machine){if(!((c>=L'a'&&c<=L'z')||(c>=L'0'&&c<=L'9')||c==L'-'))return 2;g_machine.push_back(char(c));}
    auto u32=[&](const wchar_t *key){std::size_t n=0;auto v=std::stoull(values[key],&n,0);if(n!=values[key].size()||v>0xFFFFFFFFULL)throw std::out_of_range("u32");return DWORD(v);};
    g_expected_tid=u32(L"--thread");g_expected_regiment=u32(L"--regiment");g_expected_slot=u32(L"--slot");
    g_expected_created=std::stoull(values[L"--created"],nullptr,0);
    if(g_expected_regiment==0xFFFFFFFFU)return 2;
    return Probe(u32(L"--pid"),u32(L"--timeout-ms"),values[L"--raw"],values[L"--ready"]);
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 2;}
#endif
}
