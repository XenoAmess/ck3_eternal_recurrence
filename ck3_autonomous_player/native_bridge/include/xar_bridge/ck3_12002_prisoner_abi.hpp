#pragma once

#include <cstdint>

namespace xar::ck3_12002 {

// Frozen CK3 1.20.0.2 Crozier AE1BA6FF only. The verifier checks native
// call chains, option layout and stock ordering without launching the game.
inline constexpr std::uintptr_t kPrisonerGetInteractionDatabaseRva = 0x89DA60;
inline constexpr std::uintptr_t kPrisonerHashStableKeyRva = 0x3F7E240;
inline constexpr std::uintptr_t kPrisonerLookupInteractionRva = 0xA055E0;
inline constexpr std::uintptr_t kPrisonerGetScriptIdentifierTableRva = 0x3F8A800;
inline constexpr std::uintptr_t kPrisonerLookupScriptIdentifierIdRva = 0x3F8A680;
inline constexpr std::uintptr_t kPrisonerEvaluateAnswerRva = 0x307BC80;
inline constexpr std::uintptr_t kPrisonerClearOptionsRva = 0x3078700;
inline constexpr std::uintptr_t kPrisonerSelectOptionRva = 0x30787E0;

} // namespace xar::ck3_12002
