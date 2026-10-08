#include "xar_bridge/ck3_12004_title_own_laws_v1.hpp"
#include "xar_bridge/ck3_12003_title_laws_leaf.hpp"

#include <bit>
#include <utility>

namespace xar::ck3_12004 {
namespace {
bool Ready(const CoreSnapshotPrefix &frame) noexcept {
  return frame.clock.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.local_player_id >= 0 &&
      frame.played_character_id >= 0;
}
bool Same(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return Ready(a) && Ready(b) && a.clock.date_raw == b.clock.date_raw &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.played_character_id == b.played_character_id;
}
void *Title(const TitleOwnLawsBindingsV1 &bindings, std::uint32_t id) noexcept {
  return ck3_12002::ResolveObjectiveTitle(bindings.titles.title_holder.provinces,
                                        std::bit_cast<std::int32_t>(id));
}
} // namespace

TitleOwnLawsBindingsV1 BindTitleOwnLawsImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core) noexcept {
  TitleOwnLawsBindingsV1 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_core.enabled) return out;
  out.titles = ck3_12003::title_properties::BindImage(image_base, executable_sha256);
  if (!out.titles.enabled || !out.titles.actual4) return {};
  out.core = actual_core;
  out.enabled = true;
  return out;
}

game::ReadTitleOwnLawsV1Result ReadTitleOwnLawsV1(
    const TitleOwnLawsBindingsV1 &b, std::uint32_t title_id,
    game::TitleOwnLawsV1 &out) noexcept {
  using Result = game::ReadTitleOwnLawsV1Result;
  out = {};
  out.title_id = title_id;
  const auto fail = [&out](std::string_view reason) {
    out.available = false;
    out.unavailable_reason = reason;
    out.native_law_count.reset();
    out.laws.reset();
    out.single_heir_member.reset();
    return Result::unavailable;
  };
  try {
    if (title_id == UINT32_MAX) return fail("title_reference_absent");
    if (!b.enabled || !b.core.enabled || !b.titles.enabled || !b.titles.actual4)
      return fail("title_own_laws_bindings_unavailable");
    CoreSnapshotPrefix before{};
    if (!xar::ck3_12004::ReadCoreSnapshot(b.core, before) || !Ready(before))
      return fail("paused_player_scope_unavailable");
    out.date_raw = before.clock.date_raw;
    out.actor_character_id = before.played_character_id;
    void *actor = xar::ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id);
    if (actor == nullptr) return fail("played_character_generation_unavailable");
    void *title = Title(b, title_id);
    if (title == nullptr) return fail("title_generation_unavailable");
    game::Snapshot scope{};
    scope.date_raw = before.clock.date_raw;
    scope.speed = before.clock.speed;
    scope.paused = before.clock.paused;
    scope.player_id = before.local_player_id;
    scope.map_ready = before.map_ready;
    scope.has_played_character = before.has_played_character;
    scope.played_character_id = before.played_character_id;
    scope.played_character_alive = before.played_character_alive;
    ck3_12003::title_laws::Observation physical{};
    // This existing leaf captures all rows twice and re-resolves the complete
    // TitleID. It does not evaluate has_title_law or a Faith/realm policy.
    if (!ck3_12003::title_laws::Read(b.titles, scope, title_id, physical) ||
        !physical.available || !physical.native_count || !physical.complete_laws)
      return fail(physical.unavailable_reason.empty()
          ? "title_own_law_collection_unavailable" : physical.unavailable_reason);
    CoreSnapshotPrefix after{};
    if (!xar::ck3_12004::ReadCoreSnapshot(b.core, after) || !Same(before, after) ||
        xar::ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id) != actor)
      return fail("title_own_laws_frame_changed");
    if (Title(b, title_id) != title) return fail("title_own_laws_identity_changed");
    std::vector<game::TitleOwnLawV1> rows;
    rows.reserve(physical.complete_laws->size());
    bool member = false;
    for (const auto &law : *physical.complete_laws) {
      rows.push_back({law.native_definition_id, law.key});
      member = member || law.key == "single_heir_succession_law";
    }
    out.native_law_count = physical.native_count;
    out.laws = std::move(rows);
    out.single_heir_member = member;
    out.available = true;
    out.unavailable_reason = {};
    return Result::available;
  } catch (...) { return fail("title_own_laws_read_failed"); }
}
} // namespace xar::ck3_12004
