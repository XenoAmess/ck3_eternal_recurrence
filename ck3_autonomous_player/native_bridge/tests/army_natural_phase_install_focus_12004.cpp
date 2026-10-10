#include "xar_bridge/army_natural_phase_observer_12004.hpp"

#include <array>
#include <cstring>
#include <stdexcept>
#include <windows.h>

namespace {
using namespace xar::ck3_12004;
std::byte *owned_code = nullptr;
constexpr std::size_t kCodeBytes = 8192;
constexpr std::uintptr_t kSyntheticRax = 0xEEDDCCBBAA998877ULL;
std::uintptr_t owned_base = 0;
std::array<std::byte, 0x200> owned_manager{};
std::array<std::byte, 0xD0> owned_state{};
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
bool OwnedRead(void *, std::uintptr_t address, void *out, std::size_t bytes) noexcept {
  if (address == owned_base + 0x5C68C50 && bytes == sizeof(std::uintptr_t)) {
    const auto state = reinterpret_cast<std::uintptr_t>(owned_state.data());
    std::memcpy(out, &state, bytes); return true;
  }
  const auto in = [&](std::uintptr_t start, std::size_t length) {
    return address >= start && address - start <= length && bytes <= length - (address - start);
  };
  if (!in(reinterpret_cast<std::uintptr_t>(owned_code), kCodeBytes) &&
      !in(reinterpret_cast<std::uintptr_t>(owned_manager.data()), sizeof owned_manager) &&
      !in(reinterpret_cast<std::uintptr_t>(owned_state.data()), sizeof owned_state)) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), bytes); return true;
}
void Emit(std::byte *target, const std::uint8_t *prefix, std::size_t prefix_size,
    const std::uint8_t *suffix, std::size_t suffix_size) {
  std::memcpy(target, prefix, prefix_size); target += prefix_size;
  *target++ = std::byte{0x48}; *target++ = std::byte{0xB8};
  std::memcpy(target, &kSyntheticRax, sizeof kSyntheticRax); target += sizeof kSyntheticRax;
  std::memcpy(target, suffix, suffix_size);
}
} // namespace

void RunArmyNaturalPhaseInstallFocus12004() {
  using namespace xar::ck3_12004;
  ArmyNaturalPhaseObserverState12004 rejected{};
  ArmyNaturalPhaseObserverEnvironment12004 env{};
  Check(!InstallArmyNaturalPhaseObserver12004(env, rejected), "startup requires exact build/read/suspension");
  owned_code = static_cast<std::byte *>(VirtualAlloc(nullptr, kCodeBytes,
      MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
  Check(owned_code != nullptr, "owned callback code allocation");
  owned_base = reinterpret_cast<std::uintptr_t>(owned_code) - 0x2A99000;
  const std::uint8_t pre_prefix[]{0x48,0x89,0x4c,0x24,0x08,0x55,0x53,0x56,0x57,
      0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
  const std::uint8_t pre_suffix[]{0x41,0x5f,0x41,0x5e,0x41,0x5d,0x41,0x5c,0x5f,0x5e,0x5b,0x5d,0xc3};
  // Post's source-proved19B displaced prefix ends before its push R15.
  const std::uint8_t post_prefix[]{0x48,0x89,0x5c,0x24,0x20,0x48,0x89,0x4c,0x24,0x08,
      0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
  const std::uint8_t post_suffix[]{0x48,0x8b,0x5c,0x24,0x58,0x41,0x5f,0x41,0x5e,
      0x41,0x5d,0x41,0x5c,0x5f,0x5e,0x5d,0xc3};
  Emit(owned_code + 0xDA0, pre_prefix, sizeof pre_prefix, pre_suffix, sizeof pre_suffix);
  Emit(owned_code + 0x1570, post_prefix, sizeof post_prefix, post_suffix, sizeof post_suffix);
  DWORD previous = 0;
  Check(VirtualProtect(owned_code, kCodeBytes, PAGE_EXECUTE_READ, &previous) != FALSE &&
      FlushInstructionCache(GetCurrentProcess(), owned_code, kCodeBytes) != FALSE,
      "owned source prologue executable");
  const auto pre = reinterpret_cast<ArmyNaturalPhaseOriginal12004>(owned_code + 0xDA0);
  const auto post = reinterpret_cast<ArmyNaturalPhaseOriginal12004>(owned_code + 0x1570);
  void *secondary = owned_manager.data() + 8;
  Check(pre(secondary) == kSyntheticRax && post(secondary) == kSyntheticRax, "owned original ABI baseline");
  env.module_base = owned_base;
  env.actual_exe_sha256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  env.read = OwnedRead;
  env.primary_thread_suspended_proven = true;
  ArmyNaturalPhaseObserverState12004 installed{};
  Check(InstallArmyNaturalPhaseObserver12004(env, installed) && installed.source_bytes_verified &&
      installed.pre_date_installed && installed.post_date_installed, "source-verified installed entry wrappers");
  const auto prior_count = ReadArmyNaturalPhaseJournal12004().size();
  Check(pre(secondary) == kSyntheticRax && post(secondary) == kSyntheticRax,
      "installed original once opaque RAX preserved");
  const auto records = ReadArmyNaturalPhaseJournal12004();
  const auto expected_count = prior_count <= std::size_t{62} ? prior_count + 2 : std::size_t{64};
  Check(records.size() == expected_count && records.size() >= std::size_t{2}, "installed records retained");
  const auto &pre_record = records[records.size() - 2];
  const auto &post_record = records.back();
  Check(pre_record.scope.actual_entry_rva == kArmyNaturalPreDateRva12004 &&
      post_record.scope.actual_entry_rva == kArmyNaturalPostDateRva12004 &&
      pre_record.original_returned && post_record.original_returned &&
      post_record.scope.entry_event.sequence > pre_record.returned_event.sequence,
      "installed actual entry facts in one process clock domain");
  Check(!pre_record.scope.session_identity && !post_record.scope.session_identity,
      "installer does not invent a loaded-game epoch");
  ArmyNaturalPhaseObserverState12004 duplicate{};
  Check(!InstallArmyNaturalPhaseObserver12004(env, duplicate), "one install owner per process");
  // Backing code and trampolines deliberately remain valid until this process exits.
}
