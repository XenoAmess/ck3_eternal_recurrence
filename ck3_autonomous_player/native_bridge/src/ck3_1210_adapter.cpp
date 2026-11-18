#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include <array>
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include <mutex>
#if defined(XAR_CK3_ENABLE_1210_CORE_FRAME_V1)
#include <windows.h>
#endif

namespace xar::game {
namespace {
// Default builds expose only the reviewed Core prefix. Explicit observation
// features use new exact bindings. Ordinary C++ virtual methods remain closed;
// versioned wire clock control has its own complete-value admission.
class FlorinAdapter final : public GameAdapter {
public:
  explicit FlorinAdapter(ck3_1210::CoreBindings bindings, ck3_1210::FullSnapshotBindingsV1 full={}) noexcept : core_(bindings),full_(full) {}
  const AdapterDescriptor &descriptor() const noexcept override {
    return Ck3_1210AdapterDescriptor();
  }
  bool enabled() const noexcept override { return core_.enabled; }
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    output = {};
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
    ck3_1210::FullSnapshotDiagnosticsV1 diagnostics{};
    const bool result=ck3_1210::ReadFullSnapshotV1(full_,output,diagnostics);
    try {std::lock_guard lock(diagnostic_mutex_);diagnostics_=diagnostics;} catch(...) {}
    return result;
#else
    return false;
#endif
  }
  ck3_1210::FullSnapshotDiagnosticsV1 FullDiagnostics() const noexcept {
    try {std::lock_guard lock(diagnostic_mutex_);return diagnostics_;} catch(...) {return {};}
  }
  xar::game::PauseSubmitResult
  submit_pause_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult
  submit_resume_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SelectEventOptionResult
  submit_select_event_option(std::int32_t) const noexcept override {
    return xar::game::SelectEventOptionResult::unavailable;
  }
  xar::game::SaveCheckpointResult
  submit_save_checkpoint() const noexcept override {
    return {};
  }
  xar::game::ReplyPendingInteractionResult
  submit_reply_to_pending_interaction(
      xar::game::PendingInteractionReply) const noexcept override {
    return xar::game::ReplyPendingInteractionResult::unavailable;
  }
  xar::game::RaiseTroopsResult
  submit_raise_troops_default() const noexcept override {
    return xar::game::RaiseTroopsResult::unavailable;
  }
  xar::game::MoveArmyResult
  submit_move_army(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MoveArmyResult::unavailable;
  }
  xar::game::PreviewMoveArmyResult
  preview_move_army(std::int32_t, std::int32_t) const noexcept override {
    return {};
  }
  xar::game::DisbandArmyResult
  submit_disband_army(std::int32_t) const noexcept override {
    return xar::game::DisbandArmyResult::unavailable;
  }
  xar::game::SplitArmyHalfResult
  submit_split_army_half(std::int32_t) const noexcept override {
    return xar::game::SplitArmyHalfResult::unavailable;
  }
  xar::game::MergeArmiesResult
  submit_merge_armies(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MergeArmiesResult::unavailable;
  }
  xar::game::StartAssaultResult
  submit_start_assault(std::int32_t) const noexcept override {
    return xar::game::StartAssaultResult::unavailable;
  }
  xar::game::StopAssaultResult
  submit_stop_assault(std::int32_t) const noexcept override {
    return xar::game::StopAssaultResult::unavailable;
  }
  bool read_declarable_wars(
      std::vector<xar::game::DeclarableWarSnapshot> &output) const noexcept override {
    output.clear();
    return false;
  }
  xar::game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &output)
      const noexcept override {
    output.clear();
    return xar::game::ReadDeclarableWarsResult::unavailable;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &output,
      xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    output.clear();
    diagnostics = {};
    return xar::game::ReadArrangeMarriageChoicesResult::unavailable;
  }
  xar::game::ArrangeMarriageResult submit_arrange_marriage(
      const xar::game::ArrangeMarriageChoice &) const noexcept override {
    return xar::game::ArrangeMarriageResult::unavailable;
  }
  xar::game::EnforceDemandsResult
  submit_enforce_demands(std::int32_t) const noexcept override {
    return xar::game::EnforceDemandsResult::unavailable;
  }
  xar::game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<xar::game::ArmyStrengthSnapshot> &output) const noexcept override {
    output.clear();
    return xar::game::ReadArmyStrengthsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsResult
  read_combat_simulation_inputs(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsV3Snapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsV3Result::unavailable;
  }
  xar::game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t,
      xar::game::WarTerminationOptionsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationOptionsResult::unavailable;
  }
  xar::game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t,
      xar::game::WarTerminationTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationTermsResult::unavailable;
  }
  xar::game::ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t,
      xar::game::WarTerminationExitTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationExitTermsResult::unavailable;
  }
  xar::game::SurrenderWarResult
  submit_surrender_war(std::int32_t) const noexcept override {
    return xar::game::SurrenderWarResult::unavailable;
  }
  xar::game::OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t) const noexcept override {
    return xar::game::OfferWhitePeaceResult::unavailable;
  }
  bool ReadTimelineCore(Snapshot &output) const noexcept {
    output = {};
    ck3_1210::CoreSnapshotPrefix prefix{};
    if (!ck3_1210::ReadCoreSnapshot(core_, prefix)) return false;
    output.date_raw = prefix.clock.date_raw;
    output.speed = prefix.clock.speed;
    output.paused = prefix.clock.paused;
    output.player_id = prefix.local_player_id;
    output.map_ready = prefix.map_ready;
    output.has_played_character = prefix.has_played_character;
    output.played_character_id = prefix.played_character_id;
    output.played_character_alive = prefix.played_character_alive;
    return true;
  }
