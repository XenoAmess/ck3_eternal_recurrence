#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_epidemic_recovery_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <limits>

namespace xar::ck3_12002 {
namespace {
void JsonString(std::string &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out.push_back('"');
  for (const unsigned char c : text) {
    if (c == '"' || c == '\\') { out.push_back('\\'); out.push_back(static_cast<char>(c)); }
    else if (c < 0x20U) {
      out += "\\u00"; out.push_back(hex[c >> 4U]); out.push_back(hex[c & 0xfU]);
    } else out.push_back(static_cast<char>(c));
  }
  out.push_back('"');
}
} // namespace

bool IsEpidemicRecoveryPrivate12002(std::string_view step) noexcept {
  std::int32_t requested_title = 0;
  return ck3_11906::ParsePlayerEpidemicRecoveryStepV1(step, requested_title);
}

bool ExecutePlayerEpidemicRecoveryMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &q = *static_cast<EpidemicRecoveryMailboxContext12002 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerEpidemicRecoveryMailbox12002)) {
    q.failure = "epidemic recovery published frame changed";
    q.completed = true;
    return true;
  }
  try {
    q.result = epidemic_recovery::ReadEpidemicRecovery12002(
        q.source, envelope->expected_snapshot_revision,
        static_cast<std::int32_t>(envelope->expected_snapshot.date_raw),
        static_cast<std::int32_t>(envelope->expected_snapshot.played_character_id),
        q.requested_title_id);
    q.completed = true;
    if (!FinishQueryMailbox(*envelope))
      q.failure = "epidemic recovery paused frame changed during query";
    return true;
  } catch (...) {
    q.failure = "epidemic recovery owner callback exception";
    q.completed = true;
    return false;
  }
}

std::string SerializeEpidemicRecoveryPacket12002(
    const EpidemicRecoveryMailboxContext12002 &q,
    std::string_view step, std::string_view request_id) {
  if (!q.completed || !q.failure.empty() || !q.envelope.frame_stable ||
      !q.envelope.ticket.sequence || !q.envelope.execution_stamp.pump_epoch)
    return {};
  const auto native = ck3_11906::SerializePlayerEpidemicRecoveryV1(q.result);
  if (native.empty()) return {};
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  JsonString(out, request_id);
  out += ",\"ok\":true,\"result\":{\"step\":";
  JsonString(out, step);
  out += ",\"accepted\":true,\"status\":\"";
  out += q.result.available ? "available" : "unavailable";
  out += "\",\"query_sequence\":" + std::to_string(q.envelope.ticket.sequence);
  out += ",\"observation_revision\":" + std::to_string(q.envelope.execution_stamp.pump_epoch);
  out += ",\"snapshot_revision\":" + std::to_string(q.envelope.expected_snapshot_revision);
  out += ",\"player_epidemic_recovery\":" + native;
  out += ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\"}}";
  return out;
}

bool HandleEpidemicRecoveryPrivateBound12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    const epidemic_recovery::Bindings &source,
    std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    EpidemicRecoveryMailboxContext12002 q{};
    std::uint64_t expected_revision = 0;
    if (!ParsePlayerEpidemicRecoveryStepV1(step, q.requested_title_id) ||
        !bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
        !revision || revision != expected_revision || !adapter.enabled() ||
        (adapter.descriptor().adapter_id != "ck3-1.20.0.2-msvc-x64" && !xar::game::IsCk3_12003Descriptor(adapter.descriptor())) ||
        xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
        !published.paused || !published.map_ready || !published.has_played_character ||
        !published.played_character_alive || published.played_character_id <= 0 ||
        published.played_character_id > std::numeric_limits<std::int32_t>::max() ||
        published.date_raw < std::numeric_limits<std::int32_t>::min() ||
        published.date_raw > std::numeric_limits<std::int32_t>::max() ||
        (!q.requested_title_id && (!published.has_active_event || published.active_event_instance_id <= 0))) {
      failure = "epidemic recovery request or paused player frame invalid";
      return false;
    }
    q.envelope.game = &NativeAdapter12002(adapter);
    q.envelope.mailbox = &mailbox;
    q.envelope.expected_snapshot = published;
    q.envelope.expected_snapshot_revision = revision;
    q.envelope.typed_context = &q;
    q.source = source;
    if (mailbox.permitted_executor_epidemic_recovery12002 !=
        &ExecutePlayerEpidemicRecoveryMailbox12002) {
      failure = "epidemic recovery named executor unavailable";
      return false;
    }
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecutePlayerEpidemicRecoveryMailbox12002,
            &q.envelope, q.envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "epidemic recovery named executor unavailable";
      return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 8'000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      waited = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 2'000);
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, q.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed) {
      failure = "epidemic recovery owner query did not complete";
      return false;
    }
    serialized = SerializeEpidemicRecoveryPacket12002(q, step, request_id);
    if (serialized.empty()) {
      failure = q.failure.empty() ? "epidemic recovery native packet unavailable" : q.failure;
      return false;
    }
    return true;
  } catch (...) {
    serialized.clear(); failure = "epidemic recovery handler exception";
    return false;
  }
}

bool HandleEpidemicRecoveryPrivate12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  const auto source = epidemic_recovery::BindImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
  return HandleEpidemicRecoveryPrivateBound12002(adapter, mailbox, published,
      revision, step, payload, request_id, source, serialized, failure);
}
} // namespace xar::ck3_12002
