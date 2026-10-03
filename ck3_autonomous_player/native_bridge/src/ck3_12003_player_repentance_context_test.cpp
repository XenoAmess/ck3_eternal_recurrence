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
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kRequestedHead = 501;
constexpr std::int32_t kEffectiveRecipient = 777;
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
bool shown_value = true, can_send_value = false;
void *GetTraitDb() { return trait_database_missing ? nullptr : trait_database.data(); }
bool HasTrait(void *actor, const void *trait) {
  assert(actor == player.data() && trait == trait_definition.data());
  return trait_present;
}
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
  assert(def == definition.data() && actor == kActor && recipient == kRequestedHead);
  assert(special == nullptr && resolve_defaults);
  active_context = ctx;
  refreshed = finalized = false;
  selected = {true, true};
  Write(ctx, 0, def);
  Write(ctx, 0x2D8, actor);
  Write(ctx, 0x2DC, kEffectiveRecipient);
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
bool Shown(void *ctx) { assert(ctx == active_context && finalized); ++shown_calls; return shown_value; }
bool CanSend(void *ctx, void *error) {
  assert(ctx == active_context && finalized && error == nullptr);
  return can_send_value;
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
xar::ck3_12003::PlayerRepentanceMailboxContext12003 Wrap(const rep::Context &observation) {
  xar::ck3_12003::PlayerRepentanceMailboxContext12003 query{};
  query.completed = true;
  query.envelope.frame_stable = true;
  query.envelope.expected_snapshot_revision = kRevision;
  query.envelope.expected_snapshot.date_raw = kDate;
  query.observation = observation;
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
  const auto bindings = FixtureBindings();
  auto save = [&](const char *name, const rep::Context &c) {
    std::ofstream stream(std::filesystem::path(argv[1]) / name, std::ios::binary);
    stream << xar::ck3_12003::SerializePlayerRepentanceResult12003(
        Wrap(c), "g2-read-02030000000000000000000000000001") << '\n';
    assert(stream.good());
  };
  rep::Context c{};
  assert(rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(destroyed == 1 && shown_calls == 1 && cost_calls == 1);
  assert(c.player_excommunication.available && c.player_excommunication.value == true);
  assert(c.shown.value == true && c.can_send.value == false);
  assert(c.identity.requested_recipient_character_id == static_cast<std::uint32_t>(kRequestedHead));
  assert(c.identity.effective_recipient_id == kEffectiveRecipient && c.identity.secondary_recipient_id == 888);
  assert(c.declared_costs.raw->at(9) == 900000 && c.options.all_unselected == true);
  save("trait-true-final-rejected.json", c);
  trait_present = false; can_send_value = true;
  assert(rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(c.player_excommunication.available && c.player_excommunication.value == false);
  save("trait-false.json", c);
  trait_database_missing = true;
  assert(!rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(!c.player_excommunication.available && !c.player_excommunication.value);
  assert(c.shown.available && c.can_send.available && c.declared_costs.available);
  save("trait-unavailable-terms-preserved.json", c);
  trait_database_missing = false; trait_present = true; stale_head = true;
  assert(!rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(c.player_excommunication.available && c.player_excommunication.value == true);
  assert(!c.identity.available && !c.shown.value && destroyed == 3);
  save("head-stale-trait-preserved.json", c);
  stale_head = false; shown_value = false;
  assert(rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(c.shown.value == false && c.can_send.value == true && destroyed == 4);
  save("head-hidden-final-allowed.json", c);
  shown_value = true;
  assert(rep::ReadRepentanceContext12003(bindings, player.data(), kActor, kDate, kEpoch, c));
  assert(c.shown.value == true && c.can_send.value == true && destroyed == 5);
  save("ordinary-terms-ready.json", c);
  std::cout << "GREEN: six semantic scenarios; production single-trait resolver, final-context reader and full-wire serializer; no game contacted\n";
}
