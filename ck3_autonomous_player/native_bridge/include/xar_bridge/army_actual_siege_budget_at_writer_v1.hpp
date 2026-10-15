#pragma once
#include <bit>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct ArmyActualSiegeBudgetAtWriterV1 {
  std::optional<std::int32_t> original_supply_budget_soldiers;
  std::optional<std::int32_t> original_siege_budget_soldiers;
  std::optional<std::int32_t> combined_siege_raid_budget_soldiers;
  std::optional<std::int32_t> derived_original_raid_budget_soldiers;
  bool siege_raid_capture_complete = false;
  std::uint32_t capture_failure_flags = 0;
};
inline void AppendArmyActualSiegeBudgetAtWriterV1(
    std::string &out, const ArmyActualSiegeBudgetAtWriterV1 &value) {
  const auto number = [&out](auto n) {
    char bytes[32]{}; const auto end = std::to_chars(bytes, bytes + sizeof(bytes), n);
    out.append(bytes, end.ptr);
  };
  const auto optional = [&out, &number](const auto &n) {
    if (n) number(*n); else out += "null";
  };
  out += "{\"source_callback_entry_rva\":"; number(0x24E3410U);
  out += ",\"source_writer_return_rva\":"; number(0x24E377CU);
  out += ",\"return_slot_basis\":\"natural_writer_hook_incoming_return_address\","
         "\"original_supply_budget_soldiers\":";
  optional(value.original_supply_budget_soldiers);
  out += ",\"original_siege_budget_soldiers\":"; optional(value.original_siege_budget_soldiers);
  out += ",\"combined_siege_raid_budget_soldiers\":"; optional(value.combined_siege_raid_budget_soldiers);
  out += ",\"derived_original_raid_budget_soldiers\":"; optional(value.derived_original_raid_budget_soldiers);
  out += ",\"siege_raid_capture_complete\":"; out += value.siege_raid_capture_complete ? "true" : "false";
  out += ",\"capture_failure_flags\":"; number(value.capture_failure_flags); out += '}';
}
}

namespace xar::ck3_12004 {
// These are offsets from the REAL writer incoming return-address slot, not a
// helper's return slot or the callback's entry RSP. 24E3410 sub rsp,68h and
// CALL24E3777 establish native_callback_rsp = writer_return_slot + 8.
inline constexpr std::size_t kOriginalSupplyFromWriterReturnSlot12004 = 0x28;
inline constexpr std::size_t kOriginalSiegeFromWriterReturnSlot12004 = 0x88;
inline constexpr std::size_t kCombinedFromWriterReturnSlot12004 = 0x90;
static_assert(kOriginalSiegeFromWriterReturnSlot12004 == 8 + 0x80);
static_assert(kCombinedFromWriterReturnSlot12004 == 8 + 0x88);
inline constexpr std::int32_t DeriveOriginalRaidBudget12004(
    std::int32_t combined, std::int32_t siege) noexcept {
  return std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(combined) -
                                     static_cast<std::uint32_t>(siege));
}
static_assert(DeriveOriginalRaidBudget12004(10, 10) == 0);
static_assert(DeriveOriginalRaidBudget12004(-2147483647 - 1, 2147483647) == 1);
// ReadAt is the existing fault-bounded journal reader. No getter is invoked.
template <typename ReadAt>
inline std::optional<game::ArmyActualSiegeBudgetAtWriterV1>
CaptureSiegeBudgetAtNaturalWriter12004(std::optional<std::uint64_t> return_rva,
    const void *natural_writer_return_slot, ReadAt read_at) noexcept {
  if (return_rva != 0x24E377C) return std::nullopt;
  game::ArmyActualSiegeBudgetAtWriterV1 out{};
  if (natural_writer_return_slot == nullptr) {
    out.capture_failure_flags = 1U; return out;
  }
  const auto copy = [&](std::size_t offset, std::optional<std::int32_t> &target,
                        std::uint32_t failure) {
    std::int32_t raw = 0;
    if (read_at(natural_writer_return_slot, offset, &raw, sizeof(raw))) target = raw;
    else out.capture_failure_flags |= failure;
  };
  copy(kOriginalSupplyFromWriterReturnSlot12004, out.original_supply_budget_soldiers, 2U);
  copy(kOriginalSiegeFromWriterReturnSlot12004, out.original_siege_budget_soldiers, 4U);
  copy(kCombinedFromWriterReturnSlot12004, out.combined_siege_raid_budget_soldiers, 8U);
  out.siege_raid_capture_complete = out.original_siege_budget_soldiers.has_value() &&
                                  out.combined_siege_raid_budget_soldiers.has_value();
  if (out.siege_raid_capture_complete)
    out.derived_original_raid_budget_soldiers = DeriveOriginalRaidBudget12004(
        *out.combined_siege_raid_budget_soldiers, *out.original_siege_budget_soldiers);
  return out;
}
}
