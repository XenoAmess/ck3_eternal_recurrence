#include "xar_bridge/religion_reform12002_ai_context.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template <typename T> T AIContextLoad(const void *p, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p)+offset, sizeof(value));
  return value;
}
const char *StatusKey(AIContextStatus status) {
  switch (status) {
  case AIContextStatus::bindings_unavailable: return "bindings_unavailable";
  case AIContextStatus::actor_unavailable: return "actor_unavailable";
  case AIContextStatus::container_unavailable: return "container_unavailable";
  case AIContextStatus::observed_no_ai: return "observed_no_ai";
  case AIContextStatus::observed_controllers: return "observed_controllers";
  }
  return "bindings_unavailable";
}
}
AIContextBindings BindReformAIContextImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  AIContextBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.game_state_slot = reinterpret_cast<const void *const *>(base+kGameStateSlotRva);
  return b;
}
ActorAIContext ReadActorReformAIContext12002(
    const AIContextBindings &b, void *actor, std::uint32_t expected_id) {
  ActorAIContext out{};
  if (!b.enabled || !b.game_state_slot) return out;
  out.status = AIContextStatus::actor_unavailable;
  if (!actor || expected_id==0xFFFFFFFFU ||
      AIContextLoad<std::uint32_t>(actor,0x18)!=expected_id ||
      AIContextLoad<std::uint32_t>(actor,0x1C)!=0x43686172U) return out;
  out.actor_id = expected_id;
  out.status = AIContextStatus::container_unavailable;
  const auto *root = *b.game_state_slot;
  if (!root) return out;
  const auto *state = AIContextLoad<const void *>(root,kAIContextStateDataOffset);
  if (!state) return out;
  const auto *manager = static_cast<const std::byte *>(state)+kAIContextManagerOffset;
  const auto *holder = AIContextLoad<const void *>(manager,kAIContextHolderOffset);
  if (!holder) return out;
  const auto *array = AIContextLoad<const void *>(holder,kAIContextArrayOffset);
  const auto count = AIContextLoad<std::int32_t>(holder,kAIContextCountOffset);
  if (count<0 || (!array && count)) return out;
  out.actual_holder_count = count;
  const auto *default_ai = AIContextLoad<const void *>(holder,kAIContextDefaultOffset);
  for (std::int32_t n=0;n<count;++n) {
    const auto *ai = AIContextLoad<const void *>(
        array,static_cast<std::size_t>(n)*sizeof(void *));
    if (!ai || ai==default_ai ||
        AIContextLoad<const void *>(ai,kAIContextActorOffset)!=actor ||
        AIContextLoad<std::uint32_t>(ai,kAIContextTypeOffset)!=0x41495374U)
      continue;
    ActorAIController c{};
    c.actual_ai = ai;
    c.active_raw = AIContextLoad<std::uint8_t>(ai,kAIContextActiveOffset);
    c.special_raw = AIContextLoad<std::uint8_t>(ai,kAIContextSpecialOffset);
    c.kind = c.special_raw ? AIControllerKind::player_special : AIControllerKind::ordinary;
    out.controllers.push_back(c);
  }
  out.status = out.controllers.empty() ? AIContextStatus::observed_no_ai
                                      : AIContextStatus::observed_controllers;
  return out;
}
std::string SerializeActorReformAIContext12002(const ActorAIContext &c) {
  const bool observed = c.status==AIContextStatus::observed_no_ai ||
                        c.status==AIContextStatus::observed_controllers;
  std::string out = "{\"schema\":\"ck3_12002_reform_ai_context_v1\",\"status\":\"";
  out += StatusKey(c.status);
  out += "\",\"available\":";
  out += observed ? "true" : "false";
  out += ",\"actor_id\":";
  out += c.actor_id==0xFFFFFFFFU ? "null" : std::to_string(c.actor_id);
  out += ",\"actual_holder_count\":"+std::to_string(c.actual_holder_count);
  out += ",\"controllers\":[";
  bool first=true;
  for (const auto &row:c.controllers) {
    if (!first) out += ',';
    first=false;
    out += "{\"kind\":\"";
    out += row.kind==AIControllerKind::ordinary ? "ordinary" : "player_special";
    out += "\",\"active_raw\":"+std::to_string(row.active_raw);
    out += ",\"special_raw\":"+std::to_string(row.special_raw)+'}';
  }
  return out+"]}";
}
} // namespace xar::ck3_12002::religion_reform
