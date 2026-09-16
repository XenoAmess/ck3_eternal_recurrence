#include "xar_bridge/player_lifestyle_formal_wire_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <limits>

namespace xar::ck3_11906 {
namespace {

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool OnMain(const PlayerLifestyleFormalWireContextV1 &context) noexcept {
  return context.stamp.thread_id != 0 && context.stamp.paused &&
         context.stamp.tls_initialized != 0 &&
         context.stamp.tls_main_thread_marker != 0 &&
         GetCurrentThreadId() == context.stamp.thread_id;
}

bool IsMain(void *opaque) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  return context != nullptr && OnMain(*context);
}

bool CurrentBound(const PlayerLifestyleFormalWireContextV1 &context,
                  game::Snapshot &current) noexcept {
  return OnMain(context) && ReadSnapshot(context.bindings, current) &&
         current == context.expected_snapshot && current.paused &&
         current.map_ready && current.has_played_character &&
         current.played_character_alive &&
         current.played_character_id > 0 &&
         current.date_raw == context.stamp.date_raw &&
         context.expected_revision != 0 &&
         context.snapshot_id ==
             "native:" + std::to_string(context.expected_revision);
}

bool CaptureCommon(PlayerLifestyleFormalWireContextV1 &context,
                   std::uintptr_t &character,
                   game::Snapshot &current) noexcept {
  character = 0;
  if (!CurrentBound(context, current)) return false;
  return ResolvePlayerLifestylePlayedCharacterV1(
      context.source_environment, context.source_access,
      static_cast<std::uint32_t>(current.played_character_id), character);
}

bool CaptureStateFrame(void *opaque,
                       PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr ||
      context->snapshot_id.size() >= output.snapshot_id.size()) return false;
  std::uintptr_t character = 0;
  game::Snapshot current{};
  if (!CaptureCommon(*context, character, current)) return false;
  output = {};
  std::copy(context->snapshot_id.begin(), context->snapshot_id.end(),
            output.snapshot_id.begin());
  output.public_revision = context->expected_revision;
  output.native_revision = context->expected_revision;
  output.proof_epoch =
      PlayerLifestyleFormalFrameProofEpochV1(context->expected_revision,
                                            context->stamp.pump_epoch);
  output.date_raw = current.date_raw;
  output.paused = current.paused;
  output.map_ready = current.map_ready;
  output.has_played_character = current.has_played_character;
  output.played_character_alive = current.played_character_alive;
  output.played_character_id = current.played_character_id;
  output.played_character = character;
  output.played_character_identity_round_trip = true;
  return true;
}

bool CaptureWindowFrame(void *opaque,
                        PlayerLifestyleWindowFrameV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr ||
      context->snapshot_id.size() >= output.snapshot_id.size()) return false;
  std::uintptr_t character = 0;
  game::Snapshot current{};
  if (!CaptureCommon(*context, character, current)) return false;
  output = {};
  std::copy(context->snapshot_id.begin(), context->snapshot_id.end(),
            output.snapshot_id.begin());
  output.public_revision = context->expected_revision;
  output.native_revision = context->expected_revision;
  output.proof_epoch =
      PlayerLifestyleFormalFrameProofEpochV1(context->expected_revision,
                                            context->stamp.pump_epoch);
  output.date_raw = current.date_raw;
  output.paused = current.paused;
  output.map_ready = current.map_ready;
  output.has_played_character = current.has_played_character;
  output.played_character_alive = current.played_character_alive;
  output.played_character_id =
      static_cast<std::uint32_t>(current.played_character_id);
  output.played_character = character;
  output.played_character_identity_round_trip = true;
  return true;
}

bool CaptureStockPerkFrame(void *opaque,
                           StockPerkLegalityFrameV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr ||
      context->snapshot_id.size() >= output.snapshot_id.size() ||
      context->episode_run_id.size() >= output.episode_run_id.size()) {
    return false;
  }
  std::uintptr_t character = 0;
  game::Snapshot current{};
  if (!CaptureCommon(*context, character, current)) return false;
  output = {};
  std::copy(context->episode_run_id.begin(), context->episode_run_id.end(),
            output.episode_run_id.begin());
  std::copy(context->snapshot_id.begin(), context->snapshot_id.end(),
            output.snapshot_id.begin());
  output.public_revision = context->expected_revision;
  output.native_revision = context->expected_revision;
  output.proof_epoch = PlayerLifestyleFormalFrameProofEpochV1(
      context->expected_revision, context->stamp.pump_epoch);
  output.date_raw = current.date_raw;
  output.played_character_id =
      static_cast<std::uint32_t>(current.played_character_id);
  output.played_character = character;
  output.paused = current.paused;
  output.map_ready = current.map_ready;
  output.played_character_alive = current.played_character_alive;
  output.storage_round_trip = true;
  return true;
}

