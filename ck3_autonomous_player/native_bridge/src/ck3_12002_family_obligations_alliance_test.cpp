#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace a = xar::ck3_12002::family_obligations_alliance;
using namespace xar::ck3_12002;

namespace {
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Put(object.data(), offset, value);
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Check(bool condition, const char *label) {
  if (!condition) throw std::runtime_error(label);
}
constexpr std::int32_t actor = 0x04000000, ally = 0x05000001, enemy = 0x06000002;
constexpr std::int32_t own_war = 0x07000000, ally_attack = 0x08000001, ally_defend = 0x09000002;

struct Fixture {
  std::array<std::byte, 0x210> actor_object{}, ally_object{}, enemy_object{};
  std::array<std::byte, 0x340> actor_realm{}, ally_realm{};
  std::array<std::byte, 0x30> character_storage{}, war_storage{};
  std::array<std::byte, 0x30> character_slots{}, war_slots{};
  std::array<std::array<std::byte, 0x360>, 3> wars{};
  std::array<std::array<std::byte, 0x10>, 6> participants{};
  std::array<void *, 6> participant_pointers{};
  std::array<std::int32_t, 1> first_wars{own_war};
  std::array<std::int32_t, 2> second_wars{ally_attack, ally_defend};
  std::array<std::byte, 0x2720> definition{};
  void *character_slot = character_storage.data(), *war_slot = war_storage.data();
  void *war_fallback = nullptr, *interaction_missing = nullptr, *database = this;
  bool allied = true, pick = true, can_send = true, was_called = false;
  bool identity_drift = false, acceptance_unavailable = false;
  int constructions = 0, destructions = 0, refreshes = 0, finalizations = 0;
  int validates = 0, cost_reads = 0, target_gates = 0, answer_reads = 0;
  std::int64_t acceptance = -2'500'000;
  a::Bindings bindings{};
  CoreSnapshotPrefix frame{{123456, 1, true}, 0, true, true, actor, true};

