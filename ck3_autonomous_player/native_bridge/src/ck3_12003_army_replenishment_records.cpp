#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"

#include "xar_bridge/ck3_12002_army.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}

// Same bounds as the existing army reader's registry and regiment arrays.
constexpr std::int32_t kMaximumCapacity = 1'000'000;
constexpr std::int32_t kMaximumRecords = 65'536;
constexpr std::uint32_t kArmyRegimentMagic = 0x41725267U;
constexpr std::uint32_t kPersistentRegimentMagic = 0x52656769U;

void *ResolvePersistent(const ck3_12002::ArmyBindings &bindings,
                        std::int32_t id) noexcept {
  if (id == -1 || bindings.persistent_regiment_storage_slot == nullptr ||
      *bindings.persistent_regiment_storage_slot == nullptr) return nullptr;
  const void *const storage = *bindings.persistent_regiment_storage_slot;
  const void *const objects = Load<const void *>(storage, 0x20);
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  if (capacity < 0 || capacity > kMaximumCapacity ||
      (capacity > 0 && objects == nullptr)) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *const object = Load<void *>(
      objects, static_cast<std::size_t>(index) * 0x10 + 0x08);
  return object != nullptr && Load<std::int32_t>(object, 0x10) == id
      ? object : nullptr;
}

game::ArmyRegimentReplenishmentRecordV1 ReadRecord(
    const ck3_12002::ArmyBindings &bindings, const void *record,
    std::int32_t record_index, std::int32_t army_regiment_id) noexcept {
  game::ArmyRegimentReplenishmentRecordV1 result{};
  result.record_index = record_index;
  result.persistent_regiment_id = Load<std::int32_t>(record, 0x08);
  result.chunk_index = Load<std::int32_t>(record, 0x0C);
  if (result.chunk_index < 0 || result.chunk_index >= 7) {
    result.unavailable_reason = "regiment_data_record_ordinal_invalid";
    return result;
  }
  void *const persistent = ResolvePersistent(
      bindings, result.persistent_regiment_id);
  if (persistent == nullptr) {
    result.unavailable_reason = "persistent_regiment_not_found";
    return result;
  }
  if (Load<std::uint32_t>(persistent, 0x14) != kPersistentRegimentMagic) {
    result.unavailable_reason = "persistent_regiment_identity_invalid";
    return result;
  }
  auto *const chunk = static_cast<std::byte *>(persistent) + 0x18 +
      static_cast<std::size_t>(result.chunk_index) * 0x24;
  if (Load<std::int32_t>(chunk, 0x08) != result.persistent_regiment_id ||
      Load<std::int32_t>(chunk, 0x0C) != result.chunk_index ||
      Load<std::int32_t>(chunk, 0x10) != army_regiment_id) {
    result.unavailable_reason = "regiment_data_record_chunk_backlink_mismatch";
    return result;
  }
  const auto current = Load<std::int32_t>(chunk, 0x04);
  const auto maximum = Load<std::int32_t>(chunk, 0x00);
  const auto state = Load<std::int32_t>(chunk, 0x18);
  result.current_soldiers = current;
  result.maximum_soldiers = maximum;
  result.state_raw = state;
  if (current < 0 || maximum < 0) {
    result.unavailable_reason = "regiment_chunk_soldiers_invalid";
    return result;
  }
  result.effective_current_soldiers =
      state == 3 && current == 0 ? maximum : current;
  // The two native predicates have different branches. Keep their answers
  // independent, and keep prepared cache distinct from the current getter.
  result.native_can_replenish =
      bindings.can_regiment_replenish(persistent, chunk);
  result.native_chunk_can_replenish = bindings.can_chunk_replenish(chunk);
  std::int64_t monthly_fraction = 0;
  bindings.get_regiment_monthly_replenishment_fraction(persistent,
                                                     &monthly_fraction);
  result.persistent_monthly_replenishment_fraction_raw = monthly_fraction;
  result.persistent_prepared_replenishment_fraction_raw =
      Load<std::int64_t>(persistent, 0x148);
  result.available = true;
  return result;
}

} // namespace

game::ArmyRegimentReplenishmentRecordsSnapshotV1
ReadArmyRegimentReplenishmentRecordsV1(
    const ck3_12002::ArmyBindings &bindings, const void *resolved_army_regiment,
    std::int32_t army_regiment_id) noexcept {
  game::ArmyRegimentReplenishmentRecordsSnapshotV1 result{};
  result.army_regiment_id = army_regiment_id;
  if (!bindings.enabled ||
      bindings.persistent_regiment_storage_slot == nullptr ||
      bindings.can_regiment_replenish == nullptr ||
      bindings.can_chunk_replenish == nullptr ||
      bindings.get_regiment_monthly_replenishment_fraction == nullptr) {
    result.unavailable_reason = "native_replenishment_records_bindings_unavailable";
    return result;
  }
  if (resolved_army_regiment == nullptr || army_regiment_id == -1 ||
      Load<std::uint32_t>(resolved_army_regiment, 0x14) != kArmyRegimentMagic ||
      Load<std::int32_t>(resolved_army_regiment, 0x10) != army_regiment_id) {
    result.unavailable_reason = "army_regiment_identity_invalid";
    return result;
  }
  const void *const data = Load<const void *>(resolved_army_regiment, 0x20);
  const auto capacity = Load<std::int32_t>(resolved_army_regiment, 0x28);
  const auto count = Load<std::int32_t>(resolved_army_regiment, 0x2C);
  result.native_data_record_count = count;
  if (capacity < 0 || capacity > kMaximumRecords || count < 0 ||
      count > capacity || (count > 0 && data == nullptr)) {
    result.unavailable_reason = "army_regiment_data_header_invalid";
    return result;
  }
  result.records.reserve(static_cast<std::size_t>(count));
  bool partial = false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const record = static_cast<const std::byte *>(data) +
        static_cast<std::size_t>(index) * 0x10;
    auto row = ReadRecord(bindings, record, index, army_regiment_id);
    partial = partial || !row.available;
    result.records.push_back(row);
  }
  // A valid count0 is available with records[], not a fabricated persistent
  // ID, zero fraction, zero soldiers, or a failure of the parent army row.
  result.status = partial
      ? game::ArmyRegimentReplenishmentRecordsStatusV1::partial
      : game::ArmyRegimentReplenishmentRecordsStatusV1::available;
  if (partial) result.unavailable_reason = "regiment_data_records_partial";
  return result;
}

} // namespace xar::ck3_12003
