#include "xar_bridge/combat_phase_event_trace_detour_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

constexpr std::array<std::uint8_t, 15> kSchedulePrologue{
    0x4C, 0x89, 0x44, 0x24, 0x18, 0x48, 0x89, 0x54,
    0x24, 0x10, 0x53, 0x56, 0x57, 0x41, 0x55};
constexpr std::array<std::uint8_t, 15> kFirePrologue{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
    0x24, 0x10, 0x48, 0x89, 0x7C, 0x24, 0x18};
constexpr std::array<std::uint8_t, 5> kScheduleSide0Call{
    0xE8, 0xBC, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kScheduleSide1Call{
    0xE8, 0xA4, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kFireSide0Call{
    0xE8, 0xF9, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireSide1Call{
    0xE8, 0xF1, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireTailJump{
    0xE9, 0xAD, 0xF5, 0xFF, 0xFF};

bool Fail(std::string_view reason) {
  std::cerr << reason << '\n';
  return false;
}

struct FixtureMemory {
  void *schedule_page = nullptr;
  void *fire_page = nullptr;
  bool fail_fire_patch_protection = false;
  bool fail_allocation = false;
  std::uintptr_t fire_target = 0;
  std::uint32_t live_allocations = 0;

  ~FixtureMemory() {
    if (schedule_page != nullptr) {
      VirtualFree(schedule_page, 0, MEM_RELEASE);
    }
    if (fire_page != nullptr) {
      VirtualFree(fire_page, 0, MEM_RELEASE);
    }
  }
};

void *FixtureAlloc(void *raw, std::size_t size, DWORD type,
                   DWORD protection) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(raw);
  if (fixture.fail_allocation) {
    return nullptr;
  }
  void *const result = VirtualAlloc(nullptr, size, type, protection);
  if (result != nullptr) {
    ++fixture.live_allocations;
  }
  return result;
}

bool FixtureFree(void *raw, void *address, std::size_t size,
                 DWORD type) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(raw);
  const bool result = VirtualFree(address, size, type) != FALSE;
  if (result && fixture.live_allocations != 0) {
    --fixture.live_allocations;
  }
  return result;
}

bool FixtureProtect(void *raw, void *address, std::size_t size,
                    DWORD desired, DWORD &previous) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(raw);
  if (fixture.fail_fire_patch_protection &&
      reinterpret_cast<std::uintptr_t>(address) == fixture.fire_target &&
      desired == PAGE_EXECUTE_READWRITE) {
    previous = 0;
    return false;
  }
  previous = 0;
  return VirtualProtect(address, size, desired, &previous) != FALSE;
}

bool FixtureFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

struct Fixture {
  FixtureMemory memory{};
  std::array<std::uint8_t, 5> schedule_side0_call{kScheduleSide0Call};
  std::array<std::uint8_t, 5> schedule_side1_call{kScheduleSide1Call};
  std::array<std::uint8_t, 5> fire_side0_call{kFireSide0Call};
  std::array<std::uint8_t, 5> fire_side1_call{kFireSide1Call};
  std::array<std::uint8_t, 5> fire_tail_jump{kFireTailJump};
  CombatPhaseEventTraceDetourEnvironmentV1 environment{};

  Fixture() {
    SYSTEM_INFO information{};
    GetSystemInfo(&information);
    const auto page_size =
        static_cast<std::size_t>(information.dwPageSize);
    memory.schedule_page = VirtualAlloc(
        nullptr, page_size, MEM_RESERVE | MEM_COMMIT,
        PAGE_EXECUTE_READWRITE);
    memory.fire_page = VirtualAlloc(
        nullptr, page_size, MEM_RESERVE | MEM_COMMIT,
        PAGE_EXECUTE_READWRITE);
    if (memory.schedule_page == nullptr || memory.fire_page == nullptr) {
      return;
    }
    std::memcpy(memory.schedule_page, kSchedulePrologue.data(),
                kSchedulePrologue.size());
    std::memcpy(memory.fire_page, kFirePrologue.data(),
                kFirePrologue.size());
    DWORD ignored = 0;
    (void)VirtualProtect(memory.schedule_page, page_size,
                         PAGE_EXECUTE_READ, &ignored);
    (void)VirtualProtect(memory.fire_page, page_size,
                         PAGE_EXECUTE_READ, &ignored);
    memory.fire_target =
        reinterpret_cast<std::uintptr_t>(memory.fire_page);

    environment.exact_build_admitted = true;
    environment.managed_paused_quiescence_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x0000000140000000ULL;
    environment.schedule_target_override =
        reinterpret_cast<std::uintptr_t>(memory.schedule_page);
    environment.fire_target_override = memory.fire_target;
    environment.schedule_side0_call_override =
        reinterpret_cast<std::uintptr_t>(schedule_side0_call.data());
    environment.schedule_side1_call_override =
        reinterpret_cast<std::uintptr_t>(schedule_side1_call.data());
    environment.fire_side0_call_override =
        reinterpret_cast<std::uintptr_t>(fire_side0_call.data());
    environment.fire_side1_call_override =
        reinterpret_cast<std::uintptr_t>(fire_side1_call.data());
    environment.fire_tail_jump_override =
        reinterpret_cast<std::uintptr_t>(fire_tail_jump.data());
    environment.memory_context = &memory;
    environment.virtual_alloc_override = &FixtureAlloc;
    environment.virtual_free_override = &FixtureFree;
    environment.virtual_protect_override = &FixtureProtect;
    environment.flush_instruction_cache_override = &FixtureFlush;
  }
};

bool IsAbsoluteJumpTo(const void *storage, std::uintptr_t expected) {
  const auto *bytes = static_cast<const std::uint8_t *>(storage);
  constexpr std::array<std::uint8_t, 6> prefix{
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00};
  std::uintptr_t observed = 0;
  std::memcpy(&observed, bytes + prefix.size(), sizeof(observed));
  return std::memcmp(bytes, prefix.data(), prefix.size()) == 0 &&
         observed == expected;
}

bool InstallAndUninstall() {
  Fixture fixture;
  if (fixture.memory.schedule_page == nullptr ||
      fixture.memory.fire_page == nullptr) {
    return Fail("fixture executable pages unavailable");
  }
  CombatPhaseEventTraceDetourStateV1 state{};
  if (!InstallCombatPhaseEventTraceDetoursV1(state,
                                             fixture.environment)) {
    return Fail("detour install failed");
  }
  if (state.installed.load() != 1 || state.failure_flags.load() != 0 ||
      fixture.memory.live_allocations != 2 ||
      !IsAbsoluteJumpTo(
          fixture.memory.schedule_page,
          reinterpret_cast<std::uintptr_t>(
              &XarCombatPhaseEventScheduleHookV1)) ||
      !IsAbsoluteJumpTo(
          fixture.memory.fire_page,
          reinterpret_cast<std::uintptr_t>(&XarCombatPhaseEventFireHookV1)) ||
      !IsAbsoluteJumpTo(
          static_cast<const std::uint8_t *>(state.schedule_trampoline) +
              kCombatPhaseEventTraceDetourPatchBytesV1,
          state.schedule_target +
              kCombatPhaseEventTraceDetourPatchBytesV1) ||
      !IsAbsoluteJumpTo(
          static_cast<const std::uint8_t *>(state.fire_trampoline) +
              kCombatPhaseEventTraceDetourPatchBytesV1,
          state.fire_target +
              kCombatPhaseEventTraceDetourPatchBytesV1) ||
      std::memcmp(state.schedule_trampoline, kSchedulePrologue.data(),
                  kSchedulePrologue.size()) != 0 ||
      std::memcmp(state.fire_trampoline, kFirePrologue.data(),
                  kFirePrologue.size()) != 0) {
    return Fail("installed patch/trampoline mismatch");
  }
  if (!UninstallCombatPhaseEventTraceDetoursV1(state) ||
      state.installed.load() != 0 || fixture.memory.live_allocations != 0 ||
      std::memcmp(fixture.memory.schedule_page,
                  kSchedulePrologue.data(), kSchedulePrologue.size()) != 0 ||
      std::memcmp(fixture.memory.fire_page, kFirePrologue.data(),
                  kFirePrologue.size()) != 0) {
    return Fail("detour uninstall did not restore originals");
  }
  return true;
}

bool AdmissionAndRollbackFailures() {
  {
    Fixture fixture;
    fixture.environment.managed_paused_quiescence_proven = false;
    CombatPhaseEventTraceDetourStateV1 state{};
    if (InstallCombatPhaseEventTraceDetoursV1(state,
                                              fixture.environment) ||
        (state.failure_flags.load() &
         trace_detour_failure_paused_quiescence) == 0) {
      return Fail("unpaused install did not fail closed");
    }
  }
  {
    Fixture fixture;
    fixture.schedule_side0_call[0] = 0x90;
    CombatPhaseEventTraceDetourStateV1 state{};
    if (InstallCombatPhaseEventTraceDetoursV1(state,
                                              fixture.environment) ||
        (state.failure_flags.load() & trace_detour_failure_anchor) == 0 ||
        fixture.memory.live_allocations != 0) {
      return Fail("anchor mismatch did not fail before allocation");
    }
  }
  {
    Fixture fixture;
    fixture.memory.fail_allocation = true;
    CombatPhaseEventTraceDetourStateV1 state{};
    if (InstallCombatPhaseEventTraceDetoursV1(state,
                                              fixture.environment) ||
        (state.failure_flags.load() & trace_detour_failure_allocation) == 0 ||
        std::memcmp(fixture.memory.schedule_page,
                    kSchedulePrologue.data(), kSchedulePrologue.size()) != 0 ||
        std::memcmp(fixture.memory.fire_page, kFirePrologue.data(),
                    kFirePrologue.size()) != 0) {
      return Fail("allocation failure changed target bytes");
    }
  }
  {
    Fixture fixture;
    fixture.memory.fail_fire_patch_protection = true;
    CombatPhaseEventTraceDetourStateV1 state{};
    if (InstallCombatPhaseEventTraceDetoursV1(state,
                                              fixture.environment) ||
        (state.failure_flags.load() &
         trace_detour_failure_target_protection) == 0 ||
        fixture.memory.live_allocations != 0 ||
        std::memcmp(fixture.memory.schedule_page,
                    kSchedulePrologue.data(), kSchedulePrologue.size()) != 0 ||
        std::memcmp(fixture.memory.fire_page, kFirePrologue.data(),
                    kFirePrologue.size()) != 0) {
      return Fail("partial install did not roll schedule patch back");
    }
  }
  return true;
}

} // namespace

int main() {
  static_assert(kCombatPhaseEventTraceDetourPatchBytesV1 == 15);
  static_assert(kCombatPhaseEventTraceAbsoluteJumpBytesV1 == 14);
  return InstallAndUninstall() && AdmissionAndRollbackFailures() ? 0 : 1;
}
