#pragma once

#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"
#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_11906 {

// Private overload for the query-local child result. The existing public
// relationship/descendants layouts and original serializer remain unchanged.
std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs);

} // namespace xar::ck3_11906
#endif
