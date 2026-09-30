#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kSettlementGlobalAccessorSlotRva = 0x5C6A4B0;
inline constexpr std::uintptr_t kSettlementIdentifierTableGetterRva = 0x3F8A800;
inline constexpr std::uintptr_t kSettlementIdentifierLookupRva = 0x3F8A680;

using SettlementGlobalAccessor = void *(*)();
using SettlementIdentifierTableGetter = void *(*)();
using SettlementIdentifierLookup = std::int32_t *(*)(
    void *table, std::int32_t *output, const void *name_view);

struct SettlementBindings {
  bool enabled = false;
  SettlementGlobalAccessor *global_accessor_slot = nullptr;
  SettlementIdentifierTableGetter identifier_table = nullptr;
  SettlementIdentifierLookup lookup_identifier = nullptr;
};

// Address calculation only. Runtime calls belong to the adapter's existing
// owning-thread snapshot transaction; construction never reads a process.
SettlementBindings BindSettlementImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

enum class SettlementReadResult {
  unavailable,
  not_published,
  invalid_payload,
  published,
};

// Writes only Snapshot's settlement members. An absent ready gate is normal
// before the Mod publishes a death episode; an ABI dependency failure remains
// distinguishable and must not be treated as a valid zero-valued settlement.
SettlementReadResult ReadSettlement(const SettlementBindings &bindings,
                                    const CoreBindings &core,
                                    game::Snapshot &output) noexcept;

} // namespace xar::ck3_12002
