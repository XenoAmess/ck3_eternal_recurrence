#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12002_family_abi.hpp"
#include "xar_bridge/ck3_12002_family_wire.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t actor_id = 0x03000001, heir_id = 0x03000002,
    partner_id = 0x03000003, recipient_id = 0x03000004;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
template <typename T> T Load(const void *base, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T)); return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *local_player = nullptr, *definition = nullptr;
bool legal = false, queued = true, bad_copy = false, bad_actor = false;
bool matrilineal_default = false, grand_wedding = false, mutate_date = false;
void *state_to_mutate = nullptr;
int redirects = 0, contexts = 0, destroys = 0, clones = 0, queue_calls = 0;
std::array<std::uintptr_t, 9> vtable{};
std::array<void *, 8> projection_characters{};
constexpr std::uintptr_t secondary_vtable = 0x12002;
void *LocalPlayer(void *) { return local_player; }
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient,
    std::int32_t *subject, std::int32_t *candidate, std::int32_t *intermediary,
    std::int32_t *sixth_role) {
  Check(def == definition && *actor == actor_id && *subject == heir_id &&
      *candidate >= partner_id && *candidate <= 0x03000008 && *recipient == *candidate && *intermediary == -1 &&
      *sixth_role == -1, "six-role redirect ABI / observed pair");
  ++redirects;
  *recipient = recipient_id;
  if (bad_actor) *actor = recipient_id;
}
void *Construct(void *context, void *def, std::int32_t actor, std::int32_t recipient,
    std::int32_t subject, std::int32_t candidate, std::int32_t intermediary, void *extra) {
  Check(extra == nullptr, "ordinary context final parameter");
  ++contexts;
  Put(context, 0, def); Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, subject); Put(context, 0x2E4, candidate); Put(context, 0x2E8, intermediary);
  Put(context, 0x300, std::uint8_t{grand_wedding});
  Put(context, 0x301, std::uint8_t{matrilineal_default});
  return context;
}
void Refresh(void *, bool full) { Check(full, "native refresh flag"); }
void Finalize(void *) {}
bool Validate(void *context, void *error) {
  Check(error == nullptr && Load<std::int32_t>(context, 0x2E0) == heir_id,
      "full validator must evaluate heir permissions");
  return legal;
}
std::int64_t *Score(void *, std::int64_t *out) { *out = 1'600'000; return out; }
std::uint8_t Answer(void *, std::uint8_t mode, std::uint8_t flag, void *a, void *b) {
  Check(mode == 1 && flag == 1 && a == nullptr && b == nullptr, "final answer ABI");
  if (mutate_date) Put(state_to_mutate, 8, std::int32_t{53220024});
  return 0;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  Check(block == static_cast<std::byte *>(definition) + 0x40 &&
      Load<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition,
      "native ten-resource cost ABI");
  for (int index = 0; index < 10; ++index) out[index] = index == 0 ? -20'000 : index * 10'000;
}
bool Option(const void *context, std::uint32_t id) {
  Check(id == 1 || id == 2, "bound option identity");
  return Load<std::uint8_t>(context, 0x300 + id - 1) != 0;
}
void SetOption(void *context, std::uint32_t id, bool selected) {
  Check(id == 2, "typed proposal matrilineal option only");
  Put(context, 0x301, static_cast<std::uint8_t>(selected));
}
bool Memory(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (address == 0 || out == nullptr) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size); return true;
}
bool Allied(const void *, const void *) { return false; }
bool FertilityGate(void *) { return false; }
void Project(const void *context, void *out) {
  struct Header { void *data; std::int32_t capacity, count; void *owner; };
  struct Row { const void *first, *second, *subject, *candidate; };
  auto &header = *static_cast<Header *>(out);
  const void *candidate = nullptr;
  for (const auto *character : projection_characters) {
    if (Load<std::int32_t>(character, 0x18) == Load<std::int32_t>(context, 0x2E4)) {
      candidate = character;
      break;
    }
  }
  Check(candidate != nullptr, "native projected pair uses the actual context candidate");
  const std::array<Row, 3> pairs{{
      {projection_characters[0], projection_characters[3], projection_characters[1], candidate},
      {projection_characters[0], candidate, projection_characters[1], candidate},
      {projection_characters[1], projection_characters[3], projection_characters[1], candidate}}};
  std::memcpy(header.data, pairs.data(), sizeof(pairs)); header.count = 3;
}
void Destroy(void *context) { ++destroys; Put(context, 0, static_cast<void *>(nullptr)); }
void *Send(void *command, const void *context) {
  Put(command, 0, reinterpret_cast<std::uintptr_t>(vtable.data()));
  Put(command, 0x18, secondary_vtable);
  std::memcpy(static_cast<std::byte *>(command) + 0x20, context, 0x338);
  if (bad_copy) Put(command, 0x20 + 0x301, std::uint8_t{1});
  return command;
}
void **Clone(const void *command, void **out) {
  ++clones;
  auto *copy = new std::array<std::byte, 0x368>;
  std::memcpy(copy->data(), command, copy->size()); *out = copy; return out;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Check(manager == &queue_calls && flags == 0x0E && *owned != nullptr, "owning queue ABI");
  ++queue_calls;
  Check(Load<std::int32_t>(*owned, 0x20 + 0x2D8) == actor_id &&
      Load<std::int32_t>(*owned, 0x20 + 0x2DC) == recipient_id &&
      Load<std::int32_t>(*owned, 0x20 + 0x2E0) == heir_id &&
      Load<std::int32_t>(*owned, 0x20 + 0x2E4) == partner_id,
      "queued context keeps heir / recipient permissions");
  delete static_cast<std::array<std::byte, 0x368> *>(*owned); *owned = nullptr;
  return queued;
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 16 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 8> characters{};
  std::array<std::array<std::byte, 0x30>, 8> families{};
  std::array<std::byte, 0x1000> database{};
  std::array<std::byte, 0x2720> def{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(),
      *store_ptr = store.data(), *database_ptr = database.data();
  std::int32_t threshold_zero = 16, threshold_one = 16;
  std::uint32_t grand_id = 1, matri_id = 2;
  FamilyBindings bindings{};
  Fixture() {
    legal = false; queued = true; bad_copy = bad_actor = grand_wedding =
        matrilineal_default = mutate_date = false;
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game.data()); Put(jomini.data(), 0x18, players.data());
    jomini[0x20] = std::byte{1}; Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local.data(), 0x70, std::int32_t{7});
    Put(game.data(), 0x222E8 + 0x58, entries.data());
    Put(game.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{16});
    const std::array<std::int32_t, 8> ids{actor_id, heir_id, partner_id, recipient_id,
        0x03000005, 0x03000006, 0x03000007, 0x03000008};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(characters[index].data(), 0x18, ids[index]);
      Put(slots.data(), (ids[index] & 0xFFFFFF) * 0x10 + 8, characters[index].data());
      Put(characters[index].data(), 0x1A8, families[index].data());
      // A legacy family pointer read would consume this unrelated field.
      Put(characters[index].data(), 0x1A0, std::uint64_t{0});
      Put(families[index].data(), 0x10, std::int32_t{-1});
      Put(families[index].data(), 0x14, std::int32_t{-1});
      Put(characters[index].data(), 0x68, std::int16_t{14});
      Put(characters[index].data(), 0x158, std::int32_t{-1});
      Put(characters[index].data(), 0x1C0, std::uintptr_t{1});
      if (index >= 4) {
        Put(characters[index].data(), 0x1D0, std::uintptr_t{1});
        Put(characters[index].data(), 0x1A1, std::uint8_t{1});
      }
      projection_characters[index] = characters[index].data();
    }
    Put(characters[2].data(), 0x1A1, std::uint8_t{1});
    Put(families[1].data(), 0x10, partner_id); Put(families[2].data(), 0x10, heir_id);
    Put(database.data(), 0xF30, def.data()); definition = def.data(); local_player = local.data();
    state_to_mutate = state.data(); vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    auto &c = bindings.context;
    bindings.enabled = c.enabled = true;
    c.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer};
    bindings.values.enabled = true; bindings.values.core = c.core;
    bindings.values.fertility_gate = &FertilityGate;
    c.commands.enabled = true; c.commands.command_manager = &queue_calls;
    c.commands.queue_owned_command = &Queue; c.interaction_database_slot = &database_ptr;
    c.redirect_roles = &Redirect; c.construct_all_roles = &Construct; c.refresh = &Refresh;
    c.finalize = &Finalize; c.validate = &Validate; c.destroy = &Destroy;
    c.recipient_answer_score = &Score; c.evaluate_cost = &Cost; c.construct_send_command = &Send;
    c.send_primary_vtable = reinterpret_cast<std::uintptr_t>(vtable.data());
    c.send_secondary_vtable = secondary_vtable;
    bindings.evaluate_answer = &Answer; bindings.read_boolean_option = &Option;
    bindings.set_boolean_option = &SetOption;
    bindings.adult_threshold_zero = &threshold_zero; bindings.adult_threshold_one = &threshold_one;
    bindings.grand_wedding_option = &grand_id; bindings.matrilineal_option = &matri_id;
  }
  auto Read() {
    return ReadCurrentFirstHeirBetrothalActionabilityV1(bindings,
        ReadCurrentFirstHeirRelationshipV1(bindings, heir_id));
  }
  FamilyProjectionBindings Projection() {
    FamilyProjectionBindings p{};
    p.exact_build_admitted = true; p.admitted_executable_sha256 = kExecutableSha256;
    p.offline_fixture = true; p.read_memory = &Memory; p.project_pairs = &Project;
    p.read_boolean_option = &Option; p.set_boolean_option = &SetOption; p.is_allied = &Allied;
    p.matrilineal_option_id_slot = reinterpret_cast<std::uintptr_t>(&matri_id);
    p.native_owner_vtable = 1;
    return p;
  }
};
} // namespace

