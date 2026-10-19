#include "xar_bridge/camera_presentation_v1.hpp"
#include "xar_bridge/realm_camera_geometry_v1.hpp"
#include "xar_bridge/ck3_12004_title_map.hpp"
#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include "xar_bridge/camera_follow_readonly_12004.hpp"
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
[[maybe_unused]] bool TitleProvinceMatches(const abi::TitleMapNavigationNativeEnvironmentV1 &e,
                          void *title, std::int32_t expected) noexcept {
  void *province = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    province = e.resolve_title_province && title ? e.resolve_title_province(title) : nullptr;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  std::int32_t id = 0;
  void *game = nullptr, *data = nullptr, *array = nullptr, *roundtrip = nullptr;
  std::int32_t count = 0; std::uint32_t tag = 0;
  return Read(province, 0x10, id) && id == expected && id > 0 &&
      Read(province, 0x85C, tag) && tag == 0x50726F76U &&
      Read(e.game_state_slot, 0, game) && Read(game, 0xA0, data) &&
      Read(data, 0x140, array) && Read(data, 0x14C, count) && count > id &&
      Read(array, static_cast<std::size_t>(id) * sizeof(void *), roundtrip) && roundtrip == province;
}
struct GameWindowSearch {
  DWORD pid = 0;
  HWND hwnd = nullptr;
  std::uint32_t count = 0;
};
BOOL CALLBACK FindGameWindow(HWND hwnd, LPARAM context) noexcept {
  auto &search = *reinterpret_cast<GameWindowSearch *>(context);
  DWORD pid = 0; wchar_t title[64]{};
  if (!IsWindow(hwnd) || !GetWindowThreadProcessId(hwnd, &pid) || pid != search.pid ||
      GetWindowTextW(hwnd, title, 64) <= 0 ||
      std::wstring_view(title) != L"Crusader Kings III") return TRUE;
  search.hwnd = hwnd;
  ++search.count;
  return TRUE;
}
bool IsUniqueGameWindow(HWND hwnd) noexcept {
  GameWindowSearch search{GetCurrentProcessId()};
  return EnumWindows(&FindGameWindow, reinterpret_cast<LPARAM>(&search)) &&
      search.count == 1 && search.hwnd == hwnd;
}
} // namespace

