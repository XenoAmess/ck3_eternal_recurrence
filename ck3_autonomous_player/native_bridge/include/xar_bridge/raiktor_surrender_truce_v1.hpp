#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRaiktorSurrenderTruceV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kRaiktorSurrenderTruceV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kRaiktorSurrenderTruceV1BackendId =
    "ck3-1.19.0.6-native-raiktor-surrender-truce-v1";

inline constexpr std::uintptr_t kRaiktorTruceJominiEffectVtableRva =
    0x44CF030;
inline constexpr std::uintptr_t kRaiktorTruceScriptedEffectVtableRva =
    0x44CF0F8;
inline constexpr std::uintptr_t kRaiktorTruceScriptedTemplateVtableRva =
    0x44DCD38;
inline constexpr std::uintptr_t kRaiktorTruceHiddenEffectVtableRva =
    0x44D1C88;
inline constexpr std::uintptr_t kRaiktorTruceContextEffectVtableRva =
    0x44D27B8;
inline constexpr std::uintptr_t kRaiktorTruceEffectVtableRva = 0x4461CA8;
inline constexpr std::uintptr_t kRaiktorTruceDurationEvaluatorRva =
    0x3373000;

enum class RaiktorSurrenderTruceStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class RaiktorSurrenderTruceFailureV1 : std::uint32_t {
  none = 0,
  unsupported_build,
  invalid_request,
  first_frame_unavailable,
  frame_not_paused,
  wrong_casus_belli,
  invalid_frame_identity,
  root_vtable_mismatch,
  root_slot11_missing,
  root_shape_drift,
  caddtruce_not_unique,
  duration_evaluator_unavailable,
  duration_negative,
  duration_unstable,
  second_frame_unavailable,
  frame_changed,
};

struct RaiktorSurrenderTruceFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t war_id = -1;
  std::int32_t active_casus_belli_database_index = -1;
  bool exact_raiktor_claim_cb = false;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t claimant_character_id = -1;
  void *war = nullptr;
  void *active_casus_belli = nullptr;
  void *attacker_defeat_root = nullptr;

  friend bool operator==(const RaiktorSurrenderTruceFrameV1 &,
                         const RaiktorSurrenderTruceFrameV1 &) = default;
};

using RaiktorTruceReadMemoryV1 = bool (*)(void *context,
                                         const void *address, void *output,
                                         std::size_t size);
using RaiktorTruceReadFrameV1 = bool (*)(
    void *context, RaiktorSurrenderTruceFrameV1 *output);
using RaiktorTruceEvaluateDurationDaysV1 = std::int32_t (*)(
    void *script_value, void *effect_context, void *evaluation_context);

#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
// Private, test-build-only evidence emitted at the exact evaluator call
// boundary.  The callback must append and durably flush the row before it
// returns true; a false result prevents the evaluator call.
struct RaiktorTrucePrivateEvaluatorBoundaryV1 {
  std::string_view stage = "not_started";
  std::string_view exact_path =
      "root[7].default.children[1].children[0].children[0]";
  bool exact_path_verified = false;
  std::uintptr_t truce_effect = 0;
  std::uintptr_t truce_vtable = 0;
  std::uintptr_t duration_script_value = 0;
  std::uintptr_t effect_context = 0;
  std::uintptr_t evaluation_context = 0;
  std::uintptr_t evaluator_function = 0;
  std::size_t planned_call_count = 2;
  std::size_t completed_call_count = 0;
  std::int32_t evaluated_days = -1;
};

using RaiktorTruceAppendPrivateEvaluatorBoundaryV1 = bool (*)(
    void *context, const RaiktorTrucePrivateEvaluatorBoundaryV1 &boundary);
#endif

struct RaiktorSurrenderTruceAccessV1 {
  void *context = nullptr;
  RaiktorTruceReadMemoryV1 read_memory = nullptr;
  RaiktorTruceReadFrameV1 read_frame = nullptr;
};

struct RaiktorSurrenderTruceNativeEnvironmentV1 {
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t jomini_effect_vtable = 0;
  std::uintptr_t scripted_effect_vtable = 0;
  std::uintptr_t scripted_template_vtable = 0;
  std::uintptr_t hidden_effect_vtable = 0;
  std::uintptr_t context_effect_vtable = 0;
  std::uintptr_t truce_effect_vtable = 0;
  RaiktorTruceEvaluateDurationDaysV1 evaluate_duration_days = nullptr;
#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
  void *private_evaluator_boundary_context = nullptr;
  RaiktorTruceAppendPrivateEvaluatorBoundaryV1
      append_private_evaluator_boundary = nullptr;
  // Deterministic fixture hook: model process exit immediately after the
  // durable pre-call row, without invoking the evaluator in the test process.
  bool private_fixture_stop_after_pre_call = false;
#endif
};

