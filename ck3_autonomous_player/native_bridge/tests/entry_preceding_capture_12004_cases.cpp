#include "xar_bridge/entry_preceding_capture_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x10000000;
constexpr std::uintptr_t kBits = 0xA5A55A5A12345678ULL;
constexpr std::uint32_t kFullId = 0xAB000123U;
constexpr std::array<std::uint8_t, 15> kAnchor{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,
    0x48,0x89,0x74,0x24,0x18};

template<class T> void Write(std::array<std::uint8_t, 0x700> &memory,
                             std::size_t offset, T value) {
  std::memcpy(memory.data() + offset, &value, sizeof(value));
}
void Emit64(std::vector<std::uint8_t> &code, std::uint64_t value) {
  for (unsigned i = 0; i != 8; ++i)
    code.push_back(static_cast<std::uint8_t>(value >> (i * 8)));
}
void *Target(std::uint64_t &count, bool change_id) {
  std::vector<std::uint8_t> code(kAnchor.begin(), kAnchor.end());
  code.insert(code.end(), {0x49,0xBA});
  Emit64(code, reinterpret_cast<std::uintptr_t>(&count));
  code.insert(code.end(), {0x49,0xFF,0x02}); // INC QWORD[R10].
  if (change_id) code.insert(code.end(), {0xC7,0x41,0x08,0x23,0x01,0,0xAC});
  code.insert(code.end(), {0x48,0xB8}); Emit64(code, kBits);
  code.insert(code.end(), {
      0x48,0x8B,0x5C,0x24,0x08,0x48,0x8B,0x6C,0x24,0x10,
      0x48,0x8B,0x74,0x24,0x18,0xC3});
  auto *target = VirtualAlloc(nullptr, 128, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (!target) return nullptr;
  std::memcpy(target, code.data(), code.size());
  DWORD old = 0;
  if (!VirtualProtect(target, 128, PAGE_EXECUTE_READ, &old) ||
      !FlushInstructionCache(GetCurrentProcess(), target, code.size())) {
    VirtualFree(target, 0, MEM_RELEASE); return nullptr;
  }
  return target;
}
bool FreeOnceFailure(void *context, void *address, std::size_t bytes, DWORD type) noexcept {
  auto &remaining = *static_cast<std::uint32_t *>(context);
  if (remaining != 0) { --remaining; return false; }
  return VirtualFree(address, bytes, type) != FALSE;
}
bool Check(bool value, const char *reason) {
  if (!value) std::cerr << "52c: " << reason << '\n';
  return value;
}
} // namespace

