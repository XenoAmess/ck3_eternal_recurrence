#pragma once

#include "xar_bridge/ck3_12002_family_outbound.hpp"
#include "xar_bridge/family_ruler_default_materializer_12004.hpp"
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge {

using ReadFamilyOwnerSnapshot12004 = bool (*)(
    void *context, game::Snapshot &output) noexcept;

enum class FamilyRulerOwnerOutcome12004 : std::uint8_t {
  unavailable,
  invalid_request,
  frame_changed,
  observed
};

struct FamilyRulerOwnerResult12004 {
  FamilyRulerOwnerOutcome12004 outcome = FamilyRulerOwnerOutcome12004::unavailable;
  bool frame_observed = false;
  FamilyRulerMaterializeStatus12004 materialize_status =
      FamilyRulerMaterializeStatus12004::unavailable;
  std::optional<FamilyRulerPreparedContextCopy12004> prepared{};
  FamilyOutgoingStorageCopyStatus12004 storage_status =
      FamilyOutgoingStorageCopyStatus12004::unavailable;
  FamilyOutgoingStorageCopy12004 storage{};
};

// Value-owned child of the existing CurrentFirstHeirBetrothalMailboxQueryV1.
// The parent ticket/context/adapter and this optional job stay alive through
// terminal wait and reclaim. No new mailbox layout or executor permit slot.
struct FamilyRulerOutgoingOwnerJob12004 {
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0;
  FamilyMarriageOutgoingRequestV2 request{};
  ck3_12002::ContextBindings context_bindings{};
  ck3_12002::FamilyOutboundBindings outbound_bindings{};
  FamilyRulerContextAccess12004 context_access{};
  void *snapshot_context = nullptr;
  ReadFamilyOwnerSnapshot12004 read_snapshot = nullptr;
  FamilyRulerOwnerResult12004 result{};
};

// Called only inside the existing fixed Family owner callback. Checks its
// real paused stamp and full before==expected/after==before snapshots.
// Only RULER is supported. PREP materializes its real default context, then
// filters the complete inventory by that definition and actual effective actor.
// POST constructs no context and uses only the retained request.sender.
// Missing/changed/unknown-vtable inventory stays whole unavailable, not empty.
// A valid data-unavailable observation returns true; false is null context.
bool ExecuteFamilyRulerOutgoingOwnerJob12004(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Complete current Native command_result/result wire. Caller supplies actual
// frame/query chronology only after parent wait completed+ticket reclaimed.
// Refuses non-observed/invalid/mismatched data; no available payload is made
// from default values. For observed failures, emits typed unavailable data.
std::string SerializeFamilyRulerOutgoingOwnerResult12004(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &request,
    const FamilyMarriageOutgoingFrameV2 &actual_frame,
    std::uint64_t query_sequence, const FamilyRulerOwnerResult12004 &result);

} // namespace xar::bridge
