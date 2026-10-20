#pragma once
#include "ghw_variable_observer_12004.hpp"
#include "xar_bridge/ck3_12004_family_break_penalty.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"

namespace xar::ck3_12004::religion::ghw_variables_candidate {
// Existing owner transaction supplies guarded memory reads and a current
// player/Faith/Religion frame. These are not exposed to a client or persisted.
struct BindingState {
  void *owner_context = nullptr;
  ReadMemory owner_read_memory = nullptr;
  ReadBoundFrame owner_read_frame = nullptr;
  ck3_12002::PhaseDefinitionBindings identifiers{};
  ck3_12004::SettlementBindings global{};
};
// Address-only factory. No native function or memory read is executed here.
// The caller keeps state alive, on the owning thread, throughout both passes.
Access BindGhwVariableAccess12004(BindingState &, std::uintptr_t image_base,
    std::string_view executable_sha256, void *owner_context,
    ReadMemory, ReadBoundFrame) noexcept;
} // namespace xar::ck3_12004::religion::ghw_variables_candidate
