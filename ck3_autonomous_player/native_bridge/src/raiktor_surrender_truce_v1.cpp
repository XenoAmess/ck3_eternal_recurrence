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

#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
thread_local RaiktorTrucePrivateShapeCaptureV1 g_private_shape_capture{};
#define XAR_G2_SHAPE_RESET() (g_private_shape_capture = {})
#define XAR_G2_SHAPE_STAGE(value)                                         \
  (g_private_shape_capture.failed_check = (value))
#define XAR_G2_SHAPE_VALUE(member, value)                                 \
  (g_private_shape_capture.member = (value))
#define XAR_G2_SHAPE_ADDRESS(member, value)                               \
  (g_private_shape_capture.member = reinterpret_cast<std::uintptr_t>(value))
#else
#define XAR_G2_SHAPE_RESET() ((void)0)
#define XAR_G2_SHAPE_STAGE(value) ((void)0)
#define XAR_G2_SHAPE_VALUE(member, value) ((void)0)
#define XAR_G2_SHAPE_ADDRESS(member, value) ((void)0)
#endif

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

#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
void CaptureLoadedRootChildrenForG2(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access, void *root_children,
    std::int32_t root_capacity, std::int32_t root_count) noexcept {
  auto &capture = g_private_shape_capture;
  if (root_children == nullptr) {
    capture.root_child_capture_status = "root_children_null";
    return;
  }
  if (root_capacity < 0 || root_count < 0 || root_count > root_capacity) {
    capture.root_child_capture_status = "root_vector_bounds_invalid";
    return;
  }

  const auto declared_count = static_cast<std::size_t>(root_count);
  const auto capture_limit =
      declared_count < capture.root_child_vtables.size()
          ? declared_count
          : capture.root_child_vtables.size();
  capture.root_child_capture_limit = capture_limit;
  capture.root_child_capture_status =
      capture_limit == declared_count ? "complete" : "truncated";

  for (std::size_t index = 0; index < capture_limit; ++index) {
    void *child = nullptr;
    if (!ReadValue(access, root_children, index * sizeof(void *), child)) {
      capture.root_child_capture_status = "child_pointer_read_failed";
      capture.root_child_capture_failed_index =
          static_cast<std::int32_t>(index);
      return;
    }
    if (child == nullptr) {
      capture.root_child_capture_status = "child_pointer_null";
      capture.root_child_capture_failed_index =
          static_cast<std::int32_t>(index);
      return;
    }

    std::uintptr_t child_vtable = 0;
    if (!ReadValue(access, child, 0, child_vtable)) {
      capture.root_child_capture_status = "child_vtable_read_failed";
      capture.root_child_capture_failed_index =
          static_cast<std::int32_t>(index);
      return;
    }
    capture.root_child_vtables[index] = child_vtable;
    capture.root_child_capture_completed = index + 1;
    if (child_vtable == environment.scripted_effect_vtable) {
      ++capture.root_scripted_match_count;
      capture.root_scripted_match_index = static_cast<std::int32_t>(index);
    }
  }
}

constexpr std::array<std::size_t, 2> kPrivateScriptedCandidateIndices = {
    9, 10};
constexpr std::uintptr_t kPrivateIndex9ContextChild0VtableRva = 0x44D1E18;
constexpr std::uintptr_t kPrivateIndex10ContextChild0VtableRva = 0x41E36D0;

