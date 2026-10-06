#pragma once
#include "xar_bridge/army_ordered_besieging_fixed_chunk0_preparation_v1.hpp"

namespace xar::ck3_12002 { struct ArmyBindings; }
namespace xar::game { struct ArmyOrderedBesiegingRefillInputsV1; }
namespace xar::ck3_12003 {
game::ArmyOrderedBesiegingFixedChunk0PreparationInputsV1
ReadOrderedBesiegingFixedChunk0PreparationInputs12003(
    const ck3_12002::ArmyBindings &,
    const game::ArmyOrderedBesiegingRefillInputsV1 &) noexcept;
} // namespace xar::ck3_12003
