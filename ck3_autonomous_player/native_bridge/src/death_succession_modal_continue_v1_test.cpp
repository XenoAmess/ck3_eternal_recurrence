#include "xar_bridge/death_succession_modal_continue_v1.hpp"

#include <cassert>

namespace {

using namespace xar::ck3_11906;

struct Fixture {
  int controller = 1;
  bool resolve = true;
  bool open = true;
  bool close = true;
  std::uint32_t close_attempts = 0;
};

bool Resolve(void *opaque, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.resolve ? &fixture.controller : nullptr;
  return fixture.resolve;
}

bool Open(void *opaque, void *controller, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (controller != &fixture.controller) return false;
  output = fixture.open;
  return true;
}

bool Close(void *opaque, void *controller) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (controller != &fixture.controller) return false;
  ++fixture.close_attempts;
  return fixture.close;
}

xar::game::CurrentTimelineBlockerContextV1 Timeline() {
  xar::game::CurrentTimelineBlockerContextV1 value{};
  value.status = xar::game::CurrentTimelineBlockerStatusV1::available;
  value.snapshot_revision = 77;
  value.date_raw = 53'411'568;
  value.identity =
      xar::game::CurrentTimelineBlockerIdentityV1::death_succession_modal;
  value.blocks_simulation.available = true;
  value.blocks_simulation.value = true;
  value.has_open_succession.available = true;
  value.has_open_succession.value = true;
  value.can_continue.available = true;
  value.can_continue.value = true;
  return value;
}

xar::game::DeathSuccessionModalContinueReceiptV1 Run(
    Fixture &fixture,
    xar::game::CurrentTimelineBlockerContextV1 timeline = Timeline()) {
  DeathSuccessionModalContinueRequestV1 request{77, 53'411'568, 35'465};
  DeathSuccessionModalContinueSourceV1 source{
      &fixture, &Resolve, &Open, &Close};
  xar::game::DeathSuccessionModalContinueReceiptV1 receipt{};
  ExecuteDeathSuccessionModalContinueV1(request, timeline, source, receipt);
  return receipt;
}

} // namespace

int main() {
  using Status = xar::game::DeathSuccessionModalContinueStatusV1;
  Fixture fixture{};
  auto receipt = Run(fixture);
  assert(receipt.status == Status::submitted);
  assert(receipt.snapshot_revision == 77 &&
         receipt.date_raw == 53'411'568 &&
         receipt.played_character_id == 35'465);
  assert(receipt.identity_verified && receipt.can_continue_verified &&
         receipt.paused_by_succession_verified &&
         receipt.has_open_succession_verified &&
         receipt.controller_vtable_verified &&
         receipt.controller_open_verified);
  assert(receipt.close_invocations == 1 && fixture.close_attempts == 1);

  fixture = {};
  auto timeline = Timeline();
  timeline.blocks_simulation.value = false;
  receipt = Run(fixture, timeline);
  assert(receipt.status == Status::unavailable && fixture.close_attempts == 0 &&
         receipt.unavailable_reason == "not_paused_by_succession");

  fixture = {};
  timeline = Timeline();
  timeline.has_open_succession.value = false;
  receipt = Run(fixture, timeline);
  assert(receipt.status == Status::unavailable && fixture.close_attempts == 0 &&
         receipt.unavailable_reason ==
             "played_character_has_no_open_succession");

  fixture = {};
  fixture.open = false;
  receipt = Run(fixture);
  assert(receipt.status == Status::unavailable && fixture.close_attempts == 0 &&
         receipt.unavailable_reason == "succession_controller_not_open");

  fixture = {};
  fixture.close = false;
  receipt = Run(fixture);
  assert(receipt.status == Status::unavailable &&
         receipt.close_invocations == 0 && fixture.close_attempts == 1 &&
         receipt.unavailable_reason ==
             "succession_controller_close_dispatch_failed");

  DeathSuccessionModalContinueRequestV1 request{};
  assert(ParseDeathSuccessionModalContinueV1Step(
      "continue-death-succession-modal-v1"));
  assert(!ParseDeathSuccessionModalContinueV1Step("continue-modal"));
  assert(IsDeathSuccessionModalPrivateStepV1(
      "query-current-timeline-blocker-context-v1"));
  assert(IsDeathSuccessionModalPrivateStepV1(
      "continue-death-succession-modal-v1"));
  assert(!IsDeathSuccessionModalPrivateStepV1("pause-map"));
  assert(ParseDeathSuccessionModalContinueRequestV1(
      R"({"expected_revision":77,"expected_date_raw":53411568,"expected_played_character_id":35465})",
      request));
  assert(request.expected_snapshot_revision == 77 &&
         request.expected_date_raw == 53'411'568 &&
         request.expected_played_character_id == 35'465);
  assert(!ParseDeathSuccessionModalContinueRequestV1(
      R"({"expected_revision":0,"expected_date_raw":53411568,"expected_played_character_id":35465})",
      request));
}
