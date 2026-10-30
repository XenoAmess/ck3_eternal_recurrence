#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <bit>
#include <charconv>

namespace xar::ck3_12002 {
namespace {
bool ReasonCharacterField(std::string_view json, std::string_view key,
                           std::int32_t &output) noexcept {
  const std::string needle = "\"" + std::string(key) + "\":";
  const auto field = json.find(needle);
  if (field == std::string_view::npos) return false;
  auto begin = field + needle.size();
  const auto space = [](char c) noexcept {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
  };
  while (begin < json.size() && space(json[begin])) ++begin;
  auto end = begin;
  if (end < json.size() && json[end] == '-') ++end;
  const auto digits = end;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  if (end == digits || (end - digits > 1 && json[digits] == '0') ||
      (end - begin == 2 && json[begin] == '-' && json[digits] == '0')) return false;
  auto delimiter = end;
  while (delimiter < json.size() && space(json[delimiter])) ++delimiter;
  if (delimiter == json.size() || (json[delimiter] != ',' && json[delimiter] != '}')) return false;
  std::int32_t value{};
  const auto parsed = std::from_chars(json.data() + begin, json.data() + end, value);
  if (parsed.ec != std::errc{} || parsed.ptr != json.data() + end || value == -1) return false;
  output = value;
  return true;
}

bool Parse(std::string_view payload, std::uint64_t &expected_revision,
           SwayInvalidationReasonQuery12002 &request, bool actual4) noexcept {
  if (actual4) {
    std::int32_t actor{}, target{};
    std::uint64_t scheme{};
    if (!bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
        !ReasonCharacterField(payload, "actor_character_id", actor) ||
        !ReasonCharacterField(payload, "target_character_id", target) ||
        !bridge::JsonUnsignedField(payload, "scheme_instance_id", scheme) ||
        !bridge::JsonUnsignedField(payload, "after_sequence", request.after_sequence) ||
        scheme >= std::numeric_limits<std::uint32_t>::max()) return false;
    request.actor_character_id = std::bit_cast<std::uint32_t>(actor);
    request.target_character_id = std::bit_cast<std::uint32_t>(target);
    request.scheme_id = static_cast<std::uint32_t>(scheme);
    return expected_revision != 0 && actor != target;
  }
  std::uint64_t actor{}, target{}, scheme{};
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
      !bridge::JsonUnsignedField(payload, "actor_character_id", actor) ||
      !bridge::JsonUnsignedField(payload, "target_character_id", target) ||
      !bridge::JsonUnsignedField(payload, "scheme_instance_id", scheme) ||
      !bridge::JsonUnsignedField(payload, "after_sequence", request.after_sequence) ||
      actor > std::numeric_limits<std::int32_t>::max() ||
      target > std::numeric_limits<std::int32_t>::max() ||
      scheme >= std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  request.actor_character_id = static_cast<std::uint32_t>(actor);
  request.target_character_id = static_cast<std::uint32_t>(target);
  request.scheme_id = static_cast<std::uint32_t>(scheme);
  return expected_revision != 0 && actor != 0 && target != 0 && actor != target;
}
} // namespace

bool HandleSwayCompletionInvalidationReasonV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayInvalidationReasonRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear();
  failure.clear();
  try {
    SwayCompletionInvalidationReasonMailboxContextV1 query{};
    std::uint64_t expected_revision{};
    const bool actual4 = adapter.descriptor().game_version == ck3_12004::kGameVersion &&
        adapter.descriptor().executable_sha256 == ck3_12004::kExecutableSha256;
    if (step != kSwayCompletionInvalidationReasonStepV1 || !Parse(payload, expected_revision, query.request, actual4) ||
        expected_revision != revision || !adapter.enabled() ||
        (!actual4 && xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256) ||
        !published.paused || !published.map_ready || !published.has_played_character ||
        !published.played_character_alive ||
        static_cast<std::uint32_t>(published.played_character_id) != query.request.actor_character_id) {
      failure = "sway_invalidation_reason_frame_or_request_invalid";
      return false;
    }
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.recorder = &recorder;
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayCompletionInvalidationReasonMailboxV1,
                                  &query.envelope, query.envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "sway_invalidation_reason_executor_unavailable";
      return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running) {
      waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2000);
    }
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !query.envelope.frame_stable || !query.failure.empty()) {
      failure = query.failure.empty() ? "sway_invalidation_reason_executor_result_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeSwayCompletionInvalidationReasonCommandResultV1(
        query.result, revision, query.envelope.execution_stamp.date_raw, request_id,
        actual4 ? ck3_12004::kGameVersion : "1.20.0.2",
        actual4 ? ck3_12004::kExecutableSha256 : kExecutableSha256);
    return true;
  } catch (...) {
    failure = "sway_invalidation_reason_handler_exception";
    return false;
  }
}

} // namespace xar::ck3_12002
