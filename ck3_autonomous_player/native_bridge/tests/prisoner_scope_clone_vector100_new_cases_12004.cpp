#include "xar_bridge/prisoner_scope_clone_vector100_12004.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace xar::ck3_12004 {
namespace {
struct Memory {
  std::unordered_map<std::uintptr_t, std::vector<std::byte>> atoms;
  std::size_t reads = 0;
  template <typename T> void Put(std::uintptr_t at, T value) {
    auto &bytes = atoms[at]; bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
};
bool Guard(void *context, const void *address, void *output, std::size_t bytes) noexcept {
  auto &memory = *static_cast<Memory *>(context); ++memory.reads;
  const auto it = memory.atoms.find(reinterpret_cast<std::uintptr_t>(address));
  if (it == memory.atoms.end() || it->second.size() != bytes) return false;
  std::memcpy(output, it->second.data(), bytes); return true;
}
void Require(bool ok, const char *reason) { if (!ok) throw std::runtime_error(reason); }
PrisonerQuoteSourceFrame12004 Frame() {
  PrisonerQuoteSourceFrame12004 frame{};
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x140000000; frame.native_revision = 93;
  frame.query_sequence = 17; frame.proof_epoch = 4; frame.date_raw = 53300000;
  frame.jailer_full_id = 0x11007485; frame.prisoner_full_id = 0x22007486;
  frame.recipient_full_id = 0x33007487; frame.definition_identity = 0x200000;
  frame.interaction_context_identity = 0x3FFFF8; frame.original_scope_identity = 0x400000;
  frame.roles_verified_in_owned_context = true; frame.same_frame_confirmed = true;
  return frame;
}
template <typename T> T Header(const PrisonerScopeCloneVector10012004 &out, std::size_t offset) {
  T value{}; std::memcpy(&value, out.header_raw.data() + offset, sizeof(value)); return value;
}
bool NoHeader(const PrisonerScopeCloneVector10012004 &out) {
  return std::none_of(out.header_defined_bytes.begin(), out.header_defined_bytes.end(), [](bool b) { return b; });
}
} // namespace

// One new fragment in central10's sole selected-quote compound; no local main.
void RunPrisonerScopeCloneVector10012004Cases() {
  const auto frame = Frame(); const auto member = frame.original_scope_identity + 0x100;
  Memory memory; PrisonerQuoteReadOnlyAccess12004 access{&memory, &Guard, 8};

  memory.Put(member + 0xC, std::int32_t{0}); memory.Put(member, std::uintptr_t{0x700000});
  auto out = ReadPrisonerScopeCloneVector10012004(access, frame);
  Require(out.frame == frame && out.source_inputs_ready && out.logical_postimage_ready &&
      out.ordered_source_records_ready && out.ordered_source_record_identities.empty(), "48d empty same-query projection");
  Require(out.source_data_identity == std::optional<std::uintptr_t>{0x700000} && memory.reads == 2 &&
      std::all_of(out.header_defined_bytes.begin(), out.header_defined_bytes.end(), [](bool b) { return b; }) &&
      Header<std::uintptr_t>(out, 0) == 0 && Header<std::uint32_t>(out, 8) == 0 &&
      Header<std::int32_t>(out, 0xC) == 0 && Header<std::uintptr_t>(out, 0x10) == frame.module_base + 0x54DE270 &&
      !out.physical_native_clone_identity && !out.native_return_pointer && !out.native_cleanup_completed &&
      !out.native_clone_invoked, "48d empty preserves borrowed source and native-witness absence");

  memory.Put(member + 0xC, std::int32_t{3});
  out = ReadPrisonerScopeCloneVector10012004(access, frame);
  Require(out.source_inputs_ready && out.ordered_source_records_ready && !out.logical_postimage_ready &&
      out.ordered_source_record_identities == std::vector<std::uintptr_t>{0x700000, 0x700048, 0x700090} &&
      out.allocation_request_byte_count == std::optional<std::uint64_t>{216} &&
      out.allocation_alignment == std::optional<std::uint32_t>{8} && NoHeader(out),
      "48d positive ordered raw inputs have no fabricated postimage");

  access.maximum_modifier_occurrences = 2;
  out = ReadPrisonerScopeCloneVector10012004(access, frame);
  Require(out.source_count_raw_i32 == std::optional<std::int32_t>{3} && out.source_inputs_ready &&
      !out.ordered_source_records_ready && out.ordered_source_record_identities.empty() && NoHeader(out) &&
      out.unavailable_reason == "scope_member_occurrence_budget_exceeded", "48d occurrence limit preserves raw count");

  memory.Put(member + 0xC, std::int32_t{-1});
  out = ReadPrisonerScopeCloneVector10012004(access, frame);
  Require(out.source_inputs_ready && out.source_count_raw_i32 == std::optional<std::int32_t>{-1} &&
      !out.logical_postimage_ready && !out.allocation_request_byte_count && NoHeader(out),
      "48d negative count cannot become empty");

  memory.Put(member + 0xC, std::int32_t{0}); memory.atoms.erase(member);
  out = ReadPrisonerScopeCloneVector10012004(access, frame);
  Require(out.source_count_raw_i32 == std::optional<std::int32_t>{0} && !out.source_data_identity &&
      !out.source_inputs_ready && !out.logical_postimage_ready && NoHeader(out),
      "48d missing unconditional operand cannot complete empty projection");

  auto wrong_frame = frame; wrong_frame.same_frame_confirmed = false;
  const auto before = memory.reads; out = ReadPrisonerScopeCloneVector10012004(access, wrong_frame);
  Require(out.frame == wrong_frame && memory.reads == before && !out.source_count_raw_i32 && NoHeader(out),
      "48d mismatched frame cannot read source");

  auto overflow_frame = frame;
  overflow_frame.original_scope_identity = (std::numeric_limits<std::uintptr_t>::max)() - 0x100 + 1;
  overflow_frame.interaction_context_identity = overflow_frame.original_scope_identity - 8;
  out = ReadPrisonerScopeCloneVector10012004(access, overflow_frame);
  Require(memory.reads == before && !out.source_member_identity && !out.source_inputs_ready && NoHeader(out),
      "48d original scope address overflow stays unknown");

  auto unrelated_scope = frame; unrelated_scope.original_scope_identity += 0x1000;
  out = ReadPrisonerScopeCloneVector10012004(access, unrelated_scope);
  Require(memory.reads == before && !out.source_member_identity && !out.source_inputs_ready && NoHeader(out),
      "48d arbitrary scope cannot replace literal context+8 source");
}
} // namespace xar::ck3_12004