void CaptureLoadedScriptedCandidatesForG2(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access, void *root_children,
    std::int32_t root_count) noexcept {
  auto &capture = g_private_shape_capture;
  for (std::size_t slot = 0; slot < kPrivateScriptedCandidateIndices.size();
       ++slot) {
    const auto root_index = kPrivateScriptedCandidateIndices[slot];
    auto &candidate = capture.scripted_candidates[slot];
    candidate.root_index = static_cast<std::int32_t>(root_index);
    if (root_children == nullptr || root_count < 0 ||
        root_index >= static_cast<std::size_t>(root_count)) {
      candidate.status = "root_index_unavailable";
      continue;
    }

    void *child = nullptr;
    if (!ReadValue(access, root_children, root_index * sizeof(void *), child)) {
      candidate.status = "child_pointer_read_failed";
      continue;
    }
    candidate.child = reinterpret_cast<std::uintptr_t>(child);
    if (child == nullptr) {
      candidate.status = "child_pointer_null";
      continue;
    }
    if (!ReadValue(access, child, 0, candidate.child_vtable)) {
      candidate.status = "child_vtable_read_failed";
      continue;
    }
    if (candidate.child_vtable != environment.scripted_effect_vtable) {
      candidate.status = "child_vtable_mismatch";
      continue;
    }
    if (!ReadValue(access, child, kScriptedSelectorCountOffset,
                   candidate.selector_count)) {
      candidate.status = "selector_count_read_failed";
      continue;
    }

    void *scripted_template = nullptr;
    if (!ReadValue(access, child, kScriptedTemplateOffset,
                   scripted_template)) {
      candidate.status = "template_pointer_read_failed";
      continue;
    }
    candidate.scripted_template =
        reinterpret_cast<std::uintptr_t>(scripted_template);
    if (scripted_template == nullptr) {
      candidate.status = "template_pointer_null";
      continue;
    }
    if (!ReadValue(access, scripted_template, 0, candidate.template_vtable)) {
      candidate.status = "template_vtable_read_failed";
      continue;
    }
    if (candidate.template_vtable != environment.scripted_template_vtable) {
      candidate.status = "template_vtable_mismatch";
      continue;
    }

    void *default_effect = nullptr;
    if (!ReadValue(access, scripted_template, kTemplateDefaultEffectOffset,
                   default_effect)) {
      candidate.status = "default_effect_read_failed";
      continue;
    }
    candidate.default_effect =
        reinterpret_cast<std::uintptr_t>(default_effect);
    if (default_effect == nullptr) {
      candidate.status = "default_effect_null";
      continue;
    }
    if (!ReadValue(access, default_effect, 0, candidate.default_vtable)) {
      candidate.status = "default_vtable_read_failed";
      continue;
    }
    if (candidate.default_vtable != environment.jomini_effect_vtable) {
      candidate.status = "default_vtable_mismatch";
      continue;
    }

    void *default_children = nullptr;
    if (!ReadValue(access, default_effect, kEffectChildrenOffset,
                   default_children)) {
      candidate.status = "default_children_read_failed";
      continue;
    }
    candidate.default_children =
        reinterpret_cast<std::uintptr_t>(default_children);
    if (!ReadValue(access, default_effect, kEffectCapacityOffset,
                   candidate.default_capacity)) {
      candidate.status = "default_capacity_read_failed";
      continue;
    }
    if (!ReadValue(access, default_effect, kEffectCountOffset,
                   candidate.default_count)) {
      candidate.status = "default_count_read_failed";
      continue;
    }
    candidate.status = "complete";
    ++capture.scripted_candidate_capture_completed;
    candidate.semantic_shape_match =
        default_children != nullptr && candidate.selector_count == 0 &&
        candidate.default_capacity == kScriptDefaultCapacity &&
        candidate.default_count == kScriptDefaultCount;
    if (candidate.semantic_shape_match) {
      ++capture.scripted_semantic_match_count;
      capture.scripted_semantic_match_root_index =
          static_cast<std::int32_t>(root_index);
    }

    if (default_children == nullptr) {
      candidate.sole_child_status = "default_children_null";
      continue;
    }
    if (candidate.default_count != 1 || candidate.default_capacity < 1) {
      candidate.sole_child_status = "default_not_singleton";
      continue;
    }

    void *sole_child = nullptr;
    if (!ReadValue(access, default_children, 0, sole_child)) {
      candidate.sole_child_status = "sole_child_read_failed";
      continue;
    }
    candidate.sole_child = reinterpret_cast<std::uintptr_t>(sole_child);
    if (sole_child == nullptr) {
      candidate.sole_child_status = "sole_child_null";
      continue;
    }
    if (!ReadValue(access, sole_child, 0, candidate.sole_child_vtable)) {
      candidate.sole_child_status = "sole_child_vtable_read_failed";
      continue;
    }

    void *sole_child_children = nullptr;
    if (!ReadValue(access, sole_child, kEffectChildrenOffset,
                   sole_child_children)) {
      candidate.sole_child_status = "sole_child_children_read_failed";
      continue;
    }
    candidate.sole_child_children =
        reinterpret_cast<std::uintptr_t>(sole_child_children);
    if (!ReadValue(access, sole_child, kEffectCapacityOffset,
                   candidate.sole_child_capacity)) {
      candidate.sole_child_status = "sole_child_capacity_read_failed";
      continue;
    }
    if (!ReadValue(access, sole_child, kEffectCountOffset,
                   candidate.sole_child_count)) {
      candidate.sole_child_status = "sole_child_count_read_failed";
      continue;
    }
    if (sole_child_children == nullptr || candidate.sole_child_count < 1 ||
        candidate.sole_child_capacity < candidate.sole_child_count) {
      candidate.sole_child_status = "complete_without_nested0";
      ++capture.sole_child_capture_completed;
      continue;
    }

    void *nested0 = nullptr;
    if (!ReadValue(access, sole_child_children, 0, nested0)) {
      candidate.sole_child_status = "nested0_read_failed";
      continue;
    }
    candidate.sole_child_nested0 = reinterpret_cast<std::uintptr_t>(nested0);
    if (nested0 == nullptr) {
      candidate.sole_child_status = "nested0_null";
      continue;
    }
    if (!ReadValue(access, nested0, 0,
                   candidate.sole_child_nested0_vtable)) {
      candidate.sole_child_status = "nested0_vtable_read_failed";
      continue;
    }
    candidate.sole_child_status = "complete";
    ++capture.sole_child_capture_completed;
    candidate.caddtruce_prefix_match =
        candidate.sole_child_vtable == environment.hidden_effect_vtable &&
        candidate.sole_child_capacity == 1 &&
        candidate.sole_child_count == 1 &&
        candidate.sole_child_nested0_vtable ==
            environment.context_effect_vtable;
    if (candidate.caddtruce_prefix_match) {
      ++capture.caddtruce_prefix_match_count;
      capture.caddtruce_prefix_match_root_index =
          static_cast<std::int32_t>(root_index);
    }

    void *context_node = nullptr;
    if (candidate.sole_child_vtable == environment.context_effect_vtable) {
      context_node = reinterpret_cast<void *>(candidate.sole_child);
      candidate.context_depth = 0;
    } else if (candidate.sole_child_nested0_vtable ==
               environment.context_effect_vtable) {
      context_node = reinterpret_cast<void *>(candidate.sole_child_nested0);
      candidate.context_depth = 1;
    } else {
      candidate.context_status = "exact_context_not_found";
      continue;
    }
    candidate.context_node = reinterpret_cast<std::uintptr_t>(context_node);
    if (!ReadValue(access, context_node, 0, candidate.context_vtable)) {
      candidate.context_status = "context_vtable_read_failed";
      continue;
    }

    void *context_children = nullptr;
    if (!ReadValue(access, context_node, kEffectChildrenOffset,
                   context_children)) {
      candidate.context_status = "context_children_read_failed";
      continue;
    }
    candidate.context_children =
        reinterpret_cast<std::uintptr_t>(context_children);
    if (!ReadValue(access, context_node, kEffectCapacityOffset,
                   candidate.context_capacity)) {
      candidate.context_status = "context_capacity_read_failed";
      continue;
    }
    if (!ReadValue(access, context_node, kEffectCountOffset,
                   candidate.context_count)) {
      candidate.context_status = "context_count_read_failed";
      continue;
    }
    if (!ReadValue(access, context_node, kContextScopeCountOffset,
                   candidate.context_scope_count)) {
      candidate.context_status = "context_scope_count_read_failed";
      continue;
    }
    if (context_children == nullptr || candidate.context_count < 1 ||
        candidate.context_capacity < candidate.context_count) {
      candidate.context_status = "context_child0_unavailable";
      continue;
    }

    void *context_child0 = nullptr;
    if (!ReadValue(access, context_children, 0, context_child0)) {
      candidate.context_status = "context_child0_read_failed";
      continue;
    }
    candidate.context_child0 =
        reinterpret_cast<std::uintptr_t>(context_child0);
    if (context_child0 == nullptr) {
      candidate.context_status = "context_child0_null";
      continue;
    }
    if (!ReadValue(access, context_child0, 0,
                   candidate.context_child0_vtable)) {
      candidate.context_status = "context_child0_vtable_read_failed";
      continue;
    }

    void *context_child0_children = nullptr;
    if (!ReadValue(access, context_child0, kEffectChildrenOffset,
                   context_child0_children)) {
      candidate.context_status = "context_child0_children_read_failed";
      continue;
    }
    candidate.context_child0_children =
        reinterpret_cast<std::uintptr_t>(context_child0_children);
    if (!ReadValue(access, context_child0, kEffectCapacityOffset,
                   candidate.context_child0_capacity)) {
      candidate.context_status = "context_child0_capacity_read_failed";
      continue;
    }
    if (!ReadValue(access, context_child0, kEffectCountOffset,
                   candidate.context_child0_count)) {
      candidate.context_status = "context_child0_count_read_failed";
      continue;
    }

    candidate.context_status = "complete";
    ++capture.context_capture_completed;
    candidate.truce_vtable_match =
        candidate.context_child0_vtable == environment.truce_effect_vtable;
    if (candidate.truce_vtable_match) {
      const void *duration_address = nullptr;
      if (CheckedAddress(context_child0, kTruceDurationScriptValueOffset,
                         duration_address)) {
        candidate.context_child0_duration_script_value =
            reinterpret_cast<std::uintptr_t>(duration_address);
        ++capture.truce_vtable_match_count;
        capture.truce_vtable_match_root_index =
            static_cast<std::int32_t>(root_index);
      } else {
        candidate.context_status = "truce_duration_address_failed";
        candidate.truce_vtable_match = false;
      }
    }

    const auto expected_child0_vtable =
        environment.module_base +
        (root_index == 9 ? kPrivateIndex9ContextChild0VtableRva
                         : kPrivateIndex10ContextChild0VtableRva);
    const auto expected_next_layer_count =
        static_cast<std::int32_t>(root_index == 9 ? 1 : 6);
    if (candidate.context_child0_vtable != expected_child0_vtable ||
        candidate.context_child0_children == 0 ||
        candidate.context_child0_capacity != expected_next_layer_count ||
        candidate.context_child0_count != expected_next_layer_count) {
      candidate.next_layer_status =
          root_index == 9 ? "unexpected_index9_shape"
                          : "unexpected_index10_shape";
      continue;
    }

    candidate.next_layer_capture_limit =
        static_cast<std::size_t>(expected_next_layer_count);
    bool next_layer_failed = false;
    for (std::size_t next_index = 0;
         next_index < candidate.next_layer_capture_limit; ++next_index) {
      void *next_child = nullptr;
      if (!ReadValue(access, context_child0_children,
                     next_index * sizeof(void *), next_child)) {
        candidate.next_layer_status = "child_pointer_read_failed";
        next_layer_failed = true;
        break;
      }
      if (next_child == nullptr) {
        candidate.next_layer_status = "child_null";
        next_layer_failed = true;
        break;
      }

      std::uintptr_t next_child_vtable = 0;
      if (!ReadValue(access, next_child, 0, next_child_vtable)) {
        candidate.next_layer_status = "child_vtable_read_failed";
        next_layer_failed = true;
        break;
      }
      candidate.next_layer_child_vtables[next_index] = next_child_vtable;
      candidate.next_layer_capture_completed = next_index + 1;
      if (next_child_vtable == environment.truce_effect_vtable) {
        const void *duration_address = nullptr;
        if (!CheckedAddress(next_child, kTruceDurationScriptValueOffset,
                            duration_address)) {
          candidate.next_layer_status = "truce_duration_address_failed";
          next_layer_failed = true;
          break;
        }
        ++candidate.next_layer_truce_match_count;
        candidate.next_layer_truce_match_index =
            static_cast<std::int32_t>(next_index);
        candidate.next_layer_truce_duration_script_value =
            reinterpret_cast<std::uintptr_t>(duration_address);
        ++capture.next_layer_truce_match_count;
        capture.next_layer_truce_match_root_index =
            static_cast<std::int32_t>(root_index);
        capture.next_layer_truce_match_child_index =
            static_cast<std::int32_t>(next_index);
      }
    }
    if (next_layer_failed) continue;
    candidate.next_layer_status = "complete";
    ++capture.next_layer_candidate_capture_completed;
  }
}
#endif

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
  XAR_G2_SHAPE_RESET();
  std::uintptr_t root_vtable = 0;
  if (!ReadValue(access, root, 0, root_vtable)) {
    XAR_G2_SHAPE_STAGE("root_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_vtable_mismatch;
  }
  XAR_G2_SHAPE_VALUE(root_vtable, root_vtable);
  if (root_vtable != environment.jomini_effect_vtable) {
    XAR_G2_SHAPE_STAGE("root_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_vtable_mismatch;
  }
  void *root_slot11 = nullptr;
  if (!ReadValue(access, reinterpret_cast<void *>(root_vtable),
                 kLoadedEffectSlot11Offset, root_slot11)) {
    XAR_G2_SHAPE_STAGE("root_slot11_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_slot11_missing;
  }
  XAR_G2_SHAPE_ADDRESS(root_slot11, root_slot11);
  if (root_slot11 == nullptr) {
    XAR_G2_SHAPE_STAGE("root_slot11_null");
    return RaiktorSurrenderTruceFailureV1::root_slot11_missing;
  }

  void *root_children = nullptr;
  std::int32_t root_capacity = -1;
  std::int32_t root_count = -1;
  if (!ReadValue(access, root, kEffectChildrenOffset, root_children)) {
    XAR_G2_SHAPE_STAGE("root_children_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(root_children, root_children);
  if (!ReadValue(access, root, kEffectCapacityOffset, root_capacity)) {
    XAR_G2_SHAPE_STAGE("root_capacity_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(root_capacity, root_capacity);
  if (!ReadValue(access, root, kEffectCountOffset, root_count)) {
    XAR_G2_SHAPE_STAGE("root_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(root_count, root_count);
#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
  CaptureLoadedScriptedCandidatesForG2(environment, access, root_children,
                                       root_count);
#endif
  if (root_children == nullptr) {
    XAR_G2_SHAPE_STAGE("root_children_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (root_capacity != kDefeatRootCapacity) {
    XAR_G2_SHAPE_STAGE("root_capacity_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (root_count != kDefeatRootCount) {
    XAR_G2_SHAPE_STAGE("root_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *scripted_effect = nullptr;
  std::uintptr_t scripted_vtable = 0;
  std::int32_t selector_count = -1;
  void *scripted_template = nullptr;
  if (!ReadValue(access, root_children,
                 kDefeatRootTruceScriptIndex * sizeof(void *),
                 scripted_effect)) {
    XAR_G2_SHAPE_STAGE("scripted_effect_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(scripted_effect, scripted_effect);
  if (scripted_effect == nullptr) {
    XAR_G2_SHAPE_STAGE("scripted_effect_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, scripted_effect, 0, scripted_vtable)) {
    XAR_G2_SHAPE_STAGE("scripted_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(scripted_vtable, scripted_vtable);
  if (scripted_vtable != environment.scripted_effect_vtable) {
    XAR_G2_SHAPE_STAGE("scripted_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, scripted_effect, kScriptedSelectorCountOffset,
                 selector_count)) {
    XAR_G2_SHAPE_STAGE("scripted_selector_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(scripted_selector_count, selector_count);
  if (selector_count != 0) {
    XAR_G2_SHAPE_STAGE("scripted_selector_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, scripted_effect, kScriptedTemplateOffset,
                 scripted_template)) {
    XAR_G2_SHAPE_STAGE("scripted_template_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(scripted_template, scripted_template);
  if (scripted_template == nullptr) {
    XAR_G2_SHAPE_STAGE("scripted_template_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::uintptr_t template_vtable = 0;
  void *default_effect = nullptr;
  if (!ReadValue(access, scripted_template, 0, template_vtable)) {
    XAR_G2_SHAPE_STAGE("template_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(template_vtable, template_vtable);
  if (template_vtable != environment.scripted_template_vtable) {
    XAR_G2_SHAPE_STAGE("template_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, scripted_template, kTemplateDefaultEffectOffset,
                 default_effect)) {
    XAR_G2_SHAPE_STAGE("default_effect_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(default_effect, default_effect);
  if (default_effect == nullptr) {
    XAR_G2_SHAPE_STAGE("default_effect_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::uintptr_t default_vtable = 0;
  void *default_children = nullptr;
  std::int32_t default_capacity = -1;
  std::int32_t default_count = -1;
  if (!ReadValue(access, default_effect, 0, default_vtable)) {
    XAR_G2_SHAPE_STAGE("default_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(default_vtable, default_vtable);
  if (default_vtable != environment.jomini_effect_vtable) {
    XAR_G2_SHAPE_STAGE("default_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, default_effect, kEffectChildrenOffset,
                 default_children)) {
    XAR_G2_SHAPE_STAGE("default_children_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(default_children, default_children);
  if (!ReadValue(access, default_effect, kEffectCapacityOffset,
                 default_capacity)) {
    XAR_G2_SHAPE_STAGE("default_capacity_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(default_capacity, default_capacity);
  if (!ReadValue(access, default_effect, kEffectCountOffset, default_count)) {
    XAR_G2_SHAPE_STAGE("default_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(default_count, default_count);
  if (default_children == nullptr) {
    XAR_G2_SHAPE_STAGE("default_children_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (default_capacity != kScriptDefaultCapacity) {
    XAR_G2_SHAPE_STAGE("default_capacity_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (default_count != kScriptDefaultCount) {
    XAR_G2_SHAPE_STAGE("default_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  std::size_t hidden_count = 0;
  void *hidden_effect = nullptr;
  std::size_t hidden_index = 0;
  for (std::size_t index = 0;
       index < static_cast<std::size_t>(kScriptDefaultCount); ++index) {
    XAR_G2_SHAPE_VALUE(default_child_scan_index, index);
    void *child = nullptr;
    std::uintptr_t child_vtable = 0;
    if (!ReadValue(access, default_children, index * sizeof(void *), child)) {
      XAR_G2_SHAPE_STAGE("default_child_read_failed");
      return RaiktorSurrenderTruceFailureV1::root_shape_drift;
    }
    if (child == nullptr) {
      XAR_G2_SHAPE_STAGE("default_child_null");
      return RaiktorSurrenderTruceFailureV1::root_shape_drift;
    }
    if (!ReadValue(access, child, 0, child_vtable)) {
      XAR_G2_SHAPE_STAGE("default_child_vtable_read_failed");
      return RaiktorSurrenderTruceFailureV1::root_shape_drift;
    }
    XAR_G2_SHAPE_VALUE(default_child_vtables[index], child_vtable);
    if (child_vtable == environment.hidden_effect_vtable) {
      ++hidden_count;
      hidden_effect = child;
      hidden_index = index;
    }
  }
  XAR_G2_SHAPE_VALUE(hidden_count, hidden_count);
  XAR_G2_SHAPE_VALUE(hidden_index, hidden_index);
  XAR_G2_SHAPE_ADDRESS(hidden_effect, hidden_effect);
  if (hidden_count != 1) {
    XAR_G2_SHAPE_STAGE("hidden_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  if (hidden_index != kScriptDefaultHiddenIndex) {
    XAR_G2_SHAPE_STAGE("hidden_index_mismatch");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }

  void *hidden_children = nullptr;
  std::int32_t hidden_capacity = -1;
  std::int32_t hidden_child_count = -1;
  if (!ReadValue(access, hidden_effect, kEffectChildrenOffset,
                 hidden_children)) {
    XAR_G2_SHAPE_STAGE("hidden_children_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(hidden_children, hidden_children);
  if (!ReadValue(access, hidden_effect, kEffectCapacityOffset,
                 hidden_capacity)) {
    XAR_G2_SHAPE_STAGE("hidden_capacity_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(hidden_capacity, hidden_capacity);
  if (!ReadValue(access, hidden_effect, kEffectCountOffset,
                 hidden_child_count)) {
    XAR_G2_SHAPE_STAGE("hidden_child_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(hidden_child_count, hidden_child_count);
  if (hidden_children == nullptr) {
    XAR_G2_SHAPE_STAGE("hidden_children_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (hidden_capacity != 1) {
    XAR_G2_SHAPE_STAGE("hidden_capacity_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (hidden_child_count != 1) {
    XAR_G2_SHAPE_STAGE("hidden_child_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *context_effect = nullptr;
  std::uintptr_t context_vtable = 0;
  if (!ReadValue(access, hidden_children, 0, context_effect)) {
    XAR_G2_SHAPE_STAGE("context_effect_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(context_effect, context_effect);
  if (context_effect == nullptr) {
    XAR_G2_SHAPE_STAGE("context_effect_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (!ReadValue(access, context_effect, 0, context_vtable)) {
    XAR_G2_SHAPE_STAGE("context_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(context_vtable, context_vtable);
  if (context_vtable != environment.context_effect_vtable) {
    XAR_G2_SHAPE_STAGE("context_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *context_children = nullptr;
  std::int32_t context_capacity = -1;
  std::int32_t context_child_count = -1;
  std::int32_t context_scope_count = -1;
  if (!ReadValue(access, context_effect, kEffectChildrenOffset,
                 context_children)) {
    XAR_G2_SHAPE_STAGE("context_children_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_ADDRESS(context_children, context_children);
  if (!ReadValue(access, context_effect, kEffectCapacityOffset,
                 context_capacity)) {
    XAR_G2_SHAPE_STAGE("context_capacity_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(context_capacity, context_capacity);
  if (!ReadValue(access, context_effect, kEffectCountOffset,
                 context_child_count)) {
    XAR_G2_SHAPE_STAGE("context_child_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(context_child_count, context_child_count);
  if (!ReadValue(access, context_effect, kContextScopeCountOffset,
                 context_scope_count)) {
    XAR_G2_SHAPE_STAGE("context_scope_count_read_failed");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  XAR_G2_SHAPE_VALUE(context_scope_count, context_scope_count);
  if (context_children == nullptr) {
    XAR_G2_SHAPE_STAGE("context_children_null");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (context_capacity != 1) {
    XAR_G2_SHAPE_STAGE("context_capacity_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (context_child_count != 1) {
    XAR_G2_SHAPE_STAGE("context_child_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }
  if (context_scope_count != 1) {
    XAR_G2_SHAPE_STAGE("context_scope_count_mismatch");
    return RaiktorSurrenderTruceFailureV1::root_shape_drift;
  }

  void *truce_effect = nullptr;
  std::uintptr_t truce_vtable = 0;
  const void *duration_address = nullptr;
  if (!ReadValue(access, context_children, 0, truce_effect)) {
    XAR_G2_SHAPE_STAGE("truce_effect_read_failed");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  XAR_G2_SHAPE_ADDRESS(truce_effect, truce_effect);
  if (truce_effect == nullptr) {
    XAR_G2_SHAPE_STAGE("truce_effect_null");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  if (!ReadValue(access, truce_effect, 0, truce_vtable)) {
    XAR_G2_SHAPE_STAGE("truce_vtable_read_failed");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  XAR_G2_SHAPE_VALUE(truce_vtable, truce_vtable);
  if (truce_vtable != environment.truce_effect_vtable) {
    XAR_G2_SHAPE_STAGE("truce_vtable_mismatch");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  if (!CheckedAddress(truce_effect, kTruceDurationScriptValueOffset,
                      duration_address)) {
    XAR_G2_SHAPE_STAGE("duration_script_value_address_failed");
    return RaiktorSurrenderTruceFailureV1::caddtruce_not_unique;
  }
  XAR_G2_SHAPE_ADDRESS(duration_script_value, duration_address);

  output.node = truce_effect;
  output.duration_script_value = const_cast<void *>(duration_address);
  XAR_G2_SHAPE_STAGE("complete");
  return RaiktorSurrenderTruceFailureV1::none;
}

} // namespace

#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
const RaiktorTrucePrivateShapeCaptureV1 &
LastRaiktorTrucePrivateShapeCaptureV1() noexcept {
  return g_private_shape_capture;
}
#endif

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
