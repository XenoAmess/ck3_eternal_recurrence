#include "xar_bridge/title_map_navigation_v1_camera.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kIngameIdlerObjectOffset = 0x10;
constexpr std::size_t kIngameIdlerHandlerOffset = 0x88;
constexpr std::int32_t kMaximumCameraBuckets = 4'096;

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ReadBytes(const TitleMapNavigationCameraAccessV1 &access,
               const void *address, void *output,
               std::size_t size) noexcept {
  if (access.title.read_memory != nullptr) {
    return access.title.read_memory(access.title.context, address, output,
                                    size);
  }
  return GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const TitleMapNavigationCameraAccessV1 &access,
               const void *base, std::size_t offset,
               Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const TitleMapNavigationCameraAccessV1 &access,
              const Value *slot, Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool CameraEnvironmentIsExact(
    const TitleMapNavigationCameraEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.ingame_idler_root_slot == nullptr ||
      environment.runtime_dynamic_cast == nullptr ||
      environment.idler_base_type_descriptor == nullptr ||
      environment.ingame_idler_type_descriptor == nullptr ||
      environment.expected_handler_vtable == nullptr ||
      environment.expected_camera_vtable == nullptr ||
      environment.compute_title_bounds == nullptr ||
      environment.query_handler_mode == nullptr ||
      environment.center_camera_on_title == nullptr ||
      environment.canonicalize_camera_state == nullptr ||
      environment.bucket_count == nullptr ||
      environment.bucket_thresholds_slot == nullptr ||
      environment.horizontal_offsets_slot == nullptr ||
      environment.zoom_indexes_slot == nullptr ||
      environment.degrees_to_radians == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return true;
  }
  if (environment.module_base == 0) {
    return false;
  }
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(
             environment.ingame_idler_root_slot) ==
             base + kTitleMapIngameIdlerRootSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.runtime_dynamic_cast) ==
             base + kTitleMapRuntimeDynamicCastRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.idler_base_type_descriptor) ==
             base + kTitleMapIdlerBaseTypeDescriptorRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.ingame_idler_type_descriptor) ==
             base + kTitleMapIngameIdlerTypeDescriptorRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.expected_handler_vtable) ==
             base + kTitleMapHandlerVtableRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.expected_camera_vtable) ==
             base + kTitleMapCameraVtableRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.compute_title_bounds) ==
             base + kTitleMapComputeBoundsRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.query_handler_mode) ==
             base + kTitleMapQueryHandlerModeRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.center_camera_on_title) ==
             base + kTitleMapCenterCameraOnTitleRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.canonicalize_camera_state) ==
             base + kTitleMapCanonicalizeCameraStateRva &&
         reinterpret_cast<std::uintptr_t>(environment.bucket_count) ==
             base + kTitleMapBucketCountRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.bucket_thresholds_slot) ==
             base + kTitleMapBucketThresholdsSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.horizontal_offsets_slot) ==
             base + kTitleMapHorizontalOffsetsSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.zoom_indexes_slot) ==
             base + kTitleMapZoomIndexesSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.degrees_to_radians) ==
             base + kTitleMapDegreesToRadiansRva;
}

bool InvokeDynamicCast(NativeRuntimeDynamicCastV1 function, void *object,
                       const void *source_type, const void *target_type,
                       void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = function(object, 0, source_type, target_type, 0);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function(object, 0, source_type, target_type, 0);
  return true;
#endif
}

