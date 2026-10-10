#include "xar_bridge/prisoner_support_predicate_3727580_readonly_12004.hpp"

#include <bit>
#include <cstddef>

namespace xar::ck3_12004 {
namespace {

template <typename T>
std::optional<T> ReadDefinedLittleEndian(
    std::span<const std::uint8_t> bytes,
    std::span<const std::uint8_t> defined, std::size_t offset) noexcept {
  if (offset > bytes.size() || sizeof(T) > bytes.size() - offset ||
      offset > defined.size() || sizeof(T) > defined.size() - offset) return {};
  T value = 0;
  for (std::size_t i = 0; i < sizeof(T); ++i) {
    if (defined[offset + i] == 0) return {};
    value |= static_cast<T>(bytes[offset + i]) << (8 * i);
  }
  return value;
}

} // namespace

PrisonerSupportPredicate3727580Readonly12004
ProjectPrisonerSupportPredicate3727580FreshEmpty12004(
    std::span<const std::uint8_t> copied_support80,
    std::span<const std::uint8_t> defined_mask80) noexcept {
  PrisonerSupportPredicate3727580Readonly12004 out{};
  // 3727580 CMPDWORD[RCX+1C],0; the zero route skips vector10 data.
  const auto count10 = ReadDefinedLittleEndian<std::uint32_t>(
      copied_support80, defined_mask80, 0x1C);
  if (!count10) {
    out.unavailable_reason = "support_predicate_vector10_count_unavailable";
    return out;
  }
  out.vector10_count_raw_i32 = std::bit_cast<std::int32_t>(*count10);
  if (*out.vector10_count_raw_i32 != 0) {
    out.unavailable_reason = "support_predicate_nonempty_vector10_element_operand_unavailable";
    return out;
  }

  // 3727599 MOVRAX,[RCX+30] precedes the signed count+3C load.
  out.vector30_data_raw_u64 = ReadDefinedLittleEndian<std::uint64_t>(
      copied_support80, defined_mask80, 0x30);
  if (!out.vector30_data_raw_u64) {
    out.unavailable_reason = "support_predicate_vector30_data_unavailable";
    return out;
  }
  const auto count30 = ReadDefinedLittleEndian<std::uint32_t>(
      copied_support80, defined_mask80, 0x3C);
  if (!count30) {
    out.unavailable_reason = "support_predicate_vector30_count_unavailable";
    return out;
  }
  out.vector30_count_raw_i32 = std::bit_cast<std::int32_t>(*count30);
  if (*out.vector30_count_raw_i32 != 0) {
    out.unavailable_reason = "support_predicate_nonempty_vector30_row_operand_unavailable";
    return out;
  }

  // Native end==data for signed count0. 37275C4 CMOVE RAX,RDX (RDX0),
  // TESTRAX,RAX falls through RET37275CD, so returned AL is exactly0.
  out.al_raw_u8 = std::uint8_t{0};
  return out;
}

} // namespace xar::ck3_12004
