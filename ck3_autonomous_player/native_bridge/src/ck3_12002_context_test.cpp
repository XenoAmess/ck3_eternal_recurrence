#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_12002_context.hpp"
#ifdef XAR_MARRIAGE_PROBE_TEST
#include "xar_bridge/ck3_12002_marriage_probe.hpp"
#endif

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <span>
#include <vector>

namespace {
using namespace xar::ck3_12002;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
template <typename T> T Read(const void *base, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
void *player = nullptr;
std::array<std::uintptr_t, 9> command_vtable{};
std::uintptr_t secondary_vtable = 0x12002;
bool legal = true, queue_accepts = true, bad_command = false;
int redirects = 0, constructs = 0, destroys = 0, clones = 0, queues = 0;
void *expected_definition = nullptr;
void *LocalPlayer(void *) { return player; }
void Redirect(void *definition, std::int32_t *actor, std::int32_t *recipient,
    std::int32_t *secondary_actor, std::int32_t *secondary_recipient,
    std::int32_t *intermediary, std::int32_t *added) {
  assert(definition == expected_definition && *added == -1);
  assert(*actor == *secondary_actor && *recipient == *secondary_recipient);
  assert(*intermediary == -1);
  ++redirects;
  // One deterministic native role redirect, retaining the proposed marriage IDs.
  *intermediary = 0x05000006;
}
void *Construct(void *context, void *definition, std::int32_t actor,
    std::int32_t recipient, std::int32_t sa, std::int32_t sr,
    std::int32_t intermediary, void *extra) {
  assert(extra == nullptr); ++constructs;
  Put(context, 0, definition); Put(context, 0x2D8, actor);
  Put(context, 0x2DC, recipient); Put(context, 0x2E0, sa);
  Put(context, 0x2E4, sr); Put(context, 0x2E8, intermediary);
  return context;
}
void Refresh(void *, bool refresh) { assert(refresh); }
void Finalize(void *) {}
bool Validate(void *context, void *error) {
  assert(error == nullptr);
  return legal && (Read<std::int32_t>(context, 0x2DC) & 0xFFFFFF) != 3;
}
void Destroy(void *context) { ++destroys; Put(context, 0, static_cast<void *>(nullptr)); }
std::int64_t *RecipientScore(void *, std::int64_t *out) { *out = -23'00000; return out; }
std::int64_t *IntermediaryScore(void *, std::int64_t *out) { *out = 71'00000; return out; }
void Cost(const void *block, const void *scope, std::int64_t *out) {
  assert(block == static_cast<std::byte *>(expected_definition) + 0x40);
  assert(Read<void *>(static_cast<const std::byte *>(scope) - 8, 0) == expected_definition);
  for (int index = 0; index < 10; ++index) {
    assert(out[index] == 0); out[index] = (index + 1) * 100'000;
  }
}
bool Trigger(void *, const void *) { return true; }
void **Clone(const void *source, void **out) {
  ++clones; auto *copy = new std::array<std::byte, 0x368>;
  std::memcpy(copy->data(), source, copy->size()); *out = copy; return out;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  assert(manager == &queues && flags == 0x0E); ++queues;
  assert(Read<std::int32_t>(*owned, 0x20 + 0x2DC) == 0x04000002);
  delete static_cast<std::array<std::byte, 0x368> *>(*owned); *owned = nullptr;
  return queue_accepts;
}
void *Send(void *command, const void *context) {
  Put(command, 0, reinterpret_cast<std::uintptr_t>(command_vtable.data()));
  Put(command, 0x18, bad_command ? std::uintptr_t{0xBAD} : secondary_vtable);
  std::memcpy(static_cast<std::byte *>(command) + 0x20, context, 0x338);
  return command;
}

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local_player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 5> characters{};
  std::array<std::byte, 0x30> family{};
  std::array<std::int32_t, 3> spouses{0x04000002, 0x01000002, 0x05000006};
  std::array<std::byte, 0x1000> interaction_database{};
  std::array<std::byte, 0x2720> definition{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *store_pointer = store.data(), *database_pointer = interaction_database.data();
  ContextBindings bindings;
  Fixture() {
    Put(state.data(), 8, std::int32_t{53175816});
    Put(state.data(), 0x70, std::int32_t{2}); Put(state.data(), 0xA0, data.data());
    Put(jomini.data(), 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7}); Put(local_player.data(), 0x70, std::int32_t{7});
    Put(data.data(), 0x222E8 + 0x58, entries.data());
    Put(data.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, std::int32_t{0x03000001});
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{8});
    const std::array<std::int32_t, 5> ids{0x03000001, 0x04000002, 0x03000003, 0x03000004, 0x05000006};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(characters[index].data(), 0x18, ids[index]);
      Put(slots.data(), (ids[index] & 0xFFFFFF) * 0x10 + 8, characters[index].data());
    }
    // Dead candidate at the NEW offset, then a wrong-generation/slot object.
    Put(characters[3].data(), 0x1D0, family.data());
    Put(slots.data(), 5 * 0x10 + 8, characters[1].data());
    Put(characters[0].data(), 0x1A8, family.data());
    Put(characters[0].data(), 0x1A0, reinterpret_cast<void *>(0xBAD));
    Put(family.data(), 0x10, std::int32_t{0x05000006});
    Put(family.data(), 0x14, std::int32_t{0x04000002});
    Put(family.data(), 0x20, spouses.data());
    Put(family.data(), 0x28, std::int32_t{3}); Put(family.data(), 0x2C, std::int32_t{3});
    Put(interaction_database.data(), 0xF30, definition.data());
    Put(interaction_database.data(), 0xF48, reinterpret_cast<void *>(0xBAD));
    Put(definition.data(), 0x2718, std::uint8_t{1});
    expected_definition = definition.data(); player = local_player.data();
    command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    bindings.enabled = true;
    bindings.core = {true, &state_pointer, &jomini_pointer, &store_pointer, &LocalPlayer};
    bindings.commands.enabled = true; bindings.commands.command_manager = &queues;
    bindings.commands.queue_owned_command = &Queue;
    bindings.interaction_database_slot = &database_pointer;
    bindings.redirect_roles = &Redirect; bindings.construct_all_roles = &Construct;
    bindings.refresh = &Refresh; bindings.finalize = &Finalize;
    bindings.validate = &Validate; bindings.destroy = &Destroy;
    bindings.recipient_answer_score = &RecipientScore; bindings.intermediary_answer_score = &IntermediaryScore;
    bindings.evaluate_cost = &Cost; bindings.evaluate_trigger = &Trigger;
    bindings.construct_send_command = &Send;
    bindings.send_primary_vtable = reinterpret_cast<std::uintptr_t>(command_vtable.data());
    bindings.send_secondary_vtable = secondary_vtable;
  }
};
} // namespace

