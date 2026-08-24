#include "xar_bridge/ck3_11906_adapter.hpp"
#include "xar_bridge/game_adapter.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <span>
#include <string_view>
#include <vector>

namespace {

using xar::game::AdapterDescriptor;
using xar::game::GameAdapter;

constexpr std::array<std::string_view, 1> kPreferredCapabilities{
    "fixture.preferred",
};
constexpr AdapterDescriptor kPreferredDescriptor{
    "fixture-preferred",
    "fixture.1",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "fixture_checkpoint",
    kPreferredCapabilities,
};

constexpr std::array<std::string_view, 3> kFutureCapabilities{
    "game.state.snapshot",
    "game.command.pause-map",
    "game.command.preview-move-army-N-to-N",
};
constexpr AdapterDescriptor kFutureDescriptor{
    "fixture-future",
    "fixture.2",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "fixture_checkpoint_v2",
    kFutureCapabilities,
};

class StubAdapter final : public GameAdapter {
public:
  StubAdapter(const AdapterDescriptor &descriptor, bool enabled) noexcept
      : descriptor_(descriptor), enabled_(enabled) {}

  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return enabled_; }
  bool read_snapshot(xar::game::Snapshot &) const noexcept override {
    return false;
  }
  xar::game::PauseSubmitResult submit_pause_map() const noexcept override {
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult submit_resume_map() const noexcept override {
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
  bool read_declarable_wars(
      std::vector<xar::game::DeclarableWarSnapshot> &) const noexcept override {
    return false;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &,
      xar::game::ArrangeMarriageQueryDiagnostics &) const noexcept override {
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

private:
  const AdapterDescriptor &descriptor_;
  bool enabled_;
};

std::unique_ptr<GameAdapter>
CreateDisabledPreferred(std::string_view) noexcept {
  return std::make_unique<StubAdapter>(kPreferredDescriptor, false);
}

std::unique_ptr<GameAdapter>
CreateDisabledFuture(std::string_view) noexcept {
  return std::make_unique<StubAdapter>(kFutureDescriptor, false);
}

std::unique_ptr<GameAdapter>
CreateEnabledFuture(std::string_view executable_sha256) noexcept {
  return std::make_unique<StubAdapter>(
      kFutureDescriptor, executable_sha256 == "fixture-future-hash");
}

int Fail(std::string_view message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

bool Contains(std::span<const std::string_view> values,
              std::string_view expected) {
  return std::find(values.begin(), values.end(), expected) != values.end();
}

} // namespace

int main() {
  const auto &known = xar::game::Ck3_11906AdapterDescriptor();
  if (known.adapter_id != "ck3-1.19.0.6-msvc-x64" ||
      known.game_version != "1.19.0.6" ||
      known.executable_sha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      known.checkpoint_save_name != "xar_checkpoint") {
    return Fail("known CK3 build descriptor drifted");
  }
  if (!Contains(known.capabilities, "game.state.snapshot") ||
      !Contains(known.capabilities,
                "game.state.xar-one-life-settlement") ||
      !Contains(known.capabilities, "game.state.war-primary-opponent") ||
      !Contains(known.capabilities, "game.state.war-objectives") ||
      !Contains(known.capabilities, "game.state.army-routes") ||
      !Contains(known.capabilities,
                "game.command.preview-move-army-N-to-N") ||
      !Contains(known.capabilities, "game.command.declare-war-N") ||
      !Contains(known.capabilities,
                "game.command.query-arrange-marriage-choices") ||
      !Contains(known.capabilities, "game.adapter.minimized-headless")) {
    return Fail("known adapter omitted a required semantic capability");
  }
  for (auto left = known.capabilities.begin(); left != known.capabilities.end();
       ++left) {
    if (std::find(left + 1, known.capabilities.end(), *left) !=
        known.capabilities.end()) {
      return Fail("known adapter advertised a duplicate capability");
    }
  }

  StubAdapter partial(kFutureDescriptor, true);
  if (!partial.supports("game.state.snapshot") ||
      !partial.supports("game.command.pause-map") ||
      partial.supports("game.state.war-primary-opponent") ||
      partial.supports("game.state.war-objectives") ||
      partial.supports("game.command.declare-war-N") ||
      !partial.supports_snapshot() || !partial.supports_step("pause-map") ||
      !partial.supports_step("preview-move-army-1-to-2") ||
      partial.supports_step("declare-war-99-1-0") ||
      partial.supports_step("unsupported-step")) {
    return Fail("capability lookup did not use the selected adapter set");
  }
  StubAdapter disabled(kFutureDescriptor, false);
  if (disabled.supports("game.state.snapshot")) {
    return Fail("disabled adapter exposed gameplay capabilities");
  }

  constexpr std::array<xar::game::AdapterFactory, 2> with_future{
      &CreateDisabledPreferred,
      &CreateEnabledFuture,
  };
  auto selected =
      xar::game::SelectAdapter("fixture-future-hash", with_future);
  if (selected == nullptr || !selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-future") {
    return Fail("registry did not select a later enabled build adapter");
  }
  selected = xar::game::SelectAdapter("unknown-fixture-hash", with_future);
  if (selected == nullptr || selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-preferred") {
    return Fail("registry did not pass executable identity to adapters");
  }

  constexpr std::array<xar::game::AdapterFactory, 2> unknown_build{
      &CreateDisabledPreferred,
      &CreateDisabledFuture,
  };
  selected = xar::game::SelectAdapter("fixture-hash", unknown_build);
  if (selected == nullptr || selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-preferred" ||
      selected->supports("fixture.preferred")) {
    return Fail("unknown build did not retain an unsupported preferred adapter");
  }

  constexpr std::array<xar::game::AdapterFactory, 0> no_adapters{};
  if (xar::game::SelectAdapter("fixture-hash", no_adapters) != nullptr) {
    return Fail("empty adapter registry did not return null");
  }

  auto current = xar::game::SelectCurrentProcessAdapter();
  if (current == nullptr || current->enabled() ||
      current->descriptor().adapter_id != known.adapter_id ||
      current->supports("game.state.snapshot")) {
    return Fail("unknown current test executable exposed CK3 gameplay");
  }

  std::cout << "PASS: known_descriptor=1 adapter_capability_set=1 "
               "unknown_build_unsupported=1 future_adapter_registry=1 "
               "empty_registry=1\n";
  return 0;
}