  Fixture();
};
Fixture *active = nullptr;
bool Allied(const void *, const void *) { return active->allied; }
std::uint32_t Hash(const void *db, const char *key, std::uint32_t size) {
  Check(db == active && std::string_view(key, size) == a::kInteractionKey,
        "production lookup supplies stable native key");
  return 0x11223344;
}
void *Lookup(void *db, std::int32_t hash) {
  Check(db == active && hash == 0x11223344, "production lookup consumes native hash");
  return active->definition.data();
}
bool Contains(const void *side, std::int32_t id) {
  const auto records = Get<void *const *>(side, 8);
  const auto count = Get<std::int32_t>(side, 0x14);
  for (std::int32_t i = 0; i < count; ++i)
    if (Get<std::int32_t>(records[i], 8) == id) return true;
  return false;
}
bool Called(const void *, std::int32_t) { return active->was_called; }
void *Construct(void *context, void *definition, std::int32_t first,
                std::int32_t second, void *extra, bool redirect) {
  Check(definition == active->definition.data() && extra == nullptr && redirect,
        "read-only ordinary native context uses exact definition and role redirect");
  std::memset(context, 0, 0x338);
  Put(context, 0, definition);
  Put(context, a::kContextActorOffset, first);
  Put(context, a::kContextRecipientOffset, second);
  ++active->constructions;
  return context;
}
void Refresh(void *context, bool flag) {
  Check(flag && Get<std::uint16_t>(context, a::kContextTargetOffset) == a::kWarTargetType,
        "refresh sees a real typed war target");
  ++active->refreshes;
}
void Finalize(void *context) {
  Put(context, a::kContextSpecialInstanceOffset, active);
  if (active->identity_drift) Put(context, a::kContextActorOffset, std::int32_t{-1});
  ++active->finalizations;
}
void Destroy(void *) { ++active->destructions; }
bool Pick(void *context, const void *target, void *diagnostics) {
  Check(diagnostics == nullptr && Get<void *>(context, a::kContextSpecialInstanceOffset) == active &&
        std::memcmp(target, static_cast<const std::byte *>(context) + a::kContextTargetOffset, 16) == 0,
        "target predicate is evaluated on the finalized exact target");
  ++active->target_gates;
  return active->pick;
}
bool Validate(void *context, void *diagnostics) {
  Check(diagnostics == nullptr && Get<void *>(context, a::kContextSpecialInstanceOffset) == active,
        "complete native CanSend uses finalized disposable context");
  ++active->validates;
  return active->can_send && active->allied;
}
void Cost(const void *definition_cost, const void *scope, std::int64_t *output) {
  Check(definition_cost == active->definition.data() + 0x40, "production ten-cost evaluator input");
  const auto context = static_cast<const std::byte *>(scope) - 8;
  const auto war = Get<std::uint64_t>(context, a::kContextTargetTokenOffset);
  for (std::size_t i = 0; i < 10; ++i) output[i] = static_cast<std::int64_t>((war & 0xFFU) + i) * 100'000;
  ++active->cost_reads;
}
std::int64_t *Answer(void *, std::int64_t *output) {
  ++active->answer_reads;
  *output = active->acceptance;
  return active->acceptance_unavailable ? nullptr : output;
}
bool Trigger(void *, const void *) { return false; }

Fixture::Fixture() {
  active = this;
  Put(actor_object, 0x18, actor); Put(ally_object, 0x18, ally); Put(enemy_object, 0x18, enemy);
  Put(actor_object, a::kCharacterRealmOffset, actor_realm.data());
  Put(ally_object, a::kCharacterRealmOffset, ally_realm.data());
  Put(actor_realm, a::kRealmWarIdsOffset, first_wars.data());
  Put(actor_realm, a::kRealmWarIdsOffset + 8, std::int32_t{1});
  Put(actor_realm, a::kRealmWarIdsOffset + 0xC, std::int32_t{1});
  Put(ally_realm, a::kRealmWarIdsOffset, second_wars.data());
  Put(ally_realm, a::kRealmWarIdsOffset + 8, std::int32_t{2});
  Put(ally_realm, a::kRealmWarIdsOffset + 0xC, std::int32_t{2});
  Put(character_storage, 0x20, character_slots.data());
  Put(character_storage, 0x2C, std::int32_t{3});
  Put(character_slots, 8, actor_object.data()); Put(character_slots, 0x18, ally_object.data());
  Put(character_slots, 0x28, enemy_object.data());
  Put(war_storage, 0x20, war_slots.data()); Put(war_storage, 0x2C, std::int32_t{3});
  for (std::size_t i = 0; i < 3; ++i) {
    const std::int32_t first = i == 0 ? actor : i == 1 ? ally : enemy;
    const std::int32_t second = i == 2 ? ally : enemy;
    Put(wars[i], 8, i == 0 ? own_war : i == 1 ? ally_attack : ally_defend);
    Put(war_slots, i * 0x10 + 8, wars[i].data());
    Put(wars[i], 0x288, first); Put(wars[i], 0x28C, second);
    Put(participants[i * 2], 8, first); Put(participants[i * 2 + 1], 8, second);
    participant_pointers[i * 2] = participants[i * 2].data();
    participant_pointers[i * 2 + 1] = participants[i * 2 + 1].data();
    Put(wars[i], 0x28, &participant_pointers[i * 2]);
    Put(wars[i], 0x30, std::int32_t{1}); Put(wars[i], 0x34, std::int32_t{1});
    Put(wars[i], 0x88, &participant_pointers[i * 2 + 1]);
    Put(wars[i], 0x90, std::int32_t{1}); Put(wars[i], 0x94, std::int32_t{1});
  }
  Put(definition, 0x14, std::uint32_t{0x11223344});
  Put(definition, 0x18, a::kInteractionKey.data());
  Put(definition, 0x28, static_cast<std::uint64_t>(a::kInteractionKey.size()));
  Put(definition, 0x30, static_cast<std::uint64_t>(a::kInteractionKey.size()));
  Put(definition, 0x38, std::uint32_t{0x4744624F});
  bindings.enabled = true; bindings.core.enabled = true;
  bindings.core.character_storage_slot = &character_slot;
  bindings.context.enabled = true; bindings.context.interaction_database_slot = &database;
  bindings.context.refresh = Refresh; bindings.context.finalize = Finalize;
  bindings.context.validate = Validate; bindings.context.destroy = Destroy;
  bindings.context.evaluate_cost = Cost; bindings.context.recipient_answer_score = Answer;
  bindings.context.evaluate_trigger = Trigger;
  bindings.construct_context = Construct; bindings.war_storage_slot = &war_slot;
  bindings.war_fallback_slot = &war_fallback; bindings.interaction_missing_slot = &interaction_missing;
  bindings.is_allied = Allied; bindings.key_hash = Hash; bindings.lookup_definition = Lookup;
  bindings.can_pick_war_target = Pick; bindings.was_called = Called;
  bindings.contains_participant = Contains;
}

void PositiveProductionPath() {
  Fixture f; a::Snapshot snapshot; std::string_view reason;
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason), "concrete alliance war reader");
  Check(reason.empty() && snapshot.first_has_second && snapshot.second_has_first,
        "native bilateral alliance read");
  Check(snapshot.first_wars.size() == 1 && snapshot.second_wars.size() == 2,
        "both concrete current war sets are retained");
  const auto &offensive = snapshot.second_wars[0];
  const auto &defensive = snapshot.second_wars[1];
  Check(offensive.war_id == ally_attack && offensive.caller_character_id == ally &&
        offensive.recipient_character_id == actor && offensive.caller_side == a::Side::attacker &&
        offensive.recipient_side == a::Side::absent && offensive.caller_is_primary_war_leader,
        "offensive exposure uses ally as caller and player as recipient");
  Check(defensive.war_id == ally_defend && defensive.caller_side == a::Side::defender &&
        defensive.primary_attacker_character_id == enemy && defensive.primary_defender_character_id == ally,
        "defensive exposure remains separate from offensive exposure");
  Check(offensive.attacker_character_ids == std::vector<std::int32_t>{ally} &&
        defensive.defender_character_ids == std::vector<std::int32_t>{ally},
        "exact participant graph copied to portable IDs");
  Check(offensive.native_complete_can_send && offensive.native_target_row_selectable &&
        offensive.send_cost_raw[0] == 100'000 && defensive.send_cost_raw[0] == 200'000 &&
        offensive.send_cost_raw[9] == 1'000'000 && offensive.recipient_acceptance_raw == -2'500'000,
        "target-bound real ten-cost vector and negative native acceptance");
  Check(f.constructions == 3 && f.destructions == 3 && f.refreshes == 3 && f.finalizations == 3 &&
        f.validates == 3 && f.cost_reads == 3 && f.target_gates == 3 && f.answer_reads == 3,
        "one purposefully observed native evaluation per actual war and complete cleanup");
}

