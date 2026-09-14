#include "xar_bridge/faction_gift_mitigation_native_binder_v1.hpp"

#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using Details = FactionGiftMitigationSourceDetailsV1;
using Frame = FactionGiftMitigationSourceFrameV1;
using State = FactionGiftMitigationNativeBinderStateV1;

bool SameFrame(const Frame &left, const Frame &right) noexcept {
  return left == right;
}

bool NativeFrameExtendsRowFrame(const Frame &row,
                                const Frame &native) noexcept {
  return native.paused == row.paused &&
         native.row_published_generation == row.row_published_generation &&
         native.proof_epoch == row.proof_epoch &&
         native.snapshot_revision == row.snapshot_revision &&
         native.native_snapshot_revision != 0 &&
         native.date_raw == row.date_raw &&
         native.player_character_id == row.player_character_id;
}

bool ValidAnchors(
    const FactionGiftMitigationNativeBinderEnvironmentV1 &environment)
    noexcept {
  if (environment.module_base == 0) return false;
  for (std::size_t index = 0;
       index < kFactionGiftMitigationNativeAnchorCountV1; ++index) {
    const auto &expected = kFactionGiftMitigationExpectedAnchorsV1[index];
    const auto &observed = environment.anchors[index];
    if (expected.rva == 0 ||
        environment.module_base >
            (std::numeric_limits<std::uintptr_t>::max)() - expected.rva ||
        observed.rva != expected.rva ||
        observed.resolved_address != environment.module_base + expected.rva ||
        observed.span_sha256 != expected.span_sha256) {
      return false;
    }
  }
  return true;
}

bool CompleteUpstream(
    const FactionGiftMitigationNativeUpstreamV1 &upstream) noexcept {
  return upstream.read_targeting_rows != nullptr &&
         upstream.read_frame != nullptr &&
         upstream.read_faction != nullptr &&
         upstream.read_recipient != nullptr &&
         upstream.read_preview != nullptr &&
         upstream.validate_gift != nullptr &&
         upstream.claim_idempotency_key != nullptr &&
         upstream.submit_gift != nullptr;
}

bool ReadRows(void *context,
              bridge::FactionTargetingRowProbeResultV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  return state.bound && state.upstream.read_targeting_rows != nullptr &&
         state.upstream.read_targeting_rows(state.upstream.row_context,
                                             output);
}

bool ReadDetails(void *context, const Frame &required_row_frame,
                 std::uint32_t source_faction_id,
                 std::uint32_t recipient_character_id,
                 Details &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  state.preview_binding_available = false;
  state.preview_player_character_id = 0;
  state.preview_recipient_character_id = 0;
  state.preview_definition_stable_hash = 0;
  if (!state.bound || source_faction_id == 0 ||
      recipient_character_id == 0) {
    return false;
  }

  FactionGiftMitigationNativeFrameObservationV1 frame{};
  if (!state.upstream.read_frame(state.upstream.native_context,
                                  required_row_frame, frame) ||
      !frame.available ||
      !NativeFrameExtendsRowFrame(required_row_frame, frame.frame)) {
    return false;
  }

  FactionGiftMitigationNativeFactionObservationV1 faction{};
  if (!state.upstream.read_faction(
          state.upstream.native_context, frame.frame, source_faction_id,
          faction) ||
      !faction.available || !SameFrame(frame.frame, faction.frame)) {
    return false;
  }

  FactionGiftMitigationNativeRecipientObservationV1 recipient{};
  if (!state.upstream.read_recipient(
          state.upstream.native_context, frame.frame,
          recipient_character_id, recipient) ||
      !recipient.available || !SameFrame(frame.frame, recipient.frame)) {
    return false;
  }

  FactionGiftMitigationNativePreviewObservationV1 preview{};
  const bool preview_read = state.upstream.read_preview(
      state.upstream.native_context, frame.frame,
      frame.frame.player_character_id, recipient_character_id, preview);
  const bool preview_bound =
      preview_read && preview.available &&
      SameFrame(frame.frame, preview.frame) &&
      preview.player_character_id == frame.frame.player_character_id &&
      preview.recipient_character_id == recipient_character_id &&
      preview.preview.definition_key ==
          kFactionGiftMitigationActionV1DefinitionKey &&
      preview.preview.definition_stable_hash != 0;
  if (preview_bound) {
    state.preview_binding_available = true;
    state.preview_player_character_id = preview.player_character_id;
    state.preview_recipient_character_id = preview.recipient_character_id;
    state.preview_definition_stable_hash =
        preview.preview.definition_stable_hash;
  }

  output.available = true;
  output.frame = frame.frame;
  output.player_resources_query_complete =
      frame.player_resources_query_complete;
  output.player_gold_raw = frame.player_gold_raw;
  output.player_gold_scale = frame.player_gold_scale;
  output.source_faction_query_complete = faction.query_complete;
  output.queried_source_faction_id = faction.queried_source_faction_id;
  output.source_faction_present = faction.source_faction_present;
  output.source_faction_at_war = faction.source_faction_at_war;
  output.source_faction_metrics_available = faction.metrics_available;
  output.source_faction_power_raw = faction.power_raw;
  output.source_faction_discontent_raw = faction.discontent_raw;
  output.source_faction_metric_scale = faction.metric_scale;
  output.recipient_identity_resolved = recipient.identity_resolved;
  output.recipient_character_id = recipient.recipient_character_id;
  output.recipient_alive = recipient.alive;
  output.recipient_is_ai = recipient.is_ai;
  output.recipient_is_direct_landed_vassal =
      recipient.is_direct_landed_vassal;
  output.recipient_opinion_query_complete =
      recipient.opinion_query_complete;
  output.recipient_opinion_of_player = recipient.opinion_of_player;
  output.gift_opinion_present = recipient.gift_opinion_present;
  output.gift_opinion_modifier_value =
      recipient.gift_opinion_modifier_value;
  if (preview_bound) output.gift_preview = preview.preview;
  return true;
}

