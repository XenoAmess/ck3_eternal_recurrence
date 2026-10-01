#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002 {

inline constexpr std::size_t kWarCashCharacterLivingExtensionOffset = 0x1B0;
inline constexpr std::size_t kWarCashCharacterGoldOffset = 0x100;

// The owning-thread snapshot and the private cash query share this actual
// native GetGold source. Negative gold is a real debt value. The stock getter
// returns zero for a missing living extension; a failed identity/read returns
// false and is never published as an observed zero.
bool ReadWarCashTreasury(const CoreBindings &, std::int32_t character_id,
                         std::int64_t &gold_raw) noexcept;

} // namespace xar::ck3_12002