void ObservedNegatives() {
  Fixture f; a::Snapshot snapshot; std::string_view reason;
  f.can_send = false; f.pick = true;
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        !snapshot.second_wars[0].native_complete_can_send &&
        snapshot.second_wars[0].native_target_row_selectable,
        "complete CanSend negative is observable and distinct from target row predicate");
  f.can_send = true; f.pick = false;
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) &&
        snapshot.second_wars[0].native_complete_can_send &&
        !snapshot.second_wars[0].native_target_row_selectable,
        "target predicate negative is preserved independently of complete CanSend");
  f.pick = true; f.was_called = true;
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) &&
        snapshot.second_wars[0].recipient_was_called &&
        !snapshot.second_wars[0].native_target_row_selectable,
        "WasCalled prevents repeated selectable target without inventing an action");
  f.was_called = false; f.allied = false;
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) && !snapshot.first_has_second &&
        !snapshot.second_has_first && !snapshot.second_wars[0].native_complete_can_send &&
        snapshot.second_wars.size() == 2,
        "prospective alliance current negative retains real ally war exposure");
  Put(f.participants[3], 8, actor); // Player is currently on the opposite side.
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) &&
        snapshot.second_wars[0].recipient_side == a::Side::defender &&
        !snapshot.second_wars[0].native_target_row_selectable,
        "opposite-side participation is visible rather than collapsed into already joined");
}

