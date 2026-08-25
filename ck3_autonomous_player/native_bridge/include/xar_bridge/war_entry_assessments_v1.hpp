#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

struct WarEntryAssessmentFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool actor_alive = false;
  std::int32_t actor_character_id = -1;
  std::vector<std::int32_t> declarable_target_character_ids;

  friend bool operator==(const WarEntryAssessmentFrameV1 &,
                         const WarEntryAssessmentFrameV1 &) = default;
};

struct WarEntryAssessmentRowV1 {
  std::int32_t target_character_id = -1;
  std::int32_t effective_target_character_id = -1;
  std::int64_t distance_raw = 0;
  std::int64_t actor_power_base_raw = 0;
  std::int64_t actor_network_contribution_raw = 0;
  std::int64_t actor_power_total_raw = 0;
  std::int64_t target_power_base_raw = 0;
  std::int64_t target_network_contribution_raw = 0;
  std::int64_t target_pre_adjustment_total_raw = 0;
  std::int64_t target_adjustment_delta_raw = 0;
  std::int64_t target_power_total_raw = 0;
  std::int64_t actual_power_ratio_raw = 0;
  std::int32_t target_ai_context_actor_entry_raw = 0;
  std::int32_t actor_ai_context_target_entry_raw = 0;
  std::uint8_t native_flags_raw = 0;

  friend bool operator==(const WarEntryAssessmentRowV1 &,
                         const WarEntryAssessmentRowV1 &) = default;
};

struct WarEntryAssessmentReadinessV1 {
  bool actor_identity_ready = false;
  bool targets_declarable_ready = false;
  bool effective_targets_ready = false;
  // Legacy wire key retained for schema-v1 compatibility.  In production it
  // means the authoritative 0x18784D0 native actor State16 builder is exact,
  // stable and double-sampled; it does not assert that a manager AIContext
  // exists for the human player.
  bool ai_context_ready = false;
  bool native_output_ready = false;
  bool network_decomposition_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const WarEntryAssessmentReadinessV1 &,
                         const WarEntryAssessmentReadinessV1 &) = default;
};

// Only a fully available result is serializable.  Failures retain a local
// stage for the command error but publish neither partial rows nor null-valued
// substitutes for the original AI assessment.
struct WarEntryAssessmentsV1 {
  bool available = false;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::vector<std::int32_t> requested_target_character_ids;
  std::vector<WarEntryAssessmentRowV1> assessments;
  WarEntryAssessmentReadinessV1 readiness;
  std::string unavailable_stage;

  friend bool operator==(const WarEntryAssessmentsV1 &,
                         const WarEntryAssessmentsV1 &) = default;
};

enum class ReadWarEntryAssessmentsV1Result {
  available,
  invalid_arguments,
  requires_paused,
  revision_mismatch,
  unavailable,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kWarEntryAssessmentsV1Capability =
    "game.command.query-war-entry-assessments-v1-N";
inline constexpr std::string_view kWarEntryAssessmentsV1StepPrefix =
    "query-war-entry-assessments-v1-";
inline constexpr bool kWarEntryAssessmentsV1CapabilityAdvertised = true;
inline constexpr std::int32_t kWarEntryAssessmentsV1MaximumTargets = 1;
inline constexpr std::int32_t kWarEntryAssessmentsV1FirstLiveMaximumTargets =
    kWarEntryAssessmentsV1MaximumTargets;
inline constexpr std::int64_t kWarEntryAssessmentsV1FixedPointScale = 100'000;
inline constexpr std::string_view kWarEntryAssessmentsV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kWarEntryAssessmentsV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t kWarEntryAssessmentRva = 0x1878A00;
inline constexpr std::uintptr_t kWarEntryActorStateBuilderRva = 0x18784D0;
inline constexpr std::uintptr_t kWarEntryNetworkCollectorRva = 0x1879850;
inline constexpr std::uintptr_t kWarEntryEffectiveTargetResolverRva =
    0x2909D30;
inline constexpr std::uintptr_t kWarEntryGameStateSlotRva = 0x570E068;
inline constexpr std::uintptr_t kWarEntryCharacterStorageSlotRva = 0x570C130;
inline constexpr std::uintptr_t kWarEntryCharacterFallbackSlotRva = 0x570C138;
inline constexpr std::uintptr_t kWarEntryActorStateDependencySlotRva =
    0x570C638;

// 0x18784D0 constructs the exact actor-side state consumed by 0x1878A00.
// Production builds this complete caller-owned shape immediately before each
// native sample.  The historical actor AI context is neither an admission
// gate nor a source of copied fields.
struct NativeWarEntryActorStateV1 {
  std::int64_t power_base_raw = 0;
  std::int32_t native_state_08_raw = 0;
  std::uint16_t native_state_0c_raw = 0;
  std::uint8_t native_flags_raw = 0;
  std::uint8_t native_state_0f_raw = 0;

