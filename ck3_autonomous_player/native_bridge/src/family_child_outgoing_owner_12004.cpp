#include "xar_bridge/family_child_outgoing_owner_12004.hpp"
#include "xar_bridge/family_child_matrilineal_materializer_12004.hpp"
#include "xar_bridge/family_child_default_materializer_12004.hpp"
#include "xar_bridge/family_heir_outgoing_owner_12004.hpp"
#include "xar_bridge/ck3_12002_family_subject.hpp"
#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_family_outbound.hpp"
#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"
#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <type_traits>

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

namespace xar::bridge {

namespace {

// Helper to safely read the definition pointer from the interaction database slot
// using the provided memory access callback.
bool ReadArrangeDefinitionSafe(
    const ck3_12002::ContextBindings &bindings,
    const FamilyOutgoingStorageAccess12004 &memory,
    std::uintptr_t &definition) noexcept {
  if (memory.read_memory == nullptr) return false;

  const auto slot = reinterpret_cast<std::uintptr_t>(bindings.interaction_database_slot);
  if (slot == 0 || sizeof(std::uintptr_t) - 1 >
                       (std::numeric_limits<std::uintptr_t>::max)() - slot) return false;

  std::uintptr_t database = 0;
  if (!memory.read_memory(memory.context, slot, &database, sizeof(database))) return false;
  if (database == 0) return false;

  constexpr auto offset = ck3_12002::kMarriageArrangeMarriageInteractionOffset;
  if (offset > (std::numeric_limits<std::uintptr_t>::max)() - database) return false;

  const auto address = database + offset;
  if (sizeof(definition) - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;

  if (!memory.read_memory(memory.context, address, &definition, sizeof(definition))) return false;
  return definition != 0;
}

// Helper to construct the frame from the snapshot and revision.
FamilyMarriageOutgoingFrameV2 MakeFrame(const game::Snapshot &snapshot, std::uint64_t revision) noexcept {
  return {
    revision,
    snapshot.date_raw,
    static_cast<std::uint32_t>(snapshot.played_character_id),
    snapshot.paused,
    snapshot.map_ready,
    snapshot.played_character_alive
  };
}

// Mirror of SameSubject from ck3_12002_family_subject.cpp, extended to include relationship.
bool SameChildSubject(const ck3_12002::PlayerChildMarriageSubjectRead12002 &a,
                      const ck3_12002::PlayerChildMarriageSubjectRead12002 &b) noexcept {
  return a.played_character_id == b.played_character_id &&
      a.subject_character_id == b.subject_character_id &&
      a.adult_measure_raw == b.adult_measure_raw &&
      a.lineage == b.lineage &&
      a.employer_character_id == b.employer_character_id &&
      a.subject_is_player_child == b.subject_is_player_child &&
      a.adult_readback_available == b.adult_readback_available &&
      a.adult_selector_raw == b.adult_selector_raw &&
      a.adult_threshold_raw == b.adult_threshold_raw &&
      a.is_adult == b.is_adult &&
      a.relationship == b.relationship;
}

} // namespace

bool ExecuteFamilyChildOutgoingOwnerJob12004(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {

  if (opaque == nullptr) return false;

  auto &job = *static_cast<FamilyChildOutgoingOwnerJob12004 *>(opaque);

  // Clear result state at the start of execution
  job.result = {};

  // 1. Basic Stamp and Snapshot Validation
  if (!stamp.paused) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::unavailable;
    return true;
  }

  if (stamp.date_raw != job.expected_snapshot.date_raw) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::frame_changed;
    return true;
  }

  if (job.read_snapshot == nullptr) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::unavailable;
    return true;
  }

