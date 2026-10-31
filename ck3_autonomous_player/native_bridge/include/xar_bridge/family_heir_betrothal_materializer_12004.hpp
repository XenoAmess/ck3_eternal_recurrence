#pragma once

#include "xar_bridge/family_ruler_default_materializer_12004.hpp"

namespace xar::bridge {

struct FamilyHeirBetrothalPreparedCopy12004 {
  FamilyRulerPreparedContextCopy12004 materialized{};
  bool effective_matrilineal_if_accepted = false;
  friend bool operator==(const FamilyHeirBetrothalPreparedCopy12004 &,
                         const FamilyHeirBetrothalPreparedCopy12004 &) = default;
};

// Only ACTION_PREPARATION/fulfill_betrothal, mirroring current private
// Prepare and ReadCurrentFirstHeirBetrothalActionability callers. The caller
// supplies real owner-thread/frame and previously observed heir/partner.
// This does not establish their current-heir or existing-betrothal identity.
// The caller-owned native context is copied with the existing complete two-pass
// reader, then destroyed before committing output. The private effective
// lineality comes from the current exact character selector/option contract.
// No setter, command constructor, send, inventory or Game query is invoked.
FamilyRulerMaterializeStatus12004 MaterializeFamilyHeirBetrothalContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyHeirBetrothalPreparedCopy12004 &output) noexcept;

// Current private Prepared object, including the real effective lineality
// boolean. It cannot be represented as the RULER public/default null value.
std::string SerializeFamilyHeirBetrothalPreparedContext12004(
    const FamilyHeirBetrothalPreparedCopy12004 &copy);

} // namespace xar::bridge