int main() {
  using namespace xar::game;
  Fixture f;
  assert(BindContextImage(0x140000000, kExecutableSha256).enabled);
  assert(!BindContextImage(0, kExecutableSha256).enabled);
  assert(!BindContextImage(0x140000000, "1.19.0.6").enabled);
  PlayedCharacterRelationships12002 relationships{};
  assert(ReadPlayedCharacterRelationships(f.bindings.core, 0x03000001, relationships));
  assert(relationships.betrothed_character_id == 0x05000006);
  assert(relationships.primary_spouse_character_id == 0x04000002);
  assert((relationships.spouse_character_ids == std::vector<std::int32_t>{0x04000002, 0x05000006}));
  Put(f.family.data(), 0x2C, std::int32_t{4});
  assert(!ReadPlayedCharacterRelationships(f.bindings.core, 0x03000001, relationships));
  assert(relationships.spouse_character_ids.empty());
  Put(f.family.data(), 0x2C, std::int32_t{3});
  std::vector<ArrangeMarriageChoice> choices;
  std::vector<MarriageCandidateEvaluation12002> rows;
  ArrangeMarriageQueryDiagnostics diagnostics{};
  assert(ReadArrangeMarriageChoices(f.bindings, choices, diagnostics, &rows) == ReadArrangeMarriageChoicesResult::available);
  assert(choices.size() == 2 && rows.size() == choices.size());
  assert(diagnostics.slots_scanned == 8 && diagnostics.self_candidates == 1);
  assert(diagnostics.dead_candidates == 1 && diagnostics.generation_mismatch_candidates == 1);
  assert(diagnostics.native_validate_false == 1 && diagnostics.native_validate_true == 2);
  assert(diagnostics.contexts_constructed == 3 && constructs == destroys && redirects == constructs);
  assert(rows[0].recipient_acceptance_score_raw == -23'00000 && rows[0].native_auto_accept);
  assert(rows[0].send_costs_raw[9] == 1'000'000);
  assert(rows[0].roles.intermediary_character_id == 0x05000006);
#ifdef XAR_MARRIAGE_PROBE_TEST
  std::string probe_json;
  assert(CollectMarriageProbe12002(f.bindings, probe_json));
  assert(probe_json.find("\"query_status\":\"available\"") != std::string::npos);
  assert(probe_json.find("\"recipient_acceptance_score_raw\":-2300000") != std::string::npos);
  assert(probe_json.find("\"send_costs_raw\":[100000,200000,300000,400000,500000,600000,700000,800000,900000,1000000]") != std::string::npos);
  std::cout << probe_json;
#endif
  const ArrangeMarriageChoice chosen{0x03000001, 0x04000002};
  assert(SubmitArrangeMarriage(f.bindings, chosen) == ArrangeMarriageResult::submitted);
  assert(clones == 1 && queues == 1 && destroys == constructs + 1);
  queue_accepts = false;
  assert(SubmitArrangeMarriage(f.bindings, chosen) == ArrangeMarriageResult::unavailable);
  assert(clones == 2 && queues == 2);
  bad_command = true;
  assert(SubmitArrangeMarriage(f.bindings, chosen) == ArrangeMarriageResult::unavailable);
  assert(clones == 2 && queues == 2);
  bad_command = false; legal = false;
  assert(SubmitArrangeMarriage(f.bindings, chosen) == ArrangeMarriageResult::choice_unavailable);
  assert(SubmitArrangeMarriage(f.bindings, {0x03000001, 0x01000002}) == ArrangeMarriageResult::candidate_not_found);
  assert(SubmitArrangeMarriage(f.bindings, {0x03000002, 0x04000002}) == ArrangeMarriageResult::choice_unavailable);
  assert(ReadArrangeMarriageChoices(f.bindings, choices, diagnostics, &rows) == ReadArrangeMarriageChoicesResult::available);
  assert(choices.empty() && rows.empty() && diagnostics.native_validate_false == 3);
  f.bindings.enabled = false;
  assert(ReadArrangeMarriageChoices(f.bindings, choices, diagnostics, &rows) == ReadArrangeMarriageChoicesResult::unavailable);
  assert(choices.empty() && rows.empty());
#ifdef XAR_MARRIAGE_PROBE_TEST
  assert(!CollectMarriageProbe12002(f.bindings, probe_json));
  assert(probe_json.find("\"query_status\":\"unavailable\"") != std::string::npos);
  assert(probe_json.find("\"marriage_candidate_evaluations\":[]") != std::string::npos);
#endif
  std::cout << "PASS 1.20.0.2 offline relationships, redirected marriage legality/cost/acceptance and command ownership\n";
}
