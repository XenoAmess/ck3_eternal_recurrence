#include "xar_bridge/clergy_position_check_31bd1a0_12004.hpp"

#include <bit>
#include <limits>

namespace xar::ck3_12004::religion::clergy {
namespace {
constexpr std::string_view kUpperSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::string_view kLowerSha =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

bool Add(std::uintptr_t receiver, std::uintptr_t offset,
         std::uintptr_t &address) noexcept {
  if (!receiver || receiver > (std::numeric_limits<std::uintptr_t>::max)() - offset)
    return false;
  address = receiver + offset;
  return true;
}
template <typename T>
std::optional<T> Copy(void *context, ReadMemory read,
    std::uintptr_t receiver, std::uintptr_t offset = 0) noexcept {
  std::uintptr_t address = 0;
  if (!read || !Add(receiver, offset, address) ||
      address > (std::numeric_limits<std::uintptr_t>::max)() - (sizeof(T)-1)) return {};
  T value{};
  if (!read(context, reinterpret_cast<const void *>(address), &value, sizeof(value))) return {};
  return value;
}
} // namespace

ClergyPosition31BD1A0RawAL12004 ReadClergyPosition31BD1A0RawAL12004(
    void *context, ReadMemory read, const ClergyPosition31BD1A0Arguments12004 &args) {
  ClergyPosition31BD1A0RawAL12004 out;
  if (args.executable_sha256 != kUpperSha && args.executable_sha256 != kLowerSha) {
    out.unavailable_reason = "actual4_source_image_unavailable"; return out;
  }
  std::uintptr_t literal = 0, flag = 0, condition = 0;
  if (!Add(args.module_base, kClergyPositionCheckLiteralRva12004, literal) ||
      args.stack_argument5 != literal || args.stack_argument6 != 0 ||
      !Add(args.position_identity, 0x2378, flag) ||
      !Add(args.position_identity, 0x2178, condition)) {
    out.unavailable_reason = "current_literal_call_operands_unavailable"; return out;
  }
  out.initial_child = ReadClergyShared31BDDA0RawAL12004(
      context, read, args.owner_full_id_raw_u32, flag, condition);
  if (!out.initial_child.source_ready || !out.initial_child.raw_al) {
    out.unavailable_reason = out.initial_child.unavailable_reason;
    out.next_source_entry = out.initial_child.condition_child_required ? "0x372DF10" : "0x31BDDA0";
    return out;
  }
  if (*out.initial_child.raw_al != 0 && args.r9_raw_u32 == 0) {
    out.available = true; out.raw_al = std::uint8_t{0};
    out.branch = "initial_al_nonzero_r9_zero_nulltooltip";
    return out;
  }
  out.position2338_raw_u32 = Copy<std::uint32_t>(context, read, args.position_identity, 0x2338);
  if (!out.position2338_raw_u32) {
    out.unavailable_reason = "position2338_dword_unavailable"; return out;
  }
  if (*out.position2338_raw_u32 == 0) {
    out.available = true; out.raw_al = std::uint8_t{1};
    out.branch = "position2338_zero";
    return out;
  }
  out.dynamic_numeric_required = true;
  out.branch = "position2338_nonzero_dynamic_expression";
  out.next_source_entry = "0xA0F0B0 dynamic: 0x37540B0 /0x37498A0 /0x3755500 plus named/context cleanup";
  out.clock_identity = Copy<std::uintptr_t>(context, read, args.module_base,
                                          kClergyPositionCheckClockSlotRva12004);
  if (!out.clock_identity || !*out.clock_identity) {
    out.unavailable_reason = "clock_pointer_unavailable"; return out;
  }
  out.clock_date_raw_u32 = Copy<std::uint32_t>(context, read, *out.clock_identity, 8);
  out.task28_raw_u32 = Copy<std::uint32_t>(context, read, args.task28_identity);
  if (!out.clock_date_raw_u32 || !out.task28_raw_u32) {
    out.unavailable_reason = "date_operands_unavailable"; return out;
  }
  const std::uint32_t delta = *out.clock_date_raw_u32 - *out.task28_raw_u32;
  out.elapsed_signed_div24 = std::bit_cast<std::int32_t>(delta) /24;
  // No caller-supplied ready flag, static-mode value or aggregate CanFire
  // result substitutes for the reached dynamic expression and cleanup source.
  out.unavailable_reason = "dynamic_a0f0b0_named_context_cleanup_source_pending";
  return out;
}

bool ReadClergyPosition31BD1A0Callback12004(
    void *opaque, std::uintptr_t position, std::uint32_t owner_raw,
    std::uintptr_t task28, std::uint32_t comparison,
    std::uintptr_t literal_argument5, std::uint8_t &raw_al) noexcept {
  if (!opaque) return false;
  const auto &context = *static_cast<const ClergyPosition31BD1A0ReadContext12004 *>(opaque);
  const ClergyPosition31BD1A0Arguments12004 arguments{
      context.module_base, context.executable_sha256, position, owner_raw,
      task28, comparison, literal_argument5, 0};
  const auto result = ReadClergyPosition31BD1A0RawAL12004(
      context.read_context, context.read_memory, arguments);
  if (!result.available || !result.raw_al) return false;
  raw_al = *result.raw_al;
  return true;
}

} // namespace xar::ck3_12004::religion::clergy
