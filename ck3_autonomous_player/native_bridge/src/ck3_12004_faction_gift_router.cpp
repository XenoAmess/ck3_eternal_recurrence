#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_faction_gift_router.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <algorithm>
#include <limits>
#include <windows.h>

namespace xar::ck3_12004 {
using ck3_12002::QueryMailboxEnvelope;
using ck3_12002::CaptureQuerySnapshot;
using ck3_12002::IsQueryOwningThread;
using ck3_12002::EnterQueryMailbox;
using ck3_12002::FinishQueryMailbox;
using ck3_12002::CampaignRootAccessV1;
namespace {
enum class Mode { preview, submit, receipt, cold };
struct Query {
  QueryMailboxEnvelope envelope{};
  CampaignRootFactionBindings12004 campaign{};
  PlayerFactionAlertsNativeEnvironmentV1 factions{};
  FactionGiftBindings12004 gift{};
  const FactionGiftPrivateFixtureBindings12004 *fixture = nullptr;
  FactionGiftPrivateState12004 *state = nullptr;
  Mode mode = Mode::preview;
  game::CampaignRootContextV1 root{};
  game::PlayerFactionAlertsV1 alerts{};
  game::FactionGiftMitigationObservationV1 observation{};
  game::FactionGiftMitigationRequestV1 request{};
  game::FactionGiftMitigationAckV1 ack{};
  game::FactionGiftMitigationReceiptV1 receipt{};
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  bool complete = false;
  bool receipt_complete = false;
  std::string status;
  std::string failure;
};

template <typename Frame> bool CaptureFrame(void *opaque, Frame &output) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  output = {};
  if (!CaptureQuerySnapshot(envelope, snapshot)) return false;
  output.snapshot_revision = envelope->expected_snapshot_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool ReadMemory(void *, const void *address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && output != nullptr && ReadProcessMemory(
      GetCurrentProcess(), address, output, size, &read) != 0 && read == size;
}

PlayerFactionAlertsAccessV1 MakeFactionAccess(Query &query) noexcept {
  return {&query.envelope, &CaptureFrame<game::PlayerFactionAlertsFrameV1>,
      &IsQueryOwningThread, &ReadMemory, nullptr};
}

bool CaptureObservation(void *opaque,
    game::FactionGiftMitigationObservationV1 &output) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  auto access = MakeFactionAccess(query);
  // The input revision is the already-qualified paused public frame. The
  // pump epoch remains a separate owner-thread proof, not a second clock.
  const bool captured = CaptureFactionGiftObservation12004(query.gift, query.factions, access,
      query.root, query.envelope.expected_snapshot_revision,
      query.source_faction_id, query.recipient_character_id,
      query.mode == Mode::preview || query.mode == Mode::submit, output);
  if (captured) {
    try { query.observation = output; }
    catch (...) { return false; }
  }
  return captured;
}

// Preserve the existing targeting-vector / leader-before-member order. A
// leader repeated in its own member vector is one recipient, not a retry.
template <typename Visitor>
bool VisitFactionGiftCandidates(const game::CampaignRootContextV1 &root,
    const game::PlayerFactionAlertsV1 &alerts, Visitor visit) {
  if (root.status != game::CampaignRootContextStatusV1::available ||
      !root.readiness.direct_landed_vassals_ready || !root.player_character_id ||
      alerts.status != game::PlayerFactionAlertsStatusV1::available ||
      !alerts.readiness.targeting_rows_ready || !alerts.readiness.same_frame_ready ||
      alerts.snapshot_revision != root.snapshot_revision || alerts.date_raw != root.date_raw ||
      alerts.player_character_id != root.player_character_id) return false;
  const auto eligible = [&](std::int32_t id) {
    return id > 0 && id != *root.player_character_id && std::find(
        root.direct_landed_vassal_character_ids.begin(), root.direct_landed_vassal_character_ids.end(),
        id) != root.direct_landed_vassal_character_ids.end();
  };
  bool visited = false;
  for (const auto &row : alerts.targeting_factions) {
    if (row.faction_id <= 0 || row.target_character_id != *root.player_character_id || row.faction_at_war) continue;
    const auto offer = [&](std::int32_t id) {
      if (!eligible(id)) return false;
      visited = true;
      return visit(static_cast<std::uint32_t>(row.faction_id), static_cast<std::uint32_t>(id));
    };
    if (row.leader_character_id && offer(*row.leader_character_id)) return true;
    for (auto id : row.character_member_ids) {
      if (row.leader_character_id && id == *row.leader_character_id) continue;
      if (offer(id)) return true;
    }
  }
  return visited;
}

bool ObservedGiftCandidateShouldReturn(const game::FactionGiftMitigationObservationV1 &o) {
  const auto &p = o.gift_preview;
  // Keep incomplete source and malformed positive-quote interpretation with
  // the existing consumer; neither is a known recipient denial to skip.
  if (!o.source_faction_metrics_available ||
      (p.interaction_legal && p.auto_accept &&
       (p.gold_cost_raw <= 0 || p.gold_scale != 100000 || p.opinion_delta <= 0))) return true;
  const bool member = o.source_faction_leader_character_id == o.recipient_character_id ||
      std::find(o.source_faction_member_character_ids.begin(),
          o.source_faction_member_character_ids.end(), o.recipient_character_id) !=
          o.source_faction_member_character_ids.end();
  // These are the existing Python chooser's observed recipient/preview terms.
  // Reserve/budget comparison remains with that chooser; this query never sends.
  return o.source_faction_present && o.source_faction_targeting_player &&
      o.source_faction_target_character_id == o.player_character_id &&
      !o.source_faction_at_war && member && o.recipient_alive && o.recipient_is_ai &&
      o.recipient_is_direct_landed_vassal && !o.gift_opinion_present &&
      p.available && p.interaction_legal && p.auto_accept;
}

bool Validate(void *opaque, std::uint32_t actor, std::uint32_t recipient,
    std::string_view key, bool &valid, std::string &reason) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  return ValidateFactionGift12004(query.gift, actor, recipient, key,
      query.request.expected_definition_stable_hash, valid, reason);
}

