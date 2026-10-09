#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"

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
constexpr std::int32_t kRegiment = 0x03000001;
constexpr std::int32_t kNextGeneration = 0x04000001;
constexpr std::int32_t kPersistent = 0x05000001;
constexpr std::int32_t kDate = 53288448;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &object, std::size_t offset,
           Value value) {
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
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x20> data{};
  std::array<std::byte, 0x20> physical{};
  std::array<std::byte, 0x10> game_state{};
  void *game_state_slot = game_state.data();
  std::uint32_t original_calls = 0;
  std::uint32_t selector_calls = 0;
  std::uint32_t memory_reads = 0;
  bool original_abi_matches = true;
  bool selector_abi_matches = true;

  Fixture() {
    Store(regiment, 0x10, kRegiment);
    Store(regiment, 0x14, std::uint32_t{0x41725267});
    Store(regiment, 0x20, static_cast<void *>(data.data()));
    Store(regiment, 0x28, std::int32_t{2});
    Store(regiment, 0x2C, std::int32_t{2});
    Store(regiment, 0x38, std::int32_t{100});
    Store(regiment, 0x3C, std::int32_t{120});
    for (const auto base : {std::size_t{0}, std::size_t{16}}) {
      Store(data, base + 0x08, kPersistent);
      Store(data, base + 0x0C, std::int32_t{2});
    }
    Store(physical, 0x00, std::int32_t{120});
    Store(physical, 0x04, std::int32_t{100});
    Store(physical, 0x08, kPersistent);
    // DATA's selector ordinal is independent of the chunk's own ordinal.
    Store(physical, 0x0C, std::int32_t{9});
    Store(physical, 0x10, kRegiment);
    Store(physical, 0x18, std::int32_t{1});
    Store(game_state, 0x08, kDate);
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
      InRange(address, size, fixture.regiment.data(), fixture.regiment.size()) ||
      InRange(address, size, fixture.data.data(), fixture.data.size()) ||
      InRange(address, size, fixture.physical.data(), fixture.physical.size()) ||
      InRange(address, size, fixture.game_state.data(), fixture.game_state.size()) ||
      InRange(address, size, &fixture.game_state_slot,
              sizeof(fixture.game_state_slot));
  if (!owned) return false;
  std::memcpy(output, address, size);
  return true;
}

void *__fastcall SelectPhysical(void *data) {
  auto &fixture = *active;
  ++fixture.selector_calls;
  const bool matches = data == fixture.data.data() ||
                       data == fixture.data.data() + 16;
  fixture.selector_abi_matches &= matches;
  return matches ? fixture.physical.data() : nullptr;
}

// Typed deterministic original target. The production entry wrapper, capture,
// owned journal and query serializer run unchanged; this is not the CK3 EXE.
void __fastcall Original(void *regiment, std::int64_t request_raw) {
  auto &fixture = *active;
  const auto call = fixture.original_calls++;
  fixture.original_abi_matches &= regiment == fixture.regiment.data() &&
      request_raw == (call == 0 ? 700000 : 0);
  Check(call < 3, "production wrapper invoked original more than once");
  if (call == 0) {
    Store(fixture.physical, 0x04, std::int32_t{93});
    Store(fixture.regiment, 0x38, std::int32_t{93});
  } else if (call == 2) {
    // A stale raised cache refresh has zero actual physical soldier debit.
    Store(fixture.regiment, 0x38, std::int32_t{93});
  }
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
                                     std::int32_t current_full_regiment_id) {
  game::ArmyStrengthSnapshot row{};
  row.available = true;
  row.army_id = public_army_id;
  row.native_carmy_id_observable = true;
  row.native_carmy_id = public_army_id + 1000;
  row.scope_role = game::ArmyStrengthScopeRole::player;
  row.regiment_count = 1;
  row.current_soldiers = Load<std::int32_t>(fixture.regiment, 0x38);
  row.maximum_soldiers = Load<std::int32_t>(fixture.regiment, 0x3C);
  game::ArmyRegimentStrengthSnapshot member{};
  member.army_regiment_id = current_full_regiment_id;
  member.current_soldiers = row.current_soldiers;
  member.maximum_soldiers = row.maximum_soldiers;
  member.composition_unavailable_reason = "fixture_type_not_observed";
  row.regiment_strengths = std::vector{member};
  return row;
}

void AssertCaptured(const game::ArmyActualLossWriterObservationsV1 &observed) {
  Check(observed.events.size() == 3 && observed.oldest_available_sequence == 1 &&
            observed.latest_sequence == 3 && observed.overwritten_events == 0 &&
            observed.unattributed_capture_failures == 0,
        "whole native journal did not retain exactly the three real wrapper calls");
  constexpr std::array<std::int32_t, 3> before{100, 93, 88};
  constexpr std::array<std::int32_t, 3> after{93, 93, 93};
  constexpr std::array<std::int64_t, 3> debit{7, 0, 0};
  for (std::size_t index = 0; index < observed.events.size(); ++index) {
    const auto &event = observed.events[index];
    Check(event.sequence == index + 1 && event.army_regiment_id == kRegiment &&
              event.request_raw == (index == 0 ? 700000 : 0) &&
              event.observed_date_raw == kDate && event.same_instance_after &&
              event.before_current_soldiers == before[index] &&
              event.after_current_soldiers == after[index] &&
              event.before_maximum_soldiers == 120 &&
              event.after_maximum_soldiers == 120 &&
              event.capture_failure_flags == 0,
          "entry-return observation changed native scalar identity or values");
    Check(event.native_data_record_count == 2 &&
              event.captured_data_record_count == 2 &&
              event.physical_slot_count == 1 && event.physical_capture_complete &&
              event.actual_physical_soldier_debit == debit[index],
          "physical aliases were double counted or cached movement became debit");
    Check(event.data_aliases[0].data_record_index == 0 &&
              event.data_aliases[1].data_record_index == 1 &&
              event.data_aliases[0].persistent_regiment_id == kPersistent &&
              event.data_aliases[1].persistent_regiment_id == kPersistent &&
              event.data_aliases[0].data_chunk_ordinal == 2 &&
              event.data_aliases[1].data_chunk_ordinal == 2 &&
              event.data_aliases[0].physical_slot_index == 0 &&
              event.data_aliases[1].physical_slot_index == 0 &&
              event.physical_slots[0].same_instance_after,
          "actual DATA alias-to-physical mapping was lost");
    Check(event.physical_slots[0].before.current_soldiers ==
              (index == 0 ? 100 : 93) &&
              event.physical_slots[0].after.current_soldiers == 93 &&
              event.physical_slots[0].before.maximum_soldiers == 120 &&
              event.physical_slots[0].after.maximum_soldiers == 120 &&
              event.physical_slots[0].before.state_raw == 1 &&
              event.physical_slots[0].after.state_raw == 1,
          "immediate physical before-after fields changed");
  }
}

std::string Whole(const std::array<game::ArmyStrengthSnapshot, 2> &rows) {
  std::string output =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"actual-loss-writer-whole-native-01\",\"ok\":true,"
      "\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) output += ',';
    // The production serializer itself joins its actual current full roster
    // IDs and appends the journal family. Never serialize a standalone DTO.
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
      "\"native_EXE_invoked\":false,\"wrapper_invocations\":3,"
      "\"original_invocations\":";
  output += std::to_string(fixture.original_calls);
  output +=
      ",\"original_exactly_once_per_wrapper\":true,"
      "\"full_id_membership_proven\":true,"
      "\"cached_change_and_physical_change_separate\":true,"
      "\"residual_flags_unresolved\":true,\"observed_date_raw\":";
  output += std::to_string(kDate);
  output += ",\"current_full_regiment_id\":";
  output += std::to_string(kRegiment);
  output += ",\"same_index_other_generation_id\":";
  output += std::to_string(kNextGeneration);
  output += ",\"persistent_regiment_id\":";
  output += std::to_string(kPersistent);
  output += ",\"residual_caller_return_rva\":44652776,"
            "\"residual_caller_kind\":\"residual_allocator\","
            "\"cached_current_deltas\":[-7,0,5],"
            "\"physical_soldier_debits\":[7,0,0]},\"whole\":";
  output += Whole(rows);
  output += '}';
  return output;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-out",
          "usage: xar_ck3_12004_actual_loss_writer_whole_test --wire-out <fresh-json>");
    Fixture fixture{};
    active = &fixture;
    native::ActualLossWriterJournalBindingsV1 bindings{};
    bindings.enabled = true;
    bindings.game_state_slot = &fixture.game_state_slot;
    bindings.select_physical_slot = SelectPhysical;
    bindings.read_context = &fixture;
    bindings.read_memory = ReadMemory;
    Check(native::InitializeActualLossWriterJournalFixture12004(bindings, Original),
          "production journal fixture initializer rejected typed callbacks");
    native::XarActualLossWriterHook12004V1(fixture.regiment.data(), 700000);
    Check(fixture.original_calls == 1, "first natural wrapper original count changed");
    native::XarActualLossWriterHook12004V1(fixture.regiment.data(), 0);
    Check(fixture.original_calls == 2, "zero natural wrapper original count changed");
    Store(fixture.regiment, 0x38, std::int32_t{88});
    native::XarActualLossWriterHook12004V1(fixture.regiment.data(), 0);
    Check(fixture.original_calls == 3 && fixture.original_abi_matches &&
              fixture.selector_abi_matches,
          "natural wrapper original ABI or exact count changed");
    const std::array matching{kRegiment};
    const std::array next_generation{kNextGeneration};
    const auto observed = native::ReadActualLossWriterObservations12004(matching);
    Check(observed.has_value(), "configured journal family is absent");
    AssertCaptured(*observed);
    const auto wrong = native::ReadActualLossWriterObservations12004(next_generation);
    Check(wrong && wrong->events.empty() && wrong->latest_sequence == 3 &&
              (kRegiment & 0xFFFFFF) == (kNextGeneration & 0xFFFFFF),
          "query matched a storage index instead of the whole generation ID");
    Check(native::ClassifyActualLossWriterCallerV1(0x24E35FF) ==
              game::ArmyActualLossWriterCallerV1::supply_preferred &&
              native::ClassifyActualLossWriterCallerV1(0x24E377C) ==
              game::ArmyActualLossWriterCallerV1::siege_or_raid_preferred &&
              native::ClassifyActualLossWriterCallerV1(0x2A958E8) ==
              game::ArmyActualLossWriterCallerV1::residual_allocator &&
              native::ClassifyActualLossWriterCallerV1(0x1234) ==
              game::ArmyActualLossWriterCallerV1::other_writer_caller,
          "held exact4 return sites changed; residual remains undivided");
    const std::array rows{
        CurrentRow(fixture, 11, Load<std::int32_t>(fixture.regiment, 0x10)),
        CurrentRow(fixture, 12, kNextGeneration),
    };
    const auto reads_before = fixture.memory_reads;
    const auto selectors_before = fixture.selector_calls;
    const auto packet = Packet(fixture, rows);
    Check(fixture.original_calls == 3 && fixture.memory_reads == reads_before &&
              fixture.selector_calls == selectors_before,
          "read-only query serializer resolved native memory or re-executed writer");
    const std::filesystem::path path = argv[2];
    Check(!std::filesystem::exists(path), "native whole wire output already exists");
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << packet << '\n';
    Check(static_cast<bool>(file), "native whole wire output write failed");
    active = nullptr;
    std::cout << "actual loss writer whole native fixture emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
