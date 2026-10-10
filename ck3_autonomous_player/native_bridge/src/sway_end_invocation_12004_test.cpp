#include "xar_bridge/sway_end_invocation_12004.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <windows.h>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t image_base = 0x140000000;
constexpr std::uint32_t actor = 0x03000001;
constexpr std::uint32_t target = 0x04000002;
constexpr std::uint32_t scheme = 0x0200000B;
std::size_t checks{};
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
template <class T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void *local_player{};
void *LocalPlayer(void *) { return local_player; }
enum class Post { terminal, unchanged, purge, reuse, other_target, throw_original };
struct Fixture;
Fixture *active{};
void CommandOriginal(const void *self);
void FalseOriginal(const void *self, const void *context);
void TrueOriginal(const void *self, const void *context);

// One new actual4 owned-memory case. It never invokes an old native suite,
// shared slot installer, recorder, Game or the sealed phase FIRST path.
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
  SwayEndInvocationBindings12004 bindings{};
  std::array<std::size_t, 3> calls{};
  bool arguments_match = true;
  std::uint32_t full_id = scheme;
  std::uint64_t next_invocation = 1;
  Post post = Post::terminal;

  Fixture() {
    active = this;
    local_player = local.data();
    bindings = BindSwayEndInvocationImage12004(image_base, kExecutableSha256);
    Check(bindings.enabled && bindings.state.manager_vtable_rva == 0x4779548 &&
          bindings.state.storage_vtable_rva == 0x4779838 &&
          bindings.state.instance_vtable_rva == 0x47794F8 &&
          bindings.state.type_vtable_rva == 0x48B9F30,
          "actual4 state binder is the only native profile source");
    bindings.state.core = {true, &core_pointer, &jomini_pointer,
                           &character_storage_pointer, &LocalPlayer};
    Put(core_state.data(), kGameStateDataOffset, game.data());
    Put(core_state.data(), kGameStateSpeedOffset, std::int32_t{4});
    Put(jomini.data(), kJominiPlayersOffset, players.data());
    Put(jomini.data(), kJominiPausedOffset, std::uint8_t{0});
    Put(players.data(), kPlayersLocalPlayerIdOffset, std::int32_t{0});
    Put(local.data(), kPlayerIdOffset, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + kPlayerManagerEntriesOffset,
        player_entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + kPlayerManagerCountOffset,
        std::int32_t{1});
    Put(player_entry.data(), kPlayerEntryLocalPlayerIdOffset, std::int32_t{0});
    Put(player_entry.data(), kPlayerEntryCharacterIdOffset, actor);
    Put(character_storage.data(), kCharacterStorageSlotsOffset, character_slots.data());
    Put(character_storage.data(), kCharacterStorageCapacityOffset, std::int32_t{16});
    Put(character.data(), kCharacterFullIdOffset, actor);
    Put(character_slots.data(), 0x18, character.data());
    const auto &state = bindings.state;
    Put(game.data(), state.manager_offset, image_base + state.manager_vtable_rva);
    Put(game.data(), state.manager_offset + 0x20, scheme_storage.data());
    Put(scheme_storage.data(), 0, image_base + state.storage_vtable_rva);
    Put(scheme_storage.data(), 0x20, scheme_slots.data());
    Put(scheme_storage.data(), 0x2C, std::int32_t{16});
    Put(instance.data(), 0, image_base + state.instance_vtable_rva);
    Put(instance.data(), 0x14, std::uint32_t{0x5363686D});
    Put(instance.data(), 0x20, type.data());
    Put(instance.data(), 0x30, std::uint32_t{0});
    Put(type.data(), 0, image_base + state.type_vtable_rva);
    std::memcpy(type.data() + 0x18, "sway", 4);
    Put(type.data(), 0x28, std::uint64_t{4});
    Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(command.data(), 0, image_base + kSwayEndCommandPrimaryVptr12004);
    Put(command.data(), 0x18, image_base + kSwayEndCommandSecondaryVptr12004);
    Put(false_effect.data(), 0, image_base + kSwayEndEffectVptrRvas12004[0]);
    Put(true_effect.data(), 0, image_base + kSwayEndEffectVptrRvas12004[1]);
    Put(context.data(), 0, root.data());
    Reset();
    CoreSnapshotPrefix frame{};
    Check(ReadCoreSnapshot(bindings.state.core, frame) && frame.map_ready &&
          frame.has_played_character && frame.played_character_alive &&
          static_cast<std::uint32_t>(frame.played_character_id) == actor &&
          frame.clock.speed == 5 && !frame.clock.paused,
          "actual4 core projects raw4 to public5 and reads the living owner");
  }
  ~Fixture() { active = nullptr; local_player = nullptr; }
  void Reset(std::uint32_t id = scheme) {
    full_id = id;
    Put(core_state.data(), kGameStateDateOffset, std::int32_t{53220000});
    Put(instance.data(), 0x10, id);
    Put(instance.data(), 0x28, std::int32_t{0});
    Put(instance.data(), 0x2C, actor);
    Put(instance.data(), 0x34, target);
    Put(scheme_slots.data(), (id & 0x00FFFFFFu) * 0x10 + 8, instance.data());
    Put(command.data(), 0x20, id);
    Put(root.data(), 0, std::uint16_t{9});
    Put(root.data(), 8, std::uint64_t{id});
    post = Post::terminal;
  }
  SwayEndInvocationStamp12004 Stamp() {
    // Fixture-owned source coordinate; not a native source/parent proof.
    return {71, GetCurrentThreadId(), next_invocation++, true, 0x1234};
  }
  SwayEndCaptureResult12004 Invoke(std::size_t index, SwayEndInvocation12004 &out) {
    const auto stamp = Stamp();
    if (index == 0)
      return ForwardSwayEndCommand12004(bindings, stamp, &CommandOriginal,
                                       command.data() + 0x18, out);
    return ForwardSwayEndEffect12004(bindings, stamp,
        index == 1 ? SwayEndSourceClass12004::authored_end_scheme_false_execute :
                     SwayEndSourceClass12004::authored_end_scheme_true_execute,
        index == 1 ? &FalseOriginal : &TrueOriginal,
        index == 1 ? false_effect.data() : true_effect.data(), context.data(), out);
  }
  void Original(std::size_t index, const void *self, const void *input_context) {
    ++calls[index];
    arguments_match = arguments_match &&
        self == (index == 0 ? command.data() + 0x18 :
                 index == 1 ? false_effect.data() : true_effect.data()) &&
        input_context == (index == 0 ? nullptr : context.data());
    if (post == Post::throw_original) throw std::runtime_error("original sentinel");
    Put(core_state.data(), kGameStateDateOffset, std::int32_t{53220001});
    if (post == Post::terminal || post == Post::other_target) {
      Put(instance.data(), 0x28, std::int32_t{1});
      Put(instance.data(), 0x2C, std::uint32_t{0xFFFFFFFFu});
      Put(root.data(), 8, std::uint64_t{0xFFFFFFFFu});
      Put(command.data(), 0x20, std::uint32_t{0xFFFFFFFFu});
      if (post == Post::other_target) Put(instance.data(), 0x34, target + 1);
    } else if (post == Post::purge) {
      Put(scheme_slots.data(), (full_id & 0x00FFFFFFu) * 0x10 + 8,
          static_cast<void *>(nullptr));
    } else if (post == Post::reuse) {
      Put(instance.data(), 0x10, full_id + 0x01000000u);
      Put(instance.data(), 0x28, std::int32_t{1});
    }
  }
};
void CommandOriginal(const void *self) { active->Original(0, self, nullptr); }
void FalseOriginal(const void *self, const void *context) { active->Original(1, self, context); }
void TrueOriginal(const void *self, const void *context) { active->Original(2, self, context); }
void Terminal(const SwayEndInvocation12004 &record, SwayEndSourceClass12004 source) {
  Check(record.source.source_class == source && record.source.scheme_id == scheme &&
        record.scheme_instance_generation == 2 && record.source.pre_owner == actor &&
        record.source.post_owner == 0xFFFFFFFFu &&
        record.source.post_exact_instance_join_ready &&
        record.source.native_terminal_state_observed &&
        record.source.native_terminal_transition_observed,
        "copied full generation and exact pre/post terminal transition");
  Check(record.pre_frame_observed && record.post_frame_observed &&
        record.pre_frame.clock.date_raw == 53220000 &&
        record.post_frame.clock.date_raw == 53220001 &&
        record.original_forwarded_once && record.original_returned &&
        record.stamp.observer_session_identity == 71 &&
        record.stamp.owner_thread_id == GetCurrentThreadId() &&
        record.stamp.incoming_return_address_observed &&
        record.stamp.caller_return_rva == 0x1234 &&
        !record.causal_parent_observed && record.causal_parent_invocation_id == 0,
        "independent frames and copied invocation stamp leave causal parent unavailable");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one external output directory required");
    Check(!BindSwayEndInvocationImage12004(image_base, "wrong-build").enabled,
          "exact executable SHA admission required");
    Check(kSwayEndInvocationSlotRvas12004 ==
          std::array<std::uintptr_t, 3>{0x476EB88, 0x4852280, 0x4852C38} &&
          kSwayEndInvocationOriginalRvas12004 ==
          std::array<std::uintptr_t, 3>{0x299C320, 0x2D11B30, 0x2D11AD0},
          "three actual4 typed source coordinates");
    Fixture fixture;
    SwayEndInvocation12004 record{};
    Check(fixture.Invoke(0, record) == SwayEndCaptureResult12004::captured,
          "actual4 command secondary receiver capture");
    Terminal(record, SwayEndSourceClass12004::end_scheme_command_execute);
    fixture.Reset(); fixture.post = Post::unchanged;
    Check(fixture.Invoke(1, record) == SwayEndCaptureResult12004::captured &&
          record.source.post_status_observed && record.source.post_status == 0 &&
          record.source.executing_source_observed &&
          !record.source.native_terminal_state_observed &&
          !record.source.native_terminal_transition_observed,
          "false effect source can return without a terminal transition");
    fixture.Reset();
    Check(fixture.Invoke(2, record) == SwayEndCaptureResult12004::captured,
          "true typed effect/root input capture");
    Terminal(record, SwayEndSourceClass12004::authored_end_scheme_true_execute);
    Check(record.source.input_root_scope_kind == 9,
          "effect context root kind9 is copied before original destroys its token");
    fixture.Reset(); fixture.post = Post::purge;
    Check(fixture.Invoke(2, record) == SwayEndCaptureResult12004::captured &&
          record.source.post_read_succeeded && !record.source.post_instance_present &&
          !record.source.native_terminal_state_observed,
          "missing post instance never proves terminal state");
    fixture.Reset(); fixture.post = Post::reuse;
    Check(fixture.Invoke(2, record) == SwayEndCaptureResult12004::captured &&
          record.source.post_storage_slot_reused && !record.source.post_exact_instance_join_ready &&
          !record.source.native_terminal_transition_observed,
          "same slot different generation never joins the pre instance");
    fixture.Reset(); fixture.post = Post::other_target;
    Check(fixture.Invoke(2, record) == SwayEndCaptureResult12004::captured &&
          record.source.post_instance_present && !record.source.post_exact_instance_join_ready &&
          !record.source.native_terminal_state_observed,
          "changed target does not satisfy the exact identity join");
    fixture.Reset(0xB);
    Check(fixture.Invoke(1, record) == SwayEndCaptureResult12004::captured &&
          record.source.scheme_id == 0xB && record.scheme_instance_generation == 0 &&
          record.source.native_terminal_transition_observed,
          "generation zero remains a valid full SchemeID");
    fixture.Reset(); fixture.post = Post::unchanged;
    Put(fixture.root.data(), 0, std::uint16_t{6});
    Check(fixture.Invoke(2, record) == SwayEndCaptureResult12004::ignored &&
          record.original_forwarded_once && record.original_returned &&
          !record.source.executing_source_observed,
          "ignored root source still forwards the original once");
    fixture.Reset(); fixture.post = Post::unchanged;
    auto unavailable = fixture.bindings; unavailable.enabled = false;
    Check(ForwardSwayEndCommand12004(unavailable, fixture.Stamp(), &CommandOriginal,
          fixture.command.data() + 0x18, record) == SwayEndCaptureResult12004::unavailable &&
          record.original_forwarded_once && record.original_returned,
          "unavailable observation still forwards the command once");
    auto invalid_stamp = fixture.Stamp(); invalid_stamp.observer_session_identity = 0;
    Check(ForwardSwayEndEffect12004(fixture.bindings, invalid_stamp,
          SwayEndSourceClass12004::authored_end_scheme_false_execute, &FalseOriginal,
          fixture.false_effect.data(), fixture.context.data(), record) ==
          SwayEndCaptureResult12004::unavailable && record.original_forwarded_once &&
          !record.source.executing_source_observed,
          "missing observer session cannot produce an attributable copied observation");
    fixture.Reset(); fixture.post = Post::throw_original;
    bool original_exception = false;
    try { (void)fixture.Invoke(1, record); }
    catch (const std::runtime_error &error) {
      original_exception = std::string_view(error.what()) == "original sentinel";
    }
    Check(original_exception && record.original_forwarded_once && !record.original_returned &&
          !record.post_frame_observed && !record.source.native_terminal_transition_observed,
          "original exception propagates unchanged without invented post-state");
    Check(fixture.calls == std::array<std::size_t, 3>{2, 4, 5} && fixture.arguments_match,
          "all eleven typed originals receive identical used operands exactly once");
    const std::filesystem::path directory{argv[1]};
    std::ofstream proof(directory / "sway-end-invocation-leaf-fixture.json");
    proof << "{\"schema\":\"xar.sway-end-invocation-current04-focused-fixture.v1\","
             "\"status\":\"PASS\",\"game_version\":\"" << kGameVersion <<
             "\",\"executable_sha256\":\"" << kExecutableSha256 <<
             "\",\"owned_memory_only\":true,\"live_verified\":false,"
             "\"specific_cause_qualified\":false,\"causal_parent_qualified\":false,"
             "\"checks\":" << checks << ",\"original_calls\":[2,4,5]}\n";
    Check(proof.good(), "focused copied fixture receipt emitted");
    std::cout << "PASS " << checks << " checks; actual4 end leaf; typed original once; "
                 "independent fullID pre/post; source/cause separate; owned memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
