#include "xar_bridge/ck3_12003_player_repentance_mailbox.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <string>

namespace {
namespace rep = xar::ck3_12003::religion::repentance;
namespace rc = xar::ck3_12003::religion::repentance_candidates;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kRequestedHead = 501;
constexpr std::int32_t kDate = 53226000;
constexpr std::uint64_t kEpoch = 41;
constexpr std::uint64_t kRevision = 4000;
constexpr std::int32_t kDefinitionHash = 0x0BAD1234;
std::array<std::byte, 0x2800> definition{};
std::array<std::byte, 2 * 0x730> option_rows{};
std::array<std::byte, 0x30> player{};
std::array<bool, 2> selected{};
std::array<std::byte, 0x70> trait_database{};
std::array<std::byte, 0x50> trait_definition{};
std::array<void *, 1> trait_rows{trait_definition.data()};
bool trait_present = true, trait_database_missing = false, stale_head = false;
bool shown_value = true;
void *GetTraitDb() { return trait_database_missing ? nullptr : trait_database.data(); }
bool HasTrait(void *actor, const void *trait) {
  assert(actor == player.data() && trait == trait_definition.data());
  return trait_present;
}
std::int32_t active_recipient = -1;
void *active_context = nullptr;
bool refreshed = false, finalized = false;
int destroyed = 0, shown_calls = 0, cost_calls = 0;

template <typename T>
void Write(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void *GetDefinitionDb() { return definition.data(); }
std::int32_t Hash(void *db, const char *text, std::uint32_t size) {
  assert(db == definition.data() && std::string_view(text, size) == rep::kInteractionKey);
  return kDefinitionHash;
}
void *Lookup(void *db, std::int32_t hash) {
  assert(db == definition.data() && hash == kDefinitionHash);
  return definition.data();
}
bool Heads(const rep::HeadBindings &, std::uint64_t epoch,
           rep::HeadContext &out) noexcept {
  assert(epoch == kEpoch);
  out = {};
  out.available = true;
  out.failure = xar::ck3_12002::religion::head::Failure::none;
  out.capture_epoch = epoch;
  out.date_raw = stale_head ? kDate + 1 : kDate;
  out.played_character_id = kActor;
  out.actor_rite_id = 3;
  out.faith_id = 2;
  out.faith_main_rite_id = 4;
  out.faith_religious_head_title_id = 44;
  out.faith_religious_head_holder_character_id = kRequestedHead;
  return true;
}
void *Construct(void *ctx, void *def, std::int32_t actor,
                std::int32_t recipient, void *special, bool resolve_defaults) {
  assert(def == definition.data() && actor == kActor && recipient != -1);
  active_recipient = recipient;
  assert(special == nullptr && resolve_defaults);
  active_context = ctx;
  refreshed = finalized = false;
  selected = {true, true};
  Write(ctx, 0, def);
  Write(ctx, 0x2D8, actor);
  Write(ctx, 0x2DC, recipient);
  Write(ctx, 0x2E0, std::int32_t{-1});
  Write(ctx, 0x2E4, std::int32_t{888});
  Write(ctx, 0x2E8, std::int32_t{-1});
  Write(ctx, 0x2EC, actor);
  return ctx;
}
void SetOption(void *ctx, std::uint32_t flag, bool value) {
  assert(ctx == active_context && !refreshed && !value && (flag == 17 || flag == 19));
  selected[flag == 17 ? 0 : 1] = value;
}
void Refresh(void *ctx, bool recompute) {
  assert(ctx == active_context && recompute && !selected[0] && !selected[1]);
  refreshed = true;
}
void Finalize(void *ctx) {
  assert(ctx == active_context && refreshed);
  finalized = true;
}
bool ReadOption(void *ctx, std::uint32_t flag) {
  assert(ctx == active_context && finalized && (flag == 17 || flag == 19));
  return selected[flag == 17 ? 0 : 1];
}
void Destroy(void *ctx) { assert(ctx == active_context); ++destroyed; }
bool Shown(void *ctx) { assert(ctx == active_context && finalized); ++shown_calls; return active_recipient != kRequestedHead && shown_value; }
bool CanSend(void *ctx, void *error) {
  assert(ctx == active_context && finalized && error == nullptr);
  return active_recipient == 30 || active_recipient == 40;
}
void Costs(const void *block, const void *scope, std::int64_t *out) {
  assert(block == definition.data() + 0x40 && scope ==
         static_cast<const std::byte *>(active_context) + 8 && finalized);
  ++cost_calls;
  for (int i = 0; i < 10; ++i) out[i] = 100000 * i;
}
std::int64_t *RecipientScore(void *ctx, std::int64_t *out) {
  assert(ctx == active_context && finalized);
  *out = -3500000;
  return out;
}
std::int64_t *IntermediaryScore(void *ctx, std::int64_t *out) {
  assert(ctx == active_context && finalized);
  *out = 0;
  return out;
}
std::uint8_t Outer(void *ctx, std::uint8_t first, std::uint8_t second,
                   void *arg4, void *arg5) {
  assert(ctx == active_context && finalized && first == 1 && second == 1);
  assert(arg4 == nullptr && arg5 == nullptr);
  return 2;
}
rep::Bindings FixtureBindings() {
  rep::Bindings b{};
  b.enabled = true;
  b.module_base = 0x10000000;
  b.read_heads = &Heads;
  b.traits.enabled = true;
  b.traits.get_trait_database = &GetTraitDb;
  b.traits.character_has_trait = &HasTrait;
  b.get_database = &GetDefinitionDb;
  b.stable_hash = &Hash;
  b.lookup_definition = &Lookup;
  b.construct_two_role = &Construct;
  b.set_option = &SetOption;
  b.read_option = &ReadOption;
  b.is_shown = &Shown;
  b.outer_answer = &Outer;
  b.interaction.refresh = &Refresh;
  b.interaction.finalize = &Finalize;
  b.interaction.destroy = &Destroy;
  b.interaction.validate = &CanSend;
  b.interaction.evaluate_cost = &Costs;
  b.interaction.recipient_answer_score = &RecipientScore;
  b.interaction.intermediary_answer_score = &IntermediaryScore;
  return b;
}

std::array<std::byte, 0x180> chaplain{}, superior{}, capital_holder{}, authority{};
std::array<std::byte, 0x180> barony{}, county{}, clerical{};
std::array<std::byte, 0x50> character_storage{}, title_storage{};
std::array<std::byte, (kActor + 1) * 16> character_rows{};
std::array<std::byte, 4 * 16> title_rows{};
std::array<std::byte, 0xb0> game{};
std::array<std::byte, 0x1f1e1> game_data{};
void *character_storage_pointer = character_storage.data();
void *title_storage_pointer = title_storage.data();
void *game_pointer = game.data();
bool absent = false, fallback = false, clergy_missing = false, region_missing = false;
int direct_calls = 0, fallback_calls = 0;
bool Clergy(const xar::ck3_12002::religion::clergy::Bindings &, std::int32_t actor,
            xar::ck3_12002::religion::clergy::CurrentClergySeat &out) noexcept {
  assert(actor == kActor); out = {};
  if (clergy_missing) return false;
  out.incumbent = absent ? nullptr : chaplain.data();
  out.incumbent_character_id = absent ? -1 : 20;
  return true;
}
std::int32_t *Direct(void *manager, std::int32_t *out, std::int32_t id) {
  assert(manager == game_data.data() + 0x1f1e0); ++direct_calls;
  *out = (id == 20 && !fallback && !absent) ? 30 : -1; return out;
}
std::int32_t *Top(std::int32_t *out, std::int32_t id) {
  ++fallback_calls; *out = id == 20 && fallback ? 40 : id; return out;
}
void *Authority(void *actor) { assert(actor == player.data()); return absent ? nullptr : authority.data(); }
std::int32_t *Capital(void *actor, std::int32_t *out) {
  assert(actor == player.data()); *out = absent ? -1 : 1; return out;
}
rc::Scope16 *Region(void *unused, rc::Scope16 *out, const rc::Scope16 **input) {
  assert(unused == nullptr && (*input)->kind == 5 && (*input)->id == 2);
  out->kind = 5; out->id = region_missing ? UINT32_MAX : 3; return out;
}
rc::Bindings CandidateBindings() {
  rc::Bindings b{}; b.enabled = true; b.core.enabled = true;
  b.core.character_storage_slot = &character_storage_pointer;
  b.game_state_slot = &game_pointer; b.title_storage_slot = &title_storage_pointer;
  b.read_clergy = &Clergy; b.authority = &Authority; b.lease_liege = &Direct;
  b.top_lease_liege_direct = &Top; b.capital_barony = &Capital; b.clerical_region = &Region;
  return b;
}
xar::ck3_12003::PlayerRepentanceMailboxContext12003 Wrap(const rep::Context &head, const rc::Context &candidates) {
  xar::ck3_12003::PlayerRepentanceMailboxContext12003 query{};
  query.completed = true; query.envelope.frame_stable = true;
  query.envelope.expected_snapshot_revision = kRevision;
  query.envelope.expected_snapshot.date_raw = kDate;
  query.observation = head; query.candidate_observation = candidates;
  return query;
}
} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  Write(player.data(), 0x18, kActor);
  Write(definition.data(), 0x14, kDefinitionHash);
  const char *key = rep::kInteractionKey.data();
  Write(definition.data(), 0x18, key);
  Write(definition.data(), 0x28, static_cast<std::uint64_t>(rep::kInteractionKey.size()));
  Write(definition.data(), 0x30, static_cast<std::uint64_t>(rep::kInteractionKey.size()));
  Write(definition.data(), 0x2258, static_cast<void *>(option_rows.data()));
  Write(definition.data(), 0x2264, std::int32_t{2});
  Write(option_rows.data(), 0x368, std::uint32_t{17});
  Write(option_rows.data(), 0x730 + 0x368, std::uint32_t{19});
  constexpr std::string_view trait_key = "excommunicated";
  std::memcpy(trait_definition.data() + 0x18, trait_key.data(), trait_key.size());
  Write(trait_definition.data(), 0x28, static_cast<std::uint64_t>(trait_key.size()));
  Write(trait_definition.data(), 0x30, std::uint64_t{15});
  Write(trait_database.data(), 0x50, trait_rows.data());
  Write(trait_database.data(), 0x5C, std::int32_t{1});

