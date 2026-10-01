#pragma once

#include "xar_bridge/ck3_12002_family_query_abi.hpp"

namespace xar::ck3_12002 {
// Frozen 1.20.0.2 AE1BA6... native fulfillment / outcome dispatch. Revalidated
// by verify_ck3_12002_family_query.py and verify_ck3_12002_family_fulfill.py.
inline constexpr auto kFamilyCharacterAdultMeasureOffset = family_query_abi::kAdultMeasureOffset;
inline constexpr auto kFamilyCharacterAdultSelectorOffset = family_query_abi::kAdultSelectorOffset;
inline constexpr auto kFamilyAdultThresholdZeroRva = family_query_abi::kAdultThresholdZeroSlotRva;
inline constexpr auto kFamilyAdultThresholdOneRva = family_query_abi::kAdultThresholdOneSlotRva;
inline constexpr auto kFamilyEvaluateAnswerRva = family_query_abi::kEvaluateAnswerRva;
inline constexpr auto kFamilyReadBooleanOptionRva = family_query_abi::kReadBooleanOptionRva;
inline constexpr auto kFamilyGrandWeddingOptionRva = family_query_abi::kGrandWeddingOptionIdSlotRva;
inline constexpr auto kFamilyMatrilinealOptionRva = family_query_abi::kMatrilinealOptionIdSlotRva;
} // namespace xar::ck3_12002
