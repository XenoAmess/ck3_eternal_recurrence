#include "xar_bridge/ck3_12002_lifestyle.hpp"

#include <windows.h>

#include <algorithm>
#include <limits>

namespace xar::ck3_12002::lifestyle {
namespace {

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool OnMain(const PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  return context.stamp.thread_id != 0 && context.stamp.paused &&
         context.stamp.tls_initialized != 0 &&
         context.stamp.tls_main_thread_marker != 0 &&
         GetCurrentThreadId() == context.stamp.thread_id;
}

bool IsMain(void *opaque) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  return context != nullptr && OnMain(*context);
}

bool CurrentBound(const PlayerLifestyleFormalWireContext12002V1 &context,
                  game::Snapshot &current) noexcept {
  CoreSnapshotPrefix prefix{};
  if (!OnMain(context) || !ReadCoreSnapshot(context.core_bindings12002, prefix) ||
      prefix.clock.date_raw != context.expected_snapshot.date_raw ||
      prefix.clock.paused != context.expected_snapshot.paused ||
      prefix.played_character_id != context.expected_snapshot.played_character_id ||
      prefix.played_character_alive != context.expected_snapshot.played_character_alive ||
      prefix.map_ready != context.expected_snapshot.map_ready) return false;
  current = context.expected_snapshot;
  return current.paused &&
         current.map_ready && current.has_played_character &&
         current.played_character_alive &&
         current.played_character_id > 0 &&
         current.date_raw == context.stamp.date_raw &&
         context.expected_revision != 0 &&
         context.snapshot_id ==
             "native:" + std::to_string(context.expected_revision);
}

bool CaptureCommon(PlayerLifestyleFormalWireContext12002V1 &context,
                   std::uintptr_t &character,
                   game::Snapshot &current) noexcept {
  character = 0;
  if (!CurrentBound(context, current)) return false;
  character = reinterpret_cast<std::uintptr_t>(ResolveCoreCharacter(
      context.core_bindings12002, current.played_character_id));
  return character != 0;
}

bool CaptureStateFrame(void *opaque,
                       PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
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



bool CaptureStockPerkFrame(void *opaque,
                           StockPerkLegalityFrameV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
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

bool InvokeTargetProgressGetters(
    const PlayerLifestyleSnapshotEnvironmentV1 &environment,
    void *character, void *lifestyle, std::int64_t &total,
    std::int64_t &within, std::int32_t &unspent,
    std::int32_t &used) noexcept {
  if (environment.lifestyle_xp == nullptr ||
      environment.unspent_perk_points == nullptr ||
      environment.used_perk_points == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    if (environment.lifestyle_xp(character, &total, lifestyle, false) ==
            nullptr ||
        environment.lifestyle_xp(character, &within, lifestyle, true) ==
            nullptr) {
      return false;
    }
    unspent = environment.unspent_perk_points(character, lifestyle);
    used = environment.used_perk_points(character, lifestyle);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool CaptureStockFocusTargetProgress(
    void *opaque, const StockFocusLegalityFrameV1 &frame,
    std::uintptr_t target_lifestyle,
    StockFocusTargetProgressV1 &output) noexcept {
  output = {};
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  if (context == nullptr || target_lifestyle == 0 ||
      frame.played_character_id == 0 || !OnMain(*context)) {
    return false;
  }
  std::uintptr_t character = 0;
  game::Snapshot current{};
  if (!CaptureCommon(*context, character, current) ||
      character != frame.played_character ||
      static_cast<std::uint32_t>(current.played_character_id) !=
          frame.played_character_id ||
      current.date_raw != frame.date_raw ||
      context->expected_revision != frame.native_revision) {
    return false;
  }
  const auto environment = BindPlayerLifestyleSnapshotEnvironment12002V1(
      context->module_base, true,
      kPlayerLifestyleSnapshotExecutableSha256V1);
  std::int64_t total = -1;
  std::int64_t within = -1;
  std::int32_t unspent = -1;
  std::int32_t used = -1;
  if (!InvokeTargetProgressGetters(
          environment, reinterpret_cast<void *>(character),
          reinterpret_cast<void *>(target_lifestyle), total, within,
          unspent, used)) {
    return false;
  }
  std::int32_t xp_per_level = -1;
  if (!ReadMemory(context,
                  target_lifestyle + kPlayerLifestyleXpPerLevelOffsetV1,
                  &xp_per_level, sizeof(xp_per_level))) {
    return false;
  }
  output = {true, total, within, xp_per_level, unspent, used};
  return true;
}

void ReadStockFocus(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  const auto environment = BindStockFocusLegalityEnvironment12002V1(
      context.module_base, true, kStockFocusLegalityExeSha256V1);
  const StockFocusLegalityAccessV1 access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &CaptureStockFocusTargetProgress};
  context.stock_focus_result = ReadStockFocusLegality12002V1(environment, access);
}

void ReadDiplomacyFocus(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  const auto environment = BindStockFocusLegalityEnvironment12002V1(
      context.module_base, true, kStockFocusLegalityExeSha256V1);
  const StockFocusLegalityAccessV1 access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &CaptureStockFocusTargetProgress};
  context.stock_focus_result = ReadStockFocusLegality12002V1(
      environment, access, kDiplomacyForeignAffairsFocusV1,
      kDiplomacyLifestyleV1);
}

void ReadMartialFocus(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  const auto environment = BindStockFocusLegalityEnvironment12002V1(
      context.module_base, true, kStockFocusLegalityExeSha256V1);
  const StockFocusLegalityAccessV1 access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &CaptureStockFocusTargetProgress};
  context.stock_focus_result = ReadStockFocusLegality12002V1(
      environment, access, kMartialAuthorityFocusV1, kMartialLifestyleV1);
}

bool ReadStockPerkTargetPlayerState(
    void *opaque, const StockPerkLegalityFrameV1 &frame,
    std::uintptr_t target_lifestyle,
    std::string_view target_key,
    StockPerkLegalityPlayerStateV1 &output) noexcept {
  output = {};
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  if (context == nullptr || target_lifestyle == 0 ||
      (target_key != kStockPerkLegalityTargetV1 &&
       target_key != kStockPerkLegalityFollowupTargetV1 &&
       target_key != kStockPerkLegalityNextTargetV1 &&
       target_key != kStockPerkLegalityCollectTaxesTargetV1 &&
       target_key != kDiplomacyThoughtfulPerkV1 &&
       target_key != kMartialServeTheCrownPerkV1) ||
      !OnMain(*context) ||
      context->snapshot == nullptr ||
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
      !context->snapshot->readiness.owned_perks_ready ||
      !context->snapshot->readiness.same_frame_ready) {
    return false;
  }
  std::uintptr_t character = 0;
  game::Snapshot current{};
  if (!CaptureCommon(*context, character, current) ||
      character != frame.played_character ||
      static_cast<std::uint32_t>(current.played_character_id) !=
          frame.played_character_id ||
      current.date_raw != frame.date_raw ||
      context->expected_revision != frame.native_revision) {
    return false;
  }
  const auto &state = context->snapshot->state;
  const auto lifestyle_key =
      target_key == kDiplomacyThoughtfulPerkV1
          ? kDiplomacyThoughtfulLifestyleV1
          : target_key == kMartialServeTheCrownPerkV1
                ? kMartialPerkLifestyleV1
                : kStockPerkLegalityLifestyleV1;
  if (!AssignPlayerLifestyleWindowStableKeyV1(
          lifestyle_key, output.target_lifestyle_key)) {
    return false;
  }
  const auto environment = BindPlayerLifestyleSnapshotEnvironment12002V1(
      context->module_base, true,
      kPlayerLifestyleSnapshotExecutableSha256V1);
  if (!InvokeTargetProgressGetters(
          environment, reinterpret_cast<void *>(character),
          reinterpret_cast<void *>(target_lifestyle),
          output.target_xp_total_raw, output.target_xp_within_level_raw,
          output.unspent_perk_points, output.used_perk_points) ||
      !ReadMemory(context,
                  target_lifestyle + kPlayerLifestyleXpPerLevelOffsetV1,
                  &output.target_xp_per_level,
                  sizeof(output.target_xp_per_level))) {
    return false;
  }
  output.owned_perk_state_known = true;
  output.target_perk_owned = false;
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    if (PlayerLifestyleStableKeyView12002V1(state.owned_perk_keys[index]) ==
        target_key) {
      output.target_perk_owned = true;
      break;
    }
  }
  return true;
}

bool ReadStockPerkPlayerState(
    void *opaque, const StockPerkLegalityFrameV1 &frame,
    std::uintptr_t target_lifestyle,
    StockPerkLegalityPlayerStateV1 &output) noexcept {
  return ReadStockPerkTargetPlayerState(
      opaque, frame, target_lifestyle, kStockPerkLegalityTargetV1, output);
}

void ReadProfessionalWorkforcePerk(
    PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  const auto environment = BindStockPerkLegalityEnvironment12002V1(
      context.module_base, true, kStockPerkLegalityExeSha256V1);
  StockPerkLegalityAccessV1 access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &ReadStockPerkPlayerState};
  access.read_target_player_state = &ReadStockPerkTargetPlayerState;
  context.stock_perk_result = ReadStockPerkLegality12002V1(
      environment, access, kStockPerkLegalityFollowupTargetV1);
}

