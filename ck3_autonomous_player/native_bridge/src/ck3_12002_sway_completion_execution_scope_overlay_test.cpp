// Reuse owned native/core input memory; never execute the prior domain suite.
#define main SwayExecutionCommandDomainFixtureMainUnused
#include "ck3_12002_sway_completion_execution_command_domain_test.cpp"
#undef main

namespace {
std::vector<std::int32_t> lookup_calls;
std::size_t inherited_rows_copied = 0;
bool lookup_environment_matches = true;
const void *expected_environment = nullptr;

template <typename T> T Value(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
SwayExecutionScopeToken12002 *NativeOverlayLookup(
    const void *environment, SwayExecutionScopeToken12002 *out, std::int32_t identifier) {
  lookup_calls.push_back(identifier);
  lookup_environment_matches = lookup_environment_matches && environment == expected_environment;
  *out = {};
  const auto *rows = Value<const std::byte *>(environment, 0);
  const auto count = Value<std::int32_t>(environment, 0x0C);
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *row = rows + static_cast<std::size_t>(i) * 0x20;
    if (Value<std::int32_t>(row, 0) == identifier) {
      *out = Value<SwayExecutionScopeToken12002>(row, 8);
      return out;
    }
  }
  const auto *script_data = Value<const void *>(environment, 0x3D0);
  if (script_data == nullptr) return out;
  rows = Value<const std::byte *>(script_data, 0x18);
  const auto inherited_count = Value<std::int32_t>(script_data, 0x24);
  for (std::int32_t i = 0; i < inherited_count; ++i) {
    const auto *row = rows + static_cast<std::size_t>(i) * 0x18;
    if (Value<std::int32_t>(row, 0) == identifier) {
      *out = Value<SwayExecutionScopeToken12002>(row, 8);
      ++inherited_rows_copied;
      return out;
    }
  }
  return out;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "scope-overlay artifact directory argument");
    const std::filesystem::path output{argv[1]};
    CommandDomainFixture f;
    alignas(8) std::array<std::byte, 0x3D8> environment{};
    alignas(8) std::array<std::byte, 0x28> script_data{};
    alignas(8) std::array<std::byte, 3 * 0x18> inherited_rows{};
    const auto owner_token = Token(4, actor_id);
    const auto target_token = Token(4, target_id);
    const auto scheme_token = Token(9, scheme_id);
    Put(script_data.data(), 0, f.root);
    Put(script_data.data(), 0x18, inherited_rows.data());
    Put(script_data.data(), 0x20, std::int32_t{3});
    Put(script_data.data(), 0x24, std::int32_t{3});
    Put(inherited_rows.data(), 0x00, owner_id);
    Put(inherited_rows.data(), 0x08, owner_token);
    Put(inherited_rows.data(), 0x18, target_name_id);
    Put(inherited_rows.data(), 0x20, target_token);
    Put(inherited_rows.data(), 0x30, scheme_name_id);
    Put(inherited_rows.data(), 0x38, scheme_token);
    Put(environment.data(), 0x3D0, script_data.data());
    Put(f.context.data(), 0x10, script_data.data());
    Put(f.context.data(), 0x18, environment.data());
    expected_environment = environment.data();
    f.bindings.lookup = &NativeOverlayLookup;
    f.bindings.scheme_identifier = &scheme_name_id;
    f.bindings.owner_identifier = &owner_id;
    f.bindings.target_identifier = &target_name_id;
    Check(Value<std::int32_t>(environment.data(), 0x0C) == 0 &&
          Value<void *>(environment.data(), 0) == nullptr &&
          Value<void *>(f.context.data(), 0x10) == Value<void *>(environment.data(), 0x3D0),
          "native caller-shaped input has empty Env32 and inherited ScriptScopeData24");
    SwayExecutionRecorder12002 recorder;
    recorder.SetObserverAttached(true); // fixture input; no native installation claim.
    Check(CaptureAndRecordSwayCompletionExecution12002(
        f.bindings, f.effect.data(), f.context.data(), recorder) ==
        SwayExecutionCaptureResult12002::captured,
        "production Capture publishes hidden phase with inherited scopes absent from Env32");
    Check(lookup_environment_matches && lookup_calls ==
              std::vector<std::int32_t>{scheme_name_id, owner_id, target_name_id} &&
          inherited_rows_copied == 3 && named_calls.empty(),
          "typed native overlay callback receives native environment/identifier globals and copies all inherited scopes");
    inherited_rows.fill(std::byte{});
    script_data.fill(std::byte{});
    SwayExecutionQueryResult12002 result{};
    Check(recorder.Query({actor_id, target_id, scheme_id, 0}, result) &&
          result.available && result.records.size() == 1 &&
          result.records[0].source.owner == owner_token &&
          result.records[0].source.target == target_token &&
          result.records[0].source.scheme == scheme_token &&
          result.records[0].source.date_raw == native_date,
          "copied query retains all 16 token bytes after inherited scope storage is cleared");
    const auto wire = SerializeSwayCompletionExecutionCommandResultV1(
        result, 18, native_date, "execution-inherited-scope-overlay");
    std::ofstream file(output / "inherited-scope-command-result.json");
    file << wire << '\n';
    Check(file.good(), "actual full command_result formatter emits inherited-scope capture");
    const auto bound = BindSwayExecutionImage12002(image_base, kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.lookup) == image_base + 0x373B540 &&
          reinterpret_cast<std::uintptr_t>(bound.scheme_identifier) == image_base + 0x5D4BD60 &&
          reinterpret_cast<std::uintptr_t>(bound.owner_identifier) == image_base + 0x5D4BD5C &&
          reinterpret_cast<std::uintptr_t>(bound.target_identifier) == image_base + 0x5D4BD58,
          "production BindImage supplies exact typed native overlay and scope identifier globals");
    std::cout << "PASS " << checks << " checks; one empty Env32 + inherited ScriptScopeData24 "
                 "actual Capture -> copied Recorder.Query -> full command_result; "
                 "all scopes copied through typed native overlay getter; no CK3/live claim\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
