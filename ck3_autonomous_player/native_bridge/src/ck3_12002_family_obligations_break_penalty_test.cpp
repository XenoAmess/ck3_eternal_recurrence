#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>

namespace p = xar::ck3_12002::family_break_penalty;
namespace n = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T> void Put(void *where, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(where) + offset, &value, sizeof(value));
}
void NativeKey(void *where, std::string_view key) {
  auto *data = static_cast<std::byte *>(where);
  if (key.size() < 16) {
    std::memcpy(data + 0x18, key.data(), key.size());
    Put(data, 0x30, std::size_t{15});
  } else {
    Put(data, 0x18, key.data()); Put(data, 0x30, key.size());
  }
  Put(data, 0x28, key.size());
}
struct Fixture {
  Bytes<0x220> actor{}, first{}, second{}, owner{};
  Bytes<0x60> eunuch{}, beardless{}, trait_db{}, token{}, selections{};
  Bytes<0x40> first_vars{}, second_vars{}, empty_vars{};
  Bytes<0x20> var_row{};
  Bytes<0x20> rule_service{}, rule_vtable{};
  Bytes<0x7D0> first_rite{}, second_rite{};
  std::array<void *, 2> trait_rows{};
  std::array<void *, 1> selected_tokens{};
  void *token_registry = this, *token_fallback = nullptr, *service_slot = rule_service.data();
  std::int32_t tier = 4;
  bool kin = true, extended = false, ally = false, promised = false;
  bool first_eunuch = false, second_eunuch = false, flag = false;
  bool rule_selected = false, first_rite_allowed = true, second_rite_allowed = true;
  bool use_owner = false;
  std::size_t calls = 0;
  p::Bindings binding{};
  Fixture();
};
Fixture *f = nullptr;
std::string flag_key = "can_not_marry", homo_key = "homosexuality_accepted";
std::string variable_key = "promised_grand_wedding_by";
void *Traits() { return f->trait_db.data(); }
bool HasTrait(void *character, const void *trait) {
  return trait == f->eunuch.data() &&
      ((character == f->first.data() && f->first_eunuch) ||
       (character == f->second.data() && f->second_eunuch));
}
bool HasFlag(void *, const std::int32_t *id) { assert(*id == 30); return f->flag; }
std::int32_t ScriptLookup(const n::PhaseStringView64 *key) {
  const std::string_view value(key->data, static_cast<std::size_t>(key->size));
  return value == flag_key ? 30 : value == homo_key ? 31 : -1;
}
const std::string *ScriptName(std::int32_t id) { return id == 30 ? &flag_key : &homo_key; }
void *VariableTable() { return f; }
std::int32_t *VariableLookup(void *, std::int32_t *out, const n::PhaseStringView32 *key) {
  assert(std::string_view(key->data, static_cast<std::size_t>(key->size)) == variable_key);
  *out = 32; return out;
}
const std::string *VariableName(void *, std::int32_t id) { assert(id == 32); return &variable_key; }
void *Variables(const n::PhaseVariableTarget *target) {
  assert(target->kind == 4);
  return target->payload == 2 && f->promised ? f->first_vars.data() : f->empty_vars.data();
}
std::int32_t Tier(void *character) { return character == f->owner.data() ? 2 : f->tier; }
void *Matchmaker(void *) { return f->use_owner ? f->owner.data() : f->second.data(); }
bool Close(void *, void *) { return f->kin; }
bool Extended(void *, void *) { return f->extended; }
bool Yields(void *actor, void *target, void *candidate, void *target_candidate) {
  assert(actor == f->actor.data());
  assert(target == f->second.data() || target == f->owner.data());
  assert(candidate == f->first.data() && target_candidate == f->second.data());
  ++f->calls; return f->ally;
}
void *Rite(void *character) { return character == f->first.data() ? f->first_rite.data() : f->second_rite.data(); }
bool Contains(const void *set, const std::int32_t *id) {
  assert(*id == 31);
  const auto *first_set = f->first_rite.data() + p::kRiteParameterSetOffset;
  return set == first_set ? f->first_rite_allowed : f->second_rite_allowed;
}
std::int32_t RuleHash(void *, const char *data, std::uint32_t size) {
  assert(std::string_view(data, size) == "accepted_same_sex_marriage"); return 33;
}
void *RuleToken(void *, std::int32_t id) { assert(id == 33); return f->token.data(); }
void *Selections(void *) {
  Put(f->selections.data(), 0x14, std::int32_t{f->rule_selected ? 1 : 0});
  return f->selections.data();
}
Fixture::Fixture() {
  f = this;
  std::int32_t id = 1;
  for (auto *character : {actor.data(), first.data(), second.data(), owner.data()}) {
    Put(character, 0x18, id++); Put(character, 0x1C, std::uint32_t{0x43686172});
    Put(character, 0x158, std::int32_t{-1}); Put(character, 0x1C0, static_cast<void *>(this));
  }
  Put(first.data(), 0x1A1, std::uint8_t{0}); Put(second.data(), 0x1A1, std::uint8_t{1});
  NativeKey(eunuch.data(), "eunuch_1"); NativeKey(beardless.data(), "beardless_eunuch");
  trait_rows = {eunuch.data(), beardless.data()};
  Put(trait_db.data(), 0x50, trait_rows.data()); Put(trait_db.data(), 0x5C, std::int32_t{2});
  Put(var_row.data(), 8, std::int32_t{32});
  Put(first_vars.data(), 0x10, var_row.data()); Put(first_vars.data(), 0x1C, std::int32_t{1});
  NativeKey(token.data(), "accepted_same_sex_marriage"); selected_tokens[0] = token.data();
  Put(selections.data(), 8, selected_tokens.data());
  Put(rule_service.data(), 0, rule_vtable.data()); Put(rule_vtable.data(), 0x10, &Selections);
  binding.enabled = true; binding.lineage.enabled = true;
  binding.traits.enabled = true; binding.traits.get_trait_database = &Traits;
  binding.traits.character_has_trait = &HasTrait;
  auto &d = binding.identifiers; d.enabled = true;
  d.lookup_script_identifier = &ScriptLookup; d.script_identifier_name = &ScriptName;
  d.variable_table = &VariableTable; d.lookup_variable_identifier = &VariableLookup;
  d.variable_identifier_name = &VariableName; d.variable_context = &Variables;
  d.rule_token_registry = &token_registry; d.rule_token_fallback = &token_fallback;
  d.rule_service = &service_slot; d.hash_rule_key = &RuleHash; d.lookup_rule_token = &RuleToken;
  binding.highest_tier = &Tier; binding.matchmaker = &Matchmaker;
  binding.close_family = &Close; binding.close_or_extended_family = &Extended;
  binding.has_trait_flag = &HasFlag; binding.yields_alliance = &Yields;
  binding.character_rite = &Rite; binding.parameter_set_contains = &Contains;
}
p::Penalty Read(Fixture &fixture) {
  p::Penalty result;
  assert(p::ReadFamilyBreakPenalty(fixture.binding, fixture.actor.data(),
      fixture.first.data(), fixture.second.data(), result));
  assert(result.resource_penalty_available && !result.effects_complete);
  assert(result.unavailable_reason.empty()); return result;
}
} // namespace

