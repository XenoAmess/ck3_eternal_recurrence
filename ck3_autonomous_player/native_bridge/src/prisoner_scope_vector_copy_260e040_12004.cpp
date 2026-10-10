#include "xar_bridge/prisoner_scope_vector_copy_260e040_12004.hpp"
#include <algorithm>
#include <limits>

namespace xar::ck3_12004 {
PrisonerScopeVectorCopy260E04012004 ReadPrisonerScopeVectorCopy260E04012004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    std::uintptr_t source_scope) {
  PrisonerScopeVectorCopy260E04012004 out;
  out.frame = frame;
  out.source_scope_identity = source_scope;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!PrisonerQuoteSourceFrameReady12004(frame) ||
      source_scope != frame.original_scope_identity || access.read_memory == nullptr ||
      source_scope > (std::numeric_limits<std::uintptr_t>::max)() - 0x18)
    return fail("scope_vector_current_source_frame_unavailable");
  out.source_vector_identity = source_scope + 0x18;
  out.source_data_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, out.source_vector_identity);
  out.count_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(
      access, out.source_vector_identity, 0xC);
  if (!out.source_data_identity || !out.count_i32)
    return fail("scope_vector_source_metadata_unavailable");
  if (*out.count_i32 > out.destination_capacity_i32) {
    out.allocation_required = true;
    return fail("scope_vector_allocator_postimage_unavailable");
  }
  std::array<std::byte, 8 * 24> second_copy{};
  if (*out.count_i32 > 0) {
    out.copied_inline_bytes = static_cast<std::size_t>(*out.count_i32) * 24;
    if (*out.source_data_identity == 0 ||
        *out.source_data_identity > (std::numeric_limits<std::uintptr_t>::max)() - out.copied_inline_bytes ||
        !access.read_memory(access.context, reinterpret_cast<const void *>(*out.source_data_identity),
                            out.inline_raw.data(), out.copied_inline_bytes) ||
        !access.read_memory(access.context, reinterpret_cast<const void *>(*out.source_data_identity),
                            second_copy.data(), out.copied_inline_bytes))
      return fail("scope_vector_source_cells_unavailable");
    if (out.inline_raw != second_copy)
      return fail("scope_vector_source_cells_changed");
  }
  const auto after_data = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, out.source_vector_identity);
  const auto after_count = ReadPrisonerQuoteSource12004<std::int32_t>(
      access, out.source_vector_identity, 0xC);
  if (!after_data || !after_count || after_data != out.source_data_identity ||
      after_count != out.count_i32)
    return fail("scope_vector_source_metadata_changed");
  std::fill_n(out.source_defined_inline_mask.begin(), out.copied_inline_bytes,
              std::uint8_t{1});
  out.copied_shape_ready = true;
  return out;
}
} // namespace xar::ck3_12004
