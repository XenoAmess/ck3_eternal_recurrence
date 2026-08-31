#include "xar_bridge/raiktor_surrender_truce_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kEffectChildrenOffset = 0x40;
constexpr std::size_t kEffectCapacityOffset = 0x48;
constexpr std::size_t kEffectCountOffset = 0x4C;
constexpr std::size_t kScriptedTemplateOffset = 0x60;
constexpr std::size_t kScriptedSelectorCountOffset = 0x94;
constexpr std::size_t kTemplateDefaultEffectOffset = 0x120;
constexpr std::size_t kContextScopeCountOffset = 0x6C;
constexpr std::size_t kTruceDurationScriptValueOffset = 0x108;
constexpr std::size_t kLoadedEffectSlot11Offset = 11 * sizeof(void *);

constexpr std::int32_t kDefeatRootCapacity = 19;
constexpr std::int32_t kDefeatRootCount = 14;
constexpr std::size_t kDefeatRootTruceScriptIndex = 9;
constexpr std::int32_t kScriptDefaultCapacity = 6;
constexpr std::int32_t kScriptDefaultCount = 5;
constexpr std::size_t kScriptDefaultHiddenIndex = 2;

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
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

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

bool ReadBytes(const RaiktorSurrenderTruceAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr
             ? access.read_memory(access.context, address, output, size)
             : GuardedDirectRead(address, output, size);
}

template <typename Value>
bool ReadValue(const RaiktorSurrenderTruceAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.jomini_effect_vtable == 0 ||
      environment.scripted_effect_vtable == 0 ||
      environment.scripted_template_vtable == 0 ||
      environment.hidden_effect_vtable == 0 ||
      environment.context_effect_vtable == 0 ||
      environment.truce_effect_vtable == 0 ||
      environment.evaluate_duration_days == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return environment.module_base == 0;
  }
  if (environment.module_base == 0) return false;
  const auto base = environment.module_base;
  return environment.jomini_effect_vtable ==
             base + kRaiktorTruceJominiEffectVtableRva &&
         environment.scripted_effect_vtable ==
             base + kRaiktorTruceScriptedEffectVtableRva &&
         environment.scripted_template_vtable ==
             base + kRaiktorTruceScriptedTemplateVtableRva &&
         environment.hidden_effect_vtable ==
             base + kRaiktorTruceHiddenEffectVtableRva &&
         environment.context_effect_vtable ==
             base + kRaiktorTruceContextEffectVtableRva &&
         environment.truce_effect_vtable ==
             base + kRaiktorTruceEffectVtableRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.evaluate_duration_days) ==
             base + kRaiktorTruceDurationEvaluatorRva;
}

bool FrameIdentityIsValid(
    const RaiktorSurrenderTruceFrameV1 &frame) noexcept {
  return frame.snapshot_revision != 0 && frame.native_revision != 0 &&
         frame.war_id > 0 && frame.active_casus_belli_database_index >= 0 &&
         frame.primary_attacker_character_id > 0 &&
         frame.primary_defender_character_id > 0 &&
         frame.primary_attacker_character_id !=
             frame.primary_defender_character_id &&
         frame.claimant_character_id > 0 && frame.war != nullptr &&
         frame.active_casus_belli != nullptr &&
         frame.attacker_defeat_root != nullptr;
}

struct ResolvedTruceNodeV1 {
  void *node = nullptr;
  void *duration_script_value = nullptr;
};

