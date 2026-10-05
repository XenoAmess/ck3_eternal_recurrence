#include "xar_bridge/ck3_12003_maa_create_private_mailbox.hpp"

#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <memory>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
struct Query {
  QueryMailboxEnvelope envelope;
  const game::GameAdapter *adapter = nullptr;
  game::NativeMaaRegularPersonalCreateRequestV1 request;
  game::NativeMaaRegularPersonalCreateSubmissionV1 submission;
  std::uint64_t public_revision = 0;
  std::string request_id;
  std::string action_id;
  std::string failure;
  bool complete = false;
};

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) {
      out += "\\u00";
      out += hex[ch >> 4]; out += hex[ch & 0x0f];
    } else out += static_cast<char>(ch);
  }
  return out + '"';
}
std::string NullableBool(const std::optional<bool> &value) {
  return value.has_value() ? (*value ? "true" : "false") : "null";
}
bool ReadRequest(std::string_view payload, std::uint64_t revision, Query &query) {
  std::uint64_t expected = 0, expected_snapshot = 0, index = 0;
  if (!JsonUnsignedField(payload, "expected_revision", expected) || expected != revision ||
      !JsonUnsignedField(payload, "expected_snapshot_revision", expected_snapshot) || expected_snapshot != revision ||
      !JsonUnsignedField(payload, "expected_public_revision", query.public_revision) || query.public_revision == 0 ||
      !JsonUnsignedField(payload, "type_index", index) ||
      index > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()) ||
      !JsonStringField(payload, "action_id", query.action_id, 63) || query.action_id.empty()) return false;
  query.request.type_index = static_cast<std::int32_t>(index);
  return true;
}
} // namespace

bool IsRegularMaaCreatePrivateStep12003(std::string_view step) noexcept {
  return step == kRegularMaaCreatePrivateStep12003;
}
std::string SerializeNativeMaaCreateCommandResult12003(
    const game::NativeMaaRegularPersonalCreateSubmissionV1 &value,
    std::uint64_t native_revision, std::uint64_t public_revision,
    std::int32_t date_raw, std::uint64_t capture_epoch,
    std::string_view request_id, std::string_view action_id,
    const game::AdapterDescriptor &descriptor) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(kRegularMaaCreatePrivateStep12003) +
      ",\"accepted\":true,\"private_build\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\",\"game_version\":" + Quote(descriptor.game_version) +
      ",\"executable_sha256\":" + Quote(descriptor.executable_sha256) +
      ",\"read_only\":false,\"status\":" + Quote(value.status) +
      ",\"snapshot_revision\":" + std::to_string(native_revision) +
      ",\"public_revision\":" + std::to_string(public_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"capture_epoch\":" + std::to_string(capture_epoch) +
      ",\"action_id\":" + Quote(action_id) +
      ",\"submission\":{\"schema_version\":" + std::to_string(value.schema_version) +
      ",\"status\":" + Quote(value.status) + ",\"reason\":" + Quote(value.reason) +
      ",\"command_class\":" + Quote(value.command_class) +
      ",\"owner_character_id\":" + std::to_string(value.owner_character_id) +
      ",\"type_index\":" + std::to_string(value.type_index) +
      ",\"native_can_create\":" + NullableBool(value.native_can_create) +
      ",\"native_submit_accepted\":" + NullableBool(value.native_submit_accepted) +
      ",\"command_pointer_consumed\":" + NullableBool(value.command_pointer_consumed) + "}}}";
  return game::RenderCrozierBuildIdentity(out, descriptor);
}
bool ExecuteRegularMaaCreateMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteRegularMaaCreateMailbox12003)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  try {
    query.submission = game::SubmitNativeMaaRegularPersonalCreate(*query.adapter, query.request);
    query.complete = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { query.failure = "native_regular_maa_create_executor_exception"; return true; }
}
bool HandleRegularMaaCreatePrivate12003(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsRegularMaaCreatePrivateStep12003(step) || !adapter.enabled() ||
      !game::IsCk3_12003Descriptor(adapter.descriptor()) || request_id.empty() || request_id.size() > 63 ||
      !published.paused || !published.map_ready || !published.has_played_character || !published.played_character_alive) {
    failure = "native_regular_maa_create_request_contract_invalid"; return false;
  }
  try {
    auto query = std::make_unique<Query>();
    query->adapter = &NativeAdapter12002(adapter);
    query->request.owner_character_id = published.played_character_id;
    query->request_id = request_id;
    if (!ReadRequest(payload, native_revision, *query)) {
      failure = "native_regular_maa_create_request_invalid"; return false;
    }
    query->envelope.game = &NativeAdapter12002(adapter);
    query->envelope.mailbox = &mailbox;
    query->envelope.expected_snapshot = published;
    query->envelope.expected_snapshot_revision = native_revision;
    query->envelope.typed_context = query.get();
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox, &ExecuteRegularMaaCreateMailbox12003,
        &query->envelope, query->envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "native_regular_maa_create_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query->envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query->envelope.frame_stable || !query->complete) {
      failure = query->failure.empty() ? "native_regular_maa_create_frame_unavailable" : query->failure;
      return false;
    }
    const auto &stamp = query->envelope.execution_stamp;
    serialized = SerializeNativeMaaCreateCommandResult12003(query->submission,
        native_revision, query->public_revision, stamp.date_raw, stamp.pump_epoch,
        request_id, query->action_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "native_regular_maa_create_router_exception"; return false; }
}
} // namespace xar::ck3_12002
