#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_sway_outcome_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
std::string Quoted(std::string_view value) {
  std::string output = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '\\' || ch == '"') { output += '\\'; output += static_cast<char>(ch); }
    else if (ch < 32) { output += "\\u00"; output += hex[ch >> 4]; output += hex[ch & 15]; }
    else output += static_cast<char>(ch);
  }
  return output + '"';
}

bool Parse(std::string_view payload, bool opinion_only, SwayOutcomeRequestV1 &request) noexcept {
  using bridge::JsonUnsignedField;
  std::uint64_t event{}, actor{}, target{}, scheme{};
  if (!JsonUnsignedField(payload, "expected_revision", request.expected_revision) ||
      !JsonUnsignedField(payload, "actor_character_id", actor) ||
      !JsonUnsignedField(payload, "target_character_id", target) ||
      (!opinion_only && (!JsonUnsignedField(payload, "event_instance_id", event) ||
                         !JsonUnsignedField(payload, "scheme_instance_id", scheme))) ||
      event > std::numeric_limits<std::int32_t>::max() ||
      actor > std::numeric_limits<std::int32_t>::max() ||
      target > std::numeric_limits<std::int32_t>::max() ||
      scheme >= std::numeric_limits<std::uint32_t>::max()) return false;
  request.event_instance_id = static_cast<std::int32_t>(event);
  request.actor_character_id = static_cast<std::int32_t>(actor);
  request.target_character_id = static_cast<std::int32_t>(target);
  request.scheme_id = static_cast<std::uint32_t>(scheme);
  return request.expected_revision != 0 && actor != 0 && target != 0 && actor != target;
}
} // namespace

bool ExecuteSwayOutcomeMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &query = *static_cast<SwayOutcomeMailboxContextV1 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecuteSwayOutcomeMailboxV1)) {
    query.failure = "sway_outcome_published_frame_changed";
    query.completed = true;
    return true;
  }
  if (query.opinion_only)
    (void)ReadSwayOutcomeOpinionV1(query.bindings, query.request.actor_character_id,
                                 query.request.target_character_id, query.opinion_result);
  else (void)ReadSwayOutcomeEventV1(query.bindings, query.request, query.result);
  query.completed = true;
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool HandleSwayOutcomeEventV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear();
  failure.clear();
  try {
    SwayOutcomeMailboxContextV1 query{};
    query.opinion_only = step == kSwayOutcomeOpinionStepV1;
    const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
    if ((step != kSwayOutcomeEventStepV1 && !query.opinion_only) || !Parse(payload, query.opinion_only, query.request) ||
        query.request.expected_revision != revision ||
        !adapter.enabled() || (!actual4 && game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256) ||
        (actual4 && !query.opinion_only) ||
        !published.paused || !published.map_ready || !published.has_played_character ||
        !published.played_character_alive ||
        published.played_character_id != query.request.actor_character_id) {
      failure = "sway_outcome_frame_or_request_invalid";
      return false;
    }
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.bindings = actual4 ? ck3_12004::BindSwayOutcomeOpinionImage12004(
        base, adapter.descriptor().executable_sha256) : BindSwayOutcomeImage(
        base, game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayOutcomeMailboxV1,
                                  &query.envelope, query.envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "sway_outcome_executor_unavailable";
      return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2000);
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !query.envelope.frame_stable || !query.failure.empty()) {
      failure = query.failure.empty() ? "sway_outcome_executor_result_unavailable" : query.failure;
      return false;
    }
    if (query.opinion_only) {
      serialized = SerializeSwayOutcomeOpinionResponseV1(
          query.opinion_result, revision, query.envelope.execution_stamp.date_raw,
          request_id);
      return true;
    }
    const auto native = SerializeSwayOutcomeEventV1(query.result);
    const bool available = query.result.available;
    serialized = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
        Quoted(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quoted(step) +
        ",\"accepted\":true,\"status\":" + Quoted(available ? "available" : "unavailable") +
        ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"" +
        "sway_outcome_event\":" +
        native + ",\"backend_id\":\"native-headless\"}}";
    return true;
  } catch (...) {
    failure = "sway_outcome_handler_exception";
    return false;
  }
}

} // namespace xar::ck3_12002
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_sway.hpp"
