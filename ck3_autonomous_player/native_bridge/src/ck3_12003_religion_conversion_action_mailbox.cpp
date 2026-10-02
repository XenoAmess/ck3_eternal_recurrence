#include "xar_bridge/ck3_12003_religion_conversion_action_mailbox.hpp"

#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <memory>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
namespace action = religion_conversion::action12003;
enum class Mode { submit, result };
struct Query {
  QueryMailboxEnvelope envelope;
  PlayerReligionConversionActionMailboxState12003 *state = nullptr;
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
std::string Optional(const std::optional<bool> &value) {
  return value.has_value() ? Bool(*value) : "null";
}
std::string Optional(const std::optional<std::int64_t> &value) {
  return value.has_value() ? std::to_string(*value) : "null";
}
const char *Status(action::SubmitStatus value) noexcept {
  switch (value) {
  case action::SubmitStatus::already_target_noop: return "already_target_noop";
  case action::SubmitStatus::queued_verification_pending: return "queued_verification_pending";
  default: return "not_submitted";
  }
}
action::Access Bind(const game::GameAdapter &adapter) noexcept {
  const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto sha = game::ReviewedCrozierAbiSha256(adapter.descriptor());
  action::Access access;
  access.terms = religion_conversion::terms::BindReligionConversionTermsImage12002(base, sha);
  access.reasons = religion_conversion::reasons::BindReligionConversionReasonsImage12002(base, sha);
  access.outcome = religion_conversion::outcome::BindConversionOutcomeImage12002(base, sha);
  access.commands = BindCommandImage(base, sha);
  return access;
}
std::string SerializeSubmission(const action::Submission &value) {
  return "{\"status\":" + Quote(Status(value.status)) +
      ",\"failure\":" + Quote(value.failure) +
      ",\"request_id\":" + Quote(value.request_id) +
      ",\"request\":{\"expected_revision\":" + std::to_string(value.request.expected_revision) +
      ",\"target_rite_id\":" + std::to_string(value.request.target_rite_id) +
      ",\"max_piety_cost_raw\":" + std::to_string(value.request.max_piety_cost_raw) +
      ",\"action_id\":" + Quote(value.request.action_id) + "}" +
      ",\"native_revision\":" + std::to_string(value.native_revision) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"command_target_rite_id\":" + std::to_string(value.command_target_rite_id) +
      ",\"command_pay_piety\":" + Bool(value.command_pay_piety) +
      ",\"command_channel\":" + std::to_string(value.command_channel) +
      ",\"native_submit_copy_called\":" + Bool(value.native_submit_copy_called) +
      ",\"paid_terms\":" + religion_conversion::terms::SerializeReligionConversionTerms12002(value.paid_terms) +
      ",\"native_reasons\":" + religion_conversion::reasons::SerializeReligionConversionReasons12002(value.native_reasons) +
      ",\"before\":" + religion_conversion::outcome::SerializeConversionOutcome12002(value.before) + "}";
}
std::string SerializeIndependent(const action::IndependentResult &value) {
  return "{\"request_id\":" + Quote(value.request_id) +
      ",\"action_id\":" + Quote(value.action_id) +
      ",\"submit_status\":" + Quote(Status(value.submit_status)) +
      ",\"verification_pending\":" + Bool(value.verification_pending) +
      ",\"after_actor_available\":" + Bool(value.after_actor_available) +
      ",\"after\":" + religion_conversion::outcome::SerializeConversionOutcome12002(value.after) +
      ",\"target_already_reached_before\":" + Optional(value.target_already_reached_before) +
      ",\"actual_rite_changed\":" + Optional(value.actual_rite_changed) +
      ",\"actual_target_reached_after\":" + Optional(value.actual_target_reached_after) +
      ",\"actual_target_faith_reached_after\":" + Optional(value.actual_target_faith_reached_after) +
      ",\"request_associated_conversion_material_observed\":" + Bool(value.request_associated_conversion_material_observed) +
      ",\"quoted_base_piety_cost_raw\":" + Optional(value.quoted_base_piety_cost_raw) +
      ",\"piety_net_delta_raw\":" + Optional(value.piety_net_delta_raw) +
      ",\"gold_net_delta_raw\":" + Optional(value.gold_net_delta_raw) +
      ",\"prestige_net_delta_raw\":" + Optional(value.prestige_net_delta_raw) +
      ",\"base_payment_observed\":" + Bool(value.base_payment_observed) +
      ",\"native_base_piety_charge_raw\":" + Optional(value.native_base_piety_charge_raw) +
      ",\"native_execute_observed\":" + Bool(value.native_execute_observed) +
      ",\"conversion_causality_inferred\":" + Bool(value.conversion_causality_inferred) + "}";
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
      ",\"submission\":" + SerializeSubmission(query.submission);
  if (query.mode == Mode::result)
    out += ",\"independent_result\":" + SerializeIndependent(query.independent_result);
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
  std::uint64_t target = 0, maximum = 0;
  if (!JsonUnsignedField(payload, "target_rite_id", target) || target >= religion::kAbsentReference ||
      !JsonUnsignedField(payload, "max_piety_cost_raw", maximum) ||
      maximum > static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)())) return false;
  query.request.expected_revision = query.public_revision;
  query.request.target_rite_id = static_cast<std::uint32_t>(target);
  query.request.max_piety_cost_raw = static_cast<std::int64_t>(maximum);
  query.request.action_id = query.action_id;
  return true;
}
} // namespace

