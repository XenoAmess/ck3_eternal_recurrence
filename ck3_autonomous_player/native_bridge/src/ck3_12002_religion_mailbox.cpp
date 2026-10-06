#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_context_addons.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>
#include <atomic>
#include <utility>

namespace xar::ck3_12002 {
namespace {
std::atomic<const char *> g_religion_capture_stage{"not_entered"};
void SetCaptureStage(const char *stage) noexcept {
  g_religion_capture_stage.store(stage, std::memory_order_relaxed);
}
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
bool HasField(std::string_view payload, std::string_view name) {
  return payload.find('"' + std::string(name) + '"') != std::string_view::npos;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}
void *ResolveReligionCharacter(const PlayerReligionMailboxContext12002 &query,
    std::int32_t id) noexcept {
  return query.envelope.game &&
      game::IsCk3_12004Descriptor(query.envelope.game->descriptor())
      ? ck3_12004::ResolveCoreCharacter(query.bindings.core, id)
      : ResolveCoreCharacter(query.bindings.core, id);
}
} // namespace

bool IsPlayerReligionPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionPrivateStep12002;
}

bool ParsePlayerReligionRevision12002(std::string_view payload,
                                     std::uint64_t &revision) noexcept {
  revision = 0;
  try {
    std::uint64_t alias = 0;
    const bool canonical_present = HasField(payload, "expected_snapshot_revision");
    const bool alias_present = HasField(payload, "expected_revision");
    if (canonical_present && (!bridge::JsonUnsignedField(payload,
        "expected_snapshot_revision", revision) || revision == 0)) return false;
    if (alias_present && (!bridge::JsonUnsignedField(payload,
        "expected_revision", alias) || alias == 0)) return false;
    if (canonical_present && alias_present && revision != alias) return false;
    if (!canonical_present) revision = alias;
    return true;
  } catch (...) { revision = 0; return false; }
}

