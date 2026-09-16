#include "xar_bridge/current_timeline_blocker_context_v1.hpp"

#include <array>
#include <cassert>
#include <string>

namespace {

using namespace xar::ck3_11906;

struct Fixture {
  std::array<CurrentTimelineWidgetObservationV1,
             kCurrentTimelineFixedWidgetCountV1>
      widgets{};
  bool readable = true;
};

bool Observe(void *opaque, CurrentTimelineFixedWidgetV1 identity,
             CurrentTimelineWidgetObservationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (!fixture.readable)
    return false;
  output = fixture.widgets[static_cast<std::size_t>(identity)];
  return true;
}

void Visible(Fixture &fixture, CurrentTimelineFixedWidgetV1 identity,
             bool enabled = true) {
  auto &widget = fixture.widgets[static_cast<std::size_t>(identity)];
  widget.exists = true;
  widget.effective_visible = true;
  widget.enabled = enabled;
}

xar::game::CurrentTimelineBlockerContextV1 Read(Fixture &fixture) {
  CurrentTimelineBlockerReadRequestV1 request{77, 53411568, true};
  CurrentTimelineBlockerSourceV1 source{&fixture, &Observe};
  xar::game::CurrentTimelineBlockerContextV1 output{};
  ReadCurrentTimelineBlockerContextV1(request, source, output);
  return output;
}

} // namespace

int main() {
  using Identity = xar::game::CurrentTimelineBlockerIdentityV1;
  using Status = xar::game::CurrentTimelineBlockerStatusV1;

  Fixture fixture{};
  auto output = Read(fixture);
  assert(output.status == Status::available &&
         output.identity == Identity::none);
  assert(!output.blocks_simulation.available && !output.can_continue.available);

  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_root);
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_bottom);
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_close);
  output = Read(fixture);
  assert(output.status == Status::available &&
         output.identity == Identity::death_succession_modal);
  assert(output.can_continue.available && output.can_continue.value);
  assert(!output.blocks_simulation.available);
  assert(output.evidence.decisive_widget_name == "close_button");
  auto serialized = SerializeCurrentTimelineBlockerContextV1(output);
  assert(serialized.find("\"identity\":\"death_succession_modal\"") !=
         std::string::npos);
  assert(serialized.find("\"blocks_simulation\":{\"status\":\"unavailable\"") !=
         std::string::npos);

  fixture = {};
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_root);
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_bottom);
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_menu);
  output = Read(fixture);
  assert(output.status == Status::available &&
         output.identity == Identity::game_over_modal);
  assert(output.can_continue.available && !output.can_continue.value);

  fixture = {};
  Visible(fixture, CurrentTimelineFixedWidgetV1::destiny_root);
  Visible(fixture, CurrentTimelineFixedWidgetV1::destiny_continue, false);
  Visible(fixture, CurrentTimelineFixedWidgetV1::destiny_cancel);
  output = Read(fixture);
  assert(output.status == Status::available &&
         output.identity == Identity::succession_select_destiny_modal);
  assert(output.can_continue.available && !output.can_continue.value);
  fixture
      .widgets[static_cast<std::size_t>(
          CurrentTimelineFixedWidgetV1::destiny_continue)]
      .enabled = true;
  output = Read(fixture);
  assert(output.can_continue.available && output.can_continue.value);

  fixture = {};
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_root);
  Visible(fixture, CurrentTimelineFixedWidgetV1::destiny_root);
  output = Read(fixture);
  assert(output.status == Status::unavailable &&
         output.unavailable_reason == "multiple_timeline_surfaces_visible");

  fixture = {};
  Visible(fixture, CurrentTimelineFixedWidgetV1::succession_root);
  output = Read(fixture);
  assert(output.status == Status::unavailable &&
         output.unavailable_reason == "succession_surface_semantics_ambiguous");

  fixture = {};
  fixture.readable = false;
  output = Read(fixture);
  assert(output.status == Status::unavailable &&
         output.unavailable_reason == "fixed_widget_observation_failed");

  CurrentTimelineBlockerReadRequestV1 invalid_request{77, 53411568, false};
  CurrentTimelineBlockerSourceV1 source{&fixture, &Observe};
  output = {};
  ReadCurrentTimelineBlockerContextV1(invalid_request, source, output);
  assert(output.status == Status::unavailable &&
         output.unavailable_reason == "invalid_query_boundary");

  std::uint64_t expected_revision = 0;
  assert(ParseCurrentTimelineBlockerContextV1Step(
      "query-current-timeline-blocker-context-v1"));
  assert(!ParseCurrentTimelineBlockerContextV1Step(
      "query-current-timeline-blocker-context-v2"));
  assert(ParseCurrentTimelineBlockerContextRequestV1(
      R"({"type":"execute_step","protocol_version":1,"request_id":"q","step":"query-current-timeline-blocker-context-v1","expected_revision":77})",
      expected_revision));
  assert(expected_revision == 77);
  assert(!ParseCurrentTimelineBlockerContextRequestV1(
      R"({"expected_revision":0})", expected_revision));
  assert(!ParseCurrentTimelineBlockerContextRequestV1(
      R"({"expected_revision":77,"expected_revision":78})",
      expected_revision));
}
