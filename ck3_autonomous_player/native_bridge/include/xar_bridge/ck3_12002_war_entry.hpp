#pragma once

#include "xar_bridge/war_entry_assessments_v1.hpp"

namespace xar::ck3_12002 {

// Wire DTOs and synchronous scratch shapes did not change in Crozier. Only
// these shapes are shared with the prior version; no prior version binding is
// used by this adapter. See ck3_1_20_0_2_war_entry.json for exact instruction
// evidence and the remaining paused-live boundary.
using NativeWarEntryActorStateV1 = ck3_11906::NativeWarEntryActorStateV1;
using NativeWarEntryAssessmentOutputV1 = ck3_11906::NativeWarEntryAssessmentOutputV1;
using NativeWarEntryNetworkConfigurationV1 = ck3_11906::NativeWarEntryNetworkConfigurationV1;
using NativeWarEntryActorStateBuilderFunctionV1 = ck3_11906::NativeWarEntryActorStateBuilderFunctionV1;
using NativeWarEntryAssessmentFunctionV1 = ck3_11906::NativeWarEntryAssessmentFunctionV1;
using NativeWarEntryNetworkCollectorFunctionV1 = ck3_11906::NativeWarEntryNetworkCollectorFunctionV1;
using NativeWarEntryEffectiveTargetResolverFunctionV1 = ck3_11906::NativeWarEntryEffectiveTargetResolverFunctionV1;
using WarEntryNativeEnvironmentV1 = ck3_11906::WarEntryNativeEnvironmentV1;
using WarEntryAssessmentAccessV1 = ck3_11906::WarEntryAssessmentAccessV1;
using WarEntryAssessmentsV1Request = ck3_11906::WarEntryAssessmentsV1Request;

inline constexpr std::string_view kWarEntryAssessmentsV1Capability =
    "game.command.query-war-entry-assessments-v1-N";
inline constexpr std::int32_t kWarEntryAssessmentsV1MaximumTargets = 1;
inline constexpr std::int64_t kWarEntryAssessmentsV1FixedPointScale = 100'000;
inline constexpr std::string_view kWarEntryAssessmentsV1StepPrefix =
    "query-war-entry-assessments-v1-";
inline constexpr std::string_view kWarEntryAssessmentsV1ExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kWarEntryAssessmentsV1GameVersion = "1.20.0.2";

inline constexpr std::uintptr_t kWarEntryAssessmentRva = 0x1A23240;
inline constexpr std::uintptr_t kWarEntryActorStateBuilderRva = 0x1A22D30;
inline constexpr std::uintptr_t kWarEntryNetworkCollectorRva = 0x1A24010;
inline constexpr std::uintptr_t kWarEntryEffectiveTargetResolverRva = 0x2C13460;
inline constexpr std::uintptr_t kWarEntryGameStateSlotRva = 0x5C68C50;
inline constexpr std::uintptr_t kWarEntryCharacterStorageSlotRva = 0x5C67568;
inline constexpr std::uintptr_t kWarEntryCharacterFallbackSlotRva = 0x5C67570;
inline constexpr std::uintptr_t kWarEntryActorStateDependencySlotRva = 0x5D1DD50;

WarEntryNativeEnvironmentV1 BindWarEntryNativeEnvironmentV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

game::ReadWarEntryAssessmentsV1Result ReadWarEntryAssessmentsV1(
    const WarEntryNativeEnvironmentV1 &environment,
    const WarEntryAssessmentAccessV1 &access,
    const WarEntryAssessmentsV1Request &request,
    game::WarEntryAssessmentsV1 &output) noexcept;

// Decimal request grammar is build-independent; wire provenance is emitted
// by this build's serializer and must never be inherited from 1.19.
using ck3_11906::EncodeWarEntryAssessmentsV1Step;
using ck3_11906::ParseWarEntryAssessmentsV1Step;

std::string SerializeWarEntryAssessmentsV1(
    const game::WarEntryAssessmentsV1 &result);

} // namespace xar::ck3_12002
