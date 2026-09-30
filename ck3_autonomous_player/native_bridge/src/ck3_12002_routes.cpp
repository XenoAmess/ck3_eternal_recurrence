#include "xar_bridge/ck3_12002_routes.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
using namespace xar::game;
namespace {
using Bindings = RouteBindings;
using DestroyNativeCommand = RouteBindings::Destructor;

template <class T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}
template <class T> void StoreAt(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
void *ResolveStoredComponent(void **slot, std::int32_t id, std::size_t id_offset) noexcept {
  if (slot == nullptr || *slot == nullptr || id <= 0) return nullptr;
  void *const storage = *slot;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto count = LoadAt<std::int32_t>(storage, 0x2C);
  void *const slots = LoadAt<void *>(storage, 0x20);
  if (slots == nullptr || count <= 0 || index >= static_cast<std::uint32_t>(count)) return nullptr;
  void *const object = LoadAt<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && LoadAt<std::int32_t>(object, id_offset) == id ? object : nullptr;
}
void *ResolveArmy(const Bindings &bindings, std::int32_t id) noexcept {
  return ResolveStoredComponent(bindings.army_storage_slot, id, 0x10);
}
void *ResolveCharacter(const Bindings &bindings, std::int32_t id) noexcept {
  return ResolveStoredComponent(bindings.character_storage_slot, id, 0x18);
}
bool ReadProvinceIdentity(void *p, bool &valid) noexcept {
  valid = p != nullptr && LoadAt<std::uint32_t>(p, 0x85C) == 0x50726F76U && LoadAt<std::int32_t>(p, 0x10) > 0;
  return p != nullptr;
}
bool ReadRegimentIdentity(void *p, bool &valid) noexcept {
  valid = p != nullptr && LoadAt<std::uint32_t>(p, 0x14) == 0x41725267U && LoadAt<std::int32_t>(p, 0x10) > 0;
  return p != nullptr;
}
bool ReadBattleResultIdentity(void *p, bool &valid) noexcept {
  valid = p != nullptr && LoadAt<std::uint32_t>(p, 0x0C) == 0x43625273U && LoadAt<std::int32_t>(p, 8) > 0;
  return p != nullptr;
}
void *ResolveProvince(void *game_state, std::int32_t id) noexcept {
  if (game_state == nullptr || id <= 0) return nullptr;
  void *const data = LoadAt<void *>(game_state, 0xA0);
  if (data == nullptr || id >= LoadAt<std::int32_t>(data, 0x14C)) return nullptr;
  void *const rows = LoadAt<void *>(data, 0x140);
  if (rows == nullptr) return nullptr;
  void *const p = LoadAt<void *>(rows, static_cast<std::size_t>(id) * 8);
  bool valid = false;
  return ReadProvinceIdentity(p, valid) && valid && LoadAt<std::int32_t>(p, 0x10) == id ? p : nullptr;
}
bool ClockMatches(const Bindings &b, const Snapshot &s) noexcept {
  if (!b.enabled || b.game_state_slot == nullptr || b.jomini_state_slot == nullptr ||
      *b.game_state_slot == nullptr || *b.jomini_state_slot == nullptr) return false;
  return LoadAt<std::int32_t>(*b.game_state_slot, 8) == s.date_raw &&
         (LoadAt<std::uint8_t>(*b.jomini_state_slot, 0x20) != 0) == s.paused;
}
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kArmyTargetProvinceOffset = 0x30;
constexpr std::size_t kBattleResultIdOffset = 0x08;
constexpr std::size_t kBattleResultReadyOffset = 0x28;
constexpr std::size_t kCombatAttackerSideOffset = 0x20;
constexpr std::size_t kCombatBattleResultIdOffset = 0x708;
constexpr std::size_t kCombatDefenderSideOffset = 0x368;
constexpr std::size_t kCombatFinalizedOffset = 0x704;
constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatProvinceOffset = 0x6B8;
constexpr std::size_t kCombatSideArmyCountOffset = 0x1C;
constexpr std::size_t kCombatSideArmyIdsOffset = 0x10;
constexpr std::size_t kCombatSideCombatBackPointerOffset = 0xB8;
constexpr std::size_t kCombatSidePrimaryCharacterIdOffset = 0x70;
constexpr std::size_t kCombatWinnerOffset = 0x6E0;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;
constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyRegimentCountOffset = 0x44;
constexpr std::size_t kInternalArmyRegimentIdsOffset = 0x38;
constexpr std::size_t kInternalArmyUnitIdOffset = 0x124;
constexpr std::size_t kMapAdjacencyKindOffset = 0x00;
constexpr std::size_t kMapAdjacencyStride = 0x30;
constexpr std::size_t kMapAdjacencyTargetProvinceIdOffset = 0x04;
constexpr std::size_t kMapNodeAdjacencyCountOffset = 0x5C;
constexpr std::size_t kMapNodeAdjacencyDataOffset = 0x50;
constexpr std::size_t kMapNodePathProvinceInfoOffset = 0xB0;
constexpr std::int32_t kMaximumActualContactProvinceCombats = 1'024;
constexpr std::int32_t kMaximumActualContactProvinceUnits = 4'096;
constexpr std::int32_t kMaximumActualContactRegiments = 4'096;
constexpr std::int32_t kMaximumActualContactSideArmies = 4'096;
constexpr std::int32_t kMaximumProvinceAdjacencies = 4'096;
constexpr std::int32_t kMaximumUnitRouteProvinceInfos = 4'096;
constexpr std::size_t kPathProvinceInfoLandOffset = 0x09;
constexpr std::size_t kPathProvinceInfoWaterOffset = 0x0B;
constexpr std::size_t kProvinceCombatIdCountOffset = 0x764;
constexpr std::size_t kProvinceCombatIdsOffset = 0x758;
constexpr std::size_t kProvinceContactGatePointerOffset = 0x20;
constexpr std::size_t kProvinceFortLevelOffset = 0x850;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kProvinceMapNodeOffset = 0x08;
constexpr std::size_t kProvinceUnitIdCountOffset = 0x74C;
constexpr std::size_t kProvinceUnitIdsOffset = 0x740;
constexpr std::size_t kRegimentCurrentSoldiersOffset = 0x38;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kUnitArmyIdOffset = 0x178;
constexpr std::size_t kUnitCachedCurrentEdgeSpeedOffset = 0x190;
constexpr std::size_t kUnitPathProvinceIdOffset = 0x00;
constexpr std::size_t kUnitPathProvinceInfosOffset = 0x38;
constexpr std::size_t kUnitRetreatStateOffset = 0x170;
struct MoveArmyCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 1;
  std::int32_t army_id = -1;
  std::int32_t destination_province_id = -1;
  std::int32_t move_mode = 0;
  std::int32_t route_kind = 2;
  std::int32_t direct_target = 1;
  std::array<std::byte, 0x130> path_storage{};
};

struct MoveOriginContext {
  const std::uint8_t *mode_is_one = nullptr;
  void *army = nullptr;
  void *destination_province = nullptr;
};

struct alignas(8) MovePathContextStorage {
  std::array<std::byte, 0x70> bytes{};
};

struct MoveArmyCommandCleanup {
  DestroyNativeCommand destroy = nullptr;
  MoveArmyCommand *command = nullptr;

  ~MoveArmyCommandCleanup() {
    if (destroy != nullptr && command != nullptr) {
      destroy(command, 0);
    }
  }
};


enum class ReadAdjacencyKindResult {
  available,
  invalid_encounter,
  unavailable,
};

