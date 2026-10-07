#pragma once

#include "xar_bridge/ck3_12003_steward_develop_county.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Existing software environment, access and DTOs retain their original shape.
// The tail council12004 member carries the independent actual .4 role profile.
using StewardDevelopCountyEnvironment12004 =
    ck3_12003::StewardDevelopCountyEnvironment12003;
using StewardDevelopCountyAccess12004 =
    ck3_12003::StewardDevelopCountyAccess12003;

inline constexpr std::string_view kDevelopMaterialBackend12004 =
    "ck3-1.20.0.4-native-steward-develop-county-material-v1";
inline constexpr std::uintptr_t kStewardTaskTypeDatabaseSlotRva12004 = 0x5C671D8;
inline constexpr std::uintptr_t kStewardTaskTypeFallbackSlotRva12004 = 0x5D1F900;
inline constexpr std::uintptr_t kStewardTitleStorageSlotRva12004 = 0x5D1DAF8;
inline constexpr std::uintptr_t kStewardTitleFallbackSlotRva12004 = 0x5D1DAE0;
inline constexpr std::uintptr_t kStewardHashRva12004 = 0x3F7E220;
inline constexpr std::uintptr_t kStewardTaskTypeLookupRva12004 = 0xCF1E80;
inline constexpr std::uintptr_t kStewardImmediateLiegeRva12004 = 0x28BFC50;
inline constexpr std::uintptr_t kStewardCapitalProvinceRva12004 = 0x28B1CB0;
inline constexpr std::uintptr_t kStewardIsHumanRva12004 = 0x2BAA6F0;
inline constexpr std::uintptr_t kStewardShownRva12004 = 0x31AC790;
inline constexpr std::uintptr_t kStewardValidRva12004 = 0x31AC660;
inline constexpr std::uintptr_t kStewardTargetValidRva12004 = 0x2C48950;
inline constexpr std::uintptr_t kStewardGrowthRva12004 = 0x24CF8E0;
inline constexpr std::uintptr_t kStewardDecayRva12004 = 0x24CFB30;
inline constexpr std::uintptr_t kStewardCurrentProgressRva12004 = 0x31AB500;
inline constexpr std::uintptr_t kStewardMaximumProgressRva12004 = 0x31AB820;
inline constexpr std::uintptr_t kStewardProduceTargetsRva12004 = 0x2C48E60;

// Address calculation and selected-profile checks only; neither calls CK3.
StewardDevelopCountyEnvironment12004 BindStewardDevelopCounty12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool IsStewardDevelopCountyEnvironment12004(
    const StewardDevelopCountyEnvironment12004 &environment) noexcept;
game::ReadStewardDevelopCountyCandidatesResultV1 ReadStewardDevelopCounty12004(
    const StewardDevelopCountyEnvironment12004 &environment,
    const StewardDevelopCountyAccess12004 &access,
    const ck3_11906::StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept;

// Explicit actual .4 provenance; the old serializer's defaults stay .3.
std::string SerializeStewardDevelopCountyMaterial12004(
    const StewardDevelopCountyEnvironment12004 &environment,
    const game::StewardDevelopCountyCandidatesV1 &value);
std::string SerializeStewardDevelopCountyQueryResult12004(
    const StewardDevelopCountyEnvironment12004 &environment,
    std::string_view request_id, std::uint64_t query_sequence,
    const game::StewardDevelopCountyCandidatesV1 &value);

} // namespace xar::ck3_12004