  friend bool operator==(const NativeWarEntryActorStateV1 &,
                         const NativeWarEntryActorStateV1 &) = default;
};

// 0x1878A00 writes this exact 0x28-byte caller-owned shape.  The byte at
// +0x20 is a raw native bitfield; the seven trailing bytes are alignment only.
struct NativeWarEntryAssessmentOutputV1 {
  std::int64_t distance_raw = 0;
  std::int64_t target_power_total_raw = 0;
  std::int64_t actual_power_ratio_raw = 0;
  std::int32_t target_ai_context_actor_entry_raw = 0;
  std::int32_t actor_ai_context_target_entry_raw = 0;
  std::uint8_t native_flags_raw = 0;
  std::uint8_t alignment_padding[7]{};
};

// 0x1879850 receives five pointers to synchronous caller-owned locals.  The
// pointed-to root/filters/accumulator must outlive the call and nothing may be
// cached after it returns.
struct NativeWarEntryNetworkConfigurationV1 {
  void **root_character = nullptr;
  std::int32_t *filter_a = nullptr;
  std::int32_t *filter_b = nullptr;
  std::int32_t *filter_c = nullptr;
  std::int64_t *accumulator = nullptr;
};

static_assert(sizeof(NativeWarEntryAssessmentOutputV1) == 0x28);
static_assert(sizeof(NativeWarEntryActorStateV1) == 0x10);
static_assert(offsetof(NativeWarEntryActorStateV1, power_base_raw) == 0x00);
static_assert(offsetof(NativeWarEntryActorStateV1, native_state_08_raw) ==
              0x08);
static_assert(offsetof(NativeWarEntryActorStateV1, native_state_0c_raw) ==
              0x0C);
static_assert(offsetof(NativeWarEntryActorStateV1, native_flags_raw) == 0x0E);
static_assert(offsetof(NativeWarEntryActorStateV1, native_state_0f_raw) ==
              0x0F);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1, distance_raw) == 0x00);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1,
                       target_power_total_raw) == 0x08);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1,
                       actual_power_ratio_raw) == 0x10);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1,
                       target_ai_context_actor_entry_raw) == 0x18);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1,
                       actor_ai_context_target_entry_raw) == 0x1C);
static_assert(offsetof(NativeWarEntryAssessmentOutputV1, native_flags_raw) ==
              0x20);
static_assert(sizeof(NativeWarEntryNetworkConfigurationV1) == 0x28);
static_assert(offsetof(NativeWarEntryNetworkConfigurationV1,
                       root_character) == 0x00);
static_assert(offsetof(NativeWarEntryNetworkConfigurationV1, filter_a) ==
              0x08);
static_assert(offsetof(NativeWarEntryNetworkConfigurationV1, filter_b) ==
              0x10);
static_assert(offsetof(NativeWarEntryNetworkConfigurationV1, filter_c) ==
              0x18);
static_assert(offsetof(NativeWarEntryNetworkConfigurationV1, accumulator) ==
              0x20);

#if defined(_MSC_VER)
#define XAR_WAR_ENTRY_FASTCALL __fastcall
#else
#define XAR_WAR_ENTRY_FASTCALL
#endif

