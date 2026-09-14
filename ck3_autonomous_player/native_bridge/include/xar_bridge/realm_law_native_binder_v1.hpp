#pragma once

#include "xar_bridge/realm_law_enact_action_v1.hpp"
#include "xar_bridge/realm_law_governance_source_adapter_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kRealmLawNativeBinderV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kRealmLawNativeBinderV1ExecutableSha256 =
    kRealmLawGovernanceSnapshotV1ExecutableSha256;
inline constexpr std::string_view kRealmLawNativeBinderV1EvidenceRevision =
    "g2_nonreligious_law_contract_succession_native_tree_v1@d2fc0fd";
inline constexpr bool kRealmLawNativeBinderV1HasFrozenNativeOffsets = false;
inline constexpr std::size_t kRealmLawNativeBinderV1DigestCapacity = 65;

struct RealmLawNativeRuntimeProofV1 {
  bool exact_build_admitted = false;
  std::array<char, kRealmLawNativeBinderV1DigestCapacity> executable_sha256{};
  std::uintptr_t module_base = 0;
  bool signatures_complete = false;
  std::array<char, kRealmLawNativeBinderV1DigestCapacity>
      signature_manifest_sha256{};
  std::uint64_t signature_generation = 0;
  std::uint64_t connection_generation = 0;
  std::uint64_t proof_epoch = 0;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  bool paused = false;

  friend bool operator==(const RealmLawNativeRuntimeProofV1 &,
                         const RealmLawNativeRuntimeProofV1 &) = default;
};

struct RealmLawNativeResourceSampleV1 {
  bool complete = false;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::uint32_t resource_count = 0;
  std::array<RealmLawEnactResourceBalanceV1,
             kRealmLawEnactMaximumResourcesV1>
      resources{};
};

enum class RealmLawNativeSubmitDispositionV1 : std::uint8_t {
  not_submitted,
  submitted,
  submitted_outcome_unknown,
};

using ReadRealmLawNativeRuntimeProofV1 = bool (*)(
    void *context, RealmLawNativeRuntimeProofV1 &output) noexcept;
using ReadRealmLawNativeResourcesV1 = bool (*)(
    void *context, const RealmLawGovernanceSnapshotV1 &law_snapshot,
    RealmLawNativeResourceSampleV1 &output) noexcept;
using SubmitRealmLawNativeEnactV1 = RealmLawNativeSubmitDispositionV1 (*)(
    void *context, const RealmLawEnactSubmissionV1 &submission) noexcept;

// No production address is supplied by this contract. A later exact-build
// binder must populate every operation from reviewed disassembly evidence and
// provide a runtime signature-manifest proof. Tests use the same table with an
// explicitly labelled offline fixture.
struct RealmLawNativeBinderOperationsV1 {
  ReadRealmLawNativeRuntimeProofV1 read_runtime_proof = nullptr;
  CaptureRealmLawGovernanceSourceFrameV1 capture_frame = nullptr;
  ResolveRealmLawGovernanceSourcePlayerV1 resolve_player = nullptr;
  ResolveRealmLawGovernanceSourceContainerV1 resolve_container = nullptr;
  ReadRealmLawGovernanceSourceGroupV1 read_group = nullptr;
  ReadRealmLawGovernanceSourceCandidateV1 read_candidate = nullptr;
  ReadRealmLawGovernanceSourceTitleBaselineV1 read_title_baseline = nullptr;
  ReadRealmLawNativeResourcesV1 read_resources = nullptr;
  SubmitRealmLawNativeEnactV1 submit_enact = nullptr;
};

struct RealmLawNativeBinderEnvironmentV1 {
  bool binding_enabled = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  std::string_view expected_signature_manifest_sha256{};
  void *native_context = nullptr;
  RealmLawNativeBinderOperationsV1 operations{};
};

// This state contains one complete value-only LAW4 observation so the submit
// thunk can recapture native state and reject resource/succession drift. Keep
// it in durable global or heap storage; do not place it on a small stack.
struct RealmLawNativeBinderStateV1 {
  bool attached = false;
  bool offline_fixture = false;
  bool integrity_failed = false;
  bool post_submit_integrity_failed = false;
  std::uintptr_t module_base = 0;
  std::array<char, kRealmLawNativeBinderV1DigestCapacity> executable_sha256{};
  std::array<char, kRealmLawNativeBinderV1DigestCapacity>
      signature_manifest_sha256{};
  std::uint64_t signature_generation = 0;
  std::uint64_t connection_generation = 0;
  std::uint32_t application_main_thread_id = 0;
  void *native_context = nullptr;
  RealmLawNativeBinderOperationsV1 operations{};
  bool source_transaction_open = false;
  std::uint64_t source_transaction_proof_epoch = 0;
  std::uint64_t action_capture_serial = 0;
  bool last_action_observation_available = false;
  RealmLawEnactActionObservationV1 last_action_observation{};
  bool submit_pending = false;
  RealmLawEnactSubmissionV1 last_submission{};
};

bool AssignRealmLawNativeDigestV1(
    std::string_view value,
    std::array<char, kRealmLawNativeBinderV1DigestCapacity> &output) noexcept;

bool BindRealmLawNativeV1(
    const RealmLawNativeBinderEnvironmentV1 &environment,
    RealmLawNativeBinderStateV1 &state) noexcept;

RealmLawGovernanceSourceAccessV1 MakeRealmLawNativeSourceAccessV1(
    RealmLawNativeBinderStateV1 &state) noexcept;

RealmLawEnactActionAccessV1 MakeRealmLawNativeActionAccessV1(
    RealmLawNativeBinderStateV1 &state) noexcept;

RealmLawEnactActionAckStatusV1 ExecuteBoundRealmLawNativeEnactV1(
    RealmLawNativeBinderStateV1 &state,
    const RealmLawEnactActionRequestV1 &request,
    RealmLawEnactActionAckV1 &ack) noexcept;

RealmLawEnactActionReceiptStatusV1 VerifyBoundRealmLawNativeReceiptV1(
    RealmLawNativeBinderStateV1 &state,
    const RealmLawEnactActionAckV1 &ack,
    RealmLawEnactActionReceiptV1 &receipt) noexcept;

} // namespace xar::bridge