bool ReadStockPerkPlayerState(
    void *opaque, const StockPerkLegalityFrameV1 &frame,
    StockPerkLegalityPlayerStateV1 &output) noexcept {
  output = {};
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr || context->snapshot == nullptr ||
      context->snapshot->status !=
          game::PlayerLifestyleSnapshotStatusV1::available ||
      context->snapshot->player_character_id < 0 ||
      static_cast<std::uint32_t>(context->snapshot->player_character_id) !=
          frame.played_character_id ||
      context->snapshot->public_revision != frame.public_revision ||
      context->snapshot->native_revision != frame.native_revision ||
      context->snapshot->proof_epoch != frame.proof_epoch ||
      context->snapshot->date_raw != frame.date_raw ||
      !context->snapshot->readiness.current_focus_ready ||
      !context->snapshot->readiness.lifestyle_progress_ready ||
      !context->snapshot->readiness.owned_perks_ready ||
      !context->snapshot->readiness.same_frame_ready) {
    return false;
  }
  const auto &state = context->snapshot->state;
  if (!state.current_lifestyle_progress_present ||
      state.current_lifestyle_progress.unspent_perk_points < 0 ||
      !AssignPlayerLifestyleWindowStableKeyV1(
          PlayerLifestyleStableKeyViewV1(
              state.current_lifestyle_progress.lifestyle_key),
          output.current_lifestyle_key)) {
    return false;
  }
  output.unspent_perk_points =
      state.current_lifestyle_progress.unspent_perk_points;
  output.owned_perk_state_known = true;
  output.target_perk_owned = false;
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    if (PlayerLifestyleStableKeyViewV1(state.owned_perk_keys[index]) ==
        kStockPerkLegalityTargetV1) {
      output.target_perk_owned = true;
      break;
    }
  }
  return true;
}

bool PublishStockPerkCandidates(
    const StockPerkLegalityResultV1 &source,
    game::PlayerLifestyleWindowCandidatesV1 &output) noexcept {
  using Status = StockPerkLegalityStatusV1;
  if (source.status != Status::observed_native_legal &&
      source.status != Status::observed_native_illegal) {
    return false;
  }
  output = {};
  output.status = game::PlayerLifestyleWindowCandidatesStatusV1::available;
  output.unavailable_reason =
      game::PlayerLifestyleWindowCandidatesFailureV1::none;
  std::copy(source.frame.snapshot_id.begin(), source.frame.snapshot_id.end(),
            output.snapshot_id.begin());
  output.public_revision = source.frame.public_revision;
  output.native_revision = source.frame.native_revision;
  output.proof_epoch = source.frame.proof_epoch;
  output.date_raw = source.frame.date_raw;
  output.player_character_id = source.frame.played_character_id;
  // No focus definition source is available without the stock window. Keep
  // that collection explicitly unavailable rather than claiming known-empty.
  output.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::unavailable;
  output.perk_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  output.perk_count = 1;
  output.perks[0].key = source.target_key;
  output.perks[0].lifestyle_key = source.lifestyle_key;
  output.perks[0].can_select =
      source.status == Status::observed_native_legal;
  output.perks[0].can_select_ignore_cost = false;
  output.readiness.bound_player_ready = true;
  output.readiness.containers_ready = true;
  output.readiness.perk_candidates_ready = true;
  output.readiness.final_legality_ready = true;
  output.readiness.same_frame_ready = true;
  return true;
}

PlayerLifestyleWindowSourceReadResultV1 ReadWindowSource(
    void *opaque, std::uintptr_t module_base,
    std::uint32_t played_character_id,
    PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr || !OnMain(*context)) {
    return PlayerLifestyleWindowSourceReadResultV1::source_read_failed;
  }
  return ReadPlayerLifestyleWindowSourceAdapterV1(
      context->source_state, context->source_environment,
      context->source_access, module_base, played_character_id, output);
}

bool ReadState(PlayerLifestyleFormalWireContextV1 &context) noexcept {
  if (context.snapshot == nullptr) return false;
  const auto environment = BindPlayerLifestyleSnapshotEnvironmentV1(
      context.module_base, true, kPlayerLifestyleSnapshotExecutableSha256V1);
  PlayerLifestyleSnapshotAccessV1 access{};
  access.context = &context;
  access.capture_frame = &CaptureStateFrame;
  access.is_main_thread = &IsMain;
  access.read_memory = &ReadMemory;
  const PlayerLifestyleSnapshotRequestV1 request{
      context.snapshot_id, context.expected_revision,
      context.expected_revision, context.expected_snapshot.date_raw,
      context.expected_snapshot.played_character_id};
  return ReadPlayerLifestyleSnapshotV1(environment, access, request,
                                        *context.snapshot) ==
         game::ReadPlayerLifestyleSnapshotResultV1::available;
}