bool ValidateGift(void *context, std::uint32_t player_character_id,
                  std::uint32_t recipient_character_id,
                  std::string_view definition_key, bool &valid,
                  std::string &native_reason_key) noexcept {
  auto &state = *static_cast<State *>(context);
  valid = false;
  if (!state.bound || !state.preview_binding_available ||
      player_character_id != state.preview_player_character_id ||
      recipient_character_id != state.preview_recipient_character_id ||
      definition_key != kFactionGiftMitigationActionV1DefinitionKey ||
      state.preview_definition_stable_hash == 0) {
    native_reason_key = "native_binder_preview_identity_mismatch";
    return true;
  }
  return state.upstream.validate_gift(
      state.upstream.native_context, player_character_id,
      recipient_character_id, definition_key,
      state.preview_definition_stable_hash, valid, native_reason_key);
}

bool ClaimIdempotency(void *context,
                      std::string_view idempotency_key) noexcept {
  auto &state = *static_cast<State *>(context);
  if (!state.bound || state.idempotency_claim_attempted) return false;
  state.idempotency_claim_attempted = true;
  return state.upstream.claim_idempotency_key(
      state.upstream.native_context, idempotency_key);
}

bool SubmitGift(void *context, std::uint32_t player_character_id,
                std::uint32_t recipient_character_id,
                std::uint64_t definition_stable_hash) noexcept {
  auto &state = *static_cast<State *>(context);
  if (!state.bound || state.submit_attempted ||
      !state.preview_binding_available ||
      player_character_id != state.preview_player_character_id ||
      recipient_character_id != state.preview_recipient_character_id ||
      definition_stable_hash != state.preview_definition_stable_hash) {
    return false;
  }
  state.submit_attempted = true;
  return state.upstream.submit_gift(
      state.upstream.native_context, player_character_id,
      recipient_character_id,
      kFactionGiftMitigationActionV1DefinitionKey,
      definition_stable_hash);
}

} // namespace

bool BindFactionGiftMitigationNativeCallbacksV1(
    State &state,
    const FactionGiftMitigationNativeBinderEnvironmentV1 &environment,
    const FactionGiftMitigationNativeUpstreamV1 &upstream) noexcept {
  if (state.bound) return false;
  state = {};
  if (!environment.exact_build_admitted ||
      environment.executable_sha256 !=
          kFactionGiftMitigationActionV1ExecutableSha256 ||
      !ValidAnchors(environment) || !CompleteUpstream(upstream)) {
    return false;
  }
  state.bound = true;
  state.module_base = environment.module_base;
  state.upstream = upstream;
  return true;
}

FactionGiftMitigationSourceActionAccessV1
MakeFactionGiftMitigationNativeSourceActionAccessV1(State &state) noexcept {
  if (!state.bound) return {};
  return {&state, &ReadRows, &ReadDetails, &ValidateGift,
          &ClaimIdempotency, &SubmitGift};
}

FactionGiftMitigationNativeEnvironmentV1
MakeFactionGiftMitigationCertifiedActionEnvironmentV1(
    const State &state) noexcept {
  if (!state.bound) return {};
  return {state.module_base, true, true, false};
}

} // namespace xar::ck3_11906
