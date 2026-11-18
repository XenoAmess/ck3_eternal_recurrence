#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#if defined(XAR_CK3_PERSONAL_GOLD_FRAME_TEST)
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include <windows.h>
#endif

#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>

namespace {
using namespace xar::ck3_1210;

void Require(bool condition, const char *message) {
  if (!condition) {
    std::cerr << "FAIL " << message << '\n';
    std::exit(1);
  }
}

template <class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(value) <= buffer.size() - offset,
      "fixture store bounds");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

enum class Mutation {
  none, date_first, paused_first, actor_second, living_second, gold_second,
  death_second, type_second, generation_second, map_second
};
struct Fixture;
Fixture *active = nullptr;
#if defined(XAR_CK3_PERSONAL_GOLD_FRAME_TEST)
xar::ck3_11906::MainThreadQueryMailboxV1 *owner_reset_on_first_core=nullptr;
#endif
void *LocalPlayer(void *);

// Complete independent buffers needed by the real 1.21 Core reader. All
// pointers and the native-call replacement below refer only to fixture RAM.
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data =
      std::vector<std::byte>(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> character{}, replacement{};
  std::array<std::byte, 0x108> living{}, other_living{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x20> slots{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *storage_pointer = storage.data();
  PersonalGoldBindingsV1 bindings{};
  Mutation mutation = Mutation::none;
  unsigned reads = 0;
  std::int32_t id;

  explicit Fixture(std::int32_t full_id =
      std::bit_cast<std::int32_t>(std::uint32_t{0x81000001})) : id(full_id) {
    active = this;
    Store(state, 8, std::int32_t{123456});
    Store(state, 0x70, std::int32_t{4});
    Store(state, 0xA0, data.data());
    Store(jomini, 0x18, players.data());
    jomini[0x20] = std::byte{1};
    Store(players, 0x1F0, std::int32_t{7});
    Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7});
    Store(entry, 0xB0, id);
    Store(character, 0x18, id);
    Store(character, 0x1C, std::uint32_t{0x43686172});
    Store(character, 0x1B0, living.data());
    Store(living, 0x100, std::int64_t{12345000});
    Store(other_living, 0x100, std::int64_t{12345000});
    Store(replacement, 0x18, id);
    Store(replacement, 0x1C, std::uint32_t{0x43686172});
    Store(replacement, 0x1B0, other_living.data());
    Store(storage, 0x20, slots.data());
    Store(storage, 0x2C, std::int32_t{2});
    Place(character.data());
    // Exercise the actual exact-hash constructor, then replace its Core
    // addresses with synthetic fixture memory. No mapped EXE is invoked.
    bindings = BindPersonalGoldImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted, "exact fixture binding constructor");
    bindings.core = {true, &state_pointer, &jomini_pointer,
        &storage_pointer, &LocalPlayer};
  }

  void Place(void *actor) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, index * 0x10 + 8, actor);
  }

  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix prefix{};
    Require(ReadCoreSnapshot(bindings.core, prefix), "fixture Core capture");
    Require(prefix.map_ready && prefix.has_played_character &&
        prefix.played_character_id == id && prefix.played_character_alive,
        "fixture full-generation identity");
    reads = 0;
    return prefix;
  }
};

void *LocalPlayer(void *) {
  auto &f = *active;
  ++f.reads;
#if defined(XAR_CK3_PERSONAL_GOLD_FRAME_TEST)
  if(owner_reset_on_first_core && f.reads==1)owner_reset_on_first_core->proof_reset_requested.store(true);
#endif
  if (f.reads == 1 && f.mutation == Mutation::date_first)
    Store(f.state, 8, std::int32_t{123457});
  if (f.reads == 1 && f.mutation == Mutation::paused_first)
    f.jomini[0x20] = std::byte{};
  if (f.reads == 2) {
    switch (f.mutation) {
    case Mutation::actor_second: f.Place(f.replacement.data()); break;
    case Mutation::living_second:
      Store(f.character, 0x1B0, f.other_living.data()); break;
    case Mutation::gold_second:
      Store(f.living, 0x100, std::int64_t{12345001}); break;
    case Mutation::death_second:
      Store(f.character, 0x1D0, f.character.data()); break;
    case Mutation::type_second:
      Store(f.character, 0x1C, std::uint32_t{0x4C616E64}); break;
    case Mutation::generation_second:
      Store(f.character, 0x18,
          std::bit_cast<std::int32_t>(std::uint32_t{0x82000001})); break;
    case Mutation::map_second: return nullptr;
    default: break;
    }
  }
  return f.player.data();
}

