#include "xar_bridge/ck3_12002_sway_completion_termination.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
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
  ++checks; if (!condition) throw std::runtime_error(message);
}
template <typename T> void Put(void *p, std::size_t offset, const T &v) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &v, sizeof(v));
}
void *local_pointer{};
void *LocalPlayer(void *) { return local_pointer; }
struct TerminationFixture;
TerminationFixture *active_fixture{};
void OriginalCommand(const void *self);
void OriginalFalse(const void *self, const void *context);
void OriginalTrue(const void *self, const void *context);
enum class FixturePost { terminate, unchanged, purge, reuse };
struct TerminationFixture {
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
  void *character_storage_pointer = character_storage.data();
  std::array<std::byte, 0x30> scheme_storage{};
  std::array<std::byte, 16 * 0x10> scheme_slots{};
  std::array<std::byte, 0x358> instance{};
  std::array<std::byte, 0x40> type{};
  std::array<std::byte, 0x28> command{};
  std::array<std::byte, 0x20> false_effect{};
  std::array<std::byte, 0x20> true_effect{};
  std::array<std::byte, 0x20> context{};
  std::array<std::byte, 0x10> root{};
  SwayTerminationBindings12002 bindings;
  SwayTerminationRecorder12002 recorder;
  SwayTerminationInstall12002 installation;
  std::array<std::uintptr_t, 3> originals{
      reinterpret_cast<std::uintptr_t>(&OriginalCommand),
      reinterpret_cast<std::uintptr_t>(&OriginalFalse), reinterpret_cast<std::uintptr_t>(&OriginalTrue)};
  std::array<std::uintptr_t *, 3> slots{};
  std::array<std::size_t, 3> original_calls{};
  bool original_arguments_match = true;
  FixturePost post = FixturePost::terminate;
  std::uint32_t scheme_id = scheme;
  void *page{};
  TerminationFixture() {
    active_fixture = this; local_pointer = local.data();
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
    Put(game.data(), 0xA5C0, base + 0x4779538);
    Put(game.data(), 0xA5E0, scheme_storage.data());
    Put(scheme_storage.data(), 0, base + 0x4779828);
    Put(scheme_storage.data(), 0x20, scheme_slots.data());
    Put(scheme_storage.data(), 0x2C, std::int32_t{16});
    Put(instance.data(), 0, base + 0x47794E8);
    Put(instance.data(), 0x14, std::uint32_t{0x5363686D});
    Put(instance.data(), 0x20, type.data());
    Put(instance.data(), 0x30, std::uint32_t{0});
    Put(instance.data(), 0x34, target);
    Put(type.data(), 0, base + 0x48B9F20);
    std::memcpy(type.data() + 0x18, "sway", 4);
    Put(type.data(), 0x28, std::uint64_t{4});
    Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(command.data(), 0, base + 0x476ED30);
    Put(command.data(), 0x18, base + 0x476EB70);
    Put(false_effect.data(), 0, base + 0x48521B0);
    Put(true_effect.data(), 0, base + 0x4852B68);
    Put(context.data(), 0, root.data());
    Put(root.data(), 0, std::uint16_t{9});
    bindings = {true, base, {true, &core_pointer, &jomini_pointer,
                            &character_storage_pointer, &LocalPlayer}};
    page = VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    Check(page != nullptr, "fixture owns pointer-slot page");
    auto *p = static_cast<std::uintptr_t *>(page);
    for (std::size_t i = 0; i < slots.size(); ++i) { slots[i] = p + i; *slots[i] = originals[i]; }
    DWORD previous{};
    Check(VirtualProtect(page, 4096, PAGE_READONLY, &previous) != FALSE, "fixture native-like readonly slots");
    Reset();
  }
  ~TerminationFixture() {
    (void)UninstallSwayCompletionTermination12002(installation);
    if (page) (void)VirtualFree(page, 0, MEM_RELEASE);
    active_fixture = nullptr;
  }
  void Reset(std::uint32_t id = scheme) {
    scheme_id = id;
    Put(instance.data(), 0x10, id);
    Put(instance.data(), 0x28, std::int32_t{0});
    Put(instance.data(), 0x2C, actor);
    Put(scheme_slots.data(), (id & 0x00FFFFFFu) * 0x10 + 8, instance.data());
    Put(command.data(), 0x20, id);
    Put(root.data(), 8, std::uint64_t{id});
    post = FixturePost::terminate;
  }
  SwayTerminationQuery12002 Query(std::uint64_t after = 0) const { return {actor, target, scheme_id, after}; }
  bool Install() { return InstallSwayCompletionTerminationFixture12002(bindings, slots, originals, recorder, installation); }
  void RunSource(std::size_t index) {
    if (index == 0) reinterpret_cast<SwayTerminationNativeCommand12002>(*slots[0])(command.data() + 0x18);
    else reinterpret_cast<SwayTerminationNativeEffect12002>(*slots[index])(
        index == 1 ? false_effect.data() : true_effect.data(), context.data());
  }
  void Original(std::size_t index, const void *self, const void *ctx) {
    ++original_calls[index];
    original_arguments_match = original_arguments_match &&
        self == (index == 0 ? command.data() + 0x18 : index == 1 ? false_effect.data() : true_effect.data()) &&
        ctx == (index == 0 ? nullptr : context.data());
    if (post == FixturePost::terminate) {
      Put(instance.data(), 0x28, std::int32_t{1});
      Put(instance.data(), 0x2C, std::uint32_t{0xFFFFFFFFu});
      // Destroy the input token after execution: records must keep copied IDs.
      Put(root.data(), 8, std::uint64_t{0xFFFFFFFFu});
    } else if (post == FixturePost::purge) {
      Put(scheme_slots.data(), (scheme_id & 0x00FFFFFFu) * 0x10 + 8, static_cast<void *>(nullptr));
    } else if (post == FixturePost::reuse) {
      Put(instance.data(), 0x10, scheme_id + 0x01000000u);
      Put(instance.data(), 0x28, std::int32_t{1});
    }
  }
};
void OriginalCommand(const void *self) { active_fixture->Original(0, self, nullptr); }
void OriginalFalse(const void *self, const void *ctx) { active_fixture->Original(1, self, ctx); }
void OriginalTrue(const void *self, const void *ctx) { active_fixture->Original(2, self, ctx); }
void Save(const std::filesystem::path &output, const char *name, const SwayTerminationQueryResult12002 &result) {
  std::ofstream file(output / name); file << SerializeSwayCompletionTermination12002(result) << '\n';
  Check(file.good(), "actual copied query wire saved");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "artifact directory supplied");
    const std::filesystem::path output{argv[1]};
    TerminationFixture f;
    SwayTerminationQueryResult12002 r;
    Check(!InstallSwayCompletionTermination12002(base, "old-build", f.recorder, f.installation), "wrong build rejected");
    auto wrong = f.originals; wrong[1] = wrong[0];
    Check(!InstallSwayCompletionTerminationFixture12002(f.bindings, f.slots, wrong, f.recorder, f.installation), "slot mismatch rejected");
    Check(f.Install() && f.recorder.ObserverAttached(), "actual three-slot install attaches copied recorder");
    MEMORY_BASIC_INFORMATION memory{};
    Check(VirtualQuery(f.page, &memory, sizeof(memory)) == sizeof(memory) && memory.Protect == PAGE_READONLY,
          "native-like slot protection restored after install");
    f.RunSource(0);
    Check(f.recorder.Query(f.Query(), r) && r.records.size() == 1, "command Execute produces record");
    Check(r.records[0].source.source_class == SwayTerminationSourceClass12002::end_scheme_command_execute &&
          r.records[0].source.pre_owner == actor && r.records[0].source.post_owner == 0xFFFFFFFFu &&
          r.records[0].source.native_terminal_transition_observed, "command source and post status transition joined independently");
    Save(output, "command-terminal-wire.json", r);
    f.Reset(); f.post = FixturePost::unchanged; f.RunSource(1);
    Check(f.recorder.Query(f.Query(1), r) && r.records.size() == 1 &&
          r.records[0].source.executing_source_observed && r.records[0].source.post_status_observed &&
          r.records[0].source.post_status == 0 && !r.records[0].source.native_terminal_transition_observed,
          "real false effect source forwarding can leave state unchanged; no guessed terminal");
    Save(output, "false-unchanged-wire.json", r);
    f.Reset(); f.RunSource(1);
    Check(f.recorder.Query(f.Query(2), r) && r.records.size() == 1 &&
          r.records[0].source.source_class == SwayTerminationSourceClass12002::authored_end_scheme_false_execute &&
          r.records[0].source.input_root_scope_kind == 9 && r.records[0].source.scheme_id == scheme &&
          r.records[0].source.native_terminal_transition_observed, "false source copies full-ID token before original clears input");
    Save(output, "false-terminal-wire.json", r);
    f.Reset(); f.RunSource(2);
    Check(f.recorder.Query(f.Query(3), r) && r.records.size() == 1 &&
          r.records[0].source.source_class == SwayTerminationSourceClass12002::authored_end_scheme_true_execute &&
          r.records[0].source.native_terminal_transition_observed, "true effect source has independently observed terminal transition");
    Save(output, "true-terminal-wire.json", r);
    f.Reset(); f.post = FixturePost::purge; f.RunSource(2);
    Check(f.recorder.Query(f.Query(4), r) && r.records.size() == 1 && r.records[0].source.post_read_succeeded &&
          !r.records[0].source.post_instance_present && !r.records[0].source.native_terminal_state_observed,
          "source Execute plus missing post row never proves terminal state");
    Save(output, "purged-post-wire.json", r);
    f.Reset(); f.post = FixturePost::reuse; f.RunSource(2);
    Check(f.recorder.Query(f.Query(5), r) && r.records.size() == 1 && r.records[0].source.post_storage_slot_reused &&
          !r.records[0].source.native_terminal_transition_observed, "reused generation is not old SchemeID terminal");
    Save(output, "reused-post-wire.json", r);
    f.Reset(0x0000000B); f.RunSource(1);
    Check(f.recorder.Query(f.Query(), r) && r.records.size() == 1 && r.records[0].source.scheme_id == 0xB &&
          r.records[0].source.native_terminal_transition_observed, "generation zero remains a valid full SchemeID");
    Save(output, "generation-zero-wire.json", r);
    f.Reset(); f.post = FixturePost::unchanged;
    std::memcpy(f.type.data() + 0x18, "hunt", 4); f.RunSource(0);
    Check(f.recorder.Query(f.Query(7), r) && r.records.empty(), "non-Sway input ignored while original executes");
    std::memcpy(f.type.data() + 0x18, "sway", 4);
    Check(f.original_calls == std::array<std::size_t, 3>{2, 3, 3} && f.original_arguments_match,
          "typed originals receive unchanged used inputs exactly once per actual call");
    Check(UninstallSwayCompletionTermination12002(f.installation), "actual uninstall restores slots");
    for (std::size_t i = 0; i < f.slots.size(); ++i) Check(*f.slots[i] == f.originals[i], "exact original slot restored");
    Check(!f.recorder.Query(f.Query(), r) && !r.available, "detached recorder cannot claim attached observations");
    Save(output, "detached-wire.json", r);
    std::cout << "PASS " << checks << " checks; actual 3 readonly slot install; pre copied IDs; typed original once; "
                 "native post transition separate; unchanged/missing/reused/generation0; no CK3\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