  game::Snapshot before{};
  if (!job.read_snapshot(job.snapshot_context, before)) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::unavailable;
    return true;
  }

  if (before != job.expected_snapshot) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::frame_changed;
    return true;
  }

  if (!before.has_played_character) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::unavailable;
    return true;
  }

  // 2. Request Validation
  const auto frame = MakeFrame(before, job.native_revision);

  if (job.request.route != FamilyMarriageOutgoingRouteV2::child_matrilineal &&
      job.request.route != FamilyMarriageOutgoingRouteV2::child_default) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::invalid_request;
    return true;
  }

  if (!ValidateFamilyMarriageOutgoingRequestV2(job.request, frame)) {
    job.result.outcome = FamilyHeirOwnerOutcome12004::invalid_request;
    return true;
  }

  // 3. Scope-Specific Execution
  bool scope_success = false;
  bool identity_drift = false;

  try {
    if (job.request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
      // PREP: Requires actual child subject observation

      // First successful read must have failure==none, matching IDs, child bool, adult readback
      ck3_12002::PlayerChildMarriageSubjectRead12002 first_subject{};
      bool first_read_valid = false;

      if (job.read_subject != nullptr) {
        if (job.read_subject(
            job.subject_context,
            job.subject_bindings,
            static_cast<std::int32_t>(job.request.subject),
            first_subject)) {

          // Validate first read content
          if (first_subject.failure == ck3_11906::PlayerChildMarriageSubjectFailureV1::none &&
              first_subject.played_character_id == static_cast<std::int32_t>(job.request.actor) &&
              first_subject.subject_character_id == static_cast<std::int32_t>(job.request.subject) &&
              first_subject.subject_is_player_child &&
              first_subject.adult_readback_available &&
              first_subject.adult_selector_raw <= 1) {
            first_read_valid = true;
          }
        }
      }

      if (first_read_valid) {
        // Materialize Context using the route-specific materializer
        FamilyChildMatrilinealPreparedCopy12004 prepared{};

        if (job.request.route == FamilyMarriageOutgoingRouteV2::child_matrilineal) {
          job.result.materialize_status = MaterializeFamilyChildMatrilinealContext12004(
              job.family_bindings,
              job.context_access,
              job.request,
              prepared);
        } else {
          // child_default uses ContextBindings (job.family_bindings.context) and no setter
          job.result.materialize_status = MaterializeFamilyChildDefaultContext12004(
              job.family_bindings.context,
              job.context_access,
              job.request,
              prepared);
        }

        if (job.result.materialize_status == FamilyRulerMaterializeStatus12004::complete) {
          job.result.prepared = prepared;

          // Read Storage Inventory using actual materialized definition
          std::uintptr_t definition = prepared.materialized.actual_definition;
          if (definition != 0) {
            // Use actual materialized roles[0] as sender
            const auto sender = prepared.materialized.roles[0];
            job.result.storage_status = ReadFamilyOutgoingStorageCopy12004(
                job.outbound_bindings,
                job.context_access.memory,
                definition,
                sender,
                job.result.storage);
          } else {
            job.result.storage_status = FamilyOutgoingStorageCopyStatus12004::unavailable;
          }
        }

        // Repeat the actual full child subject source after work
        ck3_12002::PlayerChildMarriageSubjectRead12002 second_subject{};

        if (job.read_subject != nullptr) {
          if (job.read_subject(
              job.subject_context,
              job.subject_bindings,
              static_cast<std::int32_t>(job.request.subject),
              second_subject)) {

            // Validate second read content
            if (second_subject.failure == ck3_11906::PlayerChildMarriageSubjectFailureV1::none &&
                second_subject.played_character_id == static_cast<std::int32_t>(job.request.actor) &&
                second_subject.subject_character_id == static_cast<std::int32_t>(job.request.subject) &&
                second_subject.subject_is_player_child &&
                second_subject.adult_readback_available &&
                second_subject.adult_selector_raw <= 1) {

              // Check stability against first read
              if (SameChildSubject(first_subject, second_subject)) {
                job.result.identity_observed = true;
                scope_success = true;
              } else {
                // Identity drift
                identity_drift = true;
              }
            } else {
              // Second read invalid
              identity_drift = true;
            }
          } else {
            // Second read failed
            identity_drift = true;
          }
        } else {
          // Callback missing for second read
          identity_drift = true;
        }
      } else {
        // First read invalid or missing callback: take no constructor/stock reads
        // Still read the actual final snapshot and return observed/frame_observed with all data unavailable if stable
        scope_success = false;
      }

    } else if (job.request.scope == FamilyMarriageOutgoingScopeV2::post_submission) {
      // POST: No child reader, no context constructor or setter, no PREP identity required
      // Use actual context interaction_database_slot pointer then canonical definition

      std::uintptr_t definition = 0;
      if (!ReadArrangeDefinitionSafe(job.family_bindings.context, job.context_access.memory, definition)) {
        job.result.storage_status = FamilyOutgoingStorageCopyStatus12004::unavailable;
      } else {
        // Use retained request.sender
        if (job.request.sender.has_value()) {
          job.result.storage_status = ReadFamilyOutgoingStorageCopy12004(
              job.outbound_bindings,
              job.context_access.memory,
              definition,
              *job.request.sender,
              job.result.storage);
        } else {
          job.result.storage_status = FamilyOutgoingStorageCopyStatus12004::unavailable;
        }
      }

      // Prepared remains absent, materialize_status notcomplete
      job.result.prepared.reset();
      job.result.materialize_status = FamilyRulerMaterializeStatus12004::unavailable;
      scope_success = true; // Infrastructure completed, data availability determined by storage_status
    }

  } catch (...) {
    // Allocation or native exceptions
    job.result = {};
    job.result.outcome = FamilyHeirOwnerOutcome12004::unavailable;
    scope_success = false;
    identity_drift = false;
  }

  // 4. Final Frame Validation
  game::Snapshot after{};
  if (!job.read_snapshot(job.snapshot_context, after)) {
    job.result = {};
    job.result.outcome = FamilyHeirOwnerOutcome12004::frame_changed;
    job.result.frame_observed = false;
    return true;
  }

  if (after != before) {
    job.result = {};
    job.result.outcome = FamilyHeirOwnerOutcome12004::frame_changed;
    job.result.frame_observed = false;
    return true;
  }

  // Success
  job.result.frame_observed = true;

  if (identity_drift) {
    job.result = {};
    job.result.outcome = FamilyHeirOwnerOutcome12004::identity_changed;
    job.result.frame_observed = false;
    return true;
  }

  if (!scope_success) {
    // Data unavailable, but frame is stable
    job.result.outcome = FamilyHeirOwnerOutcome12004::observed;
  } else {
    job.result.outcome = FamilyHeirOwnerOutcome12004::observed;
  }

  return true;
}

} // namespace xar::bridge
#endif
