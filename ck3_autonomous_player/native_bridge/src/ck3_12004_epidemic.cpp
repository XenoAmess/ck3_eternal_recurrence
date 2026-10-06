#include "xar_bridge/ck3_12004_epidemic.hpp"

namespace xar::ck3_12004 {
namespace {
// EPIDEMIC2-FUNCTION-AND-OPERAND-MAP.json closes all eight actually called
// helpers, ten binding literals and 89 title/definition/treatment/list checks.
// Sole mapper fresh cost: 3,878 bytes / 36 bounded reads. Existing shared hash
// and identifier proofs are referenced, not recaptured. Historical .3 module
// PASS never admits this profile.
constexpr EpidemicAbiProfile kProfile{
    .actual4_operands_verified = true,
    .title_store = 0x5D1DAF8,
    .modifier_database = 0x8FD4E0,
    .stable_key_hash = 0x3F7E220,
    .modifier_lookup = 0xAB8D20,
    .modifier_fallback = 0x5D1E0B0,
    .county_modifier_getter = 0x1AF5D20,
    .variable_context = 0x370EAF0,
    .variable_identifier_table = 0x3F8A7E0,
    .variable_identifier_lookup = 0x3F8A660,
    .variable_identifier_name = 0x3F8A6D0,
};

bool Admitted(std::uintptr_t base, std::string_view hash) noexcept {
  return base != 0 && hash == kExecutableSha256 &&
      kProfile.actual4_operands_verified;
}
} // namespace

const EpidemicAbiProfile &EpidemicProfile() noexcept { return kProfile; }

EpidemicRecoveryBindings BindEpidemicRecoveryImage(
    std::uintptr_t base, std::string_view hash) noexcept {
  EpidemicRecoveryBindings result{};
  if (!Admitted(base, hash)) return result;
  result.core = BindCoreImage(base, hash);
  result.identifiers.enabled = true;
  result.identifiers.variable_context =
      reinterpret_cast<ck3_12002::PhaseVariableContext>(base + kProfile.variable_context);
  result.identifiers.variable_table =
      reinterpret_cast<ck3_12002::PhaseVariableIdentifierTable>(base + kProfile.variable_identifier_table);
  result.identifiers.lookup_variable_identifier =
      reinterpret_cast<ck3_12002::PhaseVariableIdentifierLookup>(base + kProfile.variable_identifier_lookup);
  result.identifiers.variable_identifier_name =
      reinterpret_cast<ck3_12002::PhaseVariableIdentifierName>(base + kProfile.variable_identifier_name);
  result.landed_title_store_slot = reinterpret_cast<void **>(base + kProfile.title_store);
  result.modifier_fallback_slot = reinterpret_cast<void **>(base + kProfile.modifier_fallback);
  result.modifier_database = reinterpret_cast<ck3_12002::epidemic_recovery::ModifierDatabase>(
      base + kProfile.modifier_database);
  result.stable_key_hash = reinterpret_cast<ck3_12002::epidemic_recovery::StableKeyHash>(
      base + kProfile.stable_key_hash);
  result.modifier_lookup = reinterpret_cast<ck3_12002::epidemic_recovery::ModifierLookup>(
      base + kProfile.modifier_lookup);
  result.county_modifier_getter = reinterpret_cast<ck3_12002::epidemic_recovery::CountyModifierGetter>(
      base + kProfile.county_modifier_getter);
  result.enabled = result.core.enabled;
  return result;
}

EpidemicTreatmentBindings BindEpidemicTreatmentImage(
    std::uintptr_t base, std::string_view hash) noexcept {
  EpidemicTreatmentBindings result{};
  if (!Admitted(base, hash)) return result;
  result.core = BindCoreImage(base, hash);
  result.get_modifier_database = reinterpret_cast<ck3_12002::TreatmentModifierDatabaseGetter12002>(
      base + kProfile.modifier_database);
  result.hash_stable_key = reinterpret_cast<ck3_12002::TreatmentModifierKeyHash12002>(
      base + kProfile.stable_key_hash);
  result.lookup_modifier = reinterpret_cast<ck3_12002::TreatmentModifierLookup12002>(
      base + kProfile.modifier_lookup);
  result.fallback_definition_slot = reinterpret_cast<void **>(base + kProfile.modifier_fallback);
  result.enabled = result.core.enabled;
  return result;
}
} // namespace xar::ck3_12004
