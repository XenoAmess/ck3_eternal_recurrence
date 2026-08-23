#include "xar_bridge/ck3_11906_adapter.hpp"

#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <memory>

namespace xar::game {
namespace {

constexpr std::array<std::string_view, 29> kCapabilities{
    "game.state.snapshot",
    "game.state.map-ready",
    "game.state.played-character",
    "game.state.active-event",
    "game.state.pending-character-interaction",
    "game.state.active-wars",
    "game.state.war-primary-opponent",
    "game.state.player-armies",
    "game.command.pause-map",
    "game.command.resume-map",
    "game.command.set-speed-1",
    "game.command.set-speed-2",
    "game.command.set-speed-3",
    "game.command.set-speed-4",
    "game.command.set-speed-5",
    "game.command.select-event-option-N",
    "game.command.save-checkpoint",
    "game.command.accept-pending-character-interaction",
    "game.command.reject-pending-character-interaction",
    "game.command.raise-troops-default",
    "game.command.move-army-N-to-N",
    "game.command.disband-army-N",
    "game.command.query-declarable-wars",
    "game.command.declare-war-N",
    "game.command.enforce-demands-N",
    "game.command.query-arrange-marriage-choices",
    "game.command.arrange-marriage-N",
    "game.adapter.exact-build",
    "game.adapter.minimized-headless",
};

const AdapterDescriptor kDescriptor{
    "ck3-1.19.0.6-msvc-x64",
    "1.19.0.6",
    ck3_11906::kExecutableSha256,
    ck3_11906::kCheckpointSaveName,
    kCapabilities,
};

class Ck3_11906Adapter final : public GameAdapter {
public:
  explicit Ck3_11906Adapter(ck3_11906::Bindings bindings) noexcept
      : bindings_(bindings) {}

  const AdapterDescriptor &descriptor() const noexcept override {
    return kDescriptor;
  }
  bool enabled() const noexcept override { return bindings_.enabled; }
  bool read_snapshot(Snapshot &output) const noexcept override {
    return ck3_11906::ReadSnapshot(bindings_, output);
  }
  PauseSubmitResult submit_pause_map() const noexcept override {
    return ck3_11906::SubmitPauseMap(bindings_);
  }
  ResumeSubmitResult submit_resume_map() const noexcept override {
    return ck3_11906::SubmitResumeMap(bindings_);
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    return ck3_11906::SubmitSetSpeed(bindings_, speed);
  }
  SelectEventOptionResult
  submit_select_event_option(std::int32_t option_index) const noexcept override {
    return ck3_11906::SubmitSelectEventOption(bindings_, option_index);
  }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    return ck3_11906::SubmitSaveCheckpoint(bindings_);
  }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction(
      PendingInteractionReply reply) const noexcept override {
    return ck3_11906::SubmitReplyToPendingInteraction(bindings_, reply);
  }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override {
    return ck3_11906::SubmitRaiseTroopsDefault(bindings_);
  }
  MoveArmyResult submit_move_army(std::int32_t army_id,
                                  std::int32_t province_id) const
      noexcept override {
    return ck3_11906::SubmitMoveArmy(bindings_, army_id, province_id);
  }
  DisbandArmyResult
  submit_disband_army(std::int32_t army_id) const noexcept override {
    return ck3_11906::SubmitDisbandArmy(bindings_, army_id);
  }
  bool read_declarable_wars(
      std::vector<DeclarableWarSnapshot> &output) const noexcept override {
    return ck3_11906::ReadDeclarableWars(bindings_, output);
  }
  DeclareWarResult submit_declare_war(
      const DeclarableWarSnapshot &declaration) const noexcept override {
    return ck3_11906::SubmitDeclareWar(bindings_, declaration);
  }
  ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<ArrangeMarriageChoice> &output,
      ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    return ck3_11906::ReadArrangeMarriageChoices(bindings_, output,
                                                  diagnostics);
  }
  ArrangeMarriageResult submit_arrange_marriage(
      const ArrangeMarriageChoice &choice) const noexcept override {
    return ck3_11906::SubmitArrangeMarriage(bindings_, choice);
  }
  EnforceDemandsResult
  submit_enforce_demands(std::int32_t war_id) const noexcept override {
    return ck3_11906::SubmitEnforceDemands(bindings_, war_id);
  }

private:
  ck3_11906::Bindings bindings_;
};

} // namespace

const AdapterDescriptor &Ck3_11906AdapterDescriptor() noexcept {
  return kDescriptor;
}

std::unique_ptr<GameAdapter>
CreateCk3_11906Adapter(std::string_view executable_sha256) noexcept {
  return std::make_unique<Ck3_11906Adapter>(
      ck3_11906::BindCurrentProcess(
          executable_sha256 == kDescriptor.executable_sha256));
}

} // namespace xar::game
