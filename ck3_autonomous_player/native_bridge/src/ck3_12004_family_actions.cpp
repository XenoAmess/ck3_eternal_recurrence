#include "xar_bridge/ck3_12004_family_actions.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
// Faction SEND-COMMAND-CTOR-SOURCE-CLOSED.json: native ctor RIP operands.
constexpr std::uintptr_t kConstructSendCommandRva = 0x2968150;
constexpr std::uintptr_t kSendPrimaryVtableRva = 0x448BCF0;
constexpr std::uintptr_t kSendSecondaryVtableRva = 0x448BCC0;
// actual4-marriage-actions/outbound-map/FAMILY-MAP.json: actual native
// constructor/factory/storage RIP operands, independently admitted for .4.
constexpr std::uintptr_t kPendingStorageSlotRva = 0x5D1EC80;
constexpr std::uintptr_t kInteractionDatabaseSlotRva = 0x5C67538;
constexpr std::uintptr_t kPendingVtableRva = 0x4759250;
constexpr std::uintptr_t kMarriageSpecialVtableRva = 0x44B9938;

bool PendingComponentInitialized(const void *component) noexcept {
  if (component == nullptr) return false;
  std::int32_t full_id{};
  // Existing scanner supplies pending+8 and rejects ID=-1. Actual enum loads
  // pending+10, so the same field is component+8; no native leaf is rebound.
  std::memcpy(&full_id, static_cast<const std::byte *>(component) + 8,
              sizeof(full_id));
  return full_id != -1;
}
} // namespace

ck3_12002::ContextBindings BindArrangeMarriageImage(
    std::uintptr_t base, std::string_view sha,
    const ck3_12002::CommandBindings &actual_commands) noexcept {
  auto bindings = BindFamilyContextImage(base, sha);
  if (!bindings.enabled) return bindings;
  bindings.commands = actual_commands;
  bindings.construct_send_command =
      reinterpret_cast<ck3_12002::MarriageConstructSendInteractionCommand>(
          base + kConstructSendCommandRva);
  bindings.send_primary_vtable = base + kSendPrimaryVtableRva;
  bindings.send_secondary_vtable = base + kSendSecondaryVtableRva;
  return bindings;
}

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
ck3_12002::FamilyBindings BindFamilyActionImage(
    std::uintptr_t base, std::string_view sha,
    const ck3_12002::CommandBindings &actual_commands) noexcept {
  auto bindings = BindFamilyImage(base, sha);
  if (!bindings.enabled) return bindings;
  bindings.context = BindArrangeMarriageImage(base, sha, actual_commands);
  return bindings;
}
#endif

ck3_12002::FamilyOutboundBindings BindFamilyOutboundImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilyOutboundBindings bindings{};
  if (base == 0 || sha != kExecutableSha256) return bindings;
  bindings.enabled = true;
  bindings.module_base = base;
  bindings.pending_storage_slot =
      reinterpret_cast<void **>(base + kPendingStorageSlotRva);
  bindings.interaction_database_slot =
      reinterpret_cast<void **>(base + kInteractionDatabaseSlotRva);
  bindings.component_alive = &PendingComponentInitialized;
  bindings.pending_vtable = base + kPendingVtableRva;
  bindings.marriage_special_vtable = base + kMarriageSpecialVtableRva;
  return bindings;
}

} // namespace xar::ck3_12004
