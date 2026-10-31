#include "xar_bridge/family_heir_outgoing_owner_12004.hpp"
#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"
#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"
#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"
#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/current_first_heir_relationship_v1.hpp"
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

} // namespace

bool ExecuteFamilyHeirOutgoingOwnerJob12004(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {

  if (opaque == nullptr) return false;

  auto &job = *static_cast<FamilyHeirOutgoingOwnerJob12004 *>(opaque);

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

  if (job.request.route != FamilyMarriageOutgoingRouteV2::first_heir &&
      job.request.route != FamilyMarriageOutgoingRouteV2::fulfill_betrothal) {
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
      // PREP: Requires primary_heir observation
      if (!job.primary_heir.has_value()) {
        // Data unavailable, but infrastructure is valid. Proceed to final check.
        scope_success = false;
      } else {
        const auto &heir_obs = *job.primary_heir;

        // Validate source scope matches job context
        if (heir_obs.native_revision != job.native_revision ||
            heir_obs.connection_generation != job.connection_generation ||
            heir_obs.character_id != job.request.subject) {
          // Source mismatch is data unavailable
          scope_success = false;
        } else {
          if (job.request.route == FamilyMarriageOutgoingRouteV2::first_heir) {
            if (job.read_bilateral == nullptr) {
              scope_success = false;
            } else {
              auto predicate = [&job](const MarriageProposalBilateralRelationshipV1 &pair) {
                return pair.subject_character_id == static_cast<std::uint32_t>(job.request.subject) &&
                    pair.candidate_character_id == static_cast<std::uint32_t>(job.request.candidate) &&
                    pair.subject_identity_round_trip && pair.candidate_identity_round_trip &&
                    pair.subject_alive && pair.candidate_alive &&
                    !pair.subject_has_candidate_as_spouse && !pair.candidate_has_subject_as_spouse &&
                    !pair.subject_has_candidate_as_betrothed && !pair.candidate_has_subject_as_betrothed;
              };
              MarriageProposalBilateralRelationshipV1 first_pair{};
              if (!job.read_bilateral(job.bilateral_context, job.family_bindings,
                                      static_cast<std::int32_t>(job.request.subject),
                                      static_cast<std::int32_t>(job.request.candidate), first_pair) ||
                  !predicate(first_pair)) {
                scope_success = false;
              } else {
                FamilyHeirBetrothalPreparedCopy12004 prepared{};
                job.result.materialize_status = MaterializeFamilyHeirBetrothalContext12004(
                    job.family_bindings.context, job.context_access, job.request, prepared);
                if (job.result.materialize_status == FamilyRulerMaterializeStatus12004::complete) {
                  job.result.prepared = prepared;
                  const auto definition = prepared.materialized.actual_definition;
                  if (definition != 0) {
                    const auto sender = prepared.materialized.roles[0];
                    job.result.storage_status = ReadFamilyOutgoingStorageCopy12004(
                        job.outbound_bindings, job.context_access.memory, definition, sender,
                        job.result.storage);
                  } else {
                    job.result.storage_status = FamilyOutgoingStorageCopyStatus12004::unavailable;
                  }
                }
                MarriageProposalBilateralRelationshipV1 second_pair{};
                if (!job.read_bilateral(job.bilateral_context, job.family_bindings,
                                        static_cast<std::int32_t>(job.request.subject),
                                        static_cast<std::int32_t>(job.request.candidate), second_pair) ||
                    !predicate(second_pair) || second_pair != first_pair) {
                  identity_drift = true;
                } else {
                  job.result.identity_observed = true;
                  scope_success = true;
                }
              }
            }
          } else {
            // Read relationship using the supplied callback
            if (job.read_relationship == nullptr) {
              scope_success = false;
            } else {
              ck3_11906::CurrentFirstHeirRelationshipReadV1 relationship{};
              if (!job.read_relationship(
                  job.relationship_context,
                  job.family_bindings,
                  static_cast<std::int32_t>(job.request.subject),
                  relationship)) {
                scope_success = false;
              } else {
                // Validate relationship content
                if (relationship.failure != ck3_11906::CurrentFirstHeirRelationshipFailureV1::none ||
                    relationship.heir_character_id != static_cast<std::int32_t>(job.request.subject) ||
                    relationship.relationship.betrothed_character_id != static_cast<std::int32_t>(job.request.candidate)) {
                  scope_success = false;
                } else {
                  // Materialize Context
                  FamilyHeirBetrothalPreparedCopy12004 prepared{};
                  job.result.materialize_status = MaterializeFamilyHeirBetrothalContext12004(
                      job.family_bindings.context,
                      job.context_access,
                      job.request,
                      prepared);

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

                  // Repeat relationship check to ensure identity stability
                  ck3_11906::CurrentFirstHeirRelationshipReadV1 relationship_repeat{};
                  if (!job.read_relationship(
                      job.relationship_context,
                      job.family_bindings,
                      static_cast<std::int32_t>(job.request.subject),
                      relationship_repeat)) {
                    // Identity drift or failure
                    identity_drift = true;
                  } else if (relationship_repeat.failure != ck3_11906::CurrentFirstHeirRelationshipFailureV1::none ||
                             relationship_repeat.heir_character_id != static_cast<std::int32_t>(job.request.subject) ||
                             relationship_repeat.relationship.betrothed_character_id != static_cast<std::int32_t>(job.request.candidate) ||
                             relationship_repeat.relationship != relationship.relationship) {
                    // Identity drift
                    identity_drift = true;
                  } else {
                    job.result.identity_observed = true;
                    scope_success = true;
                  }
                }
              }
            }
          }
        }
      }

    } else if (job.request.scope == FamilyMarriageOutgoingScopeV2::post_submission) {
      // POST: No primary_heir or relationship required
      // No context construction or validation

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
    // Exception implies infrastructure failure or data unavailability, but we must still check frame stability
    // However, if an exception occurred, we cannot trust partial state. We treat it as unavailable.
    scope_success = false;
    identity_drift = false; // Exception doesn't necessarily mean identity drift, but data is invalid
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
    // Note: outcome is observed, but specific fields like prepared/storage may be empty/unavailable
  } else {
    job.result.outcome = FamilyHeirOwnerOutcome12004::observed;
  }

  return true;
}

} // namespace xar::bridge
#endif
