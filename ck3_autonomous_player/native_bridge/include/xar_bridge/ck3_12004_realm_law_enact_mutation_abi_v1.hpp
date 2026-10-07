#pragma once

#include "xar_bridge/ck3_12002_realm_law_enact_mutation_abi_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004::private_law {

using RealmLawMutationAbiReaderV1 = ck3_12002::private_law::RealmLawMutationAbiReaderV1;
using RealmLawMutationAbiProofV1 = ck3_12002::private_law::RealmLawMutationAbiProofV1;
using RealmLawMutationAbiFailureV1 = ck3_12002::private_law::RealmLawMutationAbiFailureV1;

inline constexpr std::string_view kRealmLawEnactMutationAbi12004V1 =
    "ck3_12004_realm_law_enact_mutation_v1_abi";
// Exact sealed UTF-8 minimum direct-command ABI manifest: GUARD06-SOURCE-SEAL.
inline constexpr std::string_view kRealmLawEnactMutationManifestSha25612004V1 =
    "0B16BD06DA28B553E6243721F88FF24CC6BF10290A903F963E01A150564B6319";

RealmLawMutationAbiProofV1 VerifyRealmLawEnactMutationAbi12004V1(
    const RealmLawMutationAbiReaderV1 &reader,
    std::uintptr_t module_base) noexcept;

} // namespace xar::ck3_12004::private_law
