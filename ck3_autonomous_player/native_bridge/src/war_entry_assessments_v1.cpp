#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterPowerContainerOffset = 0x1B8;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kCharacterPowerRawOffset = 0x308;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;

struct ResolvedTargetV1 {
  std::int32_t requested_id = -1;
  void *requested_character = nullptr;
  std::int32_t effective_id = -1;
  void *effective_character = nullptr;
  std::int64_t target_power_base_raw = 0;
};

bool ActorStatesEqualExact(const NativeWarEntryActorStateV1 &left,
                           const NativeWarEntryActorStateV1 &right) noexcept {
  return std::memcmp(&left, &right, sizeof(left)) == 0;
}

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ReadBytes(const WarEntryAssessmentAccessV1 &access, const void *address,
               void *output, std::size_t size) noexcept {
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
  return GuardedDirectRead(address, output, size);
}

template <typename Value>
bool ReadValue(const WarEntryAssessmentAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() -
                   reinterpret_cast<std::uintptr_t>(base)) {
    return false;
  }
  const auto address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(base) + offset);
  return ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const WarEntryAssessmentAccessV1 &access, const Value *slot,
              Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool CheckedAdd(std::int64_t left, std::int64_t right,
                std::int64_t &output) noexcept {
  if ((right > 0 &&
       left > std::numeric_limits<std::int64_t>::max() - right) ||
      (right < 0 &&
       left < std::numeric_limits<std::int64_t>::min() - right)) {
    return false;
  }
  output = left + right;
  return true;
}

bool CheckedSubtract(std::int64_t left, std::int64_t right,
                     std::int64_t &output) noexcept {
  if ((right > 0 &&
       left < std::numeric_limits<std::int64_t>::min() + right) ||
      (right < 0 &&
       left > std::numeric_limits<std::int64_t>::max() + right)) {
    return false;
  }
  output = left - right;
  return true;
}

// Returns floor(numerator * multiplier / denominator) without constructing an
// overflowing intermediate.  The precondition numerator < denominator makes
// the quotient smaller than multiplier; only 64 modular doubling steps are
// needed, and production uses multiplier=100000.
bool FractionMultiplyDivide(std::uint64_t numerator,
                            std::uint64_t multiplier,
                            std::uint64_t denominator,
                            std::uint64_t &output) noexcept {
  if (denominator == 0 || numerator >= denominator) {
    return false;
  }
  std::uint64_t quotient = 0;
  std::uint64_t remainder = 0;
  for (std::int32_t bit = 63; bit >= 0; --bit) {
    if (quotient > (std::numeric_limits<std::uint64_t>::max() >> 1U)) {
      return false;
    }
    quotient <<= 1U;
    if (remainder >= denominator - remainder) {
      remainder -= denominator - remainder;
      ++quotient;
    } else {
      remainder += remainder;
    }
    if (((multiplier >> static_cast<std::uint32_t>(bit)) & 1U) != 0) {
      if (remainder >= denominator - numerator) {
        remainder -= denominator - numerator;
        ++quotient;
      } else {
        remainder += numerator;
      }
    }
  }
  output = quotient;
  return true;
}

bool ReconstructNativeRatio(std::int64_t target_total,
                            std::int64_t actor_total,
                            std::int64_t &output) noexcept {
  if (actor_total <= 0) {
    output = target_total;
    return true;
  }
  if (target_total < 0) {
    return false;
  }
  const auto denominator = static_cast<std::uint64_t>(actor_total);
  const auto numerator = static_cast<std::uint64_t>(target_total);
  const auto whole = numerator / denominator;
  const auto remainder = numerator % denominator;
  constexpr auto scale = static_cast<std::uint64_t>(
      kWarEntryAssessmentsV1FixedPointScale);
  if (whole >
      static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) /
          scale) {
    return false;
  }
  std::uint64_t fractional = 0;
  if (remainder != 0 &&
      !FractionMultiplyDivide(remainder, scale, denominator, fractional)) {
    return false;
  }
  const auto combined = whole * scale + fractional;
  if (combined >
      static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
    return false;
  }
  output = static_cast<std::int64_t>(combined);
  return true;
}

bool IsPositiveFullId(std::int32_t value) noexcept { return value > 0; }

