#include "xar_bridge/ck3_12003_player_mercenary_context.hpp"

#include <utility>

namespace xar::ck3_12003::mercenary {
namespace {
struct VisitContext {
  const ContextBindings *bindings = nullptr;
  void *actor = nullptr;
  Context *observation = nullptr;
};

bool CopyCandidate(void *company, const Candidate &candidate, void *opaque) {
  auto &visit = *static_cast<VisitContext *>(opaque);
  Row row{};
  row.candidate = candidate;
  // Collection availability is independent of a row's sampled final terms.
  // False CanHire is an observed legal predicate, not a failed market read.
  (void)ReadMercenaryFinalTerms12003(visit.bindings->final_terms, company,
                                   visit.actor, row.final_terms);
  (void)ck3_12003::ReadMercenaryPositionV1(
      visit.bindings->position, visit.bindings->world, visit.actor, company,
      row.location);
  visit.observation->rows.push_back(std::move(row));
  return true;
}
} // namespace

bool ReadPlayerMercenaryContext12003(
    const ContextBindings &bindings, void *actor, std::int32_t actor_id,
    std::int32_t date_raw, std::uint64_t capture_epoch,
    Context &observation) noexcept {
  observation = {};
  observation.actor_character_id = actor_id;
  observation.date_raw = date_raw;
  observation.capture_epoch = capture_epoch;
  try {
    if (actor == nullptr || actor_id <= 0) {
      observation.unavailable_reason = "current_played_character_unavailable";
      return false;
    }
    VisitContext visit{&bindings, actor, &observation};
    std::string collection_failure;
    if (!VisitMercenaryCandidates12003(bindings.candidates, &CopyCandidate,
                                      &visit, collection_failure)) {
      observation.unavailable_reason = collection_failure.empty()
          ? "mercenary_candidate_collection_unavailable" : collection_failure;
      return false;
    }
    observation.available = true;
    observation.unavailable_reason.clear();
    return true;
  } catch (...) {
    observation.available = false;
    observation.unavailable_reason = "mercenary_context_copy_exception";
    return false;
  }
}
} // namespace xar::ck3_12003::mercenary