  Write(game.data(), 0xa0, static_cast<void *>(game_data.data()));
  Write(character_storage.data(), 0x20, static_cast<void *>(character_rows.data()));
  Write(character_storage.data(), 0x2c, std::int32_t{kActor + 1});
  Write(title_storage.data(), 0x20, static_cast<void *>(title_rows.data()));
  Write(title_storage.data(), 0x2c, std::int32_t{4});
  auto add_character = [&](void *object, std::int32_t id) {
    Write(object, 0x18, id); Write(character_rows.data(), static_cast<std::size_t>(id) * 16 + 8, object);
  };
  add_character(player.data(), kActor); add_character(chaplain.data(), 20);
  add_character(superior.data(), 30); add_character(capital_holder.data(), 40);
  add_character(authority.data(), kRequestedHead);
  auto add_title = [&](void *object, std::int32_t id) {
    Write(object, 0x10, id); Write(title_rows.data(), static_cast<std::size_t>(id) * 16 + 8, object);
  };
  add_title(barony.data(), 1); add_title(county.data(), 2); add_title(clerical.data(), 3);
  Write(barony.data(), 0x108, std::int32_t{2}); Write(clerical.data(), 0x128, std::int32_t{30});
  const auto request = FixtureBindings(); const auto bindings = CandidateBindings();
  rep::Context head{};
  assert(rep::ReadRepentanceContext12003(request, player.data(), kActor, kDate, kEpoch, head));
  assert(head.shown.value == false);
  rc::Context c{};
  auto save = [&](const char *name) {
    std::ofstream stream(std::filesystem::path(argv[1]) / name, std::ios::binary);
    stream << xar::ck3_12003::SerializePlayerRepentanceResult12003(Wrap(head, c), "g2-read-02030000000000000000000000000001") << '\n';
    assert(stream.good());
  };
  assert(rc::ReadRepentanceRecipientCandidates12003(bindings, request, player.data(), kActor, kDate, kEpoch, c));
  assert(c.roles[0].character_id == 30 && c.roles[1].character_id == 30);
  assert(c.roles[2].character_id == -1 && c.roles[3].character_id == kRequestedHead && c.roles[4].character_id == 20);
  assert(c.candidates.size() == 3 && c.candidates[0].sources.size() == 2);
  assert(c.candidates[0].terms.identity.effective_recipient_id == 30 && c.candidates[0].terms.shown.value == true);
  assert(c.candidates[0].terms.can_send.value == true && c.candidates[0].terms.declared_costs.raw->at(9) == 900000);
  assert(c.first_observed_ordinary_legal_recipient_character_id == 30);
  save("role-dedup-local-clergy-legal-head-hidden.json");
  absent = true;
  assert(rc::ReadRepentanceRecipientCandidates12003(bindings, request, player.data(), kActor, kDate, kEpoch, c));
  for (const auto &role : c.roles) assert(role.available && role.character_id == -1);
  assert(c.candidates.empty() && !c.first_observed_ordinary_legal_recipient_character_id);
  save("all-roles-legally-absent.json");
  absent = false; fallback = true; region_missing = true;
  assert(rc::ReadRepentanceRecipientCandidates12003(bindings, request, player.data(), kActor, kDate, kEpoch, c));
  assert(c.roles[0].character_id == 40 && c.roles[1].character_id == -1 && c.roles[2].character_id == -1);
  assert(c.capital_clerical_region_title_id == -1 && c.first_observed_ordinary_legal_recipient_character_id == 40);
  save("superior-fallback-and-native-region-absent.json");
  clergy_missing = true;
  assert(!rc::ReadRepentanceRecipientCandidates12003(bindings, request, player.data(), kActor, kDate, kEpoch, c));
  assert(!c.roles[0].available && !c.roles[0].character_id && !c.roles[4].available);
  assert(c.roles[1].available && c.roles[3].available && c.candidates.size() == 1);
  assert(c.candidates[0].terms.identity.effective_recipient_id == kRequestedHead && !c.first_observed_ordinary_legal_recipient_character_id);
  save("clergy-read-failure-preserves-head.json");
  assert(direct_calls == 6 && fallback_calls == 5);
  std::cout << "GREEN: four new role candidate scenarios; actual production final context and wire; no game contacted\n";
}
