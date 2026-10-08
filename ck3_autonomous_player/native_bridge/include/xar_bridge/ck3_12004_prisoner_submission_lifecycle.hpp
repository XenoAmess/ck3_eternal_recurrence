#pragma once

#include "xar_bridge/ck3_12004_prisoner_mailbox.hpp"

namespace xar::ck3_12004 {

// Existing cached terms identify the submitted full pair. Preserve them while
// the latch remains pending; a complete collection closes it after absence.
inline bool ObservePrisonerSubmissionAfterCollection12004(
    PrisonerPrivateWorkerState12004 &state,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection) noexcept {
  if (!state.may_have_submitted || !collection.available || !collection.collection_complete ||
      collection.returned_count != collection.total_count ||
      collection.returned_count > collection.rows.size()) return false;
  std::uint32_t actor = 0, target = 0;
  if (state.current_release) {
    actor = state.current_release->observation.jailer_character_id;
    target = state.current_release->observation.prisoner_character_id;
  } else if (state.current_quote) {
    actor = static_cast<std::uint32_t>(state.current_quote->jailer_character_id);
    target = static_cast<std::uint32_t>(state.current_quote->prisoner_character_id);
  }
  if (actor == 0 || target == 0 || collection.frame.played_character_id <= 0 ||
      static_cast<std::uint32_t>(collection.frame.played_character_id) != actor) return false;
  for (std::uint32_t i = 0; i < collection.returned_count; ++i)
    if (collection.rows[i].full_character_id == target) return false;
  state.may_have_submitted = false;
  state.current_quote.reset(); state.quote_revision = state.quote_query_sequence = 0;
  state.current_release.reset(); state.release_revision = state.release_query_sequence = 0;
  return true;
}

} // namespace xar::ck3_12004
