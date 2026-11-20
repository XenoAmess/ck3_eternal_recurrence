#include "xar_bridge/native_snapshot_observer_scope92.hpp"
#include "xar_bridge/fresh_full_callback_cause81.hpp"
#if defined(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1)
#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
#endif
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include "xar_bridge/ck3_1210_opening_readonly56.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_personal_cash_frame_v1.hpp"
#if defined(XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
#endif
#include <array>
#include <intrin.h>
#include "xar_bridge/ck3_1210_military_production58.hpp"
#include "xar_bridge/ck3_1210_nonempty_military_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include <mutex>
#include <atomic>
#include <cstring>
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include "xar_bridge/ck3_1210_event_option_control_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_1210_toast_query_v1.hpp"
#if defined(XAR_CK3_ENABLE_1210_CORE_FRAME_V1) || defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
#include <windows.h>
#endif

namespace xar::game {
namespace {
// Default builds expose only the reviewed Core prefix. Explicit observation
// features use new exact bindings. Ordinary C++ virtual methods remain closed;
// versioned wire clock control has its own complete-value admission.
class FlorinAdapter final : public GameAdapter {
public:
  explicit FlorinAdapter(ck3_1210::CoreBindings bindings, ck3_1210::FullSnapshotBindingsV1 full={},
      bool core_only_26785313=false) noexcept : core_(bindings),full_(full),core_only_26785313_(core_only_26785313) {}
  const AdapterDescriptor &descriptor() const noexcept override {
    if(core_only_26785313_)return Ck3_121003Core26785313AdapterDescriptor();
    return ck3_1210::IsHotfix(core_.image_build)?Ck3_1210Hotfix26757580AdapterDescriptor():Ck3_1210AdapterDescriptor();
  }
  bool enabled() const noexcept override { return core_.enabled; }
  void BindSnapshotOwner(const ck3_11906::MainThreadQueryMailboxV1 &m) const noexcept {owner_mailbox_.store(&m);}
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    return ReadSnapshotWithRequestCause81(output,nullptr);
  }
  bool ReadSnapshotWithRequestCause81(xar::game::Snapshot &output,
      [[maybe_unused]] xar::diagnostic81::RawFullCause *cause81) const noexcept {
    output = {};
    if(core_only_26785313_)return false;
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
    ck3_1210::FullSnapshotDiagnosticsV1 diagnostics{};
    const auto finish=[&](bool result) noexcept {
      // Copy this call value before publishing the legacy shared diagnostic.
      if(cause81)xar::diagnostic81::CaptureFullValue(*cause81,diagnostics);
      try {std::lock_guard lock(diagnostic_mutex_);diagnostics_=diagnostics;} catch(...) {}
      return result;
    };
    auto current=full_;
    if(!current.exact_build_admitted || !current.core.enabled) {
      diagnostics.stage="binding";diagnostics.reason="full_snapshot_exact_build_unavailable";
      return finish(false);
    }
#if defined(XAR_CK3_ENABLE_26757580_ARMY_FULL58)
    if(ck3_1210::IsHotfix(core_.image_build) && current.enable_army_base && !MilitaryTargets58(current.army_base)) {
      diagnostics.stage="binding";diagnostics.reason="full_snapshot_military_targets_unqualified";return finish(false);
    }
#endif
    SnapshotOwnerToken owner_before{};
    std::string_view owner_reason="full_snapshot_application_main_owner_unqualified";
    if(!ReadCurrentSnapshotOwner(owner_before,&owner_reason)) {
      diagnostics.stage=owner_reason=="full_snapshot_application_main_owner_unqualified"?"owner":"ingame";
      diagnostics.reason=owner_reason;
      return finish(false);
    }
#if defined(XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
#if defined(XAR_CK3_ENABLE_26757580_ARMY_FULL58)
    MilitaryOwnerScope58 military_owner{};
#endif
    if(current.enable_army_base) {
      if(current.army_fixture_access.context || current.army_fixture_access.copy) {
        diagnostics.stage="binding";diagnostics.reason="full_snapshot_live_fixture_access_rejected";
        return finish(false);
      }
      current.army_base.player_armies.integration_native_calls_permitted=true;
#if defined(XAR_CK3_ENABLE_26757580_ARMY_FULL58)
      if(ck3_1210::IsHotfix(core_.image_build)) {
        const auto &m=*owner_before.mailbox;
        military_owner={this,&current,owner_before,m.published_sequence.load(),m.executor.load(),m.executor_context,cause81};
        military_owner.observer92=xar::snapshot_observer92::ReadScope::Capture(*this,m);
        current.army_base.player_armies.native_call_admission=&AdmitMilitaryState58;
        current.army_base.player_armies.native_call_admission_context=&military_owner;
        if(!AdmitMilitaryState58(&military_owner)) {
          diagnostics.stage="owner";diagnostics.reason="full_snapshot_military_ticket_unqualified";return finish(false);
        }
      }
#endif
    }
#endif
    bool result=ck3_1210::ReadFullSnapshotV1(current,output,diagnostics,ingame_ready_witness_);
    // The owner brackets every Full observation, including zero Army calls
    // and the legacy typed-empty lane. No stale complete diagnostic survives.
    SnapshotOwnerToken owner_after{};
    if(!ReadCurrentSnapshotOwner(owner_after) || owner_before!=owner_after || (result && !owner_after.Matches(output))) {
      output={};diagnostics.complete=false;diagnostics.stage="owner";
      diagnostics.reason="full_snapshot_application_main_owner_changed";result=false;
    }
    return finish(result);
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
    if(core_only_26785313_)return false; // Only the ticketed current-image reader can serve this profile.
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
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
  struct IngameReadyOwnerIdentity {
    const ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
    std::uint32_t thread_id=0;
    std::uintptr_t tls=0,state=0,jomini=0;
    friend bool operator==(const IngameReadyOwnerIdentity&,const IngameReadyOwnerIdentity&)=default;
  };
  struct SnapshotOwnerToken {
    const ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
    std::uint64_t pump_epoch=0;
    std::uint32_t thread_id=0;
    std::uintptr_t tls=0,state=0,jomini=0,data=0,characters=0;
    std::int32_t date_raw=0,speed=0,player=-1,actor=-1;
    bool paused=false,map_ready=false,has_actor=false,actor_alive=false;
    ck3_1210::IngameReadyGraphV1 ingame{};
    bool Matches(const Snapshot &p) const noexcept {
      return p.date_raw==date_raw && p.speed==speed && p.paused==paused && p.player_id==player &&
        p.map_ready==map_ready && p.has_played_character==has_actor && p.played_character_id==actor &&
        p.played_character_alive==actor_alive;
    }
    friend bool operator==(const SnapshotOwnerToken&,const SnapshotOwnerToken&)=default;
  };
#if defined(XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
#include "military_owner58.inc"
#endif
  bool MarkSnapshotOwnerUnavailable() const noexcept {
    // A rejected worker never reads the lifecycle graph or mutates its witness.
    // Only the next qualified owner consumes this request and resets state.
    ingame_owner_reset_requested_.store(true,std::memory_order_release);return false;
  }
  bool ReadCurrentSnapshotOwner(SnapshotOwnerToken &out,std::string_view *reason=nullptr) const noexcept {
    out={};
    if(reason)*reason="full_snapshot_application_main_owner_unqualified";
    const auto *m=owner_mailbox_.load(std::memory_order_acquire);
    if(!m || m->offline_fixture || m->stop_requested.load() || m->proof_reset_requested.load())return MarkSnapshotOwnerUnavailable();
    __try {
      const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
      if(!base || m->module_base!=base || m->game_state_slot!=reinterpret_cast<std::uintptr_t>(core_.game_state_slot) ||
          m->jomini_state_slot!=reinterpret_cast<std::uintptr_t>(core_.jomini_state_slot) ||
          m->tls_initialized_flag!=base+ck3_1210::ImageRva(core_.image_build,ck3_1210::kMainThreadTlsInitializedFlagRva,ck3_1210::hotfix26757580::kTlsFlag) ||
          reinterpret_cast<std::uintptr_t>(m->tls_context_getter)!=base+ck3_1210::ImageRva(core_.image_build,ck3_1210::kMainThreadTlsContextGetterRva,ck3_1210::hotfix26757580::kTlsGetter))return MarkSnapshotOwnerUnavailable();
      const auto d=ck3_11906::ReadMainThreadQueryMailboxDiagnosticsV1(*m);
      const auto tid=GetCurrentThreadId();
      if((!d.iat_installed && !d.sdl_poll_event_hook_installed) || d.stop_requested || d.failure_flags ||
          d.owner_thread_id!=tid || d.observed_current_thread_id!=tid || !d.active_hook_calls ||
          !d.observed_stamp_read_success || d.observed_tls_initialized!=1 ||
          d.observed_tls_main_thread_marker!=1 || !d.observed_paused || !d.observed_tls_context ||
          d.paused_owner_verified_pump_epochs<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
          d.owner_verified_pump_epochs<ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs)return MarkSnapshotOwnerUnavailable();
      const auto tls=reinterpret_cast<std::uintptr_t>(m->tls_context_getter());
      if(tls!=d.observed_tls_context || *reinterpret_cast<const std::uint8_t *>(m->tls_initialized_flag)!=1 ||
          *reinterpret_cast<const std::uint8_t *>(tls+0x20)!=1)return MarkSnapshotOwnerUnavailable();
      void *state=nullptr,*jomini=nullptr;
      ck3_1210::IngameReadyObservationV1 ingame{};
      if(!ck3_1210::IsHotfix(core_.image_build)) {
      const auto &ready_core=full_.ingame_ready.core;
      if(!full_.ingame_ready.exact_build_admitted || ready_core.game_state_slot!=core_.game_state_slot ||
          ready_core.jomini_state_slot!=core_.jomini_state_slot ||
          ready_core.character_storage_slot!=core_.character_storage_slot ||
          ready_core.get_local_player!=core_.get_local_player)return MarkSnapshotOwnerUnavailable();
      std::memcpy(&state,core_.game_state_slot,sizeof(state));std::memcpy(&jomini,core_.jomini_state_slot,sizeof(jomini));
      const IngameReadyOwnerIdentity identity{m,tid,tls,reinterpret_cast<std::uintptr_t>(state),
        reinterpret_cast<std::uintptr_t>(jomini)};
      if(ingame_owner_reset_requested_.exchange(false,std::memory_order_acq_rel) ||
          identity!=ingame_ready_owner_ || d.pump_epochs<ingame_ready_owner_pump_ ||
          d.owner_verified_pump_epochs<ingame_ready_owner_verified_)ingame_ready_witness_={};
      ingame_ready_owner_=identity;ingame_ready_owner_pump_=d.pump_epochs;
      ingame_ready_owner_verified_=d.owner_verified_pump_epochs;
      if(!ck3_1210::ObserveIngameReadyV1(full_.ingame_ready,ingame_ready_witness_,ingame)) {
        if(reason)*reason=ingame.unavailable_reason;
        // A valid first graph must retain its baseline until a real frame ends.
        return false;
      }
      if(ingame.graph.root!=jomini) {ingame_ready_witness_={};return MarkSnapshotOwnerUnavailable();}
      } else {
      std::memcpy(&state,core_.game_state_slot,sizeof(state));std::memcpy(&jomini,core_.jomini_state_slot,sizeof(jomini));
        // BB3 basic Full does not claim the original-image lifecycle witness.
        ingame_ready_witness_={};
      }
      void *data=nullptr,*characters=nullptr;
      std::memcpy(&data,static_cast<const std::byte *>(state)+ck3_1210::kGameStateDataOffset,sizeof(data));
      if(core_.character_storage_slot)std::memcpy(&characters,core_.character_storage_slot,sizeof(characters));
      ck3_1210::CoreSnapshotPrefix p{};
      const bool valid=ck3_1210::ReadCoreSnapshot(core_,p) && p.clock.paused && p.clock.date_raw==d.observed_date_raw &&
          reinterpret_cast<std::uintptr_t>(state)==d.observed_game_state &&
          reinterpret_cast<std::uintptr_t>(jomini)==d.observed_jomini_state &&
          *core_.game_state_slot==state && *core_.jomini_state_slot==jomini &&
          *reinterpret_cast<void *const *>(static_cast<const std::byte *>(state)+ck3_1210::kGameStateDataOffset)==data &&
          (!core_.character_storage_slot || *core_.character_storage_slot==characters) &&
          m->module_base==base &&
          m->tls_initialized_flag==base+ck3_1210::ImageRva(core_.image_build,ck3_1210::kMainThreadTlsInitializedFlagRva,ck3_1210::hotfix26757580::kTlsFlag) &&
          reinterpret_cast<std::uintptr_t>(m->tls_context_getter)==base+ck3_1210::ImageRva(core_.image_build,ck3_1210::kMainThreadTlsContextGetterRva,ck3_1210::hotfix26757580::kTlsGetter) &&
          *reinterpret_cast<const std::uint8_t *>(m->tls_initialized_flag)==1 &&
          reinterpret_cast<std::uintptr_t>(m->tls_context_getter())==tls &&
          *reinterpret_cast<const std::uint8_t *>(tls+0x20)==1 &&
          owner_mailbox_.load(std::memory_order_acquire)==m &&
          m->pump_epochs.load()==d.pump_epochs && m->owner_thread_id.load()==tid &&
          m->active_hook_calls.load()!=0 && m->failure_flags.load()==0 &&
          !m->stop_requested.load() && !m->proof_reset_requested.load();
      if(!valid)return MarkSnapshotOwnerUnavailable();
      out={m,d.pump_epochs,tid,tls,d.observed_game_state,d.observed_jomini_state,
        reinterpret_cast<std::uintptr_t>(data),reinterpret_cast<std::uintptr_t>(characters),d.observed_date_raw,
        p.clock.speed,p.local_player_id,p.played_character_id,p.clock.paused,p.map_ready,p.has_played_character,p.played_character_alive,
        ingame.graph};
      return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) {return MarkSnapshotOwnerUnavailable();}
  }
  mutable std::atomic<bool> ingame_owner_reset_requested_{true};
  mutable ck3_1210::IngameReadyWitnessV1 ingame_ready_witness_{};
  mutable IngameReadyOwnerIdentity ingame_ready_owner_{};
  mutable std::uint64_t ingame_ready_owner_pump_=0,ingame_ready_owner_verified_=0;
#endif
  mutable std::atomic<const ck3_11906::MainThreadQueryMailboxV1 *> owner_mailbox_{nullptr};
  ck3_1210::CoreBindings core_{};
  ck3_1210::FullSnapshotBindingsV1 full_{};
  bool core_only_26785313_=false;
  mutable std::mutex diagnostic_mutex_;
  mutable ck3_1210::FullSnapshotDiagnosticsV1 diagnostics_{};
};
} // namespace

bool BindCk3_1210SnapshotOwnerMailbox(const GameAdapter &game,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept {
  const auto *florin=dynamic_cast<const FlorinAdapter *>(&game);
  if(!florin || !florin->enabled() || !IsCk3_1210BasicDescriptor(game.descriptor()))return false;
  florin->BindSnapshotOwner(mailbox);return true;
}

const AdapterDescriptor &Ck3_121003Core26785313AdapterDescriptor() noexcept {
  namespace current=ck3_121003::build26785313;
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
  static constexpr std::array<std::string_view,1> caps{ck3_1210::kCoreFrameCapabilityV1};
#else
  static constexpr std::array<std::string_view,0> caps{};
#endif
  static const AdapterDescriptor descriptor{current::kAdapterId,current::kGameVersion,
      current::kExecutableSha256,"xar_checkpoint",caps};
  return descriptor;
}

const AdapterDescriptor &Ck3_1210AdapterDescriptor() noexcept {
#if defined(XAR_CK3_ENABLE_1210_CORE_FRAME_V1)
  static constexpr std::string_view capabilities[]{
      ck3_1210::kCoreFrameCapabilityV1,
#if defined(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1)
      ck3_1210::kCharacterRosterCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
      ck3_1210::kActiveWarsIdentityCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
      "game.state.snapshot", "game.query.fresh-full-state.v1",
#if defined(XAR_CK3_ENABLE_1210_EVENT_OPTIONS_V1)
      ck3_1210::kEventOptionsQueryCapabilityV1,ck3_1210::kEventOptionsSelectCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_GUI_CONTROL_V1)
      ck3_1210::kGuiControlQueryCapabilityV1,ck3_1210::kGuiControlActivateCapabilityV1,
      ck3_1210::kToastQueryCapabilityV1,"game.command.query-current-interface-toast-v1",
      "game.command.query-scripted-widget-controls-v1","game.command.activate-scripted-widget-control-v1",
#endif
#endif
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_GOLD_V1)
      ck3_1210::kPersonalGoldCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
      ck3_1210::kPersonalCashCapabilityV1,
#if defined(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V2)
      ck3_1210::kPersonalCashCapabilityV2,
#endif
#endif
#if defined(XAR_CK3_ENABLE_1210_ACTOR_FOUNDATION_V1)
      ck3_1210::kActorFoundationCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
      ck3_1210::kActorResourceLeafCapabilityV2,
#endif
#if defined(XAR_CK3_ENABLE_1210_CORE_CONTROL_V1)
      ck3_1210::kCoreControlCapabilityV1,
#if !defined(XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1)
      "game.command.pause-map", "game.command.resume-map",
      "game.command.set-speed-1", "game.command.set-speed-2", "game.command.set-speed-3",
      "game.command.set-speed-4", "game.command.set-speed-5", "game.command.save-checkpoint",
#elif defined(XAR_CK3_ENABLE_1210_FULL_CLOCK_V1)
      ck3_1210::kFullClockControlCapabilityV1,
#if defined(XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1)
      ck3_1210::kDateSentinelCapabilityV1,
      "game.command.research-arm-tactical-daily-sentinel-v1-N",
      "game.command.research-query-tactical-daily-sentinel-v1",
      "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
      "game.command.resume-map",
#endif
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

const AdapterDescriptor &Ck3_1210Hotfix26757580AdapterDescriptor() noexcept {
#if defined(XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
  static constexpr std::string_view caps[]{
    ck3_1210::kCoreFrameCapabilityV1,"game.state.snapshot","game.query.fresh-full-state.v1",
    ck3_1210::kCoreControlCapabilityV1,ck3_1210::kFullClockControlCapabilityV1,
    ck3_1210::kDateSentinelCapabilityV1,
    "game.command.pause-map","game.command.resume-map",
    "game.command.set-speed-1","game.command.set-speed-2","game.command.set-speed-3",
    "game.command.set-speed-4","game.command.set-speed-5",
    "game.command.research-arm-tactical-daily-sentinel-v1-N",
    "game.command.research-query-tactical-daily-sentinel-v1",
    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
    ck3_1210::kApplicationExitCapabilityV1
#if defined(XAR_CK3_ENABLE_26757580_ARMY_FULL58)
    ,ck3_1210::kArmyBaseHotfixFullCapability58
#endif
#if defined(XAR_CK3_ENABLE_26757580_WAR_IDENTITY58)
    ,ck3_1210::kActiveWarsHotfixCapability58
#endif
#if defined(XAR_CK3_ENABLE_26757580_OPENING_READONLY56)
    ,ck3_1210::kOpeningScopeCapability56,ck3_1210::kOpeningCurrentCapability56
#endif
#if defined(XAR_CK3_ENABLE_26757580_SAVE_MAPPED61)
    ,"game.command.save-checkpoint"
#endif
#if defined(XAR_CK3_ENABLE_1210_HOTFIX_26757580_PERSONAL_CASH_V2)
    ,ck3_1210::kPersonalCashCapabilityV2
#endif
    };
#else
  static constexpr std::array<std::string_view,0> caps{};
#endif
  static const AdapterDescriptor d{ck3_1210::hotfix26757580::kAdapterId,ck3_1210::kGameVersion,
    ck3_1210::hotfix26757580::kExecutableSha256,"xar_checkpoint",caps};
  return d;
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
  namespace current=ck3_121003::build26785313;
  // The selected current-process hash is uppercase. Keep the old factories and
  // ImageBuildForSha unchanged: this is a separate Core-only descriptor.
  if(executable_sha256==current::kExecutableSha256) {
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    core=current::BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        executable_sha256).core;
#endif
    return std::make_unique<FlorinAdapter>(core,ck3_1210::FullSnapshotBindingsV1{},true);
  }
#if !defined(XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
  if(executable_sha256==ck3_1210::hotfix26757580::kExecutableSha256) {
    core.image_build=ck3_1210::ImageBuildV1::hotfix26757580;
    return CreateCk3_1210AdapterFromBindings(core);
  }
#endif
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

namespace xar::diagnostic81 {
bool ReadFlorinSnapshotForRequest(const game::GameAdapter &adapter,game::Snapshot &output,
                                 RawFullCause &cause) noexcept {
  const auto *native=dynamic_cast<const game::FlorinAdapter *>(&adapter);
  if(!native)return false;
  cause.exact_reader=true;cause.attempted=true;
  const bool available=native->ReadSnapshotWithRequestCause81(output,&cause);
  cause.returned=true;cause.available=available;
  return available;
}
} // namespace xar::diagnostic81
