#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
// Reuse the real, bounded War/Core RAM model. Neither Game nor its EXE runs.
#define main ActiveWarsProviderLegacyFixtureMainV1
#include "ck3_1210_active_wars_v1_test.cpp"
#undef main
#include <windows.h>
#include <filesystem>
#include <fstream>
namespace {
using namespace xar::game;
using namespace xar::ck3_11906;
class WarFrameAdapter final : public GameAdapter {
public:
  using Reader = bool (*)(void *, Snapshot &) noexcept;
  WarFrameAdapter(const AdapterDescriptor &d, Reader reader = nullptr, void *context = nullptr)
      : descriptor_(d), reader_(reader), context_(context) {}
  mutable unsigned snapshot_calls = 0;
  bool adapter_enabled = true;
  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return adapter_enabled; }
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    ++snapshot_calls;
    if (reader_ == nullptr) { output = {}; return false; }
    return reader_(context_, output);
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
private:
  const AdapterDescriptor &descriptor_;
  Reader reader_ = nullptr;
  void *context_ = nullptr;
};
void RequireFrame(bool ok,const char *why){if(!ok){std::cerr<<why<<std::endl;std::exit(1);}}
struct WarFrameFixture {
  Fixture ram;
  const std::array<std::string_view,1> capabilities{kActiveWarsIdentityCapabilityV1};
  const AdapterDescriptor descriptor{kAdapterId,kGameVersion,kExecutableSha256,"NoGame-War-frame",capabilities};
  WarFrameAdapter adapter{descriptor};
  MainThreadQueryMailboxV1 mailbox{};
  PersonalGoldMailboxContextV1 parent{};
  ActiveWarsMailboxContextV1 query{};
  MainThreadExecutionStampV1 stamp{};
  bool change_owner_after_score=false,owner_changed=false;
  WarFrameFixture() {
    query.bindings=ram.bindings;query.fixture_access={this,&Copy};
    parent.kind=ActorObservationKindV1::active_wars;parent.wars=&query;
    parent.game=&adapter;parent.mailbox=&mailbox;parent.ticket.sequence=7;
    parent.bindings=BindPersonalGoldImageV1(0x140000000,kExecutableSha256);
    parent.bindings.core=ram.bindings.core;
    const auto expected=ram.Expected();
    stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=3;
    stamp.tls_initialized=1;stamp.tls_main_thread_marker=1;stamp.tls_context=1;
    stamp.game_state=reinterpret_cast<std::uintptr_t>(ram.game_slot);
    stamp.jomini_state=reinterpret_cast<std::uintptr_t>(ram.jomini_slot);
    stamp.date_raw=expected.clock.date_raw;stamp.paused=true;
    mailbox.offline_fixture=true;mailbox.iat_hook_installed.store(true);
    mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
    mailbox.owner_thread_id.store(stamp.thread_id);mailbox.paused_owner_verified_pump_epochs.store(2);
    mailbox.published_sequence.store(7);mailbox.executor_started_sequence.store(7);
    mailbox.executor_started_pump_epoch.store(stamp.pump_epoch);
    mailbox.executor_context=&parent;mailbox.executor.store(&ExecutePersonalGoldMailboxV1);
  }
  static bool Copy(void *opaque,const void *source,void *dest,std::size_t size) noexcept {
    auto &f=*static_cast<WarFrameFixture *>(opaque);
    if(f.change_owner_after_score && native_calls!=0 && !f.owner_changed) {
      f.owner_changed=true;f.mailbox.stop_requested.store(true);
    }
    return Fixture::Copy(&f.ram,source,dest,size);
  }
  std::string Run(std::string_view request) {
    RequireFrame(ExecutePersonalGoldMailboxV1(&parent,stamp),"actual Actor MQ callback completes");
    RequireFrame(!query.bindings.integration_native_calls_permitted,"shared score permission remains OFF");
    RequireFrame(adapter.snapshot_calls==0,"standalone query never invokes Full reader");
    return SerializeActiveWarsIdentityCommandResultV1(request,query);
  }
};
void Emit(const std::filesystem::path &dir,const char *name,const std::string &packet) {
  if(dir.empty())return;
  std::ofstream file(dir/name,std::ios::binary);file.write(packet.data(),static_cast<std::streamsize>(packet.size()));
  RequireFrame(static_cast<bool>(file),"write actual C++ reader-produced fixture packet");
}
void Known(const WarFrameFixture &f){RequireFrame(f.query.application_main_observed && f.query.observation.identity_complete &&
    f.query.observation.available && f.query.observation.active_wars.has_value(),"real frame owns complete identity");}
}
int main(int argc,char **argv) {
  RequireFrame(argc<=2,"optional output directory only");
  const std::filesystem::path dir=argc==2?std::filesystem::path(argv[1]):std::filesystem::path{};
  if(!dir.empty())std::filesystem::create_directories(dir);
  {
    WarFrameFixture f;f.ram.Populate();const auto packet=f.Run("war-attacker");Known(f);
    RequireFrame(f.query.observation.score_complete && native_calls==2 && !wrong_native_abi,"actual guarded native score ABI used twice");
    RequireFrame(packet.find("\"rich\":{\"targeted_title_ids\":{\"status\":\"unavailable\"")!=std::string::npos,"rich is unavailable, never fake empty");
    Emit(dir,"war-attacker.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.ram.Defender();const auto packet=f.Run("war-defender");Known(f);
    RequireFrame(f.query.observation.active_wars->front().player_relative_war_score==-17,"defender checked sign");
    Emit(dir,"war-defender.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.ram.war_a.Put(8,std::int32_t{0});
    f.ram.war_a.Put(0x30,std::int32_t{3});f.ram.war_a.Put(0x34,std::int32_t{3});score_a=0;
    const auto packet=f.Run("war-zero-duplicates");Known(f);
    RequireFrame(f.query.observation.active_wars->front().attacker_participant_ids==std::vector<std::int32_t>{Fixture::player,0,Fixture::player},"ordered full IDs including zero/duplicates preserved");
    Emit(dir,"war-zero-duplicates.json",packet);
  }
  {
    WarFrameFixture f;const auto packet=f.Run("war-empty");Known(f);
    RequireFrame(f.query.observation.active_wars->empty() && native_calls==0,"valid typed zero-capacity absence");
    Emit(dir,"war-empty.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.ram.Defender();score_a=(std::numeric_limits<std::int32_t>::min)();
    const auto packet=f.Run("war-score-overflow");Known(f);
    RequireFrame(!f.query.observation.score_complete && f.query.observation.active_wars->front().native_attacker_score_raw==score_a &&
        !f.query.observation.active_wars->front().player_relative_war_score,"overflow retains real raw score and no relative");
    Emit(dir,"war-score-overflow.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.ram.guard_valid=false;const auto packet=f.Run("war-score-guard");Known(f);
    RequireFrame(!f.query.observation.score_complete && native_calls==0,"bad guard means zero score calls");
    Emit(dir,"war-score-guard.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();score_drifts=true;const auto packet=f.Run("war-score-changed");Known(f);
    RequireFrame(!f.query.observation.active_wars->front().native_attacker_score_raw &&
        f.query.observation.active_wars->front().score_unavailable_reason=="active_wars_score_changed","score drift unavailable without losing identity");
    Emit(dir,"war-score-changed.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.mailbox.executor_started_sequence.store(8);const auto packet=f.Run("war-owner-unavailable");
    RequireFrame(!f.query.observation.available && native_calls==0 && packet.find("\"active_wars\":null")!=std::string::npos,"owner failure never manufactures empty wars");
    Emit(dir,"war-owner-unavailable.json",packet);
  }
  {
    WarFrameFixture f;f.ram.Populate();f.change_owner_after_score=true;const auto packet=f.Run("war-owner-changed");
    RequireFrame(!f.query.observation.available && native_calls==1 && f.query.observation.native_score_calls_attempted==1,"per-call admission stops second score after owner change");
    Emit(dir,"war-owner-changed.json",packet);
  }
  std::cout<<"PASS real War-only -> Actor MQ -> independent partial DATA NoGame fixture; no Full/Root/action qualification"<<std::endl;
  return 0;
}
