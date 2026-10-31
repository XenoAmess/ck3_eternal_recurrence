#pragma once

#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"
#include "xar_bridge/ck3_12002_family_outbound.hpp"
#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <optional>
#include <string>
#include <string_view>

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

namespace xar::bridge {

// Published by completed real campaign-root primary held-title data, with
// the existing Bridge revision/connection scope. Never made from request.subject.
struct FamilyPrimaryHeirObservation12004 {
  std::uint32_t character_id = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
};

using ReadFamilyHeirSnapshot12004 = bool (*)(void *, game::Snapshot &) noexcept;
using ReadFamilyHeirRelationship12004 = bool (*)(
    void *, const ck3_12002::FamilyBindings &, std::int32_t,
    ck3_11906::CurrentFirstHeirRelationshipReadV1 &) noexcept;

using ReadFamilyHeirBilateral12004 = bool (*)(
    void *, const ck3_12002::FamilyBindings &, std::int32_t, std::int32_t,
    MarriageProposalBilateralRelationshipV1 &) noexcept;

enum class FamilyHeirOwnerOutcome12004 : std::uint8_t {
  unavailable, invalid_request, frame_changed, identity_changed, observed
};

struct FamilyHeirOwnerResult12004 {
  FamilyHeirOwnerOutcome12004 outcome = FamilyHeirOwnerOutcome12004::unavailable;
  bool frame_observed = false;
  bool identity_observed = false;
  FamilyRulerMaterializeStatus12004 materialize_status = FamilyRulerMaterializeStatus12004::unavailable;
  std::optional<FamilyHeirBetrothalPreparedCopy12004> prepared{};
  FamilyOutgoingStorageCopyStatus12004 storage_status = FamilyOutgoingStorageCopyStatus12004::unavailable;
  FamilyOutgoingStorageCopy12004 storage{};
};

// Value-owned child of the same existing fixed Family mailbox executor.
// Parent, adapter, source observation and this job live through terminal wait
// and reclaim; no mailbox ABI change or new executor permit identity.
struct FamilyHeirOutgoingOwnerJob12004 {
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  std::optional<FamilyPrimaryHeirObservation12004> primary_heir{};
  FamilyMarriageOutgoingRequestV2 request{};
  ck3_12002::FamilyBindings family_bindings{};
  ck3_12002::FamilyOutboundBindings outbound_bindings{};
  FamilyRulerContextAccess12004 context_access{};
  void *snapshot_context = nullptr;
  ReadFamilyHeirSnapshot12004 read_snapshot = nullptr;
  void *relationship_context = nullptr;
  ReadFamilyHeirRelationship12004 read_relationship = nullptr;
  void *bilateral_context = nullptr;
  ReadFamilyHeirBilateral12004 read_bilateral = nullptr;
  FamilyHeirOwnerResult12004 result{};
};

// FIRST_HEIR and fulfill_betrothal use actual independent primary scope.
// Ordinary FIRST_HEIR consumes the full pair bilateral callback; fulfillment
// retains its existing heir relationship predicate, then owned context and
// complete bounded inventory. POST invokes neither identity nor constructor:
// it uses the actual canonical definition and retained request sender.
bool ExecuteFamilyHeirOutgoingOwnerJob12004(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

// Existing generic-v2 query envelope, with the private Prepared bool lineality.
// Actual frame and query chronology are supplied only after terminal/reclaim.
std::string SerializeFamilyHeirOutgoingOwnerResult12004(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &,
    const FamilyMarriageOutgoingFrameV2 &, std::uint64_t query_sequence,
    const FamilyHeirOwnerResult12004 &);

} // namespace xar::bridge

#endif
