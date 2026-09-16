#pragma once

#include "domain_construction_shared_glue_v1.hpp"
#include "domain_construction_cost_legality_live_observer_v1.hpp"
#include "player_world_building_action_candidate_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>

namespace xar::ck3::shared {

inline constexpr std::uintptr_t
    kDomainConstructionBuildingPrimaryVtableRvaV1 = 0x432F050U;
inline constexpr std::uintptr_t
    kDomainConstructionBuildingSecondaryVtableRvaV1 = 0x432F0E8U;
inline constexpr std::uintptr_t
    kDomainConstructionHoldingPrimaryVtableRvaV1 = 0x4333128U;
inline constexpr std::uintptr_t
    kDomainConstructionHoldingSecondaryVtableRvaV1 = 0x4333060U;
inline constexpr std::uintptr_t
    kDomainConstructionReceiverSingletonRvaV1 = 0x57621F0U;
inline constexpr std::size_t kDomainConstructionNativeCommandBytesV1 = 0x30U;

enum DomainConstructionApplicationMainRedV1 : std::uint32_t {
  domain_construction_application_main_red_none = 0U,
  domain_construction_application_main_red_exact_build = 1U << 0U,
  domain_construction_application_main_red_thread = 1U << 1U,
  domain_construction_application_main_red_session = 1U << 2U,
  domain_construction_application_main_red_collector_input = 1U << 3U,
  domain_construction_application_main_red_collector = 1U << 4U,
  domain_construction_application_main_red_candidate = 1U << 5U,
  domain_construction_application_main_red_backend = 1U << 6U,
};

// Every address below is borrowed from one exact application-main call. The
// runtime consumes all four frames synchronously and never copies an engine
// pointer into its result.
struct DomainConstructionBorrowedCollectorFrameV1 final {
  research::DomainConstructionCandidateSnapshotBindingV1 observed_binding;
  std::uintptr_t candidate_row_address = 0U;
  std::uintptr_t cost_vector_address = 0U;
  std::uintptr_t resource_balance_vector_address = 0U;
  research::DomainConstructionNativeFinalLegalityObservationV1 final_legality;
  std::uintptr_t new_holding_candidate_object = 0U;
};

struct DomainConstructionConcreteCandidateCaptureV1 final {
  research::DomainConstructionCandidateSnapshotBindingV1 expected_binding;
  std::array<DomainConstructionBorrowedCollectorFrameV1, 2>
      first_publication{};
  std::array<DomainConstructionBorrowedCollectorFrameV1, 2>
      second_publication{};
};

using DomainConstructionValidateBuildingNativeV1 = bool (*)(
    void* context, const void* native_command, bool& allowed) noexcept;
using DomainConstructionValidateHoldingNativeV1 = bool (*)(
    void* context, const void* native_command,
    std::int32_t candidate_province_id, std::int32_t candidate_selector,
    std::uintptr_t candidate_object, bool& allowed) noexcept;
using DomainConstructionMaterializeNativeV1 = bool (*)(
    void* context, void* native_command,
    std::uintptr_t& owned_command) noexcept;
using DomainConstructionReceiveNativeV1 = bool (*)(
    void* context, std::uintptr_t& owned_command, std::uint32_t flags,
    bool& accepted, std::uint64_t& command_sequence) noexcept;
using DomainConstructionReleaseNativeV1 = bool (*)(
    void* context, std::uintptr_t& owned_command) noexcept;

struct DomainConstructionExactNativeCallsV1 final {
  void* context = nullptr;
  bool production_exact_addresses = false;
  DomainConstructionValidateBuildingNativeV1 validate_building = nullptr;
  DomainConstructionValidateHoldingNativeV1 validate_holding = nullptr;
  DomainConstructionMaterializeNativeV1 materialize = nullptr;
  DomainConstructionReceiveNativeV1 receive = nullptr;
  DomainConstructionReleaseNativeV1 release = nullptr;
};

struct DomainConstructionApplicationMainRequestV1 final {
  bool exact_build_admitted = false;
  bool session_live = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0U;
  std::int32_t actor_or_holder_id = -1;
  std::span<const DomainConstructionConcreteCandidateCaptureV1> candidates;
  research::DomainConstructionReadMemoryV1 read_memory = nullptr;
  void* read_context = nullptr;
  DomainConstructionExactNativeCallsV1 native_calls;
};

struct DomainConstructionApplicationMainResultV1 final {
  bool executor_completed = false;
  bool collector_ready = false;
  bool submit_accepted = false;
  std::uint32_t red_flags =
      domain_construction_application_main_red_none;
  std::uint32_t collected_candidate_count = 0U;
  DomainConstructionSharedGlueStateV1 shared;
};

struct DomainConstructionApplicationMainExecutionV1 final {
  const DomainConstructionApplicationMainRequestV1* request = nullptr;
  DomainConstructionApplicationMainResultV1* result = nullptr;
};

// Controlled stock-player world tuple route for the R746 cost/legality source.
// It has no public command registration. A caller must retain this pointer-free
// state across the next paused read; pending ACK never means applied.
enum class PlayerWorldBuildingDirectActionPhaseV1 : std::uint8_t {
  idle = 0,
  rejected,
  red,
  pending_receipt,
  applied,
};

enum class PlayerWorldBuildingDirectActionFailureV1 : std::uint8_t {
  none = 0,
  already_submitted,
  frame_binding,
  candidate_drift,
  backend,
  validator,
  materialize,
  receiver,
  ownership,
};

struct PlayerWorldBuildingDirectActionStateV1 final {
  PlayerWorldBuildingDirectActionPhaseV1 phase =
      PlayerWorldBuildingDirectActionPhaseV1::idle;
  PlayerWorldBuildingDirectActionFailureV1 failure =
      PlayerWorldBuildingDirectActionFailureV1::none;
  bool production_native_path = false;
  std::uint32_t validator_calls = 0;
  std::uint32_t materialize_calls = 0;
  std::uint32_t receiver_calls = 0;
  std::uint64_t receiver_command_sequence = 0;
  ck3_11906::PlayerWorldBuildingActionCandidateV1 submitted;
};

struct PlayerWorldBuildingDirectActionRequestV1 final {
  bool exact_build_admitted = false;
  bool session_live = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  const ck3_11906::PlayerWorldBuildingSourceResultV1* source = nullptr;
  const ck3_11906::PlayerWorldBuildingActionCandidateV1* candidate = nullptr;
  DomainConstructionExactNativeCallsV1 native_calls;
};

[[nodiscard]] bool SubmitPlayerWorldBuildingDirectActionV1(
    PlayerWorldBuildingDirectActionStateV1& state,
    const PlayerWorldBuildingDirectActionRequestV1& request,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;

[[nodiscard]] bool ObservePlayerWorldBuildingDirectActionReceiptV1(
    PlayerWorldBuildingDirectActionStateV1& state,
    const ck3_11906::PlayerWorldBuildingSourceResultV1& fresh,
    std::uint64_t fresh_proof_epoch) noexcept;

[[nodiscard]] DomainConstructionExactNativeCallsV1
BindCurrentProcessDomainConstructionExactNativeCallsV1(
    std::uintptr_t module_base) noexcept;

// Signature-compatible with MainThreadQueryExecutorV1. Business RED is
// retained in result and still returns true to the mailbox; false is reserved
// for a malformed executor context.
[[nodiscard]] bool ExecuteDomainConstructionApplicationMainRuntimeV1(
    void* context,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;

}  // namespace xar::ck3::shared
