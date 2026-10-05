#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12003::task_position {

struct ScopeToken {
  std::int32_t kind = 0;
  std::int32_t padding = 0;
  std::uint64_t payload = 0;
};
static_assert(sizeof(ScopeToken) == 0x10);

using ReadMemory = bool (*)(void *, const void *, void *, std::size_t);
using InitializeModifierVector = void (*)(void *);
using CollectScopedDeclarations = void (*)(void *, const void *, const void *);
using ConstructActorScope = void *(*)(void *, const std::int32_t *);
using Destroy = void (*)(void *);
using SaveScope = void (*)(void *, std::int32_t, const ScopeToken *);
using TaskGate = bool (*)(const void *);
using OwnerModifierBuilder = void *(*)(const void *, void *, const void *);

struct Bindings {
  bool enabled = false;
  ReadMemory read_memory = nullptr;
  void *read_memory_context = nullptr;
  void **task_storage_slot = nullptr;
  void **task_fallback_slot = nullptr;
  InitializeModifierVector initialize_modifier_vector = nullptr;
  CollectScopedDeclarations collect_scoped_declarations = nullptr;
  ConstructActorScope construct_actor_scope = nullptr;
  Destroy destroy_scope = nullptr;
  SaveScope save_scope = nullptr;
  const std::int32_t *saved_scope_token_0 = nullptr;
  const std::int32_t *saved_scope_token_4 = nullptr;
  TaskGate task_gate = nullptr;
  OwnerModifierBuilder owner_modifier_builder = nullptr;
  Destroy destroy_modifier = nullptr;
};

Bindings BindImage12003(std::uintptr_t image_base,
                       std::string_view executable_sha256) noexcept;

// Character is the existing actual requested Character, already resolved by
// the current-person producer. This helper writes only its own temporary data.
game::BattleCurrentPersonTaskPositionInputsSnapshotV1 ReadInputs12003(
    const Bindings &, const void *character, std::int32_t character_id) noexcept;

} // namespace xar::ck3_12003::task_position