bool ValidateTargetIds(const std::vector<std::int32_t> &targets) noexcept {
  if (targets.empty() ||
      targets.size() >
          static_cast<std::size_t>(kWarEntryAssessmentsV1MaximumTargets)) {
    return false;
  }
  for (std::size_t index = 0; index < targets.size(); ++index) {
    if (!IsPositiveFullId(targets[index]) ||
        std::find(targets.begin(), targets.begin() + index, targets[index]) !=
            targets.begin() + index) {
      return false;
    }
  }
  return true;
}

bool IsCanonicalDecimal(std::string_view token) noexcept {
  if (token.empty() || (token.size() > 1 && token.front() == '0')) {
    return false;
  }
  return std::all_of(token.begin(), token.end(), [](char value) {
    return value >= '0' && value <= '9';
  });
}

template <typename Value>
bool ParseDecimal(std::string_view token, Value &output) noexcept {
  if (!IsCanonicalDecimal(token)) {
    return false;
  }
  const auto parsed =
      std::from_chars(token.data(), token.data() + token.size(), output);
  return parsed.ec == std::errc{} && parsed.ptr == token.data() + token.size();
}

bool EnvironmentIsExact(const WarEntryNativeEnvironmentV1 &environment) {
  if (environment.game_state_slot == nullptr ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr ||
      environment.actor_state_dependency_slot == nullptr ||
      environment.actor_state_builder == nullptr ||
      environment.assessment == nullptr ||
      environment.network_collector == nullptr ||
      environment.effective_target_resolver == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return true;
  }
  if (environment.module_base == 0) {
    return false;
  }
  return reinterpret_cast<std::uintptr_t>(environment.game_state_slot) ==
             environment.module_base + kWarEntryGameStateSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.character_storage_slot) ==
             environment.module_base + kWarEntryCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.character_fallback_slot) ==
             environment.module_base + kWarEntryCharacterFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.actor_state_dependency_slot) ==
             environment.module_base + kWarEntryActorStateDependencySlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.actor_state_builder) ==
             environment.module_base + kWarEntryActorStateBuilderRva &&
         reinterpret_cast<std::uintptr_t>(environment.assessment) ==
             environment.module_base + kWarEntryAssessmentRva &&
         reinterpret_cast<std::uintptr_t>(environment.network_collector) ==
             environment.module_base + kWarEntryNetworkCollectorRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.effective_target_resolver) ==
             environment.module_base + kWarEntryEffectiveTargetResolverRva;
}

void *ResolveCharacter(const WarEntryNativeEnvironmentV1 &environment,
                       const WarEntryAssessmentAccessV1 &access,
                       std::int32_t full_id) noexcept {
  if (!IsPositiveFullId(full_id)) {
    return nullptr;
  }
  void *store = nullptr;
  void *fallback = nullptr;
  if (!ReadSlot(access, environment.character_storage_slot, store) ||
      !ReadSlot(access, environment.character_fallback_slot, fallback) ||
      store == nullptr) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadValue(access, store, kStorageSlotsOffset, slots) ||
      !ReadValue(access, store, kStorageCapacityOffset, capacity) ||
      capacity <= 0 || capacity > kMaximumComponentSlots || slots == nullptr) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset =
      static_cast<std::size_t>(index) * kStorageSlotStride +
      kStorageObjectOffset;
  void *character = nullptr;
  std::int32_t identity = -1;
  if (!ReadValue(access, slots, slot_offset, character) ||
      character == nullptr || character == fallback ||
      !ReadValue(access, character, kCharacterIdentityOffset, identity) ||
      identity != full_id) {
    return nullptr;
  }
  return character;
}

bool ReadPowerLeaf(const WarEntryAssessmentAccessV1 &access, void *character,
                   std::int64_t &power_raw) noexcept {
  void *container = nullptr;
  return ReadValue(access, character, kCharacterPowerContainerOffset,
                   container) &&
         container != nullptr &&
         ReadValue(access, container, kCharacterPowerRawOffset, power_raw) &&
         power_raw >= 0;
}

bool CharacterIsAliveAndPowered(const WarEntryAssessmentAccessV1 &access,
                                void *character) noexcept {
  void *power_container = nullptr;
  void *death_marker = nullptr;
  return ReadValue(access, character, kCharacterPowerContainerOffset,
                   power_container) &&
         ReadValue(access, character, kCharacterDeathMarkerOffset,
                   death_marker) &&
         power_container != nullptr && death_marker == nullptr;
}

