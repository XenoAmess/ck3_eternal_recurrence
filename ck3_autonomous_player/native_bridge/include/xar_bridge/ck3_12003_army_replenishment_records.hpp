#pragma once

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {
struct ArmyBindings;
}

namespace xar::game {

enum class ArmyRegimentReplenishmentRecordsStatusV1 : std::uint8_t {
  unavailable,
  partial,
  available,
};

constexpr std::string_view ArmyRegimentReplenishmentRecordsStatusNameV1(
    ArmyRegimentReplenishmentRecordsStatusV1 status) noexcept {
  switch (status) {
  case ArmyRegimentReplenishmentRecordsStatusV1::available: return "available";
  case ArmyRegimentReplenishmentRecordsStatusV1::partial: return "partial";
  default: return "unavailable";
  }
}

inline constexpr std::string_view kArmyRegimentReplenishmentRecordsSourceV1 =
    "native_all_data_records";

struct ArmyRegimentReplenishmentRecordV1 {
  bool available = false;
  std::int32_t record_index = -1;
  std::int32_t persistent_regiment_id = -1;
  std::int32_t chunk_index = -1;
  std::string_view unavailable_reason{};
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> maximum_soldiers;
  // Native 262C9D0 treats state3/current0 as effective maximum. Keep the
  // physical current above, rather than replacing zero with that operand.
  std::optional<std::int32_t> effective_current_soldiers;
  std::optional<std::int32_t> state_raw;
  std::optional<bool> native_can_replenish;
  std::optional<bool> native_chunk_can_replenish;
  // Both are whole-persistent signed Q100000 values. The first is the fresh
  // existing getter; the second is the cache actually consumed by 262C9D0.
  std::optional<std::int64_t> persistent_monthly_replenishment_fraction_raw;
  std::optional<std::int64_t> persistent_prepared_replenishment_fraction_raw;
  std::int32_t fraction_scale = 100'000;
  friend bool operator==(const ArmyRegimentReplenishmentRecordV1 &,
                         const ArmyRegimentReplenishmentRecordV1 &) = default;
};

struct ArmyRegimentReplenishmentRecordsSnapshotV1 {
  ArmyRegimentReplenishmentRecordsStatusV1 status =
      ArmyRegimentReplenishmentRecordsStatusV1::unavailable;
  std::int32_t army_regiment_id = -1;
  std::optional<std::int32_t> native_data_record_count;
  std::string_view unavailable_reason{};
  std::vector<ArmyRegimentReplenishmentRecordV1> records;
  friend bool operator==(const ArmyRegimentReplenishmentRecordsSnapshotV1 &,
                         const ArmyRegimentReplenishmentRecordsSnapshotV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12003 {

// The existing exact .3 binding supplies the persistent registry and native
// getters. Read on its paused owning-thread strength path from a resolved
// CArmyRegiment, not its public CUnit, CArmy or persistent CRegiment.
game::ArmyRegimentReplenishmentRecordsSnapshotV1
ReadArmyRegimentReplenishmentRecordsV1(
    const ck3_12002::ArmyBindings &bindings, const void *resolved_army_regiment,
    std::int32_t army_regiment_id) noexcept;

} // namespace xar::ck3_12003