bool Claim(void *opaque, std::string_view key) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  try {
    return query.state != nullptr &&
        query.state->claimed_idempotency_keys.emplace(key).second;
  } catch (...) { return false; }
}

bool Submit(void *opaque, std::uint32_t actor, std::uint32_t recipient,
    std::uint64_t hash) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  return SubmitFactionGift12004(query.gift, actor, recipient,
      query.request.expected_definition_key, hash);
}

std::string Quote(std::string_view input) {
  std::string output = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char c : input) {
    if (c == '"' || c == '\\') { output += '\\'; output += static_cast<char>(c); }
    else if (c < 0x20) {
      output += "\\u00"; output += hex[c >> 4]; output += hex[c & 15];
    } else output += static_cast<char>(c);
  }
  return output + '"';
}

std::string Bool(bool value) { return value ? "true" : "false"; }

std::string SerializeObservation(const game::FactionGiftMitigationObservationV1 &o) {
  std::string json = "{\"available\":" + Bool(o.available);
#define XAR_GIFT_BOOLEAN(field) json += ",\"" #field "\":" + Bool(o.field)
#define XAR_GIFT_NUMBER(field) json += ",\"" #field "\":" + std::to_string(o.field)
  XAR_GIFT_BOOLEAN(paused);
  XAR_GIFT_NUMBER(snapshot_revision); XAR_GIFT_NUMBER(native_snapshot_revision);
  XAR_GIFT_NUMBER(observed_date_raw);
  json += ",\"date_raw\":" + std::to_string(o.observed_date_raw);
  XAR_GIFT_BOOLEAN(player_resources_query_complete); XAR_GIFT_NUMBER(player_character_id);
  XAR_GIFT_NUMBER(player_gold_raw); XAR_GIFT_NUMBER(player_gold_scale);
  XAR_GIFT_BOOLEAN(source_faction_requery_complete); XAR_GIFT_NUMBER(queried_source_faction_id);
  XAR_GIFT_BOOLEAN(source_faction_present); XAR_GIFT_NUMBER(source_faction_target_character_id);
  XAR_GIFT_BOOLEAN(source_faction_targeting_player); XAR_GIFT_BOOLEAN(source_faction_at_war);
  XAR_GIFT_BOOLEAN(source_faction_metrics_available); XAR_GIFT_NUMBER(source_faction_power_raw);
  XAR_GIFT_NUMBER(source_faction_discontent_raw); XAR_GIFT_NUMBER(source_faction_metric_scale);
  XAR_GIFT_BOOLEAN(recipient_identity_resolved); XAR_GIFT_NUMBER(recipient_character_id);
  XAR_GIFT_BOOLEAN(recipient_alive); XAR_GIFT_BOOLEAN(recipient_is_ai);
  XAR_GIFT_BOOLEAN(recipient_is_direct_landed_vassal); XAR_GIFT_BOOLEAN(recipient_opinion_query_complete);
  XAR_GIFT_NUMBER(recipient_opinion_of_player); XAR_GIFT_BOOLEAN(gift_opinion_present);
#undef XAR_GIFT_BOOLEAN
#undef XAR_GIFT_NUMBER
  json += ",\"gift_opinion_modifier_value\":" +
      (o.gift_opinion_modifier_value ? std::to_string(*o.gift_opinion_modifier_value) : "null");
  json += ",\"source_faction_leader_character_id\":" +
      (o.source_faction_leader_character_id ? std::to_string(*o.source_faction_leader_character_id) : "null");
  json += ",\"source_faction_member_character_ids\":[";
  for (std::size_t i = 0; i < o.source_faction_member_character_ids.size(); ++i) {
    if (i != 0) json += ',';
    json += std::to_string(o.source_faction_member_character_ids[i]);
  }
  const auto &p = o.gift_preview;
  json += "],\"gift_preview\":{\"available\":" + Bool(p.available) +
      ",\"definition_key\":" + Quote(p.definition_key) +
      ",\"definition_stable_hash\":" + std::to_string(p.definition_stable_hash) +
      ",\"interaction_legal\":" + Bool(p.interaction_legal) +
      ",\"auto_accept\":" + Bool(p.auto_accept) +
      ",\"gold_cost_raw\":" + std::to_string(p.gold_cost_raw) +
      ",\"gold_scale\":" + std::to_string(p.gold_scale) +
      ",\"opinion_delta\":" + std::to_string(p.opinion_delta) + "}}";
  return json;
}