using NativeWarEntryActorStateBuilderFunctionV1 = void(
    XAR_WAR_ENTRY_FASTCALL *)(void *actor_character,
                             NativeWarEntryActorStateV1 *output);

// RDX is the complete 0x10-byte state built by 0x18784D0.  The assessment
// reads both the qword at +0x00 and a flag byte at +0x0E, so this must never be
// replaced with a standalone copied power value.
using NativeWarEntryAssessmentFunctionV1 = void(XAR_WAR_ENTRY_FASTCALL *)(
    void *actor_character, const NativeWarEntryActorStateV1 *actor_state,
    void *effective_target_character, NativeWarEntryAssessmentOutputV1 *output,
    const std::int64_t *distance_override, std::int32_t include_network_mode);
using NativeWarEntryNetworkCollectorFunctionV1 = void(
    XAR_WAR_ENTRY_FASTCALL *)(void *root_character,
                             NativeWarEntryNetworkConfigurationV1 *configuration);
using NativeWarEntryEffectiveTargetResolverFunctionV1 = void *(
    XAR_WAR_ENTRY_FASTCALL *)(void *actor_character, void *target_character,
                             std::uint32_t unused_home_value,
                             bool alternate_resolution_mode);

#undef XAR_WAR_ENTRY_FASTCALL

struct WarEntryNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  void **game_state_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **actor_state_dependency_slot = nullptr;
  NativeWarEntryActorStateBuilderFunctionV1 actor_state_builder = nullptr;
  NativeWarEntryAssessmentFunctionV1 assessment = nullptr;
  NativeWarEntryNetworkCollectorFunctionV1 network_collector = nullptr;
  NativeWarEntryEffectiveTargetResolverFunctionV1 effective_target_resolver =
      nullptr;
  // This escape hatch is accepted only by the offline fixture. Production
  // callers must use BindWarEntryNativeEnvironmentV1 and exact RVA identity.
  bool offline_fixture_function_overrides = false;
};

using CaptureWarEntryAssessmentFrameV1 = bool (*)(
    void *context, game::WarEntryAssessmentFrameV1 &output) noexcept;
using IsWarEntryAssessmentMainThreadV1 = bool (*)(void *context) noexcept;
using ReadWarEntryAssessmentMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;

struct WarEntryAssessmentAccessV1 {
  void *context = nullptr;
  CaptureWarEntryAssessmentFrameV1 capture_frame = nullptr;
  // Mandatory world-consistency gate. Production marshals this native
  // evaluator through the query-specific application-main mailbox; direct
  // bridge-worker invocation remains forbidden.
  IsWarEntryAssessmentMainThreadV1 is_main_thread = nullptr;
  // Null selects the guarded in-process reader. Fixtures can inject a bounded
  // address-space reader to prove every pointer/count rejection independently.
  ReadWarEntryAssessmentMemoryV1 read_memory = nullptr;
};

struct WarEntryAssessmentsV1Request {
  std::uint64_t expected_snapshot_revision = 0;
  std::vector<std::int32_t> target_character_ids;
};

WarEntryNativeEnvironmentV1
BindWarEntryNativeEnvironmentV1(std::uintptr_t module_base) noexcept;

bool ParseWarEntryAssessmentsV1Step(
    std::string_view step,
    std::vector<std::int32_t> &target_character_ids) noexcept;

std::string EncodeWarEntryAssessmentsV1Step(
    const std::vector<std::int32_t> &target_character_ids);

game::ReadWarEntryAssessmentsV1Result ReadWarEntryAssessmentsV1(
    const WarEntryNativeEnvironmentV1 &environment,
    const WarEntryAssessmentAccessV1 &access,
    const WarEntryAssessmentsV1Request &request,
    game::WarEntryAssessmentsV1 &output) noexcept;

// Returns an empty string unless the complete readiness contract is true.
// Command failures use `war_entry_assessment_unavailable:<stage>` and never a
// JSON success body with partial/null rows.
std::string
SerializeWarEntryAssessmentsV1(const game::WarEntryAssessmentsV1 &result);

} // namespace xar::ck3_11906
