#pragma once
#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_prisoner_war_retention.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include <charconv>
#include <limits>
#include <optional>

namespace xar::ck3_12002 {
struct PrisonerPrivateWorkerState12002 {
  std::uint64_t query_sequence = 0;
  std::uint64_t war_query_sequence = 0;
  std::optional<PlayerPrisonerRansomQuoteV1> current_quote;
  std::uint64_t quote_revision = 0;
  std::uint64_t quote_query_sequence = 0;
  bool may_have_submitted = false;
};
inline constexpr std::string_view kPrisonerWarRetentionStepPrefix12002 =
    "query-war-prisoner-release-pairs-v1-";
inline std::optional<std::int32_t> ParsePrisonerWarRetentionStep12002(
    std::string_view step) noexcept {
  if (!step.starts_with(kPrisonerWarRetentionStepPrefix12002)) return std::nullopt;
  const auto text = step.substr(kPrisonerWarRetentionStepPrefix12002.size());
  if (text.empty() || text.front() == '0') return std::nullopt;
  std::uint32_t id = 0;
  const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), id);
  if (error != std::errc{} || end != text.data() + text.size() || id == 0 ||
      id > static_cast<std::uint32_t>((std::numeric_limits<std::int32_t>::max)()))
    return std::nullopt;
  return static_cast<std::int32_t>(id);
}
bool ExecutePlayerPrisonerCollection12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecutePlayerPrisonerRansom12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool HandlePlayerPrisonerPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12002 &state, std::string &serialized,
    std::string &failure);
} // namespace xar::ck3_12002
