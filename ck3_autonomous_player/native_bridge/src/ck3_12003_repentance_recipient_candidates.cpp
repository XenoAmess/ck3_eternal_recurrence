#include "xar_bridge/ck3_12003_repentance_recipient_candidates.hpp"

#include <algorithm>
#include <bit>
#include <functional>
#include <cstring>
#include <sstream>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::repentance_candidates {
namespace {
template <typename T> bool Read(const void *base, std::size_t offset, T &out) noexcept {
  if (!base) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&out, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename Result, typename... Args>
bool Call(Fn fn, Result &out, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out = fn(args...); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
void Success(Role &out, std::int32_t id) noexcept {
  out.available = true; out.reason = "none"; out.character_id = id;
}
void *ResolveTitle(const Bindings &b, std::int32_t id) noexcept {
  void *storage = nullptr, *rows = nullptr, *title = nullptr;
  std::int32_t count = 0, actual = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0x00ffffffU;
  if (id == -1 || !Read(b.title_storage_slot, 0, storage) ||
      !Read(storage, 0x20, rows) || !Read(storage, 0x2c, count) || count <= 0 ||
      index >= static_cast<std::uint32_t>(count) ||
      !Read(rows, index * 16ULL + 8, title) || !Read(title, 0x10, actual) || actual != id)
    return nullptr;
  return title;
}
void Superior(const Bindings &b, std::int32_t id, Role &out) noexcept {
  if (id == -1) { Success(out, -1); return; }
  void *game = nullptr, *data = nullptr;
  std::int32_t superior = -1;
  std::int32_t *returned = nullptr;
  out.reason = "superior_lookup_unavailable";
  if (!Read(b.game_state_slot, 0, game) || !Read(game, 0xa0, data) || !data ||
      !Call(b.lease_liege, returned, static_cast<std::byte *>(data) + 0x1f1e0,
            &superior, id) || returned != &superior) return;
  if (superior == -1) {
    if (!Call(b.top_lease_liege_direct, returned, &superior, id) || returned != &superior) return;
    if (superior == id) superior = -1;
  }
  if (superior != -1 && !ck3_12002::ResolveCoreCharacter(b.core, superior)) {
    out.reason = "superior_character_unavailable"; return;
  }
  Success(out, superior);
}
void Capital(const Bindings &b, void *player, Context &out) noexcept {
  auto &role = out.roles[1];
  role.reason = "capital_barony_unavailable";
  std::int32_t barony = -1, county = -1, holder = -1;
  std::int32_t *returned = nullptr;
  if (!Call(b.capital_barony, returned, player, &barony) || returned != &barony) return;
  out.capital_barony_title_id = barony;
  if (barony == -1) {
    out.capital_county_title_id = -1; out.capital_clerical_region_title_id = -1;
    Success(role, -1); return;
  }
  role.reason = "capital_county_unavailable";
  auto *barony_object = ResolveTitle(b, barony);
  if (!Read(barony_object, 0x108, county)) return;
  out.capital_county_title_id = county;
  if (county == -1) { out.capital_clerical_region_title_id = -1; Success(role, -1); return; }
  if (!ResolveTitle(b, county)) return;
  Scope16 input{5, 0, static_cast<std::uint32_t>(county)}, region{};
  const Scope16 *input_pointer = &input;
  Scope16 *region_returned = nullptr;
  role.reason = "capital_clerical_region_unavailable";
  if (!Call(b.clerical_region, region_returned, static_cast<void *>(nullptr),
            &region, &input_pointer) || region_returned != &region || region.kind != 5 ||
      region.id > UINT32_MAX) return;
  out.capital_clerical_region_title_id = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(region.id));
  if (region.id == UINT32_MAX) { Success(role, -1); return; }
  auto *title = ResolveTitle(b, std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(region.id)));
  role.reason = "capital_clerical_holder_unavailable";
  if (!Read(title, 0x128, holder) ||
      (holder != -1 && !ck3_12002::ResolveCoreCharacter(b.core, holder))) return;
  Success(role, holder);
}
void Quote(std::ostream &out, std::string_view text) {
  out << '"';
  for (const char c : text) { if (c == '"' || c == '\\') out << '\\'; out << c; }
  out << '"';
}
template <typename T> void Number(std::ostream &out, const std::optional<T> &v) {
  if (v) out << *v; else out << "null";
}
} // namespace