std::string SerializeRows(const Query &query) {
  if (query.alerts.status != game::PlayerFactionAlertsStatusV1::available ||
      !query.alerts.readiness.targeting_rows_ready) return "null";
  std::string json = "{\"terminal\":" + Quote(query.alerts.targeting_factions.empty()
      ? "known_empty" : "ready") + ",\"snapshot_revision\":" +
      std::to_string(query.alerts.snapshot_revision) + ",\"date_raw\":" +
      std::to_string(query.envelope.expected_snapshot.date_raw) +
      ",\"player_character_id\":" + std::to_string(query.envelope.expected_snapshot.played_character_id) +
      ",\"faction_count\":" + std::to_string(query.alerts.targeting_factions.size()) +
      ",\"factions\":[";
  for (std::size_t i = 0; i < query.alerts.targeting_factions.size(); ++i) {
    if (i != 0) json += ',';
    const auto &row = query.alerts.targeting_factions[i];
    json += "{\"faction_id\":" + std::to_string(row.faction_id) +
        ",\"target_character_id\":" + std::to_string(row.target_character_id) +
        ",\"leader_character_id\":" + (row.leader_character_id
            ? std::to_string(*row.leader_character_id) : "null") +
        ",\"character_member_ids\":[";
    for (std::size_t member = 0; member < row.character_member_ids.size(); ++member) {
      if (member != 0) json += ',';
      json += std::to_string(row.character_member_ids[member]);
    }
    json += "]}";
  }
  return json + "]}";
}

std::string SerializeResult(const Query &query, std::string_view step,
    std::string_view request_id) {
  const bool preview = query.observation.available && query.observation.gift_preview.available;
  std::string native = "{\"schema_version\":1,\"private\":true,\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"backend_id\":" + Quote(kFactionGiftBackendIdV1) +
      ",\"contract_stage\":" + Quote(kFactionGiftContractStageV1) +
      ",\"completion\":" + Quote(preview ? "preview_ready" : "unavailable") +
      ",\"failure_flags\":0,\"frame_failure_stage\":\"none\","
      "\"direct_source_failure\":\"none\",\"typed_reds\":[],\"source_faction_id\":" +
      std::to_string(query.source_faction_id) + ",\"recipient_character_id\":" +
      std::to_string(query.recipient_character_id) + ",\"observation\":" +
      SerializeObservation(query.observation) + ",\"direct_targeting_rows\":" + SerializeRows(query) +
      ",\"receipt_pending\":" + Bool(query.ack.verification_pending) +
      ",\"ack\":" + (query.mode == Mode::submit ? SerializeFactionGiftAck12004(query.ack) : "null") +
      ",\"preflight\":null,\"executor_invocations\":1}";
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"private_build\":true,\"advertised\":false,\"status\":" +
      Quote(query.status) + ",\"native\":" + native + ",\"receipt\":" +
      (query.receipt_complete ? ck3_12002::RenderQueryBuildIdentity(
          ck3_11906::SerializeFactionGiftMitigationReceiptV1(query.receipt)) : "null") + "}}";
}