bool ExecutePlayerReligionMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionMailboxContext12002 *>(envelope->typed_context);
  try {
    SetCaptureStage("enter_paused_frame");
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionMailbox12002)) {
      query.failure = "player_religion_published_frame_changed";
      return true;
    }
    SetCaptureStage("base_religion_context");
    if (game::IsCk3_12004Descriptor(envelope->game->descriptor()))
      (void)ck3_12004::religion::ReadPlayedReligionContext12004(
          query.bindings, stamp.pump_epoch, query.observation);
    else
      (void)religion::ReadPlayedReligionContext12002(
          query.bindings, stamp.pump_epoch, query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.played_character_id != frame.played_character_id ||
                          out.date_raw != frame.date_raw)) {
      out = {};
      out.failure = religion::Failure::state_changed;
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      // The owner envelope still identifies the frame whose native read failed.
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    }
    // Resolve the fixed confession definition against this current Context
    // and actual player. A legal false permission remains an observed value.
    SetCaptureStage("confession_rite_permission");
    (void)ck3_12003::religion::confession_permission::ReadPlayerConfessionRitePermission12003(
        query.confession_permission_bindings, query.bindings,
        out.available ? ResolveReligionCharacter(query, out.played_character_id) : nullptr,
        out, query.confession_rite_permission);
    // Read the independent milestone component on the same owner callback.
    // Its availability does not alter the existing Context or conversion inputs.
    SetCaptureStage("spiritual_fulfillment_progress");
    (void)religion::fulfillment_progress12003::ReadPlayerSpiritualFulfillmentProgress12003(
        query.progress_bindings,
        out.available ? ResolveReligionCharacter(query, out.played_character_id) : nullptr,
        out, query.progress);
    // Reuse the exact progress binding for an independent stable type key.
    SetCaptureStage("spiritual_fulfillment_type");
    (void)ck3_12003::religion::fulfillment_type::ReadPlayerSpiritualFulfillmentType12003(
        query.progress_bindings,
        out.available ? ResolveReligionCharacter(query, out.played_character_id) : nullptr,
        out, query.spiritual_fulfillment_type);
    // The fixed decision read is independent of Faith Context and loan numerics.
    SetCaptureStage("mystical_communion_decision_terms");
    (void)ck3_12003::religion::mystical_communion::ReadPlayerMysticalCommunionDecisionTerms12003(
        query.mystical_communion_bindings,
        ResolveReligionCharacter(query, static_cast<std::int32_t>(frame.played_character_id)),
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.mystical_communion_terms);
    // Read fixed pilgrimage CanPlan and its tooltip without opening a planner.
    // This independent component does not change the existing Context.
    SetCaptureStage("pilgrimage_activity_type_terms");
    (void)ck3_12003::religion::pilgrimage::ReadPlayerPilgrimageActivityTypeTerms12003(
        query.pilgrimage_bindings,
        ResolveReligionCharacter(query, static_cast<std::int32_t>(frame.played_character_id)),
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.pilgrimage_terms);
    // Discover actual Faith candidates and quote owned local configurations.
    // Route defaults are a separate observation; neither is a live planner.
    auto *pilgrimage_actor = out.available
        ? ResolveReligionCharacter(query, out.played_character_id) : nullptr;
    SetCaptureStage("pilgrimage_headless_activity_terms");
    (void)ck3_12003::religion::pilgrimage_activity_terms::ReadPlayerPilgrimageActivityTerms12003(
        query.pilgrimage_activity_bindings, pilgrimage_actor, out,
        query.pilgrimage_activity_terms);
    query.pilgrimage_candidate_routes.clear();
    for (const auto &candidate : query.pilgrimage_activity_terms.candidates) {
      ck3_12003::religion::pilgrimage_route::Terms route;
      SetCaptureStage("pilgrimage_candidate_route");
      (void)ck3_12003::religion::pilgrimage_route::ReadPlayerPilgrimageCandidateRoute12003(
          query.pilgrimage_route_bindings, pilgrimage_actor, out.played_character_id,
          out.date_raw, out.capture_epoch, candidate.province_id, route);
      query.pilgrimage_candidate_routes.push_back(std::move(route));
    }
    // Independent fixed confession and church-income components use the
    // same resolved current player/frame; neither gates existing Context.
    SetCaptureStage("confession_decision_terms");
    (void)ck3_12003::religion::confession::ReadPlayerConfessionDecisionTerms12003(
        query.confession_bindings,
        ResolveReligionCharacter(query, static_cast<std::int32_t>(frame.played_character_id)),
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.confession_terms);
    SetCaptureStage("church_income_profile");
    (void)ck3_12003::religion::church_income::ReadPlayerChurchIncomeProfile12003(
        query.church_income_bindings,
        ResolveReligionCharacter(query, static_cast<std::int32_t>(frame.played_character_id)),
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.church_income_terms);
    // The selected native church tax rule is a separate optional observation.
    SetCaptureStage("church_tax_inputs");
    (void)ck3_12003::religion::church_tax_inputs::ReadPlayerChurchTaxInputs12003(
        query.church_tax_bindings,
        ResolveReligionCharacter(query, static_cast<std::int32_t>(frame.played_character_id)),
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.church_tax_inputs);
    // Three independent read-only religion inputs share the actual owner frame.
    auto *religion_actor = ResolveReligionCharacter(query,
        static_cast<std::int32_t>(frame.played_character_id));
    SetCaptureStage("piety_devotion_profile");
    (void)religion::devotion_profile12003::ReadPlayerDevotionProfile12003(
        query.devotion_bindings, religion_actor, out, query.devotion_profile);
    SetCaptureStage("rite_virtue_sin_profile");
    (void)religion::rite_virtue_sin_profile12003::ReadPlayerRiteVirtueSinProfile12003(
        query.rite_virtue_sin_bindings, religion_actor, out, query.rite_virtue_sin_profile);
    SetCaptureStage("vow_of_poverty_terms");
    (void)ck3_12003::religion::vow_of_poverty_terms12003::ReadVowOfPovertyTerms12003(
        query.vow_of_poverty_bindings, religion_actor,
        static_cast<std::int32_t>(frame.played_character_id),
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.vow_of_poverty_terms);
    query.completed = true;
    SetCaptureStage("finish_paused_frame");
    if (FinishQueryMailbox(*envelope)) SetCaptureStage("completed");
    return true;
  } catch (...) {
    query.failure = "player_religion_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionResult12002(
    const PlayerReligionMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  std::string pilgrimage_routes = "[";
  for (const auto &route : query.pilgrimage_candidate_routes) {
    if (pilgrimage_routes.size() > 1) pilgrimage_routes += ',';
    pilgrimage_routes +=
        ck3_12003::religion::pilgrimage_route::SerializePlayerPilgrimageCandidateRoute12003(route);
  }
  pilgrimage_routes += ']';
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_context\":" + religion::SerializePlayedReligionContext12002(query.observation) +
      ",\"player_spiritual_fulfillment_progress\":" +
      religion::fulfillment_progress12003::SerializeSpiritualFulfillmentProgress12003(query.progress) +
      ",\"player_mystical_communion_decision_terms\":" +
      ck3_12003::religion::mystical_communion::SerializePlayerMysticalCommunionDecisionTerms12003(
          query.mystical_communion_terms) +
      ",\"player_pilgrimage_activity_type_terms\":" +
      ck3_12003::religion::pilgrimage::SerializePlayerPilgrimageActivityTypeTerms12003(
          query.pilgrimage_terms) +
      ",\"player_pilgrimage_headless_activity_terms\":" +
      ck3_12003::religion::pilgrimage_activity_terms::SerializePlayerPilgrimageActivityTerms12003(
          query.pilgrimage_activity_terms) +
      ",\"player_pilgrimage_candidate_routes\":" + pilgrimage_routes +
      ",\"player_confession_decision_terms\":" +
      ck3_12003::religion::confession::SerializePlayerConfessionDecisionTerms12003(
          query.confession_terms) +
      ",\"player_confession_rite_permission\":" +
      ck3_12003::religion::confession_permission::SerializePlayerConfessionRitePermission12003(
          query.confession_rite_permission) +
      ",\"player_church_income_profile\":" +
      ck3_12003::religion::church_income::SerializePlayerChurchIncomeProfile12003(
          query.church_income_terms) +
      ",\"player_spiritual_fulfillment_type\":" +
      ck3_12003::religion::fulfillment_type::SerializePlayerSpiritualFulfillmentType12003(
          query.spiritual_fulfillment_type) +
      ",\"player_church_tax_inputs\":" +
      ck3_12003::religion::church_tax_inputs::SerializePlayerChurchTaxInputs12003(
          query.church_tax_inputs) +
      ",\"player_piety_devotion_profile\":" +
      religion::devotion_profile12003::SerializePlayerDevotionProfile12003(query.devotion_profile) +
      ",\"player_rite_virtue_sin_profile\":" +
      religion::rite_virtue_sin_profile12003::SerializePlayerRiteVirtueSinProfile12003(query.rite_virtue_sin_profile) +
      ",\"player_vow_of_poverty_terms\":" +
      ck3_12003::religion::vow_of_poverty_terms12003::SerializeVowOfPovertyTerms12003(query.vow_of_poverty_terms) + "}}";
}

