#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

enum class NegotiatedReplyReporter12004 : std::uint32_t {
  rva307B910 = 0x307B910,
  rva307BAF0 = 0x307BAF0,
};

using NegotiatedReplyReporterReadMemory12004 =
    bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;

struct NegotiatedReplyReporterRequest12004 {
  NegotiatedReplyReporter12004 reporter = NegotiatedReplyReporter12004::rva307B910;
  std::string_view executable_sha256{};
  // The actual caller RCX two-word bundle, in its original supplied frame.
  std::uintptr_t output_bundle_receiver = 0;
  std::uint64_t frame_key = 0;
};

struct NegotiatedReplyReporterSuppliedContents12004 {
  NegotiatedReplyReporter12004 reporter = NegotiatedReplyReporter12004::rva307B910;
  std::string_view executable_sha256{};
  std::uint64_t frame_key = 0;
  // Actual caller307BD70 maps first content to incoming argument5. For
  // 307B910 only, second content is incoming argument4. Caller-frame binding
  // remains its producer's responsibility; these are supplied source inputs,
  // never a capture of native RBP-relative slots.
  std::optional<std::uintptr_t> slot0_content, slot1_content;
};

enum class NegotiatedReplyReporterNullPathStatus12004 : std::uint8_t {
  source_unavailable = 0,
  bundle_unavailable,
  required_slot_address_zero,
  required_slot_content_unavailable,
  nonnull_output_branch,
  null_branch_no_external_effects,
};

struct NegotiatedReplyReporterNullPath12004 {
  NegotiatedReplyReporter12004 reporter = NegotiatedReplyReporter12004::rva307B910;
  std::uintptr_t output_bundle_receiver = 0;
  std::uint64_t frame_key = 0;
  bool null_path_source_closed = false;
  bool contents_supplied = false;
  NegotiatedReplyReporterNullPathStatus12004 status =
      NegotiatedReplyReporterNullPathStatus12004::source_unavailable;
  // Bundle words are slot addresses; null means the slot's CONTENT is zero.
  std::optional<std::uintptr_t> slot0_address;
  std::optional<std::uintptr_t> slot0_content;
  std::optional<std::uintptr_t> slot1_address;
  std::optional<std::uintptr_t> slot1_content;
  bool no_external_effects = false;
};

// Read only the exact actual native null-guard qwords in order. No helper,
// formatter, UI sink, destructor, allocator, or reply action is invoked.
// Nonnull branches are output work outside this leaf's effects proof.
// 307BAF0's null path never accesses bundle+8 or the second slot.
NegotiatedReplyReporterNullPath12004 ReadNegotiatedReplyReporterNullPath12004(
    const NegotiatedReplyReporterRequest12004 &request,
    NegotiatedReplyReporterReadMemory12004 read_memory,
    void *read_context) noexcept;

// Pure projection for the caller's existing null output arguments. It leaves
// all native bundle/slot addresses absent. 307BAF0 ignores second content,
// whose actual bundle atom is scope bits rather than a second slot address.
NegotiatedReplyReporterNullPath12004 ProjectNegotiatedReplyReporterNullContents12004(
    const NegotiatedReplyReporterSuppliedContents12004 &input) noexcept;

} // namespace xar::ck3_12004
