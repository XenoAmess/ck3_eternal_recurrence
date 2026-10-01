#pragma once

#include "xar_bridge/combat_v3.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kPhaseMaaTypeRegistrySlot = 0x5C67558;
inline constexpr std::uintptr_t kPhaseGameRuleServiceSlot = 0x5CB3D78;
inline constexpr std::uintptr_t kPhaseRuleTokenRegistrySlot = 0x5D34358;
inline constexpr std::uintptr_t kPhaseRuleTokenFallbackSlot = 0x5D37A60;
inline constexpr std::uintptr_t kPhaseRuleKeyHashRva = 0x3F7E240;
inline constexpr std::uintptr_t kPhaseRuleTokenLookupRva = 0x366C2C0;
inline constexpr std::uintptr_t kPhaseVariableContextRva = 0x370EB10;
inline constexpr std::uintptr_t kPhaseVariableIdentifierTableRva = 0x3F8A800;
inline constexpr std::uintptr_t kPhaseVariableIdentifierLookupRva = 0x3F8A680;
inline constexpr std::uintptr_t kPhaseVariableIdentifierNameRva = 0x3F8A6F0;
inline constexpr std::uintptr_t kPhaseScriptIdentifierLookupRva = 0x3F4F870;
inline constexpr std::uintptr_t kPhaseScriptIdentifierNameRva = 0x3F4F900;
inline constexpr std::uintptr_t kPhaseCombatEffectDatabaseRva = 0x8FC3E0;
inline constexpr std::uintptr_t kPhaseCombatEffectDatabaseSlot = 0x5C67200;
inline constexpr std::uintptr_t kPhaseCommanderMinRollSlot = 0x5C699BC;
inline constexpr std::uintptr_t kPhaseCommanderMaxRollSlot = 0x5C699B8;
inline constexpr std::uintptr_t kPhaseKnightDamageSlot = 0x5C699A8;
inline constexpr std::uintptr_t kPhaseKnightToughnessSlot = 0x5C699B0;
inline constexpr std::uintptr_t kPhaseMinimumCombatWidthSlot = 0x5C699C8;
inline constexpr std::uintptr_t kPhaseBaseWidthRatioSlot = 0x5C69BA8;
inline constexpr std::size_t kPhaseMaaBaseTypeDataOffset = 0xEF0;
inline constexpr std::size_t kPhaseMaaBaseTypeCountOffset = 0xEFC;
inline constexpr std::size_t kPhaseMaaBaseTypeStride = 0x58;
inline constexpr std::int32_t kPhaseCounterEfficiencyModifierIndex = 0x113;
inline constexpr std::int32_t kPhaseCounterResistanceModifierIndex = 0x114;
inline constexpr std::int32_t kPhaseCommanderMinRollModifierIndex = 0x115;
inline constexpr std::int32_t kPhaseCommanderMaxRollModifierIndex = 0x116;

struct PhaseStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t pad = 0;
};
struct PhaseStringView64 {
  const char *data = nullptr;
  std::int64_t size = 0;
};
struct PhaseVariableTarget {
  std::uint16_t kind = 0;
  std::uint8_t padding[6]{};
  std::int64_t payload = 0;
};
static_assert(sizeof(PhaseStringView32) == 0x10);
static_assert(sizeof(PhaseStringView64) == 0x10);
static_assert(sizeof(PhaseVariableTarget) == 0x10);

using PhaseRuleKeyHash = std::int32_t (*)(void *, const char *, std::uint32_t);
using PhaseRuleTokenLookup = void *(*)(void *, std::int32_t);
using PhaseVariableIdentifierTable = void *(*)();
using PhaseVariableIdentifierLookup = std::int32_t *(*)(
    void *, std::int32_t *, const PhaseStringView32 *);
using PhaseVariableIdentifierName = const std::string *(*)(void *, std::int32_t);
using PhaseScriptIdentifierLookup = std::int32_t (*)(const PhaseStringView64 *);
using PhaseScriptIdentifierName = const std::string *(*)(std::int32_t);
using PhaseVariableContext = void *(*)(const PhaseVariableTarget *);
using PhaseResolveRegiment = void *(*)(void *, std::int32_t);

struct PhaseDefinitionBindings {
  bool enabled = false;
  void **maa_type_registry = nullptr;
  void **rule_service = nullptr;
  void **rule_token_registry = nullptr;
  void **rule_token_fallback = nullptr;
  PhaseRuleKeyHash hash_rule_key = nullptr;
  PhaseRuleTokenLookup lookup_rule_token = nullptr;
  PhaseVariableIdentifierTable variable_table = nullptr;
  PhaseVariableIdentifierLookup lookup_variable_identifier = nullptr;
  PhaseVariableIdentifierName variable_identifier_name = nullptr;
  PhaseScriptIdentifierLookup lookup_script_identifier = nullptr;
  PhaseScriptIdentifierName script_identifier_name = nullptr;
  PhaseVariableContext variable_context = nullptr;
  const std::int32_t *commander_min_roll = nullptr;
  const std::int32_t *commander_max_roll = nullptr;
  const std::int32_t *knight_damage_per_prowess = nullptr;
  const std::int32_t *knight_toughness_per_prowess = nullptr;
  const std::int32_t *minimum_combat_width = nullptr;
  const std::int64_t *base_combat_width_ratio = nullptr;
  void *regiment_context = nullptr;
  PhaseResolveRegiment resolve_regiment = nullptr;
};

struct PhaseMaaBaseType {
  std::string key;
  std::int32_t value = 0;
};
struct PhaseDifficulty {
  bool easy = false;
  bool very_easy = false;
};
struct PhaseCombatDefines {
  std::int32_t commander_min_roll = 0;
  std::int32_t commander_max_roll = 0;
  std::int32_t knight_damage_per_prowess = 0;
  std::int32_t knight_toughness_per_prowess = 0;
  std::int32_t minimum_combat_width = 0;
  std::int64_t base_combat_width_ratio = 0;
};

PhaseDefinitionBindings BindPhaseDefinitionsImage(
    std::uintptr_t base, std::string_view executable_sha256) noexcept;
bool ReadPhaseMaaBaseTypes(const PhaseDefinitionBindings &bindings,
                          std::vector<PhaseMaaBaseType> &output) noexcept;
bool ReadPhaseDifficulty(const PhaseDefinitionBindings &bindings,
                         PhaseDifficulty &output) noexcept;
bool ResolvePhaseScriptIdentifier(const PhaseDefinitionBindings &bindings,
                                  std::string_view key,
                                  std::int32_t &identifier) noexcept;
bool ResolvePhaseVariableIdentifier(const PhaseDefinitionBindings &bindings,
                                    std::string_view key,
                                    std::int32_t &identifier) noexcept;
bool ReadPhaseCombatDefines(const PhaseDefinitionBindings &bindings,
                           PhaseCombatDefines &output) noexcept;
bool ReadPhaseArmyMaa(const PhaseDefinitionBindings &bindings,
                      const game::CombatArmyInputsSnapshot &base,
                      game::CombatPhaseArmyV3 &output) noexcept;

} // namespace xar::ck3_12002