int main() {
  assert(!p::BindFamilyBreakPenaltyImage(0, n::kExecutableSha256).enabled);
  assert(!p::BindFamilyBreakPenaltyImage(1, "old-build").enabled);
  const auto actual = p::BindFamilyBreakPenaltyImage(0x140000000, n::kExecutableSha256);
  assert(actual.enabled && actual.character_rite && actual.yields_alliance);
  Fixture q;
  const std::array<std::int64_t, 7> ordinary{0,35,75,150,350,750,1500};
  const std::array<std::int64_t, 7> grand{35,75,150,350,750,1500,1500};
  for (std::int32_t tier = 0; tier <= 6; ++tier) {
    q.tier = tier; q.promised = false;
    auto out = Read(q); assert(out.stock_prestige_effect_raw == -ordinary[static_cast<std::size_t>(tier)] * 100000);
    assert(out.stock_prestige_level_effect == 0 && !out.proper_reason);
    q.promised = true; out = Read(q);
    assert(out.stock_prestige_effect_raw == -grand[static_cast<std::size_t>(tier)] * 100000);
    assert(out.stock_prestige_level_effect == -1);
  }
  q.tier = 4; q.promised = false; q.kin = false; q.ally = false;
  auto out = Read(q); assert(out.stock_prestige_effect_raw == 0 && !out.ordinary_prestige_relevant);
  q.ally = true; out = Read(q); assert(out.stock_prestige_effect_raw == -35000000 && out.yields_alliance);
  const auto before = q.calls;
  Put(q.actor.data(), 0x1C0, static_cast<void *>(nullptr));
  out = Read(q); assert(out.stock_prestige_effect_raw == 0 && q.calls == before);
  Put(q.actor.data(), 0x1C0, static_cast<void *>(&q));
  q.promised = true; q.use_owner = true; q.extended = false;
  out = Read(q); assert(out.rejected_owner_character_id == 4 && out.stock_prestige_level_effect == -1);
  q.first_eunuch = true; out = Read(q);
  assert(out.proper_reason && out.stock_prestige_effect_raw == 0 && out.stock_prestige_level_effect == 0);
  assert(out.rejected_owner_character_id == 3); // Grand effect does not run with proper reason.
  q.first_eunuch = false; q.flag = true; out = Read(q); assert(out.proper_reason);
  q.flag = false; q.use_owner = false;
  Put(q.second.data(), 0x1A1, std::uint8_t{0});
  q.rule_selected = false; out = Read(q); assert(out.proper_reason);
  q.rule_selected = true; q.first_rite_allowed = true; q.second_rite_allowed = true;
  out = Read(q); assert(!out.proper_reason && out.stock_prestige_level_effect == -1);
  q.second_rite_allowed = false; out = Read(q); assert(out.proper_reason && out.stock_prestige_effect_raw == 0);
  q.binding.highest_tier = nullptr;
  assert(!p::ReadFamilyBreakPenalty(q.binding,q.actor.data(),q.first.data(),q.second.data(),out));
  assert(!out.resource_penalty_available);
  std::puts("PASS break penalty: exact stock ordinary and grand tiers; dynamic kin, alliance, promise, eunuch/flag and marriage-only same-sex predicates; no effects executed, no game access");
}
