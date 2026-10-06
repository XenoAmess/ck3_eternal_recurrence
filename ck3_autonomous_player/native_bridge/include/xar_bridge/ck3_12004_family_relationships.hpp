#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_context.hpp"

namespace xar::ck3_12004 {

// Actual .4 windows and Character1A8 -> Family20 -> B02D10 prove these
// offsets. The existing software DTO is retained without any old image binder.
namespace family_relationships_abi {
inline constexpr std::size_t kCharacterFamilyOffset = 0x1A8;
inline constexpr std::size_t kBetrothedIdOffset = 0x10;
inline constexpr std::size_t kPrimarySpouseIdOffset = 0x14;
inline constexpr std::size_t kSpouseIdsOffset = 0x20;
inline constexpr std::size_t kSpouseCapacityOffset = 0x28;
inline constexpr std::size_t kSpouseCountOffset = 0x2C;
} // namespace family_relationships_abi

bool ReadPlayedCharacterRelationships(
    const CoreBindings &core, std::int32_t character_id,
    game::PlayedCharacterRelationships12002 &output) noexcept;

} // namespace xar::ck3_12004
