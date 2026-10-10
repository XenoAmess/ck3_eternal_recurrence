#include "xar_bridge/person_installed_transfer_capture_12004.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kCallRva = 0x2A3DC44;
constexpr std::array<std::uint8_t,15> kAnchor{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,
    0x48,0x89,0x74,0x24,0x20};
constexpr std::uintptr_t kReturnBits = 0xFEDCBA9876543210ULL;
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct World {
  std::array<std::byte,0x2F8> a{},b{};
  std::array<std::byte,0x1B8> owner{},other_owner{};
  std::array<std::byte,0x260> carrier{};
  PersonSixStageCapture12004DTO capture;
  PersonInstalledTransferCaptureState12004 *state = nullptr;
  std::uint32_t calls = 0;
  bool uninstall_inside_original = false;
  bool nested_uninstall_refused = false;
  template<class T,std::size_t N>
  void Put(std::array<std::byte,N>& block,std::size_t offset,T value) {
    std::memcpy(block.data()+offset,&value,sizeof(value));
  }
  template<std::size_t N>
  std::uintptr_t Address(std::array<std::byte,N>& block) {
    return reinterpret_cast<std::uintptr_t>(block.data());
  }
  void Reset() {
    Put(owner,0x18,std::uint32_t{0xAB007485});
    Put(other_owner,0x18,std::uint32_t{0xCD007485});
    Put(owner,0x1B0,Address(carrier));
    Put(carrier,0x258,Address(a));
    Put(a,0x8,Address(other_owner));
    Put(b,0x8,Address(owner));
    capture = {};
    capture.capture_observed = true;
    capture.capture_complete = true;
    capture.capture_sequence = 7;
    capture.capture_thread_id = GetCurrentThreadId();
    capture.query_thread_id = GetCurrentThreadId();
    capture.character_id = 0xAB007485;
    capture.character_identity = Address(owner);
    capture.context_identity = Address(b)+0x10;
    capture.preparation_model.model_identity = Address(b);
    capture.preparation_model.owner_character_identity = Address(owner);
    capture.preparation_model.owner_character_id = 0xAB007485;
  }
  World() { Reset(); }
};
World *g_world = nullptr;
std::uintptr_t __fastcall Original(void *a,void *b) {
  auto &world = *g_world;
  Require(a == world.a.data() && b == world.b.data(),"original A/B must stay exact");
  ++world.calls;
  std::uintptr_t owner_a = 0,owner_b = 0;
  std::memcpy(&owner_a,world.a.data()+8,sizeof(owner_a));
  std::memcpy(&owner_b,world.b.data()+8,sizeof(owner_b));
  world.Put(world.a,8,owner_b);
  world.Put(world.b,8,owner_a);
  if (world.uninstall_inside_original)
    world.nested_uninstall_refused =
        !UninstallPersonInstalledTransferCapture12004(*world.state,true);
  world.capture.capture_sequence = 999; // Owned before-copy must stay sequence7.
  return kReturnBits;
}
void Jump(std::uint8_t *output,std::uintptr_t target) {
  constexpr std::array<std::uint8_t,6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(output,prefix.data(),prefix.size());
  std::memcpy(output+prefix.size(),&target,sizeof(target));
}
struct Arena {
  void *reservation = nullptr;
  std::uintptr_t base = 0;
  std::uint8_t *target = nullptr;
  PersonInstalledTransferOriginal12004 caller = nullptr;
  Arena() {
    // Reserve an address arena; commit only two synthetic pages. No image file
    // is loaded or read. The call's actual return address has the held RVA.
    reservation = VirtualAlloc(nullptr,0x2A3E000,MEM_RESERVE,PAGE_NOACCESS);
    Require(reservation != nullptr,"reserve synthetic RVA arena");
    base = reinterpret_cast<std::uintptr_t>(reservation);
    target = reinterpret_cast<std::uint8_t *>(base+kPersonInstalledTransferRva12004);
    for (const auto page : {base+0x291C000,base+0x2A3D000})
      Require(VirtualAlloc(reinterpret_cast<void *>(page),0x1000,MEM_COMMIT,
                           PAGE_READWRITE) != nullptr,"commit synthetic code page");
    std::memcpy(target,kAnchor.data(),kAnchor.size());
    Jump(target+15,reinterpret_cast<std::uintptr_t>(&Original));
    auto *entry = reinterpret_cast<std::uint8_t *>(base+kCallRva-4);
    constexpr std::array<std::uint8_t,4> sub{0x48,0x83,0xEC,0x28};
    constexpr std::array<std::uint8_t,5> finish{0x48,0x83,0xC4,0x28,0xC3};
    std::memcpy(entry,sub.data(),sub.size());
    entry[4]=0xE8;
    const auto relative = static_cast<std::int32_t>(
        static_cast<std::intptr_t>(base+kPersonInstalledTransferRva12004)-
        static_cast<std::intptr_t>(base+kCallRva+5));
    std::memcpy(entry+5,&relative,sizeof(relative));
    std::memcpy(entry+9,finish.data(),finish.size());
    for (const auto page : {base+0x291C000,base+0x2A3D000}) {
      DWORD old = 0;
      Require(VirtualProtect(reinterpret_cast<void *>(page),0x1000,PAGE_EXECUTE_READ,&old) != FALSE,
              "protect synthetic code");
      Require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void *>(page),0x1000) != FALSE,
              "flush synthetic code");
    }
    caller = reinterpret_cast<PersonInstalledTransferOriginal12004>(entry);
  }
  ~Arena() { if (reservation) VirtualFree(reservation,0,MEM_RELEASE); }
};
struct Failures {
  std::uint32_t target_flush_failures = 0;
  std::uint32_t free_failures = 0;
  static bool Flush(void *context,const void *address,std::size_t bytes) noexcept {
    auto &failure = *static_cast<Failures *>(context);
    if (bytes == 15 && failure.target_flush_failures != 0) {
      --failure.target_flush_failures;
      return false;
    }
    return FlushInstructionCache(GetCurrentProcess(),address,bytes) != FALSE;
  }
  static bool Free(void *context,void *address,std::size_t bytes,DWORD type) noexcept {
    auto &failure = *static_cast<Failures *>(context);
    if (failure.free_failures != 0) { --failure.free_failures; return false; }
    return VirtualFree(address,bytes,type) != FALSE;
  }
};
PersonInstalledTransferCaptureInstall12004 Environment(Arena &arena,Failures &failure) {
  PersonInstalledTransferCaptureInstall12004 env;
  env.primary_thread_suspended_proven = true;
  env.offline_fixture = true;
  env.module_base = arena.base;
  env.bindings = BindPersonInstalledTransferCaptureImage12004(
      arena.base,kPersonInstalledTransferCaptureExeSha12004);
  env.memory_context = &failure;
  env.flush_override = Failures::Flush;
  env.virtual_free_override = Failures::Free;
  return env;
}
void Compound() {
  World world;
  g_world = &world;
  Arena arena;
  Failures failure;
  auto env = Environment(arena,failure);
  PersonInstalledTransferCaptureState12004 state;
  world.state = &state;
  const auto before = NextPersonNaturalLineageEvent12004();
  const auto next = NextPersonNaturalLineageEvent12004();
  Require(before.clock_identity != 0 && before.clock_identity == next.clock_identity &&
          next.sequence > before.sequence && next.thread_id == GetCurrentThreadId(),
          "shared production clock must advance on actual thread");
  Require(!InstallPersonInstalledTransferCapture12004(state,env,"wrong"),"reject wrong image pin");
  env.primary_thread_suspended_proven = false;
  Require(!InstallPersonInstalledTransferCapture12004(state,env,kPersonInstalledTransferCaptureExeSha12004),
          "reject absent install quiescence");
  env.primary_thread_suspended_proven = true;
  failure.target_flush_failures = 1;
  Require(!InstallPersonInstalledTransferCapture12004(state,env,kPersonInstalledTransferCaptureExeSha12004) &&
          state.installed.load() == 0 && state.trampoline == nullptr &&
          std::memcmp(arena.target,kAnchor.data(),15) == 0,
          "failed target flush must rollback bytes and free unreachable backing");
  Require(InstallPersonInstalledTransferCapture12004(state,env,kPersonInstalledTransferCaptureExeSha12004),
          "install real entry patch over synthetic held prologue");
  Require(arena.caller(world.a.data(),world.b.data()) == kReturnBits && world.calls == 1,
          "actual synthetic CALL/entrypatch/trampoline must original-once and preserve RAX");
  auto query = ReadPersonInstalledTransferCapture12004();
  Require(query.records.size() == 1 && query.configured && query.installed,"retain one natural dispatch record");
  const auto stage = query.records.back().stage;
  Require(stage.original_return_rva == kPersonInstalledTransferCallerReturnRva12004 &&
          stage.preparation.preparation_capture_sequence == 7 &&
          stage.after.observed_owner_identity == world.Address(world.owner) &&
          stage.after.model_b_owner_identity == world.Address(world.other_owner) &&
          stage.after.installed_model_is_a == true &&
          stage.preparation_model_is_b == true && stage.completion_ordered_after_begin == true,
          "production default owned adapter must retain beforeB/afterA identity and original completion");
  const auto consume_begin = NextPersonNaturalLineageEvent12004();
  const auto consume_end = NextPersonNaturalLineageEvent12004();
  Require(consume_begin.clock_identity == stage.completed_event.clock_identity &&
          consume_begin.thread_id == stage.completed_event.thread_id &&
          stage.completed_event.sequence < consume_begin.sequence && consume_begin.sequence < consume_end.sequence,
          "consumer API and producer must share one actual monotonic domain");
  PersonSixStageQuery12004DTO batch;
  batch.snapshot_revision = 88;
  batch.observed_date_raw = 12004;
  PersonSixStageCapture12004DTO receiver;
  receiver.character_identity = world.Address(world.owner);
  receiver.character_id = 0xAB007485;
  batch.character_captures.push_back(receiver);
  auto filtered = CollectPersonInstalledTransferCaptureForOwners12004(batch);
  Require(filtered.request_filtered && filtered.records.size() == 1 &&
          filtered.snapshot_revision == std::uint64_t{88},"filter existing resolved batch identities");
  const auto wire = SerializePersonInstalledTransferCapture12004(filtered);
  Require(wire.find("\"request_filtered\":true") != std::string::npos &&
          wire.find("\"preparation_capture_sequence\":7") != std::string::npos &&
          wire.find("\"offline_fixture\":true") != std::string::npos &&
          wire.find("\"transfer_to_entry_association_proven\":false") != std::string::npos,
          "retained wire must preserve domains and qualification");
  std::cout << "WIRE " << wire << '\n';
  batch.character_captures.front().character_id = std::uint32_t{0xCD007485};
  Require(CollectPersonInstalledTransferCaptureForOwners12004(batch).records.empty(),
          "same low index/different full generation cannot join");
  batch.character_captures.clear();
  batch.character_captures.emplace_back();
  auto unresolved = CollectPersonInstalledTransferCaptureForOwners12004(batch);
  Require(unresolved.records.empty() && unresolved.unresolved_receiver_count == 1,
          "unresolved receiver cannot fall back to unfiltered history");
  world.Reset();
  const auto direct = reinterpret_cast<PersonInstalledTransferOriginal12004>(arena.target);
  Require(direct(world.a.data(),world.b.data()) == kReturnBits && world.calls == 2 &&
          ReadPersonInstalledTransferCapture12004().records.size() == 1,
          "nonpaired caller preserves original without new retained record");
  Require(!UninstallPersonInstalledTransferCapture12004(state,false) && state.installed.load() != 0,
          "live Stop without quiescence must retain installed backing");
  world.Reset();
  world.uninstall_inside_original = true;
  Require(arena.caller(world.a.data(),world.b.data()) == kReturnBits && world.nested_uninstall_refused,
          "active original must prevent uninstallation");
  world.uninstall_inside_original = false;
  const auto retained_count = ReadPersonInstalledTransferCapture12004().records.size();
  failure.free_failures = 1;
  Require(!UninstallPersonInstalledTransferCapture12004(state,true) &&
          state.installed.load() == 0 && state.trampoline != nullptr,
          "failed free must retain the orphan allocation explicitly");
  Require(UninstallPersonInstalledTransferCapture12004(state,true) && state.trampoline == nullptr,
          "retry releases only retained orphan backing");
  Require(ReadPersonInstalledTransferCapture12004().records.size() == retained_count &&
          !ReadPersonInstalledTransferCapture12004().configured,
          "immutable history survives actual uninstall");
  const auto clock_after_stop = NextPersonNaturalLineageEvent12004();
  Require(clock_after_stop.clock_identity == before.clock_identity && clock_after_stop.sequence > consume_end.sequence,
          "uninstall must not reset shared clock");
  PersonInstalledTransferCaptureState12004 rollback;
  failure.target_flush_failures = 2;
  Require(!InstallPersonInstalledTransferCapture12004(rollback,env,kPersonInstalledTransferCaptureExeSha12004) &&
          rollback.installed.load() != 0 && rollback.trampoline != nullptr &&
          (rollback.failure_flags.load() & transfer_capture_rollback) != 0,
          "unproven rollback must retain backing instead of pretending clean install");
  Require(UninstallPersonInstalledTransferCapture12004(rollback,true) && rollback.trampoline == nullptr,
          "explicit quiescent cleanup revalidates restored original after failed rollback flush");
  Require(InstallPersonInstalledTransferCapture12004(state,env,kPersonInstalledTransferCaptureExeSha12004),
          "reinstall without resetting clock/history");
  world.state = &state;
  for (std::size_t i=0;i<kPersonInstalledTransferCaptureCapacity12004+1;++i) {
    world.Reset();
    Require(arena.caller(world.a.data(),world.b.data()) == kReturnBits,"each ring dispatch keeps raw retval");
  }
  const auto bounded = ReadPersonInstalledTransferCapture12004();
  Require(bounded.records.size() == kPersonInstalledTransferCaptureCapacity12004 && bounded.overwritten_records > 0,
          "retained production history must remain bounded");
  const auto owned = ReadPersonInstalledTransferCaptureForOwner12004(world.Address(world.owner),0xAB007485);
  Require(owned && owned->record_sequence == bounded.latest_record_sequence,
          "owner/fullID lookup returns latest immutable matching record");
  Require(UninstallPersonInstalledTransferCapture12004(state,true),"finish synthetic lifecycle");
}
} // namespace

namespace xar::ck3_12004 {
// Only the existing owned-history lookup is supplied by the fixture. The new
// production adapter/dispatch/clock/patch/trampoline/serializer all run as built.
PersonSixStageCapture12004DTO ReadPersonSixStageCaptureForCharacter12004(
    std::uintptr_t owner,std::uint32_t full_id) noexcept {
  if (g_world && owner == g_world->Address(g_world->owner) && full_id == 0xAB007485)
    return g_world->capture;
  return {};
}
}

int main() {
  try {
    Compound();
    std::cout << "GREEN: natural-transfer install dispatch retained-wire compound; synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
