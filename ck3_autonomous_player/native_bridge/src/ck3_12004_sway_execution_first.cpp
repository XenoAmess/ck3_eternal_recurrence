// New actual4 profile case; reuse owned input memory, never call the old suite.
#define main SwayLegacyOwnedInputMainUnused
#include "ck3_12002_sway_completion_execution_install_test.cpp"
#undef main
#include "xar_bridge/ck3_12004_sway_execution.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"

namespace {
namespace actual4 = xar::ck3_12004;
std::size_t inherited_copies{};

template <class T> T Value(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
struct IdentifierView { const char *data; std::int32_t size; std::int32_t padding; };
std::int32_t *IdentifierId(void *table, std::int32_t *out, const void *input) {
  if (table != &names) return nullptr;
  const auto view = Value<IdentifierView>(input, 0);
  *out = -1;
  for (const auto &[id, name] : names) {
    if (name == std::string_view(view.data, static_cast<std::size_t>(view.size))) {
      *out = id;
      break;
    }
  }
  return out;
}
SwayExecutionScopeToken12002 *InheritedLookup(
    const void *environment, SwayExecutionScopeToken12002 *out, std::int32_t id) {
  *out = {};
  auto rows = Value<const std::byte *>(environment, 0);
  for (std::int32_t index = 0; index < Value<std::int32_t>(environment, 0x0C); ++index) {
    const auto row = rows + static_cast<std::size_t>(index) * 0x20;
    if (Value<std::int32_t>(row, 0) == id) {
      *out = Value<SwayExecutionScopeToken12002>(row, 8);
      return out;
    }
  }
  const auto script = Value<const void *>(environment, 0x3D0);
  if (script == nullptr) return out;
  rows = Value<const std::byte *>(script, 0x18);
  for (std::int32_t index = 0; index < Value<std::int32_t>(script, 0x24); ++index) {
    const auto row = rows + static_cast<std::size_t>(index) * 0x18;
    if (Value<std::int32_t>(row, 0) == id) {
      *out = Value<SwayExecutionScopeToken12002>(row, 8);
      ++inherited_copies;
      return out;
    }
  }
  return out;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one new connected FIRST output directory");
    Fixture f;
    const auto owned_core = f.bindings.core;
    f.bindings = actual4::BindSwayExecutionImage12004(base, actual4::kExecutableSha256);
    Check(f.bindings.enabled && f.bindings.read_core_snapshot == &actual4::ReadCoreSnapshot,
          "actual4 image profile precedes owned native operands");
    f.bindings.core = owned_core;
    f.bindings.get_global_command_key = &GlobalCommandKey;
    f.bindings.get_script_identifier_table = &IdentifierTable;
    f.bindings.resolve_script_identifier_name = &IdentifierName;
    f.bindings.lookup_script_identifier_id = &IdentifierId;
    f.bindings.lookup = &InheritedLookup;
    Put(f.core_state.data(), actual4::kGameStateDataOffset, f.game.data());
    // Native GameState stores0..4; the qualified reader projects public1..5.
    Put(f.core_state.data(), actual4::kGameStateSpeedOffset, std::int32_t{4});
    Put(f.game.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerEntriesOffset, f.player_entries.data());
    Put(f.game.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerCountOffset, std::int32_t{1});
    CoreSnapshotPrefix prefix{};
    Check(actual4::ReadCoreSnapshot(f.bindings.core, prefix) &&
          prefix.clock.speed == 5 && prefix.has_played_character &&
          prefix.played_character_alive &&
          static_cast<std::uint32_t>(prefix.played_character_id) == actor,
          "fixture raw4 projects public speed5 and the original living actor");
    Put(f.effect.data(), 0, base + actual4::kSwayExecutionVtableRvas12004[0]);
    Put(f.effect.data(), 0x60, base + actual4::kSwayExecutionTitleWrapperRva12004);
    Put(f.scalar.data(), 0, base + actual4::kSwayExecutionScalarRva12004);
    alignas(8) std::array<std::byte, 0x3D8> environment{};
    alignas(8) std::array<std::byte, 0x28> script{};
    alignas(8) std::array<std::byte, 3 * 0x18> rows{};
    Put(script.data(), 0x18, rows.data());
    Put(script.data(), 0x20, std::int32_t{3});
    Put(script.data(), 0x24, std::int32_t{3});
    Put(rows.data(), 0, std::int32_t{201});
    Put(rows.data(), 8, f.owner);
    Put(rows.data(), 0x18, std::int32_t{202});
    Put(rows.data(), 0x20, f.target_token);
    Put(rows.data(), 0x30, std::int32_t{203});
    Put(rows.data(), 0x38, f.scheme_token);
    Put(environment.data(), 0x3D0, script.data());
    Put(f.context.data(), 0x10, script.data());
    Put(f.context.data(), 0x18, environment.data());
    Check(f.Installed(), "existing installer wraps all three owned slots with current profile");
    *f.type_key = "sway_bad_message";
    *f.title_key = "sway_sway_failed_message";
    (*f.slots[0])(f.effect.data(), f.context.data());
    *f.type_key = "sway_good_message";
    *f.title_key = "sway_sway_success_message";
    (*f.slots[0])(f.effect.data(), f.context.data());
    Check(original_calls[0] == 2 && original_arguments_match && inherited_copies == 6,
          "two hidden branches copy inherited scopes and forward each original once");
    SwayExecutionQueryResult12002 result{};
    rows.fill(std::byte{});
    script.fill(std::byte{});
    Check(f.recorder.Query(Query(), result) && result.available && result.records.size() == 2 &&
          result.records[0].source.branch == SwayExecutionSourceBranch12002::hidden_phase_failure_source &&
          result.records[1].source.branch == SwayExecutionSourceBranch12002::hidden_phase_success_source &&
          result.records[1].source.scheme_id == scheme,
          "real copied recorder retains the full original instance after input release");
    const std::filesystem::path directory{argv[1]};
    std::ofstream packet(directory / "current-hidden-phase-command-result.json");
    packet << SerializeSwayCompletionExecutionCommandResultV1(
        result, 19, result.records.back().source.date_raw, "current-hidden-phase-first",
        actual4::kGameVersion, actual4::kExecutableSha256) << '\n';
    Check(packet.good(), "actual full current-build command result is emitted for registered consumer");
    Check(UninstallSwayCompletionExecution12002(f.installation), "existing owned slots restore");
    std::cout << "PASS current4 inherited hidden failure/success -> installed copied recorder -> full command result; fixture inputs, no Game/live credit\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
