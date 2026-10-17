// Only a local seven-DWORD q-source cold fixture. DEFAULT OFF, no CK3/DR/worker.
#ifndef XAR_ENABLE_REFILL_STACK_Q_COLD_12004
#define XAR_ENABLE_REFILL_STACK_Q_COLD_12004 0
#endif
#ifndef XAR_REFILL_STACK_Q_HEADER_SHA256
#define XAR_REFILL_STACK_Q_HEADER_SHA256 "unconfigured"
#endif
#ifndef XAR_REFILL_STACK_Q_FIXTURE_SHA256
#define XAR_REFILL_STACK_Q_FIXTURE_SHA256 "unconfigured"
#endif
#include "refill_stack_q_source_12004.hpp"
#include <cstdio>
#include <iostream>
#include <string>

namespace {
using namespace xar::research::refill_stack_q_12004;
bool HashPin(const std::string &s){
  if(s.size()!=64)return false;
  for(char c:s)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;
  return true;
}
const char *StatusText(Status s){
  switch(s){
    case Status::index_out_of_window:return "index_out_of_window";
    case Status::address_overflow:return "address_overflow";
    case Status::read_failed:return "read_failed";
    case Status::short_read:return "short_read";
    case Status::operand_mismatch:return "operand_mismatch";
    case Status::available:return "available";
  }
  return "invalid";
}
std::string Hex(const std::array<std::uint8_t,kWindowBytes>&b){
  constexpr char digits[]="0123456789abcdef";std::string s;s.reserve(2*b.size());
  for(auto v:b){s+=digits[v>>4];s+=digits[v&15];}return s;
}
void PrintRead(const char *name,const ReadResult &r){
  std::cout<<"\""<<name<<"\":{\"status\":\""<<StatusText(r.status)
    <<"\",\"read_attempted\":"<<(r.read_attempted?"true":"false")
    <<",\"bytes_read\":"<<r.bytes_read<<",\"win32_error\":"<<r.win32_error
    <<",\"selected_u32\":"<<r.selected_u32<<",\"window_hex\":\""<<Hex(r.bytes)<<"\"}";
}
}
int wmain(int argc,wchar_t **argv){
#if !XAR_ENABLE_REFILL_STACK_Q_COLD_12004
  (void)argc;(void)argv;
  std::cerr<<"default OFF: local q read fixture did not execute\n";return 3;
#else
  using namespace xar::research::refill_stack_q_12004;
  if(argc!=4||std::wstring(argv[1])!=L"--cold-self"||
      std::wstring(argv[2])!=L"--machine-id")return 2;
  std::string machine;
  for(wchar_t c:std::wstring(argv[3])){
    if(!((c>=L'a'&&c<=L'z')||(c>=L'0'&&c<=L'9')||c==L'-'))return 2;
    machine+=static_cast<char>(c);
  }
  if(machine.empty()||machine.size()>128||!HashPin(XAR_REFILL_STACK_Q_HEADER_SHA256)||
      !HashPin(XAR_REFILL_STACK_Q_FIXTURE_SHA256))return 2;
  // The only readable test memory is this owned local seven-DWORD buffer.
  // fixture_rsp is address geometry for the helper, not an observed CPU RSP.
  std::array<std::uint32_t,7> q{11,22,33,44,55,0x80000001U,77};
  const DWORD64 q_address=reinterpret_cast<DWORD64>(q.data());
  if(q_address<kWindowBegin)return 2;
  const DWORD64 fixture_rsp=q_address-kWindowBegin;
  const HANDLE self=GetCurrentProcess(); // Valid pseudo-handle, not an opened process.
  const auto before=ReadRefillStackQ12004(self,fixture_rsp,5,q[5]);
  const auto after=ReadRefillStackQ12004(self,fixture_rsp,5,q[5]);
  const auto mismatch=ReadRefillStackQ12004(self,fixture_rsp,5,q[5]^1U);
  const auto low=ReadRefillStackQ12004(self,fixture_rsp,-1,q[5]);
  const auto high=ReadRefillStackQ12004(self,fixture_rsp,7,q[5]);
  const auto overflow=ReadRefillStackQ12004(self,
      (std::numeric_limits<DWORD64>::max)()-kWindowEnd+1,5,q[5]);
  q[0]^=1U; // Change an unselected local q DWORD, never game data.
  const auto changed=ReadRefillStackQ12004(self,fixture_rsp,5,q[5]);
  std::array<std::uint8_t,kWindowBytes> expected{};
  std::memcpy(expected.data(),q.data(),expected.size());
  const bool real_read=before.complete()&&before.read_attempted&&before.bytes_read==28&&
      before.selected_u32==0x80000001U&&before.win32_error==0&&
      changed.complete()&&changed.bytes==expected;
  const bool unchanged=before.complete()&&after.complete()&&before.bytes==after.bytes;
  const bool detected_change=changed.complete()&&changed.selected_u32==before.selected_u32&&
      changed.bytes!=before.bytes;
  const bool operand_rejected=mismatch.status==Status::operand_mismatch&&mismatch.read_attempted&&
      mismatch.bytes_read==28&&mismatch.selected_u32==before.selected_u32;
  const bool bounds_rejected=low.status==Status::index_out_of_window&&!low.read_attempted&&
      high.status==Status::index_out_of_window&&!high.read_attempted&&low.bytes_read==0&&high.bytes_read==0;
  const bool overflow_rejected=overflow.status==Status::address_overflow&&
      !overflow.read_attempted&&overflow.bytes_read==0;
  const bool passed=real_read&&unchanged&&detected_change&&operand_rejected&&bounds_rejected&&overflow_rejected;
  SYSTEMTIME utc{};GetSystemTime(&utc);char timestamp[40]{};
  std::snprintf(timestamp,sizeof timestamp,"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",
      unsigned(utc.wYear),unsigned(utc.wMonth),unsigned(utc.wDay),unsigned(utc.wHour),
      unsigned(utc.wMinute),unsigned(utc.wSecond),unsigned(utc.wMilliseconds));
  std::cout<<"{\"schema\":\"xar.ck3.refill_stack_q_12004.cold_self.v1\",\"machine_id\":\""
    <<machine<<"\",\"machine_id_basis\":\"external_actual_owner_argument\",\"observed_at\":\""
    <<timestamp<<"\",\"fixture_header_sha256\":\""<<XAR_REFILL_STACK_Q_HEADER_SHA256
    <<"\",\"fixture_source_sha256\":\""<<XAR_REFILL_STACK_Q_FIXTURE_SHA256
    <<"\",\"status\":\""<<(passed?"pass":"fail")<<"\",\"checks\":{\"real_self_RPM\":"
    <<(real_read?"true":"false")<<",\"unchanged_double_read\":"<<(unchanged?"true":"false")
    <<",\"unselected_q_change_detected\":"<<(detected_change?"true":"false")
    <<",\"EDX_mismatch_rejected\":"<<(operand_rejected?"true":"false")
    <<",\"index_bounds_rejected_before_RPM\":"<<(bounds_rejected?"true":"false")
    <<",\"address_overflow_rejected_before_RPM\":"<<(overflow_rejected?"true":"false")<<"},\"reads\":{";
  PrintRead("before",before);std::cout<<',';PrintRead("after",after);std::cout<<',';
  PrintRead("mismatch",mismatch);std::cout<<',';PrintRead("index_low",low);std::cout<<',';
  PrintRead("index_high",high);std::cout<<',';PrintRead("overflow",overflow);std::cout<<',';
  PrintRead("changed_unselected",changed);
  std::cout<<"},\"CPU_register_RSP_observed\":false,\"actual_CK3_ADD_observed\":false,"
    <<"\"DR_installed\":false,\"native_core_token\":null,\"full_R06_qualified\":false}\n";
  return passed?0:1;
#endif
}