ReadAdjacencyKindResult ReadProvinceAdjacencyKind(
    void *origin_province, std::int32_t target_province_id,
    std::int32_t &kind) noexcept {
  kind = -1;
  if (origin_province == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const map_node =
      LoadAt<void *>(origin_province, kProvinceMapNodeOffset);
  if (map_node == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const adjacency_data =
      LoadAt<void *>(map_node, kMapNodeAdjacencyDataOffset);
  const auto adjacency_count = LoadAt<std::int32_t>(
      map_node, kMapNodeAdjacencyCountOffset);
  if (adjacency_count < 0 ||
      adjacency_count > kMaximumProvinceAdjacencies ||
      (adjacency_count > 0 && adjacency_data == nullptr)) {
    return ReadAdjacencyKindResult::unavailable;
  }
  bool found = false;
  for (std::int32_t index = 0; index < adjacency_count; ++index) {
    const auto *const edge =
        static_cast<const std::byte *>(adjacency_data) +
        static_cast<std::size_t>(index) * kMapAdjacencyStride;
    if (LoadAt<std::int32_t>(
            edge, kMapAdjacencyTargetProvinceIdOffset) !=
        target_province_id) {
      continue;
    }
    if (found) {
      return ReadAdjacencyKindResult::unavailable;
    }
    found = true;
    kind = LoadAt<std::int32_t>(edge, kMapAdjacencyKindOffset);
  }
  if (!found) {
    return ReadAdjacencyKindResult::invalid_encounter;
  }
  return ReadAdjacencyKindResult::available;
}

void *ResolveRouteOrigin(const Bindings &b, void *game_state, MoveOriginContext *context) noexcept {
  if (b.resolve_move_origin != nullptr) return b.resolve_move_origin(context);
  void *const unit = context->army;
  const auto count = LoadAt<std::int32_t>(unit, 0x44);
  if (count < 0 || count > 4096) return nullptr;
  const bool mode_is_one = *context->mode_is_one != 0;
  if (!mode_is_one) {
    if (b.read_route_progress == nullptr || b.movement_locked_threshold == nullptr || b.get_route_front == nullptr) return nullptr;
    std::int64_t progress = 0;
    if (b.read_route_progress(unit, &progress) != &progress) return nullptr;
    if (progress > *b.movement_locked_threshold && count > 0) {
      void *const front = b.get_route_front(unit);
      bool valid = false;
      if (ReadProvinceIdentity(front, valid) && valid && ResolveProvince(game_state, LoadAt<std::int32_t>(front, 0x10)) == front) return front;
    }
  }
  if (!mode_is_one || count == 0) {
    void *const current = LoadAt<void *>(unit, 0x20);
    bool valid = false;
    if (ReadProvinceIdentity(current, valid) && valid && ResolveProvince(game_state, LoadAt<std::int32_t>(current, 0x10)) == current) return current;
  }
  if (count > 0 && b.get_route_tail != nullptr) {
    void *const tail = b.get_route_tail(unit);
    bool valid = false;
    if (ReadProvinceIdentity(tail, valid) && valid && ResolveProvince(game_state, LoadAt<std::int32_t>(tail, 0x10)) == tail) return tail;
  }
  return context->destination_province;
}
constexpr std::int64_t kRouteDurationScale = 100'000;
constexpr std::int64_t kRouteDurationFailureSentinel = 0xFFFF'FFFFLL;
constexpr std::int64_t kMaximumProjectedRouteDurationRaw =
    365'000LL * kRouteDurationScale;

struct NativeMovePathPrefix {
  void *province_infos = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(offsetof(NativeMovePathPrefix, province_infos) == 0x00);
static_assert(offsetof(NativeMovePathPrefix, capacity) == 0x08);
static_assert(offsetof(NativeMovePathPrefix, count) == 0x0C);
static_assert(sizeof(NativeMovePathPrefix) == 0x10);

bool AddRouteDuration(std::int64_t left, std::int64_t right,
                      std::int64_t &output) noexcept {
  if (left < 0 || right < 0 ||
      left > (std::numeric_limits<std::int64_t>::max)() - right) {
    return false;
  }
  output = left + right;
  return true;
}

bool RouteDurationToDate(std::int32_t date_raw, std::int64_t duration_raw,
                         std::int32_t &output) noexcept {
  if (duration_raw < 0 ||
      duration_raw >
          (std::numeric_limits<std::int64_t>::max)() -
              (kRouteDurationScale / 2)) {
    return false;
  }
  const auto rounded_days =
      (duration_raw + (kRouteDurationScale / 2)) / kRouteDurationScale;
  if (rounded_days >
      ((std::numeric_limits<std::int64_t>::max)() / 24)) {
    return false;
  }
  const auto delta = rounded_days * 24;
  const auto projected = static_cast<std::int64_t>(date_raw) + delta;
  if (projected < (std::numeric_limits<std::int32_t>::min)() ||
      projected > (std::numeric_limits<std::int32_t>::max)()) {
    return false;
  }
  output = static_cast<std::int32_t>(projected);
  return true;
}

bool ReadPathHeader(const void *path_storage,
                    NativeMovePathPrefix &output) noexcept {
  if (path_storage == nullptr) {
    return false;
  }
  output.province_infos = LoadAt<void *>(path_storage, 0x00);
  output.capacity = LoadAt<std::int32_t>(path_storage, 0x08);
  output.count = LoadAt<std::int32_t>(path_storage, 0x0C);
  return output.capacity >= 0 && output.count >= 0 &&
         output.count <= output.capacity &&
         output.count <= kMaximumUnitRouteProvinceInfos &&
         (output.count == 0 || output.province_infos != nullptr);
}

bool PathSharesActiveRouteFront(void *unit, const void *path_storage,
                                bool &output) noexcept {
  output = false;
  if (unit == nullptr) {
    return false;
  }
  NativeMovePathPrefix proposed{};
  NativeMovePathPrefix active{};
  const auto *const active_path =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ReadPathHeader(path_storage, proposed) || proposed.count <= 0 ||
      !ReadPathHeader(active_path, active)) {
    return false;
  }
  if (active.count == 0) {
    return true;
  }
  void *const proposed_front = LoadAt<void *>(proposed.province_infos, 0);
  void *const active_front = LoadAt<void *>(active.province_infos, 0);
  if (proposed_front == nullptr || active_front == nullptr) {
    return false;
  }
  output = LoadAt<std::int32_t>(proposed_front,
                                kUnitPathProvinceIdOffset) ==
           LoadAt<std::int32_t>(active_front,
                                kUnitPathProvinceIdOffset);
  return true;
}

bool ReadRouteTravelSpeeds(const Bindings &bindings, void *unit,
                           std::int64_t &land_speed,
                           std::int64_t &naval_speed) noexcept {
  land_speed = 0;
  naval_speed = 0;
  if (bindings.read_unit_land_route_speed == nullptr ||
      bindings.read_unit_naval_route_speed == nullptr || unit == nullptr) {
    return false;
  }
  return bindings.read_unit_land_route_speed(unit, &land_speed) ==
             &land_speed &&
         bindings.read_unit_naval_route_speed(unit, &naval_speed) ==
             &naval_speed;
}

bool CurrentEdgeSpeedIsPositive(const Bindings &bindings, void *unit,
                                const void *path_storage) noexcept {
  bool shares_active_front = false;
  if (!PathSharesActiveRouteFront(unit, path_storage,
                                  shares_active_front)) {
    return false;
  }
  if (!shares_active_front) {
    return true;
  }
  auto current_edge_speed = LoadAt<std::int64_t>(
      unit, kUnitCachedCurrentEdgeSpeedOffset);
  if (current_edge_speed > 0) {
    return true;
  }
  if (bindings.read_unit_current_edge_speed == nullptr) {
    return false;
  }
  current_edge_speed = 0;
  return bindings.read_unit_current_edge_speed(
             unit, &current_edge_speed) == &current_edge_speed &&
         current_edge_speed > 0;
}

bool ValidateRouteTimingInputs(const Bindings &bindings, void *game_state,
                               void *unit, const void *path_storage,
                               void *origin_province) noexcept {
  NativeMovePathPrefix path{};
  std::int64_t land_speed = 0;
  std::int64_t naval_speed = 0;
  if (game_state == nullptr || unit == nullptr || origin_province == nullptr ||
      !ReadPathHeader(path_storage, path) || path.count <= 0 ||
      !ReadRouteTravelSpeeds(bindings, unit, land_speed, naval_speed) ||
      !CurrentEdgeSpeedIsPositive(bindings, unit, path_storage)) {
    return false;
  }

  void *edge_origin = origin_province;
  void *const origin_map_node =
      LoadAt<void *>(edge_origin, kProvinceMapNodeOffset);
  if (origin_map_node == nullptr) {
    return false;
  }
  void *source_info =
      LoadAt<void *>(origin_map_node, kMapNodePathProvinceInfoOffset);
  if (source_info == nullptr) {
    return false;
  }

  for (std::int32_t index = 0; index < path.count; ++index) {
    void *const destination_info = LoadAt<void *>(
        path.province_infos,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (destination_info == nullptr) {
      return false;
    }
    const auto destination_id = LoadAt<std::int32_t>(
        destination_info, kUnitPathProvinceIdOffset);
    void *const destination = ResolveProvince(game_state, destination_id);
    std::int32_t adjacency_kind = -1;
    if (destination == nullptr ||
        ReadProvinceAdjacencyKind(edge_origin, destination_id,
                                  adjacency_kind) !=
            ReadAdjacencyKindResult::available) {
      return false;
    }

    const bool source_is_land =
        LoadAt<std::uint8_t>(source_info, kPathProvinceInfoLandOffset) != 0;
    const bool source_is_water =
        LoadAt<std::uint8_t>(source_info, kPathProvinceInfoWaterOffset) != 0;
    const bool destination_is_land = LoadAt<std::uint8_t>(
                                               destination_info,
                                               kPathProvinceInfoLandOffset) !=
                                           0;
    const bool destination_is_water = LoadAt<std::uint8_t>(
                                                destination_info,
                                                kPathProvinceInfoWaterOffset) !=
                                            0;
    // Exact 0x2649320 branch order: embark/disembark use their fixed costs;
    // same-medium travel divides by the corresponding unit speed.  A zero
    // divisor is reported only as the additive uint32 0xffffffff value, so it
    // must be rejected before the duration ABI can silently accumulate it.
    if (source_is_land) {
      if (!destination_is_water && land_speed <= 0) {
        return false;
      }
    } else if (source_is_water) {
      if (!destination_is_land && naval_speed <= 0) {
        return false;
      }
    }

    edge_origin = destination;
    source_info = destination_info;
  }
  return true;
}

bool ProjectPathTimeline(
    const Bindings &bindings, void *game_state, void *unit,
    const void *path_storage, void *origin_province,
    std::int32_t date_raw, std::int64_t base_duration_raw,
    std::vector<std::int32_t> &province_ids,
    std::vector<std::int32_t> &arrival_date_raws) noexcept {
  province_ids.clear();
  arrival_date_raws.clear();
  if (bindings.read_route_travel_duration == nullptr || game_state == nullptr ||
      unit == nullptr || origin_province == nullptr || base_duration_raw < 0) {
    return false;
  }

  NativeMovePathPrefix full{};
  if (!ReadPathHeader(path_storage, full)) {
    return false;
  }
  if (full.count > 0 &&
      !ValidateRouteTimingInputs(bindings, game_state, unit, path_storage,
                                 origin_province)) {
    return false;
  }
  province_ids.reserve(static_cast<std::size_t>(full.count));
  arrival_date_raws.reserve(static_cast<std::size_t>(full.count));
  std::int32_t prior_arrival = date_raw;
  std::int64_t prior_path_duration_raw = 0;
  void *edge_origin = origin_province;
  for (std::int32_t index = 0; index < full.count; ++index) {
    void *const province_info = LoadAt<void *>(
        full.province_infos, static_cast<std::size_t>(index) * sizeof(void *));
    if (province_info == nullptr) {
      return false;
    }
    const auto province_id =
        LoadAt<std::int32_t>(province_info, kUnitPathProvinceIdOffset);
    void *const next_province = ResolveProvince(game_state, province_id);
    std::int32_t adjacency_kind = -1;
    if (next_province == nullptr ||
        ReadProvinceAdjacencyKind(edge_origin, province_id,
                                  adjacency_kind) !=
            ReadAdjacencyKindResult::available) {
      return false;
    }
    edge_origin = next_province;

    // The original helper reads only MovePath+0/+0x0C.  Give every prefix its
    // own zeroed full-size view so no owned allocator/cost tail can be
    // mistaken for shallow storage or destroyed by this reader.
    std::array<std::byte, 0x130> prefix{};
    StoreAt(prefix.data(), 0x00, full.province_infos);
    StoreAt(prefix.data(), 0x0C, index + 1);
    std::int64_t path_duration_raw = -1;
    if (bindings.read_route_travel_duration(
            unit, &path_duration_raw, prefix.data(), origin_province) !=
            &path_duration_raw ||
        path_duration_raw < 0) {
      return false;
    }
    if (path_duration_raw == kRouteDurationFailureSentinel ||
        path_duration_raw > kMaximumProjectedRouteDurationRaw ||
        path_duration_raw < prior_path_duration_raw) {
      return false;
    }
    std::int64_t total_duration_raw = 0;
    std::int32_t arrival_date_raw = 0;
    if (!AddRouteDuration(base_duration_raw, path_duration_raw,
                          total_duration_raw) ||
        !RouteDurationToDate(date_raw, total_duration_raw,
                             arrival_date_raw) ||
        arrival_date_raw < prior_arrival) {
      return false;
    }
    province_ids.push_back(province_id);
    arrival_date_raws.push_back(arrival_date_raw);
    prior_arrival = arrival_date_raw;
    prior_path_duration_raw = path_duration_raw;
  }
  return province_ids.size() == arrival_date_raws.size();
}

bool ReadFirstActiveEdgeDuration(const Bindings &bindings, void *game_state,
                                 void *unit, void *current_province,
                                 std::int32_t expected_front_province_id,
                                 std::int64_t &duration_raw) noexcept {
  duration_raw = -1;
  NativeMovePathPrefix active{};
  const auto *const path_storage =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ReadPathHeader(path_storage, active) || active.count <= 0) {
    return false;
  }
  void *const first_info = LoadAt<void *>(active.province_infos, 0);
  if (first_info == nullptr ||
      LoadAt<std::int32_t>(first_info, kUnitPathProvinceIdOffset) !=
          expected_front_province_id ||
      ResolveProvince(game_state, expected_front_province_id) == nullptr) {
    return false;
  }
  std::array<std::byte, 0x130> prefix{};
  StoreAt(prefix.data(), 0x00, active.province_infos);
  StoreAt(prefix.data(), 0x0C, std::int32_t{1});
  const bool read = ValidateRouteTimingInputs(
                        bindings, game_state, unit, path_storage,
                        current_province) &&
                    bindings.read_route_travel_duration(
             unit, &duration_raw, prefix.data(), current_province) ==
             &duration_raw &&
         duration_raw >= 0 &&
         duration_raw != kRouteDurationFailureSentinel &&
         duration_raw <= kMaximumProjectedRouteDurationRaw;
  return read;
}

const ArmySnapshot *FindArmySnapshot(const Snapshot &snapshot,
                                     std::int32_t army_id) noexcept {
  for (const auto &army : snapshot.player_armies) {
    if (army.army_id == army_id) {
      return &army;
    }
  }
  for (const auto &war : snapshot.active_wars) {
    for (const auto &army : war.allied_armies) {
      if (army.army_id == army_id) {
        return &army;
      }
    }
    for (const auto &army : war.enemy_armies) {
      if (army.army_id == army_id) {
        return &army;
      }
    }
  }
  return nullptr;
}

bool CollectCompleteHostileScope(const Snapshot &snapshot,
                                 std::int32_t subject_army_id,
                                 std::vector<std::int32_t> &output) {
  (void)subject_army_id;
  output.clear();
  bool found_active_war = false;
  for (const auto &war : snapshot.active_wars) {
    found_active_war = true;
    for (const auto &enemy : war.enemy_armies) {
      if (!enemy.retreating && enemy.army_id > 0 &&
          std::find(output.begin(), output.end(), enemy.army_id) ==
              output.end()) {
        output.push_back(enemy.army_id);
      }
    }
  }
  std::sort(output.begin(), output.end());
  return found_active_war && !output.empty();
}

bool SameCanonicalIdSet(std::vector<std::int32_t> left,
                        std::vector<std::int32_t> right) {
  std::sort(left.begin(), left.end());
  std::sort(right.begin(), right.end());
  return left == right &&
         std::adjacent_find(left.begin(), left.end()) == left.end() &&
         std::adjacent_find(right.begin(), right.end()) == right.end();
}

bool BuildActiveRouteTimeline(const Bindings &bindings, void *game_state,
                              std::int32_t date_raw,
                              const ArmySnapshot &snapshot,
                              game::RouteTimelineSnapshot &output) noexcept {
  output = {};
  output.army_id = snapshot.army_id;
  if (!snapshot.has_current_province) {
    return false;
  }
  output.current_province_id = snapshot.current_province_id;
  output.effective_origin_province_id = snapshot.current_province_id;
  void *const unit = ResolveArmy(bindings, snapshot.army_id);
  void *const current_province =
      ResolveProvince(game_state, snapshot.current_province_id);
  if (unit == nullptr || current_province == nullptr ||
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != current_province) {
    return false;
  }
  if (snapshot.route_province_ids.empty()) {
    NativeMovePathPrefix active{};
    const auto *const path_storage =
        static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
    output.timeline_observable =
        ReadPathHeader(path_storage, active) && active.count == 0;
    return output.timeline_observable;
  }
  output.effective_origin_province_id = snapshot.route_province_ids.front();
  const auto *const path_storage =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  if (!ProjectPathTimeline(bindings, game_state, unit, path_storage,
                           current_province, date_raw, 0,
                           output.route_province_ids,
                           output.arrival_date_raws) ||
      output.route_province_ids != snapshot.route_province_ids) {
    output.route_province_ids.clear();
    output.arrival_date_raws.clear();
    return false;
  }
  output.timeline_observable = true;
  return true;
}

RouteContactHorizonStatus BuildSubjectRouteTimeline(
    const Bindings &bindings, void *game_state, const Snapshot &snapshot,
    const game::RouteContactHorizonRequest &request,
    game::RouteTimelineSnapshot &output) noexcept {
  output = {};
  output.army_id = request.subject_army_id;
  const ArmySnapshot *selected = nullptr;
  for (const auto &candidate : snapshot.player_armies) {
    if (candidate.army_id == request.subject_army_id) {
      selected = &candidate;
      break;
    }
  }
  if (selected == nullptr) {
    return RouteContactHorizonStatus::subject_army_not_found;
  }
  if (!selected->controllable) {
    return RouteContactHorizonStatus::subject_army_not_controllable;
  }
  if (!selected->has_current_province) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  void *const unit = ResolveArmy(bindings, request.subject_army_id);
  void *const current_province =
      ResolveProvince(game_state, selected->current_province_id);
  void *const target_province =
      ResolveProvince(game_state, request.target_province_id);
  if (unit == nullptr || current_province == nullptr ||
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != current_province) {
    return RouteContactHorizonStatus::state_changed;
  }
  if (target_province == nullptr) {
    return RouteContactHorizonStatus::target_province_not_found;
  }

  // Re-querying the already committed target must project the exact stored
  // active MovePath.  Re-running A* could produce a different equal-cost tail
  // and would no longer prove the route the simulation is actually following.
  if (!selected->route_province_ids.empty() &&
      selected->route_province_ids.back() == request.target_province_id) {
    return BuildActiveRouteTimeline(bindings, game_state, snapshot.date_raw,
                                    *selected, output)
               ? RouteContactHorizonStatus::available
               : RouteContactHorizonStatus::timeline_unavailable;
  }

  constexpr std::int32_t direct_target = 1;
  constexpr std::int32_t route_kind = 2;
  const auto move_mode =
      bindings.get_army_move_mode(unit, target_province, direct_target);
  if (move_mode == 2) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  const std::uint8_t mode_is_one = move_mode == 1 ? 1U : 0U;
  MoveOriginContext origin_context{&mode_is_one, unit, target_province};
  void *const effective_origin = ResolveRouteOrigin(bindings, game_state, &origin_context);
  if (effective_origin == nullptr) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  const auto effective_origin_id =
      LoadAt<std::int32_t>(effective_origin, kProvinceIdOffset);
  if (ResolveProvince(game_state, effective_origin_id) != effective_origin ||
      (effective_origin_id != selected->current_province_id &&
       (selected->route_province_ids.empty() ||
        effective_origin_id != selected->route_province_ids.front()))) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  output.current_province_id = selected->current_province_id;
  output.effective_origin_province_id = effective_origin_id;
  std::int64_t first_edge_duration_raw = 0;
  if (effective_origin_id != selected->current_province_id) {
    if (!ReadFirstActiveEdgeDuration(
            bindings, game_state, unit, current_province,
            effective_origin_id, first_edge_duration_raw)) {
      return RouteContactHorizonStatus::timeline_unavailable;
    }
    std::int32_t first_arrival = 0;
    if (!RouteDurationToDate(snapshot.date_raw, first_edge_duration_raw,
                             first_arrival)) {
      return RouteContactHorizonStatus::timeline_unavailable;
    }
    output.route_province_ids.push_back(effective_origin_id);
    output.arrival_date_raws.push_back(first_arrival);
  }

  if (effective_origin_id == request.target_province_id) {
    output.timeline_observable = true;
    return RouteContactHorizonStatus::available;
  }
  if (effective_origin_id == selected->current_province_id &&
      selected->current_province_id == request.target_province_id) {
    output.timeline_observable = true;
    return RouteContactHorizonStatus::available;
  }

  MoveArmyCommand command{};
  command.primary_vtable = bindings.move_army_primary_vtable;
  command.secondary_vtable = bindings.move_army_secondary_vtable;
  command.command_kind = 1;
  command.army_id = request.subject_army_id;
  command.destination_province_id = request.target_province_id;
  command.move_mode = move_mode;
  command.route_kind = route_kind;
  command.direct_target = direct_target;
  if (bindings.construct_army_move_path(command.path_storage.data()) !=
      command.path_storage.data()) {
    return RouteContactHorizonStatus::route_unavailable;
  }
  MoveArmyCommandCleanup cleanup{bindings.destroy_move_army_command,
                                 &command};
  MovePathContextStorage path_context{};
  if (bindings.construct_move_path_context(path_context.bytes.data(), unit) !=
          path_context.bytes.data() ||
      !bindings.build_army_move_route(
          path_context.bytes.data(), effective_origin, target_province,
          route_kind, command.path_storage.data())) {
    return RouteContactHorizonStatus::route_unavailable;
  }

  std::vector<std::int32_t> tail_ids;
  std::vector<std::int32_t> tail_arrivals;
  if (!ProjectPathTimeline(
          bindings, game_state, unit, command.path_storage.data(),
          effective_origin, snapshot.date_raw, first_edge_duration_raw,
          tail_ids, tail_arrivals) || tail_ids.empty() ||
      tail_ids.back() != request.target_province_id) {
    return RouteContactHorizonStatus::timeline_unavailable;
  }
  output.route_province_ids.insert(output.route_province_ids.end(),
                                   tail_ids.begin(), tail_ids.end());
  output.arrival_date_raws.insert(output.arrival_date_raws.end(),
                                  tail_arrivals.begin(), tail_arrivals.end());
  if (output.route_province_ids.size() != output.arrival_date_raws.size()) {
    return RouteContactHorizonStatus::timeline_unavailable;
  }
  output.timeline_observable = true;
  return RouteContactHorizonStatus::available;
}

struct ProvinceOccupancyInterval {
  std::int32_t province_id = -1;
  std::int32_t enter = 0;
  std::int32_t leave = 0;
};

struct RouteEdgeInterval {
  std::int32_t from = -1;
  std::int32_t to = -1;
  std::int32_t depart = 0;
  std::int32_t arrive = 0;
};

void BuildTimelineIntervals(const game::RouteTimelineSnapshot &route,
                            std::int32_t horizon_start,
                            std::int32_t horizon_end,
                            std::vector<ProvinceOccupancyInterval> &occupancy,
                            std::vector<RouteEdgeInterval> &edges) {
  occupancy.clear();
  edges.clear();
  if (route.route_province_ids.size() != route.arrival_date_raws.size()) {
    return;
  }
  const auto first_leave = route.arrival_date_raws.empty()
                               ? horizon_end
                               : route.arrival_date_raws.front();
  occupancy.push_back(
      {route.current_province_id, horizon_start, first_leave});
  std::int32_t from = route.current_province_id;
  std::int32_t depart = horizon_start;
  for (std::size_t index = 0; index < route.route_province_ids.size();
       ++index) {
    const auto to = route.route_province_ids[index];
    const auto arrive = route.arrival_date_raws[index];
    edges.push_back({from, to, depart, arrive});
    const auto leave = index + 1U < route.arrival_date_raws.size()
                           ? route.arrival_date_raws[index + 1U]
                           : horizon_end;
    occupancy.push_back({to, arrive, leave});
    from = to;
    depart = arrive;
  }
}

bool ClosedIntervalsOverlap(std::int32_t left_start,
                            std::int32_t left_end,
                            std::int32_t right_start,
                            std::int32_t right_end,
                            std::int32_t horizon_start,
                            std::int32_t horizon_end,
                            std::int32_t &overlap_start,
                            std::int32_t &overlap_end) noexcept {
  overlap_start = (std::max)({left_start, right_start, horizon_start});
  overlap_end = (std::min)({left_end, right_end, horizon_end});
  return overlap_start <= overlap_end;
}

void AppendContactConflicts(
    const game::RouteTimelineSnapshot &subject,
    const game::RouteTimelineSnapshot &hostile, std::int32_t horizon_start,
    std::int32_t horizon_end,
    std::vector<game::RouteContactConflictSnapshot> &output) {
  std::vector<ProvinceOccupancyInterval> subject_occupancy;
  std::vector<ProvinceOccupancyInterval> hostile_occupancy;
  std::vector<RouteEdgeInterval> subject_edges;
  std::vector<RouteEdgeInterval> hostile_edges;
  BuildTimelineIntervals(subject, horizon_start, horizon_end,
                         subject_occupancy, subject_edges);
  BuildTimelineIntervals(hostile, horizon_start, horizon_end,
                         hostile_occupancy, hostile_edges);
  for (const auto &left : subject_occupancy) {
    for (const auto &right : hostile_occupancy) {
      std::int32_t overlap_start = 0;
      std::int32_t overlap_end = 0;
      if (left.province_id == right.province_id &&
          ClosedIntervalsOverlap(left.enter, left.leave, right.enter,
                                 right.leave, horizon_start, horizon_end,
                                 overlap_start, overlap_end)) {
        game::RouteContactConflictSnapshot conflict{};
        conflict.kind = "same_province";
        conflict.hostile_army_id = hostile.army_id;
        conflict.province_id = left.province_id;
        conflict.overlap_start_date_raw = overlap_start;
        conflict.overlap_end_date_raw = overlap_end;
        if (std::find(output.begin(), output.end(), conflict) == output.end()) {
          output.push_back(std::move(conflict));
        }
      }
    }
  }
  for (const auto &left : subject_edges) {
    for (const auto &right : hostile_edges) {
      std::int32_t overlap_start = 0;
      std::int32_t overlap_end = 0;
      if (left.from == right.to && left.to == right.from &&
          ClosedIntervalsOverlap(left.depart, left.arrive, right.depart,
                                 right.arrive, horizon_start, horizon_end,
                                 overlap_start, overlap_end)) {
        game::RouteContactConflictSnapshot conflict{};
        conflict.kind = "opposing_edge";
        conflict.hostile_army_id = hostile.army_id;
        conflict.subject_from_province_id = left.from;
        conflict.subject_to_province_id = left.to;
        conflict.hostile_from_province_id = right.from;
        conflict.hostile_to_province_id = right.to;
        conflict.overlap_start_date_raw = overlap_start;
        conflict.overlap_end_date_raw = overlap_end;
        if (std::find(output.begin(), output.end(), conflict) == output.end()) {
          output.push_back(std::move(conflict));
        }
      }
    }
  }
}

RouteContactHorizonStatus ReadRouteContactHorizonSample(
    const Bindings &bindings, const Snapshot &paused_scope, const RouteContactHorizonRequest &request,
    RouteContactHorizonSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  output.hostile_army_ids = request.hostile_army_ids;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.get_army_move_mode == nullptr ||
      (bindings.resolve_move_origin == nullptr && bindings.read_route_progress == nullptr) ||
      bindings.construct_move_path_context == nullptr ||
      bindings.construct_army_move_path == nullptr ||
      bindings.build_army_move_route == nullptr ||
      bindings.destroy_move_army_command == nullptr ||
      bindings.read_unit_land_route_speed == nullptr ||
      bindings.read_unit_naval_route_speed == nullptr ||
      bindings.read_unit_current_edge_speed == nullptr ||
      bindings.read_route_travel_duration == nullptr ||
      request.subject_army_id <= 0 || request.target_province_id <= 0 ||
      request.hostile_army_ids.empty() ||
      request.hostile_army_ids.size() > 64 ||
      std::find(request.hostile_army_ids.begin(),
                request.hostile_army_ids.end(),
                request.subject_army_id) != request.hostile_army_ids.end()) {
    output.status = RouteContactHorizonStatus::unavailable;
    return output.status;
  }
  for (const auto hostile_id : request.hostile_army_ids) {
    if (hostile_id <= 0 ||
        std::count(request.hostile_army_ids.begin(),
                   request.hostile_army_ids.end(), hostile_id) != 1) {
      output.status = RouteContactHorizonStatus::unavailable;
      return output.status;
    }
  }

  const Snapshot &before = paused_scope;
  if (!ClockMatches(bindings, before)) {
    output.status = RouteContactHorizonStatus::unavailable;
    return output.status;
  }
  if (!before.paused) {
    output.status = RouteContactHorizonStatus::requires_paused;
    return output.status;
  }
  if (before.date_raw >
      (std::numeric_limits<std::int32_t>::max)() - 24) {
    output.status = RouteContactHorizonStatus::timeline_unavailable;
    return output.status;
  }
  output.date_raw = before.date_raw;
  output.horizon_start_date_raw = before.date_raw;
  output.horizon_end_date_raw = before.date_raw + 24;

  std::vector<std::int32_t> exact_hostile_scope;
  if (!CollectCompleteHostileScope(before, request.subject_army_id,
                                   exact_hostile_scope) ||
      !SameCanonicalIdSet(exact_hostile_scope,
                          request.hostile_army_ids)) {
    output.status = RouteContactHorizonStatus::hostile_scope_mismatch;
    return output.status;
  }

  void *const game_state = *bindings.game_state_slot;
  const auto subject_status = BuildSubjectRouteTimeline(
      bindings, game_state, before, request, output.subject_route);
  if (subject_status != RouteContactHorizonStatus::available) {
    output.status = subject_status;
    return output.status;
  }
  output.hostile_routes.clear();
  output.hostile_routes.reserve(request.hostile_army_ids.size());
  for (const auto hostile_id : request.hostile_army_ids) {
    const auto *const hostile = FindArmySnapshot(before, hostile_id);
    if (hostile == nullptr || hostile->retreating) {
      output.hostile_routes.clear();
      output.status = RouteContactHorizonStatus::state_changed;
      return output.status;
    }
    output.hostile_routes.emplace_back();
    if (!BuildActiveRouteTimeline(bindings, game_state, before.date_raw,
                                  *hostile,
                                  output.hostile_routes.back())) {
      output.hostile_routes.clear();
      output.status = RouteContactHorizonStatus::timeline_unavailable;
      return output.status;
    }
  }

  if (!ClockMatches(bindings, before) ||
      ResolveProvince(game_state, request.target_province_id) == nullptr) {
    output.subject_route = {};
    output.hostile_routes.clear();
    output.status = RouteContactHorizonStatus::state_changed;
    return output.status;
  }

  output.conflicts.clear();
  for (const auto &hostile : output.hostile_routes) {
    AppendContactConflicts(output.subject_route, hostile,
                           output.horizon_start_date_raw,
                           output.horizon_end_date_raw, output.conflicts);
  }
  output.one_day_contact_free = output.conflicts.empty();
  output.status = RouteContactHorizonStatus::available;
  return output.status;
}

bool ReadContactIdArray(const void *owner, std::size_t data_offset,
                        std::size_t count_offset, std::int32_t maximum,
                        std::vector<std::int32_t> &output,
                        bool require_strictly_sorted) {
  output.clear();
  void *const data = LoadAt<void *>(owner, data_offset);
  const auto count = LoadAt<std::int32_t>(owner, count_offset);
  if (count < 0 || count > maximum || (count > 0 && data == nullptr)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = LoadAt<std::int32_t>(
        data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (id <= 0 ||
        (require_strictly_sorted && !output.empty() &&
         output.back() >= id)) {
      output.clear();
      return false;
    }
    output.push_back(id);
  }
  return true;
}

bool ResolveContactCharacter(const Bindings &bindings,
                             std::int32_t character_id,
                             void *&character) noexcept {
  character = ResolveCharacter(bindings, character_id);
  if (character == nullptr) {
    return false;
  }
  bool identity_valid = false;
  identity_valid = LoadAt<std::uint32_t>(character, 0x1C) == 0x43686172U;
  return identity_valid;
}

bool NativeArmyIdsToPublicUnitIds(
    const Bindings &bindings,
    const std::vector<std::int32_t> &native_army_ids,
    std::vector<std::int32_t> &public_unit_ids) noexcept {
  public_unit_ids.clear();
  public_unit_ids.reserve(native_army_ids.size());
  for (const auto native_id : native_army_ids) {
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_id,
        kInternalArmyIdOffset);
    if (army == nullptr) {
      public_unit_ids.clear();
      return false;
    }
    const auto unit_id =
        LoadAt<std::int32_t>(army, kInternalArmyUnitIdOffset);
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, unit_id, kArmyIdOffset);
    if (unit == nullptr ||
        LoadAt<std::int32_t>(unit, kUnitArmyIdOffset) != native_id) {
      public_unit_ids.clear();
      return false;
    }
    public_unit_ids.push_back(unit_id);
  }
  return true;
}

