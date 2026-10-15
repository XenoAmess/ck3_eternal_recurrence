#include "xar_bridge/camera_presentation_v1.hpp"
#include "xar_bridge/realm_camera_geometry_v1.hpp"
#include "xar_bridge/ck3_12004_title_map.hpp"
#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include <algorithm>
#include <cmath>
#include <chrono>
#include <climits>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

namespace xar::presentation {
namespace {
namespace abi = ck3_12004;
bool Copy(const void *source, void *target, std::size_t size) noexcept {
  if (!source || !target || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(target, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <class T> bool Read(const void *base, std::size_t offset, T &out) noexcept {
  return base && Copy(static_cast<const std::byte *>(base) + offset, &out, sizeof(out));
}
template <class T> bool Write(void *base, std::size_t offset, const T &value) noexcept {
  return base && Copy(&value, static_cast<std::byte *>(base) + offset, sizeof(value));
}
void *Resolve(void **slot, std::int32_t id, std::size_t identity_offset) noexcept {
  void *storage = nullptr, *slots = nullptr, *object = nullptr;
  std::int32_t count = 0, full_id = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (id <= 0 || !Read(slot, 0, storage) || !storage ||
      !Read(storage, 0x20, slots) || !Read(storage, 0x2C, count) ||
      count < 0 || count > 4'194'304 || index >= static_cast<std::uint32_t>(count) ||
      !Read(slots, static_cast<std::size_t>(index) * 0x10 + 8, object) || !object ||
      !Read(object, identity_offset, full_id) || full_id != id) return nullptr;
  return object;
}
bool ComputeBounds(abi::NativeComputeTitleBoundsV1 function, void *title,
                   Bounds &bounds) noexcept {
  bounds = {INT_MAX, INT_MAX, INT_MIN, INT_MIN};
#if defined(_MSC_VER)
  __try {
#endif
    return function && title && function(title, bounds.data()) && ValidBounds(bounds);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool ResolveCamera(const abi::TitleMapNavigationCameraEnvironmentV1 &e,
                   void *&camera) noexcept {
  void *root = nullptr, *object = nullptr, *cast = nullptr, *handler = nullptr;
  void *vtable = nullptr;
  if (!Read(e.ingame_idler_root_slot, 0, root) || !Read(root, 0x10, object) || !object)
    return false;
#if defined(_MSC_VER)
  __try {
#endif
    cast = e.runtime_dynamic_cast(object, 0, e.idler_base_type_descriptor,
                                 e.ingame_idler_type_descriptor, 0);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return Read(cast, 0x88, handler) && Read(handler, 0, vtable) &&
      vtable == e.expected_handler_vtable &&
      Read(handler, abi::kTitleMapHandlerCameraOffset, camera) &&
      Read(camera, 0, vtable) && vtable == e.expected_camera_vtable;
}
bool Canonicalize(abi::NativeCanonicalizeCameraStateV1 function,
                   void *camera, std::array<float, 6> &state) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    function(camera, state.data());
    return std::all_of(state.begin(), state.end(), [](float v) { return std::isfinite(v); });
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
void *TitleByKey(abi::NativeResolveLandedTitleByKeyV1 function,
                 const char *key) noexcept {
  struct String { union { char local[16]; const char *heap; } data{};
    std::uint64_t size = 0; std::uint64_t capacity = 15; } text;
  text.size = strnlen(key, 128);
  if (text.size == 0 || text.size == 128) return nullptr;
  if (text.size <= 15) std::memcpy(text.data.local, key, text.size);
  else { text.data.heap = key; text.capacity = text.size; }
#if defined(_MSC_VER)
  __try { return function(&text); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#else
  return function(&text);
#endif
}
bool Finite(const std::array<float, 6> &a) noexcept {
  return std::all_of(a.begin(), a.end(), [](float v) { return std::isfinite(v); });
}
} // namespace

CameraPresentationRuntimeV1::~CameraPresentationRuntimeV1() {
  if (shared_) UnmapViewOfFile(shared_);
  if (mapping_) CloseHandle(mapping_);
}
bool CameraPresentationRuntimeV1::Initialize(std::uintptr_t base,
    std::string_view sha, const game::GameAdapter *game) noexcept {
  if (shared_) return true;
  if (!base || !game || sha != abi::kTitleMapNavigationV1ExecutableSha256) return false;
  const auto name = L"Local\\XarCK3CameraPresentationV1-" + std::to_wstring(GetCurrentProcessId());
  mapping_ = CreateFileMappingW(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE,
                               0, static_cast<DWORD>(kMappingBytes), name.c_str());
  if (!mapping_) return false;
  shared_ = static_cast<Shared *>(MapViewOfFile(mapping_, FILE_MAP_ALL_ACCESS, 0, 0, kMappingBytes));
  if (!shared_) { CloseHandle(mapping_); mapping_ = nullptr; return false; }
  *shared_ = Shared{};
  shared_->pid = GetCurrentProcessId();
  game_ = game; base_ = base;
  return true;
}
bool CameraPresentationRuntimeV1::Pump(void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!context) return false;
  try { return static_cast<CameraPresentationRuntimeV1 *>(context)->Advance(stamp); }
  catch (...) {
    static_cast<CameraPresentationRuntimeV1 *>(context)->Publish(Status::unavailable);
    return false;
  }
}
void CameraPresentationRuntimeV1::Publish(Status status) noexcept {
  result_.request_sequence = seen_;
  result_.status = static_cast<std::uint32_t>(status);
  // Odd sequence means publication is in progress; consumers never wait.
  InterlockedIncrement(&shared_->result_sequence);
  std::memcpy(&shared_->result, &result_, sizeof(result_));
  InterlockedIncrement(&shared_->result_sequence);
}
bool CameraPresentationRuntimeV1::Advance(
    const ck3_11906::MainThreadExecutionStampV1 &stamp) {
  if (!shared_ || !stamp.game_state || stamp.tls_main_thread_marker != 1) return false;
  const auto now = GetTickCount64();
  if (now < next_check_ms_) return false;
  next_check_ms_ = now + 50;
  const auto sequence = static_cast<std::uint32_t>(InterlockedCompareExchange(
      &shared_->request_sequence, 0, 0));
  if (sequence & 1U) return false;
  if (sequence == seen_) {
    if (!camera_ || !settle_until_ms_) return false;
    std::array<float, 6> current{}, target{};
    if (!Read(camera_, abi::kTitleMapCameraCurrentStateOffset, current) ||
        !Read(camera_, abi::kTitleMapCameraTargetStateOffset, target) ||
        !Finite(current) || target != result_.target) {
      settle_until_ms_ = 0; Publish(Status::target_changed); return false;
    }
    result_.current = current;
    if (current == target) { settle_until_ms_ = 0; Publish(Status::settled); }
    else if (now > settle_until_ms_) { settle_until_ms_ = 0; Publish(Status::unavailable); }
    return true;
  }
  Request incoming{};
  std::memcpy(&incoming, &shared_->request, sizeof(incoming));
  MemoryBarrier();
  if (sequence != static_cast<std::uint32_t>(InterlockedCompareExchange(
      &shared_->request_sequence, 0, 0))) return false;
  seen_ = sequence; request_ = incoming; result_ = {}; camera_ = nullptr; settle_until_ms_ = 0;
  if (request_.mode == static_cast<std::uint32_t>(Mode::cancel)) {
    Publish(Status::cancelled); return true;
  }
  if (request_.mode > static_cast<std::uint32_t>(Mode::query) ||
      !request_.expires_uptime_ms || now > request_.expires_uptime_ms) {
    Publish(Status::unavailable); return false;
  }
  game::Snapshot snapshot{};
  if (!game_->read_snapshot(snapshot) || !snapshot.map_ready ||
      !snapshot.has_played_character || !snapshot.played_character_alive) {
    Publish(Status::unavailable); return false;
  }
  result_.actor = snapshot.played_character_id; result_.date_raw = snapshot.date_raw;
  if (request_.actor != snapshot.played_character_id ||
      snapshot.date_raw < request_.date_raw || snapshot.date_raw - request_.date_raw > 7 * 24) {
    Publish(Status::stale_actor); return false;
  }
  const bool realm = request_.mode != static_cast<std::uint32_t>(Mode::hotspot);
  const bool active_army = std::any_of(snapshot.player_armies.begin(), snapshot.player_armies.end(),
      [](const auto &army) { return army.in_combat || army.retreating ||
          army.move_target_province_id > 0 || army.army_state == "moving" ||
          army.army_state == "siege" || army.army_state == "sieging" ||
          army.army_state == "gathering"; });
  if (snapshot.has_active_event || snapshot.has_pending_character_interaction ||
      (request_.mode == static_cast<std::uint32_t>(Mode::realm) &&
       (!snapshot.active_wars.empty() || active_army))) {
    Publish(Status::preempted); return false;
  }
  const auto hwnd = reinterpret_cast<HWND>(request_.hwnd);
  DWORD pid = 0; RECT client{};
  if (!IsWindow(hwnd) || IsIconic(hwnd) || !GetWindowThreadProcessId(hwnd, &pid) ||
      pid != GetCurrentProcessId() || !GetClientRect(hwnd, &client)) {
    Publish(Status::unavailable); return false;
  }
  result_.client_width = static_cast<std::uint32_t>(client.right - client.left);
  result_.client_height = static_cast<std::uint32_t>(client.bottom - client.top);
  const auto started = std::chrono::steady_clock::now();
  const auto camera_env = abi::BindTitleMapNavigationCameraEnvironmentV1(base_, true);
  const auto title_env = abi::BindTitleMapNavigationNativeEnvironmentV1(base_, true);
  Bounds aggregate{}; bool initialized = false;
  if (realm) {
    std::vector<std::int32_t> counties;
    ck3_12002::PlayerFactionAlertsAccessV1 access{};
    if (!ck3_12002::ReadSubrealmCountyIdsV1(
            abi::BindPlayerFactionAlertsImage12004(base_, abi::kTitleMapNavigationV1ExecutableSha256),
            access, request_.actor, counties) || counties.empty() || counties.size() > kCountyCapacity) {
      Publish(Status::unavailable); return false;
    }
    for (auto id : counties) {
      Bounds bounds{};
      if (!ComputeBounds(camera_env.compute_title_bounds,
          Resolve(title_env.landed_title_storage_slot, id, 0x10), bounds) ||
          !UnionBounds(aggregate, bounds, initialized)) { Publish(Status::unavailable); return false; }
    }
    result_.county_count = static_cast<std::uint32_t>(counties.size());
    std::copy(counties.begin(), counties.end(), result_.county_ids.begin());
  } else {
    request_.title_key[127] = 0;
    if (!abi::IsCanonicalLandedTitleKeyV1(request_.title_key) ||
        !ComputeBounds(camera_env.compute_title_bounds,
            TitleByKey(title_env.resolve_landed_title_by_key, request_.title_key), aggregate)) {
      Publish(Status::unavailable); return false;
    }
  }
  result_.bounds = aggregate;
  if (request_.mode == static_cast<std::uint32_t>(Mode::query)) {
    Publish(Status::bounds_available); return true;
  }
  void *camera = nullptr; std::uint8_t blocked = 0; float dx = 0, dz = 0;
  std::int32_t extent = 0;
  if (!ResolveCamera(camera_env, camera) ||
      !Read(camera, abi::kTitleMapCameraTargetWriteBlockedOffset, blocked) || blocked ||
      !Read(camera, abi::kTitleMapCameraTransientXOffset, dx) || dx != 0 ||
      !Read(camera, abi::kTitleMapCameraTransientZOffset, dz) || dz != 0 ||
      !ViewportExtent(aggregate, result_.client_width, result_.client_height,
                      request_.padding, extent)) { Publish(Status::unavailable); return false; }
  std::int32_t count = 0; const std::int32_t *thresholds = nullptr, *indexes = nullptr;
  if (!Read(camera_env.bucket_count, 0, count) || count <= 0 || count > 4096 ||
      !Read(camera_env.bucket_thresholds_slot, 0, thresholds) || !thresholds ||
      !Read(camera_env.zoom_indexes_slot, 0, indexes) || !indexes) {
    Publish(Status::unavailable); return false;
  }
  std::vector<std::int32_t> table(static_cast<std::size_t>(count)); std::size_t bucket = 0;
  if (!Copy(thresholds, table.data(), table.size() * sizeof(std::int32_t)) ||
      !NativeBucket(extent, table, bucket) ||
      !Read(indexes, bucket * sizeof(std::int32_t), result_.zoom_index)) {
    Publish(Status::unavailable); return false;
  }
  const float *zoom = nullptr, *angles = nullptr; std::int32_t zoom_count = 0, angles_enabled = 0;
  if (!Read(camera, abi::kTitleMapCameraZoomTableOffset, zoom) || !zoom ||
      !Read(camera, abi::kTitleMapCameraZoomCountOffset, zoom_count) ||
      result_.zoom_index < 0 || result_.zoom_index >= zoom_count ||
      !Read(camera, abi::kTitleMapCameraTargetStateOffset, result_.target) ||
      !Read(zoom, static_cast<std::size_t>(result_.zoom_index) * sizeof(float), result_.target[3]) ||
      !Read(camera, abi::kTitleMapCameraParam4EnabledOffset, angles_enabled)) {
    Publish(Status::unavailable); return false;
  }
  result_.target[0] = static_cast<float>((static_cast<std::int64_t>(aggregate[0]) + aggregate[2]) / 2);
  result_.target[1] = 0;
  result_.target[2] = static_cast<float>((static_cast<std::int64_t>(aggregate[1]) + aggregate[3]) / 2);
  if (angles_enabled) {
    float degrees = 0, conversion = 0;
    if (!Read(camera, abi::kTitleMapCameraParam4TableOffset, angles) || !angles ||
        !Read(angles, static_cast<std::size_t>(result_.zoom_index) * sizeof(float), degrees) ||
        !Read(camera_env.degrees_to_radians, 0, conversion)) { Publish(Status::unavailable); return false; }
    result_.target[4] = degrees * conversion;
  }
  const auto raw = result_.target;
  if (!Finite(raw) || !Canonicalize(camera_env.canonicalize_camera_state, camera, result_.target) ||
      raw[0] != result_.target[0] || raw[2] != result_.target[2]) {
    Publish(Status::unavailable); return false;
  }
  // Equivalent target/index fields used by the reviewed native title command.
  // No game-state/script/input fields are written; normal camera update settles.
  if (!Write(camera, abi::kTitleMapCameraZoomIndexOffset, result_.zoom_index) ||
      !Write(camera, abi::kTitleMapCameraTargetStateOffset, result_.target) ||
      !Read(camera, abi::kTitleMapCameraCurrentStateOffset, result_.current)) {
    Publish(Status::unavailable); return false;
  }
  result_.native_elapsed_us = static_cast<std::uint32_t>(std::chrono::duration_cast<
      std::chrono::microseconds>(std::chrono::steady_clock::now() - started).count());
  camera_ = camera; settle_until_ms_ = now + 5000;
  Publish(Status::submitted);
  return true;
}
} // namespace xar::presentation