bool ResolveHandlerAndCamera(
    const TitleMapNavigationCameraEnvironmentV1 &environment,
    const TitleMapNavigationCameraAccessV1 &access, void *&handler,
    void *&camera) noexcept {
  handler = nullptr;
  camera = nullptr;
  if (environment.offline_fixture_function_overrides) {
    if (access.resolve_handler_camera_fixture == nullptr ||
        !access.resolve_handler_camera_fixture(access.title.context, handler,
                                               camera)) {
      return false;
    }
  } else {
    void *root = nullptr;
    void *idler_object = nullptr;
    void *cast_result = nullptr;
    if (!ReadSlot(access, environment.ingame_idler_root_slot, root) ||
        root == nullptr ||
        !ReadValue(access, root, kIngameIdlerObjectOffset, idler_object) ||
        idler_object == nullptr ||
        !InvokeDynamicCast(environment.runtime_dynamic_cast, idler_object,
                           environment.idler_base_type_descriptor,
                           environment.ingame_idler_type_descriptor,
                           cast_result) ||
        cast_result == nullptr ||
        !ReadValue(access, cast_result, kIngameIdlerHandlerOffset, handler) ||
        handler == nullptr ||
        !ReadValue(access, handler, kTitleMapHandlerCameraOffset, camera) ||
        camera == nullptr) {
      return false;
    }
  }
  void *handler_vtable = nullptr;
  void *camera_vtable = nullptr;
  return handler != nullptr && camera != nullptr &&
         ReadValue(access, handler, 0, handler_vtable) &&
         handler_vtable == environment.expected_handler_vtable &&
         ReadValue(access, camera, 0, camera_vtable) &&
         camera_vtable == environment.expected_camera_vtable;
}

enum class BoundsCallResultV1 : std::uint32_t {
  available = 0,
  not_centerable = 1,
  fault = 2,
};

BoundsCallResultV1 InvokeBounds(
    const TitleMapNavigationCameraEnvironmentV1 &environment,
    const TitleMapNavigationCameraAccessV1 &access, void *landed_title,
    std::array<std::int32_t, 4> &bounds) noexcept {
  bounds = {std::numeric_limits<std::int32_t>::max(),
            std::numeric_limits<std::int32_t>::max(),
            std::numeric_limits<std::int32_t>::min(),
            std::numeric_limits<std::int32_t>::min()};
  if (environment.offline_fixture_function_overrides) {
    if (access.compute_bounds_fixture == nullptr) {
      return BoundsCallResultV1::fault;
    }
    return access.compute_bounds_fixture(access.title.context, landed_title,
                                         bounds)
               ? BoundsCallResultV1::available
               : BoundsCallResultV1::not_centerable;
  }
#if defined(_MSC_VER)
  __try {
    return environment.compute_title_bounds(landed_title, bounds.data())
               ? BoundsCallResultV1::available
               : BoundsCallResultV1::not_centerable;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return BoundsCallResultV1::fault;
  }
#else
  return environment.compute_title_bounds(landed_title, bounds.data())
             ? BoundsCallResultV1::available
             : BoundsCallResultV1::not_centerable;
#endif
}

bool InvokeHandlerMode(
    const TitleMapNavigationCameraEnvironmentV1 &environment,
    const TitleMapNavigationCameraAccessV1 &access, void *handler,
    std::int32_t mask, bool &enabled) noexcept {
  enabled = false;
  if (environment.offline_fixture_function_overrides) {
    return access.query_handler_mode_fixture != nullptr &&
           access.query_handler_mode_fixture(access.title.context, handler,
                                             mask, enabled);
  }
#if defined(_MSC_VER)
  __try {
    enabled = environment.query_handler_mode(handler, mask);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    enabled = false;
    return false;
  }
#else
  enabled = environment.query_handler_mode(handler, mask);
  return true;
#endif
}

bool InvokeCanonicalizer(
    const TitleMapNavigationCameraEnvironmentV1 &environment,
    const TitleMapNavigationCameraAccessV1 &access, void *camera,
    std::array<float, 6> &state) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.canonicalize_fixture != nullptr &&
           access.canonicalize_fixture(access.title.context, camera, state);
  }
#if defined(_MSC_VER)
  __try {
    environment.canonicalize_camera_state(camera, state.data());
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  environment.canonicalize_camera_state(camera, state.data());
  return true;
#endif
}

bool InvokeDispatch(const TitleMapNavigationCameraEnvironmentV1 &environment,
                    const TitleMapNavigationCameraAccessV1 &access,
                    void *handler, void *landed_title) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.dispatch_fixture != nullptr &&
           access.dispatch_fixture(access.title.context, handler,
                                   landed_title, true);
  }
