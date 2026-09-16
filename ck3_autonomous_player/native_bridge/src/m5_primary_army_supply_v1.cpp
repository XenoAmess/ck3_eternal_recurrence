#include "xar_bridge/m5_primary_army_supply_v1.hpp"

#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_11906 {
namespace {

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

bool ReadOneSample(void **slot, const PrewarScopeObservationV1 &scope,
                   std::vector<M5PrimaryArmySupplyRowV1> &rows,
                   std::string &stage) {
  rows.clear();
  if (slot == nullptr || *slot == nullptr) {
    stage = "carmy_storage";
    return false;
  }
  const void *storage = *slot;
  const void *slots = LoadAt<void *>(storage, 0x20);
  const auto capacity = LoadAt<std::int32_t>(storage, 0x2C);
  if (slots == nullptr || capacity <= 0 ||
      capacity > static_cast<std::int32_t>(
                     kPrewarScopeV1MaximumComponentCapacity)) {
    stage = "carmy_storage_shape";
    return false;
  }
  rows.reserve(scope.primary_raised_armies.size());
  for (const auto &army : scope.primary_raised_armies) {
    if (army.army_id <= 0 || army.native_carmy_id <= 0 ||
        army.owner_character_id <= 0) {
      stage = "primary_army_identity";
      return false;
    }
    const auto index = static_cast<std::uint32_t>(army.native_carmy_id) &
                       0x00FFFFFFU;
    if (index >= static_cast<std::uint32_t>(capacity)) {
      stage = "carmy_identity";
      return false;
    }
    const void *carmy = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) * 0x10 + 0x08);
    if (carmy == nullptr ||
        LoadAt<std::int32_t>(carmy, 0x10) != army.native_carmy_id ||
        LoadAt<std::int32_t>(carmy, 0x124) != army.army_id) {
      stage = "carmy_identity";
      return false;
    }
    rows.push_back({army.army_id, army.native_carmy_id,
                    army.owner_character_id, army.side,
                    LoadAt<std::int64_t>(carmy, 0x180), 100'000});
  }
  return true;
}

} // namespace

M5PrimaryArmySupplyStatusV1 ReadM5PrimaryArmySupplyV1(
    void **carmy_storage_slot, bool exact_build, bool paused,
    const PrewarScopeObservationV1 &primary_scope,
    M5PrimaryArmySupplyObservationV1 &output) noexcept {
  output = {};
  output.snapshot_revision = primary_scope.snapshot_revision;
  output.date_raw = primary_scope.date_raw;
  if (primary_scope.status !=
          ReadPrewarScopeStatusV1::available_primary_scope ||
      !primary_scope.readiness.exact_build_ready ||
      !primary_scope.readiness.primary_raised_armies_ready ||
      primary_scope.snapshot_revision == 0) {
    output.status = M5PrimaryArmySupplyStatusV1::invalid_scope;
    output.failure_stage = "primary_scope_not_authenticated";
    return output.status;
  }
  if (!exact_build) {
    output.status = M5PrimaryArmySupplyStatusV1::unavailable;
    output.failure_stage = "exact_build";
    return output.status;
  }
  if (!paused) {
    output.status = M5PrimaryArmySupplyStatusV1::requires_paused;
    output.failure_stage = "paused_required";
    return output.status;
  }
  std::vector<M5PrimaryArmySupplyRowV1> first;
  std::vector<M5PrimaryArmySupplyRowV1> second;
  std::string stage;
  if (!ReadOneSample(carmy_storage_slot, primary_scope, first, stage) ||
      !ReadOneSample(carmy_storage_slot, primary_scope, second, stage)) {
    output.status = M5PrimaryArmySupplyStatusV1::unavailable;
    output.failure_stage = stage;
    return output.status;
  }
  if (first != second) {
    output.status = M5PrimaryArmySupplyStatusV1::unavailable;
    output.failure_stage = "same_frame_supply_drift";
    return output.status;
  }
  output.rows = std::move(first);
  output.status = M5PrimaryArmySupplyStatusV1::available;
  return output.status;
}

} // namespace xar::ck3_11906
