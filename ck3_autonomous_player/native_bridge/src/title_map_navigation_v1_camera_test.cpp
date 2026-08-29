#include "xar_bridge/title_map_navigation_v1_camera.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

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

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset,
           const Value &value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

template <typename Value, std::size_t Size>
Value Load(const std::array<std::byte, Size> &bytes, std::size_t offset) {
  assert(offset + sizeof(Value) <= bytes.size());
  Value output{};
  std::memcpy(&output, bytes.data() + offset, sizeof(output));
  return output;
}

bool SameFloat(float left, float right) {
  return std::bit_cast<std::uint32_t>(left) ==
         std::bit_cast<std::uint32_t>(right);
}

struct Fixture {
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, 0x160> game_data{};
  std::array<std::byte, 0x30> title_storage{};
  std::array<std::byte, 0x40> title_slots{};
  std::array<std::byte, 0x470> title{};
  std::array<std::byte, 0x90> title_template{};
  std::array<std::byte, 0x20> province{};
  std::array<std::byte, 0x20> fallback{};
  std::array<std::byte, 0x700> handler{};
  std::array<std::byte, 0x920> camera{};
  std::vector<void *> province_array = std::vector<void *>(9'823, nullptr);

  void *game_state_pointer = game_state.data();
  void *title_storage_pointer = title_storage.data();
  void *fallback_pointer = fallback.data();
  void *handler_vtable = reinterpret_cast<void *>(0x11110000ULL);
  void *camera_vtable = reinterpret_cast<void *>(0x22220000ULL);
  std::string key = "c_bianzhou";
  std::string template_key = "c_bianzhou";
  std::int32_t title_id = 0x01000002;
  std::int32_t province_id = 9'822;
  xar::game::TitleMapNavigationFrameV1 frame{17, 53'182'008, true,
                                              true};
  std::uint32_t capture_count = 0;
  bool owning_thread = true;
  bool drift = false;
  bool mode_one = true;
  bool mode_two = false;
  bool mode_two_query_succeeds = true;
  bool dispatch_succeeds = true;
  bool dispatch_writes_position = true;
  bool canonicalizer_clamps = false;
  bool handler_camera_available = true;
  std::uint32_t dispatch_count = 0;
  std::uint32_t mode_one_query_count = 0;
  std::uint32_t mode_two_query_count = 0;
  std::array<std::int32_t, 4> bounds{10, 20, 30, 40};
  std::int32_t bucket_count = 2;
  std::array<std::int32_t, 2> thresholds{100, 10};
  std::array<std::int32_t, 2> horizontal_offsets{0, 3};
  std::array<std::int32_t, 2> zoom_indexes{0, 1};
  const std::int32_t *thresholds_pointer = thresholds.data();
  const std::int32_t *horizontal_offsets_pointer =
      horizontal_offsets.data();
  const std::int32_t *zoom_indexes_pointer = zoom_indexes.data();
  std::array<float, 2> zoom_table{5.0F, 7.5F};
  std::array<float, 2> param4_table{30.0F, 45.0F};
  float degrees_to_radians = 0.01745329238474369F;

  Fixture() {
    void *game_data_pointer = game_data.data();
    Store(game_state, 0xA0, game_data_pointer);

    void *slot_bytes = title_slots.data();
    const std::int32_t title_capacity = 4;
    Store(title_storage, 0x20, slot_bytes);
    Store(title_storage, 0x2C, title_capacity);
    void *title_pointer = title.data();
    Store(title_slots, 2 * 0x10 + 0x08, title_pointer);
    Store(title, 0x10, title_id);
    void *template_pointer = title_template.data();
    Store(title, 0x160, template_pointer);
    const std::int32_t tier = 2;
    Store(title_template, 0x5C, tier);

    Store(province, 0x10, province_id);
    province_array[static_cast<std::size_t>(province_id)] = province.data();
    void *province_array_pointer = province_array.data();
    const auto province_count =
        static_cast<std::int32_t>(province_array.size());
    Store(game_data, 0x140, province_array_pointer);
    Store(game_data, 0x14C, province_count);

    Store(handler, 0, handler_vtable);
    Store(camera, 0, camera_vtable);
    void *camera_pointer = camera.data();
    Store(handler, xar::ck3_11906::kTitleMapHandlerCameraOffset,
          camera_pointer);

    const std::array<float, 6> initial{0.0F, 0.0F, 0.0F, 5.0F, 0.25F,
                                       1.0F};
    SetCurrent(initial);
    SetTarget(initial);
    SetZoomIndex(0);
    float *zoom_table_pointer = zoom_table.data();
    Store(camera, xar::ck3_11906::kTitleMapCameraZoomTableOffset,
          zoom_table_pointer);
    const std::int32_t zoom_count = 2;
    Store(camera, xar::ck3_11906::kTitleMapCameraZoomCountOffset,
          zoom_count);
    float *param4_table_pointer = param4_table.data();
    Store(camera, xar::ck3_11906::kTitleMapCameraParam4TableOffset,
          param4_table_pointer);
    const std::int32_t param4_enabled = 1;
    Store(camera, xar::ck3_11906::kTitleMapCameraParam4EnabledOffset,
          param4_enabled);
  }

  void SetCurrent(const std::array<float, 6> &value) {
    Store(camera, xar::ck3_11906::kTitleMapCameraCurrentStateOffset,
          value);
  }

  void SetTarget(const std::array<float, 6> &value) {
    Store(camera, xar::ck3_11906::kTitleMapCameraTargetStateOffset,
          value);
  }

  std::array<float, 6> Current() const {
    return Load<std::array<float, 6>>(
        camera, xar::ck3_11906::kTitleMapCameraCurrentStateOffset);
  }

  std::array<float, 6> Target() const {
    return Load<std::array<float, 6>>(
        camera, xar::ck3_11906::kTitleMapCameraTargetStateOffset);
  }

  void SetZoomIndex(std::int32_t value) {
    Store(camera, xar::ck3_11906::kTitleMapCameraZoomIndexOffset, value);
  }

  void SetBlocked(std::uint8_t value) {
    Store(camera,
          xar::ck3_11906::kTitleMapCameraTargetWriteBlockedOffset, value);
  }

  void SetTransient(float x, float z) {
    Store(camera, xar::ck3_11906::kTitleMapCameraTransientXOffset, x);
    Store(camera, xar::ck3_11906::kTitleMapCameraTransientZOffset, z);
  }

  std::array<float, 6> Expected() const {
    auto output = Target();
    output[0] = 17.0F;
    output[1] = 0.0F;
    output[2] = 30.0F;
    output[3] = zoom_table[1];
    output[4] = param4_table[1] * degrees_to_radians;
    return output;
  }
};

bool CaptureFrame(void *opaque,
                  xar::game::TitleMapNavigationFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  if (fixture.drift && fixture.capture_count > 2) {
    ++output.date_raw;
  }
  ++fixture.capture_count;
  return true;
}

bool IsOwningThread(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->owning_thread;
}

bool ReadString(void *opaque, const void *native_string,
                std::string &output) noexcept {
  const auto &fixture = *static_cast<const Fixture *>(opaque);
  if (native_string != fixture.title_template.data() + 0x18) {
    return false;
  }
  output = fixture.template_key;
  return true;
}

bool ResolveTitle(void *opaque, std::string_view key,
                  void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = key == fixture.key ? fixture.title.data() : fixture.fallback.data();
  return true;
}

bool ResolveProvince(void *opaque, void *title, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = title == fixture.title.data() ? fixture.province.data() : nullptr;
  return true;
}

bool ResolveHandlerCamera(void *opaque, void *&handler,
                          void *&camera) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (!fixture.handler_camera_available) {
    handler = nullptr;
    camera = nullptr;
    return false;
  }
  handler = fixture.handler.data();
  camera = fixture.camera.data();
  return true;
}

