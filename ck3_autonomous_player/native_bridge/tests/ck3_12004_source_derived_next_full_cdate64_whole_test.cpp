#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_future_daily_supply_schedule.hpp"
#include "xar_bridge/ck3_12004_source_derived_next_daily_supply_frame.hpp"
#include "xar_bridge/ck3_12004_cdate_calendar.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
namespace current = ck3_12004;
constexpr std::int32_t kUnit = 0x01000001;
constexpr std::int32_t kArmy = 0x02000001;
constexpr std::int32_t kRegiment = 0x03000001;
constexpr std::int32_t kCurrentDate = 53288448;
// Independent synthetic stored D; source-derived future D must not be D+1.
constexpr std::int32_t kCurrentD = 12;
constexpr std::int64_t kCurrentDateStorage = (std::int64_t{7} << 32) | kCurrentDate;
constexpr std::string_view kStem = "01-source-derived-next-full-cdate64";
constexpr std::uintptr_t kFixtureImageBase = 0x140000000ULL;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture-owned object store out of range");
  std::memcpy(object.data() + offset, &value, sizeof value);
}

// The native manager secondary is embedded at GameData+2A548; not an indirect
// pointer slot. Large input storage and its before-copy are directly heap-owned.
struct Inputs {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x2A9B0> game_data{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x18> province{};
  std::array<void *, 2> provinces{};
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  std::array<const void *, 4> next_phase_pointers{};
  std::array<std::uint8_t, 365> calendar_day_table{}, calendar_month_table{};
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Counters {
  std::size_t current_soldiers = 0, maximum_soldiers = 0;
  std::size_t supply_capacity = 0, attrition_fraction = 0, monthly_supply = 0;
  bool abi_matches = true;
  std::vector<std::string> events;
};
struct Fixture;
Fixture *active = nullptr;
std::int32_t CurrentSoldiers(void *, std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int64_t *SupplyCapacity(std::int64_t *, void *, void *);
std::int64_t *Attrition(void *, std::int64_t *, void *);
std::int64_t *MonthlySupply(void *, std::int64_t *, void *, void *);

struct Fixture {
  Inputs input{};
  void *game_slot = input.game_state.data();
  void *unit_slot = input.unit_storage.data();
  void *army_slot = input.army_storage.data();
  void *regiment_slot = input.regiment_storage.data();
  current::ArmyBindings bindings{};
  Counters calls{};
  Fixture() {
    Store(input.game_state, 0x08, kCurrentDateStorage);
    Store(input.game_state, 0x9C, kCurrentD);
    Store(input.game_state, 0xA0, static_cast<void *>(input.game_data.data()));
    input.provinces = {nullptr, input.province.data()};
    Store(input.game_data, 0x140, static_cast<void *>(input.provinces.data()));
    Store(input.game_data, 0x14C, std::int32_t{2});
    Store(input.province, 0x10, std::int32_t{1});
    Store(input.unit_storage, 0x20, static_cast<void *>(input.unit_slots.data()));
    Store(input.unit_storage, 0x2C, std::int32_t{2});
    Store(input.army_storage, 0x20, static_cast<void *>(input.army_slots.data()));
    Store(input.army_storage, 0x2C, std::int32_t{2});
    Store(input.regiment_storage, 0x20, static_cast<void *>(input.regiment_slots.data()));
    Store(input.regiment_storage, 0x2C, std::int32_t{2});
    Store(input.unit_slots, 0x18, static_cast<void *>(input.unit.data()));
    Store(input.army_slots, 0x18, static_cast<void *>(input.army.data()));
    Store(input.regiment_slots, 0x18, static_cast<void *>(input.regiment.data()));
    Store(input.unit, 0x10, kUnit);
    Store(input.unit, 0x174, std::int32_t{29829});
    Store(input.unit, 0x178, kArmy);
    Store(input.unit, 0x20, static_cast<void *>(input.province.data()));
    Store(input.army, 0x10, kArmy);
    Store(input.army, 0x14, std::uint32_t{0x41726D79});
    Store(input.army, 0x124, kUnit);
    Store(input.army, 0x38, static_cast<void *>(input.regiment_ids.data()));
    Store(input.army, 0x40, std::int32_t{2});
    Store(input.army, 0x44, std::int32_t{2});
    Store(input.army, 0x180, std::int64_t{123450000});
    Store(input.regiment, 0x10, kRegiment);
    Store(input.regiment, 0x14, std::uint32_t{0x41725267});
    Store(input.regiment, 0x38, std::int32_t{50});
    Store(input.regiment, 0x3C, std::int32_t{100});
    Store(input.regiment, 0x40, std::int64_t{25000000});
    // Current phase12 is genuinely empty. Phase13 has repeated exact CArmy
    // pointers at original positions1/3. Non-target pointers are not dereferenced.
    input.next_phase_pointers = {
        input.unit.data(), input.army.data(), nullptr, input.army.data()};
    constexpr auto next_header = std::size_t{0x2A548 + 0x190 + 24 * 13};
    Store(input.game_data, next_header, static_cast<const void *>(input.next_phase_pointers.data()));
    Store(input.game_data, next_header + 0x08, std::int32_t{4});
    Store(input.game_data, next_header + 0x0C, std::int32_t{4});
    // An independently partial unrelated phase must not erase the clock pair.
    constexpr auto partial_header = std::size_t{0x2A548 + 0x190 + 24 * 4};
    Store(input.game_data, partial_header + 0x0C, std::int32_t{-1});
    bindings.enabled = true;
    bindings.game_state_slot = &game_slot;
    bindings.unit_storage_slot = &unit_slot;
    bindings.internal_army_storage_slot = &army_slot;
    bindings.regiment_storage_slot = &regiment_slot;
    bindings.get_army_current_soldiers = CurrentSoldiers;
    bindings.get_army_maximum_soldiers = MaximumSoldiers;
    bindings.get_army_supply_capacity = SupplyCapacity;
    bindings.get_army_attrition_fraction = Attrition;
    bindings.get_army_monthly_supply_change = MonthlySupply;
    bindings.future_daily_supply_schedule_bindings =
        current::BindFutureDailySupplySchedule12004(kFixtureImageBase, current::kExecutableSha256);
    bindings.source_derived_next_daily_supply_frame_bindings =
        current::BindSourceDerivedNextDailySupplyFrame12004(kFixtureImageBase, current::kExecutableSha256);
    const auto &bound = bindings.source_derived_next_daily_supply_frame_bindings;
    Check(bound.calendar_day_table == reinterpret_cast<const std::uint8_t *>(
        kFixtureImageBase + current::kCDateCalendarDayTableRva12004) &&
        bound.calendar_month_table == reinterpret_cast<const std::uint8_t *>(
        kFixtureImageBase + current::kCDateCalendarMonthTableRva12004),
        "exact actual4 calendar RIP targets were not bound");
    // Only two selected bytes are caller-owned fixture inputs. This does not
    // claim an executable table dump or an observed future game frame.
    input.calendar_day_table[58] = 28;
    input.calendar_month_table[58] = 1;
    bindings.source_derived_next_daily_supply_frame_bindings.calendar_day_table =
        input.calendar_day_table.data();
    bindings.source_derived_next_daily_supply_frame_bindings.calendar_month_table =
        input.calendar_month_table.data();
    // No native date writer or future effect callback is enabled.
  }
};
std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  auto &f = *active;
  ++f.calls.current_soldiers;
  f.calls.events.emplace_back("army_current_soldiers");
  f.calls.abi_matches &= receiver == f.input.army.data() + 0x38 && flags == 0;
  return 100;
}
std::int32_t MaximumSoldiers(void *receiver) {
  auto &f = *active;
  ++f.calls.maximum_soldiers;
  f.calls.events.emplace_back("army_maximum_soldiers");
  f.calls.abi_matches &= receiver == f.input.army.data();
  return 200;
}
std::int64_t *SupplyCapacity(std::int64_t *out, void *receiver, void *details) {
  auto &f = *active;
  ++f.calls.supply_capacity;
  f.calls.events.emplace_back("army_supply_capacity");
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 200000000;
  return out;
}
std::int64_t *Attrition(void *receiver, std::int64_t *out, void *details) {
  auto &f = *active;
  ++f.calls.attrition_fraction;
  f.calls.events.emplace_back("army_attrition_fraction");
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 1250;
  return out;
}
std::int64_t *MonthlySupply(void *receiver, std::int64_t *out, void *province, void *details) {
  auto &f = *active;
  ++f.calls.monthly_supply;
  f.calls.events.emplace_back("army_monthly_supply_change");
  f.calls.abi_matches &= out && receiver == f.input.army.data() &&
      province == f.input.province.data() && details == nullptr;
  *out = -1200000;
  return out;
}
void AppendString(std::string &out, std::string_view value) {
  out += '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}
void AppendIds(std::string &out, const std::vector<std::int32_t> &ids) {
  out += '[';
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (i) out += ',';
    out += std::to_string(ids[i]);
  }
  out += ']';
}
void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream file(path, std::ios::binary);
  file << text << '\n';
  Check(static_cast<bool>(file), "new whole fixture artifact write failed");
}
void AssertScene(const Fixture &f, const Inputs &before, const game::ArmyStrengthSnapshot &row) {
  Check(row.available && row.army_id == kUnit && row.native_carmy_id_observable &&
      row.native_carmy_id == kArmy, "whole reader identity changed");
  Check(row.regiment_count == 2 && row.regiment_strengths && row.regiment_strengths->size() == 2 &&
      (*row.regiment_strengths)[0].army_regiment_id == kRegiment &&
      (*row.regiment_strengths)[1].army_regiment_id == kRegiment &&
      row.current_soldiers == 100 && row.maximum_soldiers == 200,
      "original whole duplicate roster/totals changed");
  Check(row.current_supply_raw == 123450000 && row.current_supply_capacity_raw == 200000000 &&
      row.current_supply_change_monthly_raw == -1200000 &&
      row.current_attrition_fraction_raw == 1250, "whole original scalar observations changed");
  Check(row.future_daily_supply_schedule_inputs_v1.has_value(), "real all30 collector omitted");
  const auto &schedule = *row.future_daily_supply_schedule_inputs_v1;
  Check(schedule.status == "partial" && !schedule.ready && schedule.phases.size() == 30 &&
      schedule.unavailable_reason == "future_daily_supply_schedule_phase_inputs_partial",
      "unrelated partial phase readiness changed");
  Check(schedule.subject_army_id_u32 == static_cast<std::uint32_t>(kUnit) &&
      schedule.subject_carmy_id_u32 == static_cast<std::uint32_t>(kArmy) &&
      schedule.current_date_storage_raw64 == kCurrentDateStorage &&
      schedule.current_date_raw_i32 == kCurrentDate &&
      schedule.native_day_index_raw_i32 == kCurrentD &&
      schedule.selected_phase_index_i32 == 12, "same-capture current clock/IDs changed");
  const auto &now = schedule.phases[12];
  const auto &next = schedule.phases[13];
  const auto &partial = schedule.phases[4];
  Check(now.ready && now.count_raw_i32 == 0 && now.data_pointer_present == false &&
      now.matching_positions && now.matching_positions->empty() &&
      now.subject_occurrence_count_i32 == 0, "real current empty bucket was not retained");
  Check(next.ready && next.count_raw_i32 == 4 && next.matching_positions &&
      *next.matching_positions == std::vector<std::int32_t>({1, 3}) &&
      next.subject_occurrence_count_i32 == 2, "next bucket duplicate/gap occurrences changed");
  Check(!partial.ready && partial.count_raw_i32 == -1 &&
      partial.data_pointer_present == false && !partial.matching_positions &&
      !partial.subject_occurrence_count_i32 &&
      partial.unavailable_reason == "future_daily_supply_schedule_negative_bucket_count",
      "unrelated negative bucket was silently completed");
  Check(row.source_derived_next_daily_supply_frame_inputs_v1.has_value(),
      "production same-row next pair hook omitted");
  const auto &pair = *row.source_derived_next_daily_supply_frame_inputs_v1;
  Check(pair.status == "available" && pair.ready && !pair.unavailable_reason &&
      pair.subject_army_id_u32 == schedule.subject_army_id_u32 &&
      pair.subject_carmy_id_u32 == schedule.subject_carmy_id_u32 &&
      pair.current_date_storage_raw64 == schedule.current_date_storage_raw64 &&
      pair.current_date_raw_i32 == schedule.current_date_raw_i32 &&
      pair.current_native_day_index_raw_i32 == schedule.native_day_index_raw_i32,
      "next pair did not use the original same-row current capture");
  // Expected future literals are assertions only; fixture never assigns a future leaf/frame.
  Check(pair.source_derived_next_date_raw_i32 == 53288472 &&
      pair.source_derived_next_native_day_index_raw_i32 == 395353 &&
      pair.source_derived_next_native_day_index_raw_i32 != kCurrentD + 1,
      "native source arithmetic changed or was replaced by currentD+1");
  constexpr auto expected_full_date = (std::int64_t{1083} << 48) |
      (std::int64_t{1} << 40) | (std::int64_t{28} << 32) | 53288472;
  Check(pair.source_derived_full_cdate64_ready &&
      pair.source_derived_next_date_storage_raw64 == expected_full_date &&
      pair.source_derived_next_calendar_day_u8 == 28 &&
      pair.source_derived_next_calendar_month_u8 == 1 &&
      pair.source_derived_next_date_storage_raw64 != kCurrentDateStorage + 24,
      "full source-derived clock did not use the selected month/day table bytes");
  Check(f.calls.abi_matches && f.calls.current_soldiers == 1 &&
      f.calls.maximum_soldiers == 1 && f.calls.supply_capacity == 1 &&
      f.calls.attrition_fraction == 1 && f.calls.monthly_supply == 1 &&
      f.calls.events == std::vector<std::string>({
          "army_current_soldiers", "army_maximum_soldiers", "army_supply_capacity",
          "army_attrition_fraction", "army_monthly_supply_change"}),
      "actual whole reader callback ABI/count/order changed");
  Check(f.input == before, "readonly whole reader changed fixture-owned input memory");
}
std::string SerializeWhole(const game::ArmyStrengthSnapshot &row) {
  std::string wire =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"army-next-full-cdate64-source-derived-01\",\"ok\":true,"
      "\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  wire += "]}}";
  return game::Render12004BuildIdentity(std::move(wire), game::Ck3_12004AdapterDescriptor());
}
std::string Context(const Fixture &f, const game::ArmyStrengthSnapshot &row) {
  const auto &pair = *row.source_derived_next_daily_supply_frame_inputs_v1;
  std::string out =
      "{\"schema\":\"xar.source-derived-next-full-cdate64-native-context.v1\","
      "\"scene\":\"source-derived-next-full-cdate64-native-row-join\","
      "\"producer\":\"ReadArmyStrengthsForScope12004 -> AppendArmyStrengthV1 -> Render12004BuildIdentity\","
      "\"actual4_identity\":{\"backend_id\":";
  AppendString(out, current::kAdapterId);
  out += ",\"game_version\":";
  AppendString(out, current::kGameVersion);
  out += ",\"executable_sha256\":";
  AppendString(out, current::kExecutableSha256);
  out += "},\"synthetic_context\":{\"actor_character_id\":29829,"
      "\"public_revision\":1,\"native_revision\":1,\"snapshot_id\":\"native:1\","
      "\"date_raw\":53288448,\"paused\":true,\"map_ready\":true,"
      "\"bridge_host_pid\":1200401,\"current_province_id\":1,\"scope_role\":\"player\","
      "\"scope_army_ids\":[16777217],\"war_ids\":[],"
      "\"transport_connection_id\":\"source-derived-next-full-cdate64-12004\","
      "\"episode_id\":\"source-derived-next-full-cdate64-12004\"},"
      "\"heartbeat_published\":false,\"native_inputs\":{\"current_date_storage_raw64\":";
  out += std::to_string(*pair.current_date_storage_raw64);
  out += ",\"current_date_raw_i32\":";
  out += std::to_string(*pair.current_date_raw_i32);
  out += ",\"current_native_day_index_raw_i32\":";
  out += std::to_string(*pair.current_native_day_index_raw_i32);
  out += ",\"source_derived_next_date_raw_i32\":";
  out += std::to_string(*pair.source_derived_next_date_raw_i32);
  out += ",\"source_derived_next_native_day_index_raw_i32\":";
  out += std::to_string(*pair.source_derived_next_native_day_index_raw_i32);
  out += ",\"source_derived_next_date_storage_raw64\":";
  out += std::to_string(*pair.source_derived_next_date_storage_raw64);
  out += ",\"source_derived_next_calendar_day_u8\":";
  out += std::to_string(*pair.source_derived_next_calendar_day_u8);
  out += ",\"source_derived_next_calendar_month_u8\":";
  out += std::to_string(*pair.source_derived_next_calendar_month_u8);
  out += ",\"source_derived_full_cdate64_ready\":true";
  out += ",\"current_phase_index_i32\":12,\"current_phase_count_raw_i32\":0,"
      "\"current_phase_matching_positions\":[],\"current_phase_subject_occurrence_count_i32\":0,"
      "\"demanded_next_phase_index_i32\":13,\"next_phase_count_raw_i32\":4,"
      "\"next_phase_matching_positions\":[1,3],\"next_phase_subject_occurrence_count_i32\":2,"
      "\"unrelated_partial_phase_index_i32\":4,\"unrelated_partial_count_raw_i32\":-1,"
      "\"unrelated_partial_data_pointer_present\":false},"
      "\"callbacks\":{\"unit_state\":0,\"army_current_soldiers\":";
  out += std::to_string(f.calls.current_soldiers);
  out += ",\"army_maximum_soldiers\":";
  out += std::to_string(f.calls.maximum_soldiers);
  out += ",\"army_supply_capacity\":";
  out += std::to_string(f.calls.supply_capacity);
  out += ",\"army_attrition_fraction\":";
  out += std::to_string(f.calls.attrition_fraction);
  out += ",\"army_monthly_supply_change\":";
  out += std::to_string(f.calls.monthly_supply);
  out += ",\"disembark\":0,\"native_daily_date_writer\":0,\"abi_matches\":";
  out += f.calls.abi_matches ? "true" : "false";
  out += ",\"ordered_events\":[";
  for (std::size_t i = 0; i < f.calls.events.size(); ++i) {
    if (i) out += ',';
    AppendString(out, f.calls.events[i]);
  }
  out += "]},\"all_fixture_input_bytes_unchanged\":true,\"assertions_passed\":true,"
      "\"calendar_source\":{\"day_table_rva\":\"0x444C4B0\","
      "\"month_table_rva\":\"0x444C340\",\"calendar_index_i32\":58,"
      "\"year_quotient_i32\":1083,\"fixture_owned_table_inputs\":true,"
      "\"selected_day_byte\":28,\"selected_month_byte\":1,"
      "\"old_month_LEA_reference_captured_raw\":false,"
      "\"old_month_LEA_reference_origin\":\"reconstructed_from_held_decoded_instruction\","
      "\"new_month_LEA_actual_read_bytes\":7},"
      "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
      "\"G2_context_is_metadata_only\":true,\"G2_actual_stored_D_claimed\":false}";
  return out;
}
} // namespace

