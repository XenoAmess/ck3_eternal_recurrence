#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

#include <cstddef>
#include <cstring>
#include <unordered_set>

namespace xar::ck3_12003 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

// Identical full-generation registry layout/bounds to the completeDATA reader.
void *ResolvePersistent(const ck3_12002::ArmyBindings &bindings,
                        std::int32_t id) noexcept {
  if (id == -1 || bindings.persistent_regiment_storage_slot == nullptr ||
      *bindings.persistent_regiment_storage_slot == nullptr) return nullptr;
  const auto *storage = *bindings.persistent_regiment_storage_slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto *objects = Load<const void *>(storage, 0x20);
  if (capacity < 0 || capacity > 1'000'000 ||
      (capacity > 0 && objects == nullptr)) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  auto *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Load<std::int32_t>(object, 0x10) == id &&
      Load<std::uint32_t>(object, 0x14) == 0x52656769U ? object : nullptr;
}

game::FixedChunk0PreparationPersistentInputV1 ReadPersistent(
    const ck3_12002::ArmyBindings &bindings, std::int32_t id) noexcept {
  game::FixedChunk0PreparationPersistentInputV1 row{};
  row.persistent_regiment_id = id;
  auto *persistent = ResolvePersistent(bindings, id);
  if (persistent == nullptr) {
    row.unavailable_reason = "fixed_chunk0_persistent_receiver_unavailable";
    return row;
  }
  row.containing_guard_138_raw = Load<std::int32_t>(persistent, 0x138);
  if (const auto *definition = Load<const void *>(persistent, 0x118))
    row.containing_definition_magic_38 = Load<std::uint32_t>(definition, 0x38);
  if (bindings.can_regiment_replenish != nullptr) {
    // Physical position0, irrespective of a DATA-selected ordinal or raw+C.
    auto *chunk0 = static_cast<std::byte *>(persistent) + 0x18;
    row.native_fixed_chunk0_can_replenish =
        bindings.can_regiment_replenish(persistent, chunk0);
  }
  if (bindings.get_regiment_monthly_replenishment_fraction != nullptr) {
    std::int64_t fraction = 0;
    if (bindings.get_regiment_monthly_replenishment_fraction(persistent, &fraction)
        == &fraction) row.fresh_fraction_raw = fraction;
  }
  const bool complete = row.containing_guard_138_raw.has_value() &&
      row.containing_definition_magic_38.has_value() &&
      row.native_fixed_chunk0_can_replenish.has_value() && row.fresh_fraction_raw.has_value();
  row.status = complete ? game::FixedChunk0PreparationInputStatusV1::available
                        : game::FixedChunk0PreparationInputStatusV1::partial;
  if (!complete) row.unavailable_reason = "fixed_chunk0_preparation_operands_partial";
  return row;
}
} // namespace

game::FixedChunk0PreparationInputsV1 ReadFixedChunk0PreparationInputsV1(
    const ck3_12002::ArmyBindings &bindings,
    const game::ArmyStrengthSnapshot &strength) noexcept {
  game::FixedChunk0PreparationInputsV1 result{};
  result.subject_army_id = strength.army_id;
  result.subject_carmy_id = strength.native_carmy_id;
  if (!bindings.enabled || !strength.available ||
      !strength.regiment_replenishment_records_v1.has_value()) {
    result.unavailable_reason = "same_query_fixed_chunk0_DATA_scope_unavailable";
    return result;
  }
  result.referenced_persistent_ids_complete = true;
  std::vector<std::int32_t> ids;
  std::unordered_set<std::int32_t> seen;
  for (const auto &raised : *strength.regiment_replenishment_records_v1) {
    if (!raised.native_data_record_count.has_value() ||
        *raised.native_data_record_count < 0 ||
        static_cast<std::size_t>(*raised.native_data_record_count) != raised.records.size())
      result.referenced_persistent_ids_complete = false;
    for (const auto &record : raised.records) {
      if (seen.insert(record.persistent_regiment_id).second)
        ids.push_back(record.persistent_regiment_id);
    }
  }
  bool complete = result.referenced_persistent_ids_complete;
  result.persistent_regiments.reserve(ids.size());
  for (const auto id : ids) {
    auto row = ReadPersistent(bindings, id);
    complete = complete && row.status == game::FixedChunk0PreparationInputStatusV1::available;
    result.persistent_regiments.push_back(row);
  }
  result.status = complete ? game::FixedChunk0PreparationInputStatusV1::available
                          : game::FixedChunk0PreparationInputStatusV1::partial;
  if (!complete) result.unavailable_reason = "scoped_fixed_chunk0_preparation_inputs_partial";
  return result;
}
} // namespace xar::ck3_12003