Bindings BindRepentanceRecipientCandidatesImage12003(std::uintptr_t base,
    std::string_view sha, const ck3_12002::CoreBindings &core,
    const ck3_12002::religion::clergy::Bindings &clergy) noexcept {
  Bindings b{};
  if (!base || sha != repentance::kExecutableSha256) return b;
  b.enabled = true; b.core = core; b.clergy = clergy;
  b.read_clergy = &ck3_12002::religion::clergy::ResolveCurrentClergySeat12002;
  b.game_state_slot = reinterpret_cast<void **>(base + 0x5c68c50);
  b.title_storage_slot = reinterpret_cast<void **>(base + 0x5d1daf8);
  b.authority = reinterpret_cast<ObjectGetter>(base + 0x2be1ba0);
  b.lease_liege = reinterpret_cast<LeaseLiege>(base + 0x2a22fa0);
  b.top_lease_liege_direct = reinterpret_cast<TopLiege>(base + 0x2a268a0);
  b.capital_barony = reinterpret_cast<CapitalBarony>(base + 0x28b2220);
  b.clerical_region = reinterpret_cast<ClericalRegion>(base + 0x1b9c9e0);
  return b;
}
bool ReadRepentanceRecipientCandidates12003(const Bindings &b,
    const repentance::Bindings &request, void *player, std::int32_t actor,
    std::int32_t date, std::uint64_t epoch, Context &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = actor;
  constexpr std::array<const char *, 5> sources{
      "court_chaplain_superior", "capital_clerical_region_holder", "actor_superior",
      "religious_head_or_challenger", "court_chaplain"};
  for (std::size_t i = 0; i < sources.size(); ++i) out.roles[i].source = sources[i];
  std::int32_t actual = -1;
  if (!b.enabled || !b.core.enabled) return false;
  if (!Read(player, 0x18, actual) || actual != actor || actor == -1) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  ck3_12002::religion::clergy::CurrentClergySeat seat{};
  bool seat_read = false;
  out.roles[4].reason = "court_chaplain_unavailable";
  if (Call(b.read_clergy, seat_read, b.clergy, actor, std::ref(seat)) && seat_read)
    Success(out.roles[4], seat.incumbent_character_id);
  if (out.roles[4].available) Superior(b, seat.incumbent_character_id, out.roles[0]);
  else out.roles[0].reason = "court_chaplain_unavailable";
  Capital(b, player, out);
  Superior(b, actor, out.roles[2]);
  out.roles[3].reason = "religious_head_or_challenger_unavailable";
  void *authority = nullptr;
  if (Call(b.authority, authority, player)) {
    std::int32_t id = -1;
    if (!authority) Success(out.roles[3], -1);
    else if (Read(authority, 0x18, id) &&
             (id == -1 || ck3_12002::ResolveCoreCharacter(b.core, id) == authority))
      Success(out.roles[3], id);
  }
  for (const auto &role : out.roles) {
    if (!role.available || !role.character_id || *role.character_id == -1 ||
        *role.character_id == actor) continue;
    const auto id = *role.character_id;
    auto existing = std::find_if(out.candidates.begin(), out.candidates.end(),
        [id](const Candidate &c) { return c.requested_recipient_character_id == id; });
    if (existing != out.candidates.end()) { existing->sources.push_back(role.source); continue; }
    Candidate candidate{}; candidate.requested_recipient_character_id = id;
    candidate.sources.push_back(role.source);
    (void)repentance::ReadRepentanceRecipientContext12003(request, player, actor, date,
        epoch, id, candidate.terms);
    if (!out.first_observed_ordinary_legal_recipient_character_id && candidate.terms.available &&
        candidate.terms.player_excommunication.value.value_or(false) &&
        candidate.terms.shown.value.value_or(false) && candidate.terms.can_send.value.value_or(false))
      out.first_observed_ordinary_legal_recipient_character_id = id;
    out.candidates.push_back(std::move(candidate));
  }
  out.available = std::all_of(out.roles.begin(), out.roles.end(),
      [](const Role &role) { return role.available; });
  out.unavailable_reason = out.available ? "none" : "one_or_more_role_sources_unavailable";
  return out.available;
}
std::string SerializeRepentanceRecipientCandidates12003(const Context &c) {
  std::ostringstream out;
  out << "{\"schema\":\"ck3_12003_repentance_recipient_candidates_v1\",\"available\":"
      << (c.available ? "true" : "false") << ",\"unavailable_reason\":";
  Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"coverage\":\"native_current_roles_only\",\"complete_stock_preferred_selector\":false"
      << ",\"roles\":[";
  for (std::size_t i = 0; i < c.roles.size(); ++i) {
    if (i) out << ',';
    const auto &r = c.roles[i];
    out << "{\"source\":"; Quote(out, r.source);
    out << ",\"available\":" << (r.available ? "true" : "false") << ",\"reason\":"; Quote(out, r.reason);
    out << ",\"character_id\":"; Number(out, r.character_id); out << '}';
  }
  out << "],\"capital_barony_title_id\":"; Number(out, c.capital_barony_title_id);
  out << ",\"capital_county_title_id\":"; Number(out, c.capital_county_title_id);
  out << ",\"capital_clerical_region_title_id\":"; Number(out, c.capital_clerical_region_title_id);
  out << ",\"candidates\":[";
  for (std::size_t i = 0; i < c.candidates.size(); ++i) {
    if (i) out << ',';
    const auto &candidate = c.candidates[i];
    out << "{\"requested_recipient_character_id\":" << candidate.requested_recipient_character_id
        << ",\"sources\":[";
    for (std::size_t j = 0; j < candidate.sources.size(); ++j) {
      if (j) out << ','; Quote(out, candidate.sources[j]);
    }
    out << "],\"terms\":" << repentance::SerializeRepentanceContext12003(candidate.terms) << '}';
  }
  out << "],\"first_observed_ordinary_legal_recipient_character_id\":";
  Number(out, c.first_observed_ordinary_legal_recipient_character_id);
  out << ",\"any_observed_ordinary_request_terms_ready\":"
      << (c.first_observed_ordinary_legal_recipient_character_id ? "true" : "false") << '}';
  return out.str();
}
} // namespace xar::ck3_12003::religion::repentance_candidates
