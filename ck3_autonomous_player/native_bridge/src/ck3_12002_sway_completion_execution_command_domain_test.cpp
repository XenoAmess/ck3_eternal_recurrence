#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <new>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::uintptr_t image_base = 0x140000000;
constexpr std::uint32_t actor_id = 0x03000001;
constexpr std::uint32_t target_id = 0x04000002;
constexpr std::uint32_t scheme_id = 0x0100000B;
constexpr std::int32_t native_date = 53220000;
constexpr std::int32_t command_id = 101;
constexpr std::int32_t owner_id = 201;
constexpr std::int32_t target_name_id = 202;
constexpr std::int32_t scheme_name_id = 203;
constexpr std::int32_t type_id = 301;
static_assert(sizeof(std::string) == 0x20);
std::size_t checks = 0;
std::vector<std::int32_t> command_calls;
std::vector<std::int32_t> named_calls;
std::size_t table_calls = 0;
bool named_table_valid = true;
std::map<std::int32_t, std::string> command_names;
std::map<std::int32_t, std::string> named_names;
void *local_player = nullptr;

template <typename T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
void *LocalPlayer(void *) { return local_player; }
void *NamedTable() { ++table_calls; return &named_names; }
const std::string *GlobalCommand(std::int32_t id) {
  command_calls.push_back(id);
  const auto found = command_names.find(id);
  return found == command_names.end() ? nullptr : &found->second;
}
const std::string *NamedIdentifier(void *table, std::int32_t id) {
  named_calls.push_back(id);
  if (table != &named_names) { named_table_valid = false; return nullptr; }
  const auto found = named_names.find(id);
  return found == named_names.end() ? nullptr : &found->second;
}
SwayExecutionScopeToken12002 Token(std::uint16_t kind, std::uint32_t id) {
  return {kind, 0, 0x12345678u, (std::uint64_t{0xABCDEF12u} << 32) | id};
}

// Independent native-owned-memory fixture; no old fixture main is linked/run.
struct CommandDomainFixture {
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
  SwayExecutionScopeToken12002 root = Token(4, actor_id);
  std::string *type_key = nullptr;
  std::string *title_key = nullptr;
  SwayExecutionBindings12002 bindings{};
  CommandDomainFixture() {
    local_player = local.data();
    command_names = {{command_id, "send_interface_message"},
                     {owner_id, "wrong_global_owner"},
                     {type_id, "wrong_global_type"}};
    named_names = {{command_id, "wrong_named_command"}, {owner_id, "owner"},
                   {target_name_id, "target"}, {scheme_name_id, "scheme"},
                   {type_id, "sway_bad_message"}};
    Put(state.data(), 8, native_date);
    Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{0});
    Put(players.data(), 0x1F0, std::int32_t{0});
    Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, player_entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{0});
    Put(player_entry.data(), 0xB0, actor_id);
    Put(character_storage.data(), 0x20, character_slots.data());
    Put(character_storage.data(), 0x2C, std::int32_t{16});
    for (std::size_t i = 0; i < characters.size(); ++i) {
      Put(characters[i].data(), 0x18, i == 0 ? actor_id : target_id);
      Put(character_slots.data(), (i + 1) * 0x10 + 8, characters[i].data());
    }
    Put(effect.data(), 0, image_base + kSwayExecutionMessageVtableRva12002);
    Put(effect.data(), 8, command_id);
    Put(effect.data(), 0x0C, std::uint8_t{0});
    Put(effect.data(), 0x50, type.data());
    Put(effect.data(), 0x58, type_id);
    Put(effect.data(), 0x5C, std::uint8_t{2});
    Put(effect.data(), 0x60, image_base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(type.data(), 0x38, std::uint32_t{0x4744624Fu});
    Put(scalar.data(), 0, image_base + kSwayExecutionScalarLocalizationVtableRva12002);
    type_key = ::new (type.data() + 0x18) std::string("sway_good_message");
    title_key = ::new (scalar.data() + 0x30) std::string("sway_sway_success_message");
    Put(context.data(), 0, &root);
    Put(context.data(), 0x18, environment.data());
    Put(environment.data(), 0, rows.data());
    Put(environment.data(), 8, std::int32_t{3});
    Put(environment.data(), 0x0C, std::int32_t{3});
    Put(rows.data(), 0x00, owner_id);
    Put(rows.data(), 0x08, Token(4, actor_id));
    Put(rows.data(), 0x20, target_name_id);
    Put(rows.data(), 0x28, Token(4, target_id));
    Put(rows.data(), 0x40, scheme_name_id);
    Put(rows.data(), 0x48, Token(9, scheme_id));
    bindings.enabled = true;
    bindings.image_base = image_base;
    bindings.core = {true, &state_pointer, &jomini_pointer, &characters_pointer, &LocalPlayer};
    bindings.get_global_command_key = &GlobalCommand;
    bindings.get_script_identifier_table = &NamedTable;
    bindings.resolve_script_identifier_name = &NamedIdentifier;
  }
  ~CommandDomainFixture() {
    std::destroy_at(type_key);
    std::destroy_at(title_key);
  }
};