void ReadDiplomacyPerk(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  const auto environment = BindStockPerkLegalityEnvironment12002V1(
      context.module_base, true, kStockPerkLegalityExeSha256V1);
  StockPerkLegalityAccessV1 access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &ReadStockPerkPlayerState};
  access.read_target_player_state = &ReadStockPerkTargetPlayerState;
  context.stock_perk_result = ReadStockPerkLegality12002V1(
      environment, access, kDiplomacyThoughtfulPerkV1);
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



bool ReadState(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  if (context.snapshot == nullptr) return false;
  const auto environment = BindPlayerLifestyleSnapshotEnvironment12002V1(
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
  return ReadPlayerLifestyleSnapshot12002V1(environment, access, request,
                                        *context.snapshot) ==
         game::ReadPlayerLifestyleSnapshotResultV1::available;
}

bool ReadCandidates(PlayerLifestyleFormalWireContext12002V1 &context) noexcept {
  if (context.candidates == nullptr) return false;
  const auto stock_environment = BindStockPerkLegalityEnvironment12002V1(
      context.module_base, true, kStockPerkLegalityExeSha256V1);
  StockPerkLegalityAccessV1 stock_access{
      &context, &IsMain, &CaptureStockPerkFrame, &ReadMemory,
      &ReadStockPerkPlayerState};
  const auto target = PlayerLifestylePolicyStockPerkTargetV1(*context.snapshot);
  if (target.empty()) {
    context.failure = "native_lifestyle_windowless_policy_perk_ownership_unavailable";
    return false;
  }
  stock_access.read_target_player_state = &ReadStockPerkTargetPlayerState;
  context.stock_perk_result =
      ReadStockPerkLegality12002V1(stock_environment, stock_access, target);
  if (!PublishStockPerkCandidates(context.stock_perk_result,
                                  *context.candidates)) {
    context.failure = "native_lifestyle_windowless_policy_perk_";
    context.failure +=
        StockPerkLegalityStatusKey12002V1(context.stock_perk_result.status);
    return false;
  }
  return true;
}

bool CapturePrecondition(
    void *opaque,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  if (context == nullptr || !ReadState(*context)) return false;
  if (context->mode == PlayerLifestyleFormalWireModeV1::submit_focus) {
    if (context->action_target_key == kMartialAuthorityFocusV1) {
      ReadMartialFocus(*context);
    } else {
      ReadStockFocus(*context);
    }
    context->precondition_result =
        BuildPlayerLifestyleStockFocusPreconditionV1(
            *context->snapshot, context->stock_focus_result,
            context->episode_run_id, output);
    return context->precondition_result ==
           PlayerLifestyleFormalPreconditionResultV1::ready;
  }
  if (!ReadCandidates(*context)) return false;
  context->precondition_result = BuildPlayerLifestyleFormalPreconditionV1(
      *context->snapshot, *context->candidates, context->episode_run_id,
      output);
  return context->precondition_result ==
         PlayerLifestyleFormalPreconditionResultV1::ready;
}

bool CaptureReceiptState(
    void *opaque,
    game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  return context != nullptr && ReadState(*context) &&
         BuildPlayerLifestyleFormalReceiptObservationV1(
             *context->snapshot, context->episode_run_id, output) ==
             PlayerLifestyleFormalPreconditionResultV1::ready;
}

bool IsPaused(void *opaque) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  return context != nullptr && OnMain(*context);
}

