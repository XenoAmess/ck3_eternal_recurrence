#pragma once

#include "xar_bridge/combat_v3.hpp"
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002::phase_culture {

inline constexpr std::uintptr_t kHouseStoreSlot = 0x5D1DAF0;
inline constexpr std::uintptr_t kHouseFallbackSlot = 0x5D1DAE8;
inline constexpr std::uintptr_t kDynastyStoreSlot = 0x5D1DE78;
inline constexpr std::uintptr_t kDynastyFallbackSlot = 0x5D1DE28;
inline constexpr std::uintptr_t kCultureStoreSlot = 0x5D1E2F0;
inline constexpr std::uintptr_t kCultureFallbackSlot = 0x5D1E2E8;
inline constexpr std::uintptr_t kInnovationDatabaseSlot = 0x5D1DEE8;
inline constexpr std::uintptr_t kInnovationFallbackSlot = 0x5D202C8;
inline constexpr std::uintptr_t kTraditionDatabaseSlot = 0x5D1DEE0;
inline constexpr std::uintptr_t kTraditionFallbackSlot = 0x5D1FB50;
inline constexpr std::uintptr_t kTraditionDatabaseRva = 0xA14910;
inline constexpr std::uintptr_t kTraditionIndexedLookupRva = 0x225D520;
inline constexpr std::uintptr_t kTraditionScopeResolverRva = 0x2B156B0;
inline constexpr std::uintptr_t kDynastyPerkDatabaseSlot = 0x5D1FC00;
inline constexpr std::uintptr_t kCharacterPerkDatabaseSlot = 0x5C67128;
inline constexpr std::uintptr_t kCharacterKnightContextRva = 0x28BFC70;
inline constexpr std::uintptr_t kCharacterPerksRva = 0x2919360;
inline constexpr std::uintptr_t kCultureHasParameterRva = 0x2549810;
inline constexpr std::uintptr_t kScriptIdentifierLookupRva = 0x3F4F870;
inline constexpr std::uintptr_t kScriptIdentifierNameRva = 0x3F4F900;

inline constexpr std::size_t kCharacterHouseIdOffset = 0x158;
inline constexpr std::size_t kCharacterCultureIdOffset = 0xB0;
inline constexpr std::size_t kCharacterRelationOffset = 0x1B8;
inline constexpr std::size_t kRelationEmployerIdOffset = 0xC8;
inline constexpr std::size_t kHouseDynastyIdOffset = 0x2C;
inline constexpr std::size_t kDynastyPerksDataOffset = 0x178;
inline constexpr std::size_t kDynastyPerksCountOffset = 0x184;
inline constexpr std::size_t kCultureTemplateOffset = 0x20;
inline constexpr std::size_t kTemplateResolvedDataOffset = 0x128;
inline constexpr std::size_t kResolvedTraditionsDataOffset = 0x58;
inline constexpr std::size_t kResolvedTraditionsCountOffset = 0x64;
inline constexpr std::size_t kResolvedPillarsDataOffset = 0x70;
inline constexpr std::size_t kCultureInnovationsDataOffset = 0x518;
inline constexpr std::size_t kCultureInnovationsCountOffset = 0x524;
inline constexpr std::size_t kDefinitionObjectsOffset = 0x50;
inline constexpr std::size_t kDefinitionCountOffset = 0x5C;

struct NativeStringView64 {
  const char *data = nullptr;
  std::int64_t size = 0;
};
using CharacterContext = void *(*)(void *);
using CharacterPerks = void *(*)(void *);
using CultureHasParameter = bool (*)(void *, std::int32_t);
using ScriptIdentifierLookup = std::int32_t (*)(const NativeStringView64 *);
using ScriptIdentifierName = const std::string *(*)(std::int32_t);

struct Bindings {
  bool enabled = false;
  void **character_store = nullptr;
  void **character_fallback = nullptr;
  void **house_store = nullptr;
  void **house_fallback = nullptr;
  void **dynasty_store = nullptr;
  void **dynasty_fallback = nullptr;
  void **culture_store = nullptr;
  void **culture_fallback = nullptr;
  void **innovation_database = nullptr;
  void **innovation_fallback = nullptr;
  void **tradition_database = nullptr;
  void **tradition_fallback = nullptr;
  void **dynasty_perk_database = nullptr;
  void **character_perk_database = nullptr;
  CharacterContext character_context = nullptr;
  CharacterPerks character_perks = nullptr;
  CultureHasParameter culture_has_parameter = nullptr;
  ScriptIdentifierLookup lookup_script_identifier = nullptr;
  ScriptIdentifierName script_identifier_name = nullptr;
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;
// Borrowed objects and native helpers must be read on the owning game thread.
// Only the non-religious fields are written; all faith fields are untouched.
bool ReadPhaseCharacterCultureRelations(
    const Bindings &bindings, void *character,
    game::CombatPhaseCharacterV3 &output,
    std::string *unavailable_reason = nullptr) noexcept;

} // namespace xar::ck3_12002::phase_culture