#if defined(_MSC_VER)
  __try {
    environment.center_camera_on_title(handler, landed_title, true);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  environment.center_camera_on_title(handler, landed_title, true);
  return true;
#endif
}

std::int32_t WrapAdd(std::int32_t left, std::int32_t right) noexcept {
  return std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(left) + static_cast<std::uint32_t>(right));
}

std::int32_t WrapSubtract(std::int32_t left,
                          std::int32_t right) noexcept {
  return std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(left) - static_cast<std::uint32_t>(right));
}

std::int32_t MidpointTowardZero(std::int32_t minimum,
                                std::int32_t maximum) noexcept {
  // CK3 first wraps the signed 32-bit LEA and then implements signed /2 with
  // (sum - signbit) >> 1.  C++ integer division has the same toward-zero
  // result once the wrapped sum has been reconstructed.
  return WrapAdd(minimum, maximum) / 2;
}

bool SameFloat(float left, float right) noexcept {
  return std::bit_cast<std::uint32_t>(left) ==
         std::bit_cast<std::uint32_t>(right);
}

template <std::size_t Size>
bool SameFloatArray(const std::array<float, Size> &left,
                    const std::array<float, Size> &right) noexcept {
  for (std::size_t index = 0; index < Size; ++index) {
    if (!SameFloat(left[index], right[index])) {
      return false;
    }
  }
  return true;
}

bool SameExpectedPrefix(const std::array<float, 6> &left,
                        const std::array<float, 6> &right) noexcept {
  for (std::size_t index = 0; index < 4; ++index) {
    if (!SameFloat(left[index], right[index])) {
      return false;
    }
  }
  return true;
}

template <std::size_t Size>
bool AllFinite(const std::array<float, Size> &values) noexcept {
  return std::all_of(values.begin(), values.end(),
                     [](float value) noexcept { return std::isfinite(value); });
}

struct CameraReadbackV1 {
  std::array<float, 6> current{};
  std::array<float, 6> target{};
  std::int32_t zoom_index = -1;
  float transient_x = 0.0F;
  float transient_z = 0.0F;
  std::uint8_t target_write_blocked = 0;
};

bool ReadCamera(const TitleMapNavigationCameraAccessV1 &access,
                void *camera, CameraReadbackV1 &output) noexcept {
  output = {};
  return ReadValue(access, camera, kTitleMapCameraCurrentStateOffset,
                   output.current) &&
         ReadValue(access, camera, kTitleMapCameraTargetStateOffset,
                   output.target) &&
         ReadValue(access, camera, kTitleMapCameraZoomIndexOffset,
                   output.zoom_index) &&
         ReadValue(access, camera, kTitleMapCameraTransientXOffset,
                   output.transient_x) &&
         ReadValue(access, camera, kTitleMapCameraTransientZOffset,
                   output.transient_z) &&
         ReadValue(access, camera,
                   kTitleMapCameraTargetWriteBlockedOffset,
                   output.target_write_blocked) &&
         AllFinite(output.current) && AllFinite(output.target) &&
         std::isfinite(output.transient_x) &&
         std::isfinite(output.transient_z);
}

bool NoTransientPositionShift(const CameraReadbackV1 &state) noexcept {
  return state.transient_x == 0.0F && state.transient_z == 0.0F;
}

struct CameraPlanV1 {
  std::array<std::int32_t, 4> bounds{};
  std::int32_t map_x_adjustment = 0;
  std::int32_t zoom_index = -1;
  float expected_zoom = 0.0F;
  std::array<float, 6> raw_expected{};
  std::array<float, 6> canonical_expected{};
};

enum class BuildCameraPlanResultV1 : std::uint32_t {
  ready = 0,
  not_centerable = 1,
  unavailable = 2,
};

