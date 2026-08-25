#include "xar_bridge/prewar_scope_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kUnitIdOffset = 0x10;
constexpr std::size_t kUnitCurrentProvinceOffset = 0x20;
constexpr std::size_t kUnitMoveTargetProvinceOffset = 0x30;
constexpr std::size_t kUnitRouteDataOffset = 0x38;
constexpr std::size_t kUnitRouteCapacityOffset = 0x40;
constexpr std::size_t kUnitRouteCountOffset = 0x44;
constexpr std::size_t kUnitOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kUnitNativeCArmyIdOffset = 0x178;
constexpr std::size_t kCArmyIdOffset = 0x10;
constexpr std::size_t kCArmyPublicUnitIdBacklinkOffset = 0x124;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kRouteProvinceIdOffset = 0x00;

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

bool IsPositiveFullId(std::int32_t value) noexcept { return value > 0; }

bool ReadProvinceIdentity(const PrewarScopeBindingsV1 &bindings,
                          void *game_state, void *province,
                          std::int32_t &province_id) noexcept {
  if (province == nullptr || bindings.resolve_province == nullptr) {
    return false;
  }
  province_id = LoadAt<std::int32_t>(province, kProvinceIdOffset);
  return IsPositiveFullId(province_id) &&
         bindings.resolve_province(game_state, province_id) == province;
}

bool ReadRoute(const PrewarScopeBindingsV1 &bindings, void *game_state,
               void *unit, std::vector<std::int32_t> &route) noexcept {
  route.clear();
  const auto count = LoadAt<std::int32_t>(unit, kUnitRouteCountOffset);
  const auto capacity = LoadAt<std::int32_t>(unit, kUnitRouteCapacityOffset);
  if (count < 0 || capacity < 0 || count > capacity ||
      count > static_cast<std::int32_t>(
                  kPrewarScopeV1MaximumRouteProvinceCount)) {
    return false;
  }
  if (count == 0) {
    return true;
  }
  void *const data = LoadAt<void *>(unit, kUnitRouteDataOffset);
  if (data == nullptr) {
    return false;
  }
  route.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    void *const row = LoadAt<void *>(
        data, static_cast<std::size_t>(index) * sizeof(void *));
    if (row == nullptr) {
      return false;
    }
    const auto province_id =
        LoadAt<std::int32_t>(row, kRouteProvinceIdOffset);
    if (!IsPositiveFullId(province_id) ||
        bindings.resolve_province(game_state, province_id) == nullptr) {
      return false;
    }
    route.push_back(province_id);
  }
  return true;
}

