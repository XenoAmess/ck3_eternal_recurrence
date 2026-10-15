#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <limits>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kWarPaymentGenericSource12004 = 0x28A6D10;
inline constexpr std::uintptr_t kWarPaymentGenericReturn12004 = 0x28A6D7C;
inline constexpr std::size_t kWarPaymentGenericStackCapacity12004 = 32;
struct WarPaymentGenericValues12004 {
  std::optional<std::uintptr_t> context_identity_before, context_identity_after;
  std::optional<std::int64_t> value_2c0, value_2c8, value_28, value_30;
  bool capture_complete = false, context_stable = false;
  std::uint32_t failed_reads = 0;
};
using WarPaymentRawRead12004 = bool (*)(void *,std::uintptr_t,void *,std::size_t) noexcept;
namespace generic_context_read_detail_12004 {
template<class T> inline std::optional<T> Read(WarPaymentRawRead12004 read,
    void *read_context,WarPaymentGenericValues12004 &v,
    std::uintptr_t address,std::size_t offset) noexcept {
  T out{};
  if(!address||offset>(std::numeric_limits<std::uintptr_t>::max)()-address||
     !read||!read(read_context,address+offset,&out,sizeof out)) {
    ++v.failed_reads;return std::nullopt;
  }
  return out;
}
} // namespace generic_context_read_detail_12004
// Shared raw memory reader only: neither a native getter nor a wallet callback.
inline WarPaymentGenericValues12004 ReadWarPaymentGenericValues12004(
    WarPaymentRawRead12004 read,void *read_context,std::uintptr_t character) noexcept {
  using generic_context_read_detail_12004::Read;
  WarPaymentGenericValues12004 v{};
  v.context_identity_before=Read<std::uintptr_t>(read,read_context,v,character,0x1C0);
  if(v.context_identity_before&&*v.context_identity_before) {
    const auto context=*v.context_identity_before;
    v.value_2c0=Read<std::int64_t>(read,read_context,v,context,0x2C0);
    v.value_2c8=Read<std::int64_t>(read,read_context,v,context,0x2C8);
    v.value_28=Read<std::int64_t>(read,read_context,v,context,0x28);
    v.value_30=Read<std::int64_t>(read,read_context,v,context,0x30);
  }
  v.context_identity_after=Read<std::uintptr_t>(read,read_context,v,character,0x1C0);
  v.context_stable=v.context_identity_before&&*v.context_identity_before&&
    v.context_identity_after&&v.context_identity_before==v.context_identity_after;
  v.capture_complete=!v.failed_reads&&v.context_stable&&v.value_2c0&&
    v.value_2c8&&v.value_28&&v.value_30;
  return v;
}
struct WarPaymentGenericParentTrace12004 {
  std::uintptr_t module_base = 0;
  std::uint32_t module_image_size = 0, reported_frame_count = 0;
  bool capture_succeeded = false, truncated = false;
  std::uint32_t caller_match_count = 0;
  std::array<std::uintptr_t,kWarPaymentGenericStackCapacity12004> frames_absolute{};
  std::optional<std::uintptr_t> parent_return_absolute, parent_return_rva;
  bool parent_in_same_image = false;
};
struct WarPaymentGenericContext12004 {
  WarPaymentGenericValues12004 before, after;
  WarPaymentGenericParentTrace12004 parent_trace;
  std::optional<std::int64_t> before_computed_add_raw;
  std::optional<bool> before_formula_matches_amount;
  bool context_values_stable = false;
};
using WarPaymentStackFrames12004 = std::uint32_t (*)(void *,std::uintptr_t *,std::size_t) noexcept;
} // namespace xar::ck3_12004