CameraPresentationRuntimeV1::~CameraPresentationRuntimeV1() {
  if (shared_) UnmapViewOfFile(shared_);
  if (mapping_) CloseHandle(mapping_);
}
bool CameraPresentationRuntimeV1::Initialize(std::uintptr_t base,
    std::string_view sha, const game::GameAdapter *game,
    const ck3_11906::MainThreadQueryMailboxV1 *mailbox) noexcept {
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
  auto *tracking = reinterpret_cast<tracked::SharedV1 *>(
      reinterpret_cast<std::byte *>(shared_) + tracked::kOffset);
  *tracking = tracked::SharedV1{};
#if !defined(XAR_CK3_ENABLE_CAMERA_TRACKING_V1)
  tracking->magic = 0; // No capability in a default/legacy build.
#endif
  tracking->provider_pid = GetCurrentProcessId();
  game_ = game; base_ = base; mailbox_ = mailbox;
  return true;
}
bool CameraPresentationRuntimeV1::Pump(void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!context) return false;
  try { return static_cast<CameraPresentationRuntimeV1 *>(context)->Advance(stamp); }
  catch (...) {
    auto *self = static_cast<CameraPresentationRuntimeV1 *>(context);
    if (self->tracking_) self->ReleaseTracking(tracked::State::ui_or_identity_unknown);
    self->Publish(Status::unavailable);
    return false;
  }
}
void CameraPresentationRuntimeV1::Publish(Status status,
    const CameraSettleDiagnosticsV1 *diagnostic) noexcept {
  result_.request_sequence = seen_;
  result_.status = static_cast<std::uint32_t>(status);
  // Odd sequence means publication is in progress; consumers never wait.
  InterlockedIncrement(&shared_->result_sequence);
  std::memcpy(&shared_->result, &result_, sizeof(result_));
  // Base Result and optional tail have ONE publication boundary. Every other
  // publication clears the tail; a new result cannot borrow old geometry.
  const CameraSettleDiagnosticsV1 absent{};
  std::memcpy(reinterpret_cast<std::byte *>(shared_) + kCameraSettleDiagnosticsOffsetV1,
              diagnostic ? diagnostic : &absent, sizeof(absent));
  InterlockedIncrement(&shared_->result_sequence);
}
bool CameraPresentationRuntimeV1::Advance(
    const ck3_11906::MainThreadExecutionStampV1 &stamp) {
  if (!shared_) return false;
  if (!stamp.game_state || stamp.tls_main_thread_marker != 1) {
    if (tracking_) ReleaseTracking(tracked::State::world_changed);
    return false;
  }
  // The mailbox supplies this fresh owner-thread stamp. These integers are
  // equality fences, never native pointers reused/dereferenced on later ticks.
  if (tracking_ && (stamp.game_state != tracking_game_state_ ||
      !stamp.jomini_state || stamp.jomini_state != tracking_jomini_state_))
    ReleaseTracking(tracked::State::world_changed);
  const auto now = GetTickCount64();
  auto *tracking = reinterpret_cast<tracked::SharedV1 *>(
      reinterpret_cast<std::byte *>(shared_) + tracked::kOffset);
  const auto connection = tracked::ReadConnectionV1();
  if (tracking->owner_epoch != connection.epoch || tracking->active != connection.active) {
    InterlockedIncrement(&tracking->capability_sequence);
    tracking->owner_epoch = connection.epoch;
    tracking->active = connection.active;
    InterlockedIncrement(&tracking->capability_sequence);
  }
  if (now < next_check_ms_) return false;
  next_check_ms_ = now + 50;
  const auto sequence = static_cast<std::uint32_t>(InterlockedCompareExchange(
      &shared_->request_sequence, 0, 0));
  if (sequence & 1U) return false;
  if (sequence == seen_) {
    if (tracking_) return AdvanceTracking(sequence, now);
    if (!camera_ || !settle_until_ms_) return false;
    std::array<float, 6> current{}, target{};
    // Preserve the old short-circuit read order and exact stability guard.
    const bool current_read = Read(camera_, abi::kTitleMapCameraCurrentStateOffset, current);
    const bool target_read = current_read &&
        Read(camera_, abi::kTitleMapCameraTargetStateOffset, target);
    if (!current_read || !target_read || !Finite(current) || target != result_.target) {
      auto diagnostic = ObserveCameraSettleV1(result_.target, current_read, current,
                                              target_read, target);
      diagnostic.request_sequence = seen_;
      diagnostic.legacy_status = static_cast<std::uint32_t>(Status::target_changed);
      diagnostic.provider_pid = shared_->pid;
      diagnostic.actor = result_.actor;
      diagnostic.submit_date_raw = result_.date_raw;
      diagnostic.request_date_raw = request_.date_raw;
      diagnostic.request_mode = request_.mode;
      diagnostic.county_count = result_.county_count;
      diagnostic.client_width = result_.client_width;
      diagnostic.client_height = result_.client_height;
      diagnostic.zoom_index = result_.zoom_index;
      diagnostic.bounds = result_.bounds;
      diagnostic.observation_uptime_ms = now;
      settle_until_ms_ = 0; Publish(Status::target_changed, &diagnostic); return false;
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
  if (tracking_) ReleaseTracking(tracked::State::superseded);
  seen_ = sequence; request_ = incoming; result_ = {}; camera_ = nullptr; settle_until_ms_ = 0;
  if (request_.mode == static_cast<std::uint32_t>(Mode::tracked_hotspot)) {
    std::memcpy(&tracking_request_, &tracking->request, sizeof(tracking_request_));
    MemoryBarrier();
    if (sequence != static_cast<std::uint32_t>(InterlockedCompareExchange(
        &shared_->request_sequence, 0, 0))) return false;
    tracking_result_ = {};
    tracking_result_.request_sequence = sequence;
    tracking_result_.owner_epoch = tracking_request_.owner_epoch;
    tracking_result_.scope_generation = tracking_request_.scope_generation;
    tracking_result_.actor = tracking_request_.actor;
    tracking_result_.fullarmy_id = tracking_request_.fullarmy_id;
    tracking_ = true; next_position_ms_ = 0;
    tracking_game_state_ = stamp.game_state; tracking_jomini_state_ = stamp.jomini_state;
    // Clear the unrelated legacy settle diagnostic; mode4 has its own result.
    Publish(Status::submitted);
    if (!tracking_jomini_state_) { ReleaseTracking(tracked::State::world_changed); return false; }
    return AdvanceTracking(sequence, now);
  }
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
  if (snapshot.has_active_event || snapshot.has_pending_character_interaction) {
    Publish(Status::preempted); return false;
  }
  const auto hwnd = reinterpret_cast<HWND>(request_.hwnd);
  DWORD pid = 0; RECT client{};
  if (!IsWindow(hwnd) || !GetWindowThreadProcessId(hwnd, &pid) ||
      pid != GetCurrentProcessId() || !IsUniqueGameWindow(hwnd) ||
      !GetClientRect(hwnd, &client) || client.right <= client.left ||
      client.bottom <= client.top) {
    Publish(Status::window_unavailable); return false;
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
  return ApplyBounds(aggregate, sequence, now, started);
}
bool CameraPresentationRuntimeV1::ApplyBounds(const Bounds &aggregate,
    std::uint32_t sequence, std::uint64_t now,
    std::chrono::steady_clock::time_point started) {
  const auto camera_env = abi::BindTitleMapNavigationCameraEnvironmentV1(base_, true);
  void *camera = nullptr; std::uint8_t blocked = 0; float dx = 0, dz = 0;
  std::int32_t extent = 0;
  if (!ResolveCamera(camera_env, camera)) {
    Publish(Status::camera_resolve_unavailable); return false;
  }
  if (!Read(camera, abi::kTitleMapCameraTargetWriteBlockedOffset, blocked) || blocked) {
    Publish(Status::camera_target_write_blocked_or_unreadable); return false;
  }
  if (!Read(camera, abi::kTitleMapCameraTransientXOffset, dx) || dx != 0) {
    Publish(Status::camera_transient_x_active_or_unreadable); return false;
  }
  if (!Read(camera, abi::kTitleMapCameraTransientZOffset, dz) || dz != 0) {
    Publish(Status::camera_transient_z_active_or_unreadable); return false;
  }
  if (!ViewportExtent(aggregate, result_.client_width, result_.client_height,
                      request_.padding, extent)) {
    Publish(Status::camera_viewport_extent_unavailable); return false;
  }
  std::int32_t count = 0; const std::int32_t *thresholds = nullptr, *indexes = nullptr;
  if (!Read(camera_env.bucket_count, 0, count) || count <= 0 || count > 4096 ||
      !Read(camera_env.bucket_thresholds_slot, 0, thresholds) || !thresholds ||
      !Read(camera_env.zoom_indexes_slot, 0, indexes) || !indexes) {
    Publish(Status::camera_bucket_table_unavailable); return false;
  }
  std::vector<std::int32_t> table(static_cast<std::size_t>(count)); std::size_t bucket = 0;
  if (!Copy(thresholds, table.data(), table.size() * sizeof(std::int32_t)) ||
      !NativeBucket(extent, table, bucket)) {
    Publish(Status::camera_bucket_read_or_match_unavailable); return false;
  }
  if (!Read(indexes, bucket * sizeof(std::int32_t), result_.zoom_index)) {
    Publish(Status::camera_zoom_index_unavailable); return false;
  }
  const float *zoom = nullptr, *angles = nullptr; std::int32_t zoom_count = 0, angles_enabled = 0;
  if (!Read(camera, abi::kTitleMapCameraZoomTableOffset, zoom) || !zoom ||
      !Read(camera, abi::kTitleMapCameraZoomCountOffset, zoom_count)) {
    Publish(Status::camera_zoom_or_target_state_unavailable); return false;
  }
  if (result_.zoom_index < 0 || result_.zoom_index >= zoom_count) {
    Publish(Status::camera_zoom_index_unavailable); return false;
  }
  if (!Read(camera, abi::kTitleMapCameraTargetStateOffset, result_.target) ||
      !Read(zoom, static_cast<std::size_t>(result_.zoom_index) * sizeof(float), result_.target[3]) ||
      !Read(camera, abi::kTitleMapCameraParam4EnabledOffset, angles_enabled)) {
    Publish(Status::camera_zoom_or_target_state_unavailable); return false;
  }
  result_.target[0] = static_cast<float>((static_cast<std::int64_t>(aggregate[0]) + aggregate[2]) / 2);
  result_.target[1] = 0;
  result_.target[2] = static_cast<float>((static_cast<std::int64_t>(aggregate[1]) + aggregate[3]) / 2);
  if (angles_enabled) {
    float degrees = 0, conversion = 0;
    if (!Read(camera, abi::kTitleMapCameraParam4TableOffset, angles) || !angles ||
        !Read(angles, static_cast<std::size_t>(result_.zoom_index) * sizeof(float), degrees) ||
        !Read(camera_env.degrees_to_radians, 0, conversion)) {
      Publish(Status::camera_angle_state_unavailable); return false;
    }
    result_.target[4] = degrees * conversion;
  }
  const auto raw = result_.target;
  if (!Finite(raw) || !Canonicalize(camera_env.canonicalize_camera_state, camera, result_.target) ||
      raw[0] != result_.target[0] || raw[2] != result_.target[2]) {
    Publish(Status::camera_canonical_target_unavailable); return false;
  }
  // Equivalent target/index fields used by the reviewed native title command.
  // No game-state/script/input fields are written; normal camera update settles.
  if (sequence != static_cast<std::uint32_t>(InterlockedCompareExchange(
      &shared_->request_sequence, 0, 0))) {
    Publish(Status::preempted); return false;
  }
  if (GetTickCount64() > request_.expires_uptime_ms) {
    Publish(Status::unavailable); return false;
  }
  if (tracking_) {
    if (!mailbox_ || mailbox_->state.load(std::memory_order_acquire) !=
        ck3_11906::MainThreadQueryMailboxStateV1::idle) {
      PublishTracking(tracked::State::yielding_to_gameplay); return false;
    }
    const auto connection = tracked::ReadConnectionV1();
    if (!connection.active || connection.epoch != tracking_request_.owner_epoch) {
      ReleaseTracking(tracked::State::connection_changed); return false;
    }
  }
  if (!Write(camera, abi::kTitleMapCameraZoomIndexOffset, result_.zoom_index) ||
      !Write(camera, abi::kTitleMapCameraTargetStateOffset, result_.target) ||
      !Read(camera, abi::kTitleMapCameraCurrentStateOffset, result_.current)) {
    Publish(Status::camera_target_write_or_readback_unavailable); return false;
  }
  result_.native_elapsed_us = static_cast<std::uint32_t>(std::chrono::duration_cast<
      std::chrono::microseconds>(std::chrono::steady_clock::now() - started).count());
  // Tracking never retains a raw camera pointer across pumps.
  camera_ = tracking_ ? nullptr : camera;
  settle_until_ms_ = tracking_ ? 0 : now + 5000;
  Publish(Status::submitted);
  return true;
}
void CameraPresentationRuntimeV1::PublishTracking(tracked::State state) noexcept {
  auto *tail = reinterpret_cast<tracked::SharedV1 *>(
      reinterpret_cast<std::byte *>(shared_) + tracked::kOffset);
  tracking_result_.state = static_cast<std::uint32_t>(state);
  tracking_result_.observed_uptime_ms = GetTickCount64();
  InterlockedIncrement(&tail->result_sequence);
  std::memcpy(&tail->result, &tracking_result_, sizeof(tracking_result_));
  InterlockedIncrement(&tail->result_sequence);
}
void CameraPresentationRuntimeV1::ReleaseTracking(tracked::State state) noexcept {
  tracking_ = false; camera_ = nullptr; settle_until_ms_ = 0;
  tracking_game_state_ = tracking_jomini_state_ = 0;
  PublishTracking(state);
}
bool CameraPresentationRuntimeV1::ContinueTrackingRead(void *context) noexcept {
  const auto *self = static_cast<CameraPresentationRuntimeV1 *>(context);
  if (!self || !self->tracking_ || !self->shared_ || !self->mailbox_ ||
      GetTickCount64() > self->request_.expires_uptime_ms ||
      self->mailbox_->state.load(std::memory_order_acquire) !=
          ck3_11906::MainThreadQueryMailboxStateV1::idle) return false;
  const auto connection = tracked::ReadConnectionV1();
  return connection.active && connection.epoch == self->tracking_request_.owner_epoch &&
      self->seen_ == static_cast<std::uint32_t>(InterlockedCompareExchange(
          &self->shared_->request_sequence, 0, 0));
}
bool CameraPresentationRuntimeV1::AdvanceTracking(std::uint32_t sequence,
                                                 std::uint64_t now) {
#if !defined(XAR_CK3_ENABLE_CAMERA_TRACKING_V1)
  (void)sequence; (void)now;
  ReleaseTracking(tracked::State::invalid_request); return false;
#else
  next_check_ms_ = now + 200;
  const auto &r = tracking_request_;
  if (!mailbox_ || !tracked::ValidRequestV1(r, sequence) || request_.actor != r.actor ||
      request_.date_raw != r.start_date_raw || !request_.expires_uptime_ms ||
      now > request_.expires_uptime_ms || request_.expires_uptime_ms - now > 120000) {
    ReleaseTracking(tracked::State::invalid_request); return false;
  }
  const auto connection = tracked::ReadConnectionV1();
  if (!connection.active || connection.epoch != r.owner_epoch) {
    ReleaseTracking(tracked::State::connection_changed); return false;
  }
  tracked::Frame frame{};
  const tracked::Request read_request{r.actor, r.fullarmy_id, r.scope_generation,
                                     r.start_date_raw, r.max_date_raw};
  const bool read = tracked::ReadTrackedSubject12004V1(base_, abi::kTitleMapNavigationV1ExecutableSha256,
      read_request, frame, &CameraPresentationRuntimeV1::ContinueTrackingRead, this);
  tracking_result_.date_raw = frame.date_raw;
  tracking_result_.combat_id = frame.combat_id;
  tracking_result_.pending_slot_capacity = frame.pending_slot_capacity;
  tracking_result_.pending_slots_visited = frame.pending_slots_visited;
  tracking_result_.reader_reason = static_cast<std::uint32_t>(frame.reason);
  tracking_result_.reader_elapsed_us = frame.elapsed_us;
  if (!read && frame.reason == tracked::Failure::cooperative_yield) {
    const auto current = tracked::ReadConnectionV1();
    if (!current.active || current.epoch != r.owner_epoch)
      ReleaseTracking(tracked::State::connection_changed);
    else if (sequence != static_cast<std::uint32_t>(InterlockedCompareExchange(
                 &shared_->request_sequence, 0, 0)))
      ReleaseTracking(tracked::State::superseded);
    else if (GetTickCount64() > request_.expires_uptime_ms)
      ReleaseTracking(tracked::State::scope_ended);
    else PublishTracking(tracked::State::yielding_to_gameplay);
    // An incomplete scan authorizes no target write. Keep only the finite
    // request lease; the next idle pump must read the entire fresh UI scope.
    return false;
  }
  const auto gate = read ? tracked::ValidateFrameV1(r, frame) : tracked::State::ui_or_identity_unknown;
  if (gate != tracked::State::tracking) { ReleaseTracking(gate); return false; }
  // Fresh identity/UI/scope above run even on same request and during throttle.
  if (now < next_position_ms_) { PublishTracking(tracked::State::tracking); return true; }
  next_position_ms_ = now + 200;
  const auto province = tracked::ObservedProvinceV1(frame);
  const tracked::Province *entry = nullptr;
  for (std::size_t i = 0; i < r.province_count; ++i)
    if (r.provinces[i].id == province) entry = &r.provinces[i];
  if (!entry) { ReleaseTracking(tracked::State::province_unlisted); return false; }
  const auto ce = abi::BindTitleMapNavigationCameraEnvironmentV1(base_, true);
  if (tracking_result_.target_updates && tracking_result_.province_id == province) {
    void *camera = nullptr; std::array<float, 6> target{};
    if (!ResolveCamera(ce, camera) || !Read(camera, abi::kTitleMapCameraTargetStateOffset, target) ||
        !Finite(target) || target != result_.target) {
      ReleaseTracking(tracked::State::camera_unavailable); return false;
    }
    PublishTracking(tracked::State::tracking); return true;
  }
  const auto te = abi::BindTitleMapNavigationNativeEnvironmentV1(base_, true);
  auto *title = TitleByKey(te.resolve_landed_title_by_key, entry->title_key);
  Bounds bounds{};
  if (!abi::IsCanonicalLandedTitleKeyV1(entry->title_key) ||
      !TitleProvinceMatches(te, title, province) ||
      !ComputeBounds(ce.compute_title_bounds, title, bounds)) {
    ReleaseTracking(tracked::State::geometry_unverified); return false;
  }
  const auto hwnd = reinterpret_cast<HWND>(request_.hwnd);
  DWORD pid = 0; RECT client{};
  if (!IsWindow(hwnd) || !GetWindowThreadProcessId(hwnd, &pid) ||
      pid != GetCurrentProcessId() || !IsUniqueGameWindow(hwnd) ||
      !GetClientRect(hwnd, &client) || client.right <= client.left || client.bottom <= client.top) {
    ReleaseTracking(tracked::State::camera_unavailable); return false;
  }
  result_.client_width = static_cast<std::uint32_t>(client.right - client.left);
  result_.client_height = static_cast<std::uint32_t>(client.bottom - client.top);
  result_.actor = frame.actor; result_.date_raw = frame.date_raw; result_.bounds = bounds;
  if (!ApplyBounds(bounds, sequence, now, std::chrono::steady_clock::now())) {
    if (tracking_result_.state == static_cast<std::uint32_t>(tracked::State::yielding_to_gameplay))
      return false; // retained finite lease; retry only on a later idle pump
    if (tracking_) ReleaseTracking(tracked::State::camera_unavailable);
    return false;
  }
  tracking_result_.province_id = province; ++tracking_result_.target_updates;
  PublishTracking(tracked::State::tracking); return true;
#endif
}
} // namespace xar::presentation
