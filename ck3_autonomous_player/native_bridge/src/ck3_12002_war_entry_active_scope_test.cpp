#include "xar_bridge/ck3_12002_war_entry.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
namespace build = xar::ck3_12002;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kTarget = 30097;
constexpr std::int32_t kEffective = 40001;

template <typename Buffer, typename Value>
void Put(Buffer &buffer, std::size_t offset, Value value) {
  if (offset + sizeof(value) > buffer.size()) std::abort();
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x1E0> actor{}, target{}, effective{}, fallback{};
  std::array<std::byte, 0x320> actor_power{}, target_power{}, effective_power{};
  std::array<std::byte, 0x30> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>(50'002 * 0x10);
  std::array<std::byte, 0xA8> game_state{};
  void *game_state_slot = game_state.data();
  void *storage_slot = storage.data();
  void *fallback_slot = fallback.data();
  void *dependency_slot = game_state.data();
  xar::game::WarEntryAssessmentFrameV1 frame{
      5, 53'236'608, true, true, true, kActor, {}, {30097, 32750}};
  bool owning_thread = true;
  bool bad_ratio = false;
  bool scratch_was_zero = true;
  std::int32_t build_calls = 0;
  std::int32_t native_calls = 0;
  std::int32_t network_calls = 0;

  Fixture() {
    const auto initialize = [this](auto &character, auto &power,
                                   std::int32_t id, std::int64_t power_raw) {
      Put(character, 0x18, id);
      Put(character, 0x1C0, static_cast<void *>(power.data()));
      Put(character, 0x1D0, static_cast<void *>(nullptr));
      // The old death field is now another component. Its nonnull value
      // must not cause the migrated reader to mark an alive actor dead.
      Put(character, 0x1C8, static_cast<void *>(fallback.data()));
      Put(power, 0x308, power_raw);
      Put(slots, (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) * 0x10 + 8,
          static_cast<void *>(character.data()));
    };
    initialize(actor, actor_power, kActor, 1'200'000);
    initialize(target, target_power, kTarget, 1'400'000);
    initialize(effective, effective_power, kEffective, 900'000);
    Put(storage, 0x20, static_cast<void *>(slots.data()));
    Put(storage, 0x2C, std::int32_t{50'002});
    Put(fallback, 0x18, std::int32_t{-1});
  }
};

thread_local Fixture *active = nullptr;

bool Frame(void *context, xar::game::WarEntryAssessmentFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}
bool OwningThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->owning_thread;
}
void Builder(void *actor, build::NativeWarEntryActorStateV1 *state) {
  auto &fixture = *active;
  ++fixture.build_calls;
  const auto *bytes = reinterpret_cast<const std::byte *>(state);
  for (std::size_t i = 0; i < sizeof(*state); ++i) {
    fixture.scratch_was_zero &= bytes[i] == std::byte{};
  }
  if (actor != fixture.actor.data()) std::abort();
  state->power_base_raw = 1'200'000;
  state->native_state_08_raw = 2;
  state->native_state_0c_raw = 0x103;
  state->native_flags_raw = 5;
}
void *Effective(void *actor, void *target, std::uint32_t home, bool alternate) {
  if (actor != active->actor.data() || target != active->target.data() ||
      home != 0 || alternate) std::abort();
  return active->effective.data();
}
void Network(void *root, build::NativeWarEntryNetworkConfigurationV1 *config) {
  ++active->network_calls;
  if (root != *config->root_character) std::abort();
  if (root == active->actor.data()) {
    if (*config->filter_a != 1 || *config->filter_b != 1 ||
        *config->filter_c != 1) std::abort();
    *config->accumulator = 300'000;
  } else {
    if (root != active->effective.data() || *config->filter_a != 0 ||
        *config->filter_b != 0 || *config->filter_c != 0) std::abort();
    *config->accumulator = 150'000;
  }
}
void Assess(void *actor, const build::NativeWarEntryActorStateV1 *state,
            void *target, build::NativeWarEntryAssessmentOutputV1 *output,
            const std::int64_t *distance_override, std::int32_t mode) {
  ++active->native_calls;
  if (actor != active->actor.data() || target != active->effective.data() ||
      state->native_flags_raw != 5 || state->native_state_0f_raw != 0 ||
      distance_override != nullptr || mode != 1) std::abort();
  *output = {1'250'000, 1'050'000, active->bad_ratio ? 70'001 : 70'000,
             11, 22, 8, {}};
}

build::WarEntryNativeEnvironmentV1 Environment(Fixture &fixture) {
  build::WarEntryNativeEnvironmentV1 environment{};
  environment.game_state_slot = &fixture.game_state_slot;
  environment.character_storage_slot = &fixture.storage_slot;
  environment.character_fallback_slot = &fixture.fallback_slot;
  environment.actor_state_dependency_slot = &fixture.dependency_slot;
  environment.actor_state_builder = Builder;
  environment.assessment = Assess;
  environment.network_collector = Network;
  environment.effective_target_resolver = Effective;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::game::ReadWarEntryAssessmentsV1Result Read(
    Fixture &fixture, std::int32_t target, xar::game::WarEntryAssessmentsV1 &output) {
  active = &fixture;
  const build::WarEntryAssessmentAccessV1 access{&fixture, Frame, OwningThread};
  return build::ReadWarEntryAssessmentsV1(
      Environment(fixture), access, {5, {target}}, output);
}
bool Check(bool value, const char *label) {
  if (!value) std::cerr << label << '\n';
  return value;
}
} // namespace

int main() {
  using Result = xar::game::ReadWarEntryAssessmentsV1Result;
  bool ok = true;
  // Same frame/targets as the two genuine paused V34 MCP failures. Only native
  // power evaluator memory is provided by the existing deterministic harness.
  for (const auto target_id : {30097, 32750}) {
    Fixture fixture;
    if (target_id != kTarget) {
      Put(fixture.target, 0x18, target_id);
      Put(fixture.slots, static_cast<std::size_t>(kTarget) * 0x10 + 8,
          static_cast<void *>(nullptr));
      Put(fixture.slots, static_cast<std::size_t>(target_id) * 0x10 + 8,
          static_cast<void *>(fixture.target.data()));
    }
    xar::game::WarEntryAssessmentsV1 output{};
    const auto result = Read(fixture, target_id, output);
    const bool passed = result == Result::available && output.available &&
        output.readiness.ready && output.requested_target_character_ids ==
            std::vector<std::int32_t>{target_id} &&
        output.assessments.size() == 1 && output.actor_character_id == kActor &&
        output.snapshot_revision == 5 && output.date_raw == 53'236'608 &&
        fixture.build_calls == 2 && fixture.native_calls == 2 &&
        fixture.network_calls == 4 && fixture.scratch_was_zero;
    std::cout << "target=" << target_id << " status=" << (passed ? "GREEN" : "RED")
              << " unavailable_stage=" << output.unavailable_stage
              << " native_calls=" << fixture.native_calls << '\n';
    ok &= Check(passed, "observed active-primary target reaches native same-frame evaluator");
  }
  return ok ? 0 : 1;
}