bool ReadFrameRequest(std::string_view payload, const game::Snapshot &frame,
    std::uint64_t revision) noexcept {
  std::uint64_t requested_revision = 0, date = 0, actor = 0;
  return bridge::JsonUnsignedField(payload, "expected_revision", requested_revision) &&
      bridge::JsonUnsignedField(payload, "expected_date_raw", date) &&
      bridge::JsonUnsignedField(payload, "expected_player_character_id", actor) &&
      revision != 0 && requested_revision == revision && frame.date_raw >= 0 &&
      date == static_cast<std::uint64_t>(frame.date_raw) && actor != 0 &&
      actor == static_cast<std::uint64_t>(frame.played_character_id) && frame.paused &&
      frame.map_ready && frame.has_played_character && frame.played_character_alive;
}

bool ReadIds(std::string_view payload, std::uint32_t &source, std::uint32_t &recipient) noexcept {
  std::uint64_t source_raw = 0, recipient_raw = 0;
  if (!bridge::JsonUnsignedField(payload, "source_faction_id", source_raw) ||
      !bridge::JsonUnsignedField(payload, "recipient_character_id", recipient_raw) ||
      source_raw == 0 || recipient_raw == 0 ||
      source_raw > (std::numeric_limits<std::uint32_t>::max)() ||
      recipient_raw > (std::numeric_limits<std::uint32_t>::max)()) return false;
  source = static_cast<std::uint32_t>(source_raw);
  recipient = static_cast<std::uint32_t>(recipient_raw);
  return true;
}

bool ReadAction(std::string_view payload, std::string_view request_id, Query &query,
    const game::Snapshot &frame, std::uint64_t revision) {
  if (query.state == nullptr || query.state->action_may_have_submitted ||
      query.state->pending_ack || !query.state->last_query || request_id.empty() ||
      !ReadIds(payload, query.source_faction_id, query.recipient_character_id)) return false;
  std::string role;
  std::uint64_t hash = 0, cost = 0, delta = 0, reserve = 0, native = 0;
  if (!bridge::JsonStringField(payload, "membership_role", role, 32) ||
      !bridge::JsonUnsignedField(payload, "definition_stable_hash", hash) ||
      !bridge::JsonUnsignedField(payload, "gold_cost_raw", cost) ||
      !bridge::JsonUnsignedField(payload, "opinion_delta", delta) ||
      !bridge::JsonUnsignedField(payload, "minimum_gold_reserve_raw", reserve) ||
      !bridge::JsonUnsignedField(payload, "expected_native_revision", native) ||
      hash == 0 || cost == 0 || delta == 0 || native == 0 ||
      cost > static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)()) ||
      reserve > static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)()) ||
      delta > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()) ||
      (role != "leader" && role != "character_member")) return false;
  const auto &before = *query.state->last_query;
  const auto &preview = before.gift_preview;
  const bool role_matches = role == "leader"
      ? before.source_faction_leader_character_id == query.recipient_character_id
      : std::find(before.source_faction_member_character_ids.begin(),
          before.source_faction_member_character_ids.end(), query.recipient_character_id) !=
          before.source_faction_member_character_ids.end();
  if (!before.available || before.snapshot_revision != revision ||
      before.observed_date_raw != frame.date_raw ||
      before.player_character_id != static_cast<std::uint32_t>(frame.played_character_id) ||
      before.native_snapshot_revision != native || before.queried_source_faction_id != query.source_faction_id ||
      before.recipient_character_id != query.recipient_character_id || !role_matches ||
      !before.source_faction_metrics_available || !before.recipient_identity_resolved ||
      !preview.available || !preview.interaction_legal || !preview.auto_accept ||
      preview.definition_stable_hash != hash || preview.gold_cost_raw != static_cast<std::int64_t>(cost) ||
      preview.opinion_delta != static_cast<std::int32_t>(delta) ||
      before.player_gold_raw < static_cast<std::int64_t>(cost) ||
      before.player_gold_raw - static_cast<std::int64_t>(cost) < static_cast<std::int64_t>(reserve)) return false;
  query.request = {std::string(request_id), std::string(request_id), revision, native,
      frame.date_raw, static_cast<std::uint32_t>(frame.played_character_id),
      query.source_faction_id, query.recipient_character_id,
      role == "leader" ? game::FactionGiftMembershipRoleV1::leader : game::FactionGiftMembershipRoleV1::character_member,
      preview.definition_key, hash, static_cast<std::int64_t>(cost), preview.gold_scale,
      static_cast<std::int32_t>(delta), static_cast<std::int64_t>(reserve), preview.gold_scale};
  return true;
}
} // namespace

