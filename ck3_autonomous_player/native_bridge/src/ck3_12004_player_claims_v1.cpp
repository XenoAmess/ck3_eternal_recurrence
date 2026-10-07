#include "xar_bridge/ck3_12004_player_claims_v1.hpp"
#include "xar_bridge/ck3_12004_war_cash_claim_terms.hpp"
#include <algorithm>
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
bool SameClaim(const game::WarClaimSnapshot &a,
               const game::WarClaimSnapshot &b) noexcept {
  return a.title_id == b.title_id && a.present == b.present && a.state == b.state &&
      a.strong == b.strong && a.implicit == b.implicit;
}
} // namespace

PlayerClaimsBindingsV1 BindPlayerClaimsImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept {
  PlayerClaimsBindingsV1 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_core.enabled || !actual_provinces.enabled) return out;
  out.enabled = true;
  out.core = actual_core;
  out.provinces = actual_provinces;
  out.read_character_claim = reinterpret_cast<ck3_12002::ReadCharacterClaim12002>(
      image_base + kClaimTermsGetterRva);
  out.character_claim_vtable = image_base + kClaimTermsClaimVtableRva;
  return out;
}

game::ReadPlayerClaimsV1Result ReadPlayerClaimsV1(
    const PlayerClaimsBindingsV1 &b, std::span<const std::int32_t> ids,
    game::PlayerClaimsV1 &out) noexcept {
  using Result = game::ReadPlayerClaimsV1Result;
  out = {};
  auto fail = [&out](std::string_view reason) {
    out.unavailable_reason = reason;
    out.claims.clear();
    return Result::unavailable;
  };
  try {
    out.title_ids.assign(ids.begin(), ids.end());
    if (!game::ValidPlayerClaimsTitleIdsV1(ids))
      return fail("ordered_title_ids_unavailable");
    if (!b.enabled || !b.core.enabled || !b.provinces.enabled ||
        b.read_character_claim == nullptr || b.character_claim_vtable == 0)
      return fail("player_claim_bindings_unavailable");
    CoreSnapshotPrefix before{};
    if (!ck3_12004::ReadCoreSnapshot(b.core, before) || !Ready(before))
      return fail("paused_player_scope_unavailable");
    out.date_raw = before.clock.date_raw;
    out.actor_character_id = before.played_character_id;
    void *actor = ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id);
    if (actor == nullptr) return fail("played_character_generation_unavailable");
    std::vector<void *> titles;
    std::vector<game::WarClaimSnapshot> rows;
    titles.reserve(ids.size());
    rows.reserve(ids.size());
    for (const auto id : ids) {
      void *title = ck3_12002::ResolveObjectiveTitle(b.provinces, id);
      if (title == nullptr) return fail("title_generation_unavailable");
      game::WarClaimSnapshot row{};
      if (!ck3_12002::ReadCharacterClaimRowV1(b.read_character_claim,
          b.character_claim_vtable, actor, title, id, row))
        return fail("claim_row_unavailable");
      titles.push_back(title);
      rows.push_back(std::move(row));
    }
    // Re-read only these requested rows; absence stays distinct from read failure.
    for (std::size_t i = 0; i < ids.size(); ++i) {
      if (ck3_12002::ResolveObjectiveTitle(b.provinces, ids[i]) != titles[i] ||
          ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id) != actor)
        return fail("player_claim_identity_changed");
      game::WarClaimSnapshot second{};
      if (!ck3_12002::ReadCharacterClaimRowV1(b.read_character_claim,
          b.character_claim_vtable, actor, titles[i], ids[i], second) ||
          !SameClaim(rows[i], second)) return fail("player_claim_rows_changed");
    }
    CoreSnapshotPrefix after{};
    if (!ck3_12004::ReadCoreSnapshot(b.core, after) || !Same(before, after) ||
        ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id) != actor)
      return fail("player_claim_frame_changed");
    for (std::size_t i = 0; i < ids.size(); ++i)
      if (ck3_12002::ResolveObjectiveTitle(b.provinces, ids[i]) != titles[i])
        return fail("player_claim_identity_changed");
    out.claims = std::move(rows);
    out.available = true;
    out.unavailable_reason = {};
    return Result::available;
  } catch (...) { return fail("player_claim_read_failed"); }
}
} // namespace xar::ck3_12004
