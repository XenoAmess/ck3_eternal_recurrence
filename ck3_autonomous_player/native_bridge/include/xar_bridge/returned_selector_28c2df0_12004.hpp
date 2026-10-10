#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kReturnedSelectorResolverRva12004 = 0x28C2DF0;
inline constexpr std::size_t kReturnedSelectorRawByteOffset12004 = 0x4D6;

using ReturnedSelectorReadBytes12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

struct ReturnedSelector28C2DF0Bindings12004 {
  bool exact_build_ready = false;
  std::uintptr_t module_base = 0;
  ReturnedSelectorReadBytes12004 read_bytes = nullptr;
  void *read_context = nullptr;
};

struct ReturnedSelector28C2DF0Step12004 {
  std::uintptr_t receiver = 0;
  std::optional<std::uint32_t> magic_1c;
  std::optional<std::uint32_t> full_id_18;
  std::optional<std::uintptr_t> context_1d0;
  std::optional<std::uintptr_t> context_1c0;
  std::optional<std::uintptr_t> related_1b8;
  std::optional<std::uint32_t> related_full_id_c8;
  std::optional<std::uintptr_t> candidate;
  std::optional<std::uint32_t> candidate_full_id_18;
  std::optional<std::uintptr_t> next_receiver;
  bool mapped_candidate_selected = false;
};

struct ReturnedObject28C2DF0Result12004 {
  std::uintptr_t input_receiver = 0;
  std::uint64_t frame_key = 0;
  std::uintptr_t returned_object = 0;
  bool source_ready = false;
  std::string_view return_path = "unavailable";
  std::string_view unavailable_reason;
  std::vector<ReturnedSelector28C2DF0Step12004> steps;
};

struct ReturnedSelector28C2DF0Result12004 : ReturnedObject28C2DF0Result12004 {
  std::optional<std::uint8_t> selector_byte_4d6;
};

ReturnedSelector28C2DF0Bindings12004 BindReturnedSelector28C2DF012004(
    std::uintptr_t module_base, std::string_view version,
    std::string_view executable_sha256, ReturnedSelectorReadBytes12004,
    void *read_context = nullptr) noexcept;

// Actual 2B9CBD7 RCX is the factor's entry RDX receiver. The caller owns the
// admitted paused-frame read boundary; frame_key preserves that attribution.
// Copies only the owned 237-byte resolver's returned-object data path. This
// entry does not read any consumer-specific member of the returned object.
// Does not invoke 28C2DF0, its diagnostic call, or any other native function.
ReturnedObject28C2DF0Result12004 ResolveReturnedObject28C2DF012004(
    const ReturnedSelector28C2DF0Bindings12004 &, std::uintptr_t actual_receiver,
    std::uint64_t frame_key);

// Factor consumer: adds its raw BYTE4D6 copy to the same object resolver.
ReturnedSelector28C2DF0Result12004 ResolveReturnedSelector28C2DF012004(
    const ReturnedSelector28C2DF0Bindings12004 &, std::uintptr_t actual_receiver,
    std::uint64_t frame_key);

} // namespace xar::ck3_12004