bool ComputeBounds(void *opaque, void *landed_title,
                   std::array<std::int32_t, 4> &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (landed_title != fixture.title.data()) {
    return false;
  }
  output = fixture.bounds;
  return true;
}

bool QueryMode(void *opaque, void *handler, std::int32_t mask,
               bool &enabled) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (handler != fixture.handler.data()) {
    return false;
  }
  if (mask == 1) {
    ++fixture.mode_one_query_count;
    enabled = fixture.mode_one;
    return true;
  }
  if (mask == 2) {
    ++fixture.mode_two_query_count;
    enabled = fixture.mode_two;
    return fixture.mode_two_query_succeeds;
  }
  return false;
}

bool Canonicalize(void *opaque, void *camera,
                  std::array<float, 6> &state) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (camera != fixture.camera.data()) {
    return false;
  }
  if (fixture.canonicalizer_clamps) {
    state[0] = 16.0F;
  }
  return true;
}

bool Dispatch(void *opaque, void *handler, void *landed_title,
              bool force_zoom) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.dispatch_count;
  if (!fixture.dispatch_succeeds || handler != fixture.handler.data() ||
      landed_title != fixture.title.data() || !force_zoom) {
    return false;
  }
  auto target = fixture.Target();
  if (fixture.dispatch_writes_position) {
    target[0] = fixture.mode_one && !fixture.mode_two ? 17.0F : 20.0F;
    target[1] = 0.0F;
    target[2] = 30.0F;
  }
  target[3] = fixture.zoom_table[1];
  target[4] = fixture.param4_table[1] * fixture.degrees_to_radians;
  fixture.SetTarget(target);
  fixture.SetZoomIndex(1);
  return true;
}

