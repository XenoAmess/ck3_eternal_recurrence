#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"
#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::bridge {

struct FamilyRulerPreparedContextCopy12004 {
  // Borrowed game definition identity, never serialized. The owning caller
  // controls its lifetime and supplies the matching real inventory request.
  std::uintptr_t actual_definition = 0;
  std::uint32_t definition_hash = 0;
  std::array<std::uint32_t, 5> roles{};
  std::vector<FamilyOutgoingOptionCopy12004> options{};
  bool can_send = false;
  bool matrilineal = false;
  bool grand_wedding = false;
  friend bool operator==(const FamilyRulerPreparedContextCopy12004 &,
                         const FamilyRulerPreparedContextCopy12004 &) = default;
};

using FamilyRulerReadBooleanOption12004 = bool (*)(const void *, std::uint32_t);
struct FamilyRulerContextAccess12004 {
  FamilyOutgoingStorageAccess12004 memory{};
  FamilyRulerReadBooleanOption12004 read_boolean_option = nullptr;
  std::uintptr_t matrilineal_option_id_slot = 0;
  std::uintptr_t grand_wedding_option_id_slot = 0;
};

enum class FamilyRulerMaterializeStatus12004 : std::uint8_t {
  complete,
  invalid_request,
  unavailable,
  changed
};

// Actual owning-thread native calls: validate/read_boolean_option. The caller
// owns this already constructed 0x338 context throughout both complete copies.
// The raw +0x2EC actor shadow must equal the public actor; it is never exposed
// as a sixth role. No option setter, send or command constructor is invoked.
// A complete result may contain can_send=false. Every failure resets output.
FamilyRulerMaterializeStatus12004 CopyFamilyRulerPreparedContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const void *actual_owned_context, std::uintptr_t expected_definition,
    FamilyRulerPreparedContextCopy12004 &output) noexcept;

// Only ACTION_PREPARATION/RULER with actor==subject and the actual distinct
// candidate. Mirrors the existing public PrepareContext sequence, including
// all six redirect arguments and five all-role constructor operands. It owns
// the aligned context and destroys it exactly once after normal construction.
// No command, queue, character selection or private-route lineality is used.
// The real owning frame/thread and already resolved binding lifetime belong
// to the caller; this component does not itself install a query provider.
FamilyRulerMaterializeStatus12004 MaterializeFamilyRulerDefaultContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const FamilyMarriageOutgoingRequestV2 &request,
    FamilyRulerPreparedContextCopy12004 &output) noexcept;

// The actual FamilyMarriageSendReads.prepared JSON object only. RULER keeps
// effective_matrilineal_if_accepted=null; current booleans and every authored
// option byte still come from the owned native context. No envelope/storage
// availability is invented. Invalid data throws std::invalid_argument.
std::string SerializeFamilyRulerPreparedContext12004(
    const FamilyRulerPreparedContextCopy12004 &copy);

} // namespace xar::bridge
