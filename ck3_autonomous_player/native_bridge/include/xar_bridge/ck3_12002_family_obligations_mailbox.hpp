#pragma once

#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

struct FamilyObligationsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  family_obligations_lineage::Bindings lineage_bindings{};
  FamilyObligationsBreakBindingsV1 break_bindings{};
  family_obligations_alliance::Bindings alliance_bindings{};
  FamilyObligationsObservation12002 observation{};
  bool call_ally_submission = false;
  family_obligations_alliance::CallAllySubmitRequest call_ally_request{};
  family_obligations_alliance::CallAllySubmitReceipt call_ally_receipt{};
  CommandSubmitResult call_ally_result = CommandSubmitResult::unavailable;
  std::string failure;
  bool completed = false;
};

bool IsFamilyObligationsPrivateStep12002(std::string_view step) noexcept;
bool ParseFamilyObligationsPrivateRequest12002(
    std::string_view payload, FamilyObligationsRequest12002 &) noexcept;
bool ExecuteFamilyObligationsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

bool HandleFamilyObligationsPrivate12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

#endif
} // namespace xar::ck3_12002
