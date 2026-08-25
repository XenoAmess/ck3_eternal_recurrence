#include "xar_bridge/combat_v3.hpp"

#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::int64_t kFixedScale = 100'000;
constexpr std::int32_t kMissingScriptIdentifier = 12;
constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::int32_t kMaximumRows = 65'536;
constexpr std::size_t kMaximumKeyBytes = 512;

constexpr std::uintptr_t kCharacterStoreSlot = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackSlot = 0x570C138;
constexpr std::uintptr_t kPublicArmyStoreSlot = 0x570CC80;
constexpr std::uintptr_t kSupplyUnitStoreSlot = 0x570CC88;
constexpr std::uintptr_t kSupplyUnitFallbackSlot = 0x570CC68;
constexpr std::uintptr_t kInternalArmyStoreSlot = 0x570C730;
constexpr std::uintptr_t kInternalArmyFallbackSlot = 0x570C720;
constexpr std::uintptr_t kRegimentStoreSlot = 0x57BF4C8;
constexpr std::uintptr_t kRegimentFallbackSlot = 0x57BF4C0;
constexpr std::uintptr_t kHouseStoreSlot = 0x570C408;
constexpr std::uintptr_t kHouseFallbackSlot = 0x570C400;
constexpr std::uintptr_t kDynastyStoreSlot = 0x570C748;
constexpr std::uintptr_t kDynastyFallbackSlot = 0x570C700;
constexpr std::uintptr_t kCultureStoreSlot = 0x570CB80;
constexpr std::uintptr_t kCultureFallbackSlot = 0x570CB78;
constexpr std::uintptr_t kFaithStoreSlot = 0x570C728;
constexpr std::uintptr_t kFaithFallbackSlot = 0x570C238;
constexpr std::uintptr_t kReligionStoreSlot = 0x570C760;
constexpr std::uintptr_t kReligionFallbackSlot = 0x570C6E0;
constexpr std::uintptr_t kAccoladeStoreSlot = 0x57BF1E0;
constexpr std::uintptr_t kAccoladeFallbackSlot = 0x57BF198;
constexpr std::uintptr_t kCourtPositionStoreSlot = 0x570C5F8;
constexpr std::uintptr_t kCourtPositionFallbackSlot = 0x570C5F0;
constexpr std::uintptr_t kInnovationDatabaseSlot = 0x570C7A8;
constexpr std::uintptr_t kInnovationFallbackSlot = 0x57C04E0;
constexpr std::uintptr_t kTraditionDatabaseSlot = 0x570C7A0;
constexpr std::uintptr_t kTraditionFallbackSlot = 0x57BF050;
constexpr std::uintptr_t kMaaBaseTypeRegistrySlot = 0x570C120;
constexpr std::uintptr_t kCourtPositionTypeDatabaseSlot = 0x570BFE0;
constexpr std::uintptr_t kCourtPositionTypeFallbackSlot = 0x570C618;
constexpr std::uintptr_t kGameRuleSelectionServiceSlot = 0x5754B48;
constexpr std::uintptr_t kGameRuleTokenRegistrySlot = 0x57D3CE8;
constexpr std::uintptr_t kGameRuleTokenFallbackSlot = 0x57D7430;

constexpr std::uintptr_t kTraitDatabaseRva = 0x8318F0;
constexpr std::uintptr_t kCharacterHasTraitRva = 0x260F740;
constexpr std::uintptr_t kCharacterTraitTracksRva = 0x260F640;
constexpr std::uintptr_t kTraitTrackIndexRva = 0x2CAFFD0;
constexpr std::uintptr_t kCharacterLiegeRva = 0x2613480;
constexpr std::uintptr_t kDynastyPerkDatabaseRva = 0xC8CF40;
constexpr std::uintptr_t kCharacterPerkDatabaseRva = 0x88EC20;
constexpr std::uintptr_t kCharacterPerksRva = 0x2669170;
constexpr std::uintptr_t kCultureHasParameterRva = 0x22C5800;
constexpr std::uintptr_t kCanBeAcclaimedRva = 0x28A4870;
constexpr std::uintptr_t kAccoladeHasParameterRva = 0x251CB60;
constexpr std::uintptr_t kAccoladeValidateRva = 0x251C200;
constexpr std::uintptr_t kVariableContextForScopeRva = 0x3329A40;
constexpr std::uintptr_t kGetScriptIdentifierTableRva = 0x3B971A0;
constexpr std::uintptr_t kLookupVariableIdentifierRva = 0x3B97020;
constexpr std::uintptr_t kVariableIdentifierNameRva = 0x3B97090;
constexpr std::uintptr_t kLookupScriptIdentifierRva = 0x3B588E0;
constexpr std::uintptr_t kScriptIdentifierNameRva = 0x3B58970;
constexpr std::uintptr_t kCharacterModifierDatabaseRva = 0x88F370;
constexpr std::uintptr_t kCharacterModifierLookupRva = 0xA41F10;
constexpr std::uintptr_t kCharacterModifierFallbackSlot = 0x570C968;
constexpr std::uintptr_t kCharacterGovernmentRva = 0x26165B0;
constexpr std::uintptr_t kFaithHostilityRva = 0x24EDB20;
constexpr std::uintptr_t kRuleSettingKeyHashRva = 0x3B8B000;
constexpr std::uintptr_t kLookupRuleSettingTokenRva = 0x32A3350;
constexpr std::uintptr_t kCombatRuleDatabaseRva = 0x88E320;
constexpr std::uintptr_t kSupplyAdvantageSelectorRva = 0x23049E0;
constexpr std::uintptr_t kDebtAdvantageSelectorRva = 0x28DBB70;
constexpr std::uintptr_t kResolveRealmTreasuryRva = 0x969640;
constexpr std::uintptr_t kFaithDoctrineParameterRva = 0x24EE100;
constexpr std::uintptr_t kReadProvinceModifierRva = 0x2917C40;
constexpr std::uintptr_t kReadModifierValueRva = 0x2940D50;
constexpr std::uintptr_t kProvinceHasHoldingRva = 0xBC24E0;
constexpr std::uintptr_t kModifierSetHasFlagRva = 0x20ABA00;
constexpr std::uintptr_t kConstructCombatSideRva = 0x23C7D30;
constexpr std::uintptr_t kPopulateCombatSideRva = 0x23C9100;
constexpr std::uintptr_t kSelectBattleCommanderRva = 0x23C8A60;
constexpr std::uintptr_t kRefreshCombatSideStrengthRva = 0x23CB840;
constexpr std::uintptr_t kReadCombatSideStrengthRva = 0x23CC340;
constexpr std::uintptr_t kDestroyCombatSideRva = 0x2303B00;
constexpr std::uintptr_t kResolveCombatAdvantageRva = 0x2308D50;
constexpr std::uintptr_t kReadSideDynamicAdvantageRva = 0x2307CB0;
constexpr std::uintptr_t kReadCommanderDynamicAdvantageRva = 0x2307680;
constexpr std::uintptr_t kReadSideModifierAdvantageRva = 0x2307230;
constexpr std::uintptr_t kReadCombatRelationKindRva = 0x2307080;
constexpr std::uintptr_t kCombatSideSavedVariablesEnabledRva = 0x4F3CF81;
constexpr std::uintptr_t kSupplyThresholdDataRva = 0x4F61F08;
constexpr std::uintptr_t kSupplyThresholdCountRva = 0x4F61F14;

constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kCombatShellSize = 0x718;
constexpr std::size_t kCombatSideSize = 0x348;
constexpr std::size_t kCombatSide0Offset = 0x20;
constexpr std::size_t kCombatSide1Offset = 0x368;
constexpr std::size_t kCombatSideArmyIdsOffset = 0x10;
constexpr std::size_t kCombatSideArmyIdsCapacityOffset = 0x18;
constexpr std::size_t kCombatSideArmyIdsCountOffset = 0x1C;
constexpr std::size_t kCombatSideKnightEntriesOffset = 0x40;
constexpr std::size_t kCombatSideKnightEntriesCapacityOffset = 0x48;
constexpr std::size_t kCombatSideKnightEntriesCountOffset = 0x4C;
constexpr std::size_t kCombatSideKnightEntryStride = 0x60;
constexpr std::size_t kCombatSideKnightRegimentIdOffset = 0x08;
constexpr std::size_t kCombatTargetProvinceOffset = 0x6B8;
constexpr std::size_t kCombatBaseAdvantageOffset = 0x6C8;
constexpr std::size_t kCombatSide0RollOffset = 0x6D0;
constexpr std::size_t kCombatSide1RollOffset = 0x6D4;
constexpr std::size_t kCombatHoldingDefenderOffset = 0x6FE;
constexpr std::size_t kCombatResolvedAdvantageOffset = 0x710;
constexpr std::size_t kCombatSideEffectLedgerOffset = 0x78;
constexpr std::size_t kCombatSideEffectLedgerAllocatorOffset = 0x88;
constexpr std::size_t kCombatSideLocalContextOffset = 0xC8;
constexpr std::size_t kCombatSideModifierAggregatorOffset = 0x110;
constexpr std::size_t kCombatSideGatheringOffset = 0x340;
constexpr std::size_t kLocalPopulationContextSize = 0x50;
constexpr std::size_t kLocalPopulationEntriesOffset = 0x38;
constexpr std::size_t kLocalPopulationAllocatorOffset = 0x48;
constexpr std::size_t kEffectAdvantagePointsOffset = 0x38;
constexpr std::size_t kEffectStableKeyOffset = 0x18;
constexpr std::size_t kTerrainAttackerEffectOffset = 0x40;
constexpr std::size_t kTerrainDefenderEffectOffset = 0x48;
constexpr std::size_t kCombatRuleGatheringArmyOffset = 0xF18;
constexpr std::size_t kCombatRuleHoldingDefenderOffset = 0xF28;
constexpr std::size_t kCombatRuleSupplySuppliedOffset = 0xF38;
constexpr std::size_t kCombatRuleSupplyRunningLowOffset = 0xF48;
constexpr std::size_t kCombatRuleSupplyStarvingOffset = 0xF58;
constexpr std::size_t kCombatRuleUnreformedFaithOffset = 0xF68;
constexpr std::size_t kCombatRuleNoIncomeDebtOffset = 0xF78;
constexpr std::size_t kCombatRuleOwnerDebtDataOffset = 0xFE8;
constexpr std::size_t kCombatRuleOwnerDebtCountOffset = 0xFF4;
constexpr std::size_t kCombatRuleTreasuryDebtDataOffset = 0x1090;
constexpr std::size_t kCombatRuleTreasuryDebtCountOffset = 0x109C;
constexpr std::size_t kCombatRuleAdjacencyAttackerOffset = 0xF88;
constexpr std::size_t kCombatRuleAdjacencyDefenderOffset = 0xFB8;

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;

constexpr std::string_view kCandidateSourceProofPolicy =
    "ccombat_side_commanders_then_knights_native_source_equivalence_v1";

constexpr std::array<std::string_view, 56> kTraitOrGroupKeys{
    "ambitious",
    "athletic",
    "berserker",
    "brave",
    "calm",
    "cautious_leader",
    "compassionate",
    "content",
    "craven",
    "desert_warrior",
    "disfigured",
    "education_martial_1",
    "education_martial_2",
    "education_martial_3",
    "education_martial_4",
    "education_martial_5",
    "education_martial_prowess_1",
    "education_martial_prowess_2",
    "education_martial_prowess_3",
    "education_martial_prowess_4",
    "flexible_leader",
    "forest_fighter",
    "giant",
    "holy_warrior",
    "impatient",
    "incapable",
    "intellect_good_1",
    "intellect_good_2",
    "intellect_good_3",
    "jungle_stalker",
    "lazy",
    "lifestyle_blademaster",
    "maimed",
    "nomadic_philosophy",
    "one_eyed",
    "one_legged",
    "open_terrain_expert",
    "patient",
    "physique_good",
    "reckless",
    "rough_terrain_expert",
    "sadistic",
    "scholar",
    "shieldmaiden",
    "shrewd",
    "strong",
    "temperate",
    "winter_soldier",
    "wrathful",
    "zealous",
    "aggressive_attacker",
    "wounded_1",
    "wounded_2",
    "wounded_3",
    "fragile_bones",
    "tourney_participant",
};

constexpr std::array<std::string_view, 3> kPhysiqueGoodTraitKeys{
    "physique_good_1", "physique_good_2", "physique_good_3"};

constexpr std::array<std::string_view, 12> kInnovationKeys{
    "innovation_quilted_armor",      "innovation_sarawit",
    "innovation_legionnaires",       "innovation_arched_saddle",
    "innovation_valets",             "innovation_tiefutu",
    "innovation_advanced_bowmaking", "innovation_repeating_crossbow",
    "innovation_war_camels",         "innovation_elephantry",
    "innovation_gunpowder",          "innovation_fire_medicine",
};

constexpr std::array<std::string_view, 14> kTraditionKeys{
    "tradition_fp1_coastal_warriors",
    "tradition_hird",
    "tradition_futuwaa",
    "tradition_druzhina",
    "tradition_khadga_puja",
    "tradition_garuda_warriors",
    "tradition_himalayan_settlers",
    "tradition_mubarizuns",
    "tradition_burman_royal_army",
    "tradition_mountaineer_ruralism",
    "tradition_caucasian_wolves",
    "tradition_roman_legacy",
    "tradition_ep3_audacious_cadets",
    "tradition_ep3_imperial_tagmata",
};

constexpr std::array<std::string_view, 10> kCultureParameterKeys{
    "knights_slightly_more_prone_to_injury",
    "blademaster_traits_more_common",
    "unlock_zhanmadao",
    "unlock_burenjia",
    "unlock_maa_cataphract_archers",
    "unlock_maa_black_armor_cavalry",
    "unlock_maa_horse_archers",
    "unlock_maa_mangudai",
    "unlock_emishi_horse_archers_units",
    "unlock_mounted_samurai_units",
};

constexpr std::array<std::string_view, 13> kAttributeUnlockKeys{
    "skirmisher", "archer",      "crossbowmen", "pike",      "vanguard",
    "outrider",   "lancer",      "camelry",     "elephantry", "horse_archer",
    "gunpowder",  "fanatic",     "valiant",
};

constexpr std::array<std::string_view, 6> kAccoladeParameterKeys{
    "accolade_defends_family_low",
    "accolade_defends_family_medium",
    "accolade_defends_family_high",
    "accolade_increase_hostile_knight_death_low",
    "accolade_increase_hostile_knight_death_medium",
    "accolade_increase_hostile_knight_death_high",
};

constexpr std::array<std::string_view, 10> kMaaBaseTypeKeys{
    "skirmishers",      "archers",          "pikemen",
    "heavy_infantry",   "light_cavalry",    "heavy_cavalry",
    "camel_cavalry",    "elephant_cavalry", "archer_cavalry",
    "gunpowder",
};

constexpr std::array<std::string_view, 3> kCrossbowTypeKeys{
    "crossbowmen", "shenbigong", "accolade_maa_crossbowers"};

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

template <typename T>
void StoreAt(void *base, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

std::uintptr_t ModuleBase() noexcept {
  return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
}

bool ReadMsvcString(const void *storage, std::string &output) noexcept {
  if (storage == nullptr) {
    return false;
  }
  const auto size = LoadAt<std::size_t>(storage, 0x10);
  const auto capacity = LoadAt<std::size_t>(storage, 0x18);
  if (size > capacity || size > kMaximumKeyBytes) {
    return false;
  }
  const char *data = capacity < 16 ? static_cast<const char *>(storage)
                                   : LoadAt<const char *>(storage, 0);
  if (size != 0 && data == nullptr) {
    return false;
  }
  output.assign(data == nullptr ? "" : data, size);
  return true;
}

bool StableKeyEquals(const void *object, std::size_t offset,
                     std::string_view expected) noexcept {
  std::string actual;
  return object != nullptr &&
         ReadMsvcString(static_cast<const std::byte *>(object) + offset,
                        actual) &&
         actual == expected;
}

void *ResolveComponent(std::uintptr_t module, std::uintptr_t store_slot_rva,
                       std::int32_t full_id,
                       std::size_t identity_offset) noexcept {
  if (module == 0 || full_id == -1) {
    return nullptr;
  }
  void *const store = *reinterpret_cast<void **>(module + store_slot_rva);
  if (store == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(store, kStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(store, kStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > kMaximumComponents ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const object = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kStorageSlotStride +
                 kStorageObjectOffset);
  return object != nullptr &&
                 LoadAt<std::int32_t>(object, identity_offset) == full_id
             ? object
             : nullptr;
}

bool IsFallback(std::uintptr_t module, std::uintptr_t fallback_slot_rva,
                const void *object) noexcept {
  return object != nullptr &&
         object == *reinterpret_cast<void **>(module + fallback_slot_rva);
}

using BoolPredicate = bool (*)(void *);

bool VcallBool(void *object, std::size_t slot_offset,
               bool &value) noexcept {
  if (object == nullptr) {
    return false;
  }
  void *const vtable = LoadAt<void *>(object, 0);
  const auto address =
      vtable == nullptr ? 0 : LoadAt<std::uintptr_t>(vtable, slot_offset);
  if (address == 0) {
    return false;
  }
  value = reinterpret_cast<BoolPredicate>(address)(object);
  return true;
}

bool ValidSpan(const void *data, std::int32_t count,
               std::int32_t maximum = kMaximumRows) noexcept {
  return count >= 0 && count <= maximum && (count == 0 || data != nullptr);
}

void AppendCanonicalInt32V3(std::string &output, std::int32_t value) {
  std::array<char, 16> buffer{};
  const auto [end, error] =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (error != std::errc{}) {
    throw std::runtime_error("candidate source integer serialization failed");
  }
  output.append(buffer.data(), end);
}

bool Sha256UpperV3(std::string_view input, std::string &output) {
  output.clear();
  if (input.size() > std::numeric_limits<ULONG>::max()) {
    return false;
  }
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool succeeded = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0 || copied != sizeof(object_size)) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0 ||
        BCryptHashData(
            hash,
            reinterpret_cast<PUCHAR>(const_cast<char *>(input.data())),
            static_cast<ULONG>(input.size()), 0) < 0 ||
        BCryptFinishHash(hash, digest.data(),
                         static_cast<ULONG>(digest.size()), 0) < 0) {
      break;
    }
    succeeded = true;
  } while (false);
  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  if (!succeeded) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  output.resize(digest.size() * 2);
  for (std::size_t index = 0; index < digest.size(); ++index) {
    output[index * 2] = digits[digest[index] >> 4U];
    output[index * 2 + 1] = digits[digest[index] & 0x0FU];
  }
  return true;
}

bool CandidateSourceSequenceDigestV3(
    std::int32_t side_index,
    const std::vector<CombatPhaseCandidateSourceRowV3> &rows,
    std::string &output) {
  if (side_index < 0 || side_index > 1 ||
      rows.size() > static_cast<std::size_t>(kMaximumRows)) {
    return false;
  }
  std::string canonical;
  canonical.reserve(192 + rows.size() * 112);
  canonical += "{\"policy\":\"";
  canonical += kCandidateSourceProofPolicy;
  canonical += "\",\"side_index\":";
  AppendCanonicalInt32V3(canonical, side_index);
  canonical += ",\"ordered_sources\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      canonical += ',';
    }
    const auto &row = rows[index];
    if ((row.role != "commander" && row.role != "knight") ||
        row.source_army_id <= 0 || row.character_id <= 0 ||
        (row.role == "commander" && row.source_regiment_id != -1) ||
        (row.role == "knight" && row.source_regiment_id <= 0)) {
      return false;
    }
    canonical += "{\"role\":\"";
    canonical += row.role;
    canonical += "\",\"source_army_id\":";
    AppendCanonicalInt32V3(canonical, row.source_army_id);
    canonical += ",\"source_regiment_id\":";
    if (row.source_regiment_id == -1) {
      canonical += "null";
    } else {
      AppendCanonicalInt32V3(canonical, row.source_regiment_id);
    }
    canonical += ",\"character_id\":";
    AppendCanonicalInt32V3(canonical, row.character_id);
    canonical += '}';
  }
  canonical += "]}";
  return Sha256UpperV3(canonical, output);
}

