#include "xar_bridge/ck3_12004_holy_order_bindings.hpp"

#include "xar_bridge/ck3_12003_holy_order_hire_wire.hpp"
#include "xar_bridge/ck3_12004_hired_troop_shared_bindings.hpp"

namespace xar::ck3_12004::religion::holy_order {
namespace old = ck3_12003::religion::holy_order;

Bindings BindPlayerHolyOrderImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  const auto shared = hired_troops::BindHiredTroopSharedImage12004(base, sha);
  if (!shared.enabled) return b;
  // Actual .4 RIP operands and complete native entrances, not a shifted old
  // image binder. See the source-first actual4 topic and operand ledger.
  b.manager_slot = reinterpret_cast<void **>(base + 0x5D1DF10);
  b.fallback_slot = reinterpret_cast<void **>(base + 0x5D1DF00);
  b.patron = reinterpret_cast<old::Patron>(base + 0x2618D60);
  b.is_military = reinterpret_cast<old::IsMilitary>(base + 0x261C470);
  b.can_hire = reinterpret_cast<old::CanHire>(base + 0x2619C30);
  b.cost = reinterpret_cast<old::Cost>(base + 0x26198C0);
  b.can_afford = shared.can_afford;
  b.reason_destroy = shared.reason_destroy;
  b.current_soldiers = reinterpret_cast<old::CurrentSoldiers>(base + 0x261ACF0);
  b.current_war_eligibility = reinterpret_cast<old::CanHire>(base + 0x261C100);
  b.release_eligible = reinterpret_cast<old::LifecyclePredicate>(base + 0x261A1B0);
  b.associated_regiment_in_combat =
      reinterpret_cast<old::LifecyclePredicate>(base + 0x261D5D0);
  b.regiment_registry_slot = reinterpret_cast<void **>(base + 0x5D1F340);
  b.army_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  b.combat_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE70);
  b.hire_cost_context.title_registry_slot =
      reinterpret_cast<void **>(base + 0x5D1DAF8);
  b.hire_cost_context.title_fallback_slot =
      reinterpret_cast<void **>(base + 0x5D1DAE0);
  b.hire_cost_context.patron_hire_multiplier_raw =
      reinterpret_cast<const std::int64_t *>(base + 0x5C69250);
  b.hire_cost_context.patron_recall_multiplier_raw =
      reinterpret_cast<const std::int64_t *>(base + 0x5C69248);

  auto &reinforcement = b.current_reinforcement;
  reinforcement.persistent_registry_slot =
      reinterpret_cast<void **>(base + 0x5D1EB68);
  reinforcement.monthly_fraction =
      reinterpret_cast<decltype(reinforcement.monthly_fraction)>(base + 0x262CAB0);
  reinforcement.months_to_full =
      reinterpret_cast<decltype(reinforcement.months_to_full)>(base + 0x262BC70);
  reinforcement.can_replenish =
      reinterpret_cast<decltype(reinforcement.can_replenish)>(base + 0x262C6E0);
  reinforcement.chunk_can_replenish =
      reinterpret_cast<decltype(reinforcement.chunk_can_replenish)>(base + 0x2657EF0);
  reinforcement.army_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  reinforcement.unit_registry_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  reinforcement.enabled = true;
  b.enabled = true;
  return b;
}

HireActionBindings BindHolyOrderHireActionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  HireActionBindings b{};
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  b.context = BindPlayerHolyOrderImage12004(base, sha);
  b.commands = hired_troops::BindHiredTroopSharedImage12004(base, sha).commands;
  // Both addresses are actual .4 constructor/clone RIP targets. Their native
  // slots prove CanExecute+30 and hidden owning-pointer Clone+40.
  b.primary_vtable = base + 0x476D9D8;
  b.secondary_vtable = base + 0x476D9A8;
  b.validate_source = reinterpret_cast<old::HireCommandValidator>(base + 0x29947F0);
  b.enabled = b.context.enabled && b.commands.enabled;
  return b;
}

std::string SerializeHolyOrderHireResult12004(const HireActionResult &action,
    std::string_view request_id, std::uint64_t command_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    const game::AdapterDescriptor &descriptor) {
  if (!game::IsCk3_12004Descriptor(descriptor)) return {};
  return game::Render12004BuildIdentity(ck3_12003::SerializeHolyOrderHireResultV1(
      action, request_id, command_sequence, snapshot_revision, date_raw), descriptor);
}

} // namespace xar::ck3_12004::religion::holy_order
