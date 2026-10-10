#pragma once

#include "xar_bridge/person_transfer_block10_12004.hpp"
#include "xar_bridge/person_transfer_block248_snapshot_adapter_12004.hpp"
#include "xar_bridge/person_transfer_keys_snapshot_12004.hpp"
#include "xar_bridge/person_transfer_snapshot_scope_12004.hpp"
#include "xar_bridge/person_transfer_values_snapshot_12004.hpp"

#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPersonTransferPhysicalPostimageSchema12004 =
    "xar.ck3.person-transfer-physical-postimage-12004-v1";

struct PersonTransferPostimageBindings12004 {
  bool enabled = false;
  void *read_context = nullptr;
  PersonTransferSnapshotRead12004 read_memory = nullptr;
  PersonTransferSnapshotLimits12004 limits;
};

struct PersonTransferModelPhysicalSnapshot12004 {
  PersonTransferSnapshotScope12004 scope;
  PersonTransferBlock10Snapshot12004 block10_rows;
  PersonTransferKeysSnapshot12004 block78_keys;
  PersonTransferValuesSnapshot12004 blocke0_values;
  PersonTransferBlock248SnapshotCapture12004 block248_raw64;
  bool four_descriptors_copy_complete = false;
  bool four_payloads_copy_complete = false;
  bool four_operands_copy_complete = false;
  std::string_view reason = "physical_receiver_unobserved";
};

struct PersonTransferPhysicalPair12004 {
  bool configured = false;
  PersonTransferSnapshotPhase12004 phase =
      PersonTransferSnapshotPhase12004::before_original;
  PersonTransferModelPhysicalSnapshot12004 a;
  PersonTransferModelPhysicalSnapshot12004 b;
};

// Each direction remains known independently. Descriptor equality is an
// observed diagnostic; an in-place exchange can preserve its own pointers and
// capacities while exchanging the complete ordered payloads.
struct PersonTransferPhysicalBlockComparison12004 {
  bool four_descriptors_copy_complete = false;
  bool four_payloads_copy_complete = false;
  bool four_operands_copy_complete = false;
  std::optional<bool> a_descriptor_equals_b_before;
  std::optional<bool> b_descriptor_equals_a_before;
  std::optional<bool> descriptor_cross_equal;
  std::optional<bool> a_payload_equals_b_before;
  std::optional<bool> b_payload_equals_a_before;
  std::optional<bool> payload_cross_equal;
};

struct PersonTransferPhysicalComparison12004 {
  bool original_transfer_returned = false;
  bool model_pair_matches_transfer = false;
  bool snapshot_scopes_match_transfer = false;
  std::optional<bool> same_clock_and_thread;
  std::optional<bool> completion_after_begin;
  bool same_original_observation_ready = false;
  PersonTransferPhysicalBlockComparison12004 block10_rows;
  PersonTransferPhysicalBlockComparison12004 block78_keys;
  PersonTransferPhysicalBlockComparison12004 blocke0_values;
  PersonTransferPhysicalBlockComparison12004 block248_raw64;
  bool four_block_operand_copies_complete = false;
  bool four_block_payload_comparison_ready = false;
  std::optional<bool> four_block_payloads_cross_equal;
  bool four_block_payload_exchange_observed = false;
  // A copied preparation descriptor associates B with its retained capture.
  // Its capture sequence belongs to that capture, not to the natural clock.
  // The preparation's numeric payload must still be compared by its owner.
  std::optional<bool> preparation_descriptor_matches_before_b;
  std::optional<bool> preparation_threads_match_original;
  std::optional<bool> b_before_pc_key_value_counts_equal;
  std::optional<bool> a_after_pc_key_value_counts_equal;
  std::string_view reason = "physical_postimage_unobserved";
};

struct PersonTransferPhysicalPostimage12004 {
  PersonTransferPhysicalPair12004 before;
  PersonTransferPhysicalPair12004 after;
  PersonTransferPhysicalComparison12004 comparison;
};

PersonTransferPostimageBindings12004 BindPersonTransferPostimageInputs12004(
    std::string_view build_version, std::string_view executable_sha256,
    PersonTransferSnapshotRead12004 read_memory, void *read_context = nullptr,
    PersonTransferSnapshotLimits12004 limits = {}) noexcept;

// Called by the existing 13 wrapper, after its borrowed preparation read and
// before its sole original, or after that original and completed-event read.
// No event, native helper, getter, preparation or PC dereference is invoked.
PersonTransferPhysicalPair12004 CapturePersonTransferPhysicalPair12004(
    const PersonTransferPostimageBindings12004 &bindings,
    const PersonInstalledTransferStage12004 &stage,
    PersonTransferSnapshotPhase12004 phase) noexcept;

PersonTransferPhysicalComparison12004 ComparePersonTransferPhysicalPostimage12004(
    const PersonInstalledTransferStage12004 &stage,
    const PersonTransferPhysicalPair12004 &before,
    const PersonTransferPhysicalPair12004 &after) noexcept;

// Moves the four owned copies into the occurrence record; it does not read
// memory or call the original. Query consumers use this immutable record.
PersonTransferPhysicalPostimage12004 JoinPersonTransferPhysicalPostimage12004(
    const PersonInstalledTransferStage12004 &stage,
    PersonTransferPhysicalPair12004 before,
    PersonTransferPhysicalPair12004 after) noexcept;

} // namespace xar::ck3_12004