BuildCameraPlanResultV1 BuildCameraPlan(
    const TitleMapNavigationCameraEnvironmentV1 &environment,
    const TitleMapNavigationCameraAccessV1 &access, void *handler,
    void *camera, void *landed_title,
    const std::array<float, 6> &seed_target,
    CameraPlanV1 &plan) noexcept {
  plan = {};
  const auto bounds_result =
      InvokeBounds(environment, access, landed_title, plan.bounds);
  if (bounds_result == BoundsCallResultV1::fault) {
    return BuildCameraPlanResultV1::unavailable;
  }
  if (bounds_result == BoundsCallResultV1::not_centerable ||
      plan.bounds[0] > plan.bounds[2] ||
      plan.bounds[1] > plan.bounds[3]) {
    return BuildCameraPlanResultV1::not_centerable;
  }

  const auto extent_x = WrapSubtract(plan.bounds[2], plan.bounds[0]);
  const auto extent_z = WrapSubtract(plan.bounds[3], plan.bounds[1]);
  const auto extent = std::max(extent_x, extent_z);
  if (extent_x < 0 || extent_z < 0) {
    return BuildCameraPlanResultV1::not_centerable;
  }

  std::int32_t bucket_count = 0;
  const std::int32_t *thresholds = nullptr;
  const std::int32_t *horizontal_offsets = nullptr;
  const std::int32_t *zoom_indexes = nullptr;
  if (!ReadSlot(access, environment.bucket_count, bucket_count) ||
      bucket_count < 0 || bucket_count > kMaximumCameraBuckets ||
      !ReadSlot(access, environment.bucket_thresholds_slot, thresholds) ||
      !ReadSlot(access, environment.horizontal_offsets_slot,
                horizontal_offsets) ||
      !ReadSlot(access, environment.zoom_indexes_slot, zoom_indexes) ||
      zoom_indexes == nullptr) {
    return BuildCameraPlanResultV1::unavailable;
  }
  if (bucket_count > 0 && thresholds == nullptr) {
    return BuildCameraPlanResultV1::unavailable;
  }

  std::int32_t bucket = 0;
  for (std::int32_t index = 0; index < bucket_count; ++index) {
    std::int32_t threshold = 0;
    if (!ReadValue(access, thresholds,
                   static_cast<std::size_t>(index) * sizeof(threshold),
                   threshold)) {
      return BuildCameraPlanResultV1::unavailable;
    }
    if (extent > threshold) {
      bucket = index;
      break;
    }
  }

  bool mode_one = false;
  bool mode_two = false;
  if (!InvokeHandlerMode(environment, access, handler, 1, mode_one)) {
    return BuildCameraPlanResultV1::unavailable;
  }
  if (mode_one &&
      !InvokeHandlerMode(environment, access, handler, 2, mode_two)) {
    return BuildCameraPlanResultV1::unavailable;
  }
  if (mode_one && !mode_two) {
    if (horizontal_offsets == nullptr ||
        !ReadValue(access, horizontal_offsets,
                   static_cast<std::size_t>(bucket) *
                       sizeof(plan.map_x_adjustment),
                   plan.map_x_adjustment)) {
      return BuildCameraPlanResultV1::unavailable;
    }
  }

  if (!ReadValue(access, zoom_indexes,
                 static_cast<std::size_t>(bucket) *
                     sizeof(plan.zoom_index),
                 plan.zoom_index)) {
    return BuildCameraPlanResultV1::unavailable;
  }
  std::int32_t zoom_count = 0;
  const float *zoom_table = nullptr;
  if (plan.zoom_index < 0 ||
      !ReadValue(access, camera, kTitleMapCameraZoomCountOffset,
                 zoom_count) ||
      plan.zoom_index >= zoom_count ||
      !ReadValue(access, camera, kTitleMapCameraZoomTableOffset,
                 zoom_table) ||
      zoom_table == nullptr ||
      !ReadValue(access, zoom_table,
                 static_cast<std::size_t>(plan.zoom_index) *
                     sizeof(plan.expected_zoom),
                 plan.expected_zoom) ||
      !std::isfinite(plan.expected_zoom)) {
    return BuildCameraPlanResultV1::unavailable;
  }

  auto center_x = MidpointTowardZero(plan.bounds[0], plan.bounds[2]);
  const auto center_z = MidpointTowardZero(plan.bounds[1], plan.bounds[3]);
  center_x = WrapSubtract(center_x, plan.map_x_adjustment);

  plan.raw_expected = seed_target;
  plan.raw_expected[0] = static_cast<float>(center_x);
  plan.raw_expected[1] = 0.0F;
  plan.raw_expected[2] = static_cast<float>(center_z);
  plan.raw_expected[3] = plan.expected_zoom;

  std::int32_t param4_enabled = 0;
  if (!ReadValue(access, camera, kTitleMapCameraParam4EnabledOffset,
                 param4_enabled)) {
    return BuildCameraPlanResultV1::unavailable;
  }
  if (param4_enabled != 0) {
    const float *param4_table = nullptr;
    float degrees_to_radians = 0.0F;
    float param4_degrees = 0.0F;
    if (!ReadValue(access, camera, kTitleMapCameraParam4TableOffset,
                   param4_table) ||
        param4_table == nullptr ||
        !ReadValue(access, param4_table,
                   static_cast<std::size_t>(plan.zoom_index) *
                       sizeof(param4_degrees),
                   param4_degrees) ||
        !ReadSlot(access, environment.degrees_to_radians,
                  degrees_to_radians) ||
        !std::isfinite(param4_degrees) ||
        !std::isfinite(degrees_to_radians)) {
      return BuildCameraPlanResultV1::unavailable;
    }
    plan.raw_expected[4] = param4_degrees * degrees_to_radians;
  }
  if (!AllFinite(plan.raw_expected)) {
    return BuildCameraPlanResultV1::unavailable;
  }

  plan.canonical_expected = plan.raw_expected;
  if (!InvokeCanonicalizer(environment, access, camera,
                           plan.canonical_expected) ||
      !AllFinite(plan.canonical_expected)) {
    return BuildCameraPlanResultV1::unavailable;
  }
  // The public v1 schema deliberately proves expected X/Z from the title
  // bounds and map-X adjustment.  A title whose computed target needs native
  // map-bound clamping cannot satisfy that cross-field proof in this version.
  return SameFloat(plan.raw_expected[0], plan.canonical_expected[0]) &&
                 SameFloat(plan.raw_expected[1],
                           plan.canonical_expected[1]) &&
                 SameFloat(plan.raw_expected[2],
                           plan.canonical_expected[2])
             ? BuildCameraPlanResultV1::ready
             : BuildCameraPlanResultV1::not_centerable;
}