void *DummyDynamicCast(void *, long, const void *, const void *, int) {
  return nullptr;
}
bool DummyBounds(void *, std::int32_t *) { return false; }
bool DummyMode(void *, std::int32_t) { return false; }
void DummyDispatch(void *, void *, bool) {}
void DummyCanonicalize(void *, float *) {}
void *DummyTitleResolver(const void *) { return nullptr; }
void *DummyProvinceResolver(void *) { return nullptr; }

xar::ck3_11906::TitleMapNavigationNativeEnvironmentV1 TitleEnvironment(
    Fixture &fixture) {
  xar::ck3_11906::TitleMapNavigationNativeEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.offline_fixture_function_overrides = true;
  output.game_state_slot = &fixture.game_state_pointer;
  output.landed_title_storage_slot = &fixture.title_storage_pointer;
  output.landed_title_fallback_slot = &fixture.fallback_pointer;
  output.resolve_landed_title_by_key = &DummyTitleResolver;
  output.resolve_title_province = &DummyProvinceResolver;
  return output;
}

xar::ck3_11906::TitleMapNavigationCameraEnvironmentV1 CameraEnvironment(
    Fixture &fixture) {
  xar::ck3_11906::TitleMapNavigationCameraEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.offline_fixture_function_overrides = true;
  output.ingame_idler_root_slot = &fixture.game_state_pointer;
  output.runtime_dynamic_cast = &DummyDynamicCast;
  output.idler_base_type_descriptor = reinterpret_cast<void *>(0x10);
  output.ingame_idler_type_descriptor = reinterpret_cast<void *>(0x20);
  output.expected_handler_vtable = fixture.handler_vtable;
  output.expected_camera_vtable = fixture.camera_vtable;
  output.compute_title_bounds = &DummyBounds;
  output.query_handler_mode = &DummyMode;
  output.center_camera_on_title = &DummyDispatch;
  output.canonicalize_camera_state = &DummyCanonicalize;
  output.bucket_count = &fixture.bucket_count;
  output.bucket_thresholds_slot = &fixture.thresholds_pointer;
  output.horizontal_offsets_slot = &fixture.horizontal_offsets_pointer;
  output.zoom_indexes_slot = &fixture.zoom_indexes_pointer;
  output.degrees_to_radians = &fixture.degrees_to_radians;
  return output;
}

xar::ck3_11906::TitleMapNavigationCameraAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::TitleMapNavigationCameraAccessV1 output{};
  output.title.context = &fixture;
  output.title.capture_frame = &CaptureFrame;
  output.title.is_owning_thread = &IsOwningThread;
  output.title.read_string = &ReadString;
  output.title.resolve_title_fixture = &ResolveTitle;
  output.title.resolve_province_fixture = &ResolveProvince;
  output.resolve_handler_camera_fixture = &ResolveHandlerCamera;
  output.compute_bounds_fixture = &ComputeBounds;
  output.query_handler_mode_fixture = &QueryMode;
  output.canonicalize_fixture = &Canonicalize;
  output.dispatch_fixture = &Dispatch;
  return output;
}

