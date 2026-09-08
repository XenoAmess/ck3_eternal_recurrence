#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kSetPlayedCharacterV1Capability =
    "game.command.set-played-character-v1-N";
inline constexpr std::string_view kSetPlayedCharacterV1StepPrefix =
    "set-played-character-v1-";
inline constexpr std::uint32_t
    kSetPlayedCharacterV1WaitBudgetMilliseconds = 8'000;

std::optional<std::int32_t>
ParseSetPlayedCharacterV1Step(std::string_view step) noexcept;

struct SetPlayedCharacterMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::int32_t target_character_id = -1;
  game::SetPlayedCharacterResult result =
      game::SetPlayedCharacterResult::unavailable;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

bool ExecuteSetPlayedCharacterMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

bool RunSetPlayedCharacterMailboxV1(
    SetPlayedCharacterMailboxContextV1 &context,
    std::uint32_t wait_budget_milliseconds =
        kSetPlayedCharacterV1WaitBudgetMilliseconds) noexcept;

std::string_view SetPlayedCharacterResultCodeV1(
    game::SetPlayedCharacterResult result) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteSetPlayedCharacterMailboxV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