bool SubmitSelection(void *opaque, game::PlayerLifestyleSelectionKindV1 kind,
                const game::PlayerLifestyleWindowStableKeyV1 &key) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
  if (context == nullptr) {
    return false;
  }
  if (kind == game::PlayerLifestyleSelectionKindV1::focus &&
      context->mode == PlayerLifestyleFormalWireModeV1::submit_focus &&
      context->stock_focus_result.status ==
          StockFocusLegalityStatusV1::observed_native_legal &&
      PlayerLifestyleWindowStableKeyViewV1(key) ==
          PlayerLifestyleWindowStableKeyViewV1(
              context->stock_focus_result.target_key) &&
      context->stock_focus_result.target_definition != 0) {
    context->native_submit.last_result =
        DispatchResolvedPlayerLifestyleFocusNativeAdapter12002V1(
            context->native_submit.environment,
            context->native_submit.access,
            context->native_submit.played_character_id,
            context->stock_focus_result.target_definition);
    return context->native_submit.last_result ==
        PlayerLifestyleSelectionNativeDispatchResultV1::
            submitted_verification_pending;
  }
  if (kind != game::PlayerLifestyleSelectionKindV1::perk ||
      context->mode != PlayerLifestyleFormalWireModeV1::submit_perk) {
    return false;
  }
  if (context->stock_perk_result.status ==
          StockPerkLegalityStatusV1::observed_native_legal &&
      PlayerLifestyleWindowStableKeyViewV1(key) ==
          PlayerLifestyleWindowStableKeyViewV1(
              context->stock_perk_result.target_key) &&
      PlayerLifestylePolicyStockPerkTargetAdmittedV1(
          PlayerLifestyleWindowStableKeyViewV1(key)) &&
      context->stock_perk_result.target_definition != 0) {
    context->native_submit.last_result =
        DispatchResolvedPlayerLifestylePerkNativeAdapter12002V1(
            context->native_submit.environment,
            context->native_submit.access,
            context->native_submit.played_character_id,
            context->stock_perk_result.target_definition);
    return context->native_submit.last_result ==
        PlayerLifestyleSelectionNativeDispatchResultV1::
            submitted_verification_pending;
  }
  return false;
}

} // namespace

