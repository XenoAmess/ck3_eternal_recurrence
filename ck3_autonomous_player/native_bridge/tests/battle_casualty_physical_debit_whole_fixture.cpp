#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12004_battle_casualty_observer.hpp"

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
constexpr std::int32_t kOtherGeneration = 0x04000001;
constexpr std::int32_t kPersistent = 0x05000001;
constexpr std::int32_t kArmy = 0x06000001;
constexpr std::int32_t kRequestedUnit = 0x07000002;
constexpr std::int32_t kWrongUnitGeneration = 0x08000002;
constexpr std::int32_t kFallbackUnit = 0x09000003;
constexpr std::int32_t kOwner = 0x0A000004;
constexpr std::int32_t kDate = 53288448;
constexpr std::int64_t kSoft = 250000;
constexpr std::int64_t kHard = 750000;
constexpr std::uintptr_t kImage = 0x140000000ULL;
constexpr std::string_view kExactSha =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &object, std::size_t offset, Value value) {
  Check(offset <= Size && sizeof(Value) <= Size - offset,
        "fixture store outside owned object");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <class Value, std::size_t Size>
Value Load(const std::array<std::byte, Size> &object, std::size_t offset) {
  Check(offset <= Size && sizeof(Value) <= Size - offset,
        "fixture load outside owned object");
  Value result{};
  std::memcpy(&result, object.data() + offset, sizeof(result));
  return result;
}
bool InRange(const void *address, std::size_t size, const void *base,
             std::size_t extent) noexcept {
  const auto first = reinterpret_cast<std::uintptr_t>(base);
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  return value >= first && value - first <= extent &&
         size <= extent - (value - first);
}

struct Fixture {
  std::array<std::byte, 0x150> regiment{};
  std::array<std::byte, 0x10> data{};
  std::array<std::byte, 0x20> physical{};
  std::array<std::byte, 0x130> army{};
  std::array<std::byte, 0x180> wrong_unit{};
  std::array<std::byte, 0x180> fallback_unit{};
  std::array<std::byte, 0x30> army_storage{};
  std::array<std::byte, 0x30> unit_storage{};
  std::array<std::byte, 0x30> army_rows{};
  std::array<std::byte, 0x30> unit_rows{};
  std::array<std::byte, 0x30> entry{};
  std::array<std::byte, 0x20> ledger{};
  std::array<std::byte, 0x20> side{};
  std::array<std::byte, 0x10> game_state{};
  void *game_state_slot = game_state.data();
  void *army_storage_slot = army_storage.data();
  void *army_fallback_slot = nullptr;
  void *unit_storage_slot = unit_storage.data();
  void *unit_fallback_slot = fallback_unit.data();
  std::uint32_t application_calls = 0;
  std::uint32_t writer_calls = 0;
  std::uint32_t memory_reads = 0;
  std::uint32_t selector_calls = 0;
  bool application_abi_matches = true;
  bool writer_abi_matches = true;
  bool selector_abi_matches = true;

  Fixture() {
    Store(regiment, 0x10, kRegiment);
    Store(regiment, 0x14, std::uint32_t{0x41725267});
    Store(regiment, 0x20, static_cast<void *>(data.data()));
    Store(regiment, 0x28, std::int32_t{1});
    Store(regiment, 0x2C, std::int32_t{1});
    Store(regiment, 0x38, std::int32_t{100});
    Store(regiment, 0x3C, std::int32_t{120});
    Store(regiment, 0x140, kArmy);
    Store(data, 0x08, kPersistent);
    Store(data, 0x0C, std::int32_t{2});
    Store(physical, 0x00, std::int32_t{120});
    Store(physical, 0x04, std::int32_t{100});
    Store(physical, 0x08, kPersistent);
    Store(physical, 0x0C, std::int32_t{9});
    Store(physical, 0x10, kRegiment);
    Store(physical, 0x18, std::int32_t{1});
    Store(army, 0x10, kArmy);
    Store(army, 0x124, kRequestedUnit);
    Store(wrong_unit, 0x10, kWrongUnitGeneration);
    Store(wrong_unit, 0x174, std::int32_t{123});
    Store(fallback_unit, 0x10, kFallbackUnit);
    Store(fallback_unit, 0x174, kOwner);
    Store(army_storage, 0x20, static_cast<void *>(army_rows.data()));
    Store(army_storage, 0x2C, std::uint32_t{3});
    Store(unit_storage, 0x20, static_cast<void *>(unit_rows.data()));
    Store(unit_storage, 0x2C, std::uint32_t{3});
    Store(army_rows, 16 + 8, static_cast<void *>(army.data()));
    Store(unit_rows, 32 + 8, static_cast<void *>(wrong_unit.data()));
    Store(entry, 0x08, kRegiment);
    Store(entry, 0x18, std::int64_t{10000000});
    Store(entry, 0x20, std::int64_t{500000});
    Store(ledger, 0x10, std::int64_t{500000});
    Store(game_state, 0x08, kDate);
  }
};
Fixture *active = nullptr;

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  ++f.memory_reads;
  const auto owns = [&](const auto &object) {
    return InRange(address, size, object.data(), object.size());
  };
  const bool owned = owns(f.regiment) || owns(f.data) || owns(f.physical) ||
      owns(f.army) || owns(f.wrong_unit) || owns(f.fallback_unit) ||
      owns(f.army_storage) || owns(f.unit_storage) || owns(f.army_rows) ||
      owns(f.unit_rows) || owns(f.entry) || owns(f.ledger) || owns(f.side) ||
      owns(f.game_state) ||
      InRange(address, size, &f.game_state_slot, sizeof(f.game_state_slot)) ||
      InRange(address, size, &f.army_storage_slot, sizeof(f.army_storage_slot)) ||
      InRange(address, size, &f.army_fallback_slot, sizeof(f.army_fallback_slot)) ||
      InRange(address, size, &f.unit_storage_slot, sizeof(f.unit_storage_slot)) ||
      InRange(address, size, &f.unit_fallback_slot, sizeof(f.unit_fallback_slot));
  if (!owned) return false;
  std::memcpy(output, address, size);
  return true;
}
void *__fastcall SelectPhysical(void *data) {
  auto &f = *active;
  ++f.selector_calls;
  f.selector_abi_matches &= data == f.data.data();
  return data == f.data.data() ? f.physical.data() : nullptr;
}
void __fastcall WriterOriginal(void *regiment, std::int64_t hard) {
  auto &f = *active;
  ++f.writer_calls;
  f.writer_abi_matches &= regiment == f.regiment.data() && hard == kHard;
  Check(f.writer_calls == 1, "nested writer original invoked more than once");
  Store(f.physical, 0x04, std::int32_t{93});
  // Raised cache movement is deliberately distinct from actual backing debit.
  Store(f.regiment, 0x38, std::int32_t{95});
}
void *__fastcall ApplicationOriginal(void *side, std::int64_t soft,
                                     std::int64_t hard, void *entry) {
  auto &f = *active;
  ++f.application_calls;
  f.application_abi_matches &= side == f.side.data() && entry == f.entry.data() &&
      soft == kSoft && hard == kHard;
  Check(f.application_calls == 1, "application original invoked more than once");
  Store(f.entry, 0x20, Load<std::int64_t>(f.entry, 0x20) + soft);
  Store(f.entry, 0x18, Load<std::int64_t>(f.entry, 0x18) - (soft + hard));
  native::XarActualLossWriterHook12004V1(f.regiment.data(), hard);
  Store(f.ledger, 0x10, Load<std::int64_t>(f.ledger, 0x10) + hard);
  return f.ledger.data();
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
game::ArmyStrengthSnapshot CurrentRow(const Fixture &f, std::int32_t army_id,
                                     std::int32_t current_full_regiment_id) {
  game::ArmyStrengthSnapshot row{};
  row.available = true;
  row.army_id = army_id;
  row.native_carmy_id_observable = true;
  row.native_carmy_id = army_id == 11 ? kArmy : 0x0B000002;
  row.scope_role = game::ArmyStrengthScopeRole::player;
  row.regiment_count = 1;
  row.current_soldiers = Load<std::int32_t>(f.regiment, 0x38);
  row.maximum_soldiers = Load<std::int32_t>(f.regiment, 0x3C);
  game::ArmyRegimentStrengthSnapshot member{};
  member.army_regiment_id = current_full_regiment_id;
  member.current_soldiers = row.current_soldiers;
  member.maximum_soldiers = row.maximum_soldiers;
  member.composition_unavailable_reason = "fixture_type_not_observed";
  row.regiment_strengths = std::vector{member};
  return row;
}

void AssertOwned(const Fixture &f,
                 const game::ArmyBattleCasualtyObservationsV1 &observed,
                 const game::ArmyActualLossWriterObservationsV1 &writers) {
  Check(!observed.observer_installed && observed.oldest_available_sequence == 1 &&
            observed.latest_sequence == 1 && observed.overwritten_events == 0 &&
            observed.events.size() == 1 && writers.events.size() == 1,
        "one completed application and nested writer were not retained");
  const auto &event = observed.events.front();
  const auto &writer = writers.events.front();
  Check(event.sequence == 1 && event.entry_identity ==
            reinterpret_cast<std::uintptr_t>(f.entry.data()) &&
            event.entry_army_regiment_id == kRegiment &&
            event.soft_request_raw == kSoft && event.hard_request_raw == kHard &&
            event.observed_date_raw == kDate &&
            event.before_fighting_raw == 10000000 &&
            event.before_soft_raw == 500000 &&
            event.after_fighting_raw == 9000000 &&
            event.after_soft_raw == 750000 && event.same_entry_after,
        "actual Entry identity, soft/hard or before-after values changed");
  Check(event.nested_writer_event_count == 1 && event.writer_sequence == 1 &&
            event.writer_sequence == writer.sequence &&
            event.writer_army_regiment_id == kRegiment &&
            event.writer_army_regiment_id == writer.army_regiment_id &&
            event.writer_request_raw == kHard && writer.request_raw == kHard &&
            event.entry_writer_association_proven &&
            event.physical_capture_complete &&
            event.actual_physical_soldier_debit == 7 &&
            event.actual_physical_soldier_debit ==
                writer.actual_physical_soldier_debit &&
            writer.before_current_soldiers == 100 &&
            writer.after_current_soldiers == 95 &&
            writer.physical_slots[0].before.current_soldiers == 100 &&
            writer.physical_slots[0].after.current_soldiers == 93,
        "nested exact association lost or Entry/cache/request became physical debit");
  Check(event.owner_army.reference_demanded &&
            event.owner_army.requested_full_id == kArmy &&
            event.owner_army.resolved_full_id == kArmy &&
            event.owner_army.used_fallback == false && event.owner_army.read_complete &&
            event.owner_unit.reference_demanded &&
            event.owner_unit.requested_full_id == kRequestedUnit &&
            event.owner_unit.resolved_full_id == kFallbackUnit &&
            event.owner_unit.used_fallback == true && event.owner_unit.read_complete &&
            event.owner_character_id == kOwner,
        "whole generation or actual Unit fallback owner resolution changed");
  Check(event.original_return_identity ==
            reinterpret_cast<std::uintptr_t>(f.ledger.data()) &&
            event.owner_hard_ledger_after_raw == 1250000,
        "actual original pointer return or hard-only ledger write changed");
}

std::string Packet(const Fixture &f,
                   const std::array<game::ArmyStrengthSnapshot, 2> &rows) {
  std::string output =
      "{\"schema_version\":1,\"fixture_receipt\":{"
      "\"original_target_kind\":\"typed_fixture_callback\","
      "\"native_EXE_invoked\":false,\"application_invocations\":1,"
      "\"application_original_invocations\":" + std::to_string(f.application_calls) +
      ",\"writer_original_invocations\":" + std::to_string(f.writer_calls) +
      ",\"original_exactly_once_per_wrapper\":true,"
      "\"actual_return_pointer_preserved\":true,"
      "\"entry_writer_full_id_association_proven\":true,"
      "\"full_id_membership_proven\":true,"
      "\"physical_entry_request_cache_distinct\":true,"
      "\"owner_unit_generation_fallback_observed\":true,"
      "\"owned_capture_survives_source_mutation\":true,"
      "\"observed_date_raw\":" + std::to_string(kDate) +
      ",\"current_full_regiment_id\":" + std::to_string(kRegiment) +
      ",\"same_index_other_generation_id\":" + std::to_string(kOtherGeneration) +
      ",\"persistent_regiment_id\":" + std::to_string(kPersistent) +
      ",\"owner_army_id\":" + std::to_string(kArmy) +
      ",\"requested_unit_id\":" + std::to_string(kRequestedUnit) +
      ",\"wrong_unit_generation_id\":" + std::to_string(kWrongUnitGeneration) +
      ",\"fallback_unit_id\":" + std::to_string(kFallbackUnit) +
      ",\"owner_character_id\":" + std::to_string(kOwner) +
      ",\"entry_identity\":" +
          std::to_string(reinterpret_cast<std::uintptr_t>(f.entry.data())) +
      ",\"original_return_identity\":" +
          std::to_string(reinterpret_cast<std::uintptr_t>(f.ledger.data())) +
      "},\"whole\":{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"battle-casualty-physical-debit-12004-whole\",\"ok\":true,"
      "\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) output += ',';
    // Production serializer joins both journals through the current whole IDs.
    game::AppendArmyStrengthV1(output, rows[index],
        [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  }
  output += "]}}}";
  return output;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-out",
          "usage: xar_ck3_12004_battle_casualty_physical_debit_whole --wire-out <fresh-json>");
    Fixture f{};
    active = &f;
    const auto factory = native::BindBattleCasualtyObserverImage12004(kImage, kExactSha);
    Check(factory.enabled && factory.image_base == kImage &&
              reinterpret_cast<std::uintptr_t>(factory.army_storage_slot) ==
                  kImage + 0x5D1DE48 &&
              reinterpret_cast<std::uintptr_t>(factory.unit_fallback_slot) ==
                  kImage + 0x5D1E378 &&
              !native::BindBattleCasualtyObserverImage12004(kImage, "wrong-sha").enabled,
          "held actual4 observer factory does not match the source-first ABI");
    native::ActualLossWriterJournalBindingsV1 writer{};
    writer.enabled = true;
    writer.game_state_slot = &f.game_state_slot;
    writer.select_physical_slot = SelectPhysical;
    writer.read_context = &f;
    writer.read_memory = ReadMemory;
    Check(native::InitializeActualLossWriterJournalFixture12004(writer, WriterOriginal),
          "existing writer journal rejected connected typed original");
    auto application = factory;
    application.image_base = 0;
    application.game_state_slot = &f.game_state_slot;
    application.army_storage_slot = &f.army_storage_slot;
    application.army_fallback_slot = &f.army_fallback_slot;
    application.unit_storage_slot = &f.unit_storage_slot;
    application.unit_fallback_slot = &f.unit_fallback_slot;
    application.read_context = &f;
    application.read_memory = ReadMemory;
    Check(native::InitializeBattleCasualtyObserverFixture12004(application,
                                                               ApplicationOriginal),
          "new application observer rejected connected typed original");
    const auto returned = native::XarBattleCasualtyApplicationHook12004(
        f.side.data(), kSoft, kHard, f.entry.data());
    Check(returned == f.ledger.data() && f.application_calls == 1 &&
              f.writer_calls == 1 && f.application_abi_matches &&
              f.writer_abi_matches && f.selector_abi_matches,
          "production wrappers changed actual arguments, original count or return");
    const std::array matching{kRegiment};
    const std::array other{kOtherGeneration};
    const auto observed = native::ReadBattleCasualtyObservations12004(matching);
    const auto writers = native::ReadActualLossWriterObservations12004(matching);
    Check(observed && writers, "configured owned observation family is absent");
    AssertOwned(f, *observed, *writers);
    const auto wrong = native::ReadBattleCasualtyObservations12004(other);
    Check(wrong && wrong->events.empty() && wrong->latest_sequence == 1 &&
              (kRegiment & 0xFFFFFF) == (kOtherGeneration & 0xFFFFFF),
          "current query joined an index without its generation");
    const std::array rows{
        CurrentRow(f, 11, Load<std::int32_t>(f.regiment, 0x10)),
        CurrentRow(f, 12, kOtherGeneration)};
    // Query must consume owned observations, never re-read these source lanes.
    Store(f.entry, 0x18, std::int64_t{-1});
    Store(f.ledger, 0x10, std::int64_t{-2});
    Store(f.fallback_unit, 0x174, std::int32_t{123});
    const auto reads = f.memory_reads;
    const auto selectors = f.selector_calls;
    const auto packet = Packet(f, rows);
    Check(f.memory_reads == reads && f.selector_calls == selectors &&
              f.application_calls == 1 && f.writer_calls == 1,
          "query serializer revisited native source or replayed mutating originals");
    const std::filesystem::path path = argv[2];
    Check(path.filename() == "battle-casualty-physical-debit-12004-whole.json" &&
              !std::filesystem::exists(path), "whole output path is not fresh/canonical");
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << packet << '\n';
    Check(static_cast<bool>(file), "whole native packet write failed");
    active = nullptr;
    std::cout << "battle casualty physical debit whole fixture emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
