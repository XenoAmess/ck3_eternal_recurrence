#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002::family_query_abi {

// Frozen 1.20.0.2 Crozier only. verify_ck3_12002_family_query.py binds these
// operands to the actual native instructions; no 1.19 addresses are reused.
inline constexpr std::size_t kFamilyDataOffset = 0x1A8;
inline constexpr std::size_t kBetrothedIdOffset = 0x10;
inline constexpr std::size_t kPrimarySpouseIdOffset = 0x14;
inline constexpr std::size_t kSpouseArrayOffset = 0x20;
inline constexpr std::size_t kAdultMeasureOffset = 0x68;
inline constexpr std::size_t kAdultSelectorOffset = 0x1A1;
inline constexpr std::uintptr_t kAdultThresholdZeroSlotRva = 0x5C6A15C;
inline constexpr std::uintptr_t kAdultThresholdOneSlotRva = 0x5C69D10;
inline constexpr std::uintptr_t kReadBooleanOptionRva = 0x3078880;
inline constexpr std::uintptr_t kMatrilinealOptionIdSlotRva = 0x5D4BDBC;
inline constexpr std::uintptr_t kGrandWeddingOptionIdSlotRva = 0x5D4C0B4;
inline constexpr std::uintptr_t kEvaluateAnswerRva = 0x307BC80;
inline constexpr std::uintptr_t kOutcomeDispatchRva = 0x2503C60;
inline constexpr std::size_t kContextActorIdOffset = 0x2D8;
inline constexpr std::size_t kContextRecipientIdOffset = 0x2DC;
inline constexpr std::size_t kContextSecondaryActorIdOffset = 0x2E0;
inline constexpr std::size_t kContextSecondaryRecipientIdOffset = 0x2E4;
inline constexpr std::size_t kContextIntermediaryIdOffset = 0x2E8;

using ReadBooleanOption = bool (*)(void *, std::uint32_t);
using EvaluateAnswer = std::uint8_t (*)(void *, std::uint8_t, std::uint8_t,
                                      void *, void *);

// Measure is signed int16; threshold is a runtime signed int32 define. Native
// uses signed greater-or-equal, not an assumed age 16 constant.
constexpr bool IsAdult(std::int16_t measure, std::int32_t threshold) noexcept {
  return measure >= threshold;
}

} // namespace xar::ck3_12002::family_query_abi