bool SelectFactionGiftPrivateCandidate12004(const game::CampaignRootContextV1 &root,
    const game::PlayerFactionAlertsV1 &alerts, std::uint32_t &source,
    std::uint32_t &recipient) noexcept {
  source = recipient = 0;
  VisitFactionGiftCandidates(root, alerts, [&](std::uint32_t faction, std::uint32_t person) {
    source = faction; recipient = person; return true;
  });
  return source != 0;
}

bool ExecuteFactionGiftPrivateMailbox12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteFactionGiftPrivateMailbox12004)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  try {
    CampaignRootAccessV1 root_access{envelope, &CaptureFrame<game::CampaignRootFrameV1>,
        &IsQueryOwningThread, &ReadMemory, nullptr};
    bool root_ready = false;
    if (query.fixture != nullptr && query.fixture->read_campaign != nullptr) {
      game::CampaignRootFrameV1 frame{};
      root_ready = CaptureFrame(envelope, frame) && query.fixture->read_campaign(
          query.fixture->context, frame, query.root);
    } else root_ready = ck3_12004::ReadCampaignRootFaction12004(query.campaign, root_access,
        {envelope->expected_snapshot_revision}, query.root);
    if (!root_ready ||
        !query.root.readiness.direct_landed_vassals_ready) {
      query.failure = "private_faction_fresh_campaign_root_unavailable";
    } else if (query.mode == Mode::preview) {
      auto access = MakeFactionAccess(query);
      bool alerts_ready = false;
      if (query.fixture != nullptr && query.fixture->read_alerts != nullptr) {
        game::PlayerFactionAlertsFrameV1 frame{};
        alerts_ready = CaptureFrame(envelope, frame) && query.fixture->read_alerts(
            query.fixture->context, frame, query.alerts);
      } else alerts_ready = ck3_12004::ReadPlayerFactionAlerts12004(query.factions, access,
          {envelope->expected_snapshot_revision}, query.alerts) == game::ReadPlayerFactionAlertsResultV1::available;
      if (!alerts_ready ||
          !query.alerts.readiness.targeting_rows_ready || !query.alerts.readiness.same_frame_ready) {
        query.failure = "private_faction_native_targeting_rows_unavailable";
      } else if (query.alerts.targeting_factions.empty()) {
        query.status = "known_empty"; query.complete = true;
      } else {
        bool selected = false;
        const bool visited = VisitFactionGiftCandidates(query.root, query.alerts,
            [&](std::uint32_t faction, std::uint32_t person) {
          query.source_faction_id = faction; query.recipient_character_id = person;
          if (!CaptureObservation(&query, query.observation)) {
            query.failure = "private_faction_native_observation_unavailable";
            return true;
          }
          selected = ObservedGiftCandidateShouldReturn(query.observation);
          return selected;
        });
        if (query.failure.empty()) {
          // A known native/recipient denial may continue to another observed
          // member. An incomplete capture above remains the original RED.
          query.status = !visited ? "no_eligible_direct_vassal"
              : selected ? "preview_ready" : "no_legal_candidate";
          query.complete = true;
        }
      }
    } else if (query.mode == Mode::submit) {
      ck3_11906::FactionGiftMitigationNativeEnvironmentV1 environment{
          query.gift.module_base, true, true, query.fixture != nullptr};
      ck3_11906::FactionGiftMitigationActionAccessV1 access{&query,
          &CaptureObservation, &Validate, &Claim, &Submit};
      ExecuteFactionGiftAction12004(environment, access, query.request, query.ack);
      query.status = query.ack.verification_pending ? "submitted_verification_pending" : "rejected_before_submit";
      query.complete = true;
    } else if (!CaptureObservation(&query, query.observation)) {
      query.failure = "private_faction_independent_post_requery_unavailable";
    } else {
      query.complete = true;
      if (query.mode == Mode::cold) query.status = "independent_read_complete";
      else {
        ck3_11906::VerifyFactionGiftMitigationReceiptV1(query.ack, query.observation, query.receipt);
        query.receipt_complete = true;
        query.status = query.receipt.postcondition_verified ? "applied" : "postcondition_red";
      }
    }
  } catch (...) { query.failure = "private_faction_executor_exception"; }
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool HandleFactionGiftPrivate12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, FactionGiftPrivateState12004 &state,
    std::string &serialized, std::string &failure,
    const FactionGiftPrivateFixtureBindings12004 *fixture_bindings) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    Query query{};
    query.state = &state;
    if (fixture_bindings != nullptr && !mailbox.offline_fixture) {
      failure = "private_faction_fixture_mailbox_required"; return false;
    }
    query.fixture = fixture_bindings;
    if (step == kFactionGiftPrivateQueryStepV1) query.mode = Mode::preview;
    else if (step == kFactionGiftPrivateSubmitStepV1) query.mode = Mode::submit;
    else if (step == kFactionGiftPrivateReceiptStepV1) query.mode = Mode::receipt;
    else if (step == kFactionGiftPrivateColdRecoveryStepV1) query.mode = Mode::cold;
    else { failure = "private_faction_step_unsupported"; return false; }
    if (!adapter.enabled() || !xar::game::IsCk3_12004Descriptor(adapter.descriptor()) ||
        xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
        !ReadFrameRequest(payload, published, revision)) {
      failure = "private_faction_frame_invalid"; return false;
    }
    if (query.mode == Mode::submit && !ReadAction(payload, request_id, query, published, revision)) {
      failure = "private_faction_action_or_pending_binding_invalid"; return false;
    }
    if (query.mode == Mode::cold && !ReadIds(payload, query.source_faction_id, query.recipient_character_id)) {
      failure = "private_faction_cold_frame_or_identity_invalid"; return false;
    }
    if (query.mode == Mode::receipt) {
      if (!state.pending_ack || !state.action_may_have_submitted ||
          revision <= state.pending_ack->pre_snapshot_revision ||
          published.date_raw != state.pending_ack->pre_observed_date_raw ||
          published.played_character_id != static_cast<std::int32_t>(state.pending_ack->player_character_id)) {
        failure = "private_faction_pending_receipt_invalid"; return false;
      }
      query.ack = *state.pending_ack;
      query.source_faction_id = query.ack.source_faction_id;
      query.recipient_character_id = query.ack.recipient_character_id;
    }
    query.envelope.game = &adapter;
    query.envelope.snapshot_comparison = fixture_bindings
        ? ck3_12002::QuerySnapshotComparison12002::full_snapshot
        : ck3_12002::QuerySnapshotComparison12002::core_frame;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.campaign = fixture_bindings != nullptr ? fixture_bindings->campaign
        : ck3_12004::BindCampaignRootFactionImage12004(base, kExecutableSha256);
    query.factions = fixture_bindings != nullptr ? fixture_bindings->factions
        : ck3_12004::BindPlayerFactionAlertsImage12004(base, kExecutableSha256);
    query.gift = fixture_bindings != nullptr ? fixture_bindings->gift
        : BindFactionGiftImage12004(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (!query.gift.enabled || TrySubmitMainThreadQueryV1(mailbox,
        &ExecuteFactionGiftPrivateMailbox12004, &query.envelope,
        query.envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "private_faction_application_main_unavailable"; return false;
    }
    if (query.mode == Mode::submit) state.action_may_have_submitted = true;
    auto wait = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.envelope.frame_stable || !query.complete) {
      // A request cancelled before execution can safely leave the existing
      // process-local state. An executed/unknown submit remains pending.
      if (query.mode == Mode::submit && !query.envelope.entered)
        state.action_may_have_submitted = false;
      failure = query.failure.empty() ? "private_faction_mailbox_or_frame_unavailable" : query.failure;
      return false;
    }
    if (query.mode == Mode::preview) {
      state.last_query.reset();
      if (query.observation.available) state.last_query = query.observation;
    } else if (query.mode == Mode::submit) {
      state.last_query.reset();
      if (query.ack.verification_pending) state.pending_ack = query.ack;
      else state.action_may_have_submitted = false;
    }
    serialized = game::Render12004BuildIdentity(SerializeResult(query, step, request_id), adapter.descriptor());
    return true;
  } catch (...) { failure = "private_faction_router_exception"; return false; }
}
} // namespace xar::ck3_12004