int main(int argc, char **argv) {
  std::filesystem::path output;
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
        "usage: xar_ck3_12004_source_derived_next_full_cdate64_whole_test --wire-dir <fresh-dir>");
    output = argv[2];
    std::filesystem::create_directories(output);
    auto fixture = std::make_unique<Fixture>();
    Check(fixture->bindings.future_daily_supply_schedule_bindings.enabled &&
        fixture->bindings.source_derived_next_daily_supply_frame_bindings.enabled,
        "new readonly binders did not select exact actual4 identity");
    auto before = std::make_unique<Inputs>(fixture->input);
    active = fixture.get();
    const std::array<current::ArmyStrengthScope, 1> scope{
        current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    const auto result = current::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows);
    Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
        "real whole Strength producer did not return one available row");
    AssertScene(*fixture, *before, rows.front());
    Write(output / (std::string(kStem) + ".json"), SerializeWhole(rows.front()));
    Write(output / (std::string(kStem) + "-native-context.json"), Context(*fixture, rows.front()));
    Write(output / "PRODUCER-RECEIPT.json",
        "{\"schema\":\"xar.source-derived-next-full-cdate64-producer-receipt.v1\","
        "\"status\":\"PASS\",\"scene_count\":1,\"whole_reader_calls\":1,"
        "\"whole_serializer_calls\":1,\"fixture_owned_objects_and_callbacks\":true,"
        "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
        "\"old_GREEN_replayed\":false,\"all_fixture_input_bytes_unchanged\":true}");
    active = nullptr;
    std::cout << "one source-derived full CDate64 whole scene emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    if (!output.empty()) {
      std::string receipt =
          "{\"schema\":\"xar.source-derived-next-full-cdate64-producer-receipt.v1\","
          "\"status\":\"FAIL\",\"scene_count\":1,\"error\":";
      AppendString(receipt, error.what());
      receipt += ",\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false}";
      std::ofstream file(output / "PRODUCER-RECEIPT.json", std::ios::binary);
      file << receipt << '\n';
    }
    std::cerr << error.what() << '\n';
    return 1;
  }
}
