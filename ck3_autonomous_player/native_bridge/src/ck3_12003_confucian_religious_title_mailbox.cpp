#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_confucian_religious_title_mailbox.hpp"
#include "xar_bridge/ck3_12003_readonly_revision.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"

#if defined(XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1)
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

bool IsConfucianReligiousTitlePrivateStep12003(std::string_view step) noexcept {
  return step == kConfucianReligiousTitlePrivateStep12003;
}

bool ParseConfucianReligiousTitleRevision12003(std::string_view payload,
                                        std::uint64_t &revision) noexcept {
  return readonly_query::ParseUniqueTopLevelRevision(payload, revision);
}

bool ExecuteConfucianReligiousTitleMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<ConfucianReligiousTitleMailboxContext12003 *>(envelope->typed_context);
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteConfucianReligiousTitleMailbox12003)) {
      query.failure = "confucian_religious_title_published_frame_changed";
      return true;
    }
    (void)religious_title::Read(
        query.bindings, envelope->expected_snapshot, stamp.pump_epoch, query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.played_character_id != frame.played_character_id ||
                          out.date_raw != frame.date_raw)) {
      out = {};
      out.actual4 = query.bindings.properties.actual4;
      out.unavailable_reason = "native_frame_changed";
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "confucian_religious_title_native_capture_exception";
    return false;
  }
}

std::string SerializeConfucianReligiousTitleResult12003(
    const ConfucianReligiousTitleMailboxContext12003 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  const bool actual4 = query.bindings.properties.actual4;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kConfucianReligiousTitlePrivateStep12003) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":" +
      Quote(actual4 ? ck3_12004::kGameVersion : kGameVersion) + ',' +
      "\"executable_sha256\":" + Quote(actual4 ? ck3_12004::kExecutableSha256 : kExecutableSha256) +
      ",\"domain_key\":" + Quote(kConfucianReligiousTitleDomainKey12003) +
      ",\"backend_id\":" + Quote(actual4
          ? "ck3-1.20.0.4-native-confucian-religious-title-v1"
          : kConfucianReligiousTitleBackend12003) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"confucian_religious_title\":" + religious_title::Serialize(query.observation) + "}}";
}

bool RunConfucianReligiousTitleMailbox12003(ConfucianReligiousTitleMailboxContext12003 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "confucian_religious_title_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecuteConfucianReligiousTitleMailbox12003, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "confucian_religious_title_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "confucian_religious_title_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeConfucianReligiousTitleResult12003(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "confucian_religious_title_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "confucian_religious_title_mailbox_exception"; return false;
  }
}

bool HandleConfucianReligiousTitlePrivate12003(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsConfucianReligiousTitlePrivateStep12003(step)) {
    failure = "confucian_religious_title_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParseConfucianReligiousTitleRevision12003(payload, expected)) {
    failure = "confucian_religious_title_request_invalid"; return false;
  }
  const auto &descriptor = adapter.descriptor();
  const bool exact3 = descriptor.game_version == kGameVersion &&
      descriptor.executable_sha256 == kExecutableSha256;
  const bool exact4 = descriptor.game_version == ck3_12004::kGameVersion &&
      descriptor.executable_sha256 == ck3_12004::kExecutableSha256;
  if (!adapter.enabled() || (!exact3 && !exact4) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "confucian_religious_title_current_frame_unavailable"; return false;
  }
  try {
    ConfucianReligiousTitleMailboxContext12003 query{};
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.bindings = religious_title::BindImage(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    return RunConfucianReligiousTitleMailbox12003(query, request_id, serialized, failure);
  } catch (...) { failure = "confucian_religious_title_handler_exception"; return false; }
}
} // namespace xar::ck3_12003
#endif
