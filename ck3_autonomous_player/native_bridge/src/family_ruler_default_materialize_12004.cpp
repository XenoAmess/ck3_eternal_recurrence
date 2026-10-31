#include "xar_bridge/family_ruler_default_materializer_12004.hpp"

#include <bit>
#include <limits>
#include <utility>

namespace xar::bridge {
namespace {

bool ValidRulerRequest(const FamilyMarriageOutgoingRequestV2 &request) noexcept {
  return request.scope == FamilyMarriageOutgoingScopeV2::action_preparation &&
      request.route == FamilyMarriageOutgoingRouteV2::ruler &&
      request.actor == request.subject && request.actor != 0 &&
      request.actor != UINT32_MAX && request.candidate != 0 &&
      request.candidate != UINT32_MAX && request.actor != request.candidate &&
      !request.expected_recipient && !request.sender &&
      !request.request_matrilineal_option &&
      !request.require_matrilineal_option_off;
}

bool ResolveDefinition(const ck3_12002::ContextBindings &bindings,
                       const FamilyOutgoingStorageAccess12004 &memory,
                       std::uintptr_t &definition) noexcept {
  const auto slot =
      reinterpret_cast<std::uintptr_t>(bindings.interaction_database_slot);
  constexpr auto top = (std::numeric_limits<std::uintptr_t>::max)();
  constexpr auto offset = ck3_12002::kMarriageArrangeMarriageInteractionOffset;
  std::uintptr_t database = 0;
  if (slot == 0 || sizeof(database) - 1 > top - slot ||
      !memory.read_memory(memory.context, slot, &database, sizeof(database)) ||
      database == 0 || offset > top - database)
    return false;
  const auto address = database + offset;
  return sizeof(definition) - 1 <= top - address &&
      memory.read_memory(memory.context, address, &definition,
                         sizeof(definition)) && definition != 0;
}

} // namespace

FamilyRulerMaterializeStatus12004 MaterializeFamilyRulerDefaultContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyRulerPreparedContextCopy12004 &output) noexcept {
  using Status = FamilyRulerMaterializeStatus12004;
  output = {};
  if (!ValidRulerRequest(request)) return Status::invalid_request;
  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.redirect_roles == nullptr ||
      bindings.construct_all_roles == nullptr || bindings.refresh == nullptr ||
      bindings.finalize == nullptr || bindings.validate == nullptr ||
      bindings.destroy == nullptr || access.memory.read_memory == nullptr ||
      access.read_boolean_option == nullptr ||
      access.matrilineal_option_id_slot == 0 ||
      access.grand_wedding_option_id_slot == 0)
    return Status::unavailable;
  std::uintptr_t definition = 0;
  if (!ResolveDefinition(bindings, access.memory, definition))
    return Status::unavailable;
  alignas(8) std::array<std::byte, 0x338> storage{};
  void *context = storage.data();
  bool initialized = false;
  try {
    auto actor = std::bit_cast<std::int32_t>(request.actor);
    auto recipient = std::bit_cast<std::int32_t>(request.candidate);
    auto secondary_actor = actor;
    auto secondary_recipient = recipient;
    std::int32_t intermediary = -1, added_role = -1;
    bindings.redirect_roles(reinterpret_cast<void *>(definition), &actor,
        &recipient, &secondary_actor, &secondary_recipient, &intermediary,
        &added_role);
    void *returned = bindings.construct_all_roles(context,
        reinterpret_cast<void *>(definition), actor, recipient, secondary_actor,
        secondary_recipient, intermediary, nullptr);
    initialized = true;
    Status status = Status::unavailable;
    FamilyRulerPreparedContextCopy12004 local{};
    if (returned == context) {
      bindings.refresh(context, true);
      bindings.finalize(context);
      status = CopyFamilyRulerPreparedContext12004(
          bindings, access, context, definition, local);
    }
    initialized = false;
    bindings.destroy(context);
    if (status == Status::complete) output = std::move(local);
    return status;
  } catch (...) {
    if (initialized) {
      initialized = false;
      try { bindings.destroy(context); } catch (...) {}
    }
    output = {};
    return Status::unavailable;
  }
}

} // namespace xar::bridge
