#pragma once

#include "xar_bridge/ck3_12004_clergy_appointment.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::religion::clergy {

inline constexpr std::uintptr_t kClergySharedConditionRva12004 = 0x31BDDA0;
inline constexpr std::uintptr_t kClergySharedConditionChildRva12004 = 0x372DF10;

struct ClergyShared31BDDA0RawAL12004 {
  std::uint32_t rcx_raw_u32 = 0;
  std::uintptr_t rdx_identity = 0;
  std::uintptr_t r8_identity = 0;
  std::optional<std::uint8_t> rdx_raw_u8;
  std::optional<std::uint32_t> r8_4c_raw_u32;
  std::optional<std::uint8_t> raw_al;
  bool source_ready = false;
  bool condition_child_required = false;
  std::string_view branch;
  std::string_view unavailable_reason;
};

// Existing parent26 owns the exact4 current paused frame, Task/Position and
// raw fullID qualification. Preserve the literal operands from04 and08;
// this leaf creates no resolver/frame or native fallback.
// Native reads BYTE[RDX] first. Only zero requires DWORD[R8+4C]. Nonzero
// bytes return unchanged, including2..255. The nonzero DWORD branch still
// requires the distinct372DF10 condition source and is unavailable here.
ClergyShared31BDDA0RawAL12004 ReadClergyShared31BDDA0RawAL12004(
    void *read_context, ReadMemory, std::uint32_t rcx_raw_u32,
    std::uintptr_t literal_rdx, std::uintptr_t literal_r8);

} // namespace xar::ck3_12004::religion::clergy
