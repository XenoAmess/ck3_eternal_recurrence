#pragma once

#include "xar_bridge/current_first_heir_child_inputs_json_v1.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_11906 {

// Query-local companion only: the existing household and public snapshot
// layouts remain unchanged.
struct CurrentCharacterConceptionTraitExclusionReadV1 {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "native_conception_traits_binding_unavailable";
  std::optional<bool> blocks_pair_conception{};
};

struct CurrentCharacterConceptionTraitExclusionRowV1 {
  std::int32_t character_id = -1;
  CurrentCharacterConceptionTraitExclusionReadV1 read{};
};

struct CurrentFirstHeirConceptionTraitInputsReadV1 {
  std::vector<CurrentCharacterConceptionTraitExclusionRowV1> rows{};
};

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs,
    const CurrentFirstHeirConceptionTraitInputsReadV1 *conception_trait_inputs);

} // namespace xar::ck3_11906
#endif
