#include "xar_bridge/zhongguo_manager_subordinate_selector_v1.hpp"

#include <cstdint>
#include <string>
#include <utility>

namespace {

using xar::ck3_11906::ZhongguoBoundedAiManagerAuthorizationV1;
using xar::ck3_11906::ZhongguoManagerSubordinateObservationResultV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{81, 53212000, true, true, true, true,
                                      100};
  xar::game::ZhongguoManagerSubordinateSelectionV1 selection{
      201, 301, 150994946, 150994949, 50331651, 3, "duchy",
      "celestial_government"};
  ZhongguoManagerSubordinateObservationResultV1 result =
      ZhongguoManagerSubordinateObservationResultV1::available;
  std::uint32_t capture_count = 0;
  std::uint32_t observe_count = 0;
  bool main_thread = true;
  bool drift_selection = false;
};

bool MainThread(void *opaque) noexcept {
  return opaque != nullptr && static_cast<Fixture *>(opaque)->main_thread;
}

bool Capture(void *opaque,
             xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  auto *fixture = static_cast<Fixture *>(opaque);
  if (fixture == nullptr) return false;
  ++fixture->capture_count;
  output = fixture->frame;
  return true;
}

ZhongguoManagerSubordinateObservationResultV1 Observe(
    void *opaque, std::int32_t player_character_id,
    xar::game::ZhongguoManagerSubordinateSelectionV1 &output) noexcept {
  auto *fixture = static_cast<Fixture *>(opaque);
  if (fixture == nullptr || player_character_id != fixture->frame.played_character_id)
    return ZhongguoManagerSubordinateObservationResultV1::unavailable;
  ++fixture->observe_count;
  output = fixture->selection;
  if (fixture->drift_selection && fixture->observe_count == 2) {
    ++output.subordinate_character_id;
  }
  return fixture->result;
}

ZhongguoBoundedAiManagerAuthorizationV1 Authorize(
    void *, std::int32_t player_character_id,
    std::int32_t manager_character_id,
    std::int32_t owner_character_id) noexcept {
  return player_character_id == 100 && manager_character_id == 201 &&
                 owner_character_id == 100
             ? ZhongguoBoundedAiManagerAuthorizationV1::
                   authorized_direct_manager
             : ZhongguoBoundedAiManagerAuthorizationV1::rejected;
}

xar::ck3_11906::ZhongguoManagerSubordinateSelectorNativeEnvironmentV1
Environment() {
  xar::ck3_11906::ZhongguoManagerSubordinateSelectorNativeEnvironmentV1
      environment{};
  environment.eligibility.variables.exact_build_admitted = true;
  environment.eligibility.variables.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoManagerSubordinateSelectorAccessV1 Access(
    Fixture &fixture) {
  xar::ck3_11906::ZhongguoManagerSubordinateSelectorAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.observe_selection = &Observe;
  access.authorize_manager_fixture = &Authorize;
  return access;
}

xar::ck3_11906::ZhongguoManagerSubordinateSelectorRequestV1 Request() {
  return {81, "b3.selector.fixture"};
}

bool AvailableAndSerialized() {
  Fixture fixture;
  xar::game::ZhongguoManagerSubordinateSelectorSnapshotV1 snapshot{};
  const auto result = xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
      Environment(), Access(fixture), Request(), snapshot);
  const auto json =
      xar::ck3_11906::SerializeZhongguoManagerSubordinateSelectorV1(snapshot);
  return result ==
             xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
                 available &&
         snapshot.status ==
             xar::game::ZhongguoManagerSubordinateSelectorStatusV1::available &&
         snapshot.readiness.ready && snapshot.readiness.same_frame_ready &&
         snapshot.selection == fixture.selection && fixture.capture_count == 2 &&
         fixture.observe_count == 2 &&
         json.find("\"provider_observed\":true") != std::string::npos &&
         json.find("\"manager_character_id\":201") != std::string::npos &&
         json.find("\"subordinate_character_id\":301") != std::string::npos &&
         json.find("\"selector_kind\":\"zg361-bounded-ai-direct-manager-selection-v1\"") !=
             std::string::npos;
}