RaiktorSurrenderTruceFailureV1 ResolveUniqueTruceNode(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access, void *root,
    ResolvedTruceNodeV1 &output) noexcept {
  output = {};
  std::uintptr_t root_vtable = 0;
  if (!ReadValue(access, root, 0, root_vtable) ||
      root_vtable != environment.jomini_effect_vtable) {
    return RaiktorSurrenderTruceFailureV1::root_vtable_mismatch;
  }
  void *root_slot11 = nullptr;
  if (!ReadValue(access, reinterpret_cast<void *>(root_vtable),
                 kLoadedEffectSlot11Offset, root_slot11) ||
      root_slot11 == nullptr) {
    return RaiktorSurrenderTruceFailureV1::root_slot11_missing;
  }

  void *root_children = nullptr;
  std::int32_t root_capacity = -1;
  std::int32_t root_count = -1;
  if (!ReadValue(access, root, kEffectChildrenOffset, root_children) ||
      !ReadValue(access, root, kEffectCapacityOffset, root_capacity) ||
      !ReadValue(access, root, kEffectCountOffset, root_count) ||
      root_children == nullptr || root_capacity != kDefeatRootCapacity ||
      root_count != kDefeatRootCount) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *scripted_effect = nullptr;
  std::uintptr_t scripted_vtable = 0;
  std::int32_t selector_count = -1;
  void *scripted_template = nullptr;
  if (!ReadValue(access, root_children,
                 kDefeatRootTruceScriptIndex * sizeof(void *),
                 scripted_effect) ||
      scripted_effect == nullptr ||
      !ReadValue(access, scripted_effect, 0, scripted_vtable) ||
      scripted_vtable != environment.scripted_effect_vtable ||
      !ReadValue(access, scripted_effect, kScriptedSelectorCountOffset,
                 selector_count) ||
      selector_count != 0 ||
      !ReadValue(access, scripted_effect, kScriptedTemplateOffset,
                 scripted_template) ||
      scripted_template == nullptr) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::uintptr_t template_vtable = 0;
  void *default_effect = nullptr;
  if (!ReadValue(access, scripted_template, 0, template_vtable) ||
      template_vtable != environment.scripted_template_vtable ||
      !ReadValue(access, scripted_template, kTemplateDefaultEffectOffset,
                 default_effect) ||
      default_effect == nullptr) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::uintptr_t default_vtable = 0;
  void *default_children = nullptr;
  std::int32_t default_capacity = -1;
  std::int32_t default_count = -1;
  if (!ReadValue(access, default_effect, 0, default_vtable) ||
      default_vtable != environment.jomini_effect_vtable ||
      !ReadValue(access, default_effect, kEffectChildrenOffset,
                 default_children) ||
      !ReadValue(access, default_effect, kEffectCapacityOffset,
                 default_capacity) ||
      !ReadValue(access, default_effect, kEffectCountOffset, default_count) ||
      default_children == nullptr ||
      default_capacity != kScriptDefaultCapacity ||
      default_count != kScriptDefaultCount) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::size_t hidden_count = 0;
  void *hidden_effect = nullptr;
  std::size_t hidden_index = 0;
  for (std::size_t index = 0;
       index < static_cast<std::size_t>(kScriptDefaultCount); ++index) {
    void *child = nullptr;
    std::uintptr_t child_vtable = 0;
    if (!ReadValue(access, default_children, index * sizeof(void *), child) ||
        child == nullptr || !ReadValue(access, child, 0, child_vtable)) {
      return RaiktorSurrenderTruceFailureV1::root_shape_drift;
    }
    if (child_vtable == environment.hidden_effect_vtable) {
      ++hidden_count;
      hidden_effect = child;
      hidden_index = index;
    }
  }
  if (hidden_count != 1 || hidden_index != kScriptDefaultHiddenIndex) {
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }

  void *hidden_children = nullptr;
  std::int32_t hidden_capacity = -1;
  std::int32_t hidden_child_count = -1;
  if (!ReadValue(access, hidden_effect, kEffectChildrenOffset,
                 hidden_children) ||
      !ReadValue(access, hidden_effect, kEffectCapacityOffset,
                 hidden_capacity) ||
      !ReadValue(access, hidden_effect, kEffectCountOffset,
                 hidden_child_count) ||
      hidden_children == nullptr || hidden_capacity != 1 ||
      hidden_child_count != 1) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *context_effect = nullptr;
  std::uintptr_t context_vtable = 0;
  if (!ReadValue(access, hidden_children, 0, context_effect) ||
      context_effect == nullptr ||
      !ReadValue(access, context_effect, 0, context_vtable) ||
      context_vtable != environment.context_effect_vtable) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *context_children = nullptr;
  std::int32_t context_capacity = -1;
  std::int32_t context_child_count = -1;
  std::int32_t context_scope_count = -1;
  if (!ReadValue(access, context_effect, kEffectChildrenOffset,
                 context_children) ||
      !ReadValue(access, context_effect, kEffectCapacityOffset,
                 context_capacity) ||
      !ReadValue(access, context_effect, kEffectCountOffset,
                 context_child_count) ||
      !ReadValue(access, context_effect, kContextScopeCountOffset,
                 context_scope_count) ||
      context_children == nullptr || context_capacity != 1 ||
      context_child_count != 1 || context_scope_count != 1) {
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *truce_effect = nullptr;
  std::uintptr_t truce_vtable = 0;
  const void *duration_address = nullptr;
  if (!ReadValue(access, context_children, 0, truce_effect) ||
      truce_effect == nullptr ||
      !ReadValue(access, truce_effect, 0, truce_vtable) ||
      truce_vtable != environment.truce_effect_vtable ||
      !CheckedAddress(truce_effect, kTruceDurationScriptValueOffset,
                      duration_address)) {
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }

  output.node = truce_effect;
  output.duration_script_value = const_cast<void *>(duration_address);
  return RaiktorSurrenderTruceFailureV1::none;
}

} // namespace

