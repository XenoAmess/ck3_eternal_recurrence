#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_actor_resources.hpp"
#include "xar_bridge/ck3_12002_events.hpp"
#include "xar_bridge/ck3_12002_settlement.hpp"

namespace xar::ck3_12004 {

inline constexpr std::size_t kEventManagerOffset12004 = 0x34480;
inline constexpr std::uintptr_t kGetCurrentEventRva12004 = 0x29C5780;
inline constexpr std::uintptr_t kPendingInteractionStorageSlotRva12004 = 0x5D1EC80;
inline constexpr std::uintptr_t kIsPendingInteractionForCharacterRva12004 = 0x136D190;
inline constexpr std::uintptr_t kValidateReplyInteractionRva12004 = 0x2968470;
inline constexpr std::uintptr_t kReplyInteractionPrimaryVtableRva12004 = 0x448BC28;
inline constexpr std::uintptr_t kReplyInteractionSecondaryVtableRva12004 = 0x448BBF8;

// Software DTO/function types are shared; the binder supplies only actual .4
// functions, slots and the vtables reached by readonly pending validation.
struct SnapshotEventBindings {
  CoreBindings core;
  ck3_12002::GetCurrentEvent get_current_event = nullptr;
  void **pending_interaction_storage_slot = nullptr;
  ck3_12002::IsPendingInteractionForCharacter is_pending_for_character = nullptr;
  ck3_12002::ValidateReplyInteraction validate_reply = nullptr;
  std::uintptr_t reply_primary_vtable = 0;
  std::uintptr_t reply_secondary_vtable = 0;
};

using ActorResourceBalances = ck3_12002::ActorResourceBalances12002;
using SettlementBindings = ck3_12002::SettlementBindings;
using SettlementReadResult = ck3_12002::SettlementReadResult;

inline constexpr std::uintptr_t kSettlementGlobalAccessorSlotRva12004 = 0x5C6A4B0;
inline constexpr std::uintptr_t kSettlementIdentifierTableGetterRva12004 = 0x3F8A7E0;
inline constexpr std::uintptr_t kSettlementIdentifierLookupRva12004 = 0x3F8A660;

struct SnapshotFoundationBindings {
  CoreBindings core;
  SnapshotEventBindings events;
  SettlementBindings settlement;
};

SnapshotFoundationBindings BindSnapshotFoundationImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
SnapshotEventBindings BindSnapshotEventsImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
SettlementBindings BindSnapshotSettlementImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

bool ReadActorResourceBalances(const CoreBindings &core,
    std::int32_t played_character_id, ActorResourceBalances &output) noexcept;
bool ReadWarCashTreasury(const CoreBindings &core,
    std::int32_t played_character_id, std::int64_t &gold_raw) noexcept;
bool ReadEventsSnapshot(const SnapshotEventBindings &bindings,
    game::Snapshot &output) noexcept;
SettlementReadResult ReadSettlement(const SettlementBindings &bindings,
    const CoreBindings &core, game::Snapshot &output) noexcept;

} // namespace xar::ck3_12004
