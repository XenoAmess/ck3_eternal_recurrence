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
struct RaiktorTrucePrivateShapeCaptureV1 {
  std::string_view failed_check = "not_started";
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
};

const RaiktorTrucePrivateShapeCaptureV1 &
LastRaiktorTrucePrivateShapeCaptureV1() noexcept;
#endif

std::string_view RaiktorSurrenderTruceFailureReasonV1(
    RaiktorSurrenderTruceFailureV1 failure) noexcept;

RaiktorSurrenderTruceObservationV1 ObserveRaiktorSurrenderTruceV1(
    const RaiktorSurrenderTruceNativeEnvironmentV1 &environment,
    const RaiktorSurrenderTruceAccessV1 &access,
    const RaiktorSurrenderTruceRequestV1 &request) noexcept;

} // namespace xar::ck3_11906