bool SamePlan(const CameraPlanV1 &left,
              const CameraPlanV1 &right) noexcept {
  return left.bounds == right.bounds &&
         left.map_x_adjustment == right.map_x_adjustment &&
         left.zoom_index == right.zoom_index &&
         SameFloat(left.expected_zoom, right.expected_zoom) &&
         SameExpectedPrefix(left.raw_expected, right.raw_expected) &&
         SameExpectedPrefix(left.canonical_expected,
                            right.canonical_expected);
}

CameraPlanV1 FrozenPlan(
    const game::TitleMapNavigationCommandV1 &command) noexcept {
  CameraPlanV1 output{};
  output.bounds = command.camera.bounds_extent;
  output.map_x_adjustment = command.camera.map_x_adjustment;
  output.zoom_index = command.camera.zoom_index;
  output.expected_zoom = command.camera.expected_zoom_value;
  output.raw_expected = command.raw_expected_target;
  output.canonical_expected = command.canonical_expected_target;
  return output;
}

void PublishEvidence(const CameraPlanV1 &plan,
                     const CameraReadbackV1 &readback,
                     game::TitleMapNavigationCameraEvidenceV1 &output,
                     bool settled) noexcept {
  output.bounds_extent = plan.bounds;
  output.map_x_adjustment = plan.map_x_adjustment;
  output.expected_position_xyz = {
      plan.canonical_expected[0], plan.canonical_expected[1],
      plan.canonical_expected[2]};
  output.expected_zoom_value = plan.expected_zoom;
  output.zoom_index = plan.zoom_index;
  output.current_state = readback.current;
  output.target_state = readback.target;
  output.settled = settled;
  output.target_write_blocked = readback.target_write_blocked != 0;
}

