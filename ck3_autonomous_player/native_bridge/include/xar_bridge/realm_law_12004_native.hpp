#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_realm_law_candidate_collection.hpp"
#include "xar_bridge/ck3_12002_realm_law_final_terms.hpp"
#include "xar_bridge/realm_law_succession_profile_12003.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12004::private_law {

// Actual .4 P0 declared instruction spans, matched by the shared mapper.
// ACTIVE-LAW-MINIMAL20-MAP.json verifies the instruction spans and ordered
// edges; kind has an explicit 40-byte code/40-byte inline-table proof.
// The four enum contents are byte-equal at actual parser RIP targets, captured
// once in FOUR-ENUM-ACTUAL-DATA.json. Runtime qualification remains separate.
inline constexpr std::uintptr_t kRealmLawCandidateKindRva12004 = 0x30B2B20;
inline constexpr std::uintptr_t kRealmLawAlreadyActiveRva12004 = 0x2BA97D0;
inline constexpr std::uintptr_t kRealmLawFinalCanEnactRva12004 = 0x30B1B50;
inline constexpr std::uintptr_t kRealmLawFinalCanEnactReasonRva12004 = 0x30B1CC0;
inline constexpr std::uintptr_t kRealmLawNumericCostRva12004 = 0x30B26B0;
inline constexpr std::uintptr_t kRealmLawReasonDestructorRva12004 = 0x856050;
inline constexpr std::size_t kRealmLawCompiledCostOffset12004 = 0xC40;

// Actual P1 instruction operands and singleton RIP target preserve these
// copied collection layouts. No .2 native admission or locator is reused.
inline constexpr std::uintptr_t kCharacterLawContextOffset12004 = 0x1C0;
inline constexpr std::uintptr_t kLawCollectionOffset12004 = 0x200;
inline constexpr std::uintptr_t kLawNativeKeyOffset12004 = 0x18;
inline constexpr std::uintptr_t kLawGroupDatabaseSingletonRva12004 = 0x5D202F0;
inline constexpr std::uintptr_t kLawGroupDatabaseArrayOffset12004 = 0x50;
inline constexpr std::uintptr_t kLawGroupDatabaseCountOffset12004 = 0x5C;
inline constexpr std::uintptr_t kLawGroupCandidateArrayOffset12004 = 0x58;
inline constexpr std::uintptr_t kLawGroupCandidateCountOffset12004 = 0x64;
inline constexpr std::uintptr_t kLawOwningGroupOffset12004 = 0x40;
inline constexpr std::size_t kRealmLawSuccessionPolicyOffset12004 = 0xBD8;
inline constexpr std::size_t kRealmLawSuccessionPolicyBytes12004 = 0x68;
inline constexpr std::size_t kRealmLawCreatePrimaryTierTitlesOffset12004 = 6;

// Existing value DTOs and callbacks remain shared. Native bindings, collection
// offsets and admission use actual .4 evidence and ck3_12004::kExecutableSha256.
bool ReadRealmLawCandidateCollectionWithObserver12004(
    const ck3_12002::private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t module_base, void *observer_context,
    ck3_12002::private_law::ObserveRealmLawCandidate11906 observer,
    ck3_12002::private_law::RealmLawCandidateCollection11906 &output) noexcept;

ck3_12002::private_law::RealmLawFinalTerms12002Operations
BindRealmLawFinalTermsImage12004(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept;

ck3_12002::private_law::RealmLawFinalTerms12002Result
ReadRealmLawFinalTerms12004(
    const ck3_12002::private_law::RealmLawFinalTerms12002Input &input,
    const ck3_12002::private_law::RealmLawFinalTerms12002Operations &operations) noexcept;

ck3_12003::private_law::RealmLawSuccessionProfile12003
ReadRealmLawSuccessionProfile12004(
    const ck3_12002::private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t native_law, std::string_view actual_executable_sha256) noexcept;

} // namespace xar::ck3_12004::private_law