int main() {
  try {
    using Result = xar::bridge::MarriageProposalNativeSubmitResultV1;
    using Failure = xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1;
    const auto bound = BindFamilyImage(0x140000000, kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.evaluate_answer) ==
        0x140000000 + kFamilyEvaluateAnswerRva, "exact-build new answer binding");
    Check(!BindFamilyImage(0x140000000, "1.19.0.6").enabled, "old build rejected");
    Fixture f;
    auto relationship = ReadCurrentFirstHeirRelationshipV1(f.bindings, heir_id);
    Check(relationship.failure == Failure::none && relationship.relationship.betrothed_character_id == partner_id,
        "bilateral current pair");
    auto observed = f.Read();
    std::cout << "XAR_FAMILY_OFFLINE_CURRENT_PAIR_NEGATIVE " <<
        xar::ck3_11906::CurrentFirstHeirBetrothalActionabilityJsonV1(observed) << '\n';
    Check(observed.unavailable_reason.empty() && observed.has_betrothal && observed.adult_readback_available &&
        observed.adult.subject_adult_measure_raw == 14 && observed.adult.candidate_adult_measure_raw == 14 &&
        observed.adult.subject_adult_threshold_raw == 16 && !observed.adult.subject_is_adult &&
        !observed.adult.candidate_is_adult && observed.final_legality_sampled && !observed.complete_can_send &&
        observed.recipient_acceptance_ready && observed.recipient_ai_accept_raw == 1'600'000 &&
        observed.recipient_character_id == recipient_id && observed.generic_cost_raw[0] == -20'000 &&
        observed.generic_cost_raw[9] == 90'000 && observed.outcome_available && observed.lineality_available &&
        observed.adult.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::betrothal,
        "BA5 14 < 16 negative is complete observation, including native signed costs");
    xar::bridge::ObservedHeirMarriagePendingV1 pending{};
    const auto old_queue_calls = queue_calls;
    Check(SubmitCurrentFirstHeirBetrothalFulfillmentV1(f.bindings, actor_id, heir_id, observed, 4, pending) ==
        Result::rejected && queue_calls == old_queue_calls && !pending.fulfill_existing_betrothal,
        "minor cannot fulfill or create pending / queued command");
    Put(f.families[2].data(), 0x10, std::int32_t{-1});
    Check(ReadCurrentFirstHeirRelationshipV1(f.bindings, heir_id).failure == Failure::bilateral_inconsistent,
        "one-way betrothal is unavailable, not empty");
    Put(f.families[2].data(), 0x10, heir_id);
    Put(f.families[1].data(), 0x10, std::int32_t{0x07000003});
    Check(ReadCurrentFirstHeirRelationshipV1(f.bindings, heir_id).failure == Failure::relationship_unavailable,
        "generation mismatch is unavailable, not empty");
    Put(f.families[1].data(), 0x10, partner_id);
    Put(f.characters[1].data(), 0x68, std::int16_t{16});
    Put(f.characters[2].data(), 0x68, std::int16_t{16}); legal = true;
    observed = f.Read();
    Check(observed.unavailable_reason.empty() && observed.complete_can_send &&
        observed.adult.subject_is_adult && observed.adult.candidate_is_adult &&
        observed.adult.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::marriage,
        "adult native actionable pair");
    Check(SubmitCurrentFirstHeirBetrothalFulfillmentV1(f.bindings, actor_id, heir_id, observed, 5, pending) ==
        Result::submitted && pending.fulfill_existing_betrothal && pending.heir_character_id == heir_id &&
        pending.candidate_character_id == partner_id && queue_calls == old_queue_calls + 1,
        "typed fulfillment copies exact pair / roles / default lineality into owning queue");
    xar::bridge::MarriageProposalBilateralRelationshipV1 after{};
    Check(ReadFamilyBilateralRelationshipV1(f.bindings, heir_id, partner_id, after) &&
        xar::bridge::ReadObservedHeirMarriageMaterialStatusV1(pending, after, 6) ==
            xar::bridge::ObservedHeirMarriageMaterialStatusV1::pending,
        "ACK and retained betrothal do not claim marriage");
    bad_copy = true;
    Check(SubmitCurrentFirstHeirBetrothalFulfillmentV1(f.bindings, actor_id, heir_id, observed, 7, pending) ==
        Result::unavailable && queue_calls == old_queue_calls + 1, "copied option changed before queue");
    bad_copy = false; queued = false;
    Check(SubmitCurrentFirstHeirBetrothalFulfillmentV1(f.bindings, actor_id, heir_id, observed, 7, pending) ==
        Result::rejected && !pending.fulfill_existing_betrothal, "queue rejection has no material result");
    queued = true; bad_actor = true;
    Check(f.Read().unavailable_reason == "current_betrothal_context_unavailable", "cannot borrow another actor's permissions");
    bad_actor = false; grand_wedding = true;
    auto wedding = f.Read();
    Check(wedding.adult.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::betrothal &&
        SubmitCurrentFirstHeirBetrothalFulfillmentV1(f.bindings, actor_id, heir_id, wedding, 8, pending) == Result::rejected,
        "grand wedding retains betrothal mode, not fulfillment");
    grand_wedding = false; mutate_date = true;
    Check(f.Read().unavailable_reason == "current_betrothal_frame_changed", "native frame drift remains unavailable");
    mutate_date = false; Put(f.state.data(), 8, std::int32_t{53220000});
    std::vector<xar::game::ArrangeMarriageFamilyCandidateV1> candidates;
    xar::game::ArrangeMarriageQueryDiagnostics diagnostics{};
    Check(ReadArrangeMarriageFamilyCandidatesV1(f.bindings, heir_id, candidates, diagnostics) ==
        xar::game::ReadArrangeMarriageFamilyCandidatesResultV1::available && candidates.size() == 2 &&
        diagnostics.self_candidates == 2 && candidates.front().subject_character_id == heir_id &&
        candidates.front().recipient_matchmaker_character_id == recipient_id &&
        candidates.front().heir_adult_measure_raw == 16 && candidates.front().recipient_answer_allows_send,
        "subject-specific native candidate enumeration retains actor / couple permissions");
    const auto rich = ReadMarriageCandidateAlliancePrivateV1(f.bindings, candidates.front(), f.Projection(), false, true);
    Check(rich.failure == xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none &&
        rich.projection.pair_count == 3 && rich.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::marriage &&
        rich.heir_is_adult && rich.candidate_is_adult && rich.heir_lineage.dynasty_id == -1 &&
        rich.generic_cost_raw[0] == -20'000 && rich.generic_cost_raw[9] == 90'000 &&
        rich.heir_fertility.available && rich.candidate_fertility.available &&
        !rich.heir_fertility.extension_present && rich.heir_fertility.effective_raw == 0,
        "rich projected alliance / lineage / fertility / native costs are concrete same-frame data");
    const auto selected_rich = ReadMarriageCandidateAlliancePrivateV1(f.bindings, candidates.front(), f.Projection(), true, true);
    Check(selected_rich.failure == xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none &&
        selected_rich.selected_option_readback && selected_rich.projection.matrilineal_option_selected &&
        selected_rich.effective_matrilineal_if_accepted, "rich explicit matrilineal final-context projection");
    bool forward = true, reverse = true;
    Check(ReadFamilyAlliancePairV1(f.bindings, f.Projection(), heir_id, partner_id, forward, reverse) &&
        !forward && !reverse, "independent native alliance pair false is known, not unavailable");
    xar::bridge::MarriageProposalSubmissionV1 proposal{};
    proposal.rankless_observed_heir = true;
    proposal.subject_character_id = heir_id; proposal.candidate_character_id = partner_id;
    proposal.roles.actor_character_id = actor_id; proposal.roles.recipient_character_id = recipient_id;
    proposal.roles.secondary_actor_character_id = heir_id;
    proposal.roles.secondary_recipient_character_id = partner_id;
    proposal.recipient_ai_accept_raw = 1'600'000; proposal.recipient_answer_status_raw = 0;
    proposal.require_matrilineal_option_off = true;
    const auto before_new = queue_calls;
    Check(SubmitFamilyMarriageProposalV1(f.bindings, proposal) == Result::rejected && queue_calls == before_new,
        "new-proposal mode cannot reuse existing betrothal");
    Put(f.families[1].data(), 0x10, std::int32_t{-1});
    Put(f.families[2].data(), 0x10, std::int32_t{-1});
    const auto fresh_rich = ReadMarriageCandidateAlliancePrivateV1(
        f.bindings, candidates.front(), f.Projection(), false, true);
    const auto fresh_selected_rich = ReadMarriageCandidateAlliancePrivateV1(
        f.bindings, candidates.front(), f.Projection(), true, true);
    Check(fresh_rich.failure == xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none &&
        fresh_selected_rich.failure == xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none,
        "actual new provider supplies fresh proposal rows to the existing wire serializer");
    for (std::size_t index = 4; index < f.characters.size(); ++index) {
      Put(f.characters[index].data(), 0x1D0, std::uintptr_t{0});
      Put(f.characters[index].data(), 0x68, std::int16_t{16});
    }
    std::vector<xar::game::ArrangeMarriageFamilyCandidateV1> wire_candidates;
    Check(ReadArrangeMarriageFamilyCandidatesV1(f.bindings, heir_id, wire_candidates, diagnostics) ==
        xar::game::ReadArrangeMarriageFamilyCandidatesResultV1::available,
        "actual native legal producer enumerates five independent wire fixture candidates");
    std::array<FamilyAllianceWireRowV1, 5> rich_wire{};
    std::size_t wire_count = 0;
    for (const auto &candidate : wire_candidates) {
      if (candidate.candidate_character_id == recipient_id) continue;
      Check(wire_count < rich_wire.size(), "exactly five distinct candidate fixture identities");
      auto read = ReadMarriageCandidateAlliancePrivateV1(
          f.bindings, candidate, f.Projection(), false, true);
      Check(read.failure == xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none,
          "each five-row wire entry is a separately evaluated actual provider read");
      rich_wire[wire_count++] = {candidate, read};
    }
    Check(wire_count == rich_wire.size(), "existing production rich48 five-row contract retained");
    const std::array<FamilyAllianceWireRowV1, 1> child_wire{{{candidates.front(), fresh_selected_rich}}};
    std::cout << "XAR_FAMILY_OFFLINE_RICH48 " << SerializeFamilyAllianceFrameV1(
        "offline-family-rich48", 11, 7, rich_wire) << '\n';
    std::cout << "XAR_FAMILY_OFFLINE_CHILD_VALUE " << SerializeFamilyAllianceFrameV1(
        "offline-family-child-value", 11, 7, child_wire, kFamilyChildValueWireStepV1) << '\n';
    Check(SubmitFamilyMarriageProposalV1(f.bindings, proposal) == Result::submitted && queue_calls == before_new + 1,
        "typed new proposal default-off copies finalized original pair");
    proposal.require_matrilineal_option_off = false; proposal.request_matrilineal_option = true;
    Check(SubmitFamilyMarriageProposalV1(f.bindings, proposal) == Result::submitted && queue_calls == before_new + 2,
        "typed matrilineal proposal copies selected native option");
    ++proposal.recipient_ai_accept_raw;
    Check(SubmitFamilyMarriageProposalV1(f.bindings, proposal) == Result::rejected && queue_calls == before_new + 2,
        "typed proposal rechecks final native acceptance operand");
    std::cout << "PASS CK3 1.20 family: bilateral/current pair, adult negative, roles/cost/answer, fulfillment, queue ownership, pending receipt\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
