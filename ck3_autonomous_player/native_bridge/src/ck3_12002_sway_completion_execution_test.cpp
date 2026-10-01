#include "xar_bridge/ck3_12002_sway_completion_execution.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::uintptr_t image_base = 0x140000000;
constexpr std::uint32_t actor_id = 0x03000001;
constexpr std::uint32_t target_id = 0x04000002;
constexpr std::uint32_t scheme_id = 0x0100000B;
constexpr std::int32_t date_raw = 53220000;
constexpr std::int32_t command_key = 101;
constexpr std::int32_t owner_key = 201;
constexpr std::int32_t target_key = 202;
constexpr std::int32_t scheme_key = 203;
constexpr std::int32_t type_key = 301;
static_assert(sizeof(std::string) == 0x20,
              "Fixture strings must use the game's release MSVC string layout");

std::size_t checks = 0;
template <typename T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
void *local_player = nullptr;
std::map<std::int32_t, std::string> names;
bool identifier_callback_abi_valid = true;
std::size_t identifier_calls = 0;
void *LocalPlayer(void *) { return local_player; }
void *IdentifierTable() { return &names; }
const std::string *IdentifierName(void *table, std::int32_t key) {
  ++identifier_calls;
  if (table != &names) {
    identifier_callback_abi_valid = false;
    return nullptr;
  }
  const auto found = names.find(key);
  return found == names.end() ? nullptr : &found->second;
}
SwayExecutionScopeToken12002 Token(std::uint16_t type, std::uint32_t id,
                                  std::uint16_t subtype) {
  return {type, subtype, 0x12345678u,
          (std::uint64_t{0xABCDEF12u} << 32) | id};
}

