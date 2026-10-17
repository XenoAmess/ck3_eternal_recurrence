#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::research::refill_stack_q_12004 {
static_assert(sizeof(void*)==8,"The source contract and cold target require x64");
inline constexpr std::size_t kWindowBytes=28;
inline constexpr DWORD64 kWindowBegin=0x20,kWindowEnd=0x3C;
enum class Status : std::uint8_t {
  index_out_of_window,address_overflow,read_failed,short_read,operand_mismatch,available
};
struct ReadResult {
  std::array<std::uint8_t,kWindowBytes> bytes{};
  Status status=Status::read_failed;
  bool read_attempted=false;
  SIZE_T bytes_read=0;
  DWORD win32_error=0;
  std::uint32_t selected_u32=0;
  bool complete() const noexcept {return status==Status::available;}
};
// This is the actual v3 producer's bounded native read, not a fixture emulator.
// No index-derived remote address is ever read. A collection bound does not
// assert that the original CK3 instruction performs this bounds check.
inline ReadResult ReadRefillStackQ12004(HANDLE process,DWORD64 rsp,
    std::int32_t q_index,std::uint32_t actual_edx_u32) noexcept {
  ReadResult result;
  if(q_index<0||q_index>=7){result.status=Status::index_out_of_window;return result;}
  if(rsp>(std::numeric_limits<DWORD64>::max)()-kWindowEnd){
    result.status=Status::address_overflow;return result;
  }
  result.read_attempted=true;
  const BOOL ok=ReadProcessMemory(process,reinterpret_cast<const void*>(rsp+kWindowBegin),
      result.bytes.data(),result.bytes.size(),&result.bytes_read);
  if(!ok){result.win32_error=GetLastError();result.status=Status::read_failed;return result;}
  if(result.bytes_read!=result.bytes.size()){result.status=Status::short_read;return result;}
  std::memcpy(&result.selected_u32,result.bytes.data()+4*q_index,sizeof result.selected_u32);
  result.status=result.selected_u32==actual_edx_u32?Status::available:Status::operand_mismatch;
  return result;
}
} // namespace xar::research::refill_stack_q_12004
