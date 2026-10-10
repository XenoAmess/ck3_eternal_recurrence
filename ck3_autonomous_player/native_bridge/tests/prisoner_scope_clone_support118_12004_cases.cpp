#include "xar_bridge/prisoner_scope_clone_support118_12004.hpp"
#include <cassert>
#include <iostream>

namespace xar::ck3_12004 {
namespace {
struct SupportFixture {
  std::array<std::uint8_t, 0x50> source{};
  std::size_t reads = 0, read_bytes = 0, rejected_reads = 0;
  std::optional<std::size_t> blocked_offset;
  template<class T> void Store(std::size_t offset, T value) {
    std::memcpy(source.data() + offset, &value, sizeof(value));
  }
  SupportFixture() {
    source.fill(0xCC);
    Store(0x10, std::uintptr_t{0x10101010});
    Store(0x1C, std::int32_t{0});
    Store(0x28, std::uint32_t{0xCAFEBABE});
    Store(0x30, std::uintptr_t{0x30303030});
    Store(0x3C, std::int32_t{0});
  }
  static bool Read(void *context, const void *address, void *out, std::size_t count) noexcept {
    auto &f = *static_cast<SupportFixture *>(context);
    ++f.reads;
    const auto base = reinterpret_cast<std::uintptr_t>(f.source.data());
    const auto at = reinterpret_cast<std::uintptr_t>(address);
    if (at < base || at - base > f.source.size() || count > f.source.size() - (at - base) ||
        (f.blocked_offset && at - base == *f.blocked_offset)) {
      ++f.rejected_reads; return false;
    }
    f.read_bytes += count;
    std::memcpy(out, f.source.data() + (at - base), count); return true;
  }
  PrisonerQuoteSourceFrame12004 Frame() const {
    PrisonerQuoteSourceFrame12004 frame;
    frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
    frame.module_base = 0x140000000ULL;
    frame.native_revision = 41; frame.query_sequence = 43; frame.proof_epoch = 47;
    frame.date_raw = -123;
    frame.jailer_full_id = 0x01000011; frame.prisoner_full_id = 0x02000022;
    frame.recipient_full_id = 0x03000033;
    frame.definition_identity = 0x4444;
    frame.original_scope_identity = reinterpret_cast<std::uintptr_t>(source.data()) - 0x118;
    frame.interaction_context_identity = frame.original_scope_identity - 8;
    frame.roles_verified_in_owned_context = true; frame.same_frame_confirmed = true;
    return frame;
  }
  PrisonerQuoteReadOnlyAccess12004 Access() { return {this, &Read}; }
};
template<class T> T Raw(const PrisonerScopeCloneSupport118Source12004 &out, std::size_t offset) {
  for (std::size_t i = offset; i < offset + sizeof(T); ++i) assert(out.defined[i] == 1);
  T value{}; std::memcpy(&value, out.raw.data() + offset, sizeof(value)); return value;
}
void Unavailable(const PrisonerScopeCloneSupport118Source12004 &out) {
  assert(!out.returned_fields_source_ready && !out.physical_cloned_support_identity && !out.native_copy_called);
  for (const auto bit : out.defined) assert(bit == 0);
  assert(!out.ordered_source_vector10_elements && !out.ordered_source_vector30_elements);
}
} // namespace

// No main: the existing new quote compound owns the only execution.
void RunPrisonerScopeCloneSupport11812004Cases() {
  {
    SupportFixture fixture; const auto frame = fixture.Frame();
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), frame);
    assert(out.returned_fields_source_ready && out.frame == frame && fixture.reads == 5 &&
           fixture.read_bytes == 28 && fixture.rejected_reads == 0);
    assert(out.source_vector10_data == 0x10101010 && out.source_vector30_data == 0x30303030);
    assert(out.original_source_support_identity == reinterpret_cast<std::uintptr_t>(fixture.source.data()));
    assert(Raw<std::uint64_t>(out, 0x10) == 0 && Raw<std::uint64_t>(out, 0x30) == 0);
    assert(Raw<std::uint32_t>(out, 0x28) == 0xCAFEBABE);
    assert(Raw<std::uint64_t>(out, 0x20) == frame.module_base + 0x54DE278 &&
           Raw<std::uint64_t>(out, 0x40) == frame.module_base + 0x54DE270);
    assert(Raw<std::int32_t>(out, 0x48) == -1 && Raw<std::uint8_t>(out, 0x4E) == 0);
    assert(out.final_predicate_al_raw_u8 == 0 && !out.physical_cloned_support_identity && !out.native_copy_called);
    assert(out.ordered_source_vector10_elements && out.ordered_source_vector10_elements->empty());
    assert(out.ordered_source_vector30_elements && out.ordered_source_vector30_elements->empty());
    std::size_t defined_count = 0;
    for (std::size_t i = 0; i < out.defined.size(); ++i) {
      const bool expected = i < 0x2C || (i >= 0x30 && i < 0x4F);
      assert(out.defined[i] == (expected ? 1 : 0)); defined_count += out.defined[i];
    }
    assert(defined_count == 75);
  }
  {
    SupportFixture fixture; fixture.Store(0x1C, std::int32_t{1});
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), fixture.Frame());
    Unavailable(out); assert(out.source_vector10_count == 1 &&
        out.unavailable_reason == "support_nonempty_copy_poststate_unavailable");
    assert(fixture.reads == 5 && fixture.rejected_reads == 0);
  }
  {
    SupportFixture fixture; fixture.Store(0x3C, std::int32_t{1});
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), fixture.Frame());
    Unavailable(out); assert(out.source_vector30_count == 1 &&
        out.unavailable_reason == "support_nonempty_copy_poststate_unavailable");
  }
  {
    SupportFixture fixture; fixture.Store(0x1C, std::int32_t{-1});
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), fixture.Frame());
    Unavailable(out); assert(out.source_vector10_count == -1 &&
        out.unavailable_reason == "support_negative_source_count_path_unclosed");
  }
  {
    SupportFixture fixture; fixture.blocked_offset = 0x30;
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), fixture.Frame());
    Unavailable(out); assert(!out.source_vector30_data && fixture.rejected_reads == 1 &&
        out.unavailable_reason == "support_original_copy_fields_read_unavailable");
  }
  {
    SupportFixture fixture; auto frame = fixture.Frame(); frame.same_frame_confirmed = false;
    const auto out = ReadPrisonerScopeCloneSupport11812004(fixture.Access(), frame);
    Unavailable(out); assert(fixture.reads == 0 && !out.original_source_support_identity &&
        out.unavailable_reason == "support_original_scope_or_current_frame_unavailable");
  }
  std::cout << "support118_cases=6 defined_bytes=75 unknown_padding_bytes=5 native_copy_calls=0 physical_clone_ids=0\n";
}
} // namespace xar::ck3_12004
