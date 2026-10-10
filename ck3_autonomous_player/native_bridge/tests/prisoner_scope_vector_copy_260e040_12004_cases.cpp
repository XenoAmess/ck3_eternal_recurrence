// No main:35/10's sole new prisoner selected-quote connected compound calls it.
#include "xar_bridge/prisoner_scope_vector_copy_260e040_12004.hpp"
#include <algorithm>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kScope = 0x20000000;
constexpr std::uintptr_t kData = 0x30000000;
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
struct RawVector {
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  std::array<std::byte, 8 * 24> raw{};
  std::size_t payload_reads = 0;
  std::size_t count_reads = 0;
  bool change_payload = false;
  bool change_count = false;
  static bool Read(void *context, const void *address, void *out,
                   std::size_t width) noexcept {
    auto &input = *static_cast<RawVector *>(context);
    const auto source = reinterpret_cast<std::uintptr_t>(address);
    if (source == kScope + 0x18 && width == sizeof(input.data)) {
      std::memcpy(out, &input.data, width);
      return true;
    }
    if (source == kScope + 0x24 && width == sizeof(input.count)) {
      ++input.count_reads;
      const auto value = input.count +
          (input.change_count && input.count_reads > 1 ? 1 : 0);
      std::memcpy(out, &value, width);
      return true;
    }
    if (source == kData && width <= input.raw.size()) {
      ++input.payload_reads;
      std::memcpy(out, input.raw.data(), width);
      if (input.change_payload && input.payload_reads > 1 && width > 0)
        static_cast<std::byte *>(out)[0] ^= std::byte{1};
      return true;
    }
    return false;
  }
};
PrisonerQuoteSourceFrame12004 Frame() {
  PrisonerQuoteSourceFrame12004 frame;
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x140000000;
  frame.native_revision = 7;
  frame.query_sequence = 11;
  frame.proof_epoch = 13;
  frame.date_raw = 17;
  frame.jailer_full_id = 0xAA000001u;
  frame.prisoner_full_id = 0xBB000002u;
  frame.recipient_full_id = 0xCC000003u;
  frame.definition_identity = 0x41000000;
  frame.interaction_context_identity = 0x42000000;
  frame.original_scope_identity = kScope;
  frame.roles_verified_in_owned_context = true;
  frame.same_frame_confirmed = true;
  return frame;
}
} // namespace

void RunPrisonerScopeVectorCopy260E04012004Cases() {
  const auto frame = Frame();
  {
    RawVector raw;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(out.copied_shape_ready && out.count_i32 == 0 && out.source_data_identity == 0 &&
        out.destination_capacity_i32 == 8 && out.data_clone_relative_offset == 0x38 &&
        out.allocator_clone_relative_offset == 0x30 && out.copied_inline_bytes == 0 &&
        raw.payload_reads == 0 && out.frame == frame &&
        std::all_of(out.source_defined_inline_mask.begin(), out.source_defined_inline_mask.end(),
                    [](std::uint8_t value) { return value == 0; }),
        "260e040_empty_source_retains_nonnull_clone_relations_without_inline_zero_claim");
  }
  {
    RawVector raw;
    raw.data = kData;
    raw.count = 2;
    for (std::size_t i = 0; i < raw.raw.size(); ++i)
      raw.raw[i] = static_cast<std::byte>((i * 37 + 19) & 0xFF);
    const std::uint64_t pointer_bits = 0xFEDCBA9876543210ull;
    std::memcpy(raw.raw.data() + 8, &pointer_bits, sizeof(pointer_bits));
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(out.copied_shape_ready && out.copied_inline_bytes == 48 &&
        std::equal(raw.raw.begin(), raw.raw.begin() + 48, out.inline_raw.begin()) &&
        raw.payload_reads == 2 && !out.allocation_required,
        "260e040_raw24B_cells_keep_literal_pointer_bits");
    for (std::size_t i = 0; i < out.source_defined_inline_mask.size(); ++i)
      Require(out.source_defined_inline_mask[i] == static_cast<std::uint8_t>(i < 48),
              "260e040_only_copied_cells_defined");
  }
  {
    RawVector raw;
    raw.count = -3;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(out.copied_shape_ready && out.count_i32 == -3 && out.copied_inline_bytes == 0 &&
        raw.payload_reads == 0, "260e040_negative_count_copied_without_data_loop");
  }
  {
    RawVector raw;
    raw.data = kData;
    raw.count = 9;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(!out.copied_shape_ready && out.allocation_required && raw.payload_reads == 0 &&
        out.unavailable_reason == "scope_vector_allocator_postimage_unavailable",
        "260e040_allocation_result_not_invented");
  }
  {
    RawVector raw;
    raw.data = kData;
    raw.count = 2;
    raw.change_count = true;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(!out.copied_shape_ready && out.unavailable_reason == "scope_vector_source_metadata_changed",
            "260e040_source_count_changed_after_copy");
  }
  {
    RawVector raw;
    raw.data = kData;
    raw.count = 2;
    raw.change_payload = true;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope);
    Require(!out.copied_shape_ready && out.unavailable_reason == "scope_vector_source_cells_changed",
            "260e040_source_payload_changed_after_copy");
  }
  {
    RawVector raw;
    const PrisonerQuoteReadOnlyAccess12004 access{&raw, &RawVector::Read};
    const auto out = ReadPrisonerScopeVectorCopy260E04012004(access, frame, kScope + 0x100);
    Require(!out.copied_shape_ready && raw.count_reads == 0 && raw.payload_reads == 0,
            "260e040_current_scope_identity_guard");
  }
}
} // namespace xar::ck3_12004