void EmptyAndReadFailures() {
  Fixture f; a::Snapshot snapshot; std::string_view reason;
  Put(f.ally_realm, a::kRealmWarIdsOffset + 0xC, std::int32_t{0});
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) && snapshot.second_wars.empty(),
        "known empty current ally war set");
  Put(f.actor_object, a::kCharacterRealmOffset, static_cast<void *>(nullptr));
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot) && snapshot.first_wars.empty(),
        "null realm follows native empty fallback vector");
  Put(f.actor_object, a::kCharacterRealmOffset, f.actor_realm.data());
  Put(f.wars[0], 0x359, std::uint8_t{1});
  Check(a::Read(f.bindings, f.frame, actor, ally, snapshot), "adjacent nonzero byte is not ended flag");
  Put(f.wars[0], 0x358, std::uint8_t{1});
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "active_war_full_id_unavailable" && snapshot.first_wars.empty(),
        "actual ended war cannot become a current zero-cost observation");
  Put(f.wars[0], 0x358, std::uint8_t{0});
  f.first_wars[0] = 0x0A000000;
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "active_war_full_id_unavailable", "stale generation is not another war's ID");
  f.first_wars[0] = own_war; f.identity_drift = true;
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "call_ally_finalized_context_identity_unavailable" && f.constructions == f.destructions,
        "native role drift remains unavailable and disposable context is released");
  f.identity_drift = false; f.acceptance_unavailable = true;
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "call_ally_native_acceptance_unavailable" && f.constructions == f.destructions,
        "native missing acceptance is not a legal raw zero");
  f.acceptance_unavailable = false;
  Put(f.definition, 0x28, std::uint64_t{1});
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "call_ally_definition_identity_unavailable", "stable definition key identity mismatch");
  Put(f.definition, 0x28, static_cast<std::uint64_t>(a::kInteractionKey.size()));
  f.frame.clock.paused = false;
  Check(!a::Read(f.bindings, f.frame, actor, ally, snapshot, &reason) &&
        reason == "paused_played_character_frame_required", "query is explicitly a paused observation");
  f.frame.clock.paused = true;
  Check(!a::Read(f.bindings, f.frame, actor, ally + 0x01000000, snapshot, &reason) &&
        reason == "alliance_pair_full_id_or_liveness_unavailable", "character full ID is portable identity");
}

void BindingContract() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto b = a::BindImage(base, kExecutableSha256);
  Check(b.enabled && reinterpret_cast<std::uintptr_t>(b.is_allied) == base + a::kIsAlliedRva &&
        reinterpret_cast<std::uintptr_t>(b.can_pick_war_target) == base + a::kCanPickWarTargetRva &&
        reinterpret_cast<std::uintptr_t>(b.was_called) == base + a::kWasCalledRva,
        "exact new-version native entry binding");
  Check(!a::BindImage(base, "old-build").enabled, "old image is not a 1.20 native producer");
}
} // namespace

int main() {
  try {
    BindingContract(); PositiveProductionPath(); ObservedNegatives(); EmptyAndReadFailures();
    std::cout << "GREEN alliance war production observer: 4 suites / no game access\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n'; return 1;
  }
}