bool ReadOneSample(const PrewarScopeBindingsV1 &bindings, void *game_state,
                   const PrewarScopeRequestV1 &request,
                   std::vector<PrewarRaisedArmyV1> &armies,
                   std::string &stage) noexcept {
  armies.clear();
  if (bindings.unit_storage_slot == nullptr ||
      bindings.carmy_storage_slot == nullptr) {
    stage = "unit_storage_slot";
    return false;
  }
  void *const storage = *bindings.unit_storage_slot;
  if (storage == nullptr) {
    stage = "unit_storage";
    return false;
  }
  void *const slots = LoadAt<void *>(storage, kStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > static_cast<std::int32_t>(
                     kPrewarScopeV1MaximumComponentCapacity)) {
    stage = "unit_storage_shape";
    return false;
  }

  void *const carmy_storage = *bindings.carmy_storage_slot;
  if (carmy_storage == nullptr) {
    stage = "carmy_storage";
    return false;
  }
  void *const carmy_slots =
      LoadAt<void *>(carmy_storage, kStorageSlotsOffset);
  const auto carmy_capacity =
      LoadAt<std::int32_t>(carmy_storage, kStorageCapacityOffset);
  if (carmy_slots == nullptr || carmy_capacity <= 0 ||
      carmy_capacity > static_cast<std::int32_t>(
                           kPrewarScopeV1MaximumComponentCapacity)) {
    stage = "carmy_storage_shape";
    return false;
  }

  for (std::int32_t index = 0; index < capacity; ++index) {
    void *const unit = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) * kStorageSlotStride +
                   kStorageSlotObjectOffset);
    if (unit == nullptr) {
      continue;
    }
    const auto unit_id = LoadAt<std::int32_t>(unit, kUnitIdOffset);
    if (!IsPositiveFullId(unit_id) ||
        (static_cast<std::uint32_t>(unit_id) & 0x00FFFFFFU) !=
            static_cast<std::uint32_t>(index)) {
      stage = "unit_identity";
      return false;
    }
    const auto owner =
        LoadAt<std::int32_t>(unit, kUnitOwnerCharacterIdOffset);
    PrewarSideV1 side{};
    if (owner == request.actor_character_id) {
      side = PrewarSideV1::attacker;
    } else if (owner == request.effective_target_character_id) {
      side = PrewarSideV1::defender;
    } else {
      continue;
    }

    PrewarRaisedArmyV1 row{};
    row.army_id = unit_id;
    row.native_carmy_id =
        LoadAt<std::int32_t>(unit, kUnitNativeCArmyIdOffset);
    if (!IsPositiveFullId(row.native_carmy_id)) {
      stage = "native_carmy_identity";
      return false;
    }
    const auto carmy_index = static_cast<std::uint32_t>(row.native_carmy_id) &
                             0x00FFFFFFU;
    if (carmy_index >= static_cast<std::uint32_t>(carmy_capacity)) {
      stage = "native_carmy_identity";
      return false;
    }
    void *const carmy = LoadAt<void *>(
        carmy_slots, static_cast<std::size_t>(carmy_index) *
                         kStorageSlotStride +
                         kStorageSlotObjectOffset);
    if (carmy == nullptr ||
        LoadAt<std::int32_t>(carmy, kCArmyIdOffset) !=
            row.native_carmy_id ||
        LoadAt<std::int32_t>(carmy,
                             kCArmyPublicUnitIdBacklinkOffset) != unit_id) {
      stage = "native_carmy_identity";
      return false;
    }
    row.owner_character_id = owner;
    row.side = side;
    void *const current_province =
        LoadAt<void *>(unit, kUnitCurrentProvinceOffset);
    if (current_province != nullptr) {
      if (!ReadProvinceIdentity(bindings, game_state, current_province,
                                row.current_province_id)) {
        stage = "current_province_identity";
        return false;
      }
      row.has_current_province = true;
    }
    void *const move_target_province =
        LoadAt<void *>(unit, kUnitMoveTargetProvinceOffset);
    if (move_target_province != nullptr) {
      if (!ReadProvinceIdentity(bindings, game_state, move_target_province,
                                row.move_target_province_id)) {
        stage = "move_target_province_identity";
        return false;
      }
      row.has_move_target_province = true;
    }
    if (!ReadRoute(bindings, game_state, unit, row.route_province_ids)) {
      stage = "unit_route";
      return false;
    }
    armies.push_back(std::move(row));
  }

  std::sort(armies.begin(), armies.end(),
            [](const PrewarRaisedArmyV1 &left,
               const PrewarRaisedArmyV1 &right) {
              if (left.side != right.side) {
                return static_cast<std::uint8_t>(left.side) <
                       static_cast<std::uint8_t>(right.side);
              }
              if (left.army_id != right.army_id) {
                return left.army_id < right.army_id;
              }
              return left.native_carmy_id < right.native_carmy_id;
            });
  return true;
}

} // namespace

ReadPrewarScopeStatusV1 ReadDeclarationBoundPrewarScopeV1(
    const PrewarScopeBindingsV1 &bindings, void *game_state,
    bool environment_exact, bool paused, const PrewarScopeRequestV1 &request,
    PrewarScopeObservationV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.snapshot_revision;
  output.date_raw = request.date_raw;
  if (!IsPositiveFullId(request.actor_character_id) ||
      !IsPositiveFullId(request.effective_target_character_id) ||
      request.actor_character_id == request.effective_target_character_id) {
    output.status = ReadPrewarScopeStatusV1::invalid_request;
    output.failure_stage = "primary_participant_identity";
    return output.status;
  }
  if (!environment_exact || game_state == nullptr ||
      bindings.resolve_province == nullptr) {
    output.status = ReadPrewarScopeStatusV1::unavailable;
    output.failure_stage = "exact_environment";
    return output.status;
  }
  if (!paused) {
    output.status = ReadPrewarScopeStatusV1::requires_paused;
    output.failure_stage = "paused_required";
    return output.status;
  }

  output.primary_participants = {
      {request.actor_character_id, PrewarSideV1::attacker,
       "declaration_primary_actor"},
      {request.effective_target_character_id, PrewarSideV1::defender,
       "declaration_effective_target"},
  };
  std::vector<PrewarRaisedArmyV1> first;
  std::vector<PrewarRaisedArmyV1> second;
  std::string stage;
  if (!ReadOneSample(bindings, game_state, request, first, stage) ||
      !ReadOneSample(bindings, game_state, request, second, stage)) {
    output.status = ReadPrewarScopeStatusV1::unavailable;
    output.failure_stage = stage;
    return output.status;
  }
  if (first != second) {
    output.status = ReadPrewarScopeStatusV1::unavailable;
    output.failure_stage = "same_frame_primary_army_scope";
    return output.status;
  }

  output.primary_raised_armies = std::move(first);
  output.readiness.exact_build_ready = true;
  output.readiness.primary_participants_ready = true;
  output.readiness.primary_raised_armies_ready = true;
  // These gates intentionally remain false until their exact-build ABIs are
  // separately closed and tested.  Primary CUnits are not a complete war
  // participant or arrival forecast.
  output.status = ReadPrewarScopeStatusV1::available_primary_scope;
  return output.status;
}

} // namespace xar::ck3_11906
