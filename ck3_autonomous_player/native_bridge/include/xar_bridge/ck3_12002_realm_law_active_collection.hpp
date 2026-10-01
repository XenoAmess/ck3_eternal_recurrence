#pragma once

#include "xar_bridge/realm_law_active_collection_11906.hpp"

namespace xar::ck3_12002::private_law {

// Value contracts are deliberately shared; only the native source layout and
// admitted build change. No 1.19 native reader is called from these providers.
using ck3_11906::private_law::RealmLawActiveCollection;
using ck3_11906::private_law::RealmLawActiveCollectionAccess;
using ck3_11906::private_law::RealmLawActiveCollectionFailure;
using ck3_11906::private_law::RealmLawActiveCollectionFailureName;
using ck3_11906::private_law::RealmLawActiveKey;
using ck3_11906::private_law::ReadRealmLawActiveMemory;
using ck3_11906::private_law::kRealmLawActiveCollectionKeyCapacity;
using ck3_11906::private_law::kRealmLawActiveCollectionMaximumLaws;

inline constexpr std::string_view kRealmLawActiveCollectionExeSha25612002 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kCharacterLawContextOffset12002 = 0x1C0;
inline constexpr std::uintptr_t kLawCollectionOffset12002 = 0x200;
inline constexpr std::uintptr_t kLawNativeKeyOffset12002 = 0x18;

bool ReadRealmLawActiveCollection12002(
    const RealmLawActiveCollectionAccess &access,
    RealmLawActiveCollection &output) noexcept;

bool ReadRealmLawNativeKey12002(
    const RealmLawActiveCollectionAccess &access,
    std::uintptr_t key_storage_address,
    RealmLawActiveKey &output) noexcept;

} // namespace xar::ck3_12002::private_law
