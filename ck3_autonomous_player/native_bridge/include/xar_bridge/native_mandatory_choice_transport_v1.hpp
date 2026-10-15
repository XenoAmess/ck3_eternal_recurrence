#pragma once

#include "xar_bridge/ck3_12004_modal_choice_port_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::mandatory_choice_v1 {

inline constexpr std::string_view kCapability =
    "game.state.native-mandatory-choice-window-v1";
inline constexpr std::string_view kQueryStep = "query-mandatory-choice-v1";
inline constexpr std::string_view kSelectStep = "select-mandatory-choice-v1";

// Owned by the connection worker; Gate is used only by the proven application
// owner executor. Never reset it while a mailbox ticket may still execute.
struct Session {
  Gate gate;
  Frame last_query_frame;
  std::uintptr_t last_receiver = 0;
  std::string last_window_id;
  std::string last_window_instance_id;
  TypedWindowRelation last_typed_relation{};
  std::uint64_t connection_generation = 0;
  void Reset(std::uint64_t generation) noexcept {
    gate.Clear(); last_query_frame = {}; last_receiver = 0;
    last_window_id.clear(); last_window_instance_id.clear();
    last_typed_relation = {};
    connection_generation = generation;
  }
};

struct MailboxContext {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch{};
  Session *session = nullptr;
  std::string request_id;
  std::string step;
  Frame requested_frame{};
  SelectRequest selection{};
  std::uint64_t state_revision = 0;
  std::uint64_t connection_generation = 0;
  QueryResult query_result{};
  TypedWindowRelation typed_relation{};
  SelectResult select_result{};
  bool completed = false;
  bool owner_verified = false;
  bool query_operation = false;
  bool old_receiver_read = false;
  bool old_receiver_still_registered = true;
  std::string old_window_id;
  std::string old_window_instance_id;
  std::string_view dispatch_stage = "not_attempted";
  std::uint32_t dispatch_exception_code = 0;
  std::string unavailable_reason;
  ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
};

std::string_view PrepareMailbox(
    const game::GameAdapter &game, const game::Snapshot *previous_snapshot,
    std::string_view request_id, std::string_view step, std::string_view payload,
    std::uint64_t state_revision, std::uint64_t connection_generation,
    std::uintptr_t module_base,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, Session &session,
    MailboxContext &context) noexcept;

bool ExecuteMailbox(void *opaque,
                    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

std::string CommandResultFrame(const MailboxContext &context);

} // namespace xar::mandatory_choice_v1
