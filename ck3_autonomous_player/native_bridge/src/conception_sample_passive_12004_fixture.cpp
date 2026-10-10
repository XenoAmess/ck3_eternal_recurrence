#include "xar_bridge/conception_sample_passive_12004.hpp"
#include "xar_bridge/conception_sample_passive_12004_serializer.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"
#include <cstring>

namespace xar::ck3_12004 {
namespace {
struct FixtureState {
  std::array<std::byte, 0x20> first{}, second{};
  std::array<std::uint32_t,2> state{UINT32_MAX, 0xA5A55A5A};
  std::array<std::uint32_t,2> other_state{1,2};
  ConceptionSampleParentScope12004 parent{};
  std::int64_t result = 10000000;
  std::int64_t received_lower = -1, received_upper = -1;
  std::uintptr_t received_receiver = 0;
  std::uint32_t calls = 0, deliveries = 0;
  bool fail_state_read = false, end_parent = false, change_generation = false;
  std::optional<ConceptionSampleObservation12004> delivered;
};
FixtureState *g_fixture = nullptr;
void StoreId(std::array<std::byte,0x20> &character, std::uint32_t id) noexcept {
  constexpr std::uint32_t magic = 0x43686172;
  std::memcpy(character.data()+0x18, &id, sizeof(id));
  std::memcpy(character.data()+0x1C, &magic, sizeof(magic));
}
bool Parent(void *, ConceptionSampleParentScope12004 &out) noexcept {
  out = g_fixture->parent;
  return out.active;
}
bool Read(void *, const void *address, void *out, std::size_t size) noexcept {
  if (g_fixture->fail_state_read && address == g_fixture->state.data()) return false;
  std::memcpy(out,address,size);
  return true;
}
void Delivered(void *, const ConceptionSampleObservation12004 &event) noexcept {
  ++g_fixture->deliveries;
  g_fixture->delivered = event;
}
std::int64_t __fastcall Original(void *receiver, std::int64_t lower,
                                 std::int64_t upper) {
  ++g_fixture->calls;
  g_fixture->received_lower = lower;
  g_fixture->received_upper = upper;
  g_fixture->received_receiver = reinterpret_cast<std::uintptr_t>(receiver);
  auto *state = static_cast<std::uint32_t *>(receiver);
  state[0] += 2U;
  if (g_fixture->end_parent) g_fixture->parent.active = false;
  if (g_fixture->change_generation) StoreId(g_fixture->first, 0x12340011);
  // A supplied typed-fixture return. No helper body, mix, seed or draw executes.
  return g_fixture->result;
}
void NewParent(FixtureState &fixture) noexcept {
  const auto coordinate = NextPersonNaturalLineageEvent12004();
  fixture.parent.active = true;
  fixture.parent.parent_scope_id = coordinate.sequence;
  fixture.parent.process_clock = coordinate.sequence;
  fixture.parent.clock_identity = coordinate.clock_identity;
  fixture.parent.thread_id = GetCurrentThreadId();
  fixture.parent.first_character = reinterpret_cast<std::uintptr_t>(fixture.first.data());
  fixture.parent.second_character = reinterpret_cast<std::uintptr_t>(fixture.second.data());
  fixture.parent.first_full_id = 0x12340010;
  fixture.parent.second_full_id = 0x56780020;
  fixture.parent.sample_receiver = reinterpret_cast<std::uintptr_t>(fixture.state.data());
  StoreId(fixture.first, fixture.parent.first_full_id);
  StoreId(fixture.second, fixture.parent.second_full_id);
}
void AbsoluteJump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t,6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(destination,prefix.data(),prefix.size());
  std::memcpy(destination+prefix.size(),&target,sizeof(target));
}
// New instrumented-entry transport test. The owned fake continuation jumps to
// the typed Original; no RNG instructions or prior241B helper qualification run.
bool ExerciseActualRbxThunk(FixtureState &fixture,
                            ConceptionSampleBindings12004 bindings) noexcept {
  auto *owned = static_cast<std::uint8_t *>(VirtualAlloc(nullptr,256,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if (!owned) return false;
  constexpr std::array<std::uint8_t,15> anchor{
      0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18};
  std::memcpy(owned,anchor.data(),anchor.size());
  AbsoluteJump(owned+anchor.size(),reinterpret_cast<std::uintptr_t>(&Original));
  auto *caller = owned+64;
  // Preserve RBX and provide native32B shadow space. RCX/RDX/R8 remain incoming.
  constexpr std::array<std::uint8_t,7> before_threshold{0x53,0x48,0x83,0xEC,0x20,0x48,0xBB};
  std::memcpy(caller,before_threshold.data(),before_threshold.size());
  constexpr std::int64_t threshold = 0x100000001LL;
  std::memcpy(caller+7,&threshold,sizeof(threshold));
  constexpr std::array<std::uint8_t,8> call_indirect{0xFF,0x15,0x02,0,0,0,0xEB,0x08};
  std::memcpy(caller+15,call_indirect.data(),call_indirect.size());
  const auto target = reinterpret_cast<std::uintptr_t>(owned);
  std::memcpy(caller+23,&target,sizeof(target));
  constexpr std::array<std::uint8_t,6> epilogue{0x48,0x83,0xC4,0x20,0x5B,0xC3};
  std::memcpy(caller+31,epilogue.data(),epilogue.size());
  bindings.image_base = reinterpret_cast<std::uintptr_t>(caller+21) -
      kConceptionSampleReturnRva12004;
  DWORD old = 0;
  if (!VirtualProtect(owned,256,PAGE_EXECUTE_READ,&old) ||
      !FlushInstructionCache(GetCurrentProcess(),owned,256)) {
    VirtualFree(owned,0,MEM_RELEASE);
    return false;
  }
  ConceptionSampleInstallEnvironment12004 environment{};
  environment.primary_thread_suspended_proven = true; // This buffer is owned and uncalled.
  environment.bindings = bindings;
  environment.callback_target_override = target;
  ConceptionSampleDetourState12004 detour{};
  if (!InstallConceptionSamplePassive12004(detour,environment,kConceptionSampleSourcePin12004)) {
    VirtualFree(owned,0,MEM_RELEASE);
    return false;
  }
  const auto *entry = static_cast<const std::uint8_t *>(detour.entry_thunk);
  const bool encoding = entry && entry[0] == 0x49 && entry[1] == 0x89 &&
      entry[2] == 0xD9 && entry[3] == 0xFF && entry[4] == 0x25;
  const auto previous_calls = fixture.calls;
  const auto native_caller = reinterpret_cast<ConceptionSampleOriginal12004>(caller);
  const std::int64_t returned = native_caller(fixture.state.data(),0,10000000);
  const bool captured = encoding && returned == fixture.result &&
      fixture.calls == previous_calls+1 && fixture.delivered &&
      fixture.delivered->threshold_at_sample == threshold &&
      fixture.delivered->threshold_capture_ready && fixture.delivered->causal_sample_ready &&
      fixture.delivered->comparison_at_sample_passed == true &&
      fixture.received_lower == 0 && fixture.received_upper == 10000000 &&
      fixture.received_receiver == reinterpret_cast<std::uintptr_t>(fixture.state.data());
  const bool uninstalled = UninstallConceptionSamplePassive12004(detour,true);
  const bool restored = std::memcmp(owned,anchor.data(),anchor.size()) == 0;
  VirtualFree(owned,0,MEM_RELEASE);
  return captured && uninstalled && restored;
}
} // namespace

// Invoked once by the new connected19b/18b compound, not a separate legacy run.
bool RunConceptionSamplePassiveFixture12004() noexcept {
  FixtureState fixture{};
  g_fixture = &fixture;
  NewParent(fixture);
  auto bindings = BindConceptionSampleImage12004(0x140000000, kConceptionSampleSourcePin12004);
  bindings.read_memory = &Read;
  bindings.read_parent = &Parent;
  bindings.child_return = &Delivered;
  if (!InitializeConceptionSampleFixture12004(bindings, &Original)) return false;
  const auto invoke = [&](std::uintptr_t rva = kConceptionSampleReturnRva12004,
                          void *receiver = nullptr, std::int64_t lower = 0,
                          std::int64_t upper = 10000000,
                          std::optional<std::int64_t> threshold = std::int64_t{10000000}) {
    const auto previous_calls = fixture.calls;
    const auto returned = InvokeConceptionSampleFixture12004(rva,
        receiver ? receiver : fixture.state.data(), lower, upper, threshold);
    return returned == fixture.result && fixture.calls == previous_calls + 1 &&
        fixture.received_lower == lower && fixture.received_upper == upper &&
        fixture.received_receiver == reinterpret_cast<std::uintptr_t>(
            receiver ? receiver : fixture.state.data());
  };
  if (!invoke() || fixture.deliveries != 1 || !fixture.delivered ||
      !fixture.delivered->causal_sample_ready || fixture.state[0] != 1 ||
      fixture.state[1] != 0xA5A55A5A ||
      (*fixture.delivered->state_before)[0] != UINT32_MAX ||
      (*fixture.delivered->state_after)[0] != 1 ||
      fixture.delivered->returned_rax != 10000000 ||
      !fixture.delivered->threshold_capture_ready ||
      fixture.delivered->comparison_at_sample_passed != false) return false;
  const auto retained = ReadConceptionSampleObservations12004(
      fixture.parent.clock_identity, fixture.parent.parent_scope_id);
  const auto calls_before_query = fixture.calls;
  std::string json;
  if (!retained || retained->events.size() != 1) return false;
  AppendConceptionSampleObservations12004(json, *retained);
  if (fixture.calls != calls_before_query ||
      json.find("\"loaded_scalar_reconstruction\":null") == std::string::npos ||
      json.find("\"state_before_2dword\":[4294967295,2779077210]") == std::string::npos)
    return false;
  // Every filter miss still forwards once, without admitting an M7 child record.
  const auto deliveries_before_misses = fixture.deliveries;
  if (!invoke(kConceptionSampleReturnRva12004+1)) return false;
  fixture.parent.active = false;
  if (!invoke()) return false;
  NewParent(fixture);
  fixture.parent.thread_id ^= 0x80000000U;
  if (!invoke()) return false;
  NewParent(fixture);
  StoreId(fixture.first, 0x12340011);
  if (!invoke()) return false;
  NewParent(fixture);
  if (!invoke(kConceptionSampleReturnRva12004, fixture.other_state.data()) ||
      !invoke(kConceptionSampleReturnRva12004, nullptr, -1,10000000) ||
      fixture.deliveries != deliveries_before_misses) return false;
  // Failed state capture preserves the actual return and reports unavailable input.
  NewParent(fixture);
  fixture.fail_state_read = true;
  if (!invoke() || !fixture.delivered || fixture.delivered->state_before ||
      fixture.delivered->state_after || fixture.delivered->causal_sample_ready)
    return false;
  fixture.fail_state_read = false;
  // Full signed64 transport must not truncate or accept an out-of-domain fixture.
  NewParent(fixture);
  fixture.result = -0x100000001LL;
  if (!invoke() || fixture.delivered->returned_rax != fixture.result ||
      fixture.delivered->causal_sample_ready) return false;
  // Parent expiry and generation replacement during original return do not join.
  NewParent(fixture);
  fixture.result = 123;
  fixture.end_parent = true;
  if (!invoke() || fixture.delivered->parent_extent_and_generation_unchanged ||
      fixture.delivered->causal_sample_ready) return false;
  fixture.end_parent = false;
  NewParent(fixture);
  fixture.change_generation = true;
  if (!invoke() || fixture.delivered->causal_sample_ready) return false;
  fixture.change_generation = false;
  NewParent(fixture);
  if (!ExerciseActualRbxThunk(fixture,bindings)) return false;
  g_fixture = nullptr;
  return true;
}
} // namespace xar::ck3_12004
