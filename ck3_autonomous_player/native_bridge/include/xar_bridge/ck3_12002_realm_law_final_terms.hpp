#pragma once

#include "xar_bridge/realm_law_final_terms_11906.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002::private_law {

inline constexpr std::string_view kRealmLawFinalTermsExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kRealmLawCandidateKindRva = 0x30B2B40;
inline constexpr std::uintptr_t kRealmLawAlreadyActiveRva = 0x2BA97F0;
inline constexpr std::uintptr_t kRealmLawFinalCanEnactRva = 0x30B1B70;
inline constexpr std::uintptr_t kRealmLawFinalCanEnactReasonRva = 0x30B1CE0;
inline constexpr std::uintptr_t kRealmLawNumericCostRva = 0x30B26D0;
inline constexpr std::uintptr_t kRealmLawReasonDestructorRva = 0x856050;
inline constexpr std::size_t kRealmLawCompiledCostOffset = 0xC40;

// The value DTO is shared with the legacy transport; the native offsets are not.
using RealmLawFinalTerms12002Input = bridge::RealmLawFinalTerms11906Input;
using RealmLawFinalTerms12002Status = bridge::RealmLawFinalTerms11906Status;

struct RealmLawFinalTerms12002Operations {
  bridge::RealmLawFinalTerms11906Operations terms{};
  bool (*full_can_enact_with_reason)(const void *, const void *, void *) = nullptr;
  void (*destroy_native_reason)(void *) = nullptr;
};

struct RealmLawFinalTerms12002Result {
  bridge::RealmLawFinalTerms11906Result terms{};
  bool native_reason_available = false;
  std::string native_reason{};
};

RealmLawFinalTerms12002Operations BindRealmLawFinalTermsImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Copies all ten signed q100000 costs, including a blocked candidate, and the
// full native reason before releasing the engine-owned string allocation.
RealmLawFinalTerms12002Result ReadRealmLawFinalTerms12002(
    const RealmLawFinalTerms12002Input &input,
    const RealmLawFinalTerms12002Operations &operations) noexcept;

} // namespace xar::ck3_12002::private_law
