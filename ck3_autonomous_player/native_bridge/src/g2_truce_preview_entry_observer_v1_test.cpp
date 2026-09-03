#include "xar_bridge/g2_truce_preview_entry_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>

namespace {

constexpr std::array<std::uint8_t,
                     xar::bridge::kG2TrucePreviewEntryPatchBytesV1> kAnchor{
    0x48, 0x8B, 0x02, 0x4D, 0x8B, 0xF0, 0x4C, 0x8B,
    0xD2, 0x48, 0x8B, 0xF9, 0x66, 0x83, 0x38, 0x04};

template <std::size_t N>
bool ContainsU64(const std::array<std::uint8_t, N> &bytes,
                 std::uint64_t value) {
  std::array<std::uint8_t, sizeof(value)> encoded{};
  std::memcpy(encoded.data(), &value, sizeof(value));
  return std::search(bytes.begin(), bytes.end(), encoded.begin(),
                     encoded.end()) != bytes.end();
}

} // namespace

int main() {
  using namespace xar::bridge;

  static_assert(!kG2TrucePreviewEntryObserverInstalledByDefaultV1);
  static_assert(kG2TrucePreviewEntryPatchRvaV1 == 0x2E87155);
  static_assert(kG2TrucePreviewEntryContinueRvaV1 == 0x2E87165);
  static_assert(kG2AddTruceEffectNormalVtableRvaV1 == 0x4461CA8);
  static_assert(kG2AddTruceEffectForcedVtableRvaV1 == 0x4461D70);

  G2TrucePreviewEntryObserverV1State denied{};
  G2TrucePreviewEntryObserverEnvironmentV1 denied_environment{};
  assert(!InstallG2TrucePreviewEntryObserverV1(denied, denied_environment));
  assert((denied.failure_flags.load() &
          g2_truce_preview_entry_observer_failure_exact_build) != 0);

  constexpr std::uintptr_t kSyntheticBase = 0x10000000;
  std::uintptr_t normal_object =
      kSyntheticBase + kG2AddTruceEffectNormalVtableRvaV1;
  std::uintptr_t forced_object =
      kSyntheticBase + kG2AddTruceEffectForcedVtableRvaV1;
  std::uintptr_t unrelated_object = kSyntheticBase + 0x1234;
  G2TrucePreviewEntryObserverV1State recorded{};
  recorded.module_base = kSyntheticBase;
  RecordG2TrucePreviewEntryV1(
      recorded, reinterpret_cast<std::uintptr_t>(&unrelated_object),
      0x2000, 0x3000);
  auto diagnostics = ReadG2TrucePreviewEntryObserverV1Diagnostics(recorded);
  assert(diagnostics.accepted_count == 0);
  assert(diagnostics.last_effect_this == 0);
  RecordG2TrucePreviewEntryV1(
      recorded, reinterpret_cast<std::uintptr_t>(&normal_object),
      0x2100, 0x3100);
  RecordG2TrucePreviewEntryV1(
      recorded, reinterpret_cast<std::uintptr_t>(&forced_object),
      0x2200, 0x3200);
  diagnostics = ReadG2TrucePreviewEntryObserverV1Diagnostics(recorded);
  assert(diagnostics.accepted_count == 2);
  assert(diagnostics.normal_effect_count == 1);
  assert(diagnostics.forced_effect_count == 1);
  assert(diagnostics.last_effect_this ==
         reinterpret_cast<std::uintptr_t>(&forced_object));
  assert(diagnostics.last_effect_vtable == forced_object);
  assert(diagnostics.last_preview_context == 0x2200);
  assert(diagnostics.last_preview_collector == 0x3200);

  void *target = VirtualAlloc(nullptr, 64, MEM_RESERVE | MEM_COMMIT,
                              PAGE_EXECUTE_READWRITE);
  assert(target != nullptr);
  std::memcpy(target, kAnchor.data(), kAnchor.size());
  G2TrucePreviewEntryObserverV1State installed{};
  G2TrucePreviewEntryObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = kSyntheticBase;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(target);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(target) + kAnchor.size();
  assert(InstallG2TrucePreviewEntryObserverV1(installed, environment));
  diagnostics = ReadG2TrucePreviewEntryObserverV1Diagnostics(installed);
  assert(diagnostics.installed);
  const auto *patch = static_cast<const std::uint8_t *>(target);
  assert(patch[0] == 0xFF && patch[1] == 0x25);
  std::array<std::uint8_t, 224> stub{};
  std::memcpy(stub.data(), installed.stub, stub.size());
  assert(ContainsU64(stub, environment.continue_target_override));
  assert(std::search(stub.begin(), stub.end(), kAnchor.begin(), kAnchor.end()) !=
         stub.end());
  assert(UninstallG2TrucePreviewEntryObserverV1(installed));
  assert(std::memcmp(target, kAnchor.data(), kAnchor.size()) == 0);
  assert(VirtualFree(target, 0, MEM_RELEASE) != FALSE);

  return 0;
}