bool ReadCombatSidePublicUnitIds(
    const Bindings &bindings, const void *combat,
    std::size_t side_offset,
    std::vector<std::int32_t> &output) noexcept {
  std::vector<std::int32_t> native_ids;
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  return ReadContactIdArray(
             side, kCombatSideArmyIdsOffset, kCombatSideArmyCountOffset,
             kMaximumActualContactSideArmies, native_ids, false) &&
         NativeArmyIdsToPublicUnitIds(bindings, native_ids, output);
}

bool ReadActiveCombatSideIds(
    const Bindings &bindings, const void *combat,
    std::size_t side_offset, std::int32_t expected_combat_id,
    std::vector<std::int32_t> &native_ids,
    std::vector<std::int32_t> &public_unit_ids) noexcept {
  native_ids.clear();
  public_unit_ids.clear();
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  if (LoadAt<const void *>(side, kCombatSideCombatBackPointerOffset) != combat ||
      !ReadContactIdArray(
          side, kCombatSideArmyIdsOffset, kCombatSideArmyCountOffset,
          kMaximumActualContactSideArmies, native_ids, false) ||
      native_ids.empty()) {
    return false;
  }
  public_unit_ids.reserve(native_ids.size());
  for (const auto native_id : native_ids) {
    void *const army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, native_id,
        kInternalArmyIdOffset);
    if (army == nullptr ||
        LoadAt<std::int32_t>(army, kInternalArmyCombatIdOffset) !=
            expected_combat_id) {
      native_ids.clear();
      public_unit_ids.clear();
      return false;
    }
    const auto unit_id =
        LoadAt<std::int32_t>(army, kInternalArmyUnitIdOffset);
    void *const unit = ResolveStoredComponent(
        bindings.army_storage_slot, unit_id, kArmyIdOffset);
    if (unit == nullptr ||
        LoadAt<std::int32_t>(unit, kUnitArmyIdOffset) != native_id ||
        std::find(public_unit_ids.begin(), public_unit_ids.end(), unit_id) !=
            public_unit_ids.end()) {
      native_ids.clear();
      public_unit_ids.clear();
      return false;
    }
    public_unit_ids.push_back(unit_id);
  }
  return true;
}

