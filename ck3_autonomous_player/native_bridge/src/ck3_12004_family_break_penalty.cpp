#include "xar_bridge/ck3_12004_family_break_penalty.hpp"

#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"

namespace xar::ck3_12004 {
namespace {
// Actual .4 entries and operands: actual4-break-penalty/function-map,
// settlement39 helper pins, Activity common-native and Faith doctrine roots.
constexpr std::uintptr_t kRuleServiceSlotRva = 0x5CB3D78;
constexpr std::uintptr_t kRuleRegistrySlotRva = 0x5D34358;
constexpr std::uintptr_t kRuleFallbackSlotRva = 0x5D37A60;
constexpr std::uintptr_t kRuleTokenLookupRva = 0x366C2A0;
constexpr std::uintptr_t kVariableTableRva = 0x3F8A7E0;
constexpr std::uintptr_t kVariableLookupRva = 0x3F8A660;
constexpr std::uintptr_t kVariableNameRva = 0x3F8A6D0;
constexpr std::uintptr_t kScriptLookupRva = 0x3F4F850;
constexpr std::uintptr_t kScriptNameRva = 0x3F4F8E0;
// Complete scope-context87B and Faith actor-map receipts are shared proofs.
constexpr std::uintptr_t kVariableContextRva = 0x370EAF0;
constexpr std::uintptr_t kActualCharacterRiteRva = 0x28D2F70;
} // namespace

ck3_12002::PhaseDefinitionBindings BindFamilyBreakIdentifiersImage(
    std::uintptr_t base, std::string_view sha256) noexcept {
  ck3_12002::PhaseDefinitionBindings b;
  if (!base || sha256 != kExecutableSha256) return b;
  b.enabled = true;
  b.rule_service = reinterpret_cast<void **>(base + kRuleServiceSlotRva);
  b.rule_token_registry = reinterpret_cast<void **>(base + kRuleRegistrySlotRva);
  b.rule_token_fallback = reinterpret_cast<void **>(base + kRuleFallbackSlotRva);
  b.hash_rule_key = reinterpret_cast<ck3_12002::PhaseRuleKeyHash>(
      base + kFamilyBreakStableHashRvaV1);
  b.lookup_rule_token = reinterpret_cast<ck3_12002::PhaseRuleTokenLookup>(
      base + kRuleTokenLookupRva);
  b.variable_table = reinterpret_cast<ck3_12002::PhaseVariableIdentifierTable>(
      base + kVariableTableRva);
  b.lookup_variable_identifier =
      reinterpret_cast<ck3_12002::PhaseVariableIdentifierLookup>(
          base + kVariableLookupRva);
  b.variable_identifier_name =
      reinterpret_cast<ck3_12002::PhaseVariableIdentifierName>(
          base + kVariableNameRva);
  b.lookup_script_identifier = reinterpret_cast<ck3_12002::PhaseScriptIdentifierLookup>(
      base + kScriptLookupRva);
  b.script_identifier_name = reinterpret_cast<ck3_12002::PhaseScriptIdentifierName>(
      base + kScriptNameRva);
  b.variable_context = reinterpret_cast<ck3_12002::PhaseVariableContext>(
      base + kVariableContextRva);
  return b;
}

ck3_12002::family_break_penalty::Bindings BindFamilyBreakPenaltyImage(
    std::uintptr_t base, std::string_view sha256) noexcept {
  using namespace ck3_12002::family_break_penalty;
  Bindings b;
  if (!base || sha256 != kExecutableSha256) return b;
  b.enabled = true;
  b.lineage = BindFamilyValuesImage(base, sha256);
  b.traits = ck3_12004::phase_character::BindImage(base, sha256);
  b.identifiers = BindFamilyBreakIdentifiersImage(base, sha256);
  b.highest_tier = reinterpret_cast<HighestTier>(base + kFamilyHighestTierRva);
  b.matchmaker = reinterpret_cast<Matchmaker>(base + kFamilyMatchmakerRva);
  b.close_family = reinterpret_cast<FamilyPredicate>(base + kFamilyCloseFamilyRva);
  b.close_or_extended_family = reinterpret_cast<FamilyPredicate>(
      base + kFamilyCloseOrExtendedFamilyRva);
  b.has_trait_flag = reinterpret_cast<TraitFlag>(base + kFamilyTraitFlagRva);
  b.yields_alliance = reinterpret_cast<YieldsAlliance>(base + kFamilyYieldsAllianceRva);
  b.character_rite = reinterpret_cast<CharacterRite>(base + kActualCharacterRiteRva);
  b.parameter_set_contains = reinterpret_cast<ParameterSetContains>(
      base + kFamilyRiteParameterSetContainsRva);
  return b;
}

} // namespace xar::ck3_12004
