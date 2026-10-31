#include "xar_bridge/family_ruler_outgoing_owner_12004.hpp"

#include <limits>
#include <utility>

namespace xar::bridge {
namespace {

FamilyMarriageOutgoingFrameV2 MakeFrame(const game::Snapshot &snapshot,
                                       std::uint64_t revision) noexcept {
  return {revision, snapshot.date_raw,
      static_cast<std::uint32_t>(snapshot.played_character_id), snapshot.paused,
      snapshot.map_ready, snapshot.played_character_alive};
}

bool ReadArrangeDefinition(const ck3_12002::ContextBindings &bindings,
                           const FamilyOutgoingStorageAccess12004 &memory,
                           std::uintptr_t &definition) noexcept {
  constexpr auto top = (std::numeric_limits<std::uintptr_t>::max)();
  constexpr auto offset = ck3_12002::kMarriageArrangeMarriageInteractionOffset;
  const auto slot =
      reinterpret_cast<std::uintptr_t>(bindings.interaction_database_slot);
  std::uintptr_t database = 0;
  if (memory.read_memory == nullptr || slot == 0 ||
      sizeof(database) - 1 > top - slot ||
      !memory.read_memory(memory.context, slot, &database, sizeof(database)) ||
      database == 0 || offset > top - database)
    return false;
  const auto address = database + offset;
  return sizeof(definition) - 1 <= top - address &&
      memory.read_memory(memory.context, address, &definition,
                         sizeof(definition)) && definition != 0;
}

} // namespace

bool ExecuteFamilyRulerOutgoingOwnerJob12004(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (context == nullptr) return false;
  auto &job = *static_cast<FamilyRulerOutgoingOwnerJob12004 *>(context);
  job.result = {};
  if (job.read_snapshot == nullptr || !stamp.paused ||
      stamp.date_raw != job.expected_snapshot.date_raw)
    return true;
  game::Snapshot before{};
  if (!job.read_snapshot(job.snapshot_context, before)) return true;
  if (before != job.expected_snapshot) {
    job.result.outcome = FamilyRulerOwnerOutcome12004::frame_changed;
    return true;
  }
  if (!before.has_played_character) return true;
  const auto frame = MakeFrame(before, job.native_revision);
  if (job.request.route != FamilyMarriageOutgoingRouteV2::ruler ||
      !ValidateFamilyMarriageOutgoingRequestV2(job.request, frame)) {
    job.result.outcome = FamilyRulerOwnerOutcome12004::invalid_request;
    return true;
  }
  try {
    std::uintptr_t definition = 0;
    std::optional<std::uint32_t> sender{};
    if (job.request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
      FamilyRulerPreparedContextCopy12004 prepared{};
      job.result.materialize_status = MaterializeFamilyRulerDefaultContext12004(
          job.context_bindings, job.context_access, job.request, prepared);
      if (job.result.materialize_status == FamilyRulerMaterializeStatus12004::complete) {
        definition = prepared.actual_definition;
        sender = prepared.roles[0];
        job.result.prepared.emplace(std::move(prepared));
      }
    } else if (ReadArrangeDefinition(job.context_bindings,
                                    job.context_access.memory, definition)) {
      sender = job.request.sender;
    }
    if (sender) {
      job.result.storage_status = ReadFamilyOutgoingStorageCopy12004(
          job.outbound_bindings, job.context_access.memory, definition, *sender,
          job.result.storage);
    }
  } catch (...) {
    job.result = {};
  }
  game::Snapshot after{};
  if (!job.read_snapshot(job.snapshot_context, after) || after != before) {
    job.result = {};
    job.result.outcome = FamilyRulerOwnerOutcome12004::frame_changed;
    return true;
  }
  job.result.frame_observed = true;
  job.result.outcome = FamilyRulerOwnerOutcome12004::observed;
  return true;
}

} // namespace xar::bridge