bool InvokeEffectiveTarget(
    NativeWarEntryEffectiveTargetResolverFunctionV1 function,
    void *actor_character, void *target_character, void *&output) noexcept {
#if defined(_MSC_VER)
  __try {
    output = function(actor_character, target_character, 0, false);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function(actor_character, target_character, 0, false);
  return true;
#endif
}

bool InvokeNetworkCollector(
    NativeWarEntryNetworkCollectorFunctionV1 function, void *root_character,
    NativeWarEntryNetworkConfigurationV1 &configuration) noexcept {
#if defined(_MSC_VER)
  __try {
    function(root_character, &configuration);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  function(root_character, &configuration);
  return true;
#endif
}

bool InvokeActorStateBuilder(
    NativeWarEntryActorStateBuilderFunctionV1 function,
    void *actor_character, NativeWarEntryActorStateV1 &output) noexcept {
  // 0x18784D0 reads the existing high nibble at +0x0E and leaves +0x0F
  // untouched.  Zero-initialization is therefore part of the exact scratch
  // ABI, not merely defensive initialization.
  output = {};
#if defined(_MSC_VER)
  __try {
    function(actor_character, &output);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    return false;
  }
#else
  function(actor_character, &output);
  return true;
#endif
}

bool InvokeAssessment(NativeWarEntryAssessmentFunctionV1 function,
                       void *actor_character,
                       const NativeWarEntryActorStateV1 *actor_state,
                       void *effective_target_character,
                       NativeWarEntryAssessmentOutputV1 &output) noexcept {
#if defined(_MSC_VER)
  __try {
    function(actor_character, actor_state,
             effective_target_character, &output, nullptr, 1);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  function(actor_character, actor_state,
           effective_target_character, &output, nullptr, 1);
  return true;
#endif
}

bool CollectNetworkContribution(
    NativeWarEntryNetworkCollectorFunctionV1 function, void *root_character,
    std::int32_t filter_a, std::int32_t filter_b, std::int32_t filter_c,
    std::int64_t &contribution) noexcept {
  void *root_local = root_character;
  auto filter_a_local = filter_a;
  auto filter_b_local = filter_b;
  auto filter_c_local = filter_c;
  std::int64_t accumulator = 0;
  NativeWarEntryNetworkConfigurationV1 configuration{
      &root_local, &filter_a_local, &filter_b_local, &filter_c_local,
      &accumulator};
  if (!InvokeNetworkCollector(function, root_character, configuration) ||
      root_local != root_character || filter_a_local != filter_a ||
      filter_b_local != filter_b || filter_c_local != filter_c ||
      configuration.root_character != &root_local ||
      configuration.filter_a != &filter_a_local ||
      configuration.filter_b != &filter_b_local ||
      configuration.filter_c != &filter_c_local ||
      configuration.accumulator != &accumulator) {
    return false;
  }
  contribution = accumulator;
  return true;
}

bool AcquireAssessmentRows(
    const WarEntryNativeEnvironmentV1 &environment,
    const WarEntryAssessmentAccessV1 &access, void *actor,
    const std::vector<ResolvedTargetV1> &resolved, bool repeated_sample,
    std::vector<game::WarEntryAssessmentRowV1> &rows,
    NativeWarEntryActorStateV1 &built_actor_state,
    void *&built_actor_state_dependency,
    std::string_view &failure_stage) {
  const auto fail = [&failure_stage, repeated_sample](
                        std::string_view initial_stage,
                        std::string_view repeated_stage) {
    failure_stage = repeated_sample ? repeated_stage : initial_stage;
    return false;
  };

  void *builder_dependency = nullptr;
  if (!ReadSlot(access, environment.actor_state_dependency_slot,
                builder_dependency) ||
      builder_dependency == nullptr) {
    return fail("actor_state_builder_dependency",
                "repeat_actor_state_builder_dependency");
  }
  const auto builder_dependency_unchanged = [&]() {
    void *observed = nullptr;
    return ReadSlot(access, environment.actor_state_dependency_slot,
                    observed) &&
           observed == builder_dependency;
  };
  NativeWarEntryActorStateV1 actor_state{};
  if (!InvokeActorStateBuilder(environment.actor_state_builder, actor,
                               actor_state)) {
    return fail("actor_state_builder_call",
                "repeat_actor_state_builder_call");
  }
  if (!builder_dependency_unchanged()) {
    return fail("actor_state_builder_dependency_drift",
                "repeat_actor_state_builder_dependency_drift");
  }
  if (actor_state.power_base_raw < 0) {
    return fail("actor_state_builder_domain",
                "repeat_actor_state_builder_domain");
  }
  const auto actor_state_after_builder = actor_state;

  std::vector<game::WarEntryAssessmentRowV1> pending;
  pending.reserve(resolved.size());
  bool actor_network_seen = false;
  std::int64_t stable_actor_network = 0;
  for (const auto &target : resolved) {
    std::int64_t target_network = 0;
    std::int64_t actor_network = 0;
    if (!CollectNetworkContribution(environment.network_collector,
                                    target.effective_character, 0, 0, 0,
                                    target_network)) {
      return fail("target_network_collector",
                  "repeat_target_network_collector");
    }
    if (!CollectNetworkContribution(environment.network_collector, actor, 1,
                                    1, 1, actor_network)) {
      return fail("actor_network_collector",
                  "repeat_actor_network_collector");
    }
    if (target_network < 0 || actor_network < 0) {
      return fail("network_contribution_domain",
                  "repeat_network_contribution_domain");
    }
    if (actor_network_seen && actor_network != stable_actor_network) {
      return fail("actor_network_intra_sample",
                  "repeat_actor_network_intra_sample");
    }
    actor_network_seen = true;
    stable_actor_network = actor_network;
    std::int64_t actor_total = 0;
    std::int64_t target_pre_adjustment = 0;
    if (!CheckedAdd(actor_state.power_base_raw, actor_network, actor_total) ||
        !CheckedAdd(target.target_power_base_raw, target_network,
                    target_pre_adjustment) ||
        actor_total < 0 || target_pre_adjustment < 0) {
      return fail("network_checked_sum", "repeat_network_checked_sum");
    }

    if (!builder_dependency_unchanged()) {
      return fail("actor_state_builder_dependency_drift",
                  "repeat_actor_state_builder_dependency_drift");
    }
    if (!ActorStatesEqualExact(actor_state, actor_state_after_builder)) {
      return fail("actor_state_builder_mutated",
                  "repeat_actor_state_builder_mutated");
    }
    NativeWarEntryAssessmentOutputV1 native{};
    if (!InvokeAssessment(environment.assessment, actor, &actor_state,
                          target.effective_character, native)) {
      return fail("native_assessment_call", "repeat_native_assessment_call");
    }
    if (!builder_dependency_unchanged()) {
      return fail("actor_state_builder_dependency_drift",
                  "repeat_actor_state_builder_dependency_drift");
    }
    if (!ActorStatesEqualExact(actor_state, actor_state_after_builder)) {
      return fail("actor_state_builder_mutated",
                  "repeat_actor_state_builder_mutated");
    }
    if (native.distance_raw < 0 || native.target_power_total_raw < 0 ||
        native.actual_power_ratio_raw < 0) {
      return fail("native_output_domain", "repeat_native_output_domain");
    }
    std::int64_t adjustment = 0;
    std::int64_t target_reconstructed = 0;
    if (!CheckedSubtract(native.target_power_total_raw, target_pre_adjustment,
                         adjustment) ||
        !CheckedAdd(target_pre_adjustment, adjustment,
                    target_reconstructed) ||
        target_reconstructed != native.target_power_total_raw) {
      return fail("target_total_cross_check",
                  "repeat_target_total_cross_check");
    }
    std::int64_t reconstructed_ratio = 0;
    if (!ReconstructNativeRatio(native.target_power_total_raw, actor_total,
                                reconstructed_ratio) ||
        reconstructed_ratio != native.actual_power_ratio_raw) {
      return fail("native_ratio_cross_check",
                  "repeat_native_ratio_cross_check");
    }

    game::WarEntryAssessmentRowV1 row{};
    row.target_character_id = target.requested_id;
    row.effective_target_character_id = target.effective_id;
    row.distance_raw = native.distance_raw;
    row.actor_power_base_raw = actor_state.power_base_raw;
    row.actor_network_contribution_raw = actor_network;
    row.actor_power_total_raw = actor_total;
    row.target_power_base_raw = target.target_power_base_raw;
    row.target_network_contribution_raw = target_network;
    row.target_pre_adjustment_total_raw = target_pre_adjustment;
    row.target_adjustment_delta_raw = adjustment;
    row.target_power_total_raw = native.target_power_total_raw;
    // The native out+0x10 value remains authoritative. The reconstructed
    // value above is only a fail-closed ABI/decomposition equality gate.
    row.actual_power_ratio_raw = native.actual_power_ratio_raw;
    row.target_ai_context_actor_entry_raw =
        native.target_ai_context_actor_entry_raw;
    row.actor_ai_context_target_entry_raw =
        native.actor_ai_context_target_entry_raw;
    row.native_flags_raw = native.native_flags_raw;
    pending.push_back(row);
  }
  if (!builder_dependency_unchanged()) {
    return fail("actor_state_builder_dependency_drift",
                "repeat_actor_state_builder_dependency_drift");
  }
  if (!ActorStatesEqualExact(actor_state, actor_state_after_builder)) {
    return fail("actor_state_builder_mutated",
                "repeat_actor_state_builder_mutated");
  }
  built_actor_state = actor_state;
  built_actor_state_dependency = builder_dependency;
  rows = std::move(pending);
  failure_stage = {};
  return true;
}

bool RevalidateAssessmentInputs(
    const WarEntryNativeEnvironmentV1 &environment,
    const WarEntryAssessmentAccessV1 &access, std::int32_t actor_id,
    void *actor, const std::vector<ResolvedTargetV1> &resolved,
    std::string_view &failure_stage) {
  void *const actor_after = ResolveCharacter(environment, access, actor_id);
  if (actor_after != actor ||
      !CharacterIsAliveAndPowered(access, actor_after)) {
    failure_stage = "actor_same_frame_revalidation";
    return false;
  }
  for (const auto &target : resolved) {
    if (ResolveCharacter(environment, access, target.requested_id) !=
            target.requested_character ||
        ResolveCharacter(environment, access, target.effective_id) !=
            target.effective_character) {
      failure_stage = "target_same_frame_identity";
      return false;
    }
    void *effective_after = nullptr;
    std::int64_t power_after = 0;
    if (!CharacterIsAliveAndPowered(access, target.requested_character) ||
        !InvokeEffectiveTarget(environment.effective_target_resolver, actor,
                               target.requested_character, effective_after) ||
        effective_after != target.effective_character ||
        !CharacterIsAliveAndPowered(access, effective_after) ||
        !ReadPowerLeaf(access, effective_after, power_after) ||
        power_after != target.target_power_base_raw) {
      failure_stage = "effective_target_same_frame";
      return false;
    }
  }
  failure_stage = {};
  return true;
}

bool IsDeclarable(const game::WarEntryAssessmentFrameV1 &frame,
                  std::int32_t target) {
  return std::find(frame.declarable_target_character_ids.begin(),
                   frame.declarable_target_character_ids.end(),
                   target) != frame.declarable_target_character_ids.end();
}

bool FrameShapeValid(const game::WarEntryAssessmentFrameV1 &frame) {
  if (!frame.map_ready || !frame.actor_alive ||
      !IsPositiveFullId(frame.actor_character_id)) {
    return false;
  }
  return std::all_of(frame.declarable_target_character_ids.begin(),
                     frame.declarable_target_character_ids.end(),
                     IsPositiveFullId);
}

game::ReadWarEntryAssessmentsV1Result
Fail(game::WarEntryAssessmentsV1 &output,
     game::ReadWarEntryAssessmentsV1Result result,
     std::string_view stage) {
  output = {};
  output.unavailable_stage.assign(stage);
  return result;
}

} // namespace

WarEntryNativeEnvironmentV1
BindWarEntryNativeEnvironmentV1(std::uintptr_t module_base) noexcept {
  WarEntryNativeEnvironmentV1 output{};
  if (module_base == 0) {
    return output;
  }
  output.module_base = module_base;
  output.game_state_slot = reinterpret_cast<void **>(
      module_base + kWarEntryGameStateSlotRva);
  output.character_storage_slot = reinterpret_cast<void **>(
      module_base + kWarEntryCharacterStorageSlotRva);
  output.character_fallback_slot = reinterpret_cast<void **>(
      module_base + kWarEntryCharacterFallbackSlotRva);
  output.actor_state_dependency_slot = reinterpret_cast<void **>(
      module_base + kWarEntryActorStateDependencySlotRva);
  output.actor_state_builder =
      reinterpret_cast<NativeWarEntryActorStateBuilderFunctionV1>(
          module_base + kWarEntryActorStateBuilderRva);
  output.assessment = reinterpret_cast<NativeWarEntryAssessmentFunctionV1>(
      module_base + kWarEntryAssessmentRva);
  output.network_collector =
      reinterpret_cast<NativeWarEntryNetworkCollectorFunctionV1>(
          module_base + kWarEntryNetworkCollectorRva);
  output.effective_target_resolver =
      reinterpret_cast<NativeWarEntryEffectiveTargetResolverFunctionV1>(
          module_base + kWarEntryEffectiveTargetResolverRva);
  return output;
}

bool ParseWarEntryAssessmentsV1Step(
    std::string_view step,
    std::vector<std::int32_t> &target_character_ids) noexcept {
  target_character_ids.clear();
  try {
    if (!step.starts_with(kWarEntryAssessmentsV1StepPrefix)) {
      return false;
    }
    auto remaining = step.substr(kWarEntryAssessmentsV1StepPrefix.size());
    const auto first_dash = remaining.find('-');
    if (first_dash == std::string_view::npos) {
      return false;
    }
    std::uint32_t count = 0;
    if (!ParseDecimal(remaining.substr(0, first_dash), count) || count == 0 ||
        count > static_cast<std::uint32_t>(
                    kWarEntryAssessmentsV1MaximumTargets)) {
      return false;
    }
    remaining.remove_prefix(first_dash + 1);
    target_character_ids.reserve(count);
    while (!remaining.empty()) {
      const auto dash = remaining.find('-');
      const auto token = remaining.substr(0, dash);
      std::int32_t target = 0;
      if (!ParseDecimal(token, target) || !IsPositiveFullId(target) ||
          std::find(target_character_ids.begin(), target_character_ids.end(),
                    target) != target_character_ids.end()) {
        target_character_ids.clear();
        return false;
      }
      target_character_ids.push_back(target);
      if (dash == std::string_view::npos) {
        remaining = {};
      } else {
        remaining.remove_prefix(dash + 1);
        if (remaining.empty()) {
          target_character_ids.clear();
          return false;
        }
      }
    }
    if (target_character_ids.size() != count) {
      target_character_ids.clear();
      return false;
    }
    return true;
  } catch (...) {
    target_character_ids.clear();
    return false;
  }
}

std::string EncodeWarEntryAssessmentsV1Step(
    const std::vector<std::int32_t> &target_character_ids) {
  if (!ValidateTargetIds(target_character_ids)) {
    return {};
  }
  std::string output(kWarEntryAssessmentsV1StepPrefix);
  std::array<char, 32> buffer{};
  const auto append = [&output, &buffer](auto value) {
    const auto encoded =
        std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
    if (encoded.ec != std::errc{}) {
      return false;
    }
    output.append(buffer.data(), encoded.ptr);
    return true;
  };
  if (!append(target_character_ids.size())) {
    return {};
  }
  for (const auto target : target_character_ids) {
    output.push_back('-');
    if (!append(target)) {
      return {};
    }
  }
  return output;
}

game::ReadWarEntryAssessmentsV1Result ReadWarEntryAssessmentsV1(
    const WarEntryNativeEnvironmentV1 &environment,
    const WarEntryAssessmentAccessV1 &access,
    const WarEntryAssessmentsV1Request &request,
    game::WarEntryAssessmentsV1 &output) noexcept {
  using game::ReadWarEntryAssessmentsV1Result;
  try {
    output = {};
    if (!ValidateTargetIds(request.target_character_ids)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::invalid_arguments,
                  "request_targets");
    }
    if (!EnvironmentIsExact(environment) || access.capture_frame == nullptr ||
        access.is_main_thread == nullptr) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "exact_build_bindings");
    }
    if (!access.is_main_thread(access.context)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "main_thread_required");
    }

    game::WarEntryAssessmentFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "frame_before");
    }
    if (!before.paused) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::requires_paused,
                  "requires_paused");
    }
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::revision_mismatch,
                  "expected_revision");
    }
    if (!FrameShapeValid(before)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "frame_identity");
    }
    for (const auto target : request.target_character_ids) {
      if (!IsDeclarable(before, target)) {
        return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                    "target_not_declarable");
      }
    }

    void *const actor = ResolveCharacter(environment, access,
                                         before.actor_character_id);
    if (actor == nullptr || !CharacterIsAliveAndPowered(access, actor)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "actor_identity");
    }
    std::vector<ResolvedTargetV1> resolved;
    resolved.reserve(request.target_character_ids.size());
    for (const auto requested_id : request.target_character_ids) {
      void *const requested_character =
          ResolveCharacter(environment, access, requested_id);
      if (requested_character == nullptr ||
          !CharacterIsAliveAndPowered(access, requested_character)) {
        return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                    "target_identity");
      }
      void *effective_character = nullptr;
      if (!InvokeEffectiveTarget(environment.effective_target_resolver, actor,
                                 requested_character, effective_character) ||
          effective_character == nullptr || effective_character == actor) {
        return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                    "effective_target_resolver");
      }
      std::int32_t effective_id = -1;
      if (!ReadValue(access, effective_character, kCharacterIdentityOffset,
                     effective_id) ||
          !IsPositiveFullId(effective_id) ||
          ResolveCharacter(environment, access, effective_id) !=
              effective_character ||
          !CharacterIsAliveAndPowered(access, effective_character)) {
        return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                    "effective_target_identity");
      }
      std::int64_t target_power_base = 0;
      if (!ReadPowerLeaf(access, effective_character, target_power_base)) {
        return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                    "target_power_leaf");
      }
      resolved.push_back({requested_id, requested_character, effective_id,
                          effective_character, target_power_base});
    }

    std::vector<game::WarEntryAssessmentRowV1> rows;
    NativeWarEntryActorStateV1 actor_state{};
    void *actor_state_dependency = nullptr;
    std::string_view sample_failure_stage;
    if (!AcquireAssessmentRows(environment, access, actor, resolved, false,
                               rows, actor_state, actor_state_dependency,
                               sample_failure_stage)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  sample_failure_stage);
    }

    game::WarEntryAssessmentFrameV1 middle{};
    if (!access.capture_frame(access.context, middle) || middle != before) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "same_frame_stamp");
    }
    if (!RevalidateAssessmentInputs(environment, access,
                                    before.actor_character_id, actor, resolved,
                                    sample_failure_stage)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  sample_failure_stage);
    }

    std::vector<game::WarEntryAssessmentRowV1> repeated_rows;
    NativeWarEntryActorStateV1 repeated_actor_state{};
    void *repeated_actor_state_dependency = nullptr;
    if (!AcquireAssessmentRows(environment, access, actor, resolved, true,
                               repeated_rows, repeated_actor_state,
                               repeated_actor_state_dependency,
                               sample_failure_stage)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  sample_failure_stage);
    }
    if (repeated_actor_state_dependency != actor_state_dependency) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "same_frame_actor_state_builder_dependency");
    }
    if (!ActorStatesEqualExact(repeated_actor_state, actor_state)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "same_frame_actor_state_builder");
    }
    if (repeated_rows != rows) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "same_frame_native_sample");
    }
    if (!RevalidateAssessmentInputs(environment, access,
                                    before.actor_character_id, actor, resolved,
                                    sample_failure_stage)) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  sample_failure_stage);
    }
    game::WarEntryAssessmentFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before) {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "same_frame_stamp_after_repeat");
    }

    output.available = true;
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    output.actor_character_id = before.actor_character_id;
    output.requested_target_character_ids = request.target_character_ids;
    output.assessments = std::move(rows);
    output.readiness = {true, true, true, true, true, true, true, true};
    output.unavailable_stage.clear();
    return ReadWarEntryAssessmentsV1Result::available;
  } catch (...) {
    try {
      return Fail(output, ReadWarEntryAssessmentsV1Result::unavailable,
                  "reader_exception");
    } catch (...) {
      output = {};
      return ReadWarEntryAssessmentsV1Result::unavailable;
    }
  }
}

} // namespace xar::ck3_11906
