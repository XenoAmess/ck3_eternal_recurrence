#pragma once

#include "xar_bridge/ck3_12002_family_subject.hpp"
#include "xar_bridge/family_child_matrilineal_materializer_12004.hpp"
#include "xar_bridge/family_heir_outgoing_owner_12004.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::bridge {

using FamilyChildOwnerResult12004 = FamilyHeirOwnerResult12004;
using ReadFamilyChildSubject12004 = bool (*)(
    void *, const ck3_12002::FamilySubjectBindings &, std::int32_t,
    ck3_12002::PlayerChildMarriageSubjectRead12002 &) noexcept;

// The full derived child observation is retained. Its base alone omits the
// actual parent-ID predicate and independent selector/adulthood evidence.
struct FamilyChildOutgoingOwnerJob12004 {
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0;
  FamilyMarriageOutgoingRequestV2 request{};
  ck3_12002::FamilyBindings family_bindings{};
  ck3_12002::FamilySubjectBindings subject_bindings{};
  ck3_12002::FamilyOutboundBindings outbound_bindings{};
  FamilyRulerContextAccess12004 context_access{};
  void *snapshot_context = nullptr;
  ReadFamilyHeirSnapshot12004 read_snapshot = nullptr;
  void *subject_context = nullptr;
  ReadFamilyChildSubject12004 read_subject = nullptr;
  FamilyChildOwnerResult12004 result{};
};

bool ExecuteFamilyChildOutgoingOwnerJob12004(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

std::string SerializeFamilyChildOutgoingOwnerResult12004(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &,
    const FamilyMarriageOutgoingFrameV2 &, std::uint64_t query_sequence,
    const FamilyChildOwnerResult12004 &);

} // namespace xar::bridge
#endif
