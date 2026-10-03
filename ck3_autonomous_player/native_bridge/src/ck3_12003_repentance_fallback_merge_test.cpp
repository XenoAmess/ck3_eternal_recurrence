#include "xar_bridge/ck3_12003_player_repentance_mailbox.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <string>
#include <unordered_map>

namespace {
namespace rep = xar::ck3_12003::religion::repentance;
namespace rc = xar::ck3_12003::religion::repentance_candidates;
namespace fb = xar::ck3_12003::religion::repentance_fallback;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kRequestedHead = 501;
constexpr std::int32_t kDate = 53226000;
constexpr std::uint64_t kEpoch = 41;
constexpr std::int32_t kDefinitionHash = 0x0BAD1234;
std::array<std::byte, 0x2800> definition{};
std::array<std::byte, 2 * 0x730> option_rows{};
std::array<std::byte, 0x30> player{};
std::array<bool, 2> selected{};
std::array<std::byte, 0x70> trait_database{};
std::array<std::byte, 0x50> trait_definition{};
std::array<void *, 1> trait_rows{trait_definition.data()};
bool trait_present = true, trait_database_missing = false, stale_head = false;
bool shown_value = true, allow_legal_candidate = true;
std::unordered_map<std::int32_t, unsigned> preview_counts;
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
  ++preview_counts[recipient];
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
  return allow_legal_candidate && active_recipient == 40;
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


rc::Context SeedCurrent() {
  rc::Context out{}; out.available = true; out.unavailable_reason = "none";
  out.capture_epoch = kEpoch; out.date_raw = kDate; out.played_character_id = kActor;
  constexpr std::array<const char *, 5> sources = {"court_chaplain_superior",
      "capital_clerical_region_holder", "actor_superior", "religious_head_or_challenger", "court_chaplain"};
  for (std::size_t i=0; i<out.roles.size(); ++i) {
    out.roles[i].source = sources[i]; out.roles[i].available = true;
    out.roles[i].reason = "none"; out.roles[i].character_id = i == 3 ? kRequestedHead : -1;
  }
  out.roles[4].character_id = 30;
  rc::Candidate c{}; c.requested_recipient_character_id = 30;
  c.sources.push_back("court_chaplain");
  assert(rep::ReadRepentanceRecipientContext12003(FixtureBindings(), player.data(), kActor, kDate, kEpoch, 30, c.terms));
  out.candidates.push_back(c);
  preview_counts.clear(); shown_calls = destroyed = cost_calls = 0;
  return out;
}
fb::Context Fallback(bool complete = true) {
  fb::Context out{}; out.available = complete; out.complete_source_traversal = complete;
  out.capture_epoch = kEpoch; out.date_raw = kDate; out.played_character_id = kActor;
  return out;
}
void ResetCalls() {
  preview_counts.clear(); shown_calls = destroyed = cost_calls = 0;
  allow_legal_candidate = true;
}
void Save(const std::filesystem::path &folder, const char *name, const rc::Context &out) {
  namespace pam = xar::ck3_12003::religion::repentance_pam_route;
  namespace rel = xar::ck3_12002::religion;
  namespace doc = xar::ck3_12002::religion::doctrine12002;
  xar::ck3_12003::PlayerRepentanceMailboxContext12003 query{};
  query.completed = true; query.envelope.frame_stable = true;
  query.envelope.expected_snapshot_revision = 4000;
  query.envelope.expected_snapshot.date_raw = kDate;
  assert(rep::ReadRepentanceContext12003(FixtureBindings(), player.data(), kActor, kDate, kEpoch, query.observation));
  query.candidate_observation = out;
  query.fallback_observation = Fallback(out.fallback_source_traversal_complete);
  auto &raw = query.recovery_observation;
  raw.available = true; raw.played_character_id = kActor; raw.date_raw = kDate; raw.capture_epoch = kEpoch;
  for (auto *flag : {&raw.pope_excom, &raw.any_held_title_has_clerical_region}) {
    flag->available = true; flag->reason = "none"; flag->value = false;
  }
  for (auto *modifier : {&raw.recent_excommunication, &raw.promised_pilgrimage_to_clergy}) {
    modifier->available = true; modifier->reason = "none"; modifier->present = false;
  }
  raw.highest_held_title_tier.available = true; raw.highest_held_title_tier.reason = "none";
  raw.highest_held_title_tier.value = 3;
  rel::Context identity{}; identity.available = true; identity.played_character_id = kActor;
  identity.date_raw = kDate; identity.capture_epoch = kEpoch;
  identity.rite_id = 3; identity.faith_id = 2; identity.faith_main_rite_id = 4;
  identity.religion_key = "christianity_religion";
  doc::TenetParameterContext parameters{}; parameters.available = true;
  parameters.played_character_id = kActor; parameters.date_raw = kDate; parameters.capture_epoch = kEpoch;
  parameters.faith_id = 2;
  parameters.faith_main_rite = doc::RiteBooleanParameters{4, {{"spiritual_head_of_faith", true}}};
  doc::FaithMainRiteDoctrines doctrines{}; doctrines.available = true;
  doctrines.played_character_id = kActor; doctrines.date_raw = kDate; doctrines.capture_epoch = kEpoch;
  doctrines.faith_id = 2; doctrines.main_rite_id = 4;
  doctrines.rows.push_back({"doctrine_sacraments_central", "sacraments", "faith_main_rite"});
  std::array<std::byte, 0x300> feature_root{};
  const auto feature_pointer = reinterpret_cast<std::uintptr_t>(feature_root.data());
  std::array<std::uint32_t, 44> feature_enums{}; feature_enums[43] = 0x4169;
  pam::Bindings bindings{}; bindings.enabled = true;
  bindings.feature_root_slot = &feature_pointer; bindings.feature_enum_table = feature_enums.data();
  pam::RawRouteInputs route{}; route.available = true; route.played_character_id = kActor;
  route.date_raw = kDate; route.capture_epoch = kEpoch;
  route.pope_excom = false; route.highest_held_title_tier = 3; route.any_held_title_has_clerical_region = false;
  assert(pam::ReadRepentancePamRoute12003(bindings, player.data(), kActor, kDate, kEpoch,
      identity, parameters, doctrines, out, route, query.pam_observation));
  std::ofstream stream(folder / (std::string{name} + ".json"), std::ios::binary);
  stream << xar::ck3_12003::SerializePlayerRepentanceResult12003(query,
      "g2-read-02030000000000000000000000000001") << '\n';
  assert(stream.good());
}
} // namespace