bool ReadCandidates(PlayerLifestyleFormalWireContextV1 &context) noexcept {
  if (context.candidates == nullptr) return false;
  const PlayerLifestyleWindowCandidatesEnvironmentV1 environment{
      true, kPlayerLifestyleWindowCandidatesExecutableSha256V1,
      context.module_base, false};
  const PlayerLifestyleWindowCandidatesAccessV1 access{
      &context, &CaptureWindowFrame, &IsMain, &ReadWindowSource};
  const PlayerLifestyleWindowCandidatesRequestV1 request{
      context.snapshot_id, context.expected_revision,
      context.expected_revision, context.expected_snapshot.date_raw,
      static_cast<std::uint32_t>(
          context.expected_snapshot.played_character_id)};
  if (ReadPlayerLifestyleWindowCandidatesV1(environment, access, request,
                                             *context.candidates) ==
      game::ReadPlayerLifestyleWindowCandidatesResultV1::available) {
    context.stock_perk_result = {};
    return true;
  }
  if (context.candidates->unavailable_reason !=
      game::PlayerLifestyleWindowCandidatesFailureV1::
          lifestyle_window_unbound_or_stale) {
    return false;
  }
  const auto stock_environment = BindStockPerkLegalityEnvironmentV1(
      context.module_base, true, kStockPerkLegalityExeSha256V1);
  const StockPerkLegalityAccessV1 stock_access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &ReadStockPerkPlayerState};
  context.stock_perk_result =
      ReadStockPerkLegalityV1(stock_environment, stock_access);
  if (!PublishStockPerkCandidates(context.stock_perk_result,
                                  *context.candidates)) {
    context.failure = "native_lifestyle_windowless_policy_perk_";
    context.failure +=
        StockPerkLegalityStatusKeyV1(context.stock_perk_result.status);
    return false;
  }
  return true;
}

bool CapturePrecondition(
    void *opaque,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr || !ReadState(*context) ||
      !ReadCandidates(*context)) return false;
  context->precondition_result = BuildPlayerLifestyleFormalPreconditionV1(
      *context->snapshot, *context->candidates, context->episode_run_id,
      output);
  return context->precondition_result ==
         PlayerLifestyleFormalPreconditionResultV1::ready;
}

bool CaptureReceiptState(
    void *opaque,
    game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  return context != nullptr && ReadState(*context) &&
         BuildPlayerLifestyleFormalReceiptObservationV1(
             *context->snapshot, context->episode_run_id, output) ==
             PlayerLifestyleFormalPreconditionResultV1::ready;
}

bool IsPaused(void *opaque) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  return context != nullptr && OnMain(*context);
}

bool SubmitPerk(void *opaque, game::PlayerLifestyleSelectionKindV1 kind,
                const game::PlayerLifestyleWindowStableKeyV1 &key) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr ||
      kind != game::PlayerLifestyleSelectionKindV1::perk) {
    return false;
  }
  if (context->stock_perk_result.status ==
          StockPerkLegalityStatusV1::observed_native_legal &&
      PlayerLifestyleWindowStableKeyViewV1(key) ==
          kStockPerkLegalityTargetV1 &&
      context->stock_perk_result.target_definition != 0) {
    context->native_submit.last_result =
        DispatchResolvedPlayerLifestylePerkNativeAdapterV1(
            context->native_submit.environment,
            context->native_submit.access,
            context->native_submit.played_character_id,
            context->stock_perk_result.target_definition);
    return context->native_submit.last_result ==
        PlayerLifestyleSelectionNativeDispatchResultV1::
            submitted_verification_pending;
  }
  return SubmitPlayerLifestyleSelectionNativeAdapterV1(
      &context->native_submit, kind, key);
}

} // namespace