void CheckUnavailable(const PersonalGoldBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, std::string_view reason) {
  PersonalGoldObservationV1 output{};
  output.available = true;
  output.same_frame_ready = true;
  output.personal_gold_raw = 777;
  Require(!ReadPersonalGoldV1(bindings, expected, output),
      "unavailable read must return false");
  Require(!output.available && !output.same_frame_ready &&
      !output.personal_gold_raw && output.unavailable_reason == reason,
      "failure clears old amount and exposes its reason");
  Require(output.partial && !output.full_snapshot_available &&
      !output.treasury_observed && !output.monthly_flow_observed,
      "failure cannot grant unrelated observation");
}

void CheckAmount(Fixture &f, std::int64_t value) {
  const auto expected = f.Expected();
  PersonalGoldObservationV1 output{};
  Require(ReadPersonalGoldV1(f.bindings, expected, output), "observed personal gold");
  Require(output.available && output.same_frame_ready &&
      output.personal_gold_raw.has_value() && *output.personal_gold_raw == value,
      "signed observed amount preserved");
  Require(output.scale == 100000 && output.schema == kPersonalGoldSchemaV1 &&
      output.game_version == kGameVersion && output.steam_build_id == kSteamBuildId &&
      output.executable_sha256 == kExecutableSha256 &&
      output.executable_file_size == kExecutableFileSize,
      "exact tuple and fixed scale");
  Require(output.frame.played_character_id == f.id &&
      output.frame.clock.date_raw == expected.clock.date_raw &&
      output.frame.clock.speed == expected.clock.speed && output.frame.clock.paused &&
      output.frame.local_player_id == expected.local_player_id && output.frame.map_ready &&
      output.frame.has_played_character && output.frame.played_character_alive &&
      output.unavailable_reason.empty(), "stable complete prefix");
  Require(output.partial && !output.full_snapshot_available &&
      !output.treasury_observed && !output.monthly_flow_observed,
      "one wallet is not complete Snapshot or finance");
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  {
    Fixture f;
    Require(f.id < 0 && f.id != -1, "fixture high generation is signed negative");
    CheckAmount(f, 12345000);
    for (const auto amount : {std::int64_t{-750000}, std::int64_t{0},
             (std::numeric_limits<std::int64_t>::min)(),
             (std::numeric_limits<std::int64_t>::max)()}) {
      Store(f.living, 0x100, amount);
      CheckAmount(f, amount);
    }
    Store(f.character, 0x1B0, static_cast<void *>(nullptr));
    CheckAmount(f, 0); // Native null-living zero while Core still says alive.
  }
  {
    Fixture f(0);
    CheckAmount(f, 12345000); // Canonical full ID zero is not the -1 sentinel.
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    auto disabled = f.bindings;
    disabled.exact_build_admitted = false;
    CheckUnavailable(disabled, expected, "unsupported_build");
    disabled = f.bindings;
    disabled.core.enabled = false;
    CheckUnavailable(disabled, expected, "unsupported_build");
    auto missing = f.bindings;
    missing.core.character_storage_slot = nullptr;
    CheckUnavailable(missing, expected, "core_binding_unavailable");
    f.state_pointer = nullptr;
    CheckUnavailable(f.bindings, expected, "core_read_failed");
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    auto wrong = expected;
    wrong.clock.paused = false;
    CheckUnavailable(f.bindings, wrong, "requires_paused");
    wrong = expected; wrong.map_ready = false;
    CheckUnavailable(f.bindings, wrong, "map_not_ready");
    wrong = expected; wrong.has_played_character = false;
    CheckUnavailable(f.bindings, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_id = -1;
    CheckUnavailable(f.bindings, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_alive = false;
    CheckUnavailable(f.bindings, wrong, "player_not_alive");
    wrong = expected; ++wrong.clock.date_raw;
    CheckUnavailable(f.bindings, wrong, "core_frame_changed");
    wrong = expected; --wrong.clock.speed;
    CheckUnavailable(f.bindings, wrong, "core_frame_changed");
    wrong = expected; ++wrong.local_player_id;
    CheckUnavailable(f.bindings, wrong, "core_frame_changed");
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    Store(f.character, 0x18,
        std::bit_cast<std::int32_t>(std::uint32_t{0x82000001}));
    CheckUnavailable(f.bindings, expected, "core_frame_changed");
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    Store(f.character, 0x1C, std::uint32_t{0x4C616E64});
    CheckUnavailable(f.bindings, expected, "player_identity_unavailable");
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    Store(f.character, 0x1D0, f.character.data());
    CheckUnavailable(f.bindings, expected, "core_frame_changed");
  }
  {
    Fixture f;
    const auto expected = f.Expected();
    Store(f.state, 0x70, std::int32_t{5});
    CheckUnavailable(f.bindings, expected, "core_read_failed");
  }
  for (const auto change : {Mutation::date_first, Mutation::paused_first,
           Mutation::actor_second, Mutation::living_second, Mutation::gold_second,
           Mutation::death_second, Mutation::type_second,
           Mutation::generation_second, Mutation::map_second}) {
    Fixture f;
    const auto expected = f.Expected();
    f.mutation = change;
    const auto reason = change == Mutation::gold_second ? "personal_gold_changed" :
        (change == Mutation::actor_second || change == Mutation::living_second ||
         change == Mutation::type_second) ? "player_identity_changed" :
        "core_frame_changed";
    CheckUnavailable(f.bindings, expected, reason);
  }
#if defined(_MSC_VER)
  {
    Fixture f;
    const auto expected = f.Expected();
    Store(f.character, 0x1B0, reinterpret_cast<void *>(std::uintptr_t{1}));
    CheckUnavailable(f.bindings, expected, "memory_read_failed");
  }
#endif
  Require(!BindPersonalGoldImageV1(0, kExecutableSha256).exact_build_admitted,
      "null image rejected");
  Require(!BindPersonalGoldImageV1(0x140000000,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
      .exact_build_admitted, "old .4 image identity rejected");
  Require(!BindPersonalGoldImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "address overflow rejected");
#if defined(XAR_CK3_PERSONAL_GOLD_FRAME_TEST)
  {
    using namespace xar::ck3_11906;
    Fixture f(0x01000001);const auto expected=f.Expected();
    auto game=xar::game::CreateCk3_1210AdapterFromBindings(f.bindings.core);
    Require(game->supports(kPersonalGoldCapabilityV1),"exact readonly capability selected");
    MainThreadQueryMailboxV1 mailbox{};
    PersonalGoldMailboxContextV1 q{};q.game=game.get();q.bindings=f.bindings;q.mailbox=&mailbox;q.ticket.sequence=7;
    MainThreadExecutionStampV1 stamp{};stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=3;
    stamp.tls_initialized=1;stamp.tls_main_thread_marker=1;stamp.tls_context=1;
    stamp.game_state=reinterpret_cast<std::uintptr_t>(f.state_pointer);
    stamp.jomini_state=reinterpret_cast<std::uintptr_t>(f.jomini_pointer);
    stamp.date_raw=expected.clock.date_raw;stamp.paused=true;
    mailbox.state.store(MainThreadQueryMailboxStateV1::executing);mailbox.owner_thread_id.store(stamp.thread_id);
    mailbox.iat_hook_installed.store(true);
    mailbox.paused_owner_verified_pump_epochs.store(2);mailbox.published_sequence.store(7);
    mailbox.executor.store(&ExecutePersonalGoldMailboxV1);mailbox.executor_context=&q;
    mailbox.offline_fixture=true; // Explicit NoGame RAM, not physical image qualification.
    mailbox.pump_epochs.store(stamp.pump_epoch);mailbox.active_hook_calls.store(1);
    mailbox.executor_started_sequence.store(q.ticket.sequence);mailbox.executor_started_pump_epoch.store(stamp.pump_epoch);
    // This used to be accepted by the actual Actor prefix despite lacking a
    // physical module witness. Only explicit offline RAM may use these slots.
    mailbox.offline_fixture=false;f.reads=0;
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && f.reads==0 && !q.application_main_observed &&
        !q.observation.available && !q.observation.personal_gold_raw,"production Actor rejects RAM Core/getter before calling it");
    const auto original_bindings=q.bindings;
    const auto module=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    mailbox.module_base=module;
    mailbox.game_state_slot=module+xar::ck3_1210::kGameStateSlotRva;
    mailbox.jomini_state_slot=module+xar::ck3_1210::kJominiStateSlotRva;
    mailbox.tls_initialized_flag=module+xar::ck3_1210::kMainThreadTlsInitializedFlagRva;
    mailbox.tls_context_getter=reinterpret_cast<MainThreadTlsContextGetterV1>(
        module+xar::ck3_1210::kMainThreadTlsContextGetterRva);
    stamp.tls_initialized_flag_address=mailbox.tls_initialized_flag;
    for(int field=0;field<5;++field) {
      q.bindings=BindPersonalGoldImageV1(module,xar::ck3_1210::kExecutableSha256);
      if(field==0)q.bindings.core.get_local_player=&LocalPlayer;
      if(field==1)q.bindings.core.character_storage_slot=nullptr;
      if(field==2)q.bindings.core.jomini_state_slot=nullptr;
      if(field==3)q.bindings.core.game_state_slot=nullptr;
      if(field==4)q.bindings=BindPersonalGoldImageV1(module+0x1000,xar::ck3_1210::kExecutableSha256);
      f.reads=0;
      Require(ExecutePersonalGoldMailboxV1(&q,stamp) && f.reads==0 && !q.observation.available && !q.observation.personal_gold_raw,
          "each crossed Core field or foreign complete bundle rejects before getter/TLS source access");
    }
    q.bindings=original_bindings;mailbox.offline_fixture=true;
    mailbox.module_base=0;mailbox.game_state_slot=0;mailbox.jomini_state_slot=0;
    mailbox.tls_initialized_flag=0;mailbox.tls_context_getter=nullptr;stamp.tls_initialized_flag_address=0;
    for(int event=0;event<3;++event) {
      mailbox.proof_reset_requested.store(event==0);
      mailbox.pump_epochs.store(stamp.pump_epoch+(event==1?1:0));
      mailbox.active_hook_calls.store(event==2?0:1);f.reads=0;
      Require(ExecutePersonalGoldMailboxV1(&q,stamp) && f.reads==0 && !q.observation.available && !q.observation.personal_gold_raw,
          "ordinary Actor rejects reset/current epoch/hook loss before any Core getter");
    }
    mailbox.proof_reset_requested.store(false);mailbox.pump_epochs.store(stamp.pump_epoch);
    mailbox.active_hook_calls.store(1);f.reads=0;
    owner_reset_on_first_core=&mailbox;
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && f.reads==1 && !q.observation.available && !q.observation.personal_gold_raw &&
        q.application_main_observed,"first Core getter revocation closes leaf reads but retains observed owner fact");
    owner_reset_on_first_core=nullptr;mailbox.proof_reset_requested.store(false);f.reads=0;

    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && q.observation.available,"own paused mailbox reads actual wallet model");
    std::cout<<SerializePersonalGoldCommandResultV1("gold-partial-fixture",q)<<std::endl;
    Store(f.living,0x100,(std::numeric_limits<std::int64_t>::min)());
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && q.observation.personal_gold_raw==(std::numeric_limits<std::int64_t>::min)(),"signed64 minimum survives producer");
    std::cout<<SerializePersonalGoldCommandResultV1("gold-minimum-fixture",q)<<std::endl;
    mailbox.iat_hook_installed.store(false);
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && !q.observation.available,"uninstalled provider has no observation authority");
    mailbox.iat_hook_installed.store(true);
    stamp.paused=false;
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && !q.observation.available,"unpaused role cannot borrow timeline exemption");
    std::cout<<SerializePersonalGoldCommandResultV1("gold-unavailable-fixture",q)<<std::endl;
    stamp.paused=true;mailbox.published_sequence.store(8);
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && !q.observation.available,"wrong ticket is unavailable");
    mailbox.published_sequence.store(7);mailbox.owner_thread_id.store(stamp.thread_id+1);
    Require(ExecutePersonalGoldMailboxV1(&q,stamp) && !q.observation.available,"foreign owner is unavailable");
  }
#endif
  std::cout << "PASS personal gold synthetic Core/full-generation/signed/null/"
      "identity/frame guards; no game image or game code executed\n";
  return 0;
}
