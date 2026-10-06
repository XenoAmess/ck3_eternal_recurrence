#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

namespace xar::ck3_12004 {
namespace {
template<class Fn> Fn Function(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return reinterpret_cast<Fn>(base + rva);
}
} // namespace

ck3_12002::SwayStateBindings12002 BindSwayStateImage12004(
    std::uintptr_t base, std::string_view sha256) noexcept {
  ck3_12002::SwayStateBindings12002 b{};
  b.core = BindCoreImage(base, sha256);
  if (!b.core.enabled) return b;
  b.module_base = base;
  b.opinion = Function<ck3_12002::SwayReadOpinion12002>(base, 0x28BC470);
  b.manager_offset = 0xA5C0;
  b.manager_vtable_rva = 0x4779548;
  b.storage_vtable_rva = 0x4779838;
  b.instance_vtable_rva = 0x47794F8;
  b.type_vtable_rva = 0x48B9F30;
  b.executable_sha256 = kExecutableSha256;
  // Actual constructor/serializer source operands preserve the storage and
  // instance offsets. Named primary RTTI/COL roles and the three current
  // getter field instructions are sealed in this migration's native-source.
  b.enabled = true;
  return b;
}

ck3_12002::SwayCommandBindingsV1 BindSwayCommandImage12004(
    std::uintptr_t base, std::string_view sha256) noexcept {
  ck3_12002::SwayCommandBindingsV1 b{};
  b.context.core = BindCoreImage(base, sha256);
  if (!b.context.core.enabled) return b;
  // Source: shared actual4 Prisoner/FamilyAlliance callbacks, Sway map01,
  // Faction/Diplomacy's complete Send constructor and Entry's command core.
  b.context.commands = BindCommandImage12004(base, sha256);
  if (!b.context.commands.enabled) return b;
  b.context.interaction_database_slot = reinterpret_cast<void **>(base + 0x5C67538);
  b.context.refresh = Function<ck3_12002::MarriageRefreshInteractionContext>(base, 0x3078A40);
  b.context.finalize = Function<ck3_12002::MarriageFinalizeInteractionContext>(base, 0x3078C70);
  b.context.validate = Function<ck3_12002::MarriageValidateInteractionContext>(base, 0x307C020);
  b.context.destroy = Function<ck3_12002::MarriageDestroyInteractionContext>(base, 0x3077380);
  b.context.evaluate_cost = Function<ck3_12002::MarriageEvaluateInteractionCost>(base, 0x310CEC0);
  b.context.construct_send_command = Function<ck3_12002::MarriageConstructSendInteractionCommand>(base, 0x2968150);
  b.context.send_primary_vtable = base + 0x448BCF0;
  b.context.send_secondary_vtable = base + 0x448BCC0;
  b.context.enabled = true;
  b.construct_two_roles = Function<ck3_12002::ConstructInteractionContext>(base, 0x3076C70);
  b.shown = Function<ck3_12002::SwayReadShownV1>(base, 0x3079690);
  b.valid = Function<ck3_12002::SwayReadValidityV1>(base, 0x307AB50);
  b.definition_primary_vtable = base + 0x48C2228;
  b.definition_secondary_vtable = base + 0x48C2238;
  b.enabled = true;
  return b;
}

ck3_12002::SwayOutcomeBindings BindSwayOutcomeOpinionImage12004(
    std::uintptr_t base, std::string_view sha256) noexcept {
  ck3_12002::SwayOutcomeBindings b{};
  b.event_window.events.core = BindCoreImage(base, sha256);
  if (!b.event_window.events.core.enabled) return b;
  // Only the adopted independent material reader is reached. Event/window
  // constructors and scheme-storage callbacks remain unbound here.
  b.event_window.hash_stable_key = Function<ck3_12002::EventHashStableKey>(base, 0x3F7E220);
  b.target_opinion = Function<ck3_12002::SwayOutcomeTargetOpinion>(base, 0x28BC470);
  auto &m = b.opinion_modifiers;
  m.core = b.event_window.events.core;
  m.module_base = base;
  m.modifier_database_slot = reinterpret_cast<void **>(base + 0x5D207E0);
  m.read_opinion = Function<ck3_12002::GiftReadCharacterOpinion12002>(base, 0x28BC470);
  m.lookup_modifier = Function<ck3_12002::GiftLookupOpinionModifier12002>(base, 0x25A2EE0);
  m.find_group = Function<ck3_12002::GiftFindOpinionGroup12002>(base, 0x2949A80);
  m.sum_modifier = Function<ck3_12002::GiftSumOpinionModifier12002>(base, 0x2596290);
  m.modifier_primary_vtable = base + 0x48C5380;
  m.modifier_secondary_vtable = base + 0x48C5348;
  m.active_opinion_vtable = base + 0x473DE18;
  m.temporary_opinion_vtable = base + 0x473DDE0;
  m.enabled = true;
  b.build_version = kGameVersion;
  return b;
}
} // namespace xar::ck3_12004