// The new Append branch does not invoke these existing role-source helpers.
// These two unused link stubs avoid compiling/running their old implementations.
namespace xar::ck3_12002 {
void *ResolveCoreCharacter(const CoreBindings &, std::int32_t) noexcept {
  assert(false && "Append must reuse supplied observations, without role collection"); return nullptr;
}
}
namespace xar::ck3_12002::religion::clergy {
bool ResolveCurrentClergySeat12002(const Bindings &, std::int32_t, CurrentClergySeat &) noexcept {
  assert(false && "Append must not re-read old clergy sources"); return false;
}
}

int main(int argc, char **argv) {
  assert(argc == 2); const std::filesystem::path folder(argv[1]);

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
  const auto request = FixtureBindings();
  {
    ResetCalls(); auto out = SeedCurrent(); auto fallback = Fallback();
    fallback.candidates.push_back({30, {std::string(fb::kRealmSource)}, {}});
    fallback.candidates.push_back({30, {std::string(fb::kDejureSource)}, {77}});
    assert(rc::AppendRepentanceFallbackRecipients12003(request, player.data(), kActor, kDate, kEpoch, fallback, out));
    assert(preview_counts.empty() && shown_calls == 0 && destroyed == 0);
    assert(out.candidates.size() == 1 && out.candidates[0].sources.size() == 3);
    assert(out.candidates[0].terms.identity.effective_recipient_id == 30);
    assert(out.candidates[0].terms.can_send.value == false && out.fallback_new_candidate_count == 0);
    assert(out.source_candidate_evaluation_complete);
    Save(folder, "merge-current-duplicate-no-preview", out);
  }
  {
    ResetCalls(); auto out = SeedCurrent(); auto fallback = Fallback();
    fallback.candidates.push_back({30, {std::string(fb::kRealmSource)}, {}});
    fallback.candidates.push_back({40, {std::string(fb::kDejureSource)}, {77}});
    assert(rc::AppendRepentanceFallbackRecipients12003(request, player.data(), kActor, kDate, kEpoch, fallback, out));
    assert(preview_counts.size() == 1 && preview_counts.at(40) == 1 && shown_calls == 1 && destroyed == 1);
    assert(out.candidates.size() == 2 && out.fallback_new_candidate_count == 1);
    assert(out.first_observed_ordinary_legal_recipient_character_id == 40);
    assert(out.candidates[1].terms.shown.value == true && out.candidates[1].terms.can_send.value == true);
    assert(out.source_candidate_evaluation_complete);
    Save(folder, "merge-new-legal-fallback-unlocks-first", out);
  }
  {
    ResetCalls(); allow_legal_candidate = false; auto out = SeedCurrent(); auto fallback = Fallback();
    fallback.candidates.push_back({41, {std::string(fb::kRealmSource)}, {}});
    fallback.candidates.push_back({42, {std::string(fb::kDejureSource)}, {78}});
    assert(rc::AppendRepentanceFallbackRecipients12003(request, player.data(), kActor, kDate, kEpoch, fallback, out));
    assert(preview_counts.size() == 2 && preview_counts.at(41) == 1 && preview_counts.at(42) == 1);
    assert(out.candidates.size() == 3 && !out.first_observed_ordinary_legal_recipient_character_id);
    assert(out.fallback_source_traversal_complete && out.source_candidate_evaluation_complete);
    Save(folder, "merge-all-false-source-complete", out);
  }
  {
    ResetCalls(); auto out = SeedCurrent(); auto fallback = Fallback(false);
    fallback.candidates.push_back({40, {std::string(fb::kRealmSource)}, {}});
    assert(!rc::AppendRepentanceFallbackRecipients12003(request, player.data(), kActor, kDate, kEpoch, fallback, out));
    assert(out.candidates.size() == 2 && preview_counts.at(40) == 1 && out.fallback_new_candidate_count == 1);
    assert(out.candidates[1].terms.available && out.candidates[1].terms.can_send.value == true);
    assert(!out.fallback_source_traversal_complete && !out.source_candidate_evaluation_complete);
    Save(folder, "merge-partial-preserves-observed-candidate", out);
  }
  {
    ResetCalls(); auto out = SeedCurrent(); auto fallback = Fallback();
    fallback.candidates.push_back({kActor, {std::string(fb::kRealmSource)}, {}});
    fallback.candidates.push_back({-1, {std::string(fb::kDejureSource)}, {77}});
    assert(rc::AppendRepentanceFallbackRecipients12003(request, player.data(), kActor, kDate, kEpoch, fallback, out));
    assert(preview_counts.empty() && shown_calls == 0 && destroyed == 0);
    assert(out.candidates.size() == 1 && out.fallback_new_candidate_count == 0);
    Save(folder, "merge-actor-and-absent-no-preview", out);
  }
  std::cout << "GREEN: five new Append fallback merge scenarios; old role scenarios not run\n";
}