struct ActiveCombatIdentityV1 {
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::int32_t selected_combat_array_index = -1;
  bool finalized = false;
  std::vector<std::int32_t> province_public_cunit_ids;
  std::vector<std::int32_t> province_combat_ids;
  std::vector<std::int32_t> attacker_native_carmy_ids;
  std::vector<std::int32_t> attacker_public_cunit_ids;
  std::vector<std::int32_t> defender_native_carmy_ids;
  std::vector<std::int32_t> defender_public_cunit_ids;

  friend bool operator==(const ActiveCombatIdentityV1 &,
                         const ActiveCombatIdentityV1 &) = default;
};

bool ReadActiveCombatIdentityV1(
    const Bindings &bindings, void *game_state, void *subject_unit,
    void *subject_native_army, void *expected_province,
    std::int32_t expected_subject_public_cunit_id, bool require_not_finalized,
    ActiveCombatIdentityV1 &output) noexcept {
  output = {};
  const auto combat_id = LoadAt<std::int32_t>(
      subject_native_army, kInternalArmyCombatIdOffset);
  if (combat_id <= 0) {
    return false;
  }
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    return false;
  }
  const bool finalized =
      LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) != 0;
  if (require_not_finalized && finalized) {
    return false;
  }
  void *const actual_province =
      LoadAt<void *>(combat, kCombatProvinceOffset);
  if (actual_province == nullptr || actual_province != expected_province ||
      LoadAt<void *>(subject_unit, kArmyCurrentProvinceOffset) !=
          actual_province) {
    return false;
  }
  const auto province_id =
      LoadAt<std::int32_t>(actual_province, kProvinceIdOffset);
  if (province_id <= 0 ||
      ResolveProvince(game_state, province_id) != actual_province) {
    return false;
  }
  if (!ReadContactIdArray(
          actual_province, kProvinceUnitIdsOffset,
          kProvinceUnitIdCountOffset, kMaximumActualContactProvinceUnits,
          output.province_public_cunit_ids, true) ||
      !ReadContactIdArray(
          actual_province, kProvinceCombatIdsOffset,
          kProvinceCombatIdCountOffset,
          kMaximumActualContactProvinceCombats,
          output.province_combat_ids, true) ||
      !std::binary_search(output.province_public_cunit_ids.begin(),
                          output.province_public_cunit_ids.end(),
                          expected_subject_public_cunit_id)) {
    return false;
  }
  const auto selected = std::lower_bound(output.province_combat_ids.begin(),
                                         output.province_combat_ids.end(),
                                         combat_id);
  if (selected == output.province_combat_ids.end() ||
      *selected != combat_id ||
      !ReadActiveCombatSideIds(
          bindings, combat, kCombatAttackerSideOffset, combat_id,
          output.attacker_native_carmy_ids,
          output.attacker_public_cunit_ids) ||
      !ReadActiveCombatSideIds(
          bindings, combat, kCombatDefenderSideOffset, combat_id,
          output.defender_native_carmy_ids,
          output.defender_public_cunit_ids)) {
    return false;
  }
  const auto attacker_subject_count = static_cast<std::size_t>(std::count(
      output.attacker_public_cunit_ids.begin(),
      output.attacker_public_cunit_ids.end(),
      expected_subject_public_cunit_id));
  const auto defender_subject_count = static_cast<std::size_t>(std::count(
      output.defender_public_cunit_ids.begin(),
      output.defender_public_cunit_ids.end(),
      expected_subject_public_cunit_id));
  if (attacker_subject_count + defender_subject_count != 1) {
    return false;
  }
  for (const auto attacker_id : output.attacker_public_cunit_ids) {
    if (std::find(output.defender_public_cunit_ids.begin(),
                  output.defender_public_cunit_ids.end(), attacker_id) !=
        output.defender_public_cunit_ids.end()) {
      return false;
    }
  }
  if (ResolveStoredComponent(bindings.combat_storage_slot, combat_id,
                             kCombatIdOffset) != combat ||
      LoadAt<std::int32_t>(subject_native_army,
                           kInternalArmyCombatIdOffset) != combat_id) {
    return false;
  }
  output.combat_id = combat_id;
  output.province_id = province_id;
  output.selected_combat_array_index = static_cast<std::int32_t>(
      std::distance(output.province_combat_ids.begin(), selected));
  output.finalized = finalized;
  return true;
}

