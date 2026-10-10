#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12004_actual_supply_callback_journal.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
namespace native = xar::ck3_12004;
namespace game = xar::game;
constexpr std::int32_t kPublicArmy = 0x0D000070;
constexpr std::int32_t kNativeArmy = 0x0E000090;
constexpr std::int32_t kOtherPublicGeneration = 0x0F000070;
constexpr std::int32_t kOtherNativeGeneration = 0x10000090;
constexpr std::uint64_t kDate = 53289576;
constexpr std::uint64_t kPreviousDate = 53289552;
constexpr std::uint32_t kWrapperInvocations = 5;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &object, std::size_t offset, Value value) {
  Check(offset <= Size && sizeof(Value) <= Size - offset,
        "fixture object store outside owned range");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

template <class Value, std::size_t Size>
Value Load(const std::array<std::byte, Size> &object, std::size_t offset) {
  Check(offset <= Size && sizeof(Value) <= Size - offset,
        "fixture object load outside owned range");
  Value result{};
  std::memcpy(&result, object.data() + offset, sizeof(result));
  return result;
}

struct Fixture {
  std::array<std::byte, 0x190> army{};
  std::uint64_t passed_date = kDate;
  std::uint32_t original_calls = 0;
  std::uint32_t memory_reads = 0;
  std::uint32_t selected_case = 0;
  bool original_abi_matches = true;
  bool partial_after_enabled = false;

  Fixture() {
    Store(army, 0x10, kNativeArmy);
    Store(army, 0x124, kPublicArmy);
    Store(army, 0x180, std::int64_t{10000000});
    Store(army, 0x188, kPreviousDate);
    Store(army, 0x22, std::uint8_t{0});
  }
};

Fixture *active = nullptr;

bool InRange(const void *address, std::size_t size, const void *base,
             std::size_t extent) noexcept {
  const auto start = reinterpret_cast<std::uintptr_t>(base);
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  return value >= start && value - start <= extent &&
         size <= extent - (value - start);
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.memory_reads;
  const bool owned =
      InRange(address, size, fixture.army.data(), fixture.army.size()) ||
      InRange(address, size, &fixture.passed_date, sizeof(fixture.passed_date));
  if (!owned) return false;
  // Only the fifth callback's immediate after-stock is unreadable. Its IDs,
  // update date and byte remain readable, so partial evidence must survive.
  if (fixture.partial_after_enabled && fixture.original_calls == 5 &&
      address == fixture.army.data() + 0x180 && size == sizeof(std::int64_t))
    return false;
  std::memcpy(output, address, size);
  return true;
}

// Typed local original. Only the production wrapper/capture/journal/serializer
// run unchanged; the CK3 executable and native supply updater are never called.
void __fastcall Original(void *army, const void *date) {
  auto &fixture = *active;
  ++fixture.original_calls;
  fixture.original_abi_matches &= army == fixture.army.data() &&
      date == &fixture.passed_date && fixture.selected_case == fixture.original_calls;
  switch (fixture.selected_case) {
  case 1:
    Store(fixture.army, 0x180, std::int64_t{9875000});
    Store(fixture.army, 0x188, kDate);
    Store(fixture.army, 0x22, std::uint8_t{1});
    break;
  case 2:
    // A complete zero result is a real observed equality, not missing data.
    break;
  case 3:
    // Rejected-shaped observation only; no updater AL/predicate is inferred.
    Store(fixture.army, 0x22, std::uint8_t{1});
    break;
  case 4:
    Store(fixture.army, 0x180, std::int64_t{10000000});
    break;
  case 5:
    Store(fixture.army, 0x180, std::int64_t{9875000});
    break;
  default:
    fixture.original_abi_matches = false;
    break;
  }
}

void Invoke(Fixture &fixture, std::uint32_t selected_case) {
  const auto count_before = fixture.original_calls;
  fixture.selected_case = selected_case;
  if (selected_case == 3) Store(fixture.army, 0x22, std::uint8_t{0});
  fixture.partial_after_enabled = selected_case == 5;
  native::XarActualSupplyCallbackHook12004V1(
      fixture.army.data(), &fixture.passed_date);
  Check(fixture.original_calls == count_before + 1 && fixture.original_abi_matches,
        "production entry wrapper changed original ABI or exact invocation count");
}

void AssertCaptured(const game::ArmyActualSupplyCallbackObservationsV1 &observed) {
  Check(!observed.observer_installed && observed.events.size() == 5 &&
            observed.oldest_available_sequence == 1 && observed.latest_sequence == 5 &&
            observed.overwritten_events == 0 && observed.unattributed_capture_failures == 0,
        "journal did not retain the five actual typed wrapper invocations");
  constexpr std::array<std::int64_t, 5> before_stock{
      10000000, 9875000, 9875000, 9875000, 10000000};
  constexpr std::array<std::int64_t, 4> after_stock{
      9875000, 9875000, 9875000, 10000000};
  constexpr std::array<std::uint8_t, 5> before_byte{0, 1, 0, 1, 1};
  for (std::size_t index = 0; index < observed.events.size(); ++index) {
    const auto &event = observed.events[index];
    Check(event.sequence == index + 1 && event.army_id == kPublicArmy &&
              event.native_carmy_id == kNativeArmy && event.passed_date_raw64 == kDate &&
              !event.caller_return_rva && event.same_instance_after &&
              event.before.supply_raw == before_stock[index] &&
              event.before.last_supply_update_date_raw64 ==
                  (index == 0 ? kPreviousDate : kDate) &&
              event.after.last_supply_update_date_raw64 == kDate &&
              event.before.supply_updated_byte_raw == before_byte[index] &&
              event.after.supply_updated_byte_raw == 1,
          "entry-return capture changed actual identity/date/independent scalar values");
    if (index < after_stock.size()) {
      Check(event.after.supply_raw == after_stock[index] &&
                event.capture_failure_flags == 0,
            "complete stock observation lost a real zero/drain/gain value");
    } else {
      Check(!event.after.supply_raw &&
                event.capture_failure_flags == native::actual_supply_callback_capture_after,
            "partial after-stock failure erased readable values or fabricated a zero");
    }
  }
}

void AssertGenerationExclusion() {
  Check((kPublicArmy & 0xFFFFFF) == (kOtherPublicGeneration & 0xFFFFFF) &&
            (kNativeArmy & 0xFFFFFF) == (kOtherNativeGeneration & 0xFFFFFF),
        "generation fixture does not retain the same storage indices");
  const auto wrong_public = native::ReadActualSupplyCallbackObservations12004(
      kOtherPublicGeneration, kNativeArmy);
  const auto wrong_native = native::ReadActualSupplyCallbackObservations12004(
      kPublicArmy, kOtherNativeGeneration);
  Check(wrong_public && wrong_native && wrong_public->events.empty() &&
            wrong_native->events.empty() && wrong_public->latest_sequence == 5 &&
            wrong_native->latest_sequence == 5,
        "journal matched a public/native index or only one of the complete IDs");
}

void AppendString(std::string &output, std::string_view value) {
  output += '"';
  for (const auto character : value) {
    if (character == '"' || character == '\\') output += '\\';
    output += character;
  }
  output += '"';
}

void AppendIds(std::string &output, const std::vector<std::int32_t> &ids) {
  output += '[';
  for (std::size_t index = 0; index < ids.size(); ++index) {
    if (index != 0) output += ',';
    output += std::to_string(ids[index]);
  }
  output += ']';
}

game::ArmyStrengthSnapshot CurrentRow(const Fixture &fixture,
                                     std::int32_t public_army_id,
                                     std::int32_t native_army_id) {
  game::ArmyStrengthSnapshot row{};
  row.available = true;
  row.army_id = public_army_id;
  row.native_carmy_id_observable = true;
  row.native_carmy_id = native_army_id;
  row.scope_role = game::ArmyStrengthScopeRole::player;
  row.regiment_count = 1;
  row.current_soldiers = 1843;
  row.maximum_soldiers = 2367;
  row.current_supply_raw = Load<std::int64_t>(fixture.army, 0x180);
  game::ArmyRegimentStrengthSnapshot regiment{};
  regiment.army_regiment_id = 0x0B000023;
  regiment.current_soldiers = row.current_soldiers;
  regiment.maximum_soldiers = row.maximum_soldiers;
  regiment.composition_unavailable_reason = "fixture_type_not_observed";
  row.regiment_strengths = std::vector{regiment};
  return row;
}

std::string Whole(const std::array<game::ArmyStrengthSnapshot, 2> &rows) {
  std::string output =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"actual-supply-callback-whole-native-01\",\"ok\":true,"
      "\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) output += ',';
    // This exact production formatter must include Root's minimal readout hook.
    // Never append, replace or prebuild a standalone supply observation leaf.
    game::AppendArmyStrengthV1(output, rows[index],
        [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  }
  output += "]}}";
  return output;
}

std::string Packet(const Fixture &fixture,
                   const std::array<game::ArmyStrengthSnapshot, 2> &rows) {
  std::string output =
      "{\"schema_version\":1,\"fixture_receipt\":{"
      "\"original_target_kind\":\"typed_fixture_callback\","
      "\"native_EXE_invoked\":false,\"wrapper_invocations\":5,"
      "\"original_invocations\":";
  output += std::to_string(fixture.original_calls);
  output += ",\"original_exactly_once_per_wrapper\":true,"
            "\"full_id_membership_proven\":true,"
            "\"both_full_id_membership_proven\":true,"
            "\"wrong_native_generation_event_count\":0,"
            "\"per_field_partial_read_preserved\":true,"
            "\"updater_return_or_predicate_inferred\":false,"
            "\"physical_soldier_loss_inferred\":false,"
            "\"observed_date_raw32\":";
  output += std::to_string(kDate);
  output += ",\"matching_army_id\":" + std::to_string(kPublicArmy);
  output += ",\"matching_native_carmy_id\":" + std::to_string(kNativeArmy);
  output += ",\"wrong_public_generation_army_id\":" + std::to_string(kOtherPublicGeneration);
  output += ",\"wrong_native_generation_carmy_id\":" + std::to_string(kOtherNativeGeneration);
  output += ",\"scene_names\":[\"drain\",\"zero\",\"byte_only_rejected_shaped\","
            "\"positive_replenishment\",\"partial_after\","
            "\"independent_full_id_generation_exclusion\"]},\"whole\":";
  output += Whole(rows);
  output += '}';
  return output;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-out",
          "usage: xar_ck3_12004_actual_supply_callback_whole_test --wire-out <fresh-json>");
    Fixture fixture{};
    active = &fixture;
    native::ActualSupplyCallbackJournalBindingsV1 bindings{};
    bindings.enabled = true;
    bindings.read_context = &fixture;
    bindings.read_memory = ReadMemory;
    Check(native::InitializeActualSupplyCallbackJournalFixture12004(bindings, Original),
          "production journal fixture initializer rejected typed local callback");
    for (std::uint32_t selected_case = 1; selected_case <= kWrapperInvocations; ++selected_case)
      Invoke(fixture, selected_case);
    const auto observations = native::ReadActualSupplyCallbackObservations12004(
        kPublicArmy, kNativeArmy);
    Check(observations.has_value(), "configured production journal family is absent");
    AssertCaptured(*observations);
    AssertGenerationExclusion();
    const std::array rows{
        CurrentRow(fixture, kPublicArmy, kNativeArmy),
        CurrentRow(fixture, kOtherPublicGeneration, kNativeArmy),
    };
    const auto reads_before = fixture.memory_reads;
    const auto packet = Packet(fixture, rows);
    Check(fixture.original_calls == kWrapperInvocations &&
              fixture.memory_reads == reads_before,
          "query serializer read native memory or replayed a callback");
    Check(packet.find("\"actual_supply_callback_observations_v1\"") != std::string::npos,
          "production Army serializer lacks the minimal natural callback journal hook");
    const std::filesystem::path path = argv[2];
    Check(!std::filesystem::exists(path), "native whole wire output already exists");
    if (!path.parent_path().empty()) std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << packet << '\n';
    Check(static_cast<bool>(file), "native whole wire output write failed");
    active = nullptr;
    std::cout << "actual supply callback whole native fixture emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