void *FindUniqueDatabaseObject(void *database, std::string_view key,
                               std::size_t key_offset = 0x18) noexcept {
  if (database == nullptr) {
    return nullptr;
  }
  void *const data = LoadAt<void *>(database, 0x68);
  const auto count = LoadAt<std::int32_t>(database, 0x74);
  if (!ValidSpan(data, count)) {
    return nullptr;
  }
  void *match = nullptr;
  for (std::int32_t index = 0; index < count; ++index) {
    void *const object =
        LoadAt<void *>(data, static_cast<std::size_t>(index) * 8);
    if (StableKeyEquals(object, key_offset, key)) {
      if (match != nullptr) {
        return nullptr;
      }
      match = object;
    }
  }
  return match;
}

bool ContainsPointer(const void *data, std::int32_t count,
                     const void *needle) noexcept {
  if (!ValidSpan(data, count)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    if (LoadAt<const void *>(data, static_cast<std::size_t>(index) * 8) ==
        needle) {
      return true;
    }
  }
  return false;
}

struct NativeStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t pad = 0;
};

struct NativeStringView64 {
  const char *data = nullptr;
  std::int64_t size = 0;
};

using LookupScriptIdentifier = std::int32_t (*)(const NativeStringView64 *);
using ScriptIdentifierName = const std::string *(*)(std::int32_t);
using GetScriptIdentifierTable = void *(*)();
using LookupVariableIdentifier = std::int32_t *(*)(
    void *, std::int32_t *, const NativeStringView32 *);
using VariableIdentifierName = const std::string *(*)(void *, std::int32_t);

bool ResolveScriptIdentifier(std::uintptr_t module, std::string_view key,
                             std::int32_t &identifier) noexcept {
  const NativeStringView64 view{key.data(),
                                static_cast<std::int64_t>(key.size())};
  identifier = reinterpret_cast<LookupScriptIdentifier>(
      module + kLookupScriptIdentifierRva)(&view);
  if (identifier == kMissingScriptIdentifier || identifier < 0) {
    return false;
  }
  const auto *const name = reinterpret_cast<ScriptIdentifierName>(
      module + kScriptIdentifierNameRva)(identifier);
  return name != nullptr && *name == key;
}

