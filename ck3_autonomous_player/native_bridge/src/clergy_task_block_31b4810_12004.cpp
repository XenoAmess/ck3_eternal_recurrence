#include "xar_bridge/clergy_task_block_31b4810_12004.hpp"

namespace xar::ck3_12004::religion::clergy {
namespace {
template <typename T>
std::optional<T> Copy(void *context, ReadMemory read, std::uintptr_t address) {
  T value{};
  if (!read || !read(context, reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return {};
  return value;
}
} // namespace

ClergyTaskBlock31B4810Operands12004 ReadClergyTaskBlock31B4810Operands12004(
    void *context, ReadMemory read, std::uintptr_t task) {
  ClergyTaskBlock31B4810Operands12004 out{};
  out.task_identity = task;
  if (!task || !read) {
    out.unavailable_reason = "actual_task_or_guarded_copy_unavailable";
    return out;
  }
  out.task_18_pointer = Copy<std::uintptr_t>(context, read, task + 0x18);
  if (!out.task_18_pointer) {
    out.unavailable_reason = "task_18_pointer_unread";
    return out;
  }
  out.pointed_40_pointer = Copy<std::uintptr_t>(context, read, *out.task_18_pointer + 0x40);
  if (!out.pointed_40_pointer) {
    out.unavailable_reason = "pointed_40_pointer_unread";
    return out;
  }
  out.child_rdx_identity = *out.pointed_40_pointer + 0x2374;
  out.child_r8_identity = *out.pointed_40_pointer + 0x1E38;
  out.task_44_raw_u32 = Copy<std::uint32_t>(context, read, task + 0x44);
  if (!out.task_44_raw_u32) {
    out.unavailable_reason = "task_44_raw_u32_unread";
    return out;
  }
  out.source_ready = true;
  return out;
}

ClergyTaskBlock31B4810Result12004 ResolveClergyTaskBlock31B4810NullTooltip12004(
    void *context, ReadMemory read, const ClergyTaskBlock31B4810Operands12004 &input,
    const std::optional<ClergyTaskBlock31BDDA0Child12004> &child) {
  ClergyTaskBlock31B4810Result12004 out{};
  out.task_identity = input.task_identity;
  if (!input.source_ready || !input.task_44_raw_u32) {
    out.unavailable_reason = "task_block_literal_operands_unavailable";
    return out;
  }
  if (!child || !child->source_ready || !child->raw_al ||
      child->actual_callee_rva != kClergyTaskBlockChildRva12004 ||
      child->rcx_raw_u32 != *input.task_44_raw_u32 ||
      child->rdx_identity != input.child_rdx_identity ||
      child->r8_identity != input.child_r8_identity) {
    out.unavailable_reason = "child_31bdda0_same_literal_operands_unavailable";
    return out;
  }
  if (*child->raw_al == 0) {
    out.branch = "child_zero";
    out.raw_al = std::uint8_t{0};
    out.source_ready = true;
    return out;
  }
  out.task_40_raw_u32 = Copy<std::uint32_t>(context, read, input.task_identity + 0x40);
  if (!out.task_40_raw_u32) {
    out.unavailable_reason = "reached_task_40_raw_u32_unread";
    return out;
  }
  const bool equals_minus_one = *out.task_40_raw_u32 == 0xFFFFFFFFU;
  out.branch = equals_minus_one ? "child_nonzero_task40_minus_one_null_tooltip" :
                               "child_nonzero_task40_other";
  out.raw_al = equals_minus_one ? std::uint8_t{1} : std::uint8_t{0};
  out.source_ready = true;
  return out;
}
} // namespace xar::ck3_12004::religion::clergy
