#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_family_obligations_mailbox.hpp"
#include "xar_bridge/ck3_12003_call_ally_private_action.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <limits>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
bool HasField(std::string_view payload, std::string_view key) {
  return payload.find('"' + std::string(key) + '"') != std::string_view::npos;
}
bool CharacterId(std::string_view payload, std::string_view key,
                 std::int32_t &output, bool required) {
  output = -1;
  if (!HasField(payload, key)) return !required;
  std::uint64_t value = 0;
  if (!bridge::JsonUnsignedField(payload, key, value) || value == 0 ||
      value > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()))
    return false;
  output = static_cast<std::int32_t>(value);
  return true;
}
} // namespace

bool IsFamilyObligationsPrivateStep12002(std::string_view step) noexcept {
  return step == kFamilyObligationsPrivateStep12002 ||
      step == kCallAllySubmitPrivateStep12003;
}

bool ParseFamilyObligationsPrivateRequest12002(
    std::string_view payload, FamilyObligationsRequest12002 &out) noexcept {
  out = {};
  try {
    if (HasField(payload, "enumerate_current_allies") &&
        !bridge::JsonBooleanField(payload, "enumerate_current_allies", out.enumerate_current_allies)) return false;
    if (!CharacterId(payload, "subject_character_id", out.subject_character_id, false) ||
        !CharacterId(payload, "candidate_character_id", out.candidate_character_id, false) ||
        !CharacterId(payload, "ally_character_id", out.ally_character_id, false) ||
        !CharacterId(payload, "break_recipient_character_id", out.break_recipient_character_id, false) ||
        ((out.subject_character_id > 0) != (out.candidate_character_id > 0)) ||
        (out.subject_character_id > 0 && out.subject_character_id == out.candidate_character_id) ||
        (out.subject_character_id <= 0 && out.ally_character_id <= 0 && !out.enumerate_current_allies) ||
        (out.break_recipient_character_id > 0 && out.subject_character_id <= 0)) return false;
    if (HasField(payload, "request_matrilineal_option") &&
        !bridge::JsonBooleanField(payload, "request_matrilineal_option", out.request_matrilineal_option)) return false;
    if (out.request_matrilineal_option && out.subject_character_id <= 0) return false;
    if (HasField(payload, "expected_snapshot_revision") &&
        (!bridge::JsonUnsignedField(payload, "expected_snapshot_revision", out.expected_snapshot_revision) ||
         out.expected_snapshot_revision == 0)) return false;
    return true;
  } catch (...) { out = {}; return false; }
}

bool ExecuteFamilyObligationsMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteFamilyObligationsMailbox12002)) return true;
  auto &query = *static_cast<FamilyObligationsMailboxContext12002 *>(envelope->typed_context);
  try {
    auto &o = query.observation;
    const auto &r = o.request;
    o.frame = envelope->expected_snapshot;
    o.snapshot_revision = envelope->expected_snapshot_revision;
    std::string_view reason;
    if (query.call_ally_submission) {
      CoreSnapshotPrefix prefix{};
      prefix.clock = {o.frame.date_raw, o.frame.speed, o.frame.paused};
      prefix.local_player_id = o.frame.player_id;
      prefix.map_ready = o.frame.map_ready;
      prefix.has_played_character = o.frame.has_played_character;
      prefix.played_character_id = o.frame.played_character_id;
      prefix.played_character_alive = o.frame.played_character_alive;
      query.call_ally_result = family_obligations_alliance::SubmitCallAlly(
          query.alliance_bindings, prefix, query.call_ally_request,
          query.call_ally_receipt, &reason);
      query.failure = std::string(reason);
      query.completed = true;
      (void)FinishQueryMailbox(*envelope);
      return true;
    }
    if (r.subject_character_id > 0) {
      o.lineage_available = family_obligations_lineage::Read(query.lineage_bindings,
          r.subject_character_id, r.candidate_character_id, r.request_matrilineal_option,
          o.lineage, &reason);
      o.lineage_reason = std::string(reason);
    }
    if (r.ally_character_id > 0 || r.enumerate_current_allies) {
      CoreSnapshotPrefix prefix{};
      prefix.clock = {o.frame.date_raw, o.frame.speed, o.frame.paused};
      prefix.map_ready = o.frame.map_ready;
      prefix.has_played_character = o.frame.has_played_character;
      prefix.played_character_id = o.frame.played_character_id;
      prefix.played_character_alive = o.frame.played_character_alive;
      if (r.ally_character_id > 0) {
        o.alliance_available = family_obligations_alliance::Read(query.alliance_bindings,
            prefix, o.frame.played_character_id, r.ally_character_id, o.alliance, &reason);
        o.alliance_reason = std::string(reason);
      }
      if (r.enumerate_current_allies) {
        o.current_allies_available = family_obligations_alliance::ReadCurrentAllies(
            query.alliance_bindings, prefix, o.current_allies, &reason);
        o.current_allies_reason = std::string(reason);
      }
    }
    if (r.break_recipient_character_id > 0)
      o.break_terms = ReadFamilyObligationsBreakTermsV1(query.break_bindings,
          r.subject_character_id, r.break_recipient_character_id);
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
  } catch (...) {
    query.completed = false;
    query.failure = "family_obligations_native_capture_exception";
  }
  return true;
}

bool HandleFamilyObligationsPrivate12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsFamilyObligationsPrivateStep12002(step)) {
    failure = "family_obligations_step_unavailable"; return false;
  }
  const bool call_ally_submission = step == kCallAllySubmitPrivateStep12003;
  FamilyObligationsRequest12002 request{};
  CallAllyPrivateActionRequest12003 action_request{};
  if (call_ally_submission) {
    if (!ParseCallAllyPrivateActionRequest12003(payload, action_request)) {
      failure = "call_ally_request_invalid"; return false;
    }
    request.expected_snapshot_revision = action_request.expected_revision;
  } else if (!ParseFamilyObligationsPrivateRequest12002(payload, request)) {
    failure = "family_obligations_request_invalid"; return false;
  }
  if (xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 || !adapter.enabled() ||
      revision == 0 || (request.expected_snapshot_revision != 0 &&
                       request.expected_snapshot_revision != revision) ||
      !published.paused || !published.map_ready || !published.has_played_character ||
      !published.played_character_alive || published.played_character_id <= 0 ||
      (call_ally_submission && !game::IsCk3_12003Descriptor(adapter.descriptor()))) {
    failure = "family_obligations_current_frame_unavailable"; return false;
  }
  try {
    FamilyObligationsMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.observation.request = request;
    query.call_ally_submission = call_ally_submission;
    query.call_ally_request = action_request.native_request;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (request.subject_character_id > 0)
      query.lineage_bindings = family_obligations_lineage::BindImage(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (call_ally_submission || request.ally_character_id > 0 || request.enumerate_current_allies)
      query.alliance_bindings = family_obligations_alliance::BindImage(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (request.break_recipient_character_id > 0)
      query.break_bindings = BindFamilyObligationsBreakImageV1(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox, &ExecuteFamilyObligationsMailbox12002,
        &query.envelope, query.envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "family_obligations_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query.envelope.frame_stable || !query.completed) {
      failure = query.failure.empty() ? "family_obligations_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = call_ally_submission
        ? SerializeCallAllySubmissionResult12003(request_id, query)
        : SerializeFamilyObligationsResult12002(request_id, query.observation);
    return !serialized.empty();
  } catch (...) {
    serialized.clear(); failure = "family_obligations_mailbox_exception"; return false;
  }
}
} // namespace xar::ck3_12002
#endif