// Every address below belongs to this process's ordinary fixture allocation.
// The production reader decodes the exact Execute input and native core roots.
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x23000);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void *, 1> player_entries{player_entry.data()};
  std::array<std::byte, 0x30> character_storage{};
  std::array<std::byte, 16 * 0x10> character_slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *characters_pointer = character_storage.data();
  alignas(8) std::array<std::byte, 0xC0> effect{};
  alignas(8) std::array<std::byte, 0x20> context{};
  alignas(8) std::array<std::byte, 0x10> environment{};
  alignas(8) std::array<std::byte, 3 * 0x20> rows{};
  alignas(8) std::array<std::byte, 0x40> type{};
  alignas(8) std::array<std::byte, 0x50> scalar{};
  SwayExecutionScopeToken12002 root = Token(4, actor_id, 0x10);
  SwayExecutionScopeToken12002 owner = Token(4, actor_id, 0x20);
  SwayExecutionScopeToken12002 target = Token(4, target_id, 0x30);
  SwayExecutionScopeToken12002 scheme = Token(9, scheme_id, 0x40);
  std::string *type_name = nullptr;
  std::string *title_name = nullptr;
  SwayExecutionBindings12002 bindings{};

  Fixture() {
    local_player = local.data();
    names = {{command_key, "send_interface_message"}, {owner_key, "owner"},
             {target_key, "target"}, {scheme_key, "scheme"},
             {type_key, "sway_good_message"}};
    Put(state.data(), 8, date_raw);
    Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{0}); // Natural execution is unpaused.
    Put(players.data(), 0x1F0, std::int32_t{0});
    Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, player_entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{0});
    Put(player_entry.data(), 0xB0, actor_id);
    Put(character_storage.data(), 0x20, character_slots.data());
    Put(character_storage.data(), 0x2C, std::int32_t{16});
    for (std::size_t index = 0; index < characters.size(); ++index) {
      const auto id = index == 0 ? actor_id : target_id;
      Put(characters[index].data(), 0x18, id);
      Put(character_slots.data(), (index + 1) * 0x10 + 8, characters[index].data());
    }
    Put(effect.data(), 0, image_base + kSwayExecutionMessageVtableRva12002);
    Put(effect.data(), 8, command_key);
    Put(effect.data(), 0x50, type.data());
    Put(effect.data(), 0x58, type_key);
    Put(effect.data(), 0x5C, std::uint8_t{2});
    Put(effect.data(), 0x60, image_base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(type.data(), 0x38, std::uint32_t{0x4744624Fu});
    Put(scalar.data(), 0, image_base + kSwayExecutionScalarLocalizationVtableRva12002);
    type_name = ::new (type.data() + 0x18) std::string("sway_good_message");
    title_name = ::new (scalar.data() + 0x30) std::string("sway_sway_success_message");
    Put(context.data(), 0, &root);
    Put(context.data(), 0x18, environment.data());
    Put(environment.data(), 0, rows.data());
    Put(environment.data(), 8, std::int32_t{3});
    Put(environment.data(), 0x0C, std::int32_t{3});
    UpdateRows();
    bindings.enabled = true;
    bindings.image_base = image_base;
    bindings.core = {true, &state_pointer, &jomini_pointer,
                     &characters_pointer, &LocalPlayer};
    bindings.get_script_identifier_table = &IdentifierTable;
    bindings.resolve_script_identifier_name = &IdentifierName;
  }
  ~Fixture() {
    std::destroy_at(type_name);
    std::destroy_at(title_name);
  }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;
  void UpdateRows() {
    Put(rows.data(), 0x00, owner_key);
    Put(rows.data(), 0x08, owner);
    Put(rows.data(), 0x20, target_key);
    Put(rows.data(), 0x28, target);
    Put(rows.data(), 0x40, scheme_key);
    Put(rows.data(), 0x48, scheme);
  }
  void Good() {
    *type_name = "sway_good_message";
    *title_name = "sway_sway_success_message";
    names[type_key] = "sway_good_message";
  }
  void Bad() {
    *type_name = "sway_bad_message";
    *title_name = "sway_sway_failed_message";
    names[type_key] = "sway_bad_message";
  }
  SwayExecutionCaptureResult12002 Capture(SwayExecutionSource12002 &out) const {
    return CaptureSwayCompletionExecution12002(bindings, effect.data(), context.data(), out);
  }
  SwayExecutionCaptureResult12002 Record(SwayExecutionRecorder12002 &recorder) const {
    return CaptureAndRecordSwayCompletionExecution12002(
        bindings, effect.data(), context.data(), recorder);
  }
};