bool InitializePlayerLifestyleFormalWireContext12002V1(
    PlayerLifestyleFormalWireContext12002V1 &context,
    const CoreBindings &bindings,
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
    context.core_bindings12002 = bindings;
    context.expected_snapshot = expected_snapshot;
    context.expected_revision = expected_revision;
    context.module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    context.episode_run_id.assign(episode_run_id);
    context.snapshot_id = "native:" + std::to_string(expected_revision);
    context.mode = mode;

    context.snapshot = std::make_unique<game::PlayerLifestyleSnapshotV1>();
    context.candidates =
        std::make_unique<game::PlayerLifestyleWindowCandidatesV1>();
    context.precondition =
        std::make_unique<game::PlayerLifestyleSelectionPreconditionV1>();
    auto &native = context.native_submit;
    native.environment = BindPlayerLifestyleSelectionNativeAdapterEnvironment12002V1(
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
    return context.module_base != 0 && context.core_bindings12002.enabled &&
        PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(native.environment);
  } catch (...) {
    return false;
  }
}

bool ExecutePlayerLifestyleFormalWireMailbox12002V1(
    void *opaque,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context = static_cast<PlayerLifestyleFormalWireContext12002V1 *>(opaque);
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
    access.submit_native = &SubmitSelection;
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
    if (context->mode == PlayerLifestyleFormalWireModeV1::query_focus_only) {
      ReadStockFocus(*context);
      context->completed = true;
      return true;
    }
    if (context->mode ==
        PlayerLifestyleFormalWireModeV1::query_martial_focus_only) {
      ReadMartialFocus(*context);
      context->completed = true;
      return true;
    }
    if (context->mode ==
        PlayerLifestyleFormalWireModeV1::query_professional_workforce_only) {
      if (!ReadState(*context)) {
        context->failure = PlayerLifestyleFormalStateFailureV1(
            context->snapshot->unavailable_reason);
        return true;
      }
      ReadProfessionalWorkforcePerk(*context);
      context->completed = true;
      return true;
    }
    if (context->mode ==
        PlayerLifestyleFormalWireModeV1::query_diplomacy_targets_only) {
      if (!ReadState(*context)) {
        context->failure = PlayerLifestyleFormalStateFailureV1(
            context->snapshot->unavailable_reason);
        return true;
      }
      ReadDiplomacyFocus(*context);
      ReadDiplomacyPerk(*context);
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
    if (context->mode == PlayerLifestyleFormalWireModeV1::submit_perk ||
        context->mode == PlayerLifestyleFormalWireModeV1::submit_focus) {
      if (context->action_request.kind !=
          (context->mode == PlayerLifestyleFormalWireModeV1::submit_focus
               ? game::PlayerLifestyleSelectionKindV1::focus
               : game::PlayerLifestyleSelectionKindV1::perk)) {
        context->failure = "lifestyle_selection_kind_mismatch";
        return true;
      }
      const auto environment =
          BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapter12002V1(
              context->native_submit.environment);
      (void)ExecutePlayerLifestyleSelectionAction12002V1(
          environment, access, context->action_request,
          context->pending_ack);
      context->completed = true;
      return true;
    }
    (void)VerifyPlayerLifestyleSelectionActionReceipt12002V1(
        access, context->pending_ack, context->receipt);
    context->completed = true;
    return true;
  } catch (...) {
    context->failure = "private_lifestyle_executor_exception";
    return true;
  }
}

} // namespace xar::ck3_12002::lifestyle