game::TitleMapNavigationCommandStatusV1 MapResolverResult(
    game::ResolveLandedTitleMapAnchorResultV1 result) noexcept {
  using From = game::ResolveLandedTitleMapAnchorResultV1;
  using To = game::TitleMapNavigationCommandStatusV1;
  switch (result) {
  case From::resolved:
    return To::pending;
  case From::unsupported_build:
    return To::unsupported_build;
  case From::requires_owning_thread:
    return To::requires_owning_thread;
  case From::requires_paused:
    return To::requires_paused;
  case From::map_not_ready:
    return To::map_not_ready;
  case From::title_key_not_found:
    return To::title_key_not_found;
  case From::title_generation_mismatch:
    return To::title_generation_mismatch;
  case From::title_not_centerable:
    return To::title_not_centerable;
  case From::state_changed:
    return To::state_changed;
  case From::internal_error:
    return To::internal_error;
  }
  return To::internal_error;
}

bool CaptureSameBinding(const TitleMapNavigationCameraAccessV1 &access,
                        const game::TitleMapNavigationFrameV1 &expected) noexcept {
  game::TitleMapNavigationFrameV1 observed{};
  return access.title.capture_frame != nullptr &&
         access.title.capture_frame(access.title.context, observed) &&
         observed == expected;
}

} // namespace

TitleMapNavigationCameraEnvironmentV1
BindTitleMapNavigationCameraEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  TitleMapNavigationCameraEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0) {
    return output;
  }
  output.ingame_idler_root_slot = reinterpret_cast<void **>(
      module_base + kTitleMapIngameIdlerRootSlotRva);
  output.runtime_dynamic_cast = reinterpret_cast<NativeRuntimeDynamicCastV1>(
      module_base + kTitleMapRuntimeDynamicCastRva);
  output.idler_base_type_descriptor = reinterpret_cast<const void *>(
      module_base + kTitleMapIdlerBaseTypeDescriptorRva);
  output.ingame_idler_type_descriptor = reinterpret_cast<const void *>(
      module_base + kTitleMapIngameIdlerTypeDescriptorRva);
  output.expected_handler_vtable = reinterpret_cast<const void *>(
      module_base + kTitleMapHandlerVtableRva);
  output.expected_camera_vtable = reinterpret_cast<const void *>(
      module_base + kTitleMapCameraVtableRva);
  output.compute_title_bounds = reinterpret_cast<NativeComputeTitleBoundsV1>(
      module_base + kTitleMapComputeBoundsRva);
  output.query_handler_mode =
      reinterpret_cast<NativeQueryTitleMapHandlerModeV1>(
          module_base + kTitleMapQueryHandlerModeRva);
  output.center_camera_on_title =
      reinterpret_cast<NativeCenterCameraOnTitleV1>(
          module_base + kTitleMapCenterCameraOnTitleRva);
  output.canonicalize_camera_state =
      reinterpret_cast<NativeCanonicalizeCameraStateV1>(
          module_base + kTitleMapCanonicalizeCameraStateRva);
  output.bucket_count = reinterpret_cast<const std::int32_t *>(
      module_base + kTitleMapBucketCountRva);
  output.bucket_thresholds_slot =
      reinterpret_cast<const std::int32_t *const *>(
          module_base + kTitleMapBucketThresholdsSlotRva);
  output.horizontal_offsets_slot =
      reinterpret_cast<const std::int32_t *const *>(
          module_base + kTitleMapHorizontalOffsetsSlotRva);
  output.zoom_indexes_slot =
      reinterpret_cast<const std::int32_t *const *>(
          module_base + kTitleMapZoomIndexesSlotRva);
  output.degrees_to_radians = reinterpret_cast<const float *>(
      module_base + kTitleMapDegreesToRadiansRva);
  return output;
}