ActualContactScopeStatus ReadExistingActualContact(
    const Bindings &bindings, void *game_state, void *unit,
    void *native_army, void *requested_province,
    const game::ActualContactScopeRequest &request,
    game::ActualContactScopeSnapshot &output) noexcept {
  ActiveCombatIdentityV1 identity{};
  if (!ReadActiveCombatIdentityV1(
          bindings, game_state, unit, native_army, requested_province,
          request.subject_army_id, true, identity) ||
      identity.province_id != request.target_province_id) {
    return ActualContactScopeStatus::state_changed;
  }
  output.target_province_id = identity.province_id;
  output.province_unit_army_ids =
      std::move(identity.province_public_cunit_ids);
  output.province_combat_ids = std::move(identity.province_combat_ids);
  output.attacker_army_ids =
      std::move(identity.attacker_public_cunit_ids);
  output.defender_army_ids =
      std::move(identity.defender_public_cunit_ids);
  output.scope_kind = "post_contact_observation";
  output.transition_kind = "in_combat";
  output.selected_combat_id = identity.combat_id;
  output.selected_combat_array_index =
      identity.selected_combat_array_index;
  output.actual_contact_scope_ready = true;
  output.combat_v3_participant_scope_ready = true;
  return ActualContactScopeStatus::available;
}

