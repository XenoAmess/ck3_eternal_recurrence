#include "xar_bridge/council_replacement_fireability_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace {

constexpr std::int32_t kIncumbentId = 33433;
constexpr std::int32_t kTaskId = 7159;

void Require(bool condition) {
  if (!condition) throw std::runtime_error("Council fireability fixture failed");
}

struct Fixture {
  int calls = 0;
  bool native_result = true;
};

bool CanConfirm(void *opaque, const void *confirmation) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.calls;
  std::int32_t incumbent = -1;
  std::int32_t task = -1;
  const auto *bytes = static_cast<const std::byte *>(confirmation);
  std::memcpy(&incumbent, bytes + 0x160, sizeof(incumbent));
  std::memcpy(&task, bytes + 0x164, sizeof(task));
  return incumbent == kIncumbentId && task == kTaskId &&
         fixture.native_result;
}

xar::ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1 Environment() {
  xar::ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1 value{};
  value.exact_build_admitted = true;
  value.admitted_executable_sha256 =
      xar::ck3_11906::kCouncilAssignCouncillorExecutableSha256V1;
  value.native_command_abi_certified = true;
  value.private_candidate_admitted = true;
  value.offline_fixture = true;
  value.current_thread_id = 7;
  value.application_main_thread_id = 7;
  return value;
}

} // namespace

int main() {
  using xar::ck3_11906::EvaluateCouncilReplacementFireabilityV1;
  Fixture fixture{};
  bool can_fire = false;
  const auto environment = Environment();
  Require(EvaluateCouncilReplacementFireabilityV1(
      environment, kIncumbentId, kTaskId, can_fire, &CanConfirm, &fixture));
  Require(can_fire && fixture.calls == 1);

  fixture.native_result = false;
  Require(EvaluateCouncilReplacementFireabilityV1(
      environment, kIncumbentId, kTaskId, can_fire, &CanConfirm, &fixture));
  Require(!can_fire && fixture.calls == 2);

  Require(!EvaluateCouncilReplacementFireabilityV1(
      environment, -1, kTaskId, can_fire, &CanConfirm, &fixture));
  Require(!can_fire && fixture.calls == 2);
  auto wrong_build = environment;
  wrong_build.admitted_executable_sha256 = "wrong build";
  Require(!EvaluateCouncilReplacementFireabilityV1(
      wrong_build, kIncumbentId, kTaskId, can_fire, &CanConfirm, &fixture));
  Require(!can_fire && fixture.calls == 2);
  auto production = environment;
  production.offline_fixture = false;
  production.module_base = 0x140000000ULL;
  Require(!EvaluateCouncilReplacementFireabilityV1(
      production, kIncumbentId, kTaskId, can_fire, &CanConfirm, &fixture));
  Require(!can_fire && fixture.calls == 2);
}
