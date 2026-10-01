#include "xar_bridge/ck3_12002_sway_completion_execution_install.hpp"

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
#include <windows.h>

namespace {
using namespace xar::ck3_12002;
constexpr std::uintptr_t base = 0x140000000;
constexpr std::uint32_t actor = 0x03000001;
constexpr std::uint32_t target = 0x04000002;
constexpr std::uint32_t scheme = 0x0200000B;
std::size_t checks{};
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
template <typename T> void Put(void *p, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
std::map<std::int32_t, std::string> names;
void *local_pointer{};
void *LocalPlayer(void *) { return local_pointer; }
void *IdentifierTable() { return &names; }
const std::string *GlobalCommandKey(std::int32_t identifier) {
  const auto found = names.find(identifier);
  return found == names.end() ? nullptr : &found->second;
}
const std::string *IdentifierName(void *table, std::int32_t identifier) {
  if (table != &names) return nullptr;
  const auto found = names.find(identifier);
  return found == names.end() ? nullptr : &found->second;
}

std::array<std::size_t, 3> original_calls{};
bool original_arguments_match = true;
bool copied_capture_precedes_original = false;
const void *expected_effect{};
const void *expected_context{};
SwayExecutionRecorder12002 *expected_recorder{};
SwayExecutionQuery12002 Query() { return {actor, target, scheme, 0}; }
void Original(std::size_t index, const void *effect, const void *context) {
  ++original_calls[index];
  original_arguments_match = original_arguments_match &&
      effect == expected_effect && context == expected_context;
  if (index == 0 && expected_recorder != nullptr) {
    SwayExecutionQueryResult12002 result;
    copied_capture_precedes_original = expected_recorder->Query(Query(), result) &&
        !result.records.empty();
  }
}
void Original0(const void *e, const void *c) { Original(0, e, c); }
void Original1(const void *e, const void *c) { Original(1, e, c); }
void Original2(const void *e, const void *c) { Original(2, e, c); }
const std::array<SwayCompletionNativeExecute12002, 3> originals{
    &Original0, &Original1, &Original2};

struct Fixture {
  std::array<std::byte, 0xA8> core_state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x23000);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void *, 1> player_entries{player_entry.data()};
  std::array<std::byte, 0x30> character_storage{};
  std::array<std::byte, 16 * 0x10> character_slots{};
  std::array<std::byte, 0x1D8> character{};
  void *core_pointer = core_state.data();
  void *jomini_pointer = jomini.data();
  void *storage_pointer = character_storage.data();
  alignas(8) std::array<std::byte, 0xC0> effect{};
  alignas(8) std::array<std::byte, 0x20> context{};
  alignas(8) std::array<std::byte, 0x10> environment{};
  alignas(8) std::array<std::byte, 3 * 0x20> rows{};
  alignas(8) std::array<std::byte, 0x40> type{};
  alignas(8) std::array<std::byte, 0x50> scalar{};
  SwayExecutionScopeToken12002 root{4, 0, 0, actor};
  SwayExecutionScopeToken12002 owner{4, 0, 0, actor};
  SwayExecutionScopeToken12002 target_token{4, 0, 0, target};
  SwayExecutionScopeToken12002 scheme_token{9, 0, 0, scheme};
  std::string *type_key{};
  std::string *title_key{};
  SwayExecutionBindings12002 bindings;
  SwayExecutionRecorder12002 recorder;
  SwayCompletionExecutionInstall12002 installation;
  void *page{};
  std::array<SwayCompletionNativeExecute12002 *, 3> slots{};

  Fixture() {
    static_assert(sizeof(std::string) == 0x20);
    page = VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    Check(page != nullptr, "fixture allocates its own pointer-slot page");
    auto *table = static_cast<SwayCompletionNativeExecute12002 *>(page);
    for (std::size_t index = 0; index < slots.size(); ++index) {
      slots[index] = table + index;
      *slots[index] = originals[index];
    }
    DWORD previous{};
    Check(VirtualProtect(page, 4096, PAGE_READONLY, &previous) != FALSE,
          "fixture slots use readonly memory like native rdata");
    names = {{101, "send_interface_message"}, {201, "owner"},
             {202, "target"}, {203, "scheme"}};
    local_pointer = local.data();
    Put(core_state.data(), 8, std::int32_t{53220000});
    Put(core_state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{0});
    Put(players.data(), 0x1F0, std::int32_t{0});
    Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, player_entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{0});
    Put(player_entry.data(), 0xB0, actor);
    Put(character_storage.data(), 0x20, character_slots.data());
    Put(character_storage.data(), 0x2C, std::int32_t{16});
    Put(character.data(), 0x18, actor);
    Put(character_slots.data(), 0x18, character.data());
    Put(effect.data(), 0, base + kSwayExecutionMessageVtableRva12002);
    Put(effect.data(), 8, std::int32_t{101});
    Put(effect.data(), 0x50, type.data());
    Put(effect.data(), 0x5C, std::uint8_t{2});
    Put(effect.data(), 0x60, base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(scalar.data(), 0, base + kSwayExecutionScalarLocalizationVtableRva12002);
    type_key = ::new (type.data() + 0x18) std::string("sway_good_message");
    title_key = ::new (scalar.data() + 0x30) std::string("sway_sway_success_message");
    Put(context.data(), 0, &root);
    Put(context.data(), 0x18, environment.data());
    Put(environment.data(), 0, rows.data());
    Put(environment.data(), 8, std::int32_t{3});
    Put(environment.data(), 0x0C, std::int32_t{3});
    Put(rows.data(), 0, std::int32_t{201});
    Put(rows.data(), 8, owner);
    Put(rows.data(), 0x20, std::int32_t{202});
    Put(rows.data(), 0x28, target_token);
    Put(rows.data(), 0x40, std::int32_t{203});
    Put(rows.data(), 0x48, scheme_token);
    bindings.enabled = true;
    bindings.image_base = base;
    bindings.core = {true, &core_pointer, &jomini_pointer,
                     &storage_pointer, &LocalPlayer};
    bindings.get_global_command_key = &GlobalCommandKey;
    bindings.get_script_identifier_table = &IdentifierTable;
    bindings.resolve_script_identifier_name = &IdentifierName;
    expected_effect = effect.data();
    expected_context = context.data();
    expected_recorder = &recorder;
  }
  ~Fixture() {
    (void)UninstallSwayCompletionExecution12002(installation);
    std::destroy_at(type_key);
    std::destroy_at(title_key);
    if (page != nullptr) (void)VirtualFree(page, 0, MEM_RELEASE);
  }
  bool Installed() {
    return InstallSwayCompletionExecutionFixture12002(
        bindings, slots, originals, recorder, installation);
  }
};

void Save(const std::filesystem::path &directory, const char *name,
          const SwayExecutionQueryResult12002 &result) {
  std::ofstream output(directory / name);
  output << SerializeSwayCompletionExecution12002(result) << '\n';
  Check(output.good(), "fixture query serializes the actual copied recorder");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "artifact directory provided");
    const std::filesystem::path output{argv[1]};
    Fixture f;
    SwayExecutionQueryResult12002 result;
    Check(!f.recorder.ObserverAttached(), "no attachment before actual install");
    Check(!InstallSwayCompletionExecution12002(base, "old-build", f.recorder,
                                              f.installation),
          "unsupported production build is rejected without fixture RVA substitution");
    Check(!f.recorder.ObserverAttached(), "failed production binding never grants availability");
    auto wrong_originals = originals;
    wrong_originals[1] = &Original0;
    Check(!InstallSwayCompletionExecutionFixture12002(
        f.bindings, f.slots, wrong_originals, f.recorder, f.installation),
        "native slot mismatch rejects the install before pointer mutation");
    Check(*f.slots[0] == originals[0] && *f.slots[1] == originals[1] &&
          *f.slots[2] == originals[2] && !f.recorder.ObserverAttached(),
          "all original slots and detached recorder survive failed install");
    Check(f.Installed() && f.installation.attached && f.installation.fixture_slots &&
          f.recorder.ObserverAttached(), "three actual fixture slots grant attachment together");
    Check(*f.slots[0] != originals[0] && *f.slots[1] != originals[1] &&
          *f.slots[2] != originals[2], "all three exact slots are wrapped");
    MEMORY_BASIC_INFORMATION memory{};
    Check(VirtualQuery(f.page, &memory, sizeof(memory)) == sizeof(memory) &&
          memory.Protect == PAGE_READONLY, "slot patch restores readonly page protection");
    (*f.slots[0])(f.effect.data(), f.context.data());
    Check(original_calls[0] == 1 && original_arguments_match &&
          copied_capture_precedes_original,
          "wrapper captures actual source then transparently calls typed original once");
    Check(f.recorder.Query(Query(), result) && result.records.size() == 1 &&
          result.records[0].source.scheme_id == scheme &&
          result.records[0].source.branch ==
              SwayExecutionSourceBranch12002::hidden_phase_success_source,
          "query observes the wrapper-produced full-ID joined source");
    Save(output, "installed-hidden-success-wire.json", result);
    names[101] = "send_interface_toast";
    Put(f.effect.data(), 0, base + kSwayExecutionToastVtableRva12002);
    (*f.slots[1])(f.effect.data(), f.context.data());
    names[101] = "send_interface_popup";
    Put(f.effect.data(), 0, base + kSwayExecutionPopupVtableRva12002);
    (*f.slots[2])(f.effect.data(), f.context.data());
    Check(original_calls[1] == 1 && original_calls[2] == 1 && original_arguments_match,
          "ignored toast/popup inputs still forward original exactly once");
    Check(f.recorder.Query(Query(), result) && result.records.size() == 1,
          "non-hidden inputs do not fabricate source records");
    names[101] = "send_interface_message";
    Put(f.effect.data(), 0, base + kSwayExecutionMessageVtableRva12002);
    *f.type_key = "sway_bad_message";
    *f.title_key = "sway_sway_failed_message";
    (*f.slots[0])(f.effect.data(), f.context.data());
    Check(original_calls[0] == 2 && f.recorder.Query(Query(), result) &&
          result.records.size() == 2 && result.records[1].source.branch ==
              SwayExecutionSourceBranch12002::hidden_phase_failure_source,
          "a second actual wrapped call records failure and forwards once");
    Save(output, "installed-hidden-failure-wire.json", result);
    Check(UninstallSwayCompletionExecution12002(f.installation) &&
          !f.installation.attached && !f.recorder.ObserverAttached(),
          "uninstall detaches availability and restores installed slots");
    Check(*f.slots[0] == originals[0] && *f.slots[1] == originals[1] &&
          *f.slots[2] == originals[2], "all three typed original pointers are restored");
    const auto before = original_calls;
    for (auto *slot : f.slots) (*slot)(f.effect.data(), f.context.data());
    Check(original_calls[0] == before[0] + 1 && original_calls[1] == before[1] + 1 &&
          original_calls[2] == before[2] + 1 && original_arguments_match,
          "restored slots execute originals once without wrapper capture");
    Check(!f.recorder.Query(Query(), result) && !result.available &&
          !result.observer_attached, "detached query cannot claim attached observations");
    Save(output, "restored-detached-wire.json", result);
    Check(UninstallSwayCompletionExecution12002(f.installation),
          "already-restored lifecycle stop is idempotent");
    Check(f.Installed() && f.recorder.ObserverAttached(), "same owned lifecycle can reinstall");
    Check(UninstallSwayCompletionExecution12002(f.installation), "reinstalled lifecycle restores");
    std::cout << "PASS " << checks << " checks; 3 readonly fixture pointer slots installed; "
                 "actual CaptureAndRecord before typed original exactly once; good/bad query; "
                 "ignored inputs forwarded; exact pointers and protection restored; no CK3 touched\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