bool RunPlayerReligionMailbox12002(PlayerReligionMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    SetCaptureStage("not_entered");
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto mailbox_failure_flags =
        envelope.mailbox->failure_flags.load(std::memory_order_acquire);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty()
          ? std::string("player_religion_paused_capture_unavailable:stage=") +
                g_religion_capture_stage.load(std::memory_order_relaxed) + ";wait=" + std::to_string(static_cast<int>(wait)) +
                ";reclaim=" + std::to_string(static_cast<int>(reclaim)) +
                ";entered=" + std::to_string(envelope.entered) +
                ";completed=" + std::to_string(query.completed) +
                ";frame_stable=" + std::to_string(envelope.frame_stable) +
                ";mailbox_failure_flags=" + std::to_string(mailbox_failure_flags)
          : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionResult12002(query, request_id);
    if (game::IsCk3_12004Descriptor(envelope.game->descriptor()))
      serialized = game::Render12004BuildIdentity(
          std::move(serialized), envelope.game->descriptor());
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionPrivateStep12002(step)) {
    failure = "player_religion_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerReligionRevision12002(payload, expected)) {
    failure = "player_religion_request_invalid"; return false;
  }
  const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
  if (!adapter.enabled() || (!actual4 &&
      (game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
       game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256)) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionMailboxContext12002 query{};
    query.envelope.game = actual4 ? &adapter : &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto image_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (actual4) {
      const auto sha = adapter.descriptor().executable_sha256;
      query.bindings = ck3_12004::religion::BindReligionContextImage12004(image_base, sha);
      const auto addons = ck3_12004::religion::BindReligionContextAddonsImage12004(image_base, sha);
      query.progress_bindings = addons.progress_bindings;
      query.mystical_communion_bindings = addons.mystical_communion_bindings;
      query.pilgrimage_bindings = addons.pilgrimage_bindings;
      query.pilgrimage_activity_bindings = addons.pilgrimage_activity_bindings;
      query.pilgrimage_route_bindings = addons.pilgrimage_route_bindings;
      query.confession_bindings = addons.confession_bindings;
      query.confession_permission_bindings = addons.confession_permission_bindings;
      query.church_income_bindings = addons.church_income_bindings;
      query.church_tax_bindings = addons.church_tax_bindings;
      query.devotion_bindings = addons.devotion_bindings;
      query.rite_virtue_sin_bindings = addons.rite_virtue_sin_bindings;
      query.vow_of_poverty_bindings = addons.vow_of_poverty_bindings;
    } else {
      query.bindings = religion::BindReligionContextImage12002(
          image_base,
          xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      query.progress_bindings =
          religion::fulfillment_progress12003::BindSpiritualFulfillmentProgressImage12003(
              image_base, adapter.descriptor());
      query.mystical_communion_bindings =
          ck3_12003::religion::mystical_communion::BindPlayerMysticalCommunionDecisionTermsImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.pilgrimage_bindings =
          ck3_12003::religion::pilgrimage::BindPlayerPilgrimageActivityTypeTermsImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.pilgrimage_activity_bindings =
          ck3_12003::religion::pilgrimage_activity_terms::BindPlayerPilgrimageActivityTermsImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.pilgrimage_route_bindings =
          ck3_12003::religion::pilgrimage_route::BindPlayerPilgrimageCandidateRouteImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.confession_bindings =
          ck3_12003::religion::confession::BindPlayerConfessionDecisionTermsImage12003(
              image_base, adapter.descriptor().executable_sha256);
      // Reuse reviewed .3 admission for the existing definition/status factory.
      // No draft reader or window operation is invoked by this query.
      query.confession_permission_bindings =
          religion_reform::BindCurrentDraftTenetSources12002(
              image_base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      query.church_income_bindings =
          ck3_12003::religion::church_income::BindPlayerChurchIncomeProfileImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.church_tax_bindings =
          ck3_12003::religion::church_tax_inputs::BindPlayerChurchTaxInputsImage12003(
              image_base, adapter.descriptor().executable_sha256);
      query.devotion_bindings =
          religion::devotion_profile12003::BindPlayerDevotionProfileImage12003(image_base, adapter.descriptor());
      query.rite_virtue_sin_bindings =
          religion::rite_virtue_sin_profile12003::BindPlayerRiteVirtueSinProfileImage12003(image_base, adapter.descriptor());
      query.vow_of_poverty_bindings =
          ck3_12003::religion::vow_of_poverty_terms12003::BindVowOfPovertyTermsImage12003(
              image_base, adapter.descriptor().executable_sha256);
    }
    return RunPlayerReligionMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