bool TypedUnavailableMatrix() {
  for (const auto &entry : {
           std::pair{ZhongguoManagerSubordinateObservationResultV1::
                         no_bounded_ai_direct_manager,
                     std::string{"no_bounded_ai_direct_manager"}},
           std::pair{ZhongguoManagerSubordinateObservationResultV1::
                         bounded_ai_manager_has_no_direct_subordinate,
                     std::string{
                         "bounded_ai_manager_has_no_direct_subordinate"}},
           std::pair{ZhongguoManagerSubordinateObservationResultV1::unavailable,
                     std::string{
                         "native_relationship_enumeration_unavailable"}},
       }) {
    Fixture fixture;
    fixture.result = entry.first;
    xar::game::ZhongguoManagerSubordinateSelectorSnapshotV1 snapshot{};
    if (xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
            Environment(), Access(fixture), Request(), snapshot) !=
            xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
                unavailable ||
        snapshot.unavailable_reason != entry.second || snapshot.readiness.ready ||
        xar::ck3_11906::SerializeZhongguoManagerSubordinateSelectorV1(snapshot)
            .empty()) {
      return false;
    }
  }
  return true;
}

bool DriftAndBoundaryFailures() {
  Fixture fixture;
  fixture.drift_selection = true;
  xar::game::ZhongguoManagerSubordinateSelectorSnapshotV1 snapshot{};
  if (xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
          Environment(), Access(fixture), Request(), snapshot) !=
          xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
              unavailable ||
      snapshot.unavailable_reason != "state_changed") {
    return false;
  }
  fixture = {};
  fixture.main_thread = false;
  if (xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
          Environment(), Access(fixture), Request(), snapshot) !=
          xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
              unavailable ||
      snapshot.unavailable_reason != "requires_application_main") {
    return false;
  }
  fixture = {};
  fixture.frame.paused = false;
  if (xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
          Environment(), Access(fixture), Request(), snapshot) !=
          xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
              unavailable ||
      snapshot.unavailable_reason != "requires_paused") {
    return false;
  }
  auto unsupported = Environment();
  unsupported.eligibility.variables.exact_build_admitted = false;
  fixture = {};
  return xar::ck3_11906::ReadZhongguoManagerSubordinateSelectorV1(
             unsupported, Access(fixture), Request(), snapshot) ==
             xar::game::ReadZhongguoManagerSubordinateSelectorResultV1::
                 unavailable &&
         snapshot.unavailable_reason == "unsupported_build";
}

bool AuthorizationFixture() {
  Fixture fixture;
  const auto environment = Environment();
  const auto access = Access(fixture);
  return xar::ck3_11906::AuthorizeZhongguoBoundedAiDirectManagerV1(
             environment, access, 100, 201, 100) ==
             ZhongguoBoundedAiManagerAuthorizationV1::
                 authorized_direct_manager &&
         xar::ck3_11906::AuthorizeZhongguoBoundedAiDirectManagerV1(
             environment, access, 100, 202, 100) ==
             ZhongguoBoundedAiManagerAuthorizationV1::rejected &&
         xar::ck3_11906::AuthorizeZhongguoBoundedAiDirectManagerV1(
             environment, access, 100, 201, 999) ==
             ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
}

bool BindingAddresses() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto environment =
      xar::ck3_11906::BindZhongguoManagerSubordinateSelectorNativeEnvironmentV1(
          base, true);
  return reinterpret_cast<std::uintptr_t>(
             environment.subject_contract_storage_slot) ==
             base + xar::ck3_11906::kZhongguoSubjectContractStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.subject_contract_fallback_slot) ==
             base + xar::ck3_11906::kZhongguoSubjectContractFallbackSlotRva;
}

} // namespace

int main() {
  return AvailableAndSerialized() && TypedUnavailableMatrix() &&
                 DriftAndBoundaryFailures() && AuthorizationFixture() &&
                 BindingAddresses()
             ? 0
             : 1;
}
