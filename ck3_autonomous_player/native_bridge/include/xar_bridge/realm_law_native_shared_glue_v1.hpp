#pragma once

#include "xar_bridge/realm_law_enact_mutation_abi_v1.hpp"
#include "xar_bridge/realm_law_native_binder_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kRealmLawNativeSharedGlueV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kRealmLawNativeSharedGlueV1ExecutableSha256 =
        ck3_11906::private_law::kRealmLawEnactMutationExeSha256V1;
inline constexpr std::string_view
    kRealmLawNativeSharedGlueV1MutationManifestSha256 =
        ck3_11906::private_law::kRealmLawEnactMutationManifestSha256V1;
inline constexpr std::uintptr_t kRealmLawNativeSubmitCommandRvaV1 =
    0x973E00;
inline constexpr std::uint32_t kRealmLawNativeSubmitFlagsV1 = 0x0E;
inline constexpr std::size_t kRealmLawNativeAddLawCommandSizeV1 = 0x30;

enum class RealmLawNativeSharedGlueFailureV1 : std::uint8_t {
  none,
  already_prepared,
  configuration_disabled,
  exact_build_mismatch,
  module_base_invalid,
  source_signature_invalid,
  source_operations_incomplete,
  source_submit_override_forbidden,
  target_resolver_unavailable,
  offline_call_contract_invalid,
  runtime_proof_unavailable,
  runtime_proof_mismatch,
  mutation_abi_rejected,
  source_callback_failed,
  native_submit_disabled,
  submission_contract_invalid,
  target_unavailable,
  target_identity_invalid,
  target_sample_drift,
  final_legality_denied,
  native_queue_rejected,
};

// These addresses are leases for one immediate submit attempt. The resolver
// is called twice, and the glue retains neither sample after the queue call.
struct RealmLawNativeEnactTargetLeaseV1 {
  bool actor_identity_round_trip = false;
  std::uintptr_t actor_address = 0;
  std::int32_t actor_character_id = -1;
  bool group_identity_round_trip = false;
  std::uint64_t group_identity = 0;
  std::uint64_t group_generation = 0;
  RealmLawGovernanceKeyV1 group_key{};
  bool law_identity_round_trip = false;
  std::uintptr_t law_address = 0;
  std::uint64_t law_identity = 0;
  std::uint64_t law_generation = 0;
  RealmLawGovernanceKeyV1 law_key{};
  std::uint64_t connection_generation = 0;
  std::uint64_t proof_epoch = 0;

  friend bool operator==(const RealmLawNativeEnactTargetLeaseV1 &,
                         const RealmLawNativeEnactTargetLeaseV1 &) = default;
};

using ResolveRealmLawNativeEnactTargetV1 = bool (*)(
    void *context, const RealmLawEnactSubmissionV1 &submission,
    RealmLawNativeEnactTargetLeaseV1 &output) noexcept;

// Overrides exist only so the standalone test can exercise the complete
// handoff without executing CK3 code. Production preparation rejects them.
using ValidateRealmLawNativeCommandOfflineV1 = bool (*)(
    void *context, const void *command,
    std::size_t command_size) noexcept;
using SubmitRealmLawNativeCommandOfflineV1 = bool (*)(
    void *context, std::uintptr_t manager_address, const void *command,
    std::size_t command_size, std::uint32_t flags) noexcept;

struct RealmLawNativeOfflineCallsV1 {
  ValidateRealmLawNativeCommandOfflineV1 validate_command = nullptr;
  SubmitRealmLawNativeCommandOfflineV1 submit_command = nullptr;
};

struct RealmLawNativeSharedGlueConfigurationV1 {
  bool enabled = false;
  bool offline_fixture = false;
  bool native_submit_enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  std::string_view expected_source_signature_manifest_sha256{};
  ck3_11906::private_law::RealmLawMutationAbiReaderV1 mutation_abi_reader{};
  void *source_context = nullptr;
  RealmLawNativeBinderOperationsV1 source_operations{};
  void *target_context = nullptr;
  ResolveRealmLawNativeEnactTargetV1 resolve_target = nullptr;
  void *offline_call_context = nullptr;
  RealmLawNativeOfflineCallsV1 offline_calls{};
};

// Preparation double-samples the source runtime proof and the LAW6 mutation
// ABI. Successful state is thereafter pinned to those source generations and
// exports the LAW6 manifest to LAW5; no executable bytes are rehashed inside
// steady-state source callbacks.

struct RealmLawNativeSharedGlueStateV1 {
  bool prepared = false;
  bool offline_fixture = false;
  bool native_submit_enabled = false;
  std::uintptr_t module_base = 0;
  std::array<char, kRealmLawNativeBinderV1DigestCapacity>
      source_signature_manifest_sha256{};
  std::uint64_t source_signature_generation = 0;
  std::uint64_t connection_generation = 0;
  std::uint32_t application_main_thread_id = 0;
  ck3_11906::private_law::RealmLawMutationAbiReaderV1 mutation_abi_reader{};
  void *source_context = nullptr;
  RealmLawNativeBinderOperationsV1 source_operations{};
  void *target_context = nullptr;
  ResolveRealmLawNativeEnactTargetV1 resolve_target = nullptr;
  void *offline_call_context = nullptr;
  RealmLawNativeOfflineCallsV1 offline_calls{};
  RealmLawNativeSharedGlueFailureV1 failure =
      RealmLawNativeSharedGlueFailureV1::configuration_disabled;
  ck3_11906::private_law::RealmLawMutationAbiFailureV1 abi_failure =
      ck3_11906::private_law::RealmLawMutationAbiFailureV1::invalid_reader;
  const char *failed_evidence = "configuration";
  std::uint64_t target_resolve_calls = 0;
  std::uint64_t final_legality_calls = 0;
  std::uint64_t native_queue_calls = 0;
};

bool PrepareRealmLawNativeSharedGlueV1(
    const RealmLawNativeSharedGlueConfigurationV1 &configuration,
    RealmLawNativeSharedGlueStateV1 &state) noexcept;

// The returned environment points at state; state must outlive the LAW5
// binder state created from it.
RealmLawNativeBinderEnvironmentV1 MakeRealmLawNativeSharedGlueEnvironmentV1(
    RealmLawNativeSharedGlueStateV1 &state) noexcept;

std::string_view RealmLawNativeSharedGlueFailureNameV1(
    RealmLawNativeSharedGlueFailureV1 failure) noexcept;

} // namespace xar::bridge
