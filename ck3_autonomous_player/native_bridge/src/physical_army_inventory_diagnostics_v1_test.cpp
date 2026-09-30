// Include the production TU to reach its private classifier directly. This
// fixture calls no game/world reader and does not execute the old matrix.
#include "ck3_11906.cpp"
#include "xar_bridge/physical_army_inventory_diagnostics_v1_json.hpp"

#include <iostream>

namespace {

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &buffer, std::size_t offset,
           Value value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

int Fail(const char *message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  constexpr std::int32_t unit_id = 0x03000001;
  constexpr std::int32_t carmy_id = 0x02000001;
  std::array<std::byte, 0x190> unit{};
  std::array<std::byte, 0x130> carmy{};
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 2 * kComponentStorageSlotSize> slots{};
  void *storage_pointer = storage.data();
  Store(unit, kUnitKindRawOffset, std::int32_t{0});
  Store(unit, kUnitArmyIdOffset, carmy_id);
  Store(carmy, kInternalArmyIdOffset, carmy_id);
  Store(carmy, kInternalArmyUnitIdOffset, unit_id);
  Store(storage, kComponentStorageSlotsOffset,
        static_cast<void *>(slots.data()));
  Store(storage, kComponentStorageCapacityOffset, std::int32_t{2});
  Store(slots, kComponentStorageSlotSize + kComponentStorageSlotObjectOffset,
        static_cast<void *>(carmy.data()));
  Bindings bindings{};
  bindings.army_internal_storage_slot = &storage_pointer;
  PhysicalArmyNoncanonicalSlotV1 row{};
  if (!IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id, &row) ||
      !IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id) ||
      !row.carmy_resolution_attempted || !row.carmy_resolved ||
      row.canonical_cunit_id != unit_id || row.reason != "not_rejected") {
    return Fail("diagnostic changed canonical classification");
  }
  for (const auto kind : {std::int32_t{1}, std::int32_t{7}}) {
    Store(unit, kUnitKindRawOffset, kind);
    // A nonzero kind must short-circuit even with no CArmy storage binding.
    bindings.army_internal_storage_slot = nullptr;
    row = {};
    if (IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id, &row) ||
        IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id) ||
        row.raw_kind != kind || row.carmy_resolution_attempted ||
        row.carmy_resolved || row.reason != "nonzero_unit_kind") {
      return Fail("nonzero kind was reinterpreted as CArmy");
    }
  }
  bindings.army_internal_storage_slot = &storage_pointer;
  Store(unit, kUnitKindRawOffset, std::int32_t{0});
  for (const auto missing : {std::int32_t{-1}, std::int32_t{0x04000001}}) {
    Store(unit, kUnitArmyIdOffset, missing);
    row = {};
    if (IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id, &row) ||
        !row.carmy_resolution_attempted || row.native_carmy_id != missing ||
        row.carmy_resolved || row.reason != "carmy_unresolved") {
      return Fail("unresolved full CArmy ID lost its diagnostic");
    }
  }
  Store(unit, kUnitArmyIdOffset, carmy_id);
  Store(carmy, kInternalArmyUnitIdOffset, std::int32_t{0x04000001});
  row = {};
  if (IsCanonicalOrderableArmyUnit(bindings, unit.data(), unit_id, &row) ||
      !row.carmy_resolved || row.canonical_cunit_id != 0x04000001 ||
      row.reason != "canonical_backlink_mismatch") {
    return Fail("full-generation backlink mismatch was not retained");
  }
  PhysicalArmyInventoryDiagnosticsV1 diagnostics{};
  auto &scan = diagnostics.first_scan;
  scan.performed = true;
  scan.date_raw = 53219928;
  scan.war_id = 16777231;
  scan.subject_army_id = unit_id;
  scan.storage_capacity = 2048;
  for (std::size_t index = 0; index <
       kPhysicalArmyNoncanonicalSampleLimitV1 + 1; ++index) {
    row.slot_index = static_cast<std::int32_t>(index);
    scan.Record(row);
  }
  if (scan.sample_count != kPhysicalArmyNoncanonicalSampleLimitV1 ||
      scan.noncanonical_slots != 33 || !scan.truncated ||
      scan.samples.back().slot_index != 31 ||
      diagnostics.second_scan.performed) {
    return Fail("bounded samples or independent scan binding changed");
  }
  std::string serialized;
  AppendPhysicalArmyInventoryDiagnosticsV1(
      serialized, diagnostics, PhysicalArmyInventoryStatusV1::partial);
  if (serialized.find("\"reader_status\":\"partial\"") == std::string::npos ||
      serialized.find("\"date_raw\":53219928") == std::string::npos ||
      serialized.find("\"sample_count\":32,\"truncated\":true") ==
          std::string::npos ||
      serialized.find("\"reason\":\"canonical_backlink_mismatch\"") ==
          std::string::npos ||
      serialized.find("\"second_scan\":{\"performed\":false") ==
          std::string::npos) {
    return Fail("diagnostic wire lost status, sample, or scan identity");
  }
  std::cout << serialized << '\n';
  return 0;
}
