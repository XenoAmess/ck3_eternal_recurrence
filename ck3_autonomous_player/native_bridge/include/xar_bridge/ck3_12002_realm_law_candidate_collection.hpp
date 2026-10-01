#pragma once

#include "xar_bridge/ck3_12002_realm_law_active_collection.hpp"
#include "xar_bridge/realm_law_candidate_collection_11906.hpp"

namespace xar::ck3_12002::private_law {

using ck3_11906::private_law::RealmLawCandidateCollectionFailure;
using ck3_11906::private_law::RealmLawCandidateCollectionFailureName;
using ck3_11906::private_law::RealmLawCandidateCollectionRow11906;
using ck3_11906::private_law::RealmLawRelevantGroup11906;
using ck3_11906::private_law::RealmLawCandidateCollection11906;
using ck3_11906::private_law::ObserveRealmLawCandidate11906;

inline constexpr std::uintptr_t kLawGroupDatabaseSingletonRva12002 = 0x5D202F0;
inline constexpr std::uintptr_t kLawGroupDatabaseArrayOffset12002 = 0x50;
inline constexpr std::uintptr_t kLawGroupDatabaseCountOffset12002 = 0x5C;
inline constexpr std::uintptr_t kLawGroupCandidateArrayOffset12002 = 0x58;
inline constexpr std::uintptr_t kLawGroupCandidateCountOffset12002 = 0x64;
inline constexpr std::uintptr_t kLawOwningGroupOffset12002 = 0x40;

bool ReadRealmLawCandidateCollectionWithObserver12002(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    void *observer_context, ObserveRealmLawCandidate11906 observer,
    RealmLawCandidateCollection11906 &output) noexcept;

bool ReadRealmLawCandidateCollection12002(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    RealmLawCandidateCollection11906 &output) noexcept;

} // namespace xar::ck3_12002::private_law