void SaveQuery(const std::filesystem::path &directory, const char *name,
               const SwayExecutionRecorder12002 &recorder, std::uint64_t after,
               std::size_t count, SwayExecutionSourceBranch12002 branch) {
  SwayExecutionQueryResult12002 result{};
  Check(recorder.Query({actor_id, target_id, scheme_id, after}, result) &&
        result.available && result.records.size() == count,
        "actual copied recorder query returns expected command-domain records");
  if (count != 0) {
    const auto &source = result.records.front().source;
    Check(source.actor_character_id == actor_id && source.target_character_id == target_id &&
          source.scheme_id == scheme_id && source.date_raw == native_date &&
          source.branch == branch,
          "copied source retains native full IDs/date and classified branch");
  }
  const auto wire = SerializeSwayCompletionExecutionCommandResultV1(
      result, 17, native_date, name);
  std::ofstream file(directory / name);
  file << wire << '\n';
  Check(file.good(), "actual full command_result formatter wire saved");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "command-domain artifact directory argument");
    const std::filesystem::path output{argv[1]};
    CommandDomainFixture f;
    SwayExecutionRecorder12002 recorder;
    recorder.SetObserverAttached(true); // fixture input; no installation claim.
    Check(CaptureAndRecordSwayCompletionExecution12002(
        f.bindings, f.effect.data(), f.context.data(), recorder) ==
        SwayExecutionCaptureResult12002::captured,
        "stock command global getter succeeds despite conflicting named ID key");
    Check(command_calls == std::vector<std::int32_t>{command_id} &&
          named_calls == std::vector<std::int32_t>{owner_id, target_name_id, scheme_name_id} &&
          named_table_valid,
          "command ID uses global ABI and named scopes retain the named registry ABI");
    SaveQuery(output, "global-good-command-result.json", recorder, 0, 1,
              SwayExecutionSourceBranch12002::hidden_phase_success_source);

    Put(f.effect.data(), 0x5C, std::uint8_t{1});
    *f.title_key = "sway_sway_failed_message";
    Check(CaptureAndRecordSwayCompletionExecution12002(
        f.bindings, f.effect.data(), f.context.data(), recorder) ==
        SwayExecutionCaptureResult12002::captured,
        "authored unresolved type still resolves in named domain, not global command domain");
    Check(command_calls == std::vector<std::int32_t>{command_id, command_id} &&
          named_calls == std::vector<std::int32_t>{owner_id, target_name_id, scheme_name_id,
                                                 type_id, owner_id, target_name_id, scheme_name_id},
          "both callback call traces match their distinct exact ID domains");
    SaveQuery(output, "named-type-bad-command-result.json", recorder, 1, 1,
              SwayExecutionSourceBranch12002::hidden_phase_failure_source);

    Put(f.effect.data(), 0x0C, std::uint8_t{1});
    const auto global_count = command_calls.size();
    const auto named_count = named_calls.size();
    const auto table_count = table_calls;
    SwayExecutionSource12002 unsupported{};
    Check(CaptureSwayCompletionExecution12002(f.bindings, f.effect.data(), f.context.data(),
        unsupported) == SwayExecutionCaptureResult12002::unavailable &&
        unsupported.unavailable_reason == "sway_execution_dynamic_command_identifier_unsupported" &&
        CaptureAndRecordSwayCompletionExecution12002(
            f.bindings, f.effect.data(), f.context.data(), recorder) !=
            SwayExecutionCaptureResult12002::captured &&
        command_calls.size() == global_count && named_calls.size() == named_count &&
        table_calls == table_count,
        "unsupported nonzero command domain never falls back to wrong command/named getter");
    Put(f.effect.data(), 0x0C, std::uint8_t{0});
    f.bindings.get_global_command_key = nullptr;
    Check(CaptureSwayCompletionExecution12002(f.bindings, f.effect.data(), f.context.data(),
        unsupported) == SwayExecutionCaptureResult12002::unavailable &&
        unsupported.unavailable_reason == "sway_execution_command_identifier_unavailable" &&
        named_calls.size() == named_count,
        "missing global getter never uses named fallback");
    f.bindings.get_global_command_key = &GlobalCommand;
    command_names[command_id] = "wrong_global_command";
    named_names[command_id] = "send_interface_message";
    Check(CaptureAndRecordSwayCompletionExecution12002(
        f.bindings, f.effect.data(), f.context.data(), recorder) ==
        SwayExecutionCaptureResult12002::ignored && named_calls.size() == named_count,
        "matching named key cannot make a different global command a stock source");
    SaveQuery(output, "unsupported-no-new-record-command-result.json", recorder, 2, 0,
              SwayExecutionSourceBranch12002::none);

    const auto bound = BindSwayExecutionImage12002(image_base, kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.get_global_command_key) ==
              image_base + 0x3F4F900 &&
          reinterpret_cast<std::uintptr_t>(bound.get_script_identifier_table) == image_base + 0x3F8A800 &&
          reinterpret_cast<std::uintptr_t>(bound.resolve_script_identifier_name) == image_base + 0x3F8A6F0,
          "production binder supplies exact independent global/named getter RVAs");
    std::cout << "PASS " << checks << " checks; distinct global command/named domains; "
                 "actual native memory capture -> copied recorder -> 3 full command_result wires; "
                 "nonzero unsupported and missing global getter never guess a domain; no CK3/live claim\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