bool InitializePlayerLifestyleFormalWireContextV1(
    PlayerLifestyleFormalWireContextV1 &context,
    const Bindings &bindings,
    const game::Snapshot &expected_snapshot,
    std::uint64_t expected_revision,
    std::string_view episode_run_id,
    PlayerLifestyleFormalWireModeV1 mode) noexcept {
  try {
    if (expected_revision == 0 || expected_snapshot.played_character_id <= 0 ||
        episode_run_id.empty() ||
        episode_run_id.size() >=
            game::kPlayerLifestyleSelectionEpisodeRunIdCapacityV1) {
      return false;
    }
    context.bindings = bindings;
    context.expected_snapshot = expected_snapshot;
    context.expected_revision = expected_revision;
    context.module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    context.episode_run_id.assign(episode_run_id);
    context.snapshot_id = "native:" + std::to_string(expected_revision);
    context.mode = mode;
    context.source_environment =
        BindPlayerLifestyleWindowSourceAdapterEnvironmentV1(
            context.module_base, true,
            kPlayerLifestyleWindowCandidatesExecutableSha256V1);
    context.source_access = {&context, &ReadMemory};
    context.snapshot = std::make_unique<game::PlayerLifestyleSnapshotV1>();
    context.candidates =
        std::make_unique<game::PlayerLifestyleWindowCandidatesV1>();
    context.precondition =
        std::make_unique<game::PlayerLifestyleSelectionPreconditionV1>();
    auto &native = context.native_submit;
    native.environment = BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
        context.module_base, true,
        kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1);
    native.access.execution_context = &context;
    native.access.is_application_main_thread = &IsMain;
    native.access.is_paused = &IsPaused;
    native.access.source_state = &context.source_state;
    native.access.source_environment = context.source_environment;
    native.access.source_access = context.source_access;
    native.requested_module_base = context.module_base;
    native.played_character_id =
        static_cast<std::uint32_t>(expected_snapshot.played_character_id);
    return context.module_base != 0 &&
           PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(
               context.source_environment);
  } catch (...) {
    return false;
  }
}

bool ExecutePlayerLifestyleFormalWireMailboxV1(
    void *opaque,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContextV1 *>(opaque);
  if (context == nullptr) return false;
  try {
    context->stamp = stamp;
    context->completed = false;
    game::Snapshot current{};
    if (!CurrentBound(*context, current)) {
      context->failure = "published_native_frame_or_main_thread_stale";
      return true;
    }
    PlayerLifestyleSelectionActionAccessV1 access{};
    access.context = context;
    access.capture_precondition = &CapturePrecondition;
    access.capture_receipt_state = &CaptureReceiptState;
    access.is_main_thread = &IsMain;
    access.submit_native = &SubmitPerk;
    if (context->mode == PlayerLifestyleFormalWireModeV1::query_state_only) {
      if (!ReadState(*context)) {
        context->failure = PlayerLifestyleFormalStateFailureV1(
            context->snapshot->unavailable_reason);
        return true;
      }
      if (!PlayerLifestyleCurrentStateOnlyReadyV1(*context->snapshot)) {
        context->failure =
            "native_lifestyle_current_state_readiness_incomplete";
        return true;
      }
      context->completed = true;
      return true;
    }
    if (context->mode == PlayerLifestyleFormalWireModeV1::query) {
      if (!ReadState(*context)) {
        context->failure = PlayerLifestyleFormalStateFailureV1(
            context->snapshot->unavailable_reason);
        return true;
      }
      if (!ReadCandidates(*context)) {
        if (context->failure.empty()) {
          context->failure = PlayerLifestyleFormalFinalCandidatesFailureV1(
              context->candidates->unavailable_reason);
        }
        return true;
      }
      context->precondition_result = BuildPlayerLifestyleFormalPreconditionV1(
          *context->snapshot, *context->candidates,
          context->episode_run_id, *context->precondition);
      if (AttachPlayerLifestyleFinalCandidatesV1(
              *context->candidates, *context->snapshot) !=
          PlayerLifestyleFormalPreconditionResultV1::ready) {
        context->failure = "final_candidates_cannot_bind_to_state";
        return true;
      }
      context->completed = true;
      return true;
    }
    if (context->mode == PlayerLifestyleFormalWireModeV1::submit_perk) {
      if (context->action_request.kind !=
          game::PlayerLifestyleSelectionKindV1::perk) {
        context->failure = "only_final_legal_perk_admitted";
        return true;
      }
      const auto environment =
          BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
              context->native_submit.environment);
      (void)ExecutePlayerLifestyleSelectionActionV1(
          environment, access, context->action_request,
          context->pending_ack);
      context->completed = true;
      return true;
    }
    (void)VerifyPlayerLifestyleSelectionActionReceiptV1(
        access, context->pending_ack, context->receipt);
    context->completed = true;
    return true;
  } catch (...) {
    context->failure = "private_lifestyle_executor_exception";
    return true;
  }
}

} // namespace xar::ck3_11906
