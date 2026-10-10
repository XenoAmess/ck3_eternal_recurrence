#pragma once
#include "xar_bridge/title_map_navigation_diagnostics_v1.hpp"
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge {
// The existing full-Snapshot guard, with the same order and one read at most.
// An empty error admits exactly the former else branch. No native reader is
// invoked by diagnostics; differences are calculated from the two owned DTOs.
template<class ReadCurrent>
inline std::string NonwarPrivateSnapshotGuardFailureV1(
    bool status_only,bool revision_parsed,std::uint64_t expected_revision,
    std::uint64_t native_revision,const std::optional<game::Snapshot> &previous,
    game::Snapshot &current,ReadCurrent &&read_current) {
  const auto fail=[&](std::string_view cause) {
    return std::string("nonwar private snapshot revision is stale or malformed: cause=")+
        std::string(cause)+" expected_revision="+std::to_string(expected_revision)+
        " native_revision="+std::to_string(native_revision);
  };
  if (status_only) return {};
  if (!revision_parsed) return fail("revision_parse_failed");
  if (expected_revision==0) return fail("expected_revision_zero");
  if (expected_revision!=native_revision) return fail("revision_mismatch");
  if (!previous) return fail("previous_snapshot_missing");
  if (!read_current(current)) return fail("current_snapshot_read_failed");
  if (current!=*previous) {
    auto names=ck3_11906::TitleMapNavigationSnapshotDiffNamesV1(
        ck3_11906::TitleMapNavigationSnapshotDiffMaskV1(*previous,current));
    // The existing diff helper predates this optional Snapshot member.
    if (previous->played_character_event_trait_membership!=current.played_character_event_trait_membership) {
      names.insert(names.size()-1,(names.size()>2 ? "," : "")+
          std::string("\"played_character_event_trait_membership\""));
    }
    if (names=="[]") names="[\"unlisted_snapshot_field\"]";
    return fail("full_snapshot_changed")+" changed_snapshot_fields="+names;
  }
  return {};
}
} // namespace xar::bridge