// Export only. The31c central connectedmain calls this once; no independent
// old family/Person/Entry fixture or main is provided.
bool RunEntryPrecedingCapture12004NewCases() {
  using namespace xar::ck3_12004;
  std::array<std::uint8_t, 0x700> combat{};
  Write(combat, 0x08, kFullId); Write(combat, 0x0C, std::uint32_t{0x436F6D62U});
  const auto identity = reinterpret_cast<std::uintptr_t>(combat.data());
  std::uintptr_t caller_slot_value = kBase + kEntryPrecedingReturnRva12004;
  const auto slot = reinterpret_cast<std::uintptr_t>(&caller_slot_value);
  std::uint64_t original_count = 0;
  auto *target = Target(original_count, false);
  if (!Check(target != nullptr, "owned executable target allocation")) return false;
  EntryPrecedingState12004 state;
  EntryPrecedingInstall12004 env;
  env.primary_thread_suspended_proven = true;
  env.offline_fixture = true;
  env.module_base = kBase;
  env.target_override = reinterpret_cast<std::uintptr_t>(target);
  env.bindings = BindEntryPrecedingCaptureImage12004(kBase, kEntryPrecedingExeSha12004);
  bool ok = Check(InstallEntryPrecedingCapture12004(state, env, kEntryPrecedingExeSha12004),
                  "source-qualified synthetic prologue install");
  if (!ok) { VirtualFree(target, 0, MEM_RELEASE); return false; }
  const auto produce = [&](std::uintptr_t return_rva = kEntryPrecedingReturnRva12004) {
    return InvokeEntryPrecedingCapture12004(combat.data(), kBase + return_rva, slot);
  };
  const auto claim = [&](std::uint32_t side) {
    return ClaimEntryPrecedingForFinalSide12004(side,
        identity + (side == 0 ? 0x20U : 0x368U),
        side == 0 ? 0x247AB17U : 0x247AB26U, slot,
        NextPersonNaturalLineageEvent12004());
  };

  // The installed native target itself enters the replacement, preserving
  // bits and one original execution; its unrelated real caller is retained.
  const auto natural = reinterpret_cast<EntryPrecedingOriginal12004>(target);
  ok &= Check(natural(combat.data()) == kBits && original_count == 1,
              "installed original once and high RAX bits");
  ok &= Check(!ReadCurrentEntryPrecedingCompletion12004(),
              "unrelated actual caller cannot publish final-stage token");
  ok &= Check(produce() == kBits && original_count == 2, "explicit same dispatcher original once");
  const auto completion = ReadCurrentEntryPrecedingCompletion12004();
  ok &= Check(completion && completion->identity_stable &&
      completion->combat_full_id_before == kFullId &&
      completion->combat_full_id_after == kFullId &&
      completion->original_returned && !completion->outer_invocation,
      "owned full generation and absent full outer invocation");
  const auto side0 = claim(0); const auto side1 = claim(1);
  ok &= Check(side0 && side1 && side0->record_sequence == side1->record_sequence &&
      !ReadCurrentEntryPrecedingCompletion12004(), "exact stack slot source-order both claims and consume");

  produce();
  ok &= Check(!claim(1) && !claim(0), "Side1 first invalidates prior-stage token");
  produce();
  ok &= Check(claim(0).has_value() && !claim(0) && !claim(1),
              "repeated Side0 cannot alias another outer invocation");
  produce();
  ok &= Check(!ClaimEntryPrecedingForFinalSide12004(0, identity + 0x20,
      0x247AB17U, slot + sizeof(std::uintptr_t), NextPersonNaturalLineageEvent12004()),
      "same Combat and near clock with different concrete caller frame is rejected");
  produce();
  ok &= Check(!ClaimEntryPrecedingForFinalSide12004(0, identity + 0x20,
      0x247AB26U, slot, NextPersonNaturalLineageEvent12004()), "wrong literal return rejected");
  produce();
  auto wrong_clock = NextPersonNaturalLineageEvent12004(); ++wrong_clock.clock_identity;
  ok &= Check(!ClaimEntryPrecedingForFinalSide12004(0, identity + 0x20,
      0x247AB17U, slot, wrong_clock), "foreign clock cannot compare sequence");
  produce();
  auto changed_thread = NextPersonNaturalLineageEvent12004();
  changed_thread.thread_id = changed_thread.thread_id.value_or(0U) + 1U;
  ok &= Check(!ClaimEntryPrecedingForFinalSide12004(0, identity + 0x20,
      0x247AB17U, slot, changed_thread), "foreign thread cannot claim");
  produce();
  bool other_thread_claimed = false;
  std::thread other([&]() { other_thread_claimed = claim(0).has_value(); }); other.join();
  ok &= Check(!other_thread_claimed && claim(0).has_value() && claim(1).has_value(),
              "actual thread-local token remains independent");
  produce(); Write(combat, 0x08, std::uint32_t{0xAC000123U});
  ok &= Check(!claim(0), "generation mismatch with same low24 ID rejected");
  Write(combat, 0x08, kFullId);
  produce(0x247AB08U);
  ok &= Check(!ReadCurrentEntryPrecedingCompletion12004(), "only actual preceding return publishes");
  Write(combat, 0x0C, std::uint32_t{0}); produce();
  ok &= Check(!ReadCurrentEntryPrecedingCompletion12004(), "unread/invalid identity independent missing token");
  Write(combat, 0x0C, std::uint32_t{0x436F6D62U});
  produce();
  const EntryPrecedingCombatOwner12004 owner{identity, kFullId};
  const auto filtered = CollectEntryPrecedingCaptureForCombats12004(std::span(&owner, 1));
  const auto wire = SerializeEntryPrecedingCapture12004(filtered);
  ok &= Check(filtered.request_filtered && !filtered.records.empty() &&
      wire.find("\"outer_invocation\":null") != std::string::npos &&
      wire.find("\"full_entry\":false") != std::string::npos &&
      CollectEntryPrecedingCaptureForCombats12004({}).records.empty(),
      "immutable filtered wire leaves complete outer unknown and empty filter empty");
  ok &= Check(UninstallEntryPrecedingCapture12004(state, true), "new owned target uninstall");
  VirtualFree(target, 0, MEM_RELEASE);

  // One independent original mutates full generation during this own call.
  original_count = 0; target = Target(original_count, true);
  if (!Check(target != nullptr, "mutation target allocation")) return false;
  EntryPrecedingState12004 mutation;
  env.target_override = reinterpret_cast<std::uintptr_t>(target);
  ok &= Check(InstallEntryPrecedingCapture12004(mutation, env, kEntryPrecedingExeSha12004),
              "mutation install");
  const auto mutated_bits = InvokeEntryPrecedingCapture12004(combat.data(), caller_slot_value, slot);
  const auto after = ReadEntryPrecedingCapture12004();
  ok &= Check(mutated_bits == kBits && original_count == 1 &&
      !ReadCurrentEntryPrecedingCompletion12004() && !after.records.empty() &&
      !after.records.back().identity_stable &&
      after.records.back().combat_full_id_before == kFullId &&
      after.records.back().combat_full_id_after == std::uint32_t{0xAC000123U},
      "post-original full generation mutation retained without publishing token");
  ok &= Check(UninstallEntryPrecedingCapture12004(mutation, true), "mutation uninstall");
  VirtualFree(target, 0, MEM_RELEASE);
  // A detached failed-free allocation must not clear a later active hook.
  Write(combat, 0x08, kFullId);
  std::uint32_t fail_free_once = 1;
  std::uint64_t orphan_original_count = 0, later_original_count = 0;
  auto *orphan_target = Target(orphan_original_count, false);
  auto *later_target = Target(later_original_count, false);
  if (!Check(orphan_target && later_target, "orphan/later target allocations")) return false;
  EntryPrecedingState12004 orphan_state, later_state;
  env.target_override = reinterpret_cast<std::uintptr_t>(orphan_target);
  env.memory_context = &fail_free_once;
  env.virtual_free_override = FreeOnceFailure;
  ok &= Check(InstallEntryPrecedingCapture12004(orphan_state, env, kEntryPrecedingExeSha12004),
              "orphan setup install");
  ok &= Check(!UninstallEntryPrecedingCapture12004(orphan_state, true) &&
      orphan_state.installed.load() == 0 && orphan_state.trampoline != nullptr,
      "failed free keeps detached orphan only");
  env.target_override = reinterpret_cast<std::uintptr_t>(later_target);
  env.memory_context = nullptr;
  env.virtual_free_override = nullptr;
  ok &= Check(InstallEntryPrecedingCapture12004(later_state, env, kEntryPrecedingExeSha12004),
              "later active setup");
  const auto later_call = reinterpret_cast<EntryPrecedingOriginal12004>(later_target);
  ok &= Check(later_call(combat.data()) == kBits && later_original_count == 1,
              "later active owns original before orphan disposal");
  ok &= Check(UninstallEntryPrecedingCapture12004(orphan_state, true) &&
      orphan_state.trampoline == nullptr && ReadEntryPrecedingCapture12004().installed &&
      later_call(combat.data()) == kBits && later_original_count == 2,
      "orphan free leaves later active globals and original intact");
  ok &= Check(UninstallEntryPrecedingCapture12004(later_state, true), "later active teardown");
  VirtualFree(orphan_target, 0, MEM_RELEASE);
  VirtualFree(later_target, 0, MEM_RELEASE);
  std::cout << "{\"entry_preceding_new_cases\":16,\"outer_invocation\":null,\"full_entry\":false}\n";
  return ok;
}