std::string_view RaiktorSurrenderTruceFailureReasonV1(
    RaiktorSurrenderTruceFailureV1 failure) noexcept {
  switch (failure) {
  case RaiktorSurrenderTruceFailureV1::none:
    return "none";
  case RaiktorSurrenderTruceFailureV1::unsupported_build:
    return "unsupported_build";
  case RaiktorSurrenderTruceFailureV1::invalid_request:
    return "invalid_request";
  case RaiktorSurrenderTruceFailureV1::first_frame_unavailable:
    return "first_frame_unavailable";
  case RaiktorSurrenderTruceFailureV1::frame_not_paused:
    return "frame_not_paused";
  case RaiktorSurrenderTruceFailureV1::wrong_casus_belli:
    return "wrong_casus_belli";
  case RaiktorSurrenderTruceFailureV1::invalid_frame_identity:
    return "invalid_frame_identity";
  case RaiktorSurrenderTruceFailureV1::root_vtable_mismatch:
    return "root_vtable_mismatch";
  case RaiktorSurrenderTruceFailureV1::root_slot11_missing:
    return "root_slot11_missing";
  case RaiktorSurrenderTruceFailureV1::root_shape_drift:
    return "root_shape_drift";
  case RaiktorSurrenderTruceFailureV1::caddtruce_not_unique:
    return "caddtruce_not_unique";
  case RaiktorSurrenderTruceFailureV1::duration_evaluator_unavailable:
    return "duration_evaluator_unavailable";
  case RaiktorSurrenderTruceFailureV1::duration_negative:
    return "duration_negative";
  case RaiktorSurrenderTruceFailureV1::duration_unstable:
    return "duration_unstable";
  case RaiktorSurrenderTruceFailureV1::second_frame_unavailable:
    return "second_frame_unavailable";
  case RaiktorSurrenderTruceFailureV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

RaiktorSurrenderTruceObservationV1 ObserveRaiktorSurrenderTruceV1(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access,
    const RaiktorSurrenderTruceRequestV1 &request) noexcept {
  RaiktorSurrenderTruceObservationV1 result;
  const auto fail = [&result](RaiktorSurrenderTruceFailureV1 failure) {
    result.status = RaiktorSurrenderTruceStatusV1::unavailable;
    result.failure = failure;
    return result;
  };
  if (!EnvironmentIsExact(environment)) {
    return fail(RaiktorSurrenderTruceFailureV1::unsupported_build);
  }
  const auto effect_context =
      reinterpret_cast<std::uintptr_t>(request.effect_context);
  if (access.read_frame == nullptr || request.effect_context == nullptr ||
      effect_context >
          (std::numeric_limits<std::uintptr_t>::max)() - 0x28 ||
      request.evaluation_context !=
          reinterpret_cast<void *>(effect_context + 0x28)) {
    return fail(RaiktorSurrenderTruceFailureV1::invalid_request);
  }

  RaiktorSurrenderTruceFrameV1 first;
  if (!access.read_frame(access.context, &first)) {
    return fail(RaiktorSurrenderTruceFailureV1::first_frame_unavailable);
  }
  result.frame = first;
  if (!first.paused) {
    return fail(RaiktorSurrenderTruceFailureV1::frame_not_paused);
  }
  if (!first.exact_raiktor_claim_cb) {
    return fail(RaiktorSurrenderTruceFailureV1::wrong_casus_belli);
  }
  if (!FrameIdentityIsValid(first)) {
    return fail(RaiktorSurrenderTruceFailureV1::invalid_frame_identity);
  }

  ResolvedTruceNodeV1 first_node;
  auto shape_failure = ResolveUniqueTruceNode(
      environment, access, first.attacker_defeat_root, first_node);
  if (shape_failure != RaiktorSurrenderTruceFailureV1::none) {
    return fail(shape_failure);
  }
  result.pointer_shape_verified = true;

  const auto first_days = environment.evaluate_duration_days(
      first_node.duration_script_value, request.effect_context,
      request.evaluation_context);
  const auto second_days = environment.evaluate_duration_days(
      first_node.duration_script_value, request.effect_context,
      request.evaluation_context);
  if (first_days < 0 || second_days < 0) {
    return fail(RaiktorSurrenderTruceFailureV1::duration_negative);
  }
  if (first_days != second_days) {
    return fail(RaiktorSurrenderTruceFailureV1::duration_unstable);
  }
  result.evaluator_double_read_stable = true;

  ResolvedTruceNodeV1 second_node;
  shape_failure = ResolveUniqueTruceNode(
      environment, access, first.attacker_defeat_root, second_node);
  if (shape_failure != RaiktorSurrenderTruceFailureV1::none ||
      second_node.node != first_node.node ||
      second_node.duration_script_value != first_node.duration_script_value) {
    return fail(shape_failure == RaiktorSurrenderTruceFailureV1::none
                    ? RaiktorSurrenderTruceFailureV1::root_shape_drift
                    : shape_failure);
  }

  RaiktorSurrenderTruceFrameV1 second;
  if (!access.read_frame(access.context, &second)) {
    return fail(RaiktorSurrenderTruceFailureV1::second_frame_unavailable);
  }
  if (!second.paused) {
    return fail(RaiktorSurrenderTruceFailureV1::frame_not_paused);
  }
  if (second != first) {
    return fail(RaiktorSurrenderTruceFailureV1::frame_changed);
  }

  result.status = RaiktorSurrenderTruceStatusV1::available;
  result.failure = RaiktorSurrenderTruceFailureV1::none;
  result.owner_character_id = first.primary_attacker_character_id;
  result.toward_character_id = first.primary_defender_character_id;
  result.evaluated_days = first_days;
  result.same_frame_stable = true;
  return result;
}

} // namespace xar::ck3_11906
