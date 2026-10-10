#include "xar_bridge/prisoner_scope_clone_vector100_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
template <typename T>
void HeaderField(PrisonerScopeCloneVector10012004 &out, std::size_t offset, T value) {
  std::memcpy(out.header_raw.data() + offset, &value, sizeof(value));
  for (std::size_t i = 0; i < sizeof(value); ++i) out.header_defined_bytes[offset + i] = true;
}
} // namespace

PrisonerScopeCloneVector10012004 ReadPrisonerScopeCloneVector10012004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame) {
  PrisonerScopeCloneVector10012004 out{};
  out.frame = frame;
  if (!PrisonerQuoteSourceFrameReady12004(frame)) {
    out.unavailable_reason = "scope_member_same_query_frame_unavailable";
    return out;
  }
  constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (frame.interaction_context_identity > maximum - 8 ||
      frame.original_scope_identity != frame.interaction_context_identity + 8) {
    out.unavailable_reason = "scope_member_original_scope_relation_unavailable";
    return out;
  }
  if (frame.original_scope_identity > maximum - 0x100) {
    out.unavailable_reason = "scope_member_address_overflow";
    return out;
  }
  out.source_member_identity = frame.original_scope_identity + 0x100;
  // Literal order: signed DWORD source+C, then QWORD source+0. Both are
  // unconditional copy operands, even when the observed count is zero.
  out.source_count_raw_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(
      access, *out.source_member_identity, 0xC);
  out.source_data_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, *out.source_member_identity);
  out.source_inputs_ready = out.source_count_raw_i32.has_value() && out.source_data_identity.has_value();
  if (!out.source_inputs_ready) {
    out.unavailable_reason = "scope_member_copy_operand_unavailable";
    return out;
  }
  const auto count = *out.source_count_raw_i32;
  if (count < 0) {
    out.unavailable_reason = "scope_member_negative_count_postimage_unavailable";
    return out;
  }
  if (count == 0) {
    if (frame.module_base > maximum - 0x54DE270) {
      out.unavailable_reason = "scope_member_allocator_address_overflow";
      return out;
    }
    // Empty889780 writes count0 only. The parent seed and 37283A3 establish
    // these four exact final fields; the empty path invokes no allocator.
    HeaderField(out, 0, std::uintptr_t{0});
    HeaderField(out, 8, std::uint32_t{0});
    HeaderField(out, 0xC, std::int32_t{0});
    HeaderField(out, 0x10, frame.module_base + 0x54DE270);
    out.ordered_source_records_ready = true;
    out.logical_postimage_ready = true;
    return out;
  }
  out.allocation_request_byte_count = static_cast<std::uint64_t>(count) * 0x48;
  out.allocation_alignment = 8;
  if (static_cast<std::size_t>(count) > access.maximum_modifier_occurrences) {
    out.unavailable_reason = "scope_member_occurrence_budget_exceeded";
    return out;
  }
  if (*out.source_data_identity == 0) {
    out.unavailable_reason = "scope_member_positive_count_null_source_data";
    return out;
  }
  const auto last_offset = (static_cast<std::uint64_t>(count) - 1) * 0x48;
  if (last_offset > maximum || *out.source_data_identity > maximum - last_offset) {
    out.unavailable_reason = "scope_member_source_record_address_overflow";
    return out;
  }
  out.ordered_source_record_identities.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i)
    out.ordered_source_record_identities.push_back(*out.source_data_identity + static_cast<std::uintptr_t>(i) * 0x48);
  out.ordered_source_records_ready = true;
  // Raw borrowed record identities do not prove DBDB80's mandatory virtual
  // callback, 37297F0 nested copies, or a physical allocation result.
  out.unavailable_reason = "scope_member_positive_copy_postimage_requires_qualified_children";
  return out;
}
} // namespace xar::ck3_12004