struct RaiktorSurrenderTruceRequestV1 {
  void *effect_context = nullptr;
  void *evaluation_context = nullptr;
};

struct RaiktorSurrenderTruceObservationV1 {
  RaiktorSurrenderTruceStatusV1 status =
      RaiktorSurrenderTruceStatusV1::unavailable;
  RaiktorSurrenderTruceFailureV1 failure =
      RaiktorSurrenderTruceFailureV1::invalid_request;
  RaiktorSurrenderTruceFrameV1 frame;
  std::int32_t owner_character_id = -1;
  std::int32_t toward_character_id = -1;
  std::int32_t evaluated_days = -1;
  bool pointer_shape_verified = false;
  bool evaluator_double_read_stable = false;
  bool same_frame_stable = false;
  // Intentionally false in v1.  This primitive observes the exact evaluator
  // result; it does not synthesize CK3's persisted truce expiry semantics.
  bool expiry_observable = false;
};

#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)
// One-off staged evidence for the private GEN-034 reader. This type and its
// accessor do not exist in the default production DLL or on the MCP wire.
struct RaiktorTrucePrivateScriptedCandidateV1 {
  std::int32_t root_index = -1;
  std::string_view status = "not_attempted";
  std::uintptr_t child = 0;
  std::uintptr_t child_vtable = 0;
  std::int32_t selector_count = -1;
  std::uintptr_t scripted_template = 0;
  std::uintptr_t template_vtable = 0;
  std::uintptr_t default_effect = 0;
  std::uintptr_t default_vtable = 0;
  std::uintptr_t default_children = 0;
  std::int32_t default_capacity = -1;
  std::int32_t default_count = -1;
  bool semantic_shape_match = false;
  std::string_view sole_child_status = "not_attempted";
  std::uintptr_t sole_child = 0;
  std::uintptr_t sole_child_vtable = 0;
  std::uintptr_t sole_child_children = 0;
  std::int32_t sole_child_capacity = -1;
  std::int32_t sole_child_count = -1;
  std::uintptr_t sole_child_nested0 = 0;
  std::uintptr_t sole_child_nested0_vtable = 0;
  bool caddtruce_prefix_match = false;
  std::string_view context_status = "not_attempted";
  std::int32_t context_depth = -1;
  std::uintptr_t context_node = 0;
  std::uintptr_t context_vtable = 0;
  std::uintptr_t context_children = 0;
  std::int32_t context_capacity = -1;
  std::int32_t context_count = -1;
  std::int32_t context_scope_count = -1;
  std::uintptr_t context_child0 = 0;
  std::uintptr_t context_child0_vtable = 0;
  std::uintptr_t context_child0_children = 0;
  std::int32_t context_child0_capacity = -1;
  std::int32_t context_child0_count = -1;
  std::uintptr_t context_child0_duration_script_value = 0;
  bool truce_vtable_match = false;
  std::string_view next_layer_status = "not_attempted";
  std::array<std::uintptr_t, 6> next_layer_child_vtables{};
  std::size_t next_layer_capture_limit = 0;
  std::size_t next_layer_capture_completed = 0;
  std::size_t next_layer_truce_match_count = 0;
  std::int32_t next_layer_truce_match_index = -1;
  std::uintptr_t next_layer_truce_duration_script_value = 0;
};

struct RaiktorTrucePrivateNestedContainerV1 {
  std::int32_t root_index = -1;
  std::int32_t source_child_index = -1;
  std::string_view status = "not_attempted";
  std::uintptr_t node = 0;
  std::uintptr_t node_vtable = 0;
  bool common_vector_requested = false;
  std::string_view common_vector_status = "not_requested";
  std::uintptr_t common_children = 0;
  std::int32_t common_capacity = -1;
  std::int32_t common_count = -1;
  std::array<std::uintptr_t, 16> common_child_vtables{};
  std::size_t common_capture_limit = 0;
  std::size_t common_capture_completed = 0;
  std::int32_t common_capture_failed_index = -1;
  std::size_t common_truce_match_count = 0;
  std::int32_t common_truce_match_index = -1;
  bool optional_effect_requested = false;
  std::string_view optional_effect_status = "not_requested";
  std::uintptr_t optional_effect = 0;
  std::uintptr_t optional_effect_vtable = 0;
  bool optional_truce_match = false;
};

