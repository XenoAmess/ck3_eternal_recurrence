#include "xar_bridge/clergy_shared_condition_31bdda0_12004.hpp"

#include <limits>

namespace xar::ck3_12004::religion::clergy {
namespace {
template <typename T>
std::optional<T> Copy(void *context, ReadMemory read,
    std::uintptr_t receiver, std::uintptr_t offset) {
  if (read == nullptr ||
      receiver > std::numeric_limits<std::uintptr_t>::max() - offset) {
    return std::nullopt;
  }
  const auto address = receiver + offset;
  if (address > std::numeric_limits<std::uintptr_t>::max() - (sizeof(T) - 1)) {
    return std::nullopt;
  }
  T value{};
  if (!read(context, reinterpret_cast<const void *>(address), &value, sizeof(T))) {
    return std::nullopt;
  }
  return value;
}
} // namespace

ClergyShared31BDDA0RawAL12004 ReadClergyShared31BDDA0RawAL12004(
    void *read_context, ReadMemory read, std::uint32_t rcx_raw_u32,
    std::uintptr_t literal_rdx, std::uintptr_t literal_r8) {
  ClergyShared31BDDA0RawAL12004 result;
  result.rcx_raw_u32 = rcx_raw_u32;
  result.rdx_identity = literal_rdx;
  result.r8_identity = literal_r8;
  result.rdx_raw_u8 = Copy<std::uint8_t>(read_context, read, literal_rdx, 0);
  if (!result.rdx_raw_u8) {
    result.unavailable_reason = "literal_rdx_byte_unread";
    return result;
  }
  if (*result.rdx_raw_u8 != 0) {
    result.raw_al = *result.rdx_raw_u8;
    result.source_ready = true;
    result.branch = "literal_rdx_byte_nonzero";
    return result;
  }
  result.r8_4c_raw_u32 = Copy<std::uint32_t>(read_context, read, literal_r8, 0x4C);
  if (!result.r8_4c_raw_u32) {
    result.unavailable_reason = "literal_r8_4c_dword_unread";
    return result;
  }
  if (*result.r8_4c_raw_u32 == 0) {
    result.raw_al = std::uint8_t{0};
    result.source_ready = true;
    result.branch = "literal_rdx_zero_r8_4c_zero";
    return result;
  }
  result.condition_child_required = true;
  result.branch = "literal_rdx_zero_r8_4c_nonzero";
  result.unavailable_reason = "condition_372df10_source_pending";
  return result;
}

} // namespace xar::ck3_12004::religion::clergy
