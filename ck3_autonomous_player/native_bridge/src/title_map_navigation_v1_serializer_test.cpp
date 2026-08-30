#include "xar_bridge/title_map_navigation_v1_serializer.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace {

void TestAssert(bool condition, const char *expression, int line) noexcept {
  if (condition) {
    return;
  }
  std::fprintf(stderr, "test assertion failed at line %d: %s\n", line,
               expression);
  std::fflush(stderr);
  std::_Exit(3);
}

#undef assert
#define assert(expression) TestAssert((expression), #expression, __LINE__)

xar::game::TitleMapNavigationCommandV1 Command(bool centered) {
  xar::game::TitleMapNavigationCommandV1 output{};
  output.request.expected_snapshot_revision = 17;
  output.request.title_key = "c_bianzhou";
  output.binding = {17, 53'182'008, true, true};
  output.title.key = "c_bianzhou";
  output.title.title_id = 0x01000002;
  output.title.tier_raw = 2;
  output.title.tier_key = "county";
  output.title.capital_province_id = 9'822;
  output.camera.bounds_extent = {10, 20, 30, 40};
  output.camera.map_x_adjustment = 3;
  output.camera.expected_position_xyz = {17.0F, 0.0F, 30.0F};
  output.camera.expected_zoom_value = 7.5F;
  output.camera.zoom_index = 1;
  output.camera.current_state = {17.0F, 0.0F, 30.0F, 7.5F, -0.0F, 1.0F};
  output.camera.target_state = output.camera.current_state;
  output.camera.settled = true;
  output.camera.target_write_blocked = false;
  output.initialized = true;
  output.dispatched = centered;
  output.status =
      centered
          ? xar::game::TitleMapNavigationCommandStatusV1::centered
          : xar::game::TitleMapNavigationCommandStatusV1::already_centered;
  return output;
}

} // namespace

int main() {
  auto centered = Command(true);
  const auto centered_json =
      xar::ck3_11906::SerializeTitleMapNavigationResultV1(centered, 29);
  assert(!centered_json.empty());
  assert(centered_json.find("\"status\":\"centered\"") !=
         std::string::npos);
  assert(centered_json.find("\"anchor_kind\":\"title_bounds_center\"") !=
         std::string::npos);
  assert(centered_json.find("\"bounds_extent\":[10,20,30,40]") !=
         std::string::npos);
  assert(centered_json.find("\"map_x_adjustment\":3") !=
         std::string::npos);
  assert(centered_json.find("\"snapshot_id\":\"native:17\"") !=
         std::string::npos);
  assert(centered_json.find("\"native_revision\":17") !=
         std::string::npos);
  assert(centered_json.find("\"sequence\":29,\"status\":\"dispatched\"") !=
         std::string::npos);
  assert(centered_json.find("\"expected_zoom_value\":7.5") !=
         std::string::npos);
  assert(centered_json.find(",-0.0,1") != std::string::npos);
  assert(centered_json.find("\"before_target_province_id\"") ==
         std::string::npos);
  assert(centered_json.find("\"after_target_province_id\"") ==
         std::string::npos);

  auto already = Command(false);
  already.title.capital_province_id.reset();
  const auto already_json =
      xar::ck3_11906::SerializeTitleMapNavigationResultV1(already, 0);
  assert(!already_json.empty());
  assert(already_json.find("\"status\":\"already_centered\"") !=
         std::string::npos);
  assert(already_json.find("\"capital_province_id\":null") !=
         std::string::npos);
  assert(already_json.find("\"sequence\":null,\"status\":\"not_needed\"") !=
         std::string::npos);

  assert(
      xar::ck3_11906::SerializeTitleMapNavigationResultV1(centered, 0).empty());
  assert(
      xar::ck3_11906::SerializeTitleMapNavigationResultV1(already, 29).empty());

  auto unsettled = centered;
  unsettled.camera.settled = false;
  assert(xar::ck3_11906::SerializeTitleMapNavigationResultV1(unsettled, 29)
             .empty());

  auto zoom_forged = centered;
  zoom_forged.camera.expected_zoom_value = 8.0F;
  assert(xar::ck3_11906::SerializeTitleMapNavigationResultV1(zoom_forged, 29)
             .empty());

  auto signed_zero_drift = centered;
  signed_zero_drift.camera.target_state[4] = 0.0F;
  assert(xar::ck3_11906::SerializeTitleMapNavigationResultV1(
             signed_zero_drift, 29)
             .empty());

  auto position_forged = centered;
  position_forged.camera.expected_position_xyz[0] = 18.0F;
  assert(xar::ck3_11906::SerializeTitleMapNavigationResultV1(position_forged,
                                                             29)
             .empty());

  auto zero_revision = centered;
  zero_revision.binding.snapshot_revision = 0;
  assert(xar::ck3_11906::SerializeTitleMapNavigationResultV1(zero_revision, 29)
             .empty());
  return 0;
}
