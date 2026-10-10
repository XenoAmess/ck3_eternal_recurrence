#include "xar_bridge/ck3_12004_lifestyle_transport.hpp"
#include "xar_bridge/lifestyle_perk_predicate_inputs_12004_serializer.hpp"
#include "xar_bridge/lifestyle_perk_trigger_frontier_12004_serializer.hpp"
#include "xar_bridge/protocol.hpp"
#include <algorithm>
#include <limits>
#include <utility>
namespace xar::ck3_12004::lifestyle {
namespace {
bool SameCoreFrame(const game::Snapshot &observed,
                   const game::Snapshot &expected) noexcept {
  // Same eight fields as QuerySnapshotComparison12002::core_frame.
  return observed.date_raw == expected.date_raw &&
      observed.speed == expected.speed &&
      observed.paused == expected.paused &&
      observed.player_id == expected.player_id &&
      observed.map_ready == expected.map_ready &&
      observed.has_played_character == expected.has_played_character &&
      observed.played_character_id == expected.played_character_id &&
      observed.played_character_alive == expected.played_character_alive;
}
void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') { output += '\\'; output += static_cast<char>(c); }
    else if (c < 32) { output += "\\u00"; output += hex[c >> 4]; output += hex[c & 15]; }
    else output += static_cast<char>(c);
  }
  output += '"';
}
template<std::size_t N> std::string_view LifestyleFixed(const std::array<char,N> &value) {
  return {value.data(), static_cast<std::size_t>(
      std::find(value.begin(), value.end(), '\0') - value.begin())};
}
std::string CommandResultFrame(std::string_view request_id, std::string_view step,
                              bool ok, std::string_view status) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ok ? ",\"ok\":true,\"result\":{\"step\":" : ",\"ok\":false,\"error\":";
  if (ok) { AppendJsonString(result, step); result += ",\"accepted\":true,\"status\":"; }
  AppendJsonString(result, status);
  result += ok ? "}}" : "}";
  return result;
}
} // namespace
bool AcceptsPlayerLifestyleStep12004(std::string_view step) noexcept {
  using namespace ck3_11906;
  return step == kPlayerLifestyleFormalPrivateQueryStepV1 ||
      step == kPlayerLifestyleFormalPrivateCurrentStateStepV1 ||
      step == kPlayerLifestyleFormalPrivateStockFocusStepV1 ||
      step == kPlayerLifestyleFormalPrivateProfessionalWorkforceStepV1 ||
      step == kPlayerLifestyleFormalPrivateDiplomacyStepV1 ||
      step == kPlayerLifestyleFormalPrivateMartialStepV1 ||
      step == kPlayerLifestyleFormalPrivateSubmitStepV1 ||
      step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1 ||
      step == kPlayerLifestyleFormalPrivateReceiptStepV1;
}
bool PlayerLifestyleNeedsPostSubmitSnapshot12004(
    const PlayerLifestyleTransport12004 &transport, std::string_view request_id) noexcept {
  return transport.pending_ack.has_value() &&
      ck3_11906::PlayerLifestyleAckNeedsPostSubmitSnapshotV1(
          *transport.pending_ack, request_id);
}
std::string RenderPlayerLifestyle12004(
    std::string_view request_id, std::string_view step,
    const xar::ck3_11906::PlayerLifestyleFormalWireContextV1 &context,
    const game::AdapterDescriptor &descriptor) {
  if (!context.completed) {
    return game::Render12004BuildIdentity(CommandResultFrame(
        request_id, step, false,
        context.failure.empty() ? "private_lifestyle_executor_unavailable"
                                : context.failure), descriptor);
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,";
  result += "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"private_build\":true,\"advertised\":false,";
  if (context.mode == xar::ck3_11906::
                          PlayerLifestyleFormalWireModeV1::query_state_only) {
    result += "\"status\":\"available\",\"episode_run_id\":";
    AppendJsonString(result, context.episode_run_id);
    result += ",\"snapshot\":";
    result += SerializePlayerLifestyleSnapshot12004V1(*context.snapshot);
  } else if (context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::
                                     query_focus_only ||
             context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::
                                     query_martial_focus_only) {
    const auto &focus = context.stock_focus_result;
    result += "\"status\":";
    AppendJsonString(
        result, xar::ck3_11906::StockFocusLegalityStatusKeyV1(focus.status));
    result += ",\"read_only\":true,\"policy_scoped\":true,";
    result += "\"episode_run_id\":";
    AppendJsonString(result, context.episode_run_id);
    result += ",\"snapshot_id\":";
    AppendJsonString(result, context.snapshot_id);
    result += ",\"target_key\":";
    AppendJsonString(
        result,
        context.mode == xar::ck3_11906::
                            PlayerLifestyleFormalWireModeV1::query_martial_focus_only
            ? xar::ck3_11906::kMartialAuthorityFocusV1
            : xar::ck3_11906::kStockFocusLegalityTargetV1);
    if (focus.status == xar::ck3_11906::
                            StockFocusLegalityStatusV1::observed_native_legal ||
        focus.status == xar::ck3_11906::
                            StockFocusLegalityStatusV1::observed_native_illegal) {
      result += ",\"native_legal\":";
      result += focus.status == xar::ck3_11906::
                                    StockFocusLegalityStatusV1::
                                        observed_native_legal
                    ? "true" : "false";
      result += ",\"scanned_database_rows\":" +
          std::to_string(focus.scanned_database_rows);
      result += ",\"target_lifestyle_key\":";
      AppendJsonString(
          result,
          xar::ck3_11906::PlayerLifestyleWindowStableKeyViewV1(
              focus.lifestyle_key));
      result += ",\"target_lifestyle_progress\":{\"presence\":";
      if (focus.target_progress.available) {
        result += "\"present\",\"source\":\"exact_native_getters\"";
        result += ",\"xp_total_raw\":" +
            std::to_string(focus.target_progress.xp_total_raw);
        result += ",\"xp_within_level_raw\":" +
            std::to_string(focus.target_progress.xp_within_level_raw);
        result += ",\"xp_per_level\":" +
            std::to_string(focus.target_progress.xp_per_level);
        result += ",\"unspent_perk_points\":" +
            std::to_string(focus.target_progress.unspent_perk_points);
        result += ",\"used_perk_points\":" +
            std::to_string(focus.target_progress.used_perk_points);
      } else {
        result += "\"unavailable\",\"reason\":\"target_native_getters_unavailable\"";
      }
      result += '}';
    }
  } else if (context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::
                                     query_professional_workforce_only) {
    const auto &perk = context.stock_perk_result;
    result += "\"status\":";
    AppendJsonString(
        result, xar::ck3_11906::StockPerkLegalityStatusKeyV1(perk.status));
    result += ",\"read_only\":true,\"policy_scoped\":true,";
    result += "\"episode_run_id\":";
    AppendJsonString(result, context.episode_run_id);
    result += ",\"snapshot_id\":";
    AppendJsonString(result, context.snapshot_id);
    result += ",\"native_revision\":" +
        std::to_string(context.expected_revision);
    result += ",\"date_raw\":" +
        std::to_string(context.expected_snapshot.date_raw);
    result += ",\"played_character_id\":" +
        std::to_string(context.expected_snapshot.played_character_id);
    result += ",\"target_key\":";
    AppendJsonString(
        result, xar::ck3_11906::kStockPerkLegalityFollowupTargetV1);
    if (perk.status == xar::ck3_11906::
                           StockPerkLegalityStatusV1::observed_native_legal ||
        perk.status == xar::ck3_11906::
                           StockPerkLegalityStatusV1::observed_native_illegal) {
      result += ",\"lifestyle_key\":";
      AppendJsonString(result,
                       xar::ck3_11906::PlayerLifestyleWindowStableKeyViewV1(
                           perk.lifestyle_key));
      result += ",\"native_legal\":";
      result += perk.status == xar::ck3_11906::
                                   StockPerkLegalityStatusV1::
                                       observed_native_legal
                    ? "true" : "false";
      result += ",\"target_perk_owned\":";
      result += perk.observed_target_owned ? "true" : "false";
      result += ",\"unspent_perk_points\":" +
          std::to_string(perk.observed_unspent_points);
      result += ",\"used_perk_points\":" +
          std::to_string(perk.observed_used_points);
      result += ",\"xp_total_raw\":" +
          std::to_string(perk.observed_target_xp_total_raw);
      result += ",\"xp_within_level_raw\":" +
          std::to_string(perk.observed_target_xp_within_level_raw);
      result += ",\"xp_per_level\":" +
          std::to_string(perk.observed_target_xp_per_level);
      result += ",\"validator_invoked_twice\":";
      result += perk.validator_invoked_twice ? "true" : "false";
      result += ",\"scanned_database_rows\":" +
          std::to_string(perk.scanned_database_rows);
    }
  } else if (context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::
                                     query_diplomacy_targets_only) {
    using namespace xar::ck3_11906;
    const auto &focus = context.stock_focus_result;
    const auto &perk = context.stock_perk_result;
    const bool focus_observed =
        focus.status == StockFocusLegalityStatusV1::observed_native_legal ||
        focus.status == StockFocusLegalityStatusV1::observed_native_illegal;
    const bool perk_observed =
        perk.status == StockPerkLegalityStatusV1::observed_native_legal ||
        perk.status == StockPerkLegalityStatusV1::observed_native_illegal;
    const bool targets_agree =
        focus_observed && perk_observed && focus.target_progress.available &&
        focus.frame == perk.frame &&
        PlayerLifestyleWindowStableKeyViewV1(focus.lifestyle_key) ==
            PlayerLifestyleWindowStableKeyViewV1(perk.lifestyle_key) &&
        focus.target_progress.xp_total_raw ==
            perk.observed_target_xp_total_raw &&
        focus.target_progress.xp_within_level_raw ==
            perk.observed_target_xp_within_level_raw &&
        focus.target_progress.xp_per_level ==
            perk.observed_target_xp_per_level &&
        focus.target_progress.unspent_perk_points ==
            perk.observed_unspent_points &&
        focus.target_progress.used_perk_points ==
            perk.observed_used_points;
    result += "\"status\":\"";
    result += targets_agree ? "observed"
             : focus_observed && perk_observed &&
                       focus.target_progress.available
                 ? "inconsistent" : "unavailable";
    result += "\",\"read_only\":true,\"policy_scoped\":true,";
    result += "\"episode_run_id\":";
    AppendJsonString(result, context.episode_run_id);
    result += ",\"snapshot_id\":";
    AppendJsonString(result, context.snapshot_id);
    result += ",\"native_revision\":" +
        std::to_string(context.expected_revision);
    result += ",\"date_raw\":" +
        std::to_string(context.expected_snapshot.date_raw);
    result += ",\"played_character_id\":" +
        std::to_string(context.expected_snapshot.played_character_id);
    result += ",\"focus\":{\"target_key\":";
    AppendJsonString(result, kDiplomacyForeignAffairsFocusV1);
    result += ",\"status\":";
    AppendJsonString(result, StockFocusLegalityStatusKeyV1(focus.status));
    if (focus_observed) {
      result += ",\"native_legal\":";
      result += focus.status ==
                        StockFocusLegalityStatusV1::observed_native_legal
                    ? "true" : "false";
      result += ",\"lifestyle_key\":";
      AppendJsonString(result, PlayerLifestyleWindowStableKeyViewV1(
                                   focus.lifestyle_key));
      result += ",\"target_lifestyle_progress\":{\"presence\":";
      if (focus.target_progress.available) {
        result += "\"present\",\"source\":\"exact_native_getters\"";
        result += ",\"xp_total_raw\":" +
                  std::to_string(focus.target_progress.xp_total_raw);
        result += ",\"xp_within_level_raw\":" +
                  std::to_string(focus.target_progress.xp_within_level_raw);
        result += ",\"xp_per_level\":" +
                  std::to_string(focus.target_progress.xp_per_level);
        result += ",\"unspent_perk_points\":" +
                  std::to_string(focus.target_progress.unspent_perk_points);
        result += ",\"used_perk_points\":" +
                  std::to_string(focus.target_progress.used_perk_points);
      } else {
        result += "\"unavailable\",\"reason\":\"target_native_getters_unavailable\"";
      }
      result += '}';
    }
    result += "},\"perk\":{\"target_key\":";
    AppendJsonString(result, kDiplomacyThoughtfulPerkV1);
    result += ",\"status\":";
    AppendJsonString(result, StockPerkLegalityStatusKeyV1(perk.status));
    if (perk_observed) {
      result += ",\"native_legal\":";
      result += perk.status == StockPerkLegalityStatusV1::observed_native_legal
                    ? "true" : "false";
      result += ",\"lifestyle_key\":";
      AppendJsonString(result, PlayerLifestyleWindowStableKeyViewV1(
                                   perk.lifestyle_key));
      result += ",\"target_perk_owned\":";
      result += perk.observed_target_owned ? "true" : "false";
      result += ",\"unspent_perk_points\":" +
                std::to_string(perk.observed_unspent_points);
      result += ",\"used_perk_points\":" +
                std::to_string(perk.observed_used_points);
      result += ",\"xp_total_raw\":" +
                std::to_string(perk.observed_target_xp_total_raw);
      result += ",\"xp_within_level_raw\":" +
                std::to_string(perk.observed_target_xp_within_level_raw);
      result += ",\"xp_per_level\":" +
                std::to_string(perk.observed_target_xp_per_level);
    }
    result += '}';
  } else if (context.mode == xar::ck3_11906::
                          PlayerLifestyleFormalWireModeV1::query) {
    result += "\"status\":\"available\",\"episode_run_id\":";
    AppendJsonString(result, context.episode_run_id);
    result += ",\"formal_precondition_status\":";
    AppendJsonString(
        result, xar::ck3_11906::PlayerLifestyleFormalPreconditionResultKeyV1(
                    context.precondition_result));
    result += ",\"snapshot\":";
    result += SerializePlayerLifestyleSnapshot12004V1(*context.snapshot);
  } else if (context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::submit_perk ||
             context.mode == xar::ck3_11906::
                                 PlayerLifestyleFormalWireModeV1::submit_focus) {
    const auto &ack = context.pending_ack;
    result += "\"status\":";
    AppendJsonString(
        result, ack.status == xar::game::
                                 PlayerLifestyleSelectionActionAckStatusV1::
                                     submitted_verification_pending
                    ? "submitted_verification_pending"
                    : "rejected_before_submit");
    result += ",\"verification_pending\":";
    result += ack.verification_pending ? "true" : "false";
    result += ",\"action_request_id\":";
    AppendJsonString(result, ack.request_id);
    result += ",\"target_key\":";
    AppendJsonString(result,
                     xar::ck3_11906::PlayerLifestyleWindowStableKeyViewV1(
                         ack.target_key));
    result += ",\"pre_snapshot_id\":";
    AppendJsonString(result, LifestyleFixed(ack.snapshot_id));
    result += ",\"episode_run_id\":";
    AppendJsonString(result, LifestyleFixed(ack.episode_run_id));
    result += ",\"pre_public_revision\":" +
        std::to_string(ack.pre_public_revision);
    result += ",\"failure_class\":";
    AppendJsonString(
        result,
        xar::ck3_11906::PlayerLifestyleSelectionActionFailureClassKeyV1(
            ack.failure_class));
    result += ",\"rejection_reason\":";
    AppendJsonString(result, ack.rejection_reason);
  } else {
    const auto &receipt = context.receipt;
    result += "\"status\":";
    AppendJsonString(
        result, receipt.status == xar::game::
                                     PlayerLifestyleSelectionActionReceiptStatusV1::
                                         applied
                    ? "applied"
                    : receipt.status == xar::game::
                                          PlayerLifestyleSelectionActionReceiptStatusV1::
                                              rejected
                          ? "rejected"
                          : "postcondition_failed");
    result += ",\"action_request_id\":";
    AppendJsonString(result, receipt.request_id);
    result += ",\"post_snapshot_id\":";
    AppendJsonString(result, LifestyleFixed(receipt.post_snapshot_id));
    result += ",\"episode_run_id\":";
    AppendJsonString(result, LifestyleFixed(receipt.episode_run_id));
    result += ",\"post_public_revision\":" +
        std::to_string(receipt.post_public_revision);
    result += ",\"post_target_perk_owned\":";
    result += receipt.post_target_perk_owned ? "true" : "false";
    result += ",\"post_has_current_focus\":";
    result += receipt.post_has_current_focus ? "true" : "false";
    result += ",\"post_current_focus_key\":";
    AppendJsonString(result,
                     xar::ck3_11906::PlayerLifestyleWindowStableKeyViewV1(
                         receipt.post_current_focus_key));
    result += ",\"postcondition_verified\":";
    result += receipt.postcondition_verified ? "true" : "false";
    result += ",\"reason\":";
    AppendJsonString(result, receipt.reason);
  }
  if (context.mode == xar::ck3_11906::PlayerLifestyleFormalWireModeV1::query ||
      context.mode == xar::ck3_11906::
                          PlayerLifestyleFormalWireModeV1::query_professional_workforce_only ||
      context.mode == xar::ck3_11906::
                          PlayerLifestyleFormalWireModeV1::query_diplomacy_targets_only) {
    AppendLifestylePerkPredicateSourceSibling12004(result,
                                                  context.stock_perk_result);
    AppendLifestylePerkTriggerFrontierSibling12004(result,
                                                  context.stock_perk_result);
  }
  result += "}}";
  return game::Render12004BuildIdentity(std::move(result), descriptor);
}
std::string HandlePlayerLifestyle12004(
    PlayerLifestyleTransport12004 &transport, std::string_view request_id,
    std::string_view step, std::string_view payload,
    const game::GameAdapter &adapter, const PlayerLifestyleBindings12004 &bindings,
    const game::Snapshot &published, std::uint64_t published_revision,
    MainThreadQueryMailboxV1 &mailbox) {
  if (!AcceptsPlayerLifestyleStep12004(step)) return {};
  using namespace xar::ck3_11906;
  std::string expected_snapshot_id;
  std::string episode_run_id;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_date = 0;
  std::uint64_t expected_player = 0;
  if (!xar::bridge::JsonStringField(
          payload, "expected_snapshot_id", expected_snapshot_id, 48) ||
      !xar::bridge::JsonStringField(
          payload,
          step == kPlayerLifestyleFormalPrivateQueryStepV1 ||
                  step == kPlayerLifestyleFormalPrivateCurrentStateStepV1 ||
                  step == kPlayerLifestyleFormalPrivateStockFocusStepV1 ||
                  step == kPlayerLifestyleFormalPrivateProfessionalWorkforceStepV1 ||
                  step == kPlayerLifestyleFormalPrivateDiplomacyStepV1 ||
                  step == kPlayerLifestyleFormalPrivateMartialStepV1
              ? "episode_run_id"
              : "expected_episode_run_id",
          episode_run_id, 64) ||
      !xar::bridge::JsonUnsignedField(
          payload, "expected_revision", expected_revision) ||
      !xar::bridge::JsonUnsignedField(
          payload, "expected_date_raw", expected_date) ||
      !xar::bridge::JsonUnsignedField(
          payload, "expected_player_character_id", expected_player) ||
      expected_revision == 0 || expected_revision != published_revision ||
      expected_date > static_cast<std::uint64_t>(
                          std::numeric_limits<std::int32_t>::max()) ||
      expected_player == 0 ||
      expected_player > static_cast<std::uint64_t>(
                            std::numeric_limits<std::uint32_t>::max()) ||
      expected_snapshot_id != "native:" + std::to_string(published_revision) ||
      published.date_raw < 0 ||
      expected_date != static_cast<std::uint64_t>(published.date_raw) ||
      expected_player !=
          static_cast<std::uint64_t>(published.played_character_id) ||
      episode_run_id.rfind(
          "native-" + std::to_string(expected_player) + "-", 0) != 0) {
    return CommandResultFrame(request_id, step, false,
                              "private_lifestyle_frame_or_episode_invalid");
  }
  xar::game::Snapshot current{};
  if (!published.paused || !published.map_ready ||
      !published.has_played_character ||
      !published.played_character_alive ||
      !xar::game::ReadCk3_12002TimelineCoreSnapshot(adapter, current) ||
      !SameCoreFrame(current, published)) {
    return CommandResultFrame(request_id, step, false,
                              "private_lifestyle_published_frame_stale");
  }
  if (step == kPlayerLifestyleFormalPrivateSubmitStepV1 ||
      step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1) {
    std::string kind;
    std::string target;
    std::uint64_t expected_native = 0;
    std::uint64_t expected_proof = 0;
    if (!xar::bridge::JsonStringField(payload, "kind", kind, 16) ||
        !xar::bridge::JsonStringField(payload, "target_key", target, 128) ||
        !xar::bridge::JsonUnsignedField(
            payload, "expected_native_revision", expected_native) ||
        !xar::bridge::JsonUnsignedField(
            payload, "expected_proof_epoch", expected_proof) ||
        kind != (step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1
                     ? "focus" : "perk") ||
        (step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1 &&
         target != kStockFocusLegalityTargetV1 &&
         target != kMartialAuthorityFocusV1) ||
        (step == kPlayerLifestyleFormalPrivateSubmitStepV1 &&
         !PlayerLifestylePolicyStockPerkTargetAdmittedV1(target)) ||
        expected_native != published_revision ||
        expected_proof != published_revision ||
        transport.action_may_have_submitted ||
        transport.pending_ack.has_value() ||
        transport.last_query_revision != published_revision ||
        transport.last_query_stock_focus !=
            (step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1) ||
        (step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1 &&
         transport.last_query_focus_target != target) ||
        transport.last_query_episode != episode_run_id ||
        transport.last_query_player !=
            published.played_character_id) {
      return CommandResultFrame(
          request_id, step, false,
          "private_lifestyle_action_binding_or_pending_state_invalid");
    }
    xar::game::PlayerLifestyleWindowStableKeyV1 key{};
    if (!AssignPlayerLifestyleWindowStableKeyV1(target, key)) {
      return CommandResultFrame(request_id, step, false,
                                "private_lifestyle_target_key_invalid");
    }
  } else if (step == kPlayerLifestyleFormalPrivateReceiptStepV1) {
    std::string action_id;
    if (!xar::bridge::JsonStringField(
            payload, "action_request_id", action_id, 128) ||
        !transport.pending_ack.has_value() ||
        !transport.action_may_have_submitted ||
        action_id != transport.pending_ack->request_id ||
        episode_run_id != LifestyleFixed(
                              transport.pending_ack->
                                  episode_run_id) ||
        published_revision <=
            transport.pending_ack->pre_public_revision) {
      return CommandResultFrame(request_id, step, false,
                                "private_lifestyle_pending_receipt_invalid");
    }
  }

  if (!game::IsCk3_12004Descriptor(adapter.descriptor()) || !bindings.enabled) {
    return CommandResultFrame(request_id, step, false,
                              "private_lifestyle_actual4_bind_unavailable");
  }
  auto context12004 = std::make_unique<PlayerLifestyleFormalWireContext12004V1>();
  auto *context = context12004.get();
  const auto mode =
      step == kPlayerLifestyleFormalPrivateQueryStepV1
          ? PlayerLifestyleFormalWireModeV1::query
          : step == kPlayerLifestyleFormalPrivateCurrentStateStepV1
                ? PlayerLifestyleFormalWireModeV1::query_state_only
                : step == kPlayerLifestyleFormalPrivateStockFocusStepV1
                      ? PlayerLifestyleFormalWireModeV1::query_focus_only
                : step == kPlayerLifestyleFormalPrivateProfessionalWorkforceStepV1
                      ? PlayerLifestyleFormalWireModeV1::
                            query_professional_workforce_only
                : step == kPlayerLifestyleFormalPrivateDiplomacyStepV1
                      ? PlayerLifestyleFormalWireModeV1::
                            query_diplomacy_targets_only
                : step == kPlayerLifestyleFormalPrivateMartialStepV1
                      ? PlayerLifestyleFormalWireModeV1::
                            query_martial_focus_only
                : step == kPlayerLifestyleFormalPrivateSubmitStepV1
                      ? PlayerLifestyleFormalWireModeV1::submit_perk
                      : step == kPlayerLifestyleFormalPrivateSubmitFocusStepV1
                            ? PlayerLifestyleFormalWireModeV1::submit_focus
                      : PlayerLifestyleFormalWireModeV1::verify_receipt;
  const bool initialized = InitializePlayerLifestyleFormalWireContext12004V1(
      *context, bindings, current, published_revision, episode_run_id, mode);
  context->envelope.game = &adapter;
  context->envelope.mailbox = &mailbox;
  context->envelope.expected_snapshot = current;
  context->envelope.expected_snapshot_revision = published_revision;
  context->envelope.typed_context = context;
  context->envelope.snapshot_comparison =
      ck3_12002::QuerySnapshotComparison12002::core_frame;
  if (!initialized) {
    return CommandResultFrame(request_id, step, false,
                              "private_lifestyle_source_bind_unavailable");
  }
  if (mode == PlayerLifestyleFormalWireModeV1::submit_perk ||
      mode == PlayerLifestyleFormalWireModeV1::submit_focus) {
    context->action_request_id.assign(request_id);
    xar::bridge::JsonStringField(payload, "target_key",
                                 context->action_target_key, 128);
    context->action_request.request_id =
        context->action_request_id;
    context->action_request.kind =
        mode == PlayerLifestyleFormalWireModeV1::submit_focus
            ? xar::game::PlayerLifestyleSelectionKindV1::focus
            : xar::game::PlayerLifestyleSelectionKindV1::perk;
    context->action_request.target_key =
        context->action_target_key;
    context->action_request.expected_snapshot_id = context->snapshot_id;
    context->action_request.expected_episode_run_id =
        context->episode_run_id;
    context->action_request.expected_public_revision = published_revision;
    context->action_request.expected_native_revision = published_revision;
    context->action_request.expected_proof_epoch = published_revision;
    context->action_request.expected_date_raw = current.date_raw;
    context->action_request.expected_player_character_id =
        static_cast<std::uint32_t>(current.played_character_id);
  } else if (mode == PlayerLifestyleFormalWireModeV1::verify_receipt) {
    context->pending_ack = *transport.pending_ack;
  }
  auto &ticket = context->envelope.ticket;
  const auto submit = TrySubmitMainThreadQueryV1(
      mailbox, &ExecutePlayerLifestyleMailbox12004, &context->envelope, ticket);
  if (submit != MainThreadQuerySubmitResultV1::submitted) {
    return CommandResultFrame(request_id, step, false,
                              "private_lifestyle_application_main_unavailable");
  }
  if (mode == PlayerLifestyleFormalWireModeV1::submit_perk ||
      mode == PlayerLifestyleFormalWireModeV1::submit_focus)
    transport.action_may_have_submitted = true;
  auto wait = WaitForMainThreadQueryV1(mailbox,
                                      ticket, 8'000);
  while (wait == MainThreadQueryWaitResultV1::
                     timeout_executor_already_running) {
    wait = WaitForMainThreadQueryV1(mailbox,
                                   ticket, 2'000);
  }
  xar::game::Snapshot completion{};
  const bool stable =
      wait == MainThreadQueryWaitResultV1::completed &&
      context->envelope.frame_stable &&
      xar::game::ReadCk3_12002TimelineCoreSnapshot(adapter, completion) &&
      SameCoreFrame(completion, current);
  if ((mode == PlayerLifestyleFormalWireModeV1::submit_perk ||
       mode == PlayerLifestyleFormalWireModeV1::submit_focus) &&
      context->pending_ack.status ==
          xar::game::PlayerLifestyleSelectionActionAckStatusV1::
              submitted_verification_pending) {
    transport.pending_ack = context->pending_ack;
    transport.last_query_revision = 0;
    transport.last_query_stock_focus = false;
    transport.last_query_focus_target.clear();
  }
  std::string response =
      stable ? RenderPlayerLifestyle12004(
                   request_id, step, *context, adapter.descriptor())
             : CommandResultFrame(
                   request_id, step, false,
                   "private_lifestyle_executor_or_completion_state_red");
  if (stable && context->completed) {
    if (mode == PlayerLifestyleFormalWireModeV1::query ||
        ((mode == PlayerLifestyleFormalWireModeV1::query_focus_only ||
          mode == PlayerLifestyleFormalWireModeV1::query_martial_focus_only) &&
         context->stock_focus_result.status ==
             StockFocusLegalityStatusV1::observed_native_legal &&
         context->stock_focus_result.target_progress.available)) {
      transport.last_query_episode = episode_run_id;
      transport.last_query_revision = published_revision;
      transport.last_query_player =
          published.played_character_id;
      transport.last_query_stock_focus =
          mode == PlayerLifestyleFormalWireModeV1::query_focus_only ||
          mode == PlayerLifestyleFormalWireModeV1::query_martial_focus_only;
      transport.last_query_focus_target =
          transport.last_query_stock_focus
              ? std::string(PlayerLifestyleWindowStableKeyViewV1(
                    context->stock_focus_result.target_key))
              : std::string{};
    } else if ((mode == PlayerLifestyleFormalWireModeV1::submit_perk ||
                mode == PlayerLifestyleFormalWireModeV1::submit_focus) &&
               PlayerLifestyleAckProvesNoNativeSubmitV1(
                   context->pending_ack)) {
      transport.action_may_have_submitted = false;
      transport.last_query_revision = 0;
      transport.last_query_stock_focus = false;
      transport.last_query_focus_target.clear();
    } else if (mode == PlayerLifestyleFormalWireModeV1::verify_receipt &&
               context->receipt.status ==
                   xar::game::PlayerLifestyleSelectionActionReceiptStatusV1::
                       applied) {
      transport.pending_ack.reset();
      transport.action_may_have_submitted = false;
    }
  }
  if (ReclaimMainThreadQueryV1(mailbox,
                               ticket) !=
      MainThreadQueryReclaimResultV1::reclaimed) {
    response = CommandResultFrame(
        request_id, step, false,
        "private_lifestyle_mailbox_result_not_reclaimed");
  }
  return response;
}
} // namespace xar::ck3_12004::lifestyle
