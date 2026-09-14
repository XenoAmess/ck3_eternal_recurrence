#pragma once

#include "xar_bridge/realm_law_governance_snapshot_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// Native addresses in these leases are valid only for the callback sequence
// that received them. The adapter re-resolves every lease for the second
// sample and never places an address in the LAW2 value snapshot.
struct RealmLawGovernanceSourcePlayerLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::int32_t character_id = -1;
};

struct RealmLawGovernanceSourceContainerLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::int32_t owner_character_id = -1;
  std::size_t group_count = 0;
};

struct RealmLawGovernanceSourceGroupLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 active_law_key{};
  bool can_change_evaluated = false;
  bool can_change = false;
  std::size_t candidate_count = 0;
};

enum class RealmLawGovernanceSourceAdapterFailureV1 : std::uint8_t {
  none,
  exact_build_mismatch,
  callbacks_unavailable,
  application_main_thread_required,
  frame_unavailable,
  not_paused,
  frame_invalid,
  player_unavailable,
  player_drift,
  container_unavailable,
  container_drift,
  group_count_invalid,
  group_unavailable,
  group_drift,
  candidate_count_invalid,
  candidate_unavailable,
  title_baseline_unavailable,
  source_sample_drift,
  frame_drift,
  working_storage_unavailable,
  core_rejected,
};

using CaptureRealmLawGovernanceSourceFrameV1 = bool (*)(
    void *context, RealmLawGovernanceFrameV1 &output) noexcept;
using ResolveRealmLawGovernanceSourcePlayerV1 = bool (*)(
    void *context, std::int32_t expected_character_id,
    RealmLawGovernanceSourcePlayerLeaseV1 &output) noexcept;
using ResolveRealmLawGovernanceSourceContainerV1 = bool (*)(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceSourceContainerLeaseV1 &output) noexcept;
using ReadRealmLawGovernanceSourceGroupV1 = bool (*)(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    std::size_t group_index,
    RealmLawGovernanceSourceGroupLeaseV1 &output) noexcept;
using ReadRealmLawGovernanceSourceCandidateV1 = bool (*)(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    const RealmLawGovernanceSourceGroupLeaseV1 &group,
    std::size_t candidate_index,
    RealmLawGovernanceCandidateV1 &output) noexcept;
using ReadRealmLawGovernanceSourceTitleBaselineV1 = bool (*)(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceTitleBaselineV1 &output) noexcept;

struct RealmLawGovernanceSourceAccessV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CaptureRealmLawGovernanceSourceFrameV1 capture_frame = nullptr;
  ResolveRealmLawGovernanceSourcePlayerV1 resolve_player = nullptr;
  ResolveRealmLawGovernanceSourceContainerV1 resolve_container = nullptr;
  ReadRealmLawGovernanceSourceGroupV1 read_group = nullptr;
  ReadRealmLawGovernanceSourceCandidateV1 read_candidate = nullptr;
  ReadRealmLawGovernanceSourceTitleBaselineV1 read_title_baseline = nullptr;
};

struct RealmLawGovernanceSourceResultV1 {
  RealmLawGovernanceSourceAdapterFailureV1 failure =
      RealmLawGovernanceSourceAdapterFailureV1::callbacks_unavailable;
  RealmLawGovernanceSnapshotV1Failure core_failure =
      RealmLawGovernanceSnapshotV1Failure::source_adapter_unavailable;
  RealmLawGovernanceSnapshotV1 snapshot{};
};

// Runs one synchronous application-main transaction. The source callbacks
// must provide GUI-equivalent engine-final can-have/can-pass/can-enact,
// opaque blocked reason and cost values. This adapter does not duplicate law
// script rules and performs no effect, command or GUI action.
bool ObserveRealmLawGovernanceSourceV1(
    const RealmLawGovernanceSourceAccessV1 &access,
    RealmLawGovernanceSourceResultV1 &output) noexcept;

std::string_view RealmLawGovernanceSourceAdapterFailureNameV1(
    RealmLawGovernanceSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::bridge
