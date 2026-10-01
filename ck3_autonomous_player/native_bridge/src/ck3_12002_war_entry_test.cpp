#include "xar_bridge/ck3_12002_war_entry.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
namespace build = xar::ck3_12002;
constexpr std::int32_t kActor = 0x01000001;
constexpr std::int32_t kTarget = 0x02000002;
constexpr std::int32_t kEffective = 0x03000003;

template <typename Buffer, typename Value>
void Put(Buffer &buffer, std::size_t offset, Value value) {
  if (offset + sizeof(value) > buffer.size()) std::abort();
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x1E0> actor{}, target{}, effective{}, fallback{};
  std::array<std::byte, 0x320> actor_power{}, target_power{}, effective_power{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x50> slots{};
  std::array<std::byte, 0xA8> game_state{};
  void *game_state_slot = game_state.data();
  void *storage_slot = storage.data();
  void *fallback_slot = fallback.data();
  void *dependency_slot = game_state.data();
  xar::game::WarEntryAssessmentFrameV1 frame{
      74, 53'175'816, true, true, true, kActor, {kTarget}};
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
    Put(storage, 0x2C, std::int32_t{5});
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
    Fixture &fixture, xar::game::WarEntryAssessmentsV1 &output) {
  active = &fixture;
  const build::WarEntryAssessmentAccessV1 access{&fixture, Frame, OwningThread};
  return build::ReadWarEntryAssessmentsV1(
      Environment(fixture), access, {74, {kTarget}}, output);
}
bool Check(bool value, const char *label) {
  if (!value) std::cerr << label << '\n';
  return value;
}
} // namespace

int main() {
  using Result = xar::game::ReadWarEntryAssessmentsV1Result;
  bool ok = true;
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto exact = build::BindWarEntryNativeEnvironmentV1(
      base, build::kWarEntryAssessmentsV1ExecutableSha256);
  ok &= Check(reinterpret_cast<std::uintptr_t>(exact.assessment) ==
                  base + 0x1A23240 &&
              reinterpret_cast<std::uintptr_t>(exact.actor_state_builder) ==
                  base + 0x1A22D30 &&
              reinterpret_cast<std::uintptr_t>(exact.network_collector) ==
                  base + 0x1A24010 &&
              reinterpret_cast<std::uintptr_t>(exact.effective_target_resolver) ==
                  base + 0x2C13460 &&
              reinterpret_cast<std::uintptr_t>(exact.actor_state_dependency_slot) ==
                  base + 0x5D1DD50, "exact 1.20 binding");
  ok &= Check(build::BindWarEntryNativeEnvironmentV1(base, "old-build")
                  .assessment == nullptr, "reject previous build identity");
  xar::game::WarEntryAssessmentsV1 result{};
  Fixture valid;
  ok &= Check(Read(valid, result) == Result::available && result.available &&
              result.readiness.ready && result.assessments.size() == 1 &&
              result.assessments.front().effective_target_character_id == kEffective &&
              result.assessments.front().actor_power_total_raw == 1'500'000 &&
              result.assessments.front().target_power_base_raw == 900'000 &&
              result.assessments.front().actual_power_ratio_raw == 70'000 &&
              valid.build_calls == 2 && valid.native_calls == 2 &&
              valid.network_calls == 4 && valid.scratch_was_zero,
              "migrated layouts, original full IDs and exact effective-target samples");
  const auto wire = build::SerializeWarEntryAssessmentsV1(result);
  ok &= Check(wire.find("1.20.0.2") != std::string::npos &&
              wire.find("0x1A23240") != std::string::npos &&
              wire.find("0x1A24010") != std::string::npos &&
              wire.find("CCharacter+0x1C0->+0x308") != std::string::npos &&
              wire.find("0x1878A00") == std::string::npos,
              "new-build serialized provenance");
  Fixture stale;
  Put(stale.target, 0x18, std::int32_t{0x04000002});
  ok &= Check(Read(stale, result) == Result::unavailable &&
              result.unavailable_stage == "target_identity" &&
              !result.available && result.assessments.empty(),
              "reject same storage index with different generation");
  Fixture dead;
  Put(dead.actor, 0x1D0, static_cast<void *>(dead.fallback.data()));
  ok &= Check(Read(dead, result) == Result::unavailable &&
              result.unavailable_stage == "actor_identity", "new death component");
  Fixture unpaused;
  unpaused.frame.paused = false;
  ok &= Check(Read(unpaused, result) == Result::requires_paused &&
              unpaused.native_calls == 0, "paused evaluator precondition");
  Fixture worker;
  worker.owning_thread = false;
  ok &= Check(Read(worker, result) == Result::unavailable &&
              result.unavailable_stage == "main_thread_required" &&
              worker.native_calls == 0, "typed owning-thread dispatch precondition");
  Fixture broken;
  broken.bad_ratio = true;
  ok &= Check(Read(broken, result) == Result::unavailable &&
              result.unavailable_stage == "native_ratio_cross_check" &&
              !result.available && result.assessments.empty(),
              "preserve native result and decomposition contract");
  Fixture wrong_revision;
  ++wrong_revision.frame.snapshot_revision;
  ok &= Check(Read(wrong_revision, result) == Result::revision_mismatch &&
              wrong_revision.native_calls == 0, "expected paused frame revision");
  if (ok) std::cout << "CK3 1.20.0.2 war-entry offline fixture GREEN\n";
  return ok ? 0 : 1;
}
