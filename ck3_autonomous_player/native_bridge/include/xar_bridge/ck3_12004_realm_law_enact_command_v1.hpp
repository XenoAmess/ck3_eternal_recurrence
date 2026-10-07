#pragma once

#include "xar_bridge/ck3_12002_realm_law_enact_command_v1.hpp"
#include "xar_bridge/ck3_12004_realm_law_enact_mutation_abi_v1.hpp"

namespace xar::ck3_12004::private_law {

using AddLawCommandV1 = ck3_12002::private_law::AddLawCommandV1;
using AddLawCommandOfflineCallsV1 = ck3_12002::private_law::AddLawCommandOfflineCallsV1;
using AddLawCommandAccessV1 = ck3_12002::private_law::AddLawCommandAccessV1;
using AddLawCommandFailureV1 = ck3_12002::private_law::AddLawCommandFailureV1;
using AddLawCommandSubmitResultV1 = ck3_12002::private_law::AddLawCommandSubmitResultV1;

// FUNCTIONS01-SOURCE.json closes these actual .4 entries and the popup/clone
// receiver stores. These are source operands, not an inferred image shift.
inline constexpr std::size_t kAddLawCommandSize12004V1 = 0x30;
inline constexpr std::uint32_t kAddLawCommandSubmitFlags12004V1 = 0x0E;
inline constexpr std::uintptr_t kAddLawCommandPrimaryVtableRva12004V1 = 0x4760108;
inline constexpr std::uintptr_t kAddLawCommandSecondaryVtableRva12004V1 = 0x47601A0;
inline constexpr std::uintptr_t kAddLawCommandValidatorRva12004V1 = 0x288DA20;
inline constexpr std::uintptr_t kAddLawCommandCloneRva12004V1 = 0x2896210;
inline constexpr std::uintptr_t kAddLawCommandDestructorRva12004V1 = 0x9D1560;
inline constexpr std::uintptr_t kRealmLawLockedQueueRva12004V1 = 0x37F06D0;
inline constexpr std::uintptr_t kCommandManagerRva12004V1 = 0x5CC1240;

AddLawCommandV1 BuildAddLawCommand12004V1(
    std::uintptr_t module_base, std::int32_t actor_character_id,
    std::uintptr_t law_address) noexcept;

AddLawCommandSubmitResultV1 SubmitAddLawCommand12004V1(
    const AddLawCommandAccessV1 &access,
    const bridge::RealmLawEnactSubmissionV1 &submission,
    const bridge::RealmLawNativeEnactTargetLeaseV1 &target) noexcept;

} // namespace xar::ck3_12004::private_law
