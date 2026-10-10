#pragma once

#include "xar_bridge/prisoner_answer_helpers_12004.hpp"

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kPrisonerControlCollectionSlotRva12004 = 0x5C68C50;
inline constexpr std::uintptr_t kPrisonerControlDebugObjectRva12004 = 0x5D1E330;
inline constexpr std::uintptr_t kPrisonerControlDebugGuardRva12004 = 0x5D1E370;

struct PrisonerControlMembershipRaw12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::uint32_t> context_2d8_raw_u32;
  std::optional<std::uintptr_t> instance, collection_object, list_data;
  std::optional<std::int32_t> list_count_i32;
  // The actual find stops at its first match; unread later elements are not
  // required. If no match is copied, the complete count must be observed.
  std::vector<std::uint32_t> copied_prefix;
  std::string unavailable_reason;
};

PrisonerControlMembershipRaw12004 ReadPrisonerControlMembershipRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &,
    const PrisonerQuoteSourceFrame12004 &,
    std::optional<std::uint32_t> context_2d8_raw_u32);
PrisonerAnswerByteChild12004 ProjectPrisonerControlMembership12004(
    const PrisonerControlMembershipRaw12004 &);

// A copied literal signed DWORD from the current query thread's GS:[58]
// first TLS block+10, with the existing complete source frame. This is never
// frame.proof_epoch or a revision converted into a TLS epoch.
struct PrisonerControlTlsEpoch12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::int32_t> literal_tls_epoch_i32;
  bool copied_from_current_query_thread = false;
};

struct PrisonerControlDebugRaw12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t static_object_identity = 0;
  std::optional<std::int32_t> initialization_guard_i32;
  std::optional<std::uint8_t> observed_byte0, observed_byte1;
};

PrisonerControlDebugRaw12004 ReadPrisonerControlDebugRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &,
    const PrisonerQuoteSourceFrame12004 &);
PrisonerAnswerDebugFlags12004 ProjectPrisonerControlDebugFlags12004(
    const PrisonerControlDebugRaw12004 &,
    const std::optional<PrisonerControlTlsEpoch12004> &current_thread_epoch);

struct PrisonerAnswerControlPackage12004 {
  PrisonerControlMembershipRaw12004 membership_raw;
  PrisonerControlDebugRaw12004 debug_raw;
  PrisonerAnswerByteChild12004 id_2baa6f0;
  PrisonerAnswerDebugFlags12004 debug_a75d00;
};

// Read-only child package for 39's mode branch and 35's unique selected query.
// Neither initializer, native find nor either original helper is invoked.
PrisonerAnswerControlPackage12004 ReadPrisonerAnswerControlPackage12004(
    const PrisonerQuoteReadOnlyAccess12004 &,
    const PrisonerQuoteSourceFrame12004 &,
    std::optional<std::uint32_t> context_2d8_raw_u32,
    const std::optional<PrisonerControlTlsEpoch12004> &current_thread_epoch =
        std::nullopt);

} // namespace xar::ck3_12004