bool HasPositiveContactSoldiers(const Bindings &bindings, void *army,
                                bool &positive) noexcept {
  positive = false;
  std::vector<std::int32_t> regiment_ids;
  if (!ReadContactIdArray(army, kInternalArmyRegimentIdsOffset,
                          kInternalArmyRegimentCountOffset,
                          kMaximumActualContactRegiments, regiment_ids,
                          false)) {
    return false;
  }
  std::int64_t total = 0;
  for (const auto regiment_id : regiment_ids) {
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      return false;
    }
    bool identity_valid = false;
    if (!ReadRegimentIdentity(regiment, identity_valid)) {
      return false;
    }
    if (!identity_valid) {
      continue;
    }
    const auto soldiers =
        LoadAt<std::int32_t>(regiment, kRegimentCurrentSoldiersOffset);
    if (soldiers < 0 ||
        total > std::numeric_limits<std::int32_t>::max() - soldiers) {
      return false;
    }
    total += soldiers;
  }
  positive = total > 0;
  return true;
}

bool AppendLoserExclusions(const Bindings &bindings, void *combat,
                           std::vector<std::int32_t> &output) noexcept {
  const auto battle_result_id =
      LoadAt<std::int32_t>(combat, kCombatBattleResultIdOffset);
  void *const battle_result = ResolveStoredComponent(
      bindings.battle_result_storage_slot, battle_result_id,
      kBattleResultIdOffset);
  if (battle_result == nullptr) {
    return true;
  }
  bool identity_valid = false;
  if (!ReadBattleResultIdentity(battle_result, identity_valid)) {
    return false;
  }
  if (!identity_valid) {
    return true;
  }
  const auto winner = LoadAt<std::int32_t>(combat, kCombatWinnerOffset);
  if (LoadAt<std::uint8_t>(battle_result, kBattleResultReadyOffset) == 0 ||
      winner == -1) {
    return true;
  }
  const auto loser_side = winner == 0 ? kCombatDefenderSideOffset
                                      : kCombatAttackerSideOffset;
  std::vector<std::int32_t> loser_ids;
  const auto *const side = static_cast<const std::byte *>(combat) + loser_side;
  if (!ReadContactIdArray(side, kCombatSideArmyIdsOffset,
                          kCombatSideArmyCountOffset,
                          kMaximumActualContactSideArmies, loser_ids,
                          false)) {
    return false;
  }
  output.insert(output.end(), loser_ids.begin(), loser_ids.end());
  return true;
}

bool ReadContactAdjacencyKind(void *unit, std::int32_t &kind) noexcept {
  kind = 0;
  void *const current = LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  void *const prior = LoadAt<void *>(unit, kArmyTargetProvinceOffset);
  if (current == nullptr || prior == nullptr) {
    return true;
  }
  bool current_valid = false;
  bool prior_valid = false;
  if (!ReadProvinceIdentity(current, current_valid) ||
      !ReadProvinceIdentity(prior, prior_valid)) {
    return false;
  }
  if (!current_valid || !prior_valid) {
    return true;
  }
  void *const map_node = LoadAt<void *>(current, kProvinceMapNodeOffset);
  if (map_node == nullptr) {
    return false;
  }
  void *const rows = LoadAt<void *>(map_node, kMapNodeAdjacencyDataOffset);
  const auto count =
      LoadAt<std::int32_t>(map_node, kMapNodeAdjacencyCountOffset);
  if (count < 0 || count > kMaximumProvinceAdjacencies ||
      (count > 0 && rows == nullptr)) {
    return false;
  }
  const auto prior_id = LoadAt<std::int32_t>(prior, kProvinceIdOffset);
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const row = static_cast<const std::byte *>(rows) +
                            static_cast<std::size_t>(index) *
                                kMapAdjacencyStride;
    if (LoadAt<std::int32_t>(row,
                             kMapAdjacencyTargetProvinceIdOffset) == prior_id) {
      kind = LoadAt<std::int32_t>(row, kMapAdjacencyKindOffset);
      return true;
    }
  }
  return true;
}

