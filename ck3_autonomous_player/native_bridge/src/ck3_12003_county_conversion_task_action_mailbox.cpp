#include "xar_bridge/ck3_12003_county_conversion_task_action_mailbox.hpp"

#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <memory>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
namespace action = ck3_12003::religion::county_conversion::action;
enum class Mode { submit, result };
struct Query {
  QueryMailboxEnvelope envelope;
  PlayerCountyConversionTaskActionMailboxState12003 *state = nullptr;
  Mode mode = Mode::submit;
  action::Request request;
  std::uint64_t public_revision = 0;
  std::string request_id;
  std::string submitted_request_id;
  std::string action_id;
  action::Submission submission;
  action::IndependentResult independent_result;
  std::string status;
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
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
const char *Status(action::SubmitStatus value) noexcept {
  switch (value) {
  case action::SubmitStatus::already_active_noop: return "already_active_noop";
  case action::SubmitStatus::queued_verification_pending: return "queued_verification_pending";
  default: return "not_submitted";
  }
}
action::Access Bind(const game::GameAdapter &adapter) noexcept {
  return action::BindCountyConversionTaskActionImage12003(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      adapter.descriptor().executable_sha256);
}
std::string Serialize(const Query &query, std::string_view step,
                      std::string_view request_id, const game::AdapterDescriptor &descriptor) {
  const auto &stamp = query.envelope.execution_stamp;
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"private_build\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\",\"game_version\":" + Quote(descriptor.game_version) +
      ",\"executable_sha256\":" + Quote(descriptor.executable_sha256) +
      ",\"read_only\":" + Bool(query.mode == Mode::result) +
      ",\"status\":" + Quote(query.status) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"public_revision\":" + std::to_string(query.public_revision) +
      ",\"date_raw\":" + std::to_string(stamp.date_raw) +
      ",\"capture_epoch\":" + std::to_string(stamp.pump_epoch) +
      ",\"submission\":" + action::SerializeCountyConversionTaskSubmission12003(query.submission);
  if (query.mode == Mode::result)
    out += ",\"independent_result\":" + action::SerializeCountyConversionTaskIndependentResult12003(query.independent_result);
  return game::RenderCrozierBuildIdentity(out + "}}", descriptor);
}
bool ReadRequest(std::string_view payload, std::uint64_t revision, Query &query) {
  std::uint64_t expected = 0, expected_snapshot = 0;
  if (!JsonUnsignedField(payload, "expected_revision", expected) || expected != revision ||
      !JsonUnsignedField(payload, "expected_snapshot_revision", expected_snapshot) || expected_snapshot != revision ||
      !JsonUnsignedField(payload, "expected_public_revision", query.public_revision) || query.public_revision == 0 ||
      !JsonStringField(payload, "action_id", query.action_id, 63) || query.action_id.empty()) return false;
  if (query.mode == Mode::result)
    return JsonStringField(payload, "submitted_request_id", query.submitted_request_id, 63) &&
        !query.submitted_request_id.empty();
  std::uint64_t task = 0, incumbent = 0, province = 0;
  const auto maximum = static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)());
  if (!JsonUnsignedField(payload, "expected_active_task_id", task) || task == 0 || task > maximum ||
      !JsonUnsignedField(payload, "expected_incumbent_character_id", incumbent) || incumbent == 0 || incumbent > maximum ||
      !JsonUnsignedField(payload, "province_id", province) || province == 0 || province > maximum ||
      !JsonBooleanField(payload, "replace_existing_task", query.request.replace_existing_task)) return false;
  query.request.expected_revision = query.public_revision;
  query.request.expected_active_task_id = static_cast<std::int32_t>(task);
  query.request.expected_incumbent_character_id = static_cast<std::int32_t>(incumbent);
  query.request.province_id = static_cast<std::int32_t>(province);
  query.request.action_id = query.action_id;
  return true;
}
} // namespace

bool IsPlayerCountyConversionTaskActionPrivateStep12003(std::string_view step) noexcept {
  return step == kPlayerCountyConversionTaskSubmitStep12003 ||
      step == kPlayerCountyConversionTaskResultStep12003;
}
bool ExecutePlayerCountyConversionTaskActionMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecutePlayerCountyConversionTaskActionMailbox12003)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  try {
    auto &state = *query.state;
    auto access = Bind(*envelope->game);
    access.county.application_main_thread_id = stamp.thread_id;
    access.county.clergy.application_main_thread_id = stamp.thread_id;
    if (query.mode == Mode::submit) {
      if (state.verification_pending)
        query.failure = "previous_county_conversion_task_submission_verification_pending";
      else {
        query.submission = action::SubmitCountyConversionTask12003(access,
            envelope->expected_snapshot, query.public_revision,
            envelope->expected_snapshot_revision, stamp.pump_epoch, query.request_id, query.request);
        state.submission = query.submission;
        state.has_submission = true;
        state.submission_sequence = envelope->ticket.sequence;
        state.verification_pending = query.submission.status == action::SubmitStatus::queued_verification_pending;
        query.status = Status(query.submission.status);
        query.complete = true;
      }
    } else if (!state.has_submission || state.submission.request_id != query.submitted_request_id ||
               state.submission.request.action_id != query.action_id ||
               envelope->ticket.sequence <= state.submission_sequence)
      query.failure = "independent_county_conversion_task_submission_unavailable";
    else {
      query.submission = state.submission;
      query.independent_result = action::ReadCountyConversionTaskResult12003(access,
          query.submission, stamp.pump_epoch);
      state.verification_pending = query.independent_result.verification_pending;
      query.status = query.independent_result.task_assignment_material_observed
          ? "task_assignment_material_observed" : state.verification_pending
          ? "verification_pending" : Status(query.submission.status);
      query.complete = true;
    }
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { query.failure = "native_county_conversion_task_action_executor_exception"; return true; }
}
bool HandlePlayerCountyConversionTaskActionPrivate12003(
    PlayerCountyConversionTaskActionMailboxState12003 &state, const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t native_revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerCountyConversionTaskActionPrivateStep12003(step) || !adapter.enabled() ||
      !game::IsCk3_12003Descriptor(adapter.descriptor()) || request_id.empty() || request_id.size() > 63 ||
      !published.paused || !published.map_ready || !published.has_played_character || !published.played_character_alive) {
    failure = "native_county_conversion_task_action_request_contract_invalid"; return false;
  }
  try {
    auto query = std::make_unique<Query>();
    query->state = &state;
    query->mode = step == kPlayerCountyConversionTaskSubmitStep12003 ? Mode::submit : Mode::result;
    query->request_id = request_id;
    if (!ReadRequest(payload, native_revision, *query)) {
      failure = "native_county_conversion_task_action_request_invalid"; return false;
    }
    query->envelope.game = &NativeAdapter12002(adapter);
    query->envelope.mailbox = &mailbox;
    query->envelope.expected_snapshot = published;
    query->envelope.expected_snapshot_revision = native_revision;
    query->envelope.typed_context = query.get();
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox, &ExecutePlayerCountyConversionTaskActionMailbox12003,
        &query->envelope, query->envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "native_county_conversion_task_action_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query->envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query->envelope.frame_stable || !query->complete) {
      failure = query->failure.empty() ? "native_county_conversion_task_action_frame_unavailable" : query->failure;
      return false;
    }
    serialized = Serialize(*query, step, request_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "native_county_conversion_task_action_router_exception"; return false; }
}
} // namespace xar::ck3_12002