bool ResolveVariableIdentifier(std::uintptr_t module, std::string_view key,
                               std::int32_t &identifier) noexcept {
  void *const table = reinterpret_cast<GetScriptIdentifierTable>(
      module + kGetScriptIdentifierTableRva)();
  if (table == nullptr ||
      key.size() > static_cast<std::size_t>(
                       std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  const NativeStringView32 view{key.data(),
                                static_cast<std::int32_t>(key.size()), 0};
  identifier = -1;
  if (reinterpret_cast<LookupVariableIdentifier>(
          module + kLookupVariableIdentifierRva)(table, &identifier,
                                                  &view) == nullptr ||
      identifier < 0) {
    return false;
  }
  const auto *const name = reinterpret_cast<VariableIdentifierName>(
      module + kVariableIdentifierNameRva)(table, identifier);
  return name != nullptr && *name == key;
}

bool SameSnapshotFrame(const game::Snapshot &left,
                       const game::Snapshot &right) noexcept {
  return left.paused && right.paused && left.date_raw == right.date_raw &&
         left.player_id == right.player_id &&
         left.played_character_id == right.played_character_id &&
         left.played_character_alive == right.played_character_alive &&
         left.active_wars == right.active_wars &&
         left.player_armies == right.player_armies;
}

struct TraitDefinitionRow {
  std::string_view key;
  std::vector<void *> concrete_traits;
  void *single_trait = nullptr;
};

struct TraitReadContext {
  void *database = nullptr;
  std::vector<TraitDefinitionRow> rows;
};

using GetDatabase = void *(*)();
using CharacterHasTrait = bool (*)(void *, const void *);
using CharacterTraitTracks = void *(*)(void *, void *, const void *);
using TraitTrackIndex = std::int32_t (*)(const void *, const std::string *);

bool BuildTraitReadContext(std::uintptr_t module, TraitReadContext &context,
                           std::string &failure) noexcept {
  context = {};
  failure.clear();
  const auto fail = [&failure](std::string_view stage,
                               std::string_view key = {},
                               std::int32_t index = -1) {
    failure = "native_phase_trait_context_";
    failure += stage;
    if (!key.empty()) {
      failure += ':';
      failure += key;
    }
    if (index >= 0) {
      failure += ':';
      failure += std::to_string(index);
    }
    return false;
  };
  context.database =
      reinterpret_cast<GetDatabase>(module + kTraitDatabaseRva)();
  if (context.database == nullptr) {
    return fail("database_unavailable");
  }
  void *const trait_data = LoadAt<void *>(context.database, 0x68);
  const auto trait_count =
      LoadAt<std::int32_t>(context.database, 0x74);
  if (!ValidSpan(trait_data, trait_count)) {
    return fail("database_span_invalid");
  }
  context.rows.reserve(kTraitOrGroupKeys.size());
  for (const auto key : kTraitOrGroupKeys) {
    std::vector<void *> concrete_traits;
    if (key == "physique_good") {
      concrete_traits.reserve(kPhysiqueGoodTraitKeys.size());
      for (std::int32_t index = 0;
           index < static_cast<std::int32_t>(kPhysiqueGoodTraitKeys.size());
           ++index) {
        void *const trait = FindUniqueDatabaseObject(
            context.database,
            kPhysiqueGoodTraitKeys[static_cast<std::size_t>(index)]);
        if (trait == nullptr) {
          return fail("group_child_unavailable", key, index);
        }
        concrete_traits.push_back(trait);
      }
    } else {
      void *const trait = FindUniqueDatabaseObject(context.database, key);
      if (trait == nullptr) {
        return fail("definition_unavailable", key);
      }
      concrete_traits.push_back(trait);
    }
    void *const single =
        concrete_traits.size() == 1 ? concrete_traits.front() : nullptr;
    context.rows.push_back({key, std::move(concrete_traits), single});
  }
  return true;
}

const TraitDefinitionRow *FindTraitDefinition(
    const TraitReadContext &context, std::string_view key) noexcept {
  const auto iterator = std::find_if(
      context.rows.begin(), context.rows.end(),
      [key](const auto &row) { return row.key == key; });
  return iterator == context.rows.end() ? nullptr : &*iterator;
}

bool ReadTraitPresence(std::uintptr_t module,
                       const TraitReadContext &context, void *character,
                       std::vector<NamedBoolV3> &output) noexcept {
  output.clear();
  output.reserve(context.rows.size());
  const auto has_trait =
      reinterpret_cast<CharacterHasTrait>(module + kCharacterHasTraitRva);
  for (const auto &row : context.rows) {
    if (row.concrete_traits.empty()) {
      return false;
    }
    const bool present = std::any_of(
        row.concrete_traits.begin(), row.concrete_traits.end(),
        [character, has_trait](void *trait) {
          return trait != nullptr && has_trait(character, trait);
        });
    output.push_back({std::string(row.key), present});
  }
  return true;
}

bool NamedBoolValue(const std::vector<NamedBoolV3> &values,
                    std::string_view key, bool &output) noexcept {
  const auto iterator =
      std::find_if(values.begin(), values.end(), [key](const auto &row) {
        return row.key == key;
      });
  if (iterator == values.end()) {
    return false;
  }
  output = iterator->value;
  return true;
}

bool ReadTraitTrackXp(std::uintptr_t module, void *character,
                      const TraitDefinitionRow &descriptor,
                      std::string_view track_key,
                      std::int64_t &output) noexcept {
  output = 0;
  if (descriptor.single_trait == nullptr) {
    return false;
  }
  alignas(8) std::array<std::byte, 0x10> span{};
  const auto read_tracks = reinterpret_cast<CharacterTraitTracks>(
      module + kCharacterTraitTracksRva);
  if (read_tracks(character, span.data(), descriptor.single_trait) !=
      span.data()) {
    return false;
  }
  const auto *const data = LoadAt<const std::int64_t *>(span.data(), 0);
  const auto count = LoadAt<std::int32_t>(span.data(), 0x0C);
  if (!ValidSpan(data, count, 1024)) {
    return false;
  }
  if (count == 0) {
    output = 0;
    return true;
  }
  std::int32_t index = 0;
  if (track_key.empty()) {
    const auto descriptor_count =
        LoadAt<std::int32_t>(descriptor.single_trait, 0x294);
    if (descriptor_count != 1) {
      return false;
    }
  } else {
    const std::string native_key(track_key);
    index = reinterpret_cast<TraitTrackIndex>(
        module + kTraitTrackIndexRva)(descriptor.single_trait, &native_key);
  }
  if (index < 0 || index >= count) {
    return false;
  }
  output = data[index];
  return true;
}

bool ResolveOptionalComponent(std::uintptr_t module,
                              std::uintptr_t store_slot,
                              std::uintptr_t fallback_slot,
                              std::int32_t full_id,
                              std::size_t identity_offset,
                              OptionalFullIdV3 &wire,
                              void *&object) noexcept {
  wire = {};
  object = nullptr;
  if (full_id == -1) {
    return true;
  }
  if (full_id < 0) {
    return false;
  }
  object = ResolveComponent(module, store_slot, full_id, identity_offset);
  if (object == nullptr || IsFallback(module, fallback_slot, object)) {
    object = nullptr;
    return false;
  }
  wire.present = true;
  wire.value = full_id;
  return true;
}

bool ReadCharacterAlive(void *character, bool &alive) noexcept {
  bool valid = false;
  if (!VcallBool(static_cast<std::byte *>(character) + 0x10, 0x08,
                 valid)) {
    return false;
  }
  alive = valid && LoadAt<void *>(character, 0x1C8) == nullptr;
  return true;
}

using IsHumanPlayerCharacter = bool (*)(std::int32_t);

bool ReadCharacterIdentity(std::uintptr_t module, void *character,
                           std::int32_t character_id,
                           CombatPhaseCharacterV3 &output) noexcept {
  if (ResolveComponent(module, kCharacterStoreSlot, character_id, 0x18) !=
          character ||
      IsFallback(module, kCharacterFallbackSlot, character) ||
      !ReadCharacterAlive(character, output.alive)) {
    return false;
  }
  output.is_ai = output.alive
                     ? !reinterpret_cast<IsHumanPlayerCharacter>(
                           module + 0x28BCEB0)(character_id)
                     : true;
  output.martial = LoadAt<std::int32_t>(character, 0xD8);
  output.learning = LoadAt<std::int32_t>(character, 0xE4);
  output.prowess = LoadAt<std::int32_t>(character, 0xE8);
  return true;
}

bool ReadCharacterTraits(std::uintptr_t module,
                         const TraitReadContext &traits, void *character,
                         CombatPhaseCharacterV3 &output) noexcept {
  if (!ReadTraitPresence(module, traits, character,
                         output.traits_or_groups)) {
    return false;
  }
  std::int32_t wounded_rank = 0;
  for (std::int32_t rank = 1; rank <= 3; ++rank) {
    const auto key = rank == 1 ? "wounded_1"
                     : rank == 2 ? "wounded_2"
                                 : "wounded_3";
    bool present = false;
    if (!NamedBoolValue(output.traits_or_groups, key, present)) {
      return false;
    }
    if (present) {
      if (wounded_rank != 0) {
        return false;
      }
      wounded_rank = rank;
    }
  }
  output.wounded_rank_raw =
      static_cast<std::int64_t>(wounded_rank) * kFixedScale;
  bool fragile_present = false;
  if (!NamedBoolValue(output.traits_or_groups, "fragile_bones",
                      fragile_present)) {
    return false;
  }
  output.fragile_bones_rank_raw = fragile_present ? kFixedScale : 0;
  const auto *const fragile = FindTraitDefinition(traits, "fragile_bones");
  const auto *const blademaster =
      FindTraitDefinition(traits, "lifestyle_blademaster");
  const auto *const tourney =
      FindTraitDefinition(traits, "tourney_participant");
  return fragile != nullptr && blademaster != nullptr && tourney != nullptr &&
         ReadTraitTrackXp(module, character, *fragile, "fragile_bones",
                          output.fragile_bones_xp_raw) &&
         ReadTraitTrackXp(module, character, *blademaster, "",
                          output.lifestyle_blademaster_xp_raw) &&
         ReadTraitTrackXp(module, character, *tourney, "bow",
                          output.tourney_bow_xp_raw) &&
         ReadTraitTrackXp(module, character, *tourney, "foot",
                          output.tourney_foot_xp_raw) &&
         ReadTraitTrackXp(module, character, *tourney, "horse",
                          output.tourney_horse_xp_raw);
}

struct NamedPointerV3 {
  std::string_view key;
  void *value = nullptr;
};

struct QueryDefinitionContext {
  void *warfare_legacy_3 = nullptr;
  void *stalwart_leader = nullptr;
  void *extreme_conqueror_modifier = nullptr;
  void *garuda_court_position_type = nullptr;
  void *easy_difficulty = nullptr;
  void *very_easy_difficulty = nullptr;
  std::vector<NamedPointerV3> innovations;
  std::vector<NamedPointerV3> traditions;
  std::vector<NamedSignedV3> culture_parameter_ids;
  std::vector<NamedSignedV3> accolade_parameter_ids;
  std::vector<NamedSignedV3> attribute_variable_ids;
  std::int32_t death_is_glory_id = -1;
  std::int32_t government_is_nomadic_id = -1;
  std::int32_t men_at_arms_category_id = -1;
  std::int32_t conqueror_variable_id = -1;
  std::int32_t hold_court_knight_variable_id = -1;
  std::int32_t hold_court_promise_variable_id = -1;
  std::int32_t accolade_progress_variable_id = -1;
};

using RuleSettingKeyHash = std::int32_t (*)(void *, const char *,
                                             std::uint32_t);
using LookupRuleSettingToken = void *(*)(void *, std::int32_t);
using LookupCharacterModifier = void *(*)(void *, std::int32_t);

bool ResolveRuleSettingToken(std::uintptr_t module, std::string_view key,
                             void *&output) noexcept {
  output = nullptr;
  void *const registry =
      *reinterpret_cast<void **>(module + kGameRuleTokenRegistrySlot);
  if (registry == nullptr || key.size() >
                                 std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  const auto hash = reinterpret_cast<RuleSettingKeyHash>(
      module + kRuleSettingKeyHashRva)(registry, key.data(),
                                       static_cast<std::uint32_t>(key.size()));
  output = reinterpret_cast<LookupRuleSettingToken>(
      module + kLookupRuleSettingTokenRva)(registry, hash);
  return output != nullptr &&
         output != *reinterpret_cast<void **>(
                       module + kGameRuleTokenFallbackSlot) &&
         StableKeyEquals(output, 0x18, key);
}

bool BuildQueryDefinitionContext(std::uintptr_t module,
                                 QueryDefinitionContext &output,
                                 std::string &failure) noexcept {
  output = {};
  failure.clear();
  const auto fail = [&failure](std::string_view stage,
                               std::string_view key = {}) {
    failure = "native_phase_definition_context_";
    failure += stage;
    if (!key.empty()) {
      failure += ':';
      failure += key;
    }
    return false;
  };
  void *const dynasty_perks = reinterpret_cast<GetDatabase>(
      module + kDynastyPerkDatabaseRva)();
  void *const character_perks = reinterpret_cast<GetDatabase>(
      module + kCharacterPerkDatabaseRva)();
  void *const modifiers = reinterpret_cast<GetDatabase>(
      module + kCharacterModifierDatabaseRva)();
  output.warfare_legacy_3 =
      FindUniqueDatabaseObject(dynasty_perks, "warfare_legacy_3");
  output.stalwart_leader =
      FindUniqueDatabaseObject(character_perks, "stalwart_leader_perk");
  // Mirror the compiled has_character_modifier initializer: hash the stable
  // key, use the CharacterModifier database's own read lookup, and then
  // reject its fallback, and round-trip the returned key at +0x18.  The
  // modifier payload starts at +0x38; it is not the stable key.
  constexpr std::string_view kExtremeConquerorModifier =
      "ai_extreme_conqueror_modifier";
  if (modifiers == nullptr ||
      kExtremeConquerorModifier.size() >
          std::numeric_limits<std::uint32_t>::max()) {
    return fail("modifier_database_unavailable");
  }
  const auto modifier_hash = reinterpret_cast<RuleSettingKeyHash>(
      module + kRuleSettingKeyHashRva)(
      modifiers, kExtremeConquerorModifier.data(),
      static_cast<std::uint32_t>(kExtremeConquerorModifier.size()));
  output.extreme_conqueror_modifier =
      reinterpret_cast<LookupCharacterModifier>(
          module + kCharacterModifierLookupRva)(modifiers, modifier_hash);
  if (output.warfare_legacy_3 == nullptr) {
    return fail("definition_unavailable", "warfare_legacy_3");
  }
  if (output.stalwart_leader == nullptr) {
    return fail("definition_unavailable", "stalwart_leader_perk");
  }
  if (output.extreme_conqueror_modifier ==
          *reinterpret_cast<void **>(module +
                                      kCharacterModifierFallbackSlot) ||
      !StableKeyEquals(output.extreme_conqueror_modifier, 0x18,
                       kExtremeConquerorModifier)) {
    output.extreme_conqueror_modifier = nullptr;
    return fail("definition_unavailable",
                kExtremeConquerorModifier);
  }
  void *const court_position_types =
      *reinterpret_cast<void **>(module + kCourtPositionTypeDatabaseSlot);
  output.garuda_court_position_type = FindUniqueDatabaseObject(
      court_position_types, "garuda_court_position");
  if (output.garuda_court_position_type == nullptr ||
      IsFallback(module, kCourtPositionTypeFallbackSlot,
                 output.garuda_court_position_type)) {
    return fail("definition_unavailable", "garuda_court_position");
  }
  if (!ResolveRuleSettingToken(module, "easy_difficulty",
                               output.easy_difficulty)) {
    return fail("rule_setting_unavailable", "easy_difficulty");
  }
  if (!ResolveRuleSettingToken(module, "very_easy_difficulty",
                               output.very_easy_difficulty)) {
    return fail("rule_setting_unavailable", "very_easy_difficulty");
  }
  if (output.easy_difficulty == output.very_easy_difficulty) {
    return fail("rule_setting_collision");
  }

  void *const innovation_db =
      *reinterpret_cast<void **>(module + kInnovationDatabaseSlot);
  void *const tradition_db =
      *reinterpret_cast<void **>(module + kTraditionDatabaseSlot);
  if (innovation_db == nullptr || tradition_db == nullptr) {
    return fail("culture_definition_database_unavailable");
  }
  output.innovations.reserve(kInnovationKeys.size());
  for (const auto key : kInnovationKeys) {
    void *const object = FindUniqueDatabaseObject(innovation_db, key);
    if (object == nullptr ||
        IsFallback(module, kInnovationFallbackSlot, object)) {
      return fail("innovation_unavailable", key);
    }
    output.innovations.push_back({key, object});
  }
  output.traditions.reserve(kTraditionKeys.size());
  for (const auto key : kTraditionKeys) {
    void *const object = FindUniqueDatabaseObject(tradition_db, key);
    bool valid = false;
    if (object == nullptr || IsFallback(module, kTraditionFallbackSlot, object) ||
        !VcallBool(object, 0, valid) || !valid) {
      return fail("tradition_unavailable", key);
    }
    output.traditions.push_back({key, object});
  }

  output.culture_parameter_ids.reserve(kCultureParameterKeys.size());
  for (const auto key : kCultureParameterKeys) {
    std::int32_t identifier = -1;
    if (!ResolveScriptIdentifier(module, key, identifier)) {
      return fail("culture_parameter_unavailable", key);
    }
    output.culture_parameter_ids.push_back(
        {std::string(key), identifier});
  }
  output.accolade_parameter_ids.reserve(kAccoladeParameterKeys.size());
  for (const auto key : kAccoladeParameterKeys) {
    std::int32_t identifier = -1;
    if (!ResolveVariableIdentifier(module, key, identifier)) {
      return fail("accolade_parameter_unavailable", key);
    }
    output.accolade_parameter_ids.push_back(
        {std::string(key), identifier});
  }
  if (!ResolveScriptIdentifier(module, "death_is_glory",
                               output.death_is_glory_id)) {
    return fail("script_identifier_unavailable", "death_is_glory");
  }
  if (!ResolveScriptIdentifier(module, "government_is_nomadic",
                               output.government_is_nomadic_id)) {
    return fail("script_identifier_unavailable", "government_is_nomadic");
  }
  if (!ResolveVariableIdentifier(module, "men_at_arms",
                                 output.men_at_arms_category_id)) {
    return fail("script_identifier_unavailable", "men_at_arms");
  }

  const auto resolve_variable = [module](std::string_view key,
                                         std::int32_t &id) {
    return ResolveVariableIdentifier(module, key, id);
  };
  if (!resolve_variable("conqueror", output.conqueror_variable_id)) {
    return fail("variable_identifier_unavailable", "conqueror");
  }
  if (!resolve_variable("hold_court_8050_knight",
                        output.hold_court_knight_variable_id)) {
    return fail("variable_identifier_unavailable",
                "hold_court_8050_knight");
  }
  if (!resolve_variable("hold_court_8050_promise",
                        output.hold_court_promise_variable_id)) {
    return fail("variable_identifier_unavailable",
                "hold_court_8050_promise");
  }
  if (!resolve_variable("accolade_progress",
                        output.accolade_progress_variable_id)) {
    return fail("variable_identifier_unavailable", "accolade_progress");
  }
  output.attribute_variable_ids.reserve(kAttributeUnlockKeys.size());
  for (const auto short_key : kAttributeUnlockKeys) {
    const auto full_key = std::string(short_key) + "_attribute_unlock";
    std::int32_t identifier = -1;
    if (!resolve_variable(full_key, identifier)) {
      return fail("variable_identifier_unavailable", full_key);
    }
    output.attribute_variable_ids.push_back(
        {std::string(short_key), identifier});
  }
  return true;
}

using CharacterLiege = void *(*)(void *);
using CharacterPerks = void *(*)(void *);

bool ReadCharacterRelationsAndPerks(
    std::uintptr_t module, const QueryDefinitionContext &definitions,
    void *character, CombatPhaseCharacterV3 &output) noexcept {
  void *house = nullptr;
  const auto house_id = LoadAt<std::int32_t>(character, 0x150);
  if (!ResolveOptionalComponent(module, kHouseStoreSlot, kHouseFallbackSlot,
                                house_id, 0x10, output.house, house)) {
    return false;
  }

  void *const raw_liege = reinterpret_cast<CharacterLiege>(
      module + kCharacterLiegeRva)(character);
  void *liege = nullptr;
  if (raw_liege == nullptr ||
      IsFallback(module, kCharacterFallbackSlot, raw_liege)) {
    output.liege = {};
    output.liege_house = {};
  } else {
    const auto liege_id = LoadAt<std::int32_t>(raw_liege, 0x18);
    if (!ResolveOptionalComponent(module, kCharacterStoreSlot,
                                  kCharacterFallbackSlot, liege_id, 0x18,
                                  output.liege, liege) ||
        !output.liege.present || liege != raw_liege) {
      return false;
    }
    void *liege_house = nullptr;
    const auto liege_house_id = LoadAt<std::int32_t>(liege, 0x150);
    if (!ResolveOptionalComponent(module, kHouseStoreSlot,
                                  kHouseFallbackSlot, liege_house_id, 0x10,
                                  output.liege_house, liege_house)) {
      return false;
    }
  }

  void *dynasty = nullptr;
  std::int32_t dynasty_id = -1;
  if (house != nullptr) {
    dynasty_id = LoadAt<std::int32_t>(house, 0x2C);
  }
  if (!ResolveOptionalComponent(module, kDynastyStoreSlot,
                                kDynastyFallbackSlot, dynasty_id, 0x10,
                                output.dynasty, dynasty)) {
    return false;
  }
  output.warfare_legacy_3 = false;
  if (dynasty != nullptr) {
    void *const data = LoadAt<void *>(dynasty, 0x170);
    const auto count = LoadAt<std::int32_t>(dynasty, 0x17C);
    if (!ValidSpan(data, count)) {
      return false;
    }
    output.warfare_legacy_3 =
        ContainsPointer(data, count, definitions.warfare_legacy_3);
  }

  void *const perk_span = reinterpret_cast<CharacterPerks>(
      module + kCharacterPerksRva)(character);
  if (perk_span == nullptr) {
    return false;
  }
  void *const perk_data = LoadAt<void *>(perk_span, 0);
  const auto perk_count = LoadAt<std::int32_t>(perk_span, 0x0C);
  if (!ValidSpan(perk_data, perk_count)) {
    return false;
  }
  output.stalwart_leader =
      ContainsPointer(perk_data, perk_count, definitions.stalwart_leader);

  void *const relation = LoadAt<void *>(character, 0x1B0);
  std::int32_t employer_id = -1;
  if (relation != nullptr) {
    employer_id = LoadAt<std::int32_t>(relation, 0xC8);
  }
  void *employer = nullptr;
  if (!ResolveOptionalComponent(module, kCharacterStoreSlot,
                                kCharacterFallbackSlot, employer_id, 0x18,
                                output.employer, employer)) {
    return false;
  }
  return true;
}

using CultureHasParameter = bool (*)(void *, std::int32_t);
using FaithDoctrineParameter = void *(*)(void *, std::int32_t);

bool ReadFaithCulture(std::uintptr_t module,
                      const QueryDefinitionContext &definitions,
                      void *character,
                      CombatPhaseCharacterV3 &output) noexcept {
  void *culture = nullptr;
  if (!ResolveOptionalComponent(
          module, kCultureStoreSlot, kCultureFallbackSlot,
          LoadAt<std::int32_t>(character, 0xB0), 0x10, output.culture,
          culture)) {
    return false;
  }
  void *faith = nullptr;
  if (!ResolveOptionalComponent(module, kFaithStoreSlot, kFaithFallbackSlot,
                                LoadAt<std::int32_t>(character, 0xB4), 0x08,
                                output.faith, faith)) {
    return false;
  }
  void *religion = nullptr;
  const auto religion_id =
      faith == nullptr ? -1 : LoadAt<std::int32_t>(faith, 0x1C);
  if (!ResolveOptionalComponent(module, kReligionStoreSlot,
                                kReligionFallbackSlot, religion_id, 0x08,
                                output.religion, religion)) {
    return false;
  }

  output.heritage_north_germanic = false;
  output.knights_slightly_more_prone_to_injury = false;
  output.blademaster_traits_more_common = false;
  output.innovations.clear();
  output.traditions.clear();
  output.culture_parameters.clear();
  output.innovations.reserve(definitions.innovations.size());
  output.traditions.reserve(definitions.traditions.size());
  output.culture_parameters.reserve(
      definitions.culture_parameter_ids.size());
  if (culture != nullptr) {
    void *const pillar_data = LoadAt<void *>(culture, 0x190);
    const auto pillar_count = LoadAt<std::int32_t>(culture, 0x19C);
    if (!ValidSpan(pillar_data, pillar_count, 16) || pillar_count != 5) {
      return false;
    }
    for (std::int32_t category = 0; category < pillar_count; ++category) {
      void *const pillar = LoadAt<void *>(
          pillar_data, static_cast<std::size_t>(category) * 8);
      if (pillar == nullptr) {
        return false;
      }
      if (StableKeyEquals(pillar, 0x18, "heritage_north_germanic")) {
        output.heritage_north_germanic = true;
      }
    }
    void *const innovation_data = LoadAt<void *>(culture, 0x758);
    const auto innovation_count = LoadAt<std::int32_t>(culture, 0x764);
    void *const tradition_data = LoadAt<void *>(culture, 0x178);
    const auto tradition_count = LoadAt<std::int32_t>(culture, 0x184);
    if (!ValidSpan(innovation_data, innovation_count) ||
        !ValidSpan(tradition_data, tradition_count)) {
      return false;
    }
    for (const auto &definition : definitions.innovations) {
      output.innovations.push_back(
          {std::string(definition.key),
           ContainsPointer(innovation_data, innovation_count,
                           definition.value)});
    }
    for (const auto &definition : definitions.traditions) {
      output.traditions.push_back(
          {std::string(definition.key),
           ContainsPointer(tradition_data, tradition_count,
                           definition.value)});
    }
    const auto has_parameter = reinterpret_cast<CultureHasParameter>(
        module + kCultureHasParameterRva);
    for (const auto &definition : definitions.culture_parameter_ids) {
      output.culture_parameters.push_back(
          {definition.key,
           has_parameter(culture,
                         static_cast<std::int32_t>(definition.value))});
    }
    if (!NamedBoolValue(output.culture_parameters,
                        "knights_slightly_more_prone_to_injury",
                        output.knights_slightly_more_prone_to_injury) ||
        !NamedBoolValue(output.culture_parameters,
                        "blademaster_traits_more_common",
                        output.blademaster_traits_more_common)) {
      return false;
    }
  } else {
    for (const auto &definition : definitions.innovations) {
      output.innovations.push_back({std::string(definition.key), false});
    }
    for (const auto &definition : definitions.traditions) {
      output.traditions.push_back({std::string(definition.key), false});
    }
    for (const auto &definition : definitions.culture_parameter_ids) {
      output.culture_parameters.push_back({definition.key, false});
    }
  }

  output.death_is_glory = false;
  output.tenet_warmonger = false;
  if (faith != nullptr) {
    void *const doctrine_container =
        static_cast<std::byte *>(faith) + 0x278;
    void *const doctrine_data = LoadAt<void *>(doctrine_container, 0x08);
    const auto doctrine_count =
        LoadAt<std::int32_t>(doctrine_container, 0x14);
    if (!ValidSpan(doctrine_data, doctrine_count)) {
      return false;
    }
    for (std::int32_t index = 0; index < doctrine_count; ++index) {
      void *const doctrine = LoadAt<void *>(
          doctrine_data, static_cast<std::size_t>(index) * 8);
      if (StableKeyEquals(doctrine, 0x18, "tenet_warmonger")) {
        output.tenet_warmonger = true;
      }
    }
    void *const parameter_row =
        reinterpret_cast<FaithDoctrineParameter>(
            module + 0x24EE100)(doctrine_container,
                                definitions.death_is_glory_id);
    output.death_is_glory =
        parameter_row != nullptr &&
        LoadAt<std::uint8_t>(parameter_row, 0x08) != 0;
  }
  output.germanic_religion =
      religion != nullptr &&
      StableKeyEquals(religion, 0x58, "germanic_religion");
  return true;
}

struct EventTarget16 {
  std::uint16_t kind = 0;
  std::array<std::uint8_t, 6> reserved{};
  std::int64_t payload = 0;
};
static_assert(sizeof(EventTarget16) == 0x10);

using VariableContextForScope = void *(*)(const EventTarget16 *);

struct VariableValue {
  bool present = false;
  std::uint16_t kind = 0;
  std::int64_t payload = 0;
};

bool FindVariableValue(void *context, std::int32_t identifier,
                       VariableValue &output) noexcept {
  output = {};
  if (context == nullptr) {
    return false;
  }
  void *const data = LoadAt<void *>(context, 0x10);
  const auto count = LoadAt<std::int32_t>(context, 0x1C);
  if (!ValidSpan(data, count)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const row = static_cast<const std::byte *>(data) +
                            static_cast<std::size_t>(index) * 0x20;
    if (LoadAt<std::int32_t>(row, 0x08) != identifier) {
      continue;
    }
    if (output.present) {
      return false;
    }
    output.present = true;
    output.kind = LoadAt<std::uint16_t>(row, 0x10);
    output.payload = LoadAt<std::int64_t>(row, 0x18);
  }
  return true;
}

bool ReadVariableContextForCharacter(std::uintptr_t module,
                                     std::int32_t character_id,
                                     void *&context) noexcept {
  const EventTarget16 target{4, {}, character_id};
  context = reinterpret_cast<VariableContextForScope>(
      module + kVariableContextForScopeRva)(&target);
  return context != nullptr;
}

bool ReadOptionalCharacterVariable(std::uintptr_t module, void *context,
                                   std::int32_t identifier,
                                   OptionalFullIdV3 &output) noexcept {
  VariableValue value{};
  if (!FindVariableValue(context, identifier, value)) {
    return false;
  }
  output = {};
  if (!value.present) {
    return true;
  }
  if (value.kind != 4 || value.payload <= 0 ||
      value.payload > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  const auto character_id = static_cast<std::int32_t>(value.payload);
  void *const character =
      ResolveComponent(module, kCharacterStoreSlot, character_id, 0x18);
  if (character == nullptr ||
      IsFallback(module, kCharacterFallbackSlot, character)) {
    return false;
  }
  output.present = true;
  output.value = character_id;
  return true;
}

bool ReadVariables(std::uintptr_t module,
                   const QueryDefinitionContext &definitions,
                   void *character,
                   CombatPhaseCharacterV3 &output) noexcept {
  void *context = nullptr;
  if (!ReadVariableContextForCharacter(module, output.character_id,
                                       context)) {
    return false;
  }
  VariableValue value{};
  if (!FindVariableValue(context, definitions.conqueror_variable_id,
                         value)) {
    return false;
  }
  output.conqueror_variable_present = value.present;
  output.attribute_unlock_variables.clear();
  output.attribute_unlock_variables.reserve(
      definitions.attribute_variable_ids.size());
  for (const auto &definition : definitions.attribute_variable_ids) {
    if (!FindVariableValue(context,
                           static_cast<std::int32_t>(definition.value),
                           value)) {
      return false;
    }
    output.attribute_unlock_variables.push_back(
        {definition.key, value.present});
  }
  if (!ReadOptionalCharacterVariable(
          module, context, definitions.hold_court_knight_variable_id,
          output.hold_court_8050_knight)) {
    return false;
  }

  output.employer_hold_court_8050_promise = {};
  if (output.employer.present) {
    void *employer_context = nullptr;
    if (!ReadVariableContextForCharacter(module, output.employer.value,
                                         employer_context) ||
        !ReadOptionalCharacterVariable(
            module, employer_context,
            definitions.hold_court_promise_variable_id,
            output.employer_hold_court_8050_promise)) {
      return false;
    }
  }

  output.liege_accolade_progress_raw = 0;
  if (output.liege.present) {
    void *liege_context = nullptr;
    if (!ReadVariableContextForCharacter(module, output.liege.value,
                                         liege_context) ||
        !FindVariableValue(liege_context,
                           definitions.accolade_progress_variable_id,
                           value)) {
      return false;
    }
    if (value.present) {
      if (value.kind != 1) {
        return false;
      }
      output.liege_accolade_progress_raw =
          std::min<std::int64_t>(value.payload, 2'000'000);
    }
  }

  void *const extension = LoadAt<void *>(character, 0x1A8);
  output.ai_extreme_conqueror_modifier = false;
  if (extension != nullptr) {
    void *const rows = LoadAt<void *>(extension, 0x188);
    const auto count = LoadAt<std::int32_t>(extension, 0x194);
    if (!ValidSpan(rows, count)) {
      return false;
    }
    for (std::int32_t index = 0; index < count; ++index) {
      const auto *const row = static_cast<const std::byte *>(rows) +
                              static_cast<std::size_t>(index) * 0x48;
      if (LoadAt<void *>(row, 0) ==
          definitions.extreme_conqueror_modifier) {
        output.ai_extreme_conqueror_modifier = true;
      }
    }
  }
  return true;
}

using CanBeAcclaimed = bool (*)(void *, void *, void *);
using AccoladeHasParameter = bool (*)(void *, std::int32_t);
using AccoladeValidate = bool (*)(void *);

bool ReadInt32SpanContains(const void *span, std::int32_t needle,
                           bool &contains,
                           bool require_sorted = true) noexcept {
  contains = false;
  void *const data = LoadAt<void *>(span, 0);
  const auto count = LoadAt<std::int32_t>(span, 0x0C);
  if (!ValidSpan(data, count)) {
    return false;
  }
  std::int32_t previous = std::numeric_limits<std::int32_t>::min();
  for (std::int32_t index = 0; index < count; ++index) {
    const auto value =
        LoadAt<std::int32_t>(data, static_cast<std::size_t>(index) * 4);
    if (require_sorted && index != 0 && value <= previous) {
      return false;
    }
    if (value == needle) {
      contains = true;
    }
    previous = value;
  }
  return true;
}

bool ReadAccolade(std::uintptr_t module,
                  const QueryDefinitionContext &definitions,
                  void *character,
                  CombatPhaseCharacterV3 &output,
                  std::string &failure) noexcept {
  failure.clear();
  const auto fail = [&failure, &output](std::string_view stage,
                                        std::int32_t index = -1) {
    failure = "native_phase_character_reader_accolade_";
    failure += stage;
    failure += ':';
    failure += std::to_string(output.character_id);
    if (index >= 0) {
      failure += ':';
      failure += std::to_string(index);
    }
    return false;
  };
  output.accolade = {};
  output.is_acclaimed = false;
  output.accolade_has_men_at_arms_category = false;
  output.accolade_parameters.clear();
  output.accolade_parameters.reserve(definitions.accolade_parameter_ids.size());
  void *accolade = nullptr;
  void *const extension = LoadAt<void *>(character, 0x1A8);
  const auto accolade_id =
      extension == nullptr ? -1 : LoadAt<std::int32_t>(extension, 0x568);
  if (!ResolveOptionalComponent(module, kAccoladeStoreSlot,
                                kAccoladeFallbackSlot, accolade_id, 0x08,
                                output.accolade, accolade)) {
    return fail("resolve_failed");
  }
  if (accolade == nullptr) {
    for (const auto &definition : definitions.accolade_parameter_ids) {
      output.accolade_parameters.push_back({definition.key, false});
    }
  } else {
    if (!reinterpret_cast<AccoladeValidate>(module + kAccoladeValidateRva)(
            accolade)) {
      return fail("validation_failed");
    }
    if (!VcallBool(accolade, 0x08, output.is_acclaimed)) {
      return fail("status_unavailable");
    }
    void *const rows = LoadAt<void *>(accolade, 0x58);
    const auto count = LoadAt<std::int32_t>(accolade, 0x64);
    if (!ValidSpan(rows, count)) {
      return fail("attribute_span_invalid");
    }
    for (std::int32_t index = 0; index < count; ++index) {
      const auto *const row = static_cast<const std::byte *>(rows) +
                              static_cast<std::size_t>(index) * 0x18;
      void *const attribute = LoadAt<void *>(row, 0x10);
      if (attribute == nullptr) {
        return fail("attribute_null", index);
      }
      const auto *const category_span =
          static_cast<const std::byte *>(attribute) + 0x3E8;
      bool has_category = false;
      if (!ReadInt32SpanContains(category_span,
                                 definitions.men_at_arms_category_id,
                                 has_category, false)) {
        return fail("category_span_invalid", index);
      }
      if (has_category) {
        output.accolade_has_men_at_arms_category = true;
      }
    }
    const auto has_parameter = reinterpret_cast<AccoladeHasParameter>(
        module + kAccoladeHasParameterRva);
    for (const auto &definition : definitions.accolade_parameter_ids) {
      output.accolade_parameters.push_back(
          {definition.key,
           has_parameter(accolade,
                         static_cast<std::int32_t>(definition.value))});
    }
  }
  output.can_be_acclaimed = reinterpret_cast<CanBeAcclaimed>(
      module + kCanBeAcclaimedRva)(character, nullptr, nullptr);
  return true;
}

using CharacterGovernment = void *(*)(void *);

bool ReadGovernment(std::uintptr_t module,
                    const QueryDefinitionContext &definitions,
                    void *character,
                    CombatPhaseCharacterV3 &output) noexcept {
  void *const government = reinterpret_cast<CharacterGovernment>(
      module + kCharacterGovernmentRva)(character);
  if (government == nullptr) {
    return false;
  }
  return ReadInt32SpanContains(
      static_cast<std::byte *>(government) + 0x48,
      definitions.government_is_nomadic_id,
      output.government_is_nomadic);
}

bool ReadCourtPosition(std::uintptr_t module,
                       const QueryDefinitionContext &definitions,
                       void *character,
                       CombatPhaseCharacterV3 &output) noexcept {
  output.garuda_court_position = false;
  void *const relation = LoadAt<void *>(character, 0x1B0);
  if (relation == nullptr) {
    return true;
  }
  void *const ids = LoadAt<void *>(relation, 0xD0);
  const auto count = LoadAt<std::int32_t>(relation, 0xDC);
  if (!ValidSpan(ids, count)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id =
        LoadAt<std::int32_t>(ids, static_cast<std::size_t>(index) * 4);
    void *const position =
        ResolveComponent(module, kCourtPositionStoreSlot, id, 0x08);
    if (position == nullptr ||
        IsFallback(module, kCourtPositionFallbackSlot, position)) {
      return false;
    }
    void *const type = LoadAt<void *>(position, 0x110);
    if (type == nullptr) {
      return false;
    }
    if (type == definitions.garuda_court_position_type) {
      output.garuda_court_position = true;
    }
  }
  return true;
}

using ReadSelectedGameRules = void *(*)(void *);

bool ReadGameRules(std::uintptr_t module,
                   const QueryDefinitionContext &definitions, bool &easy,
                   bool &very_easy) noexcept {
  easy = false;
  very_easy = false;
  void *const service =
      *reinterpret_cast<void **>(module + kGameRuleSelectionServiceSlot);
  if (service == nullptr) {
    return false;
  }
  void *const vtable = LoadAt<void *>(service, 0);
  const auto address =
      vtable == nullptr ? 0 : LoadAt<std::uintptr_t>(vtable, 0x10);
  if (address == 0) {
    return false;
  }
  void *const selected =
      reinterpret_cast<ReadSelectedGameRules>(address)(service);
  if (selected == nullptr) {
    return false;
  }
  void *const data = LoadAt<void *>(selected, 0x08);
  const auto count = LoadAt<std::int32_t>(selected, 0x14);
  if (!ValidSpan(data, count)) {
    return false;
  }
  std::int32_t easy_count = 0;
  std::int32_t very_easy_count = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    void *const token =
        LoadAt<void *>(data, static_cast<std::size_t>(index) * 8);
    if (token == nullptr) {
      return false;
    }
    if (token == definitions.easy_difficulty) {
      ++easy_count;
    } else if (token == definitions.very_easy_difficulty) {
      ++very_easy_count;
    }
  }
  if (easy_count > 1 || very_easy_count > 1 ||
      (easy_count != 0 && very_easy_count != 0)) {
    return false;
  }
  easy = easy_count == 1;
  very_easy = very_easy_count == 1;
  return true;
}

bool ReadMaaBaseTypeEnums(std::uintptr_t module,
                          std::vector<NamedSignedV3> &output) noexcept {
  output.clear();
  void *const registry =
      *reinterpret_cast<void **>(module + kMaaBaseTypeRegistrySlot);
  if (registry == nullptr) {
    return false;
  }
  void *const data = LoadAt<void *>(registry, 0xF08);
  const auto count = LoadAt<std::int32_t>(registry, 0xF14);
  if (!ValidSpan(data, count)) {
    return false;
  }
  output.reserve(kMaaBaseTypeKeys.size());
  for (const auto expected : kMaaBaseTypeKeys) {
    bool found = false;
    std::int32_t value = 0;
    for (std::int32_t index = 0; index < count; ++index) {
      const auto *const row = static_cast<const std::byte *>(data) +
                              static_cast<std::size_t>(index) * 0x58;
      if (!StableKeyEquals(row, 0x08, expected)) {
        continue;
      }
      if (found) {
        return false;
      }
      found = true;
      value = LoadAt<std::int32_t>(row, 0);
    }
    if (!found) {
      return false;
    }
    output.push_back({std::string(expected), value});
  }
  return true;
}

bool NamedSignedValue(const std::vector<NamedSignedV3> &values,
                      std::string_view key,
                      std::int64_t &output) noexcept {
  const auto iterator =
      std::find_if(values.begin(), values.end(), [key](const auto &row) {
        return row.key == key;
      });
  if (iterator == values.end()) {
    return false;
  }
  output = iterator->value;
  return true;
}

bool CheckedScaleCount(std::int64_t value, std::int64_t &output) noexcept {
  if (value > std::numeric_limits<std::int64_t>::max() / kFixedScale ||
      value < std::numeric_limits<std::int64_t>::min() / kFixedScale) {
    return false;
  }
  output = value * kFixedScale;
  return true;
}

bool ReadArmyMaa(std::uintptr_t module,
                 const std::vector<NamedSignedV3> &base_type_enums,
                 const game::CombatArmyInputsSnapshot &base_army,
                 CombatPhaseArmyV3 &output) noexcept {
  output.army_id = base_army.army_id;
  output.native_carmy_id = base_army.native_carmy_id;
  output.encounter_role = base_army.encounter_role;
  if (!base_army.native_carmy_id_observable ||
      !base_army.regiments_observable) {
    return false;
  }
  void *const army = ResolveComponent(module, kInternalArmyStoreSlot,
                                      base_army.native_carmy_id, 0x10);
  if (army == nullptr ||
      IsFallback(module, kInternalArmyFallbackSlot, army)) {
    return false;
  }
  void *const native_regiment_ids = LoadAt<void *>(army, 0x38);
  const auto native_regiment_count = LoadAt<std::int32_t>(army, 0x44);
  if (!ValidSpan(native_regiment_ids, native_regiment_count) ||
      static_cast<std::size_t>(native_regiment_count) !=
          base_army.regiments.size()) {
    return false;
  }
  for (std::int32_t index = 0; index < native_regiment_count; ++index) {
    if (LoadAt<std::int32_t>(native_regiment_ids,
                             static_cast<std::size_t>(index) * 4) !=
        base_army.regiments[static_cast<std::size_t>(index)].regiment_id) {
      return false;
    }
  }
  std::array<std::int64_t, kMaaBaseTypeKeys.size()> base_counts{};
  std::array<std::int64_t, kCrossbowTypeKeys.size()> crossbow_counts{};
  std::int64_t total = 0;
  for (const auto &base_regiment : base_army.regiments) {
    void *const regiment = ResolveComponent(
        module, kRegimentStoreSlot, base_regiment.regiment_id, 0x10);
    if (regiment == nullptr ||
        IsFallback(module, kRegimentFallbackSlot, regiment) ||
        LoadAt<std::int32_t>(regiment, 0x140) !=
            base_army.native_carmy_id) {
      return false;
    }
    void *const type = LoadAt<void *>(regiment, 0x18);
    bool valid_maa = false;
    if (type == nullptr || !VcallBool(type, 0, valid_maa)) {
      return false;
    }
    if (valid_maa) {
      ++total;
    } else {
      continue;
    }
    const auto base_enum = LoadAt<std::int32_t>(type, 0x270);
    for (std::size_t index = 0; index < kMaaBaseTypeKeys.size(); ++index) {
      if (base_enum == base_type_enums[index].value) {
        ++base_counts[index];
      }
    }
    std::string type_key;
    if (!ReadMsvcString(static_cast<std::byte *>(type) + 0x18,
                        type_key)) {
      return false;
    }
    for (std::size_t index = 0; index < kCrossbowTypeKeys.size(); ++index) {
      if (type_key == kCrossbowTypeKeys[index]) {
        ++crossbow_counts[index];
      }
    }
  }
  if (!CheckedScaleCount(total, output.maa_regiment_count_raw)) {
    return false;
  }
  const auto base_index = [](std::string_view key) {
    for (std::size_t index = 0; index < kMaaBaseTypeKeys.size(); ++index) {
      if (kMaaBaseTypeKeys[index] == key) {
        return index;
      }
    }
    return kMaaBaseTypeKeys.size();
  };
  const auto append_count = [&output](std::string_view key,
                                      std::int64_t value) {
    std::int64_t raw = 0;
    if (!CheckedScaleCount(value, raw)) {
      return false;
    }
    output.maa_counts_raw.push_back({std::string(key), raw});
    return true;
  };
  output.maa_counts_raw.clear();
  output.maa_counts_raw.reserve(11);
  if (!append_count("skirmishers_raw",
                    base_counts[base_index("skirmishers")]) ||
      !append_count("pikemen_raw", base_counts[base_index("pikemen")]) ||
      !append_count("heavy_infantry_raw",
                    base_counts[base_index("heavy_infantry")]) ||
      !append_count("light_cavalry_raw",
                    base_counts[base_index("light_cavalry")]) ||
      !append_count("heavy_cavalry_raw",
                    base_counts[base_index("heavy_cavalry")]) ||
      !append_count("camel_cavalry_raw",
                    base_counts[base_index("camel_cavalry")]) ||
      !append_count("elephant_cavalry_raw",
                    base_counts[base_index("elephant_cavalry")]) ||
      !append_count("archer_cavalry_raw",
                    base_counts[base_index("archer_cavalry")]) ||
      !append_count("gunpowder_raw",
                    base_counts[base_index("gunpowder")])) {
    return false;
  }
  const auto crossbow = crossbow_counts[0] + crossbow_counts[1] +
                        crossbow_counts[2];
  if (!append_count("crossbow_family_raw", crossbow) ||
      !append_count("non_crossbow_archers_raw",
                    base_counts[base_index("archers")] - crossbow)) {
    return false;
  }
  return ResolveComponent(module, kInternalArmyStoreSlot,
                          base_army.native_carmy_id, 0x10) == army &&
         LoadAt<void *>(army, 0x38) == native_regiment_ids &&
         LoadAt<std::int32_t>(army, 0x44) == native_regiment_count;
}

bool ReadCharacterPhaseRow(std::uintptr_t module,
                           const TraitReadContext &traits,
                           const QueryDefinitionContext &definitions,
                           CombatPhaseCharacterV3 &output,
                           std::string &failure) noexcept {
  failure.clear();
  const auto fail = [&failure, &output](std::string_view stage) {
    failure = "native_phase_character_reader_";
    failure += stage;
    failure += ':';
    failure += std::to_string(output.character_id);
    return false;
  };
  void *const character = ResolveComponent(
      module, kCharacterStoreSlot, output.character_id, 0x18);
  if (character == nullptr ||
      IsFallback(module, kCharacterFallbackSlot, character)) {
    return fail("resolve_failed");
  }
  if (!ReadCharacterIdentity(module, character, output.character_id, output)) {
    return fail("identity_unavailable");
  }
  if (!ReadCharacterTraits(module, traits, character, output)) {
    return fail("traits_unavailable");
  }
  if (!ReadCharacterRelationsAndPerks(module, definitions, character,
                                      output)) {
    return fail("relations_perks_unavailable");
  }
  if (!ReadFaithCulture(module, definitions, character, output)) {
    return fail("faith_culture_unavailable");
  }
  std::string accolade_failure;
  if (!ReadAccolade(module, definitions, character, output,
                    accolade_failure)) {
    failure = accolade_failure.empty()
                  ? "native_phase_character_reader_accolade_unavailable:" +
                        std::to_string(output.character_id)
                  : std::move(accolade_failure);
    return false;
  }
  if (!ReadVariables(module, definitions, character, output)) {
    return fail("variables_unavailable");
  }
  if (!ReadGovernment(module, definitions, character, output)) {
    return fail("government_unavailable");
  }
  if (!ReadCourtPosition(module, definitions, character, output)) {
    return fail("court_position_unavailable");
  }
  if (ResolveComponent(module, kCharacterStoreSlot, output.character_id,
                       0x18) != character) {
    return fail("generation_drift");
  }
  return true;
}

bool AppendOrMergeCharacter(std::vector<CombatPhaseCharacterV3> &characters,
                            CombatPhaseCharacterV3 row) noexcept {
  const auto existing = std::find_if(
      characters.begin(), characters.end(), [&row](const auto &candidate) {
        return candidate.character_id == row.character_id &&
               candidate.source_army_id == row.source_army_id;
      });
  if (existing == characters.end()) {
    characters.push_back(std::move(row));
    return true;
  }
  if (row.phase_roles != std::vector<std::string>{"knight"} ||
      existing->phase_roles != std::vector<std::string>{"commander"} ||
      existing->source_regiment_id != -1 || row.source_regiment_id <= 0) {
    return false;
  }
  existing->phase_roles = {"commander", "knight"};
  existing->source_regiment_id = row.source_regiment_id;
  return true;
}

bool BuildCharacterRoster(std::uintptr_t module,
                          const game::CombatSimulationInputsSnapshot &base,
                          std::vector<CombatPhaseCharacterV3> &characters,
                          std::vector<CombatPhaseSideV3> &sides,
                          std::string &failure) noexcept {
  characters.clear();
  sides.clear();
  failure.clear();
  const auto fail = [&failure](std::string_view stage,
                               std::int32_t first = -1,
                               std::int32_t second = -1) {
    failure = "native_phase_roster_";
    failure += stage;
    if (first >= 0) {
      failure += ':';
      failure += std::to_string(first);
    }
    if (second >= 0) {
      failure += ':';
      failure += std::to_string(second);
    }
    return false;
  };
  sides.resize(2);
  sides[0].side_index = 0;
  sides[0].encounter_role = "attacker";
  sides[0].ordered_army_ids = base.scenario.attacker_army_ids;
  sides[1].side_index = 1;
  sides[1].encounter_role = "defender";
  sides[1].ordered_army_ids = base.scenario.defender_army_ids;

  std::array<std::vector<CombatPhaseCandidateSourceRowV3>, 2>
      expected_commander_sources;
  std::array<std::vector<CombatPhaseCandidateSourceRowV3>, 2>
      expected_knight_sources;

  for (const auto &army : base.armies) {
    const auto side_index = army.encounter_role == "attacker" ? 0 : 1;
    if (army.encounter_role != "attacker" &&
        army.encounter_role != "defender") {
      return fail("army_role_invalid", army.army_id);
    }
    auto &side = sides[side_index];
    if (army.commander.status == game::CombatObservationStatus::available) {
      CombatPhaseCharacterV3 row{};
      row.character_id = army.commander.character_id;
      row.source_army_id = army.army_id;
      row.encounter_role = army.encounter_role;
      row.phase_roles = {"commander"};
      if (row.character_id <= 0) {
        return fail("commander_id_invalid", army.army_id);
      }
      if (!AppendOrMergeCharacter(characters, row)) {
        return fail("commander_merge_invalid", army.army_id,
                    row.character_id);
      }
      side.ordered_commander_ids.push_back(row.character_id);
      expected_commander_sources[side_index].push_back(
          {"commander", army.army_id, -1, row.character_id});
    } else if (army.commander.status ==
               game::CombatObservationStatus::unavailable) {
      return fail("commander_unavailable", army.army_id);
    }

    std::vector<std::pair<std::int32_t, std::int32_t>> native_knights;
    for (const auto &regiment_row : army.regiments) {
      void *const regiment = ResolveComponent(
          module, kRegimentStoreSlot, regiment_row.regiment_id, 0x10);
      if (regiment == nullptr ||
          IsFallback(module, kRegimentFallbackSlot, regiment)) {
        return fail("regiment_resolve_failed", army.army_id,
                    regiment_row.regiment_id);
      }
      if (LoadAt<std::int32_t>(regiment, 0x140) !=
          army.native_carmy_id) {
        return fail("regiment_army_mismatch", army.army_id,
                    regiment_row.regiment_id);
      }
      const auto character_id = LoadAt<std::int32_t>(regiment, 0x148);
      if (character_id == -1) {
        continue;
      }
      if (character_id <= 0) {
        return fail("knight_id_invalid", army.army_id,
                    regiment_row.regiment_id);
      }
      void *const character = ResolveComponent(
          module, kCharacterStoreSlot, character_id, 0x18);
      void *const link =
          character == nullptr ? nullptr : LoadAt<void *>(character, 0x1B0);
      if (character == nullptr ||
          IsFallback(module, kCharacterFallbackSlot, character)) {
        return fail("knight_character_resolve_failed", army.army_id,
                    character_id);
      }
      if (link == nullptr ||
          LoadAt<std::int32_t>(link, 0xF8) != regiment_row.regiment_id) {
        return fail("knight_regiment_backlink_mismatch", army.army_id,
                    regiment_row.regiment_id);
      }
      native_knights.emplace_back(character_id, regiment_row.regiment_id);
      CombatPhaseCharacterV3 row{};
      row.character_id = character_id;
      row.source_army_id = army.army_id;
      row.source_regiment_id = regiment_row.regiment_id;
      row.encounter_role = army.encounter_role;
      row.phase_roles = {"knight"};
      if (!AppendOrMergeCharacter(characters, std::move(row))) {
        return fail("knight_merge_invalid", army.army_id, character_id);
      }
      side.ordered_knight_ids.push_back(character_id);
      expected_knight_sources[side_index].push_back(
          {"knight", army.army_id, regiment_row.regiment_id, character_id});
    }
    if (!army.knights.available) {
      return fail("base_knights_unavailable", army.army_id);
    }
    if (native_knights.size() != army.knights.members.size()) {
      return fail("base_knights_count_mismatch", army.army_id);
    }
    for (const auto &[character_id, regiment_id] : native_knights) {
      const auto matched = std::find_if(
          army.knights.members.begin(), army.knights.members.end(),
          [character_id, regiment_id](const auto &candidate) {
            return candidate.character_id == character_id &&
                   candidate.source_regiment_id == regiment_id;
          });
      if (matched == army.knights.members.end()) {
        return fail("base_knight_member_mismatch", army.army_id,
                    regiment_id);
      }
    }
  }
  for (std::size_t side_index = 0; side_index < sides.size(); ++side_index) {
    auto &side = sides[side_index];
    for (const auto &row : characters) {
      if (row.encounter_role == side.encounter_role) {
        side.ordered_character_ids.push_back(row.character_id);
      }
    }
    auto &expected = side.candidate_source_proof.ordered_sources;
    expected = std::move(expected_commander_sources[side_index]);
    expected.insert(expected.end(),
                    std::make_move_iterator(
                        expected_knight_sources[side_index].begin()),
                    std::make_move_iterator(
                        expected_knight_sources[side_index].end()));
    side.candidate_source_proof.policy =
        std::string(kCandidateSourceProofPolicy);
    side.candidate_source_proof.source_vector_equivalence = false;
    side.candidate_source_proof.sequence_sha256.clear();
    if (side.ordered_army_ids.empty()) {
      return fail("side_armies_empty", static_cast<std::int32_t>(side_index));
    }
  }
  return true;
}

bool FixedMultiply(std::int64_t left, std::int64_t right,
                   std::int64_t &output) noexcept {
  if (left == 0 || right == 0) {
    output = 0;
    return true;
  }
  if ((left == -1 &&
       right == std::numeric_limits<std::int64_t>::min()) ||
      (right == -1 &&
       left == std::numeric_limits<std::int64_t>::min())) {
    return false;
  }
  if (left > 0) {
    if ((right > 0 &&
         left > std::numeric_limits<std::int64_t>::max() / right) ||
        (right < 0 &&
         right < std::numeric_limits<std::int64_t>::min() / left)) {
      return false;
    }
  } else if ((right > 0 &&
              left < std::numeric_limits<std::int64_t>::min() / right) ||
             (right < 0 &&
              left < std::numeric_limits<std::int64_t>::max() / right)) {
    return false;
  }
  const auto product = left * right;
  output = product / kFixedScale;
  return true;
}

bool ReadSideStrengthMirror(
    const std::vector<const game::CombatArmyInputsSnapshot *> &armies,
    std::int32_t &strength, std::int64_t &army_size_raw) noexcept {
  std::int64_t strength_sum = 0;
  std::int64_t soldier_sum = 0;
  for (const auto *army : armies) {
    if (army == nullptr || !army->regiments_observable) {
      return false;
    }
    for (const auto &regiment : army->regiments) {
      if (!regiment.identity_valid ||
          regiment.kind.status != game::CombatObservationStatus::available ||
          !regiment.effective_stats.available ||
          regiment.current_soldiers < 0) {
        return false;
      }
      if (soldier_sum > std::numeric_limits<std::int32_t>::max() -
                            regiment.current_soldiers) {
        return false;
      }
      soldier_sum += regiment.current_soldiers;
      if (!regiment.kind.fights_in_main_phase) {
        continue;
      }
      if ((regiment.effective_stats.toughness_raw > 0 &&
           regiment.effective_stats.damage_raw >
               std::numeric_limits<std::int64_t>::max() -
                   regiment.effective_stats.toughness_raw) ||
          (regiment.effective_stats.toughness_raw < 0 &&
           regiment.effective_stats.damage_raw <
               std::numeric_limits<std::int64_t>::min() -
                   regiment.effective_stats.toughness_raw)) {
        return false;
      }
      const auto stat_sum = regiment.effective_stats.damage_raw +
                            regiment.effective_stats.toughness_raw;
      std::int64_t current_raw =
          static_cast<std::int64_t>(regiment.current_soldiers) * kFixedScale;
      std::int64_t first = 0;
      if (!FixedMultiply(current_raw, stat_sum, first)) {
        return false;
      }
      const auto entry_strength = first / kFixedScale;
      if ((entry_strength > 0 &&
           strength_sum > std::numeric_limits<std::int32_t>::max() -
                              entry_strength) ||
          (entry_strength < 0 &&
           strength_sum < std::numeric_limits<std::int32_t>::min() -
                              entry_strength)) {
        return false;
      }
      strength_sum += entry_strength;
    }
  }
  strength = static_cast<std::int32_t>(strength_sum);
  return CheckedScaleCount(soldier_sum, army_size_raw);
}

bool ReadSideParticipants(
    std::uintptr_t module,
    const std::vector<const game::CombatArmyInputsSnapshot *> &armies,
    CombatPhaseSideV3 &side) noexcept {
  side.participants.clear();
  for (const auto *army : armies) {
    void *const unit = ResolveComponent(module, kPublicArmyStoreSlot,
                                        army->army_id, 0x10);
    if (unit == nullptr || LoadAt<std::int32_t>(unit, 0x178) !=
                               army->native_carmy_id) {
      return false;
    }
    const auto owner_id = LoadAt<std::int32_t>(unit, 0x174);
    const auto existing =
        std::find_if(side.participants.begin(), side.participants.end(),
                     [owner_id](const auto &row) {
                       return row.owner_character_id == owner_id;
                     });
    if (existing != side.participants.end()) {
      continue;
    }
    void *const owner = ResolveComponent(module, kCharacterStoreSlot,
                                         owner_id, 0x18);
    if (owner == nullptr ||
        IsFallback(module, kCharacterFallbackSlot, owner)) {
      return false;
    }
    const auto faith_id = LoadAt<std::int32_t>(owner, 0xB4);
    void *const faith =
        ResolveComponent(module, kFaithStoreSlot, faith_id, 0x08);
    if (faith == nullptr || IsFallback(module, kFaithFallbackSlot, faith)) {
      return false;
    }
    side.participants.push_back({army->army_id, owner_id, faith_id});
  }
  if (side.participants.empty()) {
    return false;
  }
  side.primary_source_army_id = armies.front()->army_id;
  side.primary_participant_character_id =
      side.participants.front().owner_character_id;
  return true;
}

using FaithHostility = std::int32_t (*)(void *, void *, void *);

bool ReadFaithHostilityMatrix(
    std::uintptr_t module,
    const std::vector<CombatPhaseCharacterV3> &characters,
    const std::vector<CombatPhaseSideV3> &sides,
    std::vector<CombatPhaseFaithHostilityV3> &output) noexcept {
  output.clear();
  if (sides.size() != 2) {
    return false;
  }
  const auto hostility =
      reinterpret_cast<FaithHostility>(module + kFaithHostilityRva);
  for (const auto &root : characters) {
    if (!root.faith.present || root.faith.value <= 0) {
      // A valid optional faith scope produces no hostility matches.
      continue;
    }
    const auto own_side = root.encounter_role == "attacker" ? 0 : 1;
    if (root.encounter_role != "attacker" &&
        root.encounter_role != "defender") {
      return false;
    }
    const auto enemy_side = 1 - own_side;
    void *const root_faith = ResolveComponent(
        module, kFaithStoreSlot, root.faith.value, 0x08);
    if (root_faith == nullptr ||
        IsFallback(module, kFaithFallbackSlot, root_faith)) {
      return false;
    }
    for (const auto &enemy : sides[static_cast<std::size_t>(enemy_side)]
                                 .participants) {
      void *const enemy_faith = ResolveComponent(
          module, kFaithStoreSlot, enemy.faith_id, 0x08);
      if (enemy_faith == nullptr ||
          IsFallback(module, kFaithFallbackSlot, enemy_faith)) {
        return false;
      }
      const auto level = hostility(
          static_cast<std::byte *>(enemy_faith) + 0x278, enemy_faith,
          root_faith);
      if (level < 0 || level > 3) {
        return false;
      }
      output.push_back({root.character_id, enemy_side,
                        enemy.owner_character_id, enemy.faith_id,
                        root.faith.value, level});
    }
  }
  return true;
}

bool CollectSideArmies(
    const game::CombatSimulationInputsSnapshot &base,
    std::string_view encounter_role,
    std::vector<const game::CombatArmyInputsSnapshot *> &output) noexcept {
  output.clear();
  const auto &expected = encounter_role == "attacker"
                             ? base.scenario.attacker_army_ids
                             : base.scenario.defender_army_ids;
  if (encounter_role != "attacker" && encounter_role != "defender") {
    return false;
  }
  output.reserve(expected.size());
  for (const auto army_id : expected) {
    const auto iterator = std::find_if(
        base.armies.begin(), base.armies.end(),
        [army_id, encounter_role](const auto &army) {
          return army.army_id == army_id &&
                 army.encounter_role == encounter_role;
        });
    if (iterator == base.armies.end()) {
      return false;
    }
    output.push_back(&*iterator);
  }
  return output.size() == expected.size();
}

bool RevalidatePhaseObjects(
    std::uintptr_t module,
    const std::vector<CombatPhaseCharacterV3> &characters,
    const std::vector<CombatPhaseArmyV3> &armies,
    const std::vector<CombatPhaseSideV3> &sides) noexcept {
  for (const auto &character : characters) {
    void *const object = ResolveComponent(
        module, kCharacterStoreSlot, character.character_id, 0x18);
    if (object == nullptr ||
        IsFallback(module, kCharacterFallbackSlot, object)) {
      return false;
    }
  }
  for (const auto &army : armies) {
    void *const object = ResolveComponent(
        module, kInternalArmyStoreSlot, army.native_carmy_id, 0x10);
    if (object == nullptr ||
        IsFallback(module, kInternalArmyFallbackSlot, object)) {
      return false;
    }
  }
  for (const auto &side : sides) {
    for (const auto &participant : side.participants) {
      void *const owner = ResolveComponent(
          module, kCharacterStoreSlot, participant.owner_character_id,
          0x18);
      void *const faith = ResolveComponent(
          module, kFaithStoreSlot, participant.faith_id, 0x08);
      if (owner == nullptr || faith == nullptr ||
          IsFallback(module, kCharacterFallbackSlot, owner) ||
          IsFallback(module, kFaithFallbackSlot, faith) ||
          LoadAt<std::int32_t>(owner, 0xB4) != participant.faith_id) {
        return false;
      }
    }
  }
  return true;
}

struct NativeArrayHeaderV3 {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
static_assert(sizeof(NativeArrayHeaderV3) == 0x10);

struct NativeAdvantageLedgerEntryV3 {
  void *effect = nullptr;
  std::int64_t scale_raw = 0;
};
static_assert(sizeof(NativeAdvantageLedgerEntryV3) == 0x10);

struct AdvantageArmyContextV3 {
  const game::CombatArmyInputsSnapshot *snapshot = nullptr;
  void *army = nullptr;
  void *unit = nullptr;
  void *owner = nullptr;
  std::int32_t owner_character_id = -1;
};

using GetCombatRuleDatabaseV3 = void *(*)();
using SelectSupplyAdvantageV3 = void *(*)(NativeArrayHeaderV3 *);
using SelectDebtAdvantageV3 = std::int32_t (*)(void *, std::int32_t);
using ResolveRealmTreasuryV3 = void *(*)(const std::int32_t *);
using ReadFaithDoctrineParameterV3 = void *(*)(void *, std::int32_t);
using ReadProvinceModifierV3 = std::int64_t *(*)(
    std::int64_t *, void *, std::int32_t, std::int32_t, void *);
using ReadModifierValueV3 = std::int64_t *(*)(
    std::int64_t *, void *, std::int32_t, void *, std::int64_t,
    std::int32_t);
using ProvincePredicateV3 = bool (*)(void *);
using ModifierFlagPredicateV3 = bool (*)(void *, std::int32_t);
using ConstructCombatSideV3 = void *(*)(void *, void *);
using PopulateCombatSideV3 = void (*)(void *, void *);
using SelectBattleCommanderV3 = void *(*)(void *);
using RefreshCombatSideStrengthV3 = void (*)(void *);
using ReadCombatSideStrengthV3 = std::int32_t (*)(void *);
using DestroyCombatSideV3 = void (*)(void *);
using ResolveCombatAdvantageV3 = void (*)(void *);
using ReadSideDynamicAdvantageV3 = std::int64_t *(*)(
    void *, std::int64_t *, std::int32_t, void *);
using ReadCommanderDynamicAdvantageV3 = std::int64_t *(*)(
    void *, std::int64_t *, void *, std::int32_t, std::int32_t, void *);
using ReadSideModifierAdvantageV3 = std::int64_t *(*)(
    void *, std::int64_t *, void *, std::int32_t, std::int32_t, void *);
using ReadCombatRelationKindV3 = std::int32_t (*)(void *, std::int32_t);
using NativeAllocateV3 = void *(*)(void *, std::size_t, std::size_t);
using NativeFreeV3 = void (*)(void *, void *, std::size_t);

void *ResolveProvinceV3(const Bindings &bindings,
                        std::int32_t province_id) noexcept {
  if (province_id < 1 || bindings.game_state_slot == nullptr) {
    return nullptr;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const game_data =
      game_state == nullptr
          ? nullptr
          : LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const provinces =
      LoadAt<void *>(game_data, kGameDataProvinceArrayOffset);
  const auto province_count =
      LoadAt<std::int32_t>(game_data, kGameDataProvinceCountOffset);
  if (provinces == nullptr || province_count <= 1 ||
      province_id >= province_count) {
    return nullptr;
  }
  void *const province = LoadAt<void *>(
      provinces, static_cast<std::size_t>(province_id) * sizeof(void *));
  return province != nullptr &&
                 LoadAt<std::int32_t>(province, kProvinceIdOffset) ==
                     province_id
             ? province
             : nullptr;
}

bool CheckedAddV3(std::int64_t left, std::int64_t right,
                  std::int64_t &output) noexcept {
  if ((right > 0 &&
       left > std::numeric_limits<std::int64_t>::max() - right) ||
      (right < 0 &&
       left < std::numeric_limits<std::int64_t>::min() - right)) {
    return false;
  }
  output = left + right;
  return true;
}

bool CheckedSubtractV3(std::int64_t left, std::int64_t right,
                       std::int64_t &output) noexcept {
  if (right == std::numeric_limits<std::int64_t>::min()) {
    if (left >= 0) {
      return false;
    }
    output = left - right;
    return true;
  }
  return CheckedAddV3(left, -right, output);
}

bool CheckedNegateV3(std::int64_t value, std::int64_t &output) noexcept {
  if (value == std::numeric_limits<std::int64_t>::min()) {
    return false;
  }
  output = -value;
  return true;
}

bool CheckedPointsScaleV3(std::int32_t points, std::int64_t scale_raw,
                          std::int64_t &output) noexcept {
  const auto points_raw = static_cast<std::int64_t>(points) * kFixedScale;
  return FixedMultiply(points_raw, scale_raw, output);
}

bool ReadEffectKeyV3(void *effect, std::string &output) noexcept {
  output.clear();
  return effect != nullptr &&
         ReadMsvcString(static_cast<std::byte *>(effect) +
                            kEffectStableKeyOffset,
                        output) &&
         !output.empty();
}

bool RequireEffectKeyV3(void *effect, std::string_view expected) noexcept {
  return StableKeyEquals(effect, kEffectStableKeyOffset, expected);
}

bool ReadEffectValidityV3(void *effect, bool &valid) noexcept {
  valid = false;
  return effect != nullptr && VcallBool(effect, 0, valid);
}

bool BuildAdvantageArmyContextsV3(
    std::uintptr_t module,
    const game::CombatSimulationInputsSnapshot &base,
    std::array<std::vector<AdvantageArmyContextV3>, 2> &output) noexcept {
  output = {};
  for (std::size_t side_index = 0; side_index < output.size();
       ++side_index) {
    const auto role = side_index == 0 ? std::string_view{"attacker"}
                                      : std::string_view{"defender"};
    std::vector<const game::CombatArmyInputsSnapshot *> snapshots;
    if (!CollectSideArmies(base, role, snapshots) || snapshots.empty()) {
      return false;
    }
    auto &rows = output[side_index];
    rows.reserve(snapshots.size());
    for (const auto *snapshot : snapshots) {
      if (snapshot == nullptr || !snapshot->available ||
          !snapshot->native_carmy_id_observable ||
          snapshot->native_carmy_id <= 0 || snapshot->army_id <= 0 ||
          snapshot->owner.status != game::CombatObservationStatus::available) {
        return false;
      }
      void *const army = ResolveComponent(
          module, kInternalArmyStoreSlot, snapshot->native_carmy_id, 0x10);
      if (army == nullptr ||
          IsFallback(module, kInternalArmyFallbackSlot, army)) {
        return false;
      }
      const auto unit_id = LoadAt<std::int32_t>(army, 0x124);
      if (unit_id != snapshot->army_id) {
        return false;
      }
      void *const unit = ResolveComponent(
          module, kPublicArmyStoreSlot, unit_id, 0x10);
      if (unit == nullptr) {
        return false;
      }
      const auto owner_id = LoadAt<std::int32_t>(unit, 0x174);
      void *const owner = ResolveComponent(
          module, kCharacterStoreSlot, owner_id, 0x18);
      if (owner == nullptr ||
          IsFallback(module, kCharacterFallbackSlot, owner) ||
          owner_id != snapshot->owner.character_id) {
        return false;
      }
      rows.push_back({snapshot, army, unit, owner, owner_id});
    }
  }
  return true;
}

bool RevalidateAdvantageArmyContextsV3(
    std::uintptr_t module,
    const std::array<std::vector<AdvantageArmyContextV3>, 2> &sides) noexcept {
  for (const auto &side : sides) {
    for (const auto &row : side) {
      if (row.snapshot == nullptr ||
          ResolveComponent(module, kInternalArmyStoreSlot,
                           row.snapshot->native_carmy_id, 0x10) != row.army ||
          ResolveComponent(module, kPublicArmyStoreSlot,
                           row.snapshot->army_id, 0x10) != row.unit ||
          ResolveComponent(module, kCharacterStoreSlot,
                           row.owner_character_id, 0x18) != row.owner ||
          LoadAt<std::int32_t>(row.army, 0x124) !=
              row.snapshot->army_id ||
          LoadAt<std::int32_t>(row.unit, 0x174) !=
              row.owner_character_id) {
        return false;
      }
    }
  }
  return true;
}

bool ValidatePopulatedCombatSideV3(
    void *side, void *local_context,
    const std::vector<AdvantageArmyContextV3> &armies) noexcept {
  if (side == nullptr || local_context == nullptr || armies.empty() ||
      armies.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  void *const army_ids = LoadAt<void *>(side, 0x10);
  const auto army_count = LoadAt<std::int32_t>(side, 0x1C);
  if (!ValidSpan(army_ids, army_count) ||
      army_count != static_cast<std::int32_t>(armies.size()) ||
      LoadAt<std::int32_t>(side, 0x70) !=
          armies.front().owner_character_id ||
      LoadAt<void *>(side, kCombatSideLocalContextOffset) != local_context ||
      LoadAt<void *>(local_context, kLocalPopulationAllocatorOffset) !=
          LoadAt<void *>(side, 0x50)) {
    return false;
  }
  for (std::size_t index = 0; index < armies.size(); ++index) {
    if (armies[index].snapshot == nullptr ||
        LoadAt<std::int32_t>(army_ids, index * sizeof(std::int32_t)) !=
            armies[index].snapshot->native_carmy_id) {
      return false;
    }
  }
  void *const population_entries =
      LoadAt<void *>(local_context, kLocalPopulationEntriesOffset);
  const auto population_capacity = LoadAt<std::int32_t>(
      local_context, kLocalPopulationEntriesOffset + 0x08);
  const auto population_count = LoadAt<std::int32_t>(
      local_context, kLocalPopulationEntriesOffset + 0x0C);
  return ValidSpan(population_entries, population_count) &&
         population_capacity >= population_count &&
         population_capacity <= kMaximumRows;
}

const AdvantageArmyContextV3 *FindCandidateSourceArmyV3(
    const std::vector<AdvantageArmyContextV3> &armies,
    std::int32_t native_carmy_id) noexcept {
  const AdvantageArmyContextV3 *match = nullptr;
  for (const auto &row : armies) {
    if (row.snapshot != nullptr &&
        row.snapshot->native_carmy_id == native_carmy_id) {
      if (match != nullptr) {
        return nullptr;
      }
      match = &row;
    }
  }
  return match;
}

bool CandidateSourceArmyContainsRegimentV3(
    const AdvantageArmyContextV3 &army,
    std::int32_t regiment_id) noexcept {
  if (army.snapshot == nullptr || !army.snapshot->regiments_observable) {
    return false;
  }
  const game::CombatRegimentSnapshot *match = nullptr;
  for (const auto &row : army.snapshot->regiments) {
    if (row.regiment_id == regiment_id) {
      if (match != nullptr) {
        return false;
      }
      match = &row;
    }
  }
  return match != nullptr && match->available && match->identity_valid;
}

bool ReadNativeCandidateSourceRowsV3(
    std::uintptr_t module, void *side,
    const std::vector<AdvantageArmyContextV3> &armies,
    std::vector<CombatPhaseCandidateSourceRowV3> &output) {
  output.clear();
  if (module == 0 || side == nullptr || armies.empty() ||
      armies.size() > static_cast<std::size_t>(kMaximumRows)) {
    return false;
  }

  // Exact source leaf used by CCombatSideCommanderListBuilder/0x19DD750.
  // Reading the already populated vector avoids allocating script scopes while
  // preserving the native helper's stored CArmyID order.
  void *const army_ids = LoadAt<void *>(side, kCombatSideArmyIdsOffset);
  const auto army_capacity =
      LoadAt<std::int32_t>(side, kCombatSideArmyIdsCapacityOffset);
  const auto army_count =
      LoadAt<std::int32_t>(side, kCombatSideArmyIdsCountOffset);
  if (!ValidSpan(army_ids, army_count) || army_capacity < army_count ||
      army_capacity > kMaximumRows ||
      army_count != static_cast<std::int32_t>(armies.size())) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(army_count));
  for (std::int32_t index = 0; index < army_count; ++index) {
    const auto native_carmy_id = LoadAt<std::int32_t>(
        army_ids, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    const auto *const army =
        FindCandidateSourceArmyV3(armies, native_carmy_id);
    if (army == nullptr || army->snapshot == nullptr || army->army == nullptr ||
        army->snapshot->army_id <= 0 ||
        ResolveComponent(module, kInternalArmyStoreSlot, native_carmy_id,
                         0x10) != army->army) {
      return false;
    }
    const auto character_id = LoadAt<std::int32_t>(army->army, 0x120);
    if (character_id == -1) {
      continue;
    }
    void *const character = ResolveComponent(
        module, kCharacterStoreSlot, character_id, 0x18);
    if (character_id <= 0 || character == nullptr ||
        IsFallback(module, kCharacterFallbackSlot, character)) {
      return false;
    }
    output.push_back({"commander", army->snapshot->army_id, -1,
                      character_id});
  }

  // Exact source leaf used by CCombatSideKnightListBuilder/0x19DD670.  The
  // source builder itself only turns these rows into kind-4 script scopes; the
  // row vector is therefore the allocation-free equivalent native reader.
  void *const knight_entries =
      LoadAt<void *>(side, kCombatSideKnightEntriesOffset);
  const auto knight_capacity = LoadAt<std::int32_t>(
      side, kCombatSideKnightEntriesCapacityOffset);
  const auto knight_count =
      LoadAt<std::int32_t>(side, kCombatSideKnightEntriesCountOffset);
  if (!ValidSpan(knight_entries, knight_count) ||
      knight_capacity < knight_count || knight_capacity > kMaximumRows ||
      static_cast<std::size_t>(knight_count) >
          (std::numeric_limits<std::size_t>::max() /
           kCombatSideKnightEntryStride)) {
    return false;
  }
  output.reserve(output.size() + static_cast<std::size_t>(knight_count));
  for (std::int32_t index = 0; index < knight_count; ++index) {
    const auto *const entry =
        static_cast<const std::byte *>(knight_entries) +
        static_cast<std::size_t>(index) * kCombatSideKnightEntryStride;
    const auto regiment_id = LoadAt<std::int32_t>(
        entry, kCombatSideKnightRegimentIdOffset);
    void *const regiment = ResolveComponent(
        module, kRegimentStoreSlot, regiment_id, 0x10);
    if (regiment_id <= 0 || regiment == nullptr ||
        IsFallback(module, kRegimentFallbackSlot, regiment)) {
      return false;
    }
    const auto native_carmy_id = LoadAt<std::int32_t>(regiment, 0x140);
    const auto *const army =
        FindCandidateSourceArmyV3(armies, native_carmy_id);
    if (army == nullptr || army->snapshot == nullptr ||
        army->snapshot->army_id <= 0 ||
        !CandidateSourceArmyContainsRegimentV3(*army, regiment_id)) {
      return false;
    }
    const auto character_id = LoadAt<std::int32_t>(regiment, 0x148);
    if (character_id == -1) {
      continue;
    }
    void *const character = ResolveComponent(
        module, kCharacterStoreSlot, character_id, 0x18);
    void *const relation =
        character == nullptr ? nullptr : LoadAt<void *>(character, 0x1B0);
    if (character_id <= 0 || character == nullptr ||
        IsFallback(module, kCharacterFallbackSlot, character) ||
        relation == nullptr ||
        LoadAt<std::int32_t>(relation, 0xF8) != regiment_id) {
      return false;
    }
    output.push_back({"knight", army->snapshot->army_id, regiment_id,
                      character_id});
  }
  return true;
}

bool SealCandidateSourceProofV3(
    CombatPhaseSideV3 &side,
    std::vector<CombatPhaseCandidateSourceRowV3> native_rows) {
  auto &proof = side.candidate_source_proof;
  if (proof.policy != kCandidateSourceProofPolicy ||
      proof.source_vector_equivalence || !proof.sequence_sha256.empty() ||
      proof.ordered_sources != native_rows) {
    return false;
  }
  std::string digest;
  if (!CandidateSourceSequenceDigestV3(side.side_index, native_rows,
                                       digest)) {
    return false;
  }
  proof.ordered_sources = std::move(native_rows);
  proof.sequence_sha256 = std::move(digest);
  proof.source_vector_equivalence = true;
  return true;
}

bool ValidateCandidateSourceProofV3(
    const CombatPhaseSideV3 &side,
    const std::vector<CombatPhaseCharacterV3> &characters) {
  const auto &proof = side.candidate_source_proof;
  if (proof.policy != kCandidateSourceProofPolicy ||
      !proof.source_vector_equivalence ||
      proof.sequence_sha256.size() != 64) {
    return false;
  }
  std::vector<std::int32_t> commander_ids;
  std::vector<std::int32_t> knight_ids;
  bool reached_knights = false;
  for (const auto &source : proof.ordered_sources) {
    if (source.role == "commander") {
      if (reached_knights || source.source_regiment_id != -1) {
        return false;
      }
      commander_ids.push_back(source.character_id);
    } else if (source.role == "knight") {
      reached_knights = true;
      if (source.source_regiment_id <= 0) {
        return false;
      }
      knight_ids.push_back(source.character_id);
    } else {
      return false;
    }
    if (std::find(side.ordered_army_ids.begin(), side.ordered_army_ids.end(),
                  source.source_army_id) == side.ordered_army_ids.end()) {
      return false;
    }
    std::size_t matching_characters = 0;
    for (const auto &character : characters) {
      if (character.character_id != source.character_id ||
          character.source_army_id != source.source_army_id ||
          character.encounter_role != side.encounter_role ||
          std::find(character.phase_roles.begin(),
                    character.phase_roles.end(), source.role) ==
              character.phase_roles.end() ||
          (source.role == "knight" &&
           character.source_regiment_id != source.source_regiment_id)) {
        continue;
      }
      ++matching_characters;
    }
    if (matching_characters != 1) {
      return false;
    }
  }
  if (commander_ids != side.ordered_commander_ids ||
      knight_ids != side.ordered_knight_ids) {
    return false;
  }
  std::string digest;
  return CandidateSourceSequenceDigestV3(
             side.side_index, proof.ordered_sources, digest) &&
         digest == proof.sequence_sha256;
}

bool AddNonNegativeV3(std::int64_t value, std::int64_t &total) noexcept {
  return value >= 0 && CheckedAddV3(total, value, total);
}

bool ReadSupplyEligibleSoldiersV3(
    std::uintptr_t module,
    const std::vector<AdvantageArmyContextV3> &armies,
    std::array<std::int64_t, 3> &by_state) noexcept {
  by_state = {};
  const auto *const thresholds = *reinterpret_cast<const std::int32_t **>(
      module + kSupplyThresholdDataRva);
  const auto threshold_count = *reinterpret_cast<const std::int32_t *>(
      module + kSupplyThresholdCountRva);
  if (thresholds == nullptr || threshold_count < 3 ||
      threshold_count > 64) {
    return false;
  }
  for (const auto &row : armies) {
    if (row.snapshot == nullptr || !row.snapshot->regiments_observable) {
      return false;
    }
    const auto supply_whole =
        LoadAt<std::int64_t>(row.army, 0x180) / kFixedScale;
    std::int32_t state_index = threshold_count - 1;
    for (std::int32_t index = 0; index < threshold_count; ++index) {
      if (supply_whole >= thresholds[index]) {
        state_index = index;
        break;
      }
    }
    const std::size_t bucket =
        state_index == 0 ? 0U : (state_index == 1 ? 1U : 2U);
    for (const auto &regiment_snapshot : row.snapshot->regiments) {
      void *const regiment = ResolveComponent(
          module, kRegimentStoreSlot, regiment_snapshot.regiment_id, 0x10);
      if (regiment == nullptr ||
          IsFallback(module, kRegimentFallbackSlot, regiment) ||
          LoadAt<std::int32_t>(regiment, 0x140) !=
              row.snapshot->native_carmy_id) {
        return false;
      }
      bool identity_valid = false;
      if (!VcallBool(static_cast<std::byte *>(regiment) + 0x08, 0x08,
                     identity_valid) ||
          identity_valid != regiment_snapshot.identity_valid ||
          !identity_valid) {
        return false;
      }
      bool eligible = LoadAt<std::int32_t>(regiment, 0x14C) != 1;
      if (!eligible) {
        void *const membership_data = LoadAt<void *>(regiment, 0x20);
        const auto membership_count =
            LoadAt<std::int32_t>(regiment, 0x2C);
        if (membership_count < 0 || membership_count > kMaximumRows ||
            (membership_count > 0 && membership_data == nullptr)) {
          return false;
        }
        if (membership_count > 0) {
          const auto supply_unit_id =
              LoadAt<std::int32_t>(membership_data, 0x08);
          void *const supply_unit = ResolveComponent(
              module, kSupplyUnitStoreSlot, supply_unit_id, 0x10);
          if (supply_unit == nullptr ||
              IsFallback(module, kSupplyUnitFallbackSlot, supply_unit)) {
            return false;
          }
          eligible = LoadAt<std::uint8_t>(supply_unit, 0x141) != 0;
        }
      }
      const auto live_soldiers = LoadAt<std::int32_t>(regiment, 0x38);
      if (live_soldiers != regiment_snapshot.current_soldiers ||
          live_soldiers < 0) {
        return false;
      }
      if (eligible && !AddNonNegativeV3(live_soldiers, by_state[bucket])) {
        return false;
      }
    }
  }
  return true;
}

bool SelectSupplyBucketV3(const std::array<std::int64_t, 3> &by_state,
                          std::size_t &output) noexcept {
  std::int64_t total = 0;
  if (!CheckedAddV3(by_state[0], by_state[1], total) ||
      !CheckedAddV3(total, by_state[2], total)) {
    return false;
  }
  if (total <= 0 || by_state[0] > total - by_state[0]) {
    output = 0;
    return true;
  }
  std::int64_t supplied_or_low = 0;
  if (!CheckedAddV3(by_state[0], by_state[1], supplied_or_low)) {
    return false;
  }
  output = supplied_or_low > total - supplied_or_low ? 1U : 2U;
  return true;
}

bool ReadSupplySideInputV3(
    std::uintptr_t module, void *combat_rules,
    const std::vector<AdvantageArmyContextV3> &armies,
    game::CombatAdvantageSupplyInputV3TestOnly &output,
    void *&selected_effect) noexcept {
  output = {};
  selected_effect = nullptr;
  if (armies.empty()) {
    return false;
  }
  std::array<std::int64_t, 3> by_state{};
  if (!ReadSupplyEligibleSoldiersV3(module, armies, by_state)) {
    return false;
  }
  std::size_t selected_bucket = 0;
  if (!SelectSupplyBucketV3(by_state, selected_bucket)) {
    return false;
  }
  constexpr std::array<std::size_t, 3> offsets{
      kCombatRuleSupplySuppliedOffset,
      kCombatRuleSupplyRunningLowOffset,
      kCombatRuleSupplyStarvingOffset,
  };
  constexpr std::array<std::string_view, 3> keys{
      "supply_state_supplied_advantage",
      "supply_state_running_low_advantage",
      "supply_state_starving_advantage",
  };
  selected_effect =
      LoadAt<void *>(combat_rules, offsets[selected_bucket]);
  if (!RequireEffectKeyV3(selected_effect, keys[selected_bucket])) {
    return false;
  }
  std::vector<std::int32_t> native_army_ids;
  native_army_ids.reserve(armies.size());
  for (const auto &army : armies) {
    native_army_ids.push_back(army.snapshot->native_carmy_id);
  }
  NativeArrayHeaderV3 header{
      native_army_ids.data(), static_cast<std::int32_t>(native_army_ids.size()),
      static_cast<std::int32_t>(native_army_ids.size())};
  const auto selector = reinterpret_cast<SelectSupplyAdvantageV3>(
      module + kSupplyAdvantageSelectorRva);
  if (selector(&header) != selected_effect ||
      header.data != native_army_ids.data() ||
      header.count != static_cast<std::int32_t>(native_army_ids.size())) {
    return false;
  }
  std::int64_t total = 0;
  if (!CheckedAddV3(by_state[0], by_state[1], total) ||
      !CheckedAddV3(total, by_state[2], total)) {
    return false;
  }
  output.selected_key = std::string(keys[selected_bucket]);
  output.selected_effect_identity =
      selected_bucket == 0
          ? "loaded_combat_rule_database:+0xF38"
          : (selected_bucket == 1
                 ? "loaded_combat_rule_database:+0xF48"
                 : "loaded_combat_rule_database:+0xF58");
  output.selected_effect_points =
      LoadAt<std::int32_t>(selected_effect, kEffectAdvantagePointsOffset);
  output.eligible_soldiers_total = total;
  output.eligible_soldiers_supplied = by_state[0];
  output.eligible_soldiers_running_low = by_state[1];
  output.eligible_soldiers_starving = by_state[2];
  return true;
}

bool ResolveDebtEffectV3(void *combat_rules, std::int32_t selector,
                         bool treasury, void *&effect,
                         std::string &key) noexcept {
  effect = nullptr;
  key.clear();
  const auto count_offset = treasury ? kCombatRuleTreasuryDebtCountOffset
                                     : kCombatRuleOwnerDebtCountOffset;
  const auto data_offset = treasury ? kCombatRuleTreasuryDebtDataOffset
                                    : kCombatRuleOwnerDebtDataOffset;
  const auto count = LoadAt<std::int32_t>(combat_rules, count_offset);
  void *const data = LoadAt<void *>(combat_rules, data_offset);
  if (count <= 0 || count > 1'024 || data == nullptr || selector < 0 ||
      selector > count) {
    return false;
  }
  if (selector == count) {
    effect = LoadAt<void *>(combat_rules, kCombatRuleNoIncomeDebtOffset);
    key = "combat_debt_level_no_income";
  } else {
    effect = LoadAt<void *>(data, static_cast<std::size_t>(selector) * 8);
    key = treasury ? "treasury_combat_debt_level_"
                   : "combat_debt_level_";
    key += std::to_string(selector);
  }
  return RequireEffectKeyV3(effect, key);
}

bool ReadTreasuryDebtSelectorV3(std::uintptr_t module, void *owner,
                                std::int32_t &selector,
                                bool &observable) noexcept {
  selector = 0;
  observable = false;
  const auto government = reinterpret_cast<CharacterGovernment>(
      module + kCharacterGovernmentRva);
  void *const government_type = government(owner);
  if (government_type == nullptr) {
    return false;
  }
  const bool government_eligible =
      ((LoadAt<std::uint32_t>(government_type, 0x38) >> 29U) & 1U) != 0;
  if (!government_eligible || LoadAt<void *>(owner, 0x1A8) == nullptr) {
    return true;
  }

  std::int32_t realm_id = -1;
  void *const first_container = LoadAt<void *>(owner, 0x1B8);
  if (first_container != nullptr) {
    void *const data = LoadAt<void *>(first_container, 0x1E0);
    const auto count = LoadAt<std::int32_t>(first_container, 0x1EC);
    if (count < 0 || count > kMaximumRows ||
        (count > 0 && data == nullptr)) {
      return false;
    }
    if (count > 0) {
      realm_id = LoadAt<std::int32_t>(data, 0);
    }
  } else {
    void *const second_container = LoadAt<void *>(owner, 0x1C8);
    if (second_container != nullptr) {
      void *const data = LoadAt<void *>(second_container, 0x68);
      const auto count = LoadAt<std::int32_t>(second_container, 0x74);
      if (count < 0 || count > kMaximumRows ||
          (count > 0 && data == nullptr)) {
        return false;
      }
      if (count > 0) {
        realm_id = LoadAt<std::int32_t>(data, 0);
      }
    }
  }
  if (realm_id == -1) {
    return true;
  }
  const auto resolve_treasury = reinterpret_cast<ResolveRealmTreasuryV3>(
      module + kResolveRealmTreasuryRva);
  void *const treasury = resolve_treasury(&realm_id);
  bool treasury_valid = false;
  if (treasury == nullptr ||
      !VcallBool(static_cast<std::byte *>(treasury) + 0x08, 0x08,
                 treasury_valid) ||
      !treasury_valid) {
    return false;
  }
  if (LoadAt<std::int64_t>(treasury, 0x440) >= 0) {
    return true;
  }
  const auto debt_selector = reinterpret_cast<SelectDebtAdvantageV3>(
      module + kDebtAdvantageSelectorRva);
  selector = debt_selector(owner, 3);
  observable = true;
  return true;
}

bool ReadHoldingScaleV3(std::uintptr_t module, void *target,
                        std::int64_t &scale_raw) noexcept {
  scale_raw = 0;
  const auto read_province_modifier =
      reinterpret_cast<ReadProvinceModifierV3>(
          module + kReadProvinceModifierRva);
  std::int64_t base_scale = 0;
  if (read_province_modifier(&base_scale, target, 0x1DE, 0, nullptr) !=
      &base_scale) {
    return false;
  }
  scale_raw = base_scale;
  const auto province_has_holding = reinterpret_cast<ProvincePredicateV3>(
      module + kProvinceHasHoldingRva);
  if (province_has_holding(target)) {
    const auto read_modifier = reinterpret_cast<ReadModifierValueV3>(
        module + kReadModifierValueRva);
    std::int64_t holding_scale = 0;
    if (read_modifier(&holding_scale,
                      static_cast<std::byte *>(target) + 0x30, 0x1C9,
                      nullptr, kFixedScale, 0) != &holding_scale ||
        !CheckedAddV3(scale_raw, holding_scale, scale_raw)) {
      return false;
    }
  }
  return true;
}

bool ReadUnreformedTargetFaithV3(std::uintptr_t module, void *target,
                                 void *&faith, std::int32_t &faith_id,
                                 bool &enabled) noexcept {
  faith = nullptr;
  faith_id = -1;
  enabled = false;
  void *const holding = LoadAt<void *>(target, 0x850);
  if (holding == nullptr) {
    return false;
  }
  faith_id = LoadAt<std::int32_t>(holding, 0x368);
  faith = ResolveComponent(module, kFaithStoreSlot, faith_id, 0x08);
  if (faith == nullptr || IsFallback(module, kFaithFallbackSlot, faith)) {
    return false;
  }
  const auto read_parameter =
      reinterpret_cast<ReadFaithDoctrineParameterV3>(
          module + kFaithDoctrineParameterRva);
  void *const parameter = read_parameter(
      static_cast<std::byte *>(faith) + 0x278, 0x304D);
  enabled = parameter != nullptr &&
            LoadAt<std::uint8_t>(parameter, 0x08) != 0;
  return true;
}

bool NativeFreeBufferV3(void *allocator, void *buffer) noexcept {
  if (buffer == nullptr) {
    return true;
  }
  if (allocator == nullptr) {
    return false;
  }
  void *const vtable = LoadAt<void *>(allocator, 0);
  const auto address =
      vtable == nullptr ? 0 : LoadAt<std::uintptr_t>(vtable, 0x10);
  if (address == 0) {
    return false;
  }
  reinterpret_cast<NativeFreeV3>(address)(allocator, buffer, 8);
  return true;
}

class LocalCombatContextV3 final {
public:
  explicit LocalCombatContextV3(DestroyCombatSideV3 destroy) noexcept
      : destroy_(destroy) {}

  LocalCombatContextV3(const LocalCombatContextV3 &) = delete;
  LocalCombatContextV3 &operator=(const LocalCombatContextV3 &) = delete;

  ~LocalCombatContextV3() noexcept { (void)CleanupChecked(); }

  void *shell() noexcept { return shell_.data(); }

  void *side(std::size_t index) noexcept {
    return shell_.data() +
           (index == 0 ? kCombatSide0Offset : kCombatSide1Offset);
  }

  void *local_context(std::size_t index) noexcept {
    return local_contexts_[index].data();
  }

  void MarkConstructed() noexcept { ++constructed_count_; }

  bool CleanupChecked() noexcept {
    if (cleaned_) {
      return cleanup_succeeded_;
    }
    cleaned_ = true;
    std::array<void *, 2> population_buffers{};
    std::array<void *, 2> population_allocators{};
    for (std::size_t index = 0; index < constructed_count_; ++index) {
      void *const local = local_context(index);
      population_buffers[index] =
          LoadAt<void *>(local, kLocalPopulationEntriesOffset);
      population_allocators[index] =
          LoadAt<void *>(local, kLocalPopulationAllocatorOffset);
    }

    bool succeeded = true;
    for (std::size_t reverse = constructed_count_; reverse > 0; --reverse) {
      const auto index = reverse - 1;
      if (destroy_ != nullptr) {
        destroy_(side(index));
      } else {
        succeeded = false;
      }
    }
    for (std::size_t reverse = constructed_count_; reverse > 0; --reverse) {
      const auto index = reverse - 1;
      void *const local = local_context(index);
      if (!NativeFreeBufferV3(population_allocators[index],
                              population_buffers[index])) {
        succeeded = false;
      }
      StoreAt<void *>(local, kLocalPopulationEntriesOffset, nullptr);
      StoreAt<std::int32_t>(local, kLocalPopulationEntriesOffset + 0x08, 0);
      StoreAt<std::int32_t>(local, kLocalPopulationEntriesOffset + 0x0C, 0);
    }
    constructed_count_ = 0;
    cleanup_succeeded_ = succeeded;
    return cleanup_succeeded_;
  }

private:
  // The native shell is exactly 0x718 bytes. Eight trailing caller-owned
  // padding bytes keep the following 16-byte-aligned auxiliary objects from
  // introducing implicit compiler padding; no native helper can see them.
  alignas(16) std::array<std::byte, kCombatShellSize + 0x08> shell_{};
  alignas(16)
      std::array<std::array<std::byte, kLocalPopulationContextSize>, 2>
          local_contexts_{};
  DestroyCombatSideV3 destroy_ = nullptr;
  std::size_t constructed_count_ = 0;
  bool cleaned_ = false;
  bool cleanup_succeeded_ = false;
  std::array<std::byte, 14> alignment_padding_{};
};

bool AllocateEffectLedgerV3(
    void *side,
    const std::vector<NativeAdvantageLedgerEntryV3> &entries) noexcept {
  if (side == nullptr ||
      LoadAt<void *>(side, kCombatSideEffectLedgerOffset) != nullptr ||
      LoadAt<std::int32_t>(side,
                           kCombatSideEffectLedgerOffset + 0x08) != 0 ||
      LoadAt<std::int32_t>(side,
                           kCombatSideEffectLedgerOffset + 0x0C) != 0) {
    return false;
  }
  if (entries.empty()) {
    return true;
  }
  if (entries.size() >
      static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  void *const allocator =
      LoadAt<void *>(side, kCombatSideEffectLedgerAllocatorOffset);
  void *const vtable =
      allocator == nullptr ? nullptr : LoadAt<void *>(allocator, 0);
  const auto address =
      vtable == nullptr ? 0 : LoadAt<std::uintptr_t>(vtable, 0x08);
  if (address == 0 ||
      entries.size() > std::numeric_limits<std::size_t>::max() /
                           sizeof(NativeAdvantageLedgerEntryV3)) {
    return false;
  }
  const auto byte_size =
      entries.size() * sizeof(NativeAdvantageLedgerEntryV3);
  void *const buffer = reinterpret_cast<NativeAllocateV3>(address)(
      allocator, byte_size, 8);
  if (buffer == nullptr) {
    return false;
  }
  std::memcpy(buffer, entries.data(), byte_size);
  StoreAt<void *>(side, kCombatSideEffectLedgerOffset, buffer);
  StoreAt<std::int32_t>(side, kCombatSideEffectLedgerOffset + 0x08,
                        static_cast<std::int32_t>(entries.size()));
  StoreAt<std::int32_t>(side, kCombatSideEffectLedgerOffset + 0x0C,
                        static_cast<std::int32_t>(entries.size()));
  return true;
}

bool ValidateEffectLedgerV3(
    void *side,
    const std::vector<NativeAdvantageLedgerEntryV3> &entries) noexcept {
  if (side == nullptr ||
      entries.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  void *const data = LoadAt<void *>(side, kCombatSideEffectLedgerOffset);
  const auto capacity = LoadAt<std::int32_t>(
      side, kCombatSideEffectLedgerOffset + 0x08);
  const auto count = LoadAt<std::int32_t>(
      side, kCombatSideEffectLedgerOffset + 0x0C);
  if (capacity != static_cast<std::int32_t>(entries.size()) ||
      count != static_cast<std::int32_t>(entries.size()) ||
      (entries.empty() ? data != nullptr : data == nullptr)) {
    return false;
  }
  for (std::size_t index = 0; index < entries.size(); ++index) {
    const auto *const row = static_cast<const std::byte *>(data) +
                            index * sizeof(NativeAdvantageLedgerEntryV3);
    if (LoadAt<void *>(row, 0) != entries[index].effect ||
        LoadAt<std::int64_t>(row, sizeof(void *)) !=
            entries[index].scale_raw) {
      return false;
    }
  }
  return true;
}

bool AppendAdvantageSourceV3(
    game::CombatAdvantageModelV3TestOnly &model,
    std::array<std::vector<NativeAdvantageLedgerEntryV3>, 2> &ledgers,
    std::string_view stage, std::size_t side_index, void *effect,
    bool selected, bool applied, std::int64_t scale_raw,
    std::string source_key, std::string skip_reason,
    std::int32_t &next_append_order,
    std::int64_t &accumulator) noexcept {
  if (side_index > 1 ||
      (applied && (!selected || scale_raw == 0)) ||
      (selected && (effect == nullptr || source_key.empty())) ||
      (!selected && effect != nullptr)) {
    return false;
  }
  game::CombatAdvantageConstructorSourceV3TestOnly row{};
  row.stage_order = static_cast<std::int32_t>(model.constructor_sources.size());
  row.stage = std::string(stage);
  row.side = side_index == 0 ? "attacker" : "defender";
  row.selected = selected;
  row.applied = applied;
  row.scale_raw = scale_raw;
  row.accumulator_before_raw = accumulator;
  if (selected) {
    row.source_key = std::move(source_key);
    row.effect_advantage_points =
        LoadAt<std::int32_t>(effect, kEffectAdvantagePointsOffset);
  }
  if (applied) {
    std::int64_t contribution = 0;
    if (!CheckedPointsScaleV3(row.effect_advantage_points, scale_raw,
                              contribution) ||
        (side_index == 1 &&
         !CheckedNegateV3(contribution, contribution))) {
      return false;
    }
    std::int64_t next = 0;
    if (!CheckedAddV3(accumulator, contribution, next)) {
      return false;
    }
    accumulator = std::clamp<std::int64_t>(next, -10'000'000, 10'000'000);
    row.append_order = next_append_order++;
    row.signed_contribution_raw = contribution;
    ledgers[side_index].push_back({effect, scale_raw});
  } else {
    row.append_order = -1;
    row.signed_contribution_raw = 0;
    row.skip_reason = std::move(skip_reason);
    if (row.skip_reason.empty()) {
      return false;
    }
  }
  row.accumulator_after_raw = accumulator;
  model.constructor_sources.push_back(std::move(row));
  return true;
}

bool ReadAdvantageModel(
    const Bindings &bindings,
    const game::CombatSimulationInputsSnapshot &base,
    std::vector<CombatPhaseSideV3> &sides,
    game::CombatAdvantageModelV3TestOnly &output) noexcept {
  output = {};
  output.observation_origin = "native_exact_build_production";
  output.unavailable_reason = "native_advantage_model_preconditions_unavailable";
  try {
    const auto module = ModuleBase();
    const auto fail_precondition = [&](const char *reason) noexcept {
      output.unavailable_reason = reason;
      return false;
    };
    if (module == 0) {
      return fail_precondition("native_advantage_model_precondition_module");
    }
    if (!bindings.enabled) {
      return fail_precondition("native_advantage_model_precondition_bindings");
    }
    if (bindings.get_province_terrain == nullptr) {
      return fail_precondition(
          "native_advantage_model_precondition_terrain_binding");
    }
    if (bindings.get_character_modifier_aggregator == nullptr) {
      return fail_precondition(
          "native_advantage_model_precondition_modifier_binding");
    }
    if (bindings.is_holding_defender == nullptr) {
      return fail_precondition(
          "native_advantage_model_precondition_holding_binding");
    }
    if (sides.size() != 2) {
      return fail_precondition(
          "native_advantage_model_precondition_side_count");
    }
    if (base.scenario.attacker_army_ids.empty()) {
      return fail_precondition(
          "native_advantage_model_precondition_attackers");
    }
    if (base.scenario.defender_army_ids.empty()) {
      return fail_precondition(
          "native_advantage_model_precondition_defenders");
    }
    if (!base.target_province.available) {
      return fail_precondition("native_advantage_model_precondition_target");
    }
    if (!base.target_province.terrain.available) {
      return fail_precondition("native_advantage_model_precondition_terrain");
    }
    if (!base.target_province.crossing.available) {
      return fail_precondition("native_advantage_model_precondition_crossing");
    }
    if (!base.target_province.defender_context.available) {
      return fail_precondition(
          "native_advantage_model_precondition_defender_context");
    }
    if (base.target_province.defender_context.holding_defender_status !=
        game::CombatObservationStatus::available) {
      return fail_precondition(
          "native_advantage_model_precondition_holding_status");
    }
    const bool saved_variables_enabled =
        *reinterpret_cast<const std::uint8_t *>(
            module + kCombatSideSavedVariablesEnabledRva) != 0;
    void *const game_state = bindings.game_state_slot == nullptr
                                 ? nullptr
                                 : *bindings.game_state_slot;
    if (saved_variables_enabled &&
        (game_state == nullptr ||
         LoadAt<void *>(game_state, kGameStateGameDataOffset) == nullptr)) {
      return fail_precondition(
          "native_advantage_model_precondition_saved_variables_manager");
    }

    output.unavailable_reason = "native_advantage_model_target_unavailable";
    void *const target = ResolveProvinceV3(bindings, base.target_province_id);
    if (target == nullptr) {
      return false;
    }
    void *const terrain = bindings.get_province_terrain(target);
    if (terrain == nullptr ||
        !StableKeyEquals(terrain, 0x18, base.target_province.terrain.key)) {
      return false;
    }
    output.unavailable_reason = "native_advantage_model_rules_unavailable";
    const auto get_rules = reinterpret_cast<GetCombatRuleDatabaseV3>(
        module + kCombatRuleDatabaseRva);
    void *const combat_rules = get_rules();
    if (combat_rules == nullptr) {
      return false;
    }

    output.unavailable_reason =
        "native_advantage_model_army_contexts_unavailable";
    std::array<std::vector<AdvantageArmyContextV3>, 2> army_contexts;
    if (!BuildAdvantageArmyContextsV3(module, base, army_contexts)) {
      return false;
    }

    output.unavailable_reason =
        "native_advantage_model_side_construction_unavailable";
    const auto construct_side = reinterpret_cast<ConstructCombatSideV3>(
        module + kConstructCombatSideRva);
    const auto populate_side = reinterpret_cast<PopulateCombatSideV3>(
        module + kPopulateCombatSideRva);
    const auto select_commander = reinterpret_cast<SelectBattleCommanderV3>(
        module + kSelectBattleCommanderRva);
    const auto refresh_strength =
        reinterpret_cast<RefreshCombatSideStrengthV3>(
            module + kRefreshCombatSideStrengthRva);
    const auto read_side_strength =
        reinterpret_cast<ReadCombatSideStrengthV3>(
            module + kReadCombatSideStrengthRva);
    const auto destroy_side = reinterpret_cast<DestroyCombatSideV3>(
        module + kDestroyCombatSideRva);
    LocalCombatContextV3 local(destroy_side);
    StoreAt<std::int32_t>(local.shell(), 0x08, -1);
    StoreAt<void *>(local.shell(), kCombatTargetProvinceOffset, target);
    StoreAt<std::uint8_t>(local.shell(), 0x6FC, 1);
    const auto province_has_holding = reinterpret_cast<ProvincePredicateV3>(
        module + kProvinceHasHoldingRva);
    StoreAt<std::uint8_t>(local.shell(), 0x6FD,
                          province_has_holding(target) ? 1 : 0);
    StoreAt<std::int32_t>(local.shell(), kCombatSide0RollOffset, 0);
    StoreAt<std::int32_t>(local.shell(), kCombatSide1RollOffset, 0);

    std::array<std::vector<CombatPhaseCandidateSourceRowV3>, 2>
        native_candidate_sources;
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      void *const side = local.side(side_index);
      if (construct_side(side, local.shell()) != side) {
        return false;
      }
      local.MarkConstructed();
      const auto saved_variables_slot = LoadAt<std::int32_t>(side, 0x08);
      if ((saved_variables_enabled && saved_variables_slot < 0) ||
          (!saved_variables_enabled && saved_variables_slot != -1)) {
        output.unavailable_reason =
            "native_advantage_model_side_saved_variables_slot_unavailable:" +
            std::to_string(side_index);
        return false;
      }
      void *const local_context = local.local_context(side_index);
      void *const population_allocator = LoadAt<void *>(side, 0x50);
      if (population_allocator == nullptr) {
        return false;
      }
      StoreAt<void *>(local_context, kLocalPopulationAllocatorOffset,
                      population_allocator);
      StoreAt<void *>(side, kCombatSideLocalContextOffset, local_context);
      for (const auto &army : army_contexts[side_index]) {
        populate_side(side, army.army);
      }
      if (!ValidatePopulatedCombatSideV3(
              side, local_context, army_contexts[side_index]) ||
          LoadAt<std::int32_t>(side, 0x70) !=
              sides[side_index].primary_participant_character_id ||
          sides[side_index].primary_source_army_id !=
              army_contexts[side_index].front().snapshot->army_id ||
          !ReadNativeCandidateSourceRowsV3(
              module, side, army_contexts[side_index],
              native_candidate_sources[side_index]) ||
          !SealCandidateSourceProofV3(
              sides[side_index],
              std::move(native_candidate_sources[side_index]))) {
        return false;
      }
      const auto gathering_raw =
          LoadAt<std::int32_t>(army_contexts[side_index].front().army, 0x1D0);
      StoreAt<std::uint8_t>(side, kCombatSideGatheringOffset,
                            gathering_raw > 0 ? 1 : 0);
    }

    output.unavailable_reason =
        "native_advantage_model_commander_selection_unavailable";
    std::array<void *, 2> selected_commanders{};
    std::array<std::int32_t, 2> selected_commander_ids{-1, -1};
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      void *const side = local.side(side_index);
      output.unavailable_reason =
          "native_advantage_model_commander_selection_null:" +
          std::to_string(side_index);
      void *const commander = select_commander(side);
      if (commander == nullptr) {
        return false;
      }
      const auto commander_id = LoadAt<std::int32_t>(commander, 0x18);
      output.unavailable_reason =
          "native_advantage_model_commander_selection_identity:" +
          std::to_string(side_index) + ":" + std::to_string(commander_id);
      if ((commander_id == -1 &&
           !IsFallback(module, kCharacterFallbackSlot, commander)) ||
          (commander_id != -1 &&
           (commander_id <= 0 ||
            ResolveComponent(module, kCharacterStoreSlot, commander_id,
                             0x18) != commander ||
            IsFallback(module, kCharacterFallbackSlot, commander)))) {
        return false;
      }
      StoreAt<std::int32_t>(side, 0x74, commander_id);
      StoreAt<std::int32_t>(local.local_context(side_index), 0x08,
                            commander_id);
      selected_commanders[side_index] = commander;
      selected_commander_ids[side_index] = commander_id;
      sides[side_index].commander_character_id = commander_id;
    }
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      void *const side = local.side(side_index);
      output.unavailable_reason =
          "native_advantage_model_strength_refresh_unavailable:" +
          std::to_string(side_index);
      refresh_strength(side);
      // 0x23CB840 only refreshes intermediate entry totals.  The final
      // 0x23CC340 side_strength equality becomes valid after 0x2308D50 has
      // completed dynamic entry materialization and is checked below.
    }

    output.unavailable_reason = "native_advantage_model_side_inputs_unavailable";
    output.side_inputs.resize(2);
    std::array<void *, 2> supply_effects{};
    const auto debt_selector = reinterpret_cast<SelectDebtAdvantageV3>(
        module + kDebtAdvantageSelectorRva);
    std::array<void *, 2> owner_debt_effects{};
    std::array<std::string, 2> owner_debt_keys{};
    std::array<bool, 2> owner_debt_effect_valid{};
    std::array<void *, 2> treasury_debt_effects{};
    std::array<std::string, 2> treasury_debt_keys{};
    std::array<bool, 2> treasury_debt_effect_valid{};
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      auto &side_input = output.side_inputs[side_index];
      side_input.side = side_index == 0 ? "attacker" : "defender";
      side_input.primary_army_id =
          army_contexts[side_index].front().snapshot->army_id;
      for (const auto &army : army_contexts[side_index]) {
        side_input.ordered_army_ids.push_back(army.snapshot->army_id);
      }
      if (!ReadSupplySideInputV3(module, combat_rules,
                                 army_contexts[side_index],
                                 side_input.supply,
                                 supply_effects[side_index])) {
        return false;
      }
      side_input.primary_army_gathering_raw =
          LoadAt<std::int32_t>(army_contexts[side_index].front().army,
                               0x5C);
      side_input.owner_character_id =
          army_contexts[side_index].front().owner_character_id;
      side_input.owner_debt_selector_raw = debt_selector(
          army_contexts[side_index].front().owner, 0);
      if (side_input.owner_debt_selector_raw < -1 ||
          (side_input.owner_debt_selector_raw != -1 &&
           (!ResolveDebtEffectV3(combat_rules,
                                side_input.owner_debt_selector_raw, false,
                                owner_debt_effects[side_index],
                                owner_debt_keys[side_index]) ||
            !ReadEffectValidityV3(owner_debt_effects[side_index],
                                  owner_debt_effect_valid[side_index])))) {
        return false;
      }
      if (!ReadTreasuryDebtSelectorV3(
              module, army_contexts[side_index].front().owner,
              side_input.treasury_debt_selector_raw,
              side_input.treasury_debt_selector_observable)) {
        return false;
      }
      if (side_input.treasury_debt_selector_observable &&
          (side_input.treasury_debt_selector_raw < -1 ||
           (side_input.treasury_debt_selector_raw != -1 &&
            (!ResolveDebtEffectV3(
                 combat_rules, side_input.treasury_debt_selector_raw, true,
                 treasury_debt_effects[side_index],
                 treasury_debt_keys[side_index]) ||
             !ReadEffectValidityV3(treasury_debt_effects[side_index],
                                   treasury_debt_effect_valid[side_index]))))) {
        return false;
      }
    }

    std::array<std::vector<NativeAdvantageLedgerEntryV3>, 2> ledgers;
    std::int64_t accumulator = 0;
    std::int32_t append_order = 0;
    const auto crossing_kind = [&base]() -> std::int32_t {
      if (base.target_province.crossing.kind == "none") {
        return 0;
      }
      if (base.target_province.crossing.kind == "strait") {
        return 1;
      }
      if (base.target_province.crossing.kind == "river") {
        return 2;
      }
      if (base.target_province.crossing.kind == "large_river") {
        return 3;
      }
      return -1;
    }();
    if (crossing_kind < 0) {
      return false;
    }

    void *const attacker_adjacency = LoadAt<void *>(
        combat_rules, kCombatRuleAdjacencyAttackerOffset +
                          static_cast<std::size_t>(crossing_kind) * 8);
    bool attacker_adjacency_valid = false;
    if (!ReadEffectValidityV3(attacker_adjacency,
                              attacker_adjacency_valid)) {
      return false;
    }
    std::string attacker_adjacency_key;
    if (attacker_adjacency_valid &&
        !ReadEffectKeyV3(attacker_adjacency, attacker_adjacency_key)) {
      return false;
    }
    if (!AppendAdvantageSourceV3(
            output, ledgers, "attacker_adjacency", 0,
            attacker_adjacency_valid ? attacker_adjacency : nullptr,
            attacker_adjacency_valid, attacker_adjacency_valid, kFixedScale,
            std::move(attacker_adjacency_key),
            "loaded_adjacency_effect_not_selected", append_order,
            accumulator)) {
      return false;
    }

    void *const defender_adjacency = LoadAt<void *>(
        combat_rules, kCombatRuleAdjacencyDefenderOffset +
                          static_cast<std::size_t>(crossing_kind) * 8);
    bool defender_adjacency_valid = false;
    if (!ReadEffectValidityV3(defender_adjacency,
                              defender_adjacency_valid)) {
      return false;
    }
    bool ignores_water_crossing = false;
    if (defender_adjacency_valid) {
      void *const aggregator = bindings.get_character_modifier_aggregator(
          selected_commanders[0]);
      if (aggregator == nullptr) {
        return false;
      }
      const auto has_modifier_flag =
          reinterpret_cast<ModifierFlagPredicateV3>(
              module + kModifierSetHasFlagRva);
      ignores_water_crossing = has_modifier_flag(
          static_cast<std::byte *>(aggregator) + 0x68, 0x197);
    }
    std::string defender_adjacency_key;
    if (defender_adjacency_valid &&
        !ReadEffectKeyV3(defender_adjacency, defender_adjacency_key)) {
      return false;
    }
    if (!AppendAdvantageSourceV3(
            output, ledgers, "defender_adjacency", 1,
            defender_adjacency_valid ? defender_adjacency : nullptr,
            defender_adjacency_valid,
            defender_adjacency_valid && !ignores_water_crossing, kFixedScale,
            std::move(defender_adjacency_key),
            defender_adjacency_valid
                ? "attacker_no_water_crossing_penalty"
                : "loaded_adjacency_effect_not_selected",
            append_order, accumulator)) {
      return false;
    }

    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      void *const terrain_effect = LoadAt<void *>(
          terrain, side_index == 0 ? kTerrainAttackerEffectOffset
                                   : kTerrainDefenderEffectOffset);
      bool valid = false;
      if (!ReadEffectValidityV3(terrain_effect, valid)) {
        return false;
      }
      const auto stage = side_index == 0 ? "attacker_terrain"
                                         : "defender_terrain";
      std::string source_key;
      if (valid) {
        source_key = "terrain:";
        source_key += base.target_province.terrain.key;
        source_key += side_index == 0 ? ":attacker" : ":defender";
      }
      if (!AppendAdvantageSourceV3(
              output, ledgers, stage, side_index,
              valid ? terrain_effect : nullptr, valid, valid, kFixedScale,
              std::move(source_key), "terrain_effect_not_selected",
              append_order, accumulator)) {
        return false;
      }
    }

    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      const auto &supply = output.side_inputs[side_index].supply;
      const bool applied = supply.selected_effect_points != 0;
      if (!AppendAdvantageSourceV3(
              output, ledgers, side_index == 0 ? "supply_0" : "supply_1",
              side_index, supply_effects[side_index], true, applied,
              kFixedScale, supply.selected_key,
              "zero_effect_not_appended", append_order, accumulator)) {
        return false;
      }
    }

    const bool holding = bindings.is_holding_defender(
        army_contexts[1].front().owner, target);
    if (holding !=
        base.target_province.defender_context.holding_defender) {
      return false;
    }
    StoreAt<std::uint8_t>(local.shell(), kCombatHoldingDefenderOffset,
                          holding ? 1 : 0);
    void *const holding_effect = LoadAt<void *>(
        combat_rules, kCombatRuleHoldingDefenderOffset);
    if (!RequireEffectKeyV3(holding_effect,
                            "holding_defender_advantage")) {
      return false;
    }
    std::int64_t holding_scale = kFixedScale;
    if (holding && !ReadHoldingScaleV3(module, target, holding_scale)) {
      return false;
    }
    if (!AppendAdvantageSourceV3(
            output, ledgers, "holding_defender_1", 1,
            holding ? holding_effect : nullptr, holding,
            holding && holding_scale > 0,
            holding ? holding_scale : kFixedScale,
            holding ? "holding_defender_advantage" : std::string{},
            holding ? "holding_scale_not_positive"
                    : "holding_defender_predicate_false",
            append_order, accumulator)) {
      return false;
    }

    void *const gathering_effect =
        LoadAt<void *>(combat_rules, kCombatRuleGatheringArmyOffset);
    if (!RequireEffectKeyV3(gathering_effect, "gathering_army_advantage")) {
      return false;
    }
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      const bool selected =
          output.side_inputs[side_index].primary_army_gathering_raw != 0;
      if (!AppendAdvantageSourceV3(
              output, ledgers,
              side_index == 0 ? "gathering_army_0" : "gathering_army_1",
              side_index, selected ? gathering_effect : nullptr, selected,
              selected, kFixedScale,
              selected ? "gathering_army_advantage" : std::string{},
              "primary_army_not_gathering", append_order, accumulator)) {
        return false;
      }
    }

    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      if (!AppendAdvantageSourceV3(
              output, ledgers,
              side_index == 0 ? "debt_0_owner" : "debt_1_owner",
              side_index,
              owner_debt_effect_valid[side_index]
                  ? owner_debt_effects[side_index]
                  : nullptr,
              owner_debt_effect_valid[side_index],
              owner_debt_effect_valid[side_index], kFixedScale,
              owner_debt_effect_valid[side_index]
                  ? owner_debt_keys[side_index]
                  : std::string{},
              "owner_debt_effect_not_selected", append_order,
              accumulator)) {
        return false;
      }
      const bool treasury_selected =
          output.side_inputs[side_index].treasury_debt_selector_observable &&
          treasury_debt_effect_valid[side_index];
      if (!AppendAdvantageSourceV3(
              output, ledgers,
              side_index == 0 ? "debt_0_treasury" : "debt_1_treasury",
              side_index,
              treasury_selected ? treasury_debt_effects[side_index]
                                : nullptr,
              treasury_selected, treasury_selected, kFixedScale,
              treasury_selected ? treasury_debt_keys[side_index]
                                : std::string{},
              output.side_inputs[side_index]
                      .treasury_debt_selector_observable
                  ? "treasury_debt_effect_not_selected"
                  : "treasury_debt_gate_false",
              append_order, accumulator)) {
        return false;
      }
    }

    void *target_faith = nullptr;
    std::int32_t target_faith_id = -1;
    bool target_unreformed = false;
    if (!ReadUnreformedTargetFaithV3(module, target, target_faith,
                                     target_faith_id,
                                     target_unreformed)) {
      return false;
    }
    void *const faith_effect = LoadAt<void *>(
        combat_rules, kCombatRuleUnreformedFaithOffset);
    if (!RequireEffectKeyV3(faith_effect,
                            "unreformed_faith_province")) {
      return false;
    }
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      const bool selected =
          target_unreformed &&
          LoadAt<std::int32_t>(army_contexts[side_index].front().owner,
                               0xB4) == target_faith_id;
      if (!AppendAdvantageSourceV3(
              output, ledgers,
              side_index == 0 ? "unreformed_faith_0"
                              : "unreformed_faith_1",
              side_index, selected ? faith_effect : nullptr, selected,
              selected, kFixedScale,
              selected ? "unreformed_faith_province" : std::string{},
              target_unreformed ? "side_owner_faith_mismatch"
                                : "target_faith_not_unreformed",
              append_order, accumulator)) {
        return false;
      }
    }

    if (output.constructor_sources.size() != 15 ||
        !AllocateEffectLedgerV3(local.side(0), ledgers[0]) ||
        !AllocateEffectLedgerV3(local.side(1), ledgers[1]) ||
        !ValidateEffectLedgerV3(local.side(0), ledgers[0]) ||
        !ValidateEffectLedgerV3(local.side(1), ledgers[1])) {
      return false;
    }
    StoreAt<std::int64_t>(local.shell(), kCombatBaseAdvantageOffset,
                          accumulator);
    output.base_static_accumulator_raw = accumulator;

    const auto resolve_advantage =
        reinterpret_cast<ResolveCombatAdvantageV3>(
            module + kResolveCombatAdvantageRva);
    resolve_advantage(local.shell());
    const auto original_total = LoadAt<std::int64_t>(
        local.shell(), kCombatResolvedAdvantageOffset);

    const auto read_relation = reinterpret_cast<ReadCombatRelationKindV3>(
        module + kReadCombatRelationKindRva);
    const auto read_side_total =
        reinterpret_cast<ReadSideDynamicAdvantageV3>(
            module + kReadSideDynamicAdvantageRva);
    const auto read_commander =
        reinterpret_cast<ReadCommanderDynamicAdvantageV3>(
            module + kReadCommanderDynamicAdvantageRva);
    const auto read_side_modifier =
        reinterpret_cast<ReadSideModifierAdvantageV3>(
            module + kReadSideModifierAdvantageRva);
    output.resolved_dynamic.sides.resize(2);
    std::array<std::int64_t, 2> side_totals{};
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      auto &dynamic = output.resolved_dynamic.sides[side_index];
      dynamic.side = side_index == 0 ? "attacker" : "defender";
      dynamic.battle_commander_character_id =
          selected_commander_ids[side_index];
      dynamic.battle_commander_selected =
          selected_commander_ids[side_index] != -1;
      dynamic.primary_army_gathering_raw = LoadAt<std::int32_t>(
          army_contexts[side_index].front().army, 0x1D0);
      dynamic.relation_kind_raw =
          read_relation(local.shell(), static_cast<std::int32_t>(side_index));
      if (dynamic.relation_kind_raw < 0 ||
          dynamic.relation_kind_raw > 2) {
        return false;
      }
      dynamic.roll_points = 0;
      dynamic.roll_raw = 0;
      std::int64_t side_total = 0;
      std::int64_t commander_total = 0;
      std::int64_t side_modifier_total = 0;
      if (read_side_total(local.shell(), &side_total,
                          static_cast<std::int32_t>(side_index), nullptr) !=
              &side_total ||
          read_commander(local.shell(), &commander_total,
                         selected_commanders[side_index],
                         static_cast<std::int32_t>(side_index),
                         dynamic.relation_kind_raw, nullptr) !=
              &commander_total ||
          read_side_modifier(
              local.shell(), &side_modifier_total,
              static_cast<std::byte *>(local.side(side_index)) +
                  kCombatSideModifierAggregatorOffset,
              static_cast<std::int32_t>(side_index),
              dynamic.relation_kind_raw, nullptr) != &side_modifier_total) {
        return false;
      }
      std::int64_t residual = 0;
      if (!CheckedSubtractV3(side_total, dynamic.roll_raw, residual) ||
          !CheckedSubtractV3(residual, commander_total, residual) ||
          !CheckedSubtractV3(residual, side_modifier_total, residual)) {
        return false;
      }
      dynamic.target_conditionals_residual_raw = residual;
      dynamic.commander_dynamic_raw = commander_total;
      dynamic.side_dynamic_raw = side_modifier_total;
      dynamic.side_total_raw = side_total;
      if (side_index == 0) {
        dynamic.contribution_to_resolved_raw = side_total;
      } else if (!CheckedNegateV3(
                     side_total, dynamic.contribution_to_resolved_raw)) {
        return false;
      }
      side_totals[side_index] = side_total;
    }
    output.resolved_dynamic.side_0_dynamic_raw = side_totals[0];
    output.resolved_dynamic.side_1_dynamic_raw = side_totals[1];
    std::int64_t resolved = 0;
    if (!CheckedAddV3(accumulator, side_totals[0], resolved) ||
        !CheckedSubtractV3(resolved, side_totals[1], resolved) ||
        resolved != original_total ||
        LoadAt<std::int64_t>(local.shell(),
                             kCombatBaseAdvantageOffset) != accumulator ||
        LoadAt<std::int32_t>(local.shell(), kCombatSide0RollOffset) != 0 ||
        LoadAt<std::int32_t>(local.shell(), kCombatSide1RollOffset) != 0 ||
        ResolveProvinceV3(bindings, base.target_province_id) != target ||
        bindings.get_province_terrain(target) != terrain ||
        get_rules() != combat_rules ||
        !RevalidateAdvantageArmyContextsV3(module, army_contexts)) {
      return false;
    }
    void *revalidated_faith = nullptr;
    std::int32_t revalidated_faith_id = -1;
    bool revalidated_unreformed = false;
    if (!ReadUnreformedTargetFaithV3(
            module, target, revalidated_faith, revalidated_faith_id,
            revalidated_unreformed) ||
        revalidated_faith != target_faith ||
        revalidated_faith_id != target_faith_id ||
        revalidated_unreformed != target_unreformed) {
      return false;
    }
    if (LoadAt<std::uint8_t>(local.shell(), 0x6FC) != 1 ||
        LoadAt<std::uint8_t>(local.shell(), 0x6FD) !=
            (province_has_holding(target) ? 1 : 0) ||
        LoadAt<std::uint8_t>(local.shell(),
                             kCombatHoldingDefenderOffset) !=
            (holding ? 1 : 0)) {
      return false;
    }
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      std::vector<CombatPhaseCandidateSourceRowV3> revalidated_sources;
      if (!ValidatePopulatedCombatSideV3(
              local.side(side_index), local.local_context(side_index),
              army_contexts[side_index]) ||
          !ReadNativeCandidateSourceRowsV3(
              module, local.side(side_index), army_contexts[side_index],
              revalidated_sources) ||
          revalidated_sources !=
              sides[side_index].candidate_source_proof.ordered_sources ||
          !ValidateEffectLedgerV3(local.side(side_index),
                                  ledgers[side_index]) ||
          LoadAt<std::int32_t>(local.side(side_index), 0x74) !=
              selected_commander_ids[side_index] ||
          LoadAt<std::int32_t>(local.local_context(side_index), 0x08) !=
              selected_commander_ids[side_index] ||
          read_side_strength(local.side(side_index)) !=
              sides[side_index].side_strength_raw) {
        return false;
      }
      if ((selected_commander_ids[side_index] == -1 &&
           !IsFallback(module, kCharacterFallbackSlot,
                       selected_commanders[side_index])) ||
          (selected_commander_ids[side_index] != -1 &&
           ResolveComponent(module, kCharacterStoreSlot,
                            selected_commander_ids[side_index], 0x18) !=
               selected_commanders[side_index])) {
        return false;
      }
    }
    if (!local.CleanupChecked()) {
      return false;
    }
    output.resolved_dynamic.resolved_advantage_at_zero_roll_raw = resolved;
    output.resolved_dynamic.original_total_helper_raw = original_total;
    output.resolved_dynamic.original_total_helper_match = true;
    output.available = true;
    output.unavailable_reason.clear();
    return true;
  } catch (const std::exception &) {
    output = {};
    output.observation_origin = "native_exact_build_production";
    output.unavailable_reason = "native_advantage_model_exception";
    return false;
  } catch (...) {
    output = {};
    output.observation_origin = "native_exact_build_production";
    output.unavailable_reason = "native_advantage_model_exception";
    return false;
  }
}

} // namespace

