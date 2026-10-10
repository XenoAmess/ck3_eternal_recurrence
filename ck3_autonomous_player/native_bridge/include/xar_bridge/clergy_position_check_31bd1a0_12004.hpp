#pragma once

#include "xar_bridge/clergy_shared_condition_31bdda0_12004.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::religion::clergy {

inline constexpr std::uintptr_t kClergyPositionCheckRva12004 = 0x31BD1A0;
inline constexpr std::uintptr_t kClergyPositionCheckLiteralRva12004 = 0x48C8710;
inline constexpr std::uintptr_t kClergyPositionCheckClockSlotRva12004 = 0x5C68C50;

struct ClergyPosition31BD1A0Arguments12004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
  std::uintptr_t position_identity = 0;
  std::uint32_t owner_full_id_raw_u32 = 0;
  std::uintptr_t task28_identity = 0;
  std::uint32_t r9_raw_u32 = 0;
  std::uintptr_t stack_argument5 = 0;
  std::uintptr_t stack_argument6 = 0;
};

struct ClergyPosition31BD1A0RawAL12004 {
  bool available = false;
  std::optional<std::uint8_t> raw_al;
  ClergyShared31BDDA0RawAL12004 initial_child;
  std::optional<std::uint32_t> position2338_raw_u32;
  std::optional<std::uintptr_t> clock_identity;
  std::optional<std::uint32_t> clock_date_raw_u32, task28_raw_u32;
  std::optional<std::int32_t> elapsed_signed_div24;
  bool dynamic_numeric_required = false;
  std::string_view branch, unavailable_reason, next_source_entry;
};

struct ClergyPosition31BD1A0ReadContext12004 {
  void *read_context = nullptr;
  ReadMemory read_memory = nullptr;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
};

// Literal current31B4A10@31B4A96 operands only. Parent26 owns its existing
// Task/Position/fullID/current-frame qualification and guarded-copy adapter.
// No native CanFire/CanReassign/validator, constructor or evaluator is called.
// Availability is computed from actual reads and reached closed branches.
// Nonzero Position+2338 requires dynamic A0F0B0 source: it is the same B8
// field, so that evaluator's static mode is never a replacement here.
ClergyPosition31BD1A0RawAL12004 ReadClergyPosition31BD1A0RawAL12004(
    void *read_context, ReadMemory read_memory,
    const ClergyPosition31BD1A0Arguments12004 &arguments);

// Exact parent26 software-final callback ABI. The context carries only its
// existing image/read adapter; nulltooltip is fixed by this caller profile.
// False leaves output unchanged and means unavailable, not native ALfalse.
bool ReadClergyPosition31BD1A0Callback12004(
    void *context, std::uintptr_t position, std::uint32_t owner_raw,
    std::uintptr_t task28, std::uint32_t comparison,
    std::uintptr_t literal_argument5, std::uint8_t &raw_al) noexcept;

} // namespace xar::ck3_12004::religion::clergy
