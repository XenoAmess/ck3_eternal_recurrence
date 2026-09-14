#include "xar_bridge/marriage_alliance_readback_adapter_v1.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;

namespace {

const void *g_subject = nullptr;
const void *g_candidate = nullptr;
bool g_forward = false;
bool g_reverse = false;
std::uint32_t g_calls = 0;

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool IsAlliedTo(const void *subject, const void *target) {
  ++g_calls;
  if (subject == g_subject && target == g_candidate) return g_forward;
  if (subject == g_candidate && target == g_subject) return g_reverse;
  assert(false);
  return false;
}

void Initialize(bridge::MarriageAllianceReadbackStateV1 &state) {
  auto &env = state.environment;
  env.module_base = 1;
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.offline_fixture = true;
  env.read_memory = &ReadMemory;
  env.is_allied_to = &IsAlliedTo;
}

void TestBindingConfigurationAndBilateralRead() {
  const auto bound = bridge::BindMarriageAllianceReadbackEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  assert(reinterpret_cast<std::uintptr_t>(bound.is_allied_to) ==
         0x10000000U + bridge::kMarriageCharacterIsAlliedToRvaV1);

  std::uint64_t subject = 1;
  std::uint64_t candidate = 2;
  g_subject = &subject;
  g_candidate = &candidate;
  g_forward = true;
  g_reverse = false;
  g_calls = 0;
  bridge::MarriageAllianceReadbackStateV1 state{};
  Initialize(state);
  bridge::MarriageProposalNativeBinderStateV1 binder{};
  assert(bridge::ConfigureMarriageAllianceReadbackV1(state, binder));
  assert(binder.environment.alliance_readback_certified &&
         binder.environment.alliance_context == &state &&
         binder.environment.read_alliance_pair ==
             &bridge::ReadMarriageAlliancePairExactV1);
  bool forward = false;
  bool reverse = false;
  assert(bridge::ReadMarriageAlliancePairExactV1(
      &state, reinterpret_cast<std::uintptr_t>(&subject),
      reinterpret_cast<std::uintptr_t>(&candidate), forward, reverse));
  assert(forward && !reverse && g_calls == 2);
}

void TestInvalidInputAndShaFailClosed() {
  bridge::MarriageAllianceReadbackStateV1 state{};
  Initialize(state);
  bool forward = true;
  bool reverse = true;
  assert(!bridge::ReadMarriageAlliancePairExactV1(
      &state, 1, 1, forward, reverse));
  assert(!forward && !reverse);
  assert(bridge::ReadMarriageAllianceReadbackFailureV1(state) ==
         bridge::MarriageAllianceReadbackFailureV1::invalid_input);
  state.environment.admitted_executable_sha256 = "wrong";
  assert(!bridge::ReadMarriageAlliancePairExactV1(
      &state, 1, 2, forward, reverse));
  assert(bridge::ReadMarriageAllianceReadbackFailureV1(state) ==
         bridge::MarriageAllianceReadbackFailureV1::
             exact_build_not_admitted);
}

} // namespace

int main() {
  TestBindingConfigurationAndBilateralRead();
  TestInvalidInputAndShaFailClosed();
  std::cout << "marriage alliance readback adapter v1 tests passed\n";
  return 0;
}
