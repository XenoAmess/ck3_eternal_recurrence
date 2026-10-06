#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_confucian_challenger_graph_mailbox.hpp"
#include "xar_bridge/ck3_12003_readonly_revision.hpp"

#if defined(XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

namespace xar::ck3_12003 {
namespace {
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id != -1;
}
} // namespace

bool IsConfucianChallengerGraphPrivateStep12003(std::string_view step) noexcept {
  return step == kConfucianChallengerGraphPrivateStep12003;
}

bool ParseConfucianChallengerGraphRevision12003(std::string_view payload,
                                        std::uint64_t &revision) noexcept {
  challenger_graph::Request request;
  const bool valid = challenger_graph::ParseRequest(payload, request);
  revision = valid ? request.expected_snapshot_revision : 0;
  return valid;
}

bool ExecuteConfucianChallengerGraphMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<ConfucianChallengerGraphMailboxContext12003 *>(envelope->typed_context);
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteConfucianChallengerGraphMailbox12003)) {
      query.failure = "confucian_challenger_graph_published_frame_changed";
      return true;
    }
    (void)challenger_graph::Read(
        query.bindings, envelope->expected_snapshot, stamp.pump_epoch,
        std::span<const std::uint32_t>(query.request.faith_full_ids.data(), query.request.faith_count),
        query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.played_character_id != frame.played_character_id ||
                          out.date_raw != frame.date_raw)) {
      out = {};
      out.unavailable_reason = "native_frame_changed";
      out.capture_epoch = stamp.pump_epoch;
      out.requested_faith_full_ids.assign(query.request.faith_full_ids.begin(),
          query.request.faith_full_ids.begin() + query.request.faith_count);
    }
    if (!out.available) {
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "confucian_challenger_graph_native_capture_exception";
    return false;
  }
}

std::string SerializeConfucianChallengerGraphResult12003(
    const ConfucianChallengerGraphMailboxContext12003 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kConfucianChallengerGraphPrivateStep12003) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.3\"," +
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kConfucianChallengerGraphDomainKey12003) +
      ",\"backend_id\":" + Quote(kConfucianChallengerGraphBackend12003) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"confucian_challenger_graph\":" + challenger_graph::Serialize(query.observation) + "}}";
}

bool RunConfucianChallengerGraphMailbox12003(ConfucianChallengerGraphMailboxContext12003 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "confucian_challenger_graph_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecuteConfucianChallengerGraphMailbox12003, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "confucian_challenger_graph_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "confucian_challenger_graph_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeConfucianChallengerGraphResult12003(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "confucian_challenger_graph_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "confucian_challenger_graph_mailbox_exception"; return false;
  }
}

bool HandleConfucianChallengerGraphPrivate12003(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsConfucianChallengerGraphPrivateStep12003(step)) {
    failure = "confucian_challenger_graph_step_unavailable"; return false;
  }
  challenger_graph::Request request;
  if (!challenger_graph::ParseRequest(payload, request)) {
    failure = "confucian_challenger_graph_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != ck3_12003::kGameVersion ||
      adapter.descriptor().executable_sha256 != ck3_12003::kExecutableSha256 ||
      !ValidFrame(published, revision) || (request.expected_snapshot_revision != revision)) {
    failure = "confucian_challenger_graph_current_frame_unavailable"; return false;
  }
  try {
    ConfucianChallengerGraphMailboxContext12003 query{};
    query.request = request;
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.bindings = challenger_graph::BindImage(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    return RunConfucianChallengerGraphMailbox12003(query, request_id, serialized, failure);
  } catch (...) { failure = "confucian_challenger_graph_handler_exception"; return false; }
}
} // namespace xar::ck3_12003
#endif
