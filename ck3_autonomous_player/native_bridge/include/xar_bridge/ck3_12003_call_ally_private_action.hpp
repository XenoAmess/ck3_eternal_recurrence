#pragma once

#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

inline constexpr std::string_view kCallAllySubmitPrivateStep12003 =
    "submit-call-ally-to-war-v1-private";
struct FamilyObligationsMailboxContext12002;
struct CallAllyPrivateActionRequest12003 {
  family_obligations_alliance::CallAllySubmitRequest native_request{};
  std::uint64_t expected_revision = 0;
};

bool ParseCallAllyPrivateActionRequest12003(
    std::string_view payload, CallAllyPrivateActionRequest12003 &) noexcept;

// A queue receipt only. Recipient war participation and resource debit must
// be observed later; the read-only family query remains a separate selector.
std::string SerializeCallAllySubmissionResult12003(
    std::string_view request_id, const FamilyObligationsMailboxContext12002 &);

#endif
} // namespace xar::ck3_12002