private:
  ck3_1210::CoreBindings core_{};
  ck3_1210::FullSnapshotBindingsV1 full_{};
  mutable std::mutex diagnostic_mutex_;
  mutable ck3_1210::FullSnapshotDiagnosticsV1 diagnostics_{};
};
} // namespace

const AdapterDescriptor &Ck3_1210AdapterDescriptor() noexcept {
#if defined(XAR_CK3_ENABLE_1210_CORE_FRAME_V1)
  static constexpr std::string_view capabilities[]{
      ck3_1210::kCoreFrameCapabilityV1,
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
      "game.state.snapshot", "game.query.fresh-full-state.v1",
#endif
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_GOLD_V1)
      ck3_1210::kPersonalGoldCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_ACTOR_FOUNDATION_V1)
      ck3_1210::kActorFoundationCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_CORE_CONTROL_V1)
      ck3_1210::kCoreControlCapabilityV1,
#if !defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
      "game.command.pause-map", "game.command.resume-map",
      "game.command.set-speed-1", "game.command.set-speed-2", "game.command.set-speed-3",
      "game.command.set-speed-4", "game.command.set-speed-5", "game.command.save-checkpoint",
#elif defined(XAR_CK3_ENABLE_1210_FULL_CLOCK_V1)
      ck3_1210::kFullClockControlCapabilityV1,
      "game.command.pause-map", "game.command.set-speed-1", "game.command.set-speed-2",
      "game.command.set-speed-3", "game.command.set-speed-4", "game.command.set-speed-5", "game.command.save-checkpoint",
#endif
#if defined(XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1)
      ck3_1210::kApplicationExitCapabilityV1,
#endif
#endif
  };
#else
  static constexpr std::array<std::string_view, 0> capabilities{};
#endif
  static const AdapterDescriptor descriptor{
      ck3_1210::kAdapterId, ck3_1210::kGameVersion,
      ck3_1210::kExecutableSha256, "xar_checkpoint", capabilities};
  return descriptor;
}

std::unique_ptr<GameAdapter> CreateCk3_1210AdapterFromBindings(
    ck3_1210::CoreBindings bindings) noexcept {
  return std::make_unique<FlorinAdapter>(bindings);
}

ck3_1210::FullSnapshotDiagnosticsV1 ReadCk3_1210FullSnapshotDiagnostics(const GameAdapter &game) noexcept {
 const auto *native=dynamic_cast<const FlorinAdapter*>(&game);
 return native?native->FullDiagnostics():ck3_1210::FullSnapshotDiagnosticsV1{};
}
bool ReadCk3_1210TimelineCoreSnapshot(const GameAdapter &adapter,
    Snapshot &output) noexcept {
  output = {};
  const auto *native = dynamic_cast<const FlorinAdapter *>(&adapter);
  return native != nullptr && native->ReadTimelineCore(output);
}

std::unique_ptr<GameAdapter> CreateCk3_1210Adapter(
    std::string_view executable_sha256) noexcept {
  ck3_1210::CoreBindings core{};
#if defined(XAR_CK3_ENABLE_1210_CORE_FRAME_V1)
  core = ck3_1210::BindCoreImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), executable_sha256);
#else
  static_cast<void>(executable_sha256);
#endif
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
  return std::make_unique<FlorinAdapter>(core,ck3_1210::BindFullSnapshotImageV1(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),executable_sha256));
#else
  return CreateCk3_1210AdapterFromBindings(core);
#endif
}
} // namespace xar::game