struct RaiktorTrucePrivateShapeCaptureV1 {
  std::string_view failed_check = "not_started";
  std::string_view targeted_index7_status = "not_attempted";
  std::uintptr_t root_vtable = 0;
  std::uintptr_t root_slot11 = 0;
  std::uintptr_t root_children = 0;
  std::int32_t root_capacity = -1;
  std::int32_t root_count = -1;
  std::string_view root_child_capture_status = "not_attempted";
  std::array<std::uintptr_t, 16> root_child_vtables{};
  std::size_t root_child_capture_limit = 0;
  std::size_t root_child_capture_completed = 0;
  std::int32_t root_child_capture_failed_index = -1;
  std::size_t root_scripted_match_count = 0;
  std::int32_t root_scripted_match_index = -1;
  std::array<RaiktorTrucePrivateScriptedCandidateV1, 2>
      scripted_candidates{};
  std::size_t scripted_candidate_capture_completed = 0;
  std::size_t scripted_semantic_match_count = 0;
  std::int32_t scripted_semantic_match_root_index = -1;
  std::size_t sole_child_capture_completed = 0;
  std::size_t caddtruce_prefix_match_count = 0;
  std::int32_t caddtruce_prefix_match_root_index = -1;
  std::size_t context_capture_completed = 0;
  std::size_t truce_vtable_match_count = 0;
  std::int32_t truce_vtable_match_root_index = -1;
  std::size_t next_layer_candidate_capture_completed = 0;
  std::size_t next_layer_truce_match_count = 0;
  std::int32_t next_layer_truce_match_root_index = -1;
  std::int32_t next_layer_truce_match_child_index = -1;
  std::array<RaiktorTrucePrivateNestedContainerV1, 4>
      nested_containers{};
  std::size_t nested_container_capture_completed = 0;
  std::size_t nested_truce_match_count = 0;
  std::int32_t nested_truce_match_container_slot = -1;
  std::int32_t nested_truce_match_common_child_index = -1;
  bool nested_truce_match_optional_effect = false;
  std::uintptr_t scripted_effect = 0;
  std::uintptr_t scripted_vtable = 0;
  std::int32_t scripted_selector_count = -1;
  std::uintptr_t scripted_template = 0;
  std::uintptr_t template_vtable = 0;
  std::uintptr_t default_effect = 0;
  std::uintptr_t default_vtable = 0;
  std::uintptr_t default_children = 0;
  std::int32_t default_capacity = -1;
  std::int32_t default_count = -1;
  std::array<std::uintptr_t, 5> default_child_vtables{};
  std::size_t default_child_scan_index = 0;
  std::size_t hidden_count = 0;
  std::size_t hidden_index = 0;
  std::uintptr_t hidden_effect = 0;
  std::uintptr_t hidden_children = 0;
  std::int32_t hidden_capacity = -1;
  std::int32_t hidden_child_count = -1;
  std::uintptr_t context_effect = 0;
  std::uintptr_t context_vtable = 0;
  std::uintptr_t context_children = 0;
  std::int32_t context_capacity = -1;
  std::int32_t context_child_count = -1;
  std::int32_t context_scope_count = -1;
  std::uintptr_t truce_effect = 0;
  std::uintptr_t truce_vtable = 0;
  std::uintptr_t duration_script_value = 0;
  std::string_view evaluator_capture_status = "not_attempted";
  std::uintptr_t evaluator_function = 0;
  std::uintptr_t evaluator_effect_context = 0;
  std::uintptr_t evaluator_evaluation_context = 0;
  std::int32_t evaluator_first_days = -1;
  std::int32_t evaluator_second_days = -1;
  std::size_t evaluator_call_count = 0;
  bool evaluator_nonnegative = false;
  bool evaluator_stable = false;
};

const RaiktorTrucePrivateShapeCaptureV1 &
LastRaiktorTrucePrivateShapeCaptureV1() noexcept;
void ResetRaiktorTrucePrivateShapeCaptureV1() noexcept;

// Private candidate seam used only while an exact CAddTruce leaf-preview
// context is alive.  expected_truce_effect binds the callback to the authored
// index-7 target before either evaluator call is made.
RaiktorSurrenderTruceObservationV1
ObserveRaiktorSurrenderTrucePrivateLeafContextV1(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access,
    const RaiktorSurrenderTruceRequestV1 &request,
    void *expected_truce_effect) noexcept;
#endif

std::string_view RaiktorSurrenderTruceFailureReasonV1(
    RaiktorSurrenderTruceFailureV1 failure) noexcept;

RaiktorSurrenderTruceObservationV1 ObserveRaiktorSurrenderTruceV1(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access,
    const RaiktorSurrenderTruceRequestV1 &request) noexcept;

} // namespace xar::ck3_11906