xar::game::TitleMapNavigationCommandV1 Command(Fixture &fixture) {
  xar::game::TitleMapNavigationCommandV1 output{};
  output.request.expected_snapshot_revision = fixture.frame.snapshot_revision;
  output.request.title_key = fixture.key;
  return output;
}

xar::game::TitleMapNavigationCommandStatusV1 Advance(
    Fixture &fixture, xar::game::TitleMapNavigationCommandV1 &command) {
  return xar::ck3_11906::AdvanceTitleMapNavigationCommandV1(
      TitleEnvironment(fixture), CameraEnvironment(fixture), Access(fixture),
      command);
}

} // namespace

int main() {
  using Status = xar::game::TitleMapNavigationCommandStatusV1;

  Fixture fixture{};
  auto command = Command(fixture);
  assert(Advance(fixture, command) == Status::pending);
  assert(command.initialized);
  assert(command.dispatched);
  assert(fixture.dispatch_count == 1);
  assert(command.camera.bounds_extent == fixture.bounds);
  assert(command.camera.map_x_adjustment == 3);
  assert(command.camera.zoom_index == 1);
  assert(SameFloat(command.camera.expected_zoom_value, 7.5F));
  const std::array<float, 3> expected_position{17.0F, 0.0F, 30.0F};
  assert(command.camera.expected_position_xyz == expected_position);
  assert(!command.camera.settled);
  const auto expected = fixture.Target();
  fixture.SetCurrent(expected);
  assert(Advance(fixture, command) == Status::centered);
  assert(command.camera.settled);
  assert(!command.camera.target_write_blocked);
  assert(command.camera.current_state == command.camera.target_state);
  assert(fixture.dispatch_count == 1);

  Fixture opaque_param_clamp{};
  auto opaque_param_clamp_command = Command(opaque_param_clamp);
  assert(Advance(opaque_param_clamp, opaque_param_clamp_command) ==
         Status::pending);
  auto clamped_opaque_target = opaque_param_clamp.Target();
  clamped_opaque_target[4] = 0.5F;
  opaque_param_clamp.SetTarget(clamped_opaque_target);
  opaque_param_clamp.SetCurrent(clamped_opaque_target);
  assert(Advance(opaque_param_clamp, opaque_param_clamp_command) ==
         Status::centered);
  assert(opaque_param_clamp_command.camera.current_state ==
         opaque_param_clamp_command.camera.target_state);
  assert(SameFloat(opaque_param_clamp_command.camera.target_state[3],
                   opaque_param_clamp_command.camera.expected_zoom_value));

  Fixture already{};
  const auto already_expected = already.Expected();
  already.SetCurrent(already_expected);
  already.SetTarget(already_expected);
  already.SetZoomIndex(1);
  auto already_command = Command(already);
  assert(Advance(already, already_command) == Status::already_centered);
  assert(!already_command.dispatched);
  assert(already.dispatch_count == 0);
  assert(already_command.camera.settled);

  Fixture blocked{};
  blocked.SetBlocked(1);
  auto blocked_command = Command(blocked);
  assert(Advance(blocked, blocked_command) == Status::pending);
  assert(!blocked_command.dispatched);
  assert(blocked.dispatch_count == 0);
  blocked.SetBlocked(0);
  assert(Advance(blocked, blocked_command) == Status::pending);
  assert(blocked_command.dispatched);
  assert(blocked.dispatch_count == 1);

  Fixture transient{};
  transient.SetTransient(1.0F, 0.0F);
  auto transient_command = Command(transient);
  assert(Advance(transient, transient_command) == Status::pending);
  assert(!transient_command.dispatched);
  transient.SetTransient(0.0F, 0.0F);
  assert(Advance(transient, transient_command) == Status::pending);
  assert(transient_command.dispatched);

  Fixture dispatch_failure{};
  dispatch_failure.dispatch_succeeds = false;
  auto dispatch_failure_command = Command(dispatch_failure);
  assert(Advance(dispatch_failure, dispatch_failure_command) ==
         Status::submission_failed);

  Fixture partial_dispatch{};
  partial_dispatch.dispatch_writes_position = false;
  auto partial_command = Command(partial_dispatch);
  assert(Advance(partial_dispatch, partial_command) ==
         Status::submission_failed);

  Fixture target_drift{};
  auto target_drift_command = Command(target_drift);
  assert(Advance(target_drift, target_drift_command) == Status::pending);
  auto drifted_target = target_drift.Target();
  drifted_target[0] += 1.0F;
  target_drift.SetTarget(drifted_target);
  assert(Advance(target_drift, target_drift_command) ==
         Status::state_changed);

  Fixture signed_zero{};
  const auto signed_zero_expected = signed_zero.Expected();
  auto signed_zero_current = signed_zero_expected;
  signed_zero_current[1] = -0.0F;
  signed_zero.SetCurrent(signed_zero_current);
  signed_zero.SetTarget(signed_zero_expected);
  signed_zero.SetZoomIndex(1);
  auto signed_zero_command = Command(signed_zero);
  assert(Advance(signed_zero, signed_zero_command) == Status::pending);
  assert(signed_zero_command.dispatched);

  Fixture invalid_zoom{};
  invalid_zoom.zoom_indexes[1] = 2;
  auto invalid_zoom_command = Command(invalid_zoom);
  assert(Advance(invalid_zoom, invalid_zoom_command) ==
         Status::camera_state_unavailable);

  Fixture short_circuit_mode{};
  short_circuit_mode.mode_one = false;
  short_circuit_mode.mode_two_query_succeeds = false;
  auto short_circuit_command = Command(short_circuit_mode);
  assert(Advance(short_circuit_mode, short_circuit_command) ==
         Status::pending);
  assert(short_circuit_mode.mode_one_query_count == 1);
  assert(short_circuit_mode.mode_two_query_count == 0);
  assert(short_circuit_command.camera.map_x_adjustment == 0);

  Fixture clamped{};
  clamped.canonicalizer_clamps = true;
  auto clamped_command = Command(clamped);
  assert(Advance(clamped, clamped_command) ==
         Status::title_not_centerable);

  Fixture missing_camera{};
  missing_camera.handler_camera_available = false;
  auto missing_camera_command = Command(missing_camera);
  assert(Advance(missing_camera, missing_camera_command) ==
         Status::camera_state_unavailable);

  Fixture wrong_camera_vtable{};
  void *wrong_vtable = reinterpret_cast<void *>(0x33330000ULL);
  Store(wrong_camera_vtable.camera, 0, wrong_vtable);
  auto wrong_camera_command = Command(wrong_camera_vtable);
  assert(Advance(wrong_camera_vtable, wrong_camera_command) ==
         Status::camera_state_unavailable);

  Fixture changed_camera{};
  auto changed_camera_command = Command(changed_camera);
  changed_camera.SetBlocked(1);
  assert(Advance(changed_camera, changed_camera_command) == Status::pending);
  std::array<std::byte, 0x920> replacement_camera = changed_camera.camera;
  void *replacement_pointer = replacement_camera.data();
  Store(changed_camera.handler,
        xar::ck3_11906::kTitleMapHandlerCameraOffset,
        replacement_pointer);
  // The fixture resolver returns its camera array directly, so model an
  // identity change via the frozen identity instead of dereferencing a stale
  // pointer.
  changed_camera_command.native_camera_identity = replacement_pointer;
  assert(Advance(changed_camera, changed_camera_command) ==
         Status::state_changed);

  assert(xar::ck3_11906::TitleMapNavigationCommandRejectionCodeV1(
             Status::submission_failed) == "submission_failed");
  assert(xar::ck3_11906::TitleMapNavigationCommandRejectionCodeV1(
             Status::centered)
             .empty());
  assert(xar::ck3_11906::IsTitleMapNavigationTerminalV1(Status::centered));
  assert(!xar::ck3_11906::IsTitleMapNavigationTerminalV1(Status::pending));

  Fixture illegal{};
  auto illegal_command = Command(illegal);
  illegal_command.dispatched = true;
  assert(Advance(illegal, illegal_command) == Status::internal_error);

  Fixture forged_success{};
  auto forged_success_command = Command(forged_success);
  forged_success_command.status = Status::centered;
  assert(Advance(forged_success, forged_success_command) ==
         Status::internal_error);
  return 0;
}
