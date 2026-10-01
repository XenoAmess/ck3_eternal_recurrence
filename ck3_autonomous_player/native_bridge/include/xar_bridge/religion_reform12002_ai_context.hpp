#pragma once
#include "xar_bridge/ck3_12002.hpp"
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion_reform {
inline constexpr std::size_t kAIContextStateDataOffset = 0xA0;
inline constexpr std::size_t kAIContextManagerOffset = 0x2D48;
inline constexpr std::size_t kAIContextHolderOffset = 0x20;
inline constexpr std::size_t kAIContextDefaultOffset = 0x08;
inline constexpr std::size_t kAIContextArrayOffset = 0x10;
inline constexpr std::size_t kAIContextCountOffset = 0x1C;
inline constexpr std::size_t kAIContextActorOffset = 0x18;
inline constexpr std::size_t kAIContextTypeOffset = 0x28;
inline constexpr std::size_t kAIContextActiveOffset = 0x2C;
inline constexpr std::size_t kAIContextSpecialOffset = 0x2E;

struct AIContextBindings {
  bool enabled = false;
  const void *const *game_state_slot = nullptr;
};
enum class AIContextStatus { bindings_unavailable, actor_unavailable,
    container_unavailable, observed_no_ai, observed_controllers };
enum class AIControllerKind { ordinary, player_special };
struct ActorAIController {
  AIControllerKind kind = AIControllerKind::ordinary;
  // Internal pointer for the same paused owner; serializer omits this field.
  const void *actual_ai = nullptr;
  std::uint8_t active_raw = 0;
  std::uint8_t special_raw = 0;
};
struct ActorAIContext {
  AIContextStatus status = AIContextStatus::bindings_unavailable;
  std::uint32_t actor_id = 0xFFFFFFFFU;
  std::int32_t actual_holder_count = 0;
  std::vector<ActorAIController> controllers;
};
AIContextBindings BindReformAIContextImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// Existing paused owner supplies its already-resolved played actor/full ID.
// Reads the actual table only; never invokes a creator or native updater.
ActorAIContext ReadActorReformAIContext12002(
    const AIContextBindings &bindings, void *resolved_actor,
    std::uint32_t expected_full_actor_id);
std::string SerializeActorReformAIContext12002(const ActorAIContext &context);
} // namespace xar::ck3_12002::religion_reform