SwayExecutionQuery12002 Request(std::uint64_t after = 0) {
  return {actor_id, target_id, scheme_id, after};
}
void Save(const std::filesystem::path &directory, const char *name,
          const SwayExecutionQueryResult12002 &result) {
  const auto wire = SerializeSwayCompletionExecution12002(result);
  Check(!wire.empty(), "production source-history serializer emits wire");
  std::ofstream output(directory / name);
  output << wire << '\n';
  Check(output.good(), "wire saved to fixture artifact directory");
}
void NoCapture(Fixture &fixture, SwayExecutionRecorder12002 &recorder,
               const char *message) {
  SwayExecutionQueryResult12002 before{}, after{};
  Check(recorder.Query(Request(), before), "recorder before negative capture");
  Check(fixture.Record(recorder) != SwayExecutionCaptureResult12002::captured, message);
  Check(recorder.Query(Request(), after) && after.latest_sequence == before.latest_sequence &&
        after.records.size() == before.records.size(), "uncorrelated Execute does not append");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "fixture artifact directory argument");
    const std::filesystem::path output{argv[1]};
    Fixture fixture;
    SwayExecutionRecorder12002 recorder;
    SwayExecutionQueryResult12002 result{};
    SwayExecutionSource12002 source{};
    Check(!recorder.ObserverAttached() && !recorder.Query(Request(), result) &&
          !result.available && !result.observer_attached && result.records.empty(),
          "constructed recorder is unavailable before root confirms actual attachment");
    Save(output, "not-attached-wire.json", result);
    Check(fixture.Capture(source) == SwayExecutionCaptureResult12002::captured &&
          source.branch == SwayExecutionSourceBranch12002::hidden_phase_success_source &&
          source.actor_character_id == actor_id && source.target_character_id == target_id &&
          source.scheme_id == scheme_id && source.date_raw == date_raw &&
          source.root == fixture.root && source.owner == fixture.owner &&
          source.target == fixture.target && source.scheme == fixture.scheme,
          "actual Execute capture decodes resolved type and copies all four complete tokens");
    Check(!recorder.Append(source) &&
          fixture.Record(recorder) != SwayExecutionCaptureResult12002::captured,
          "capture cannot publish history from an unattached recorder");
    recorder.SetObserverAttached(true);
    Check(recorder.ObserverAttached() && fixture.Record(recorder) ==
          SwayExecutionCaptureResult12002::captured,
          "root attachment permits real unpaused hidden success Execute recording");
    Check(recorder.Query(Request(), result) && result.available && result.observer_attached &&
          result.records.size() == 1 && result.records[0].sequence == 1 &&
          result.records[0].source == source,
          "actual recorder query exposes the exact copied source");
    Save(output, "hidden-good-resolved-wire.json", result);

    const auto copied = result.records.front();
    fixture.target.payload = (std::uint64_t{0xDEADBEEFu} << 32) | 0x05000002u;
    fixture.scheme.payload = (std::uint64_t{0x87654321u} << 32) | 0x0200000Bu;
    fixture.UpdateRows();
    *fixture.title_name = "fixture_mutated_after_callback";
    Check(recorder.Query(Request(), result) && result.records.size() == 1 &&
          result.records.front().source == copied.source,
          "changing native environment and localization after capture does not change owned record");
    fixture.target = copied.source.target;
    fixture.scheme = copied.source.scheme;
    fixture.UpdateRows();
    fixture.Bad();
    Put(fixture.effect.data(), 0x5C, std::uint8_t{1});
    Put(fixture.effect.data(), 0x50, static_cast<void *>(nullptr));
    Check(fixture.Record(recorder) == SwayExecutionCaptureResult12002::captured &&
          recorder.Query(Request(), result) && result.records.size() == 2 &&
          result.records[1].source.branch == SwayExecutionSourceBranch12002::hidden_phase_failure_source,
          "unresolved stage-one type uses typed native identifier-to-MSVC-string callback");
    Check(identifier_callback_abi_valid && identifier_calls > 0,
          "actual identifier callback receives native table and returns real MSVC strings");
    Save(output, "hidden-bad-unresolved-wire.json", result);
    Check(recorder.Query(Request(1), result) && result.records.size() == 1 &&
          result.records[0].sequence == 2,
          "after_sequence excludes the previously consumed source record");
    Save(output, "sequence-filter-wire.json", result);
    auto wrong = Request();
    wrong.scheme_id = 0x0200000Bu;
    Check(recorder.Query(wrong, result) && result.available && result.records.empty(),
          "same scheme index with another full generation never matches source history");
    Save(output, "wrong-generation-wire.json", result);
    wrong = Request(); wrong.target_character_id = 0x05000002u;
    Check(recorder.Query(wrong, result) && result.records.empty(),
          "another target generation never matches source history");

    fixture.Good();
    Put(fixture.effect.data(), 0x50, fixture.type.data());
    Put(fixture.effect.data(), 0x5C, std::uint8_t{2});
    fixture.root.payload = (fixture.root.payload & 0xFFFFFFFF00000000ULL) | target_id;
    NoCapture(fixture, recorder, "root must equal current full actor ID");
    fixture.root = copied.source.root;
    fixture.owner.payload = (fixture.owner.payload & 0xFFFFFFFF00000000ULL) | 0x04000001u;
    fixture.UpdateRows();
    NoCapture(fixture, recorder, "owner with same index but different full generation is rejected");
    fixture.owner = copied.source.owner; fixture.UpdateRows();
    Put(fixture.environment.data(), 0x0C, std::int32_t{2});
    NoCapture(fixture, recorder, "missing named scheme scope cannot become an available record");
    Put(fixture.environment.data(), 0x0C, std::int32_t{3});
    fixture.scheme.type = 4; fixture.UpdateRows();
    NoCapture(fixture, recorder, "named scheme must carry native type nine");
    fixture.scheme = copied.source.scheme; fixture.UpdateRows();
    *fixture.type_name = "sway_good_message_extra";
    NoCapture(fixture, recorder, "near-prefix message type does not match exact stock tuple");
    fixture.Good();
    *fixture.title_name = "sway_sway_success_message_extra";
    NoCapture(fixture, recorder, "near-prefix authored scalar title does not match exact stock tuple");
    fixture.Good();
    *fixture.type_name = "sway_bad_message";
    NoCapture(fixture, recorder, "message type and authored title must match the same hidden branch");
    fixture.Good(); names[command_key] = "send_interface_message_extra";
    NoCapture(fixture, recorder, "near-prefix native command is not a stock hidden source");
    names[command_key] = "send_interface_message";
    Put(fixture.effect.data(), 0x60, image_base + kSwayExecutionTitleWrapperVtableRva12002 + 8);
    NoCapture(fixture, recorder, "authored title wrapper requires exact new-build vtable");
    Put(fixture.effect.data(), 0x60, image_base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(fixture.type.data(), 0x38, std::uint32_t{0});
    NoCapture(fixture, recorder, "resolved type definition requires native marker");
    Put(fixture.type.data(), 0x38, std::uint32_t{0x4744624Fu});
    fixture.bindings.enabled = false;
    NoCapture(fixture, recorder, "disabled exact-build source bindings are unavailable");
    fixture.bindings.enabled = true;

    SwayExecutionRecorder12002 bounded;
    bounded.SetObserverAttached(true);
    for (std::size_t index = 0; index < kSwayExecutionRecordCapacity12002 + 2; ++index) {
      if ((index & 1) == 0) fixture.Good(); else fixture.Bad();
      Check(fixture.Record(bounded) == SwayExecutionCaptureResult12002::captured,
            "bounded recorder appends actual production captures");
    }
    Check(bounded.Query(Request(1), result) && result.available && result.retention_gap &&
          result.earliest_sequence == 3 && result.latest_sequence == 130 &&
          result.records.size() == kSwayExecutionRecordCapacity12002 &&
          result.records.front().sequence == 3 && result.records.back().sequence == 130,
          "128 copied records retain ordered newest entries and publish overwritten sequence gap");
    Save(output, "bounded-retention-gap-wire.json", result);
    Check(bounded.Query(Request(2), result) && !result.retention_gap &&
          result.records.size() == kSwayExecutionRecordCapacity12002,
          "query at retained predecessor has no missing sequence gap");
    Check(bounded.Query(Request(129), result) && !result.retention_gap &&
          result.records.size() == 1 && result.records.front().sequence == 130,
          "sequence filtering works after ring wrap");
    Save(output, "bounded-latest-wire.json", result);
    bounded.SetObserverAttached(false);
    Check(!bounded.Query(Request(), result) && !result.available && !result.observer_attached,
          "detached observer cannot advertise available records");
    Save(output, "detached-wire.json", result);

    const auto bound = BindSwayExecutionImage12002(image_base, kExecutableSha256);
    Check(bound.enabled && bound.core.enabled &&
          reinterpret_cast<std::uintptr_t>(bound.get_script_identifier_table) == image_base + 0x3F8A800 &&
          reinterpret_cast<std::uintptr_t>(bound.resolve_script_identifier_name) == image_base + 0x3F8A6F0 &&
          !BindSwayExecutionImage12002(image_base, "old-game-build").enabled,
          "production Execute-source binder uses exact executable and typed name resolver RVAs");
    std::cout << "PASS " << checks << " checks; actual Execute capture + attached copied recorder + "
                 "query/serializer; resolved/unresolved hidden good/bad + full generation + "
                 "negative tuples + bounded retention; material/terminal remain independent\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