game::TitleMapNavigationCommandStatusV1 AdvanceTitleMapNavigationCommandV1(
    const TitleMapNavigationNativeEnvironmentV1 &title_environment,
    const TitleMapNavigationCameraEnvironmentV1 &camera_environment,
    const TitleMapNavigationCameraAccessV1 &access,
    game::TitleMapNavigationCommandV1 &command) noexcept {
  using Status = game::TitleMapNavigationCommandStatusV1;
  if (IsTitleMapNavigationTerminalV1(command.status)) {
    const bool valid_success =
        (command.status == Status::centered && command.initialized &&
         command.dispatched && command.camera.settled) ||
        (command.status == Status::already_centered && command.initialized &&
         !command.dispatched && command.camera.settled);
    if ((command.status == Status::centered ||
         command.status == Status::already_centered) &&
        !valid_success) {
      command.status = Status::internal_error;
    }
    return command.status;
  }
  try {
    if ((command.dispatched && !command.initialized) ||
        (!command.initialized &&
         (command.native_handler_identity != nullptr ||
          command.native_camera_identity != nullptr))) {
      command.status = Status::internal_error;
      return command.status;
    }
    if (!CameraEnvironmentIsExact(camera_environment)) {
      command.status = Status::unsupported_build;
      return command.status;
    }

    game::TitleMapNavigationFrameV1 binding{};
    game::LandedTitleMapAnchorV1 title{};
    const auto resolved = ResolveLandedTitleMapAnchorV1(
        title_environment, access.title, command.request, binding, title);
    if (resolved != game::ResolveLandedTitleMapAnchorResultV1::resolved) {
      command.status = MapResolverResult(resolved);
      return command.status;
    }
    if (command.initialized &&
        (binding != command.binding || title != command.title)) {
      command.status = Status::state_changed;
      return command.status;
    }

    void *handler = nullptr;
    void *camera = nullptr;
    if (!ResolveHandlerAndCamera(camera_environment, access, handler,
                                 camera)) {
      command.status = Status::camera_state_unavailable;
      return command.status;
    }
    if (command.initialized &&
        (handler != command.native_handler_identity ||
         camera != command.native_camera_identity)) {
      command.status = Status::state_changed;
      return command.status;
    }

    CameraReadbackV1 before{};
    if (!ReadCamera(access, camera, before)) {
      command.status = Status::camera_state_unavailable;
      return command.status;
    }
    const auto seed = command.initialized ? command.raw_expected_target
                                          : before.target;
    CameraPlanV1 plan{};
    const auto plan_result =
        BuildCameraPlan(camera_environment, access, handler, camera,
                        title.native_title, seed, plan);
    if (plan_result != BuildCameraPlanResultV1::ready) {
      command.status =
          plan_result == BuildCameraPlanResultV1::not_centerable
              ? Status::title_not_centerable
              : command.initialized ? Status::state_changed
                                    : Status::camera_state_unavailable;
      return command.status;
    }
    if (command.initialized && !SamePlan(FrozenPlan(command), plan)) {
      command.status = Status::state_changed;
      return command.status;
    }

    if (!command.initialized) {
      command.binding = binding;
      command.title = title;
      command.raw_expected_target = plan.raw_expected;
      command.canonical_expected_target = plan.canonical_expected;
      command.native_handler_identity = handler;
      command.native_camera_identity = camera;
      command.initialized = true;
    }

    const bool target_is_canonical =
        SameExpectedPrefix(before.target, plan.canonical_expected);
    const bool current_equals_target =
        SameFloatArray(before.current, before.target);
    const bool zoom_matches = before.zoom_index == plan.zoom_index &&
                              SameFloat(before.current[3],
                                        plan.expected_zoom) &&
                              SameFloat(before.target[3],
                                        plan.expected_zoom);

    if (!command.dispatched && before.target_write_blocked == 0 &&
        NoTransientPositionShift(before) && target_is_canonical &&
        current_equals_target && zoom_matches) {
      if (!CaptureSameBinding(access, command.binding)) {
        command.status = Status::state_changed;
        return command.status;
      }
      PublishEvidence(plan, before, command.camera, true);
      command.status = Status::already_centered;
      return command.status;
    }

    if (!command.dispatched) {
      // Input-mode inhibition and transient target translation are expected to
      // clear on a later native update.  Do not call A79C70 while either is
      // active because it may partially mutate zoom without writing position.
      if (before.target_write_blocked != 0 ||
          !NoTransientPositionShift(before)) {
        PublishEvidence(plan, before, command.camera, false);
        command.status = Status::pending;
        return command.status;
      }
      if (!InvokeDispatch(camera_environment, access, handler,
                          title.native_title)) {
        command.status = Status::submission_failed;
        return command.status;
      }

      CameraReadbackV1 immediate{};
      void *immediate_handler = nullptr;
      void *immediate_camera = nullptr;
      if (!ResolveHandlerAndCamera(camera_environment, access,
                                   immediate_handler, immediate_camera) ||
          immediate_handler != command.native_handler_identity ||
          immediate_camera != command.native_camera_identity ||
          !ReadCamera(access, immediate_camera, immediate) ||
          immediate.target_write_blocked != 0 ||
          !NoTransientPositionShift(immediate) ||
          immediate.zoom_index != plan.zoom_index ||
          !SameFloatArray(immediate.target, plan.raw_expected) ||
          !SameFloat(immediate.target[3], plan.expected_zoom) ||
          !CaptureSameBinding(access, command.binding)) {
        command.status = Status::submission_failed;
        return command.status;
      }
      command.dispatched = true;
      PublishEvidence(plan, immediate, command.camera, false);
      command.status = Status::pending;
      return command.status;
    }

    // A dispatched action is complete only on a later application-main pump.
    // Native camera update is responsible for interpolating and finally
    // snapping current_state to target_state.
    if (before.target_write_blocked != 0 ||
        !NoTransientPositionShift(before)) {
      command.status = Status::state_changed;
      return command.status;
    }
    const bool target_is_raw =
        SameExpectedPrefix(before.target, plan.raw_expected);
    if (!target_is_raw && !target_is_canonical) {
      command.status = Status::state_changed;
      return command.status;
    }
    if (before.zoom_index != plan.zoom_index ||
        !SameFloat(before.target[3], plan.expected_zoom)) {
      command.status = Status::state_changed;
      return command.status;
    }
    if (!CaptureSameBinding(access, command.binding)) {
      command.status = Status::state_changed;
      return command.status;
    }

    const bool settled = target_is_canonical && current_equals_target &&
                         zoom_matches;
    PublishEvidence(plan, before, command.camera, settled);
    command.status = settled ? Status::centered : Status::pending;
    return command.status;
  } catch (...) {
    command.status = Status::internal_error;
    return command.status;
  }
}

bool IsTitleMapNavigationTerminalV1(
    game::TitleMapNavigationCommandStatusV1 status) noexcept {
  return status != game::TitleMapNavigationCommandStatusV1::pending;
}

std::string_view TitleMapNavigationCommandRejectionCodeV1(
    game::TitleMapNavigationCommandStatusV1 status) noexcept {
  using Status = game::TitleMapNavigationCommandStatusV1;
  switch (status) {
  case Status::pending:
  case Status::centered:
  case Status::already_centered:
    return {};
  case Status::unsupported_build:
    return "unsupported_build";
  case Status::requires_owning_thread:
    return "requires_owning_thread";
  case Status::requires_paused:
    return "requires_paused";
  case Status::map_not_ready:
    return "map_not_ready";
  case Status::title_key_not_found:
    return "title_key_not_found";
  case Status::title_generation_mismatch:
    return "title_generation_mismatch";
  case Status::title_not_centerable:
    return "title_not_centerable";
  case Status::camera_state_unavailable:
    return "camera_state_unavailable";
  case Status::state_changed:
    return "state_changed";
  case Status::submission_failed:
    return "submission_failed";
  case Status::internal_error:
    return "internal_error";
  }
  return "internal_error";
}

} // namespace xar::ck3_11906
