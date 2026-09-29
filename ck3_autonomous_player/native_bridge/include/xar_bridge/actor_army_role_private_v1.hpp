#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

// Unadvertised, default-off diagnostic. It never changes a role or advances time.
inline constexpr std::string_view kActorArmyRolePrivateStepPrefixV1 =
    "query-war-actor-army-role-v1-";

bool ParseActorArmyRolePrivateStepV1(std::string_view step,
                                    std::int32_t &actor_character_id,
                                    std::int32_t &public_army_id) noexcept;

struct ActorArmyRoleResultV1 {
  std::string status = "unavailable";
  std::string unavailable_stage = "not_read";
  std::uint64_t native_revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t public_army_id = -1;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> current_province_id;
  std::string army_state = "unknown";
  std::optional<bool> in_combat;
  std::optional<bool> retreating;
  std::string commander_status = "unknown";
  std::optional<std::int32_t> commander_character_id;
  std::optional<bool> is_commander_of_requested_army;
  std::string knight_status = "unknown";
  std::optional<std::int32_t> knight_regiment_id;
  std::optional<bool> is_knight_in_requested_army;
};

struct ActorArmyRolePrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  std::uintptr_t module_base = 0;
  std::uint64_t expected_revision = 0;
  game::Snapshot expected_snapshot{};
  std::int32_t actor_character_id = -1;
  std::int32_t public_army_id = -1;
  ActorArmyRoleResultV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool completed = false;
  std::string failure_stage;
};

bool ExecuteActorArmyRolePrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeActorArmyRolePrivateResultV1(
    const ActorArmyRoleResultV1 &result);

} // namespace xar::ck3_11906