ReadCombatSimulationInputsV3Result ReadCombatSimulationInputsV3(
    const Bindings &bindings,
    const game::CombatSimulationInputsRequest &request,
    CombatSimulationInputsV3Snapshot &output) noexcept {
  output = {};
  try {
    if (!bindings.enabled) {
      return ReadCombatSimulationInputsV3Result::unavailable;
    }
    game::Snapshot before{};
    if (!ReadSnapshot(bindings, before)) {
      return ReadCombatSimulationInputsV3Result::unavailable;
    }
    if (!before.paused) {
      return ReadCombatSimulationInputsV3Result::requires_paused;
    }
    if (!before.has_played_character || !before.played_character_alive) {
      return ReadCombatSimulationInputsV3Result::no_played_character;
    }

    game::CombatSimulationInputsSnapshot base{};
    const auto base_result = ReadCombatSimulationInputs(bindings, request,
                                                        base);
    switch (base_result) {
    case game::ReadCombatSimulationInputsResult::requires_paused:
      return ReadCombatSimulationInputsV3Result::requires_paused;
    case game::ReadCombatSimulationInputsResult::no_played_character:
      return ReadCombatSimulationInputsV3Result::no_played_character;
    case game::ReadCombatSimulationInputsResult::invalid_arguments:
      return ReadCombatSimulationInputsV3Result::invalid_arguments;
    case game::ReadCombatSimulationInputsResult::target_province_not_found:
      return ReadCombatSimulationInputsV3Result::target_province_not_found;
    case game::ReadCombatSimulationInputsResult::army_not_in_scope:
      return ReadCombatSimulationInputsV3Result::army_not_in_scope;
    case game::ReadCombatSimulationInputsResult::invalid_encounter:
      return ReadCombatSimulationInputsV3Result::invalid_encounter;
    case game::ReadCombatSimulationInputsResult::partial:
      return ReadCombatSimulationInputsV3Result::base_inputs_unavailable;
    case game::ReadCombatSimulationInputsResult::unavailable:
      return ReadCombatSimulationInputsV3Result::unavailable;
    case game::ReadCombatSimulationInputsResult::available:
      break;
    }
    if (!base.input_observation_ready || base.armies.empty()) {
      return ReadCombatSimulationInputsV3Result::base_inputs_unavailable;
    }

    const auto module = ModuleBase();
    if (module == 0) {
      return ReadCombatSimulationInputsV3Result::unavailable;
    }
    TraitReadContext traits{};
    QueryDefinitionContext definitions{};
    CombatPhaseInputsV3 phase{};
    const auto phase_unavailable =
        [&output, &base, &phase](std::string reason) {
          phase = {};
          phase.unavailable_reason = std::move(reason);
          output.base_inputs = std::move(base);
          output.phase_event_inputs = std::move(phase);
          return ReadCombatSimulationInputsV3Result::phase_inputs_unavailable;
        };
    std::string trait_context_failure;
    if (!BuildTraitReadContext(module, traits, trait_context_failure)) {
      return phase_unavailable(
          trait_context_failure.empty()
              ? std::string("native_phase_trait_context_unavailable")
              : std::move(trait_context_failure));
    }
    std::string definition_context_failure;
    if (!BuildQueryDefinitionContext(module, definitions,
                                     definition_context_failure)) {
      return phase_unavailable(
          definition_context_failure.empty()
              ? std::string("native_phase_definition_context_unavailable")
              : std::move(definition_context_failure));
    }
    std::string roster_failure;
    if (!BuildCharacterRoster(module, base, phase.characters, phase.sides,
                              roster_failure)) {
      return phase_unavailable(
          roster_failure.empty() ? std::string("native_phase_roster_unavailable")
                                 : std::move(roster_failure));
    }
    for (auto &character : phase.characters) {
      std::string character_failure;
      if (!ReadCharacterPhaseRow(module, traits, definitions, character,
                                 character_failure)) {
        return phase_unavailable(
            character_failure.empty()
                ? std::string("native_phase_character_reader_unavailable")
                : std::move(character_failure));
      }
    }

    std::vector<NamedSignedV3> maa_base_types;
    if (!ReadMaaBaseTypeEnums(module, maa_base_types)) {
      return phase_unavailable("native_phase_maa_database_unavailable");
    }
    phase.armies.reserve(base.armies.size());
    for (const auto &base_army : base.armies) {
      CombatPhaseArmyV3 army{};
      if (!ReadArmyMaa(module, maa_base_types, base_army, army)) {
        return phase_unavailable("native_phase_maa_reader_unavailable");
      }
      phase.armies.push_back(std::move(army));
    }

    for (std::size_t side_index = 0; side_index < phase.sides.size();
         ++side_index) {
      auto &side = phase.sides[side_index];
      std::vector<const game::CombatArmyInputsSnapshot *> side_armies;
      if (!CollectSideArmies(base, side.encounter_role, side_armies) ||
          !ReadSideStrengthMirror(side_armies, side.side_strength_raw,
                                  side.side_army_size_raw) ||
          !ReadSideParticipants(module, side_armies, side)) {
        return phase_unavailable("native_phase_side_reader_unavailable");
      }
    }
    if (!ReadFaithHostilityMatrix(module, phase.characters, phase.sides,
                                  phase.faith_hostility) ||
        !ReadGameRules(module, definitions, phase.easy_difficulty,
                       phase.very_easy_difficulty) ||
        !RevalidatePhaseObjects(module, phase.characters, phase.armies,
                                phase.sides)) {
      return phase_unavailable(
          "native_phase_relation_or_rule_reader_unavailable");
    }
    if (!ReadAdvantageModel(bindings, base, phase.sides,
                            phase.advantage_model)) {
      return phase_unavailable(
          phase.advantage_model.unavailable_reason.empty()
              ? "native_advantage_model_unavailable"
              : phase.advantage_model.unavailable_reason);
    }
    for (const auto &side : phase.sides) {
      if (!ValidateCandidateSourceProofV3(side, phase.characters)) {
        return phase_unavailable(
            "native_candidate_source_equivalence_unavailable");
      }
    }

    game::Snapshot after{};
    if (!ReadSnapshot(bindings, after) ||
        !SameSnapshotFrame(before, after) ||
        !RevalidatePhaseObjects(module, phase.characters, phase.armies,
                                phase.sides)) {
      return phase_unavailable("native_phase_identity_revalidation_failed");
    }
    for (const auto &side : phase.sides) {
      if (!ValidateCandidateSourceProofV3(side, phase.characters)) {
        return phase_unavailable(
            "native_candidate_source_identity_revalidation_failed");
      }
    }
    phase.available = true;
    phase.unavailable_reason.clear();
    output.base_inputs = std::move(base);
    output.phase_event_inputs = std::move(phase);
    return ReadCombatSimulationInputsV3Result::available;
  } catch (const std::exception &) {
    output = {};
    return ReadCombatSimulationInputsV3Result::unavailable;
  } catch (...) {
    output = {};
    return ReadCombatSimulationInputsV3Result::unavailable;
  }
}

} // namespace xar::ck3_11906
