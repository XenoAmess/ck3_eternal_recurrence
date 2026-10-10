#pragma once

#include "xar_bridge/ck3_12004_clergy_appointment.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>

namespace xar::ck3_12004::religion::clergy {

struct ClergyPositionRawAlOperands12004 {
  std::uint32_t owner_full_id = 0;
  std::uintptr_t position_byte_input = 0;
  std::uintptr_t predicate_input = 0;
  std::uintptr_t tooltip_input = 0;
};

struct ClergyPositionRawAlInputs12004 {
  ClergyPositionRawAlOperands12004 operands;
  std::optional<std::uint8_t> position_byte_raw;
  std::optional<std::uint32_t> predicate_4c_raw_u32;
};

enum class ClergyPositionRawAlBranch12004 : std::uint8_t {
  unavailable, original_byte_not_one, original_one_zero_4c, predicate_child,
};
enum class ClergyPositionRawAlUnavailable12004 : std::uint8_t {
  none, position_byte, predicate_4c, current_null_tooltip_path, predicate_source,
};
struct ClergyPositionRawAlResult12004 {
  std::optional<std::uint8_t> raw_al;
  ClergyPositionRawAlBranch12004 branch = ClergyPositionRawAlBranch12004::unavailable;
  ClergyPositionRawAlUnavailable12004 unavailable = ClergyPositionRawAlUnavailable12004::none;
  bool native_predicate_or_initializer_called = false;
};

template <typename T>
inline std::optional<T> ReadClergyPositionLiteral12004(
    ReadMemory read_memory, void *read_context,
    std::uintptr_t base, std::size_t offset) noexcept {
  if (read_memory == nullptr || base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base ||
      sizeof(T) > (std::numeric_limits<std::uintptr_t>::max)() - (base + offset))
    return {};
  T value{};
  if (!read_memory(read_context, reinterpret_cast<const void *>(base + offset),
                   &value, sizeof(value))) return {};
  return value;
}

inline ClergyPositionRawAlInputs12004 ReadClergyPositionRawAlInputs12004(
    ReadMemory read_memory, void *read_context,
    const ClergyPositionRawAlOperands12004 &operands) noexcept {
  ClergyPositionRawAlInputs12004 out{};
  out.operands = operands;
  out.position_byte_raw = ReadClergyPositionLiteral12004<std::uint8_t>(
      read_memory, read_context, operands.position_byte_input, 0);
  // Source31BDEC8 skips the R8+4C read unless the exact byte is1.
  if (out.position_byte_raw && *out.position_byte_raw == 1)
    out.predicate_4c_raw_u32 = ReadClergyPositionLiteral12004<std::uint32_t>(
        read_memory, read_context, operands.predicate_input, 0x4C);
  return out;
}

// The child owner binds only the actual read-only372DF10 source plus the
// actual889F60 initial scope shape. Its ABI receives literal parent inputs,
// the same current read callback/context and the source-defined root/payload.
// It cannot be bound directly to the native372DF10 function ABI. No physical
// initialized scope address or new frame is manufactured by this leaf.
struct ClergyPositionRawAlChildReader12004 {
  void *context = nullptr;
  bool (*read_actual_372df10_raw_al)(
      void *, ReadMemory, void *, std::uintptr_t predicate_input,
      std::uint16_t scope_root_word, std::uint64_t scope_payload_u64,
      std::uint8_t &raw_al) noexcept = nullptr;
};

inline ClergyPositionRawAlResult12004 ProjectClergyPositionRawAl12004(
    ReadMemory read_memory, void *read_context,
    const ClergyPositionRawAlInputs12004 &input,
    const ClergyPositionRawAlChildReader12004 &child = {}) noexcept {
  ClergyPositionRawAlResult12004 out{};
  if (!input.position_byte_raw) {
    out.unavailable = ClergyPositionRawAlUnavailable12004::position_byte;
    return out;
  }
  if (*input.position_byte_raw != 1) {
    // Source EAX is the zero-extended original byte. No bool normalization.
    out.raw_al = input.position_byte_raw;
    out.branch = ClergyPositionRawAlBranch12004::original_byte_not_one;
    return out;
  }
  if (!input.predicate_4c_raw_u32) {
    out.unavailable = ClergyPositionRawAlUnavailable12004::predicate_4c;
    return out;
  }
  if (*input.predicate_4c_raw_u32 == 0) {
    // This source branch retains original AL1, not a synthesized false.
    out.raw_al = std::uint8_t{1};
    out.branch = ClergyPositionRawAlBranch12004::original_one_zero_4c;
    return out;
  }
  if (input.operands.tooltip_input != 0) {
    out.unavailable = ClergyPositionRawAlUnavailable12004::current_null_tooltip_path;
    return out;
  }
  out.branch = ClergyPositionRawAlBranch12004::predicate_child;
  std::uint8_t child_raw = 0;
  if (child.read_actual_372df10_raw_al == nullptr ||
      !child.read_actual_372df10_raw_al(
          child.context, read_memory, read_context, input.operands.predicate_input,
          std::uint16_t{4}, static_cast<std::uint64_t>(input.operands.owner_full_id),
          child_raw)) {
    out.unavailable = ClergyPositionRawAlUnavailable12004::predicate_source;
    return out;
  }
  // Actual31BDEFF saves child AL in SIL. The null-tooltip path skips the
  // diagnostic arm and31BE0E4 restores EAX from SIL after ordinary cleanup.
  // This result qualifies the raw byte only, without claiming cleanup effects.
  out.raw_al = child_raw;
  return out;
}

inline ClergyPositionRawAlResult12004 ReadClergyPositionRawAl12004(
    ReadMemory read_memory, void *read_context,
    const ClergyPositionRawAlOperands12004 &operands,
    const ClergyPositionRawAlChildReader12004 &child = {}) noexcept {
  const auto input = ReadClergyPositionRawAlInputs12004(
      read_memory, read_context, operands);
  return ProjectClergyPositionRawAl12004(read_memory, read_context, input, child);
}

} // namespace xar::ck3_12004::religion::clergy
