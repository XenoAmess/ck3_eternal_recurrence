#pragma once

#include "domain_construction_native_submit_adapter_v1.hpp"

#include <cstdint>
#include <span>

namespace xar::ck3::shared {

enum class DomainConstructionSharedPhaseV1 : std::uint8_t {
  idle = 0,
  candidate_ready,
  pending_receipt,
  applied,
  red,
};

enum class DomainConstructionSharedRedV1 : std::uint32_t {
  none = 0U,
  candidate_selection = 1U << 0U,
  candidate_binding = 1U << 1U,
  exact_build = 1U << 2U,
  application_main_thread = 1U << 3U,
  native_backend_unwired = 1U << 4U,
  validator = 1U << 5U,
  materialize = 1U << 6U,
  receiver = 1U << 7U,
  ownership_lifecycle = 1U << 8U,
  receipt = 1U << 9U,
  duplicate_submit = 1U << 10U,
};

struct DomainConstructionNativeBackendEnvironmentV1 final {
  bool exact_build_admitted = false;
  bool application_main_thread = false;
  bool concrete_native_backend_bound = false;
  bool offline_fixture_backend = false;
};

using ValidateDomainConstructionNativeCommandV1 = bool (*)(
    void* context,
    const research::DomainConstructionNativeCommandContextV1& command,
    const research::DomainConstructionTransientNativeSubmitContextV1&
        transient,
    bool& allowed) noexcept;

using MaterializeDomainConstructionNativeCommandV1 = bool (*)(
    void* context,
    const research::DomainConstructionNativeCommandContextV1& command,
    const research::DomainConstructionTransientNativeSubmitContextV1&
        transient,
    std::uintptr_t& owned_command) noexcept;

using ReceiveDomainConstructionNativeCommandV1 = bool (*)(
    void* context, std::uintptr_t& owned_command, std::uint32_t receiver_flags,
    bool& accepted, std::uint64_t& command_sequence) noexcept;

using ReleaseDomainConstructionNativeCommandV1 = bool (*)(
    void* context, std::uintptr_t& owned_command) noexcept;

struct DomainConstructionNativeBackendAccessV1 final {
  void* context = nullptr;
  ValidateDomainConstructionNativeCommandV1 validate = nullptr;
  MaterializeDomainConstructionNativeCommandV1 materialize = nullptr;
  ReceiveDomainConstructionNativeCommandV1 receive = nullptr;
  ReleaseDomainConstructionNativeCommandV1 release = nullptr;
};

struct DomainConstructionSharedGlueStateV1 final {
  DomainConstructionSharedPhaseV1 phase = DomainConstructionSharedPhaseV1::idle;
  std::uint32_t red_flags = 0U;
  bool candidate_ready = false;
  bool candidate_live = false;
  research::DomainConstructionActionSelectionFailureV1 selection_failure =
      research::DomainConstructionActionSelectionFailureV1::none;
  research::DomainConstructionNativeSubmitFailureV1 native_failure =
      research::DomainConstructionNativeSubmitFailureV1::none;
  research::DomainConstructionReceiptFailureV1 receipt_failure =
      research::DomainConstructionReceiptFailureV1::none;
  research::DomainConstructionSemanticActionRequestV1 candidate;
  research::DomainConstructionNativeSubmitStateV1 native_submit;
};

[[nodiscard]] bool PrepareDomainConstructionSharedCandidateV1(
    DomainConstructionSharedGlueStateV1& state,
    std::span<const research::DomainConstructionCostLegalityPublicationV1>
        first_sample,
    std::span<const research::DomainConstructionCostLegalityPublicationV1>
        second_sample) noexcept;

[[nodiscard]] bool SubmitDomainConstructionSharedCandidateV1(
    DomainConstructionSharedGlueStateV1& state,
    const DomainConstructionNativeBackendEnvironmentV1& environment,
    const DomainConstructionNativeBackendAccessV1& backend,
    const research::DomainConstructionCandidateSnapshotBindingV1&
        observed_binding,
    std::int32_t actor_or_holder_id,
    std::uintptr_t new_holding_candidate_object) noexcept;

[[nodiscard]] bool ObserveDomainConstructionSharedReceiptV1(
    DomainConstructionSharedGlueStateV1& state,
    research::DomainConstructionNativeReceiptSourceV1 source,
    const research::DomainConstructionFreshReceiptV1& receipt) noexcept;

[[nodiscard]] bool DomainConstructionSharedGlueHasRedV1(
    const DomainConstructionSharedGlueStateV1& state,
    DomainConstructionSharedRedV1 red) noexcept;

}  // namespace xar::ck3::shared