bool IsPlayerReligionConversionActionPrivateStep12003(std::string_view step) noexcept {
  return step == kPlayerReligionConversionSubmitStep12003 ||
      step == kPlayerReligionConversionResultStep12003;
}
bool ExecutePlayerReligionConversionActionMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionConversionActionMailbox12003)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  try {
    auto &state = *query.state;
    const auto access = Bind(*envelope->game);
    if (query.mode == Mode::submit) {
      if (state.verification_pending)
        query.failure = "previous_religion_conversion_submission_verification_pending";
      else {
        query.submission = action::SubmitPaidPlayerConversion12003(access,
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
      query.failure = "independent_religion_conversion_submission_unavailable";
    else {
      query.submission = state.submission;
      query.independent_result = action::ReadPlayerConversionResult12003(access,
          query.submission, stamp.pump_epoch);
      state.verification_pending = query.independent_result.verification_pending;
      query.status = query.independent_result.request_associated_conversion_material_observed
          ? "conversion_material_observed" : state.verification_pending
          ? "verification_pending" : Status(query.submission.status);
      query.complete = true;
    }
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { query.failure = "native_religion_conversion_action_executor_exception"; return true; }
}
bool HandlePlayerReligionConversionActionPrivate12003(
    PlayerReligionConversionActionMailboxState12003 &state, const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t native_revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionConversionActionPrivateStep12003(step) || !adapter.enabled() ||
      !game::IsCk3_12003Descriptor(adapter.descriptor()) || request_id.empty() || request_id.size() > 63 ||
      !published.paused || !published.map_ready || !published.has_played_character || !published.played_character_alive) {
    failure = "native_religion_conversion_action_request_contract_invalid"; return false;
  }
  try {
    auto query = std::make_unique<Query>();
    query->state = &state;
    query->mode = step == kPlayerReligionConversionSubmitStep12003 ? Mode::submit : Mode::result;
    query->request_id = request_id;
    if (!ReadRequest(payload, native_revision, *query)) {
      failure = "native_religion_conversion_action_request_invalid"; return false;
    }
    query->envelope.game = &NativeAdapter12002(adapter);
    query->envelope.mailbox = &mailbox;
    query->envelope.expected_snapshot = published;
    query->envelope.expected_snapshot_revision = native_revision;
    query->envelope.typed_context = query.get();
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox, &ExecutePlayerReligionConversionActionMailbox12003,
        &query->envelope, query->envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "native_religion_conversion_action_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query->envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query->envelope.frame_stable || !query->complete) {
      failure = query->failure.empty() ? "native_religion_conversion_action_frame_unavailable" : query->failure;
      return false;
    }
    serialized = Serialize(*query, step, request_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "native_religion_conversion_action_router_exception"; return false; }
}
} // namespace xar::ck3_12002
