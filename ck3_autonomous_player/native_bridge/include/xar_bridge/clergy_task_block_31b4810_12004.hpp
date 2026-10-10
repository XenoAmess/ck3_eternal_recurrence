#pragma once

#include "xar_bridge/ck3_12004_clergy_appointment.hpp"

namespace xar::ck3_12004::religion::clergy {
inline constexpr std::uintptr_t kClergyTaskBlockRva12004 = 0x31B4810;
inline constexpr std::uintptr_t kClergyTaskBlockChildRva12004 = 0x31BDDA0;

struct ClergyTaskBlock31B4810Operands12004 {
  std::uintptr_t task_identity = 0;
  std::optional<std::uintptr_t> task_18_pointer, pointed_40_pointer;
  std::optional<std::uint32_t> task_44_raw_u32;
  std::uintptr_t child_rdx_identity = 0, child_r8_identity = 0;
  bool source_ready = false;
  std::string_view unavailable_reason;
};

struct ClergyTaskBlock31BDDA0Child12004 {
  std::uintptr_t actual_callee_rva = 0;
  std::uint32_t rcx_raw_u32 = 0;
  std::uintptr_t rdx_identity = 0, r8_identity = 0;
  std::optional<std::uint8_t> raw_al;
  bool source_ready = false;
};

struct ClergyTaskBlock31B4810Result12004 {
  std::uintptr_t task_identity = 0;
  std::optional<std::uint32_t> task_40_raw_u32;
  std::optional<std::uint8_t> raw_al;
  bool source_ready = false;
  std::string_view branch, unavailable_reason;
};

// The existing current-base caller owns exact4 Task qualification, the paused
// transaction and before/after identity checks. No new frame or query is made.
// These entries use only its guarded-copy callback; no native fallback exists.
ClergyTaskBlock31B4810Operands12004 ReadClergyTaskBlock31B4810Operands12004(
    void *read_context, ReadMemory, std::uintptr_t actual_task);

// Actual mode0 null-tooltip path only. Task40 is read only after a nonzero
// source-closed child AL, matching CMP31B4849. Tooltip formatting is unreached.
ClergyTaskBlock31B4810Result12004 ResolveClergyTaskBlock31B4810NullTooltip12004(
    void *read_context, ReadMemory, const ClergyTaskBlock31B4810Operands12004 &,
    const std::optional<ClergyTaskBlock31BDDA0Child12004> &);
} // namespace xar::ck3_12004::religion::clergy