ActualContactScopeStatus ReadActualContactScopeSample(
    const Bindings &bindings, const game::ActualContactScopeRequest &request,
    game::ActualContactScopeSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  void *const game_state = *bindings.game_state_slot;
  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, request.subject_army_id, kArmyIdOffset);
  if (unit == nullptr) {
    return ActualContactScopeStatus::subject_army_not_found;
  }
  void *const province =
      ResolveProvince(game_state, request.target_province_id);
  if (province == nullptr) {
    return ActualContactScopeStatus::target_province_not_found;
  }
  if (LoadAt<void *>(unit, kArmyCurrentProvinceOffset) != province) {
    return ActualContactScopeStatus::subject_not_at_target;
  }
  const auto native_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *const native_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot, native_army_id,
      kInternalArmyIdOffset);
  if (native_army == nullptr ||
      LoadAt<std::int32_t>(native_army, kInternalArmyUnitIdOffset) !=
          request.subject_army_id) {
    return ActualContactScopeStatus::state_changed;
  }
  const auto owner_id =
      LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
  void *owner = nullptr;
  if (!ResolveContactCharacter(bindings, owner_id, owner)) {
    return ActualContactScopeStatus::entry_rejected;
  }
  output.subject_native_carmy_id = native_army_id;
  output.subject_owner_character_id = owner_id;

  const bool subject_in_combat = bindings.is_army_in_combat(native_army);
  if (subject_in_combat) {
    return ReadExistingActualContact(
        bindings, game_state, unit, native_army, province, request, output);
  }

  void *const province_gate =
      LoadAt<void *>(province, kProvinceContactGatePointerOffset);
  void *const mode_root = *bindings.contact_game_mode_slot;
  void *const mode = mode_root == nullptr
                         ? nullptr
                         : LoadAt<void *>(mode_root, 0x1C0);
  if (province_gate == nullptr ||
      LoadAt<std::uint8_t>(province_gate, 0x1B) == 0 || mode == nullptr ||
      LoadAt<std::uint8_t>(mode, 0x28) != 0 ||
      LoadAt<std::int32_t>(unit, 0x18) != 0 ||
      LoadAt<std::int32_t>(unit, kUnitRetreatStateOffset) > 0 ||
      bindings.is_army_empty_for_contact(native_army)) {
    return ActualContactScopeStatus::entry_rejected;
  }

  if (!ReadContactIdArray(
          province, kProvinceUnitIdsOffset, kProvinceUnitIdCountOffset,
          kMaximumActualContactProvinceUnits,
          output.province_unit_army_ids, true) ||
      !ReadContactIdArray(
          province, kProvinceCombatIdsOffset, kProvinceCombatIdCountOffset,
          kMaximumActualContactProvinceCombats,
          output.province_combat_ids, true) ||
      !std::binary_search(output.province_unit_army_ids.begin(),
                          output.province_unit_army_ids.end(),
                          request.subject_army_id)) {
    return ActualContactScopeStatus::state_changed;
  }

  void *selected_combat = nullptr;
  for (std::size_t index = 0; index < output.province_combat_ids.size();
       ++index) {
    const auto combat_id = output.province_combat_ids[index];
    void *const combat = ResolveStoredComponent(
        bindings.combat_storage_slot, combat_id, kCombatIdOffset);
    if (combat == nullptr ||
        LoadAt<void *>(combat, kCombatProvinceOffset) != province) {
      return ActualContactScopeStatus::state_changed;
    }
    bool compatible = false;
    if (LoadAt<std::uint8_t>(combat, kCombatFinalizedOffset) == 0) {
      const auto attacker_primary_id = LoadAt<std::int32_t>(
          combat, kCombatAttackerSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
      const auto defender_primary_id = LoadAt<std::int32_t>(
          combat, kCombatDefenderSideOffset +
                      kCombatSidePrimaryCharacterIdOffset);
      void *attacker_primary = nullptr;
      void *defender_primary = nullptr;
      if (!ResolveContactCharacter(bindings, attacker_primary_id,
                                   attacker_primary) ||
          !ResolveContactCharacter(bindings, defender_primary_id,
                                   defender_primary)) {
        return ActualContactScopeStatus::relation_unavailable;
      }
      const bool hostile_to_attacker =
          bindings.is_character_hostile(owner, attacker_primary, false);
      const bool hostile_to_defender =
          bindings.is_character_hostile(owner, defender_primary, false);
      compatible = hostile_to_attacker != hostile_to_defender;
    }
    if (compatible) {
      selected_combat = combat;
      output.selected_combat_id = combat_id;
      output.selected_combat_array_index =
          static_cast<std::int32_t>(index);
      continue;
    }
    if (selected_combat == nullptr &&
        !AppendLoserExclusions(
            bindings, combat,
            output.loser_excluded_native_carmy_ids)) {
      return ActualContactScopeStatus::state_changed;
    }
  }

  if (selected_combat != nullptr) {
    const auto attacker_primary_id = LoadAt<std::int32_t>(
        selected_combat, kCombatAttackerSideOffset +
                             kCombatSidePrimaryCharacterIdOffset);
    const auto defender_primary_id = LoadAt<std::int32_t>(
        selected_combat, kCombatDefenderSideOffset +
                             kCombatSidePrimaryCharacterIdOffset);
    void *attacker_primary = nullptr;
    void *defender_primary = nullptr;
    if (!ResolveContactCharacter(bindings, attacker_primary_id,
                                 attacker_primary) ||
        !ResolveContactCharacter(bindings, defender_primary_id,
                                 defender_primary)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    const bool joins_defender =
        bindings.is_character_hostile(attacker_primary, owner, false);
    const bool joins_attacker =
        bindings.is_character_hostile(defender_primary, owner, false);
    if (joins_defender == joins_attacker ||
        !ReadCombatSidePublicUnitIds(bindings, selected_combat,
                                     kCombatAttackerSideOffset,
                                     output.attacker_army_ids) ||
        !ReadCombatSidePublicUnitIds(bindings, selected_combat,
                                     kCombatDefenderSideOffset,
                                     output.defender_army_ids)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    auto &joined_side = joins_defender ? output.defender_army_ids
                                       : output.attacker_army_ids;
    if (std::find(joined_side.begin(), joined_side.end(),
                  request.subject_army_id) == joined_side.end()) {
      joined_side.push_back(request.subject_army_id);
    }
    output.transition_kind = "join_existing";
    output.join_side = joins_defender ? "defender" : "attacker";
    output.actual_contact_scope_ready = true;
    output.combat_v3_participant_scope_ready = true;
    return ActualContactScopeStatus::available;
  }

  std::vector<std::int32_t> opponent_native_army_ids;
  for (const auto candidate_unit_id : output.province_unit_army_ids) {
    void *const candidate_unit = ResolveStoredComponent(
        bindings.army_storage_slot, candidate_unit_id, kArmyIdOffset);
    if (candidate_unit == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    const auto candidate_owner_id = LoadAt<std::int32_t>(
        candidate_unit, kArmyOwnerCharacterIdOffset);
    if (candidate_owner_id == owner_id ||
        LoadAt<std::int32_t>(candidate_unit, 0x18) != 0 ||
        LoadAt<std::int32_t>(candidate_unit, kUnitRetreatStateOffset) > 0) {
      continue;
    }
    const auto candidate_native_id = LoadAt<std::int32_t>(
        candidate_unit, kUnitArmyIdOffset);
    void *const candidate_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, candidate_native_id,
        kInternalArmyIdOffset);
    if (candidate_army == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (bindings.is_army_empty_for_contact(candidate_army) ||
        bindings.is_army_in_combat(candidate_army) ||
        std::find(output.loser_excluded_native_carmy_ids.begin(),
                  output.loser_excluded_native_carmy_ids.end(),
                  candidate_native_id) !=
            output.loser_excluded_native_carmy_ids.end()) {
      continue;
    }
    void *candidate_owner = nullptr;
    if (!ResolveContactCharacter(bindings, candidate_owner_id,
                                 candidate_owner)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (bindings.is_character_hostile(owner, candidate_owner, false)) {
      output.defender_seed_character_id = candidate_owner_id;
      break;
    }
  }
  if (output.defender_seed_character_id == -1) {
    output.actual_contact_scope_ready = true;
    return ActualContactScopeStatus::available;
  }
  bool positive_soldiers = false;
  if (!HasPositiveContactSoldiers(bindings, native_army,
                                  positive_soldiers)) {
    return ActualContactScopeStatus::state_changed;
  }
  if (!positive_soldiers) {
    // The hostile seed is only part of a create-new projection.  Native stops
    // before construction when the initiator has no positive regiment
    // strength, so do not expose the intermediate scan candidate as a
    // transition participant.
    output.defender_seed_character_id = -1;
    output.actual_contact_scope_ready = true;
    return ActualContactScopeStatus::available;
  }

  for (const auto candidate_unit_id : output.province_unit_army_ids) {
    void *const candidate_unit = ResolveStoredComponent(
        bindings.army_storage_slot, candidate_unit_id, kArmyIdOffset);
    if (candidate_unit == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (LoadAt<std::int32_t>(candidate_unit, 0x18) != 0 ||
        LoadAt<std::int32_t>(candidate_unit, kUnitRetreatStateOffset) > 0) {
      continue;
    }
    const auto candidate_native_id = LoadAt<std::int32_t>(
        candidate_unit, kUnitArmyIdOffset);
    void *const candidate_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, candidate_native_id,
        kInternalArmyIdOffset);
    if (candidate_army == nullptr) {
      return ActualContactScopeStatus::state_changed;
    }
    if (bindings.is_army_empty_for_contact(candidate_army) ||
        bindings.is_army_in_combat(candidate_army)) {
      continue;
    }
    const auto candidate_owner_id = LoadAt<std::int32_t>(
        candidate_unit, kArmyOwnerCharacterIdOffset);
    void *candidate_owner = nullptr;
    if (!ResolveContactCharacter(bindings, candidate_owner_id,
                                 candidate_owner)) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (candidate_owner_id == output.defender_seed_character_id ||
        bindings.is_character_hostile(candidate_owner, owner, false)) {
      if (LoadAt<std::int32_t>(candidate_army,
                               kInternalArmyUnitIdOffset) !=
          candidate_unit_id) {
        return ActualContactScopeStatus::state_changed;
      }
      opponent_native_army_ids.push_back(candidate_native_id);
      output.opponent_army_ids.push_back(candidate_unit_id);
    }
  }
  if (output.opponent_army_ids.empty()) {
    return ActualContactScopeStatus::state_changed;
  }

  bool initiator_is_defender = false;
  if (LoadAt<std::int32_t>(province, kProvinceFortLevelOffset) > 0) {
    std::int32_t holder_id = -1;
    if (bindings.read_province_holder_character_id(province, &holder_id) !=
        &holder_id) {
      return ActualContactScopeStatus::relation_unavailable;
    }
    if (holder_id != -1) {
      void *holder = nullptr;
      if (!ResolveContactCharacter(bindings, holder_id, holder)) {
        return ActualContactScopeStatus::relation_unavailable;
      }
      initiator_is_defender =
          bindings.classify_contact_defender_by_holder(owner, holder);
    }
  }
  if (!initiator_is_defender) {
    initiator_is_defender =
        bindings.classify_contact_defender_fallback(owner, province);
  }
  output.initiator_is_defender = initiator_is_defender;
  if (!ReadContactAdjacencyKind(unit, output.adjacency_kind_raw)) {
    return ActualContactScopeStatus::state_changed;
  }
  std::vector<std::int32_t> unique_opponent_native_army_ids;
  unique_opponent_native_army_ids.reserve(opponent_native_army_ids.size());
  for (const auto opponent_native_id : opponent_native_army_ids) {
    if (std::find(unique_opponent_native_army_ids.begin(),
                  unique_opponent_native_army_ids.end(),
                  opponent_native_id) ==
        unique_opponent_native_army_ids.end()) {
      unique_opponent_native_army_ids.push_back(opponent_native_id);
    }
  }
  std::vector<std::int32_t> unique_opponent_army_ids;
  if (!NativeArmyIdsToPublicUnitIds(bindings,
                                    unique_opponent_native_army_ids,
                                    unique_opponent_army_ids)) {
    return ActualContactScopeStatus::state_changed;
  }
  if (initiator_is_defender) {
    output.attacker_army_ids = std::move(unique_opponent_army_ids);
    output.defender_army_ids = {request.subject_army_id};
  } else {
    output.attacker_army_ids = {request.subject_army_id};
    output.defender_army_ids = std::move(unique_opponent_army_ids);
  }
  output.transition_kind = "create_new";
  output.actual_contact_scope_ready = true;
  output.combat_v3_participant_scope_ready = true;
  return ActualContactScopeStatus::available;
}

} // namespace

RouteBindings BindRouteImage(std::uintptr_t base, std::string_view sha) noexcept {
  RouteBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.game_state_slot = reinterpret_cast<void **>(base + 0x5C68C50);
  b.jomini_state_slot = reinterpret_cast<void **>(base + 0x5C6A520);
  b.army_storage_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  b.army_internal_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  b.regiment_storage_slot = reinterpret_cast<void **>(base + 0x5D1F340);
  b.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  b.combat_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE70);
  b.battle_result_storage_slot = reinterpret_cast<void **>(base + 0x5D1FFE0);
  b.contact_game_mode_slot = reinterpret_cast<void **>(base + 0x5CB87F8);
  b.read_unit_land_route_speed = reinterpret_cast<RouteBindings::UnitSpeed>(base + 0x24AA940);
  b.read_unit_naval_route_speed = reinterpret_cast<RouteBindings::UnitSpeed>(base + 0x24AAC00);
  b.read_unit_current_edge_speed = reinterpret_cast<RouteBindings::UnitSpeed>(base + 0x24AB5C0);
  b.read_route_travel_duration = reinterpret_cast<RouteBindings::TravelDuration>(base + 0x24AADA0);
  b.read_route_progress = reinterpret_cast<RouteBindings::UnitSpeed>(base + 0x24AB2F0);
  b.movement_locked_threshold = reinterpret_cast<const std::int64_t *>(base + 0x5C699E8);
  b.get_route_front = reinterpret_cast<RouteBindings::UnitProvince>(base + 0x24AA7D0);
  b.get_route_tail = reinterpret_cast<RouteBindings::UnitProvince>(base + 0x24AA820);
  b.get_army_move_mode = reinterpret_cast<RouteBindings::MoveMode>(base + 0x296A0A0);
  b.construct_move_path_context = reinterpret_cast<RouteBindings::PathContext>(base + 0x2648060);
  b.construct_army_move_path = reinterpret_cast<RouteBindings::PathConstructor>(base + 0xD1A0B0);
  b.build_army_move_route = reinterpret_cast<RouteBindings::BuildRoute>(base + 0x2648150);
  b.destroy_move_army_command = reinterpret_cast<RouteBindings::Destructor>(base + 0x2969620);
  b.move_army_primary_vtable = base + 0x476B168;
  b.move_army_secondary_vtable = base + 0x476B138;
  b.is_character_hostile = reinterpret_cast<RouteBindings::Hostile>(base + 0x2C09640);
  b.is_army_empty_for_contact = reinterpret_cast<RouteBindings::ArmyPredicate>(base + 0x24E83C0);
  b.is_army_in_combat = reinterpret_cast<RouteBindings::ArmyPredicate>(base + 0x24E8360);
  b.read_province_holder_character_id = reinterpret_cast<RouteBindings::ProvinceHolder>(base + 0x247D030);
  b.classify_contact_defender_by_holder = reinterpret_cast<RouteBindings::DefenderPredicate>(base + 0x2C09810);
  b.classify_contact_defender_fallback = reinterpret_cast<RouteBindings::DefenderPredicate>(base + 0x2C164E0);
  return b;
}

bool ReadCommittedRouteTimeline(
    const RouteBindings &bindings, const game::Snapshot &paused_scope,
    std::int32_t public_cunit_id, std::vector<std::int32_t> &province_ids,
    std::vector<std::int32_t> &arrival_date_raws) noexcept {
  province_ids.clear();
  arrival_date_raws.clear();
  if (!paused_scope.paused || !ClockMatches(bindings, paused_scope)) {
    return false;
  }
  void *const unit = ResolveArmy(bindings, public_cunit_id);
  if (unit == nullptr) {
    return false;
  }
  void *const state = *bindings.game_state_slot;
  void *const origin = LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  if (origin == nullptr ||
      ResolveProvince(state, LoadAt<std::int32_t>(origin, kProvinceIdOffset)) !=
          origin) {
    return false;
  }
  const void *const path =
      static_cast<const std::byte *>(unit) + kUnitPathProvinceInfosOffset;
  NativeMovePathPrefix header{};
  if (!ReadPathHeader(path, header)) {
    return false;
  }
  if (header.count == 0) {
    return ClockMatches(bindings, paused_scope);
  }
  if (!ProjectPathTimeline(bindings, state, unit, path, origin,
                           paused_scope.date_raw, 0, province_ids,
                           arrival_date_raws) ||
      !ClockMatches(bindings, paused_scope)) {
    province_ids.clear();
    arrival_date_raws.clear();
    return false;
  }
  return true;
}

game::RouteContactHorizonStatus ReadRouteContactHorizon(
    const RouteBindings &bindings, const game::Snapshot &paused_scope,
    const game::RouteContactHorizonRequest &request,
    game::RouteContactHorizonSnapshot &output) noexcept {
  try {
    game::RouteContactHorizonSnapshot first{};
    const auto a = ReadRouteContactHorizonSample(bindings, paused_scope, request, first);
    const auto b = ReadRouteContactHorizonSample(bindings, paused_scope, request, output);
    if (a != b || first != output) {
      output = {};
      output.subject_army_id = request.subject_army_id;
      output.target_province_id = request.target_province_id;
      output.status = game::RouteContactHorizonStatus::state_changed;
    }
    return output.status;
  } catch (...) {
    output = {};
    output.status = game::RouteContactHorizonStatus::unavailable;
    return output.status;
  }
}

ActualContactScopeStatus ReadActualContactScope(
    const Bindings &bindings, const Snapshot &paused_scope, const ActualContactScopeRequest &request,
    ActualContactScopeSnapshot &output) noexcept {
  output = {};
  output.subject_army_id = request.subject_army_id;
  output.target_province_id = request.target_province_id;
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.battle_result_storage_slot == nullptr ||
      bindings.contact_game_mode_slot == nullptr ||
      bindings.is_character_hostile == nullptr ||
      bindings.is_army_empty_for_contact == nullptr ||
      bindings.is_army_in_combat == nullptr ||
      bindings.read_province_holder_character_id == nullptr ||
      bindings.classify_contact_defender_by_holder == nullptr ||
      bindings.classify_contact_defender_fallback == nullptr ||
      request.subject_army_id <= 0 || request.target_province_id <= 0) {
    output.status = ActualContactScopeStatus::unavailable;
    return output.status;
  }
  const Snapshot &before = paused_scope;
  if (!ClockMatches(bindings, before)) {
    output.status = ActualContactScopeStatus::unavailable;
    return output.status;
  }
  if (!before.paused) {
    output.status = ActualContactScopeStatus::requires_paused;
    return output.status;
  }
  const auto *const subject =
      FindArmySnapshot(before, request.subject_army_id);
  if (subject == nullptr) {
    output.status = ActualContactScopeStatus::subject_army_not_found;
    return output.status;
  }
  if (!subject->controllable) {
    output.status = ActualContactScopeStatus::subject_army_not_controllable;
    return output.status;
  }
  if (!subject->has_current_province ||
      subject->current_province_id != request.target_province_id) {
    output.status = ActualContactScopeStatus::subject_not_at_target;
    return output.status;
  }

  ActualContactScopeSnapshot first{};
  ActualContactScopeSnapshot second{};
  const auto first_status =
      ReadActualContactScopeSample(bindings, request, first);
  const auto second_status =
      ReadActualContactScopeSample(bindings, request, second);
  if (first_status != second_status || first != second ||
      !ClockMatches(bindings, before)) {
    output.status = ActualContactScopeStatus::state_changed;
    return output.status;
  }
  output = std::move(second);
  output.date_raw = before.date_raw;
  output.status = second_status;
  return output.status;
}


} // namespace xar::ck3_12002
