#pragma once

#include "xar_bridge/ck3_12003_current_commander_martial_dto.hpp"

#include <cstdint>

namespace xar::ck3_12003 {

// The caller supplies the existing generation/tag/GetArmyCommander-validated
// actual role receiver. Native28B16B0 index1 reads signed32 Character+DC total
// skill cache; it does not rebuild skills, assign a role or observe a candidate.
CurrentCommanderTotalMartialSnapshot ReadCurrentCommanderTotalMartial(
    std::int32_t actual_character_id, void *validated_current_character,
    std::int32_t (*get_total_skill)(void *, std::int32_t)) noexcept;

} // namespace xar::ck3_12003
