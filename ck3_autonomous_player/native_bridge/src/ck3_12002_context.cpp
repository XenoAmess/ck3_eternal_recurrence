#include "xar_bridge/ck3_12002_context.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}

void *ResolveCharacter(const CoreBindings &core, std::int32_t id) noexcept {
  if (!core.enabled || id == -1 || core.character_storage_slot == nullptr ||
      *core.character_storage_slot == nullptr) return nullptr;
  void *storage = *core.character_storage_slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  void *slots = Load<void *>(storage, 0x20);
  if (slots == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *character = Load<void *>(slots, index * 0x10U + 0x08U);
  return character != nullptr && Load<std::int32_t>(character, 0x18) == id
             ? character : nullptr;
}

struct alignas(8) ContextStorage {
  std::array<std::byte, 0x338> bytes{};
};
struct alignas(8) SendCommandStorage {
  std::array<std::byte, 0x368> bytes{};
};
static_assert(sizeof(ContextStorage) == 0x338);
static_assert(sizeof(SendCommandStorage) == 0x368);

bool HasReadBindings(const ContextBindings &b) noexcept {
  return b.enabled && b.core.enabled && b.interaction_database_slot != nullptr &&
         *b.interaction_database_slot != nullptr && b.redirect_roles != nullptr &&
         b.construct_all_roles != nullptr && b.refresh != nullptr &&
         b.finalize != nullptr && b.validate != nullptr && b.destroy != nullptr;
}

void *MarriageDefinition(const ContextBindings &b) noexcept {
  return b.interaction_database_slot == nullptr ||
         *b.interaction_database_slot == nullptr ? nullptr :
      Load<void *>(*b.interaction_database_slot, kMarriageArrangeMarriageInteractionOffset);
}

bool PrepareContext(const ContextBindings &b, const game::ArrangeMarriageChoice &choice,
                    ContextStorage &storage,
                    game::ArrangeMarriageValidationSample &sample) noexcept {
  void *definition = MarriageDefinition(b);
  if (definition == nullptr) return false;
  std::int32_t actor = choice.played_character_id;
  std::int32_t recipient = choice.candidate_character_id;
  std::int32_t secondary_actor = actor;
  std::int32_t secondary_recipient = recipient;
  std::int32_t intermediary = -1;
  std::int32_t added_role = -1;
  b.redirect_roles(definition, &actor, &recipient, &secondary_actor,
                   &secondary_recipient, &intermediary, &added_role);
  sample.candidate_character_id = choice.candidate_character_id;
  sample.actor_character_id = actor;
  sample.recipient_character_id = recipient;
  sample.secondary_actor_character_id = secondary_actor;
  sample.secondary_recipient_character_id = secondary_recipient;
  sample.intermediary_character_id = intermediary;
  void *context = storage.bytes.data();
  if (b.construct_all_roles(context, definition, actor, recipient, secondary_actor,
                            secondary_recipient, intermediary, nullptr) != context)
    return false;
  b.refresh(context, true);
  b.finalize(context);
  return true;
}

bool EvaluateChoice(const ContextBindings &b, void *context,
                    game::MarriageCandidateEvaluation12002 &output) noexcept {
  if (b.recipient_answer_score == nullptr || b.intermediary_answer_score == nullptr ||
      b.evaluate_cost == nullptr || b.evaluate_trigger == nullptr) return false;
  void *definition = Load<void *>(context, 0);
  if (definition == nullptr ||
      b.recipient_answer_score(context, &output.recipient_acceptance_score_raw) !=
          &output.recipient_acceptance_score_raw ||
      b.intermediary_answer_score(context, &output.intermediary_acceptance_score_raw) !=
          &output.intermediary_acceptance_score_raw) return false;
  b.evaluate_cost(static_cast<const std::byte *>(definition) + 0x40,
                  static_cast<const std::byte *>(context) + 0x08,
                  output.send_costs_raw.data());
  void *trigger = Load<void *>(definition, 0x2290);
  output.native_auto_accept = trigger == nullptr ?
      Load<std::uint8_t>(definition, 0x2718) != 0 :
      b.evaluate_trigger(trigger, static_cast<const std::byte *>(context) + 0x08);
  // Native pending construction also accepts same actor and recipient directly.
  if (output.roles.actor_character_id == output.roles.recipient_character_id)
    output.native_auto_accept = true;
  return true;
}

} // namespace

ContextBindings BindContextImage(std::uintptr_t base, std::string_view sha) noexcept {
  ContextBindings b{};
  b.core = BindCoreImage(base, sha);
  b.commands = BindCommandImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.interaction_database_slot = reinterpret_cast<void **>(base + kMarriageInteractionDatabaseSlotRva);
  b.redirect_roles = reinterpret_cast<MarriageRedirectInteractionRoles>(base + kMarriageRedirectInteractionRolesRva);
  b.construct_all_roles = reinterpret_cast<MarriageConstructInteractionAllRoles>(base + kMarriageConstructInteractionAllRolesRva);
  b.refresh = reinterpret_cast<MarriageRefreshInteractionContext>(base + kMarriageRefreshInteractionContextRva);
  b.finalize = reinterpret_cast<MarriageFinalizeInteractionContext>(base + kMarriageFinalizeInteractionContextRva);
  b.validate = reinterpret_cast<MarriageValidateInteractionContext>(base + kMarriageValidateInteractionContextRva);
  b.destroy = reinterpret_cast<MarriageDestroyInteractionContext>(base + kMarriageDestroyInteractionContextRva);
  b.recipient_answer_score = reinterpret_cast<MarriageReadInteractionAnswerScore>(base + kMarriageRecipientInteractionAnswerScoreRva);
  b.intermediary_answer_score = reinterpret_cast<MarriageReadInteractionAnswerScore>(base + kMarriageIntermediaryInteractionAnswerScoreRva);
  b.evaluate_cost = reinterpret_cast<MarriageEvaluateInteractionCost>(base + kMarriageInteractionCostEvaluatorRva);
  b.evaluate_trigger = reinterpret_cast<MarriageEvaluateInteractionTrigger>(base + kMarriageInteractionTriggerEvaluatorRva);
  b.construct_send_command = reinterpret_cast<MarriageConstructSendInteractionCommand>(base + kMarriageConstructSendInteractionCommandRva);
  b.send_primary_vtable = base + kMarriageSendInteractionPrimaryVtableRva;
  b.send_secondary_vtable = base + kMarriageSendInteractionSecondaryVtableRva;
  return b;
}

bool ReadPlayedCharacterRelationships(const CoreBindings &core, std::int32_t id,
    game::PlayedCharacterRelationships12002 &output) noexcept {
  output = {};
  void *character = ResolveCharacter(core, id);
  if (character == nullptr) return false;
  void *family = Load<void *>(character, kMarriageCharacterFamilyDataOffset);
  if (family == nullptr) return true;
  const auto betrothed = Load<std::int32_t>(family, 0x10);
  const auto primary = Load<std::int32_t>(family, 0x14);
  if (ResolveCharacter(core, betrothed) != nullptr) output.betrothed_character_id = betrothed;
  if (ResolveCharacter(core, primary) != nullptr) output.primary_spouse_character_id = primary;
  const auto *ids = Load<const std::int32_t *>(family, 0x20);
  const auto capacity = Load<std::int32_t>(family, 0x28);
  const auto count = Load<std::int32_t>(family, 0x2C);
  if (count < 0 || capacity < count || count > 1'000'000 ||
      (count > 0 && ids == nullptr)) { output = {}; return false; }
  for (std::int32_t index = 0; index < count; ++index)
    if (ResolveCharacter(core, ids[index]) != nullptr)
      output.spouse_character_ids.push_back(ids[index]);
  return true;
}

game::ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const ContextBindings &b, std::vector<game::ArrangeMarriageChoice> &output,
    game::ArrangeMarriageQueryDiagnostics &d,
    std::vector<game::MarriageCandidateEvaluation12002> *evaluations) noexcept {
  output.clear(); d = {};
  if (evaluations != nullptr) evaluations->clear();
  if (!HasReadBindings(b) || MarriageDefinition(b) == nullptr)
    return game::ReadArrangeMarriageChoicesResult::unavailable;
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(b.core, current)) return game::ReadArrangeMarriageChoicesResult::unavailable;
  if (!current.has_played_character || !current.played_character_alive)
    return game::ReadArrangeMarriageChoicesResult::no_played_character;
  void *store = b.core.character_storage_slot == nullptr ? nullptr : *b.core.character_storage_slot;
  if (store == nullptr) return game::ReadArrangeMarriageChoicesResult::unavailable;
  void *slots = Load<void *>(store, 0x20);
  const auto count = Load<std::int32_t>(store, 0x2C);
  d.storage_capacity = count;
  if (slots == nullptr || count <= 0 || count > 1'000'000)
    return game::ReadArrangeMarriageChoicesResult::unavailable;
  std::vector<game::ArrangeMarriageChoice> choices;
  std::vector<game::MarriageCandidateEvaluation12002> rows;
  for (std::int32_t index = 0; index < count; ++index) {
    ++d.slots_scanned;
    void *candidate = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
    if (candidate == nullptr) { ++d.empty_slots; continue; }
    const auto id = Load<std::int32_t>(candidate, 0x18);
    if (id == current.played_character_id) { ++d.self_candidates; continue; }
    if (Load<void *>(candidate, kCharacterDeathDataOffset) != nullptr) { ++d.dead_candidates; continue; }
    if ((static_cast<std::uint32_t>(id) & 0x00FFFFFFU) != static_cast<std::uint32_t>(index) ||
        ResolveCharacter(b.core, id) != candidate) { ++d.generation_mismatch_candidates; continue; }
    ++d.live_candidates;
    ContextStorage storage{};
    game::MarriageCandidateEvaluation12002 row{};
    row.choice = {current.played_character_id, id};
    row.roles.slot_index = index;
    if (!PrepareContext(b, row.choice, storage, row.roles)) {
      ++d.context_construct_failures;
      return game::ReadArrangeMarriageChoicesResult::unavailable;
    }
    ++d.contexts_constructed;
    row.native_legal = b.validate(storage.bytes.data(), nullptr);
    if (!row.native_legal) {
      ++d.native_validate_false;
      if (d.validation_false_samples.size() < 8) d.validation_false_samples.push_back(row.roles);
    } else {
      ++d.native_validate_true;
      choices.push_back(row.choice);
      if (evaluations != nullptr && !EvaluateChoice(b, storage.bytes.data(), row)) {
        b.destroy(storage.bytes.data());
        return game::ReadArrangeMarriageChoicesResult::unavailable;
      }
      if (evaluations != nullptr) rows.push_back(std::move(row));
    }
    b.destroy(storage.bytes.data());
  }
  output = std::move(choices);
  if (evaluations != nullptr) *evaluations = std::move(rows);
  return game::ReadArrangeMarriageChoicesResult::available;
}

game::ArrangeMarriageResult SubmitArrangeMarriage(const ContextBindings &b,
    const game::ArrangeMarriageChoice &choice) noexcept {
  if (!HasReadBindings(b) || b.construct_send_command == nullptr ||
      !b.commands.enabled || b.send_primary_vtable == 0 || b.send_secondary_vtable == 0)
    return game::ArrangeMarriageResult::unavailable;
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(b.core, current)) return game::ArrangeMarriageResult::unavailable;
  if (!current.has_played_character || !current.played_character_alive)
    return game::ArrangeMarriageResult::no_played_character;
  if (choice.played_character_id != current.played_character_id ||
      choice.candidate_character_id == current.played_character_id)
    return game::ArrangeMarriageResult::choice_unavailable;
  void *candidate = ResolveCharacter(b.core, choice.candidate_character_id);
  if (candidate == nullptr || Load<void *>(candidate, kCharacterDeathDataOffset) != nullptr)
    return game::ArrangeMarriageResult::candidate_not_found;
  ContextStorage storage{};
  game::ArrangeMarriageValidationSample sample{};
  if (!PrepareContext(b, choice, storage, sample)) return game::ArrangeMarriageResult::unavailable;
  void *context = storage.bytes.data();
  if (!b.validate(context, nullptr)) {
    b.destroy(context);
    return game::ArrangeMarriageResult::choice_unavailable;
  }
  SendCommandStorage command{};
  void *native_command = command.bytes.data();
  const bool constructed = b.construct_send_command(native_command, context) == native_command;
  const bool identity = constructed && Load<std::uintptr_t>(native_command, 0) == b.send_primary_vtable &&
      Load<std::uintptr_t>(native_command, 0x18) == b.send_secondary_vtable;
  const auto result = identity ? SubmitCommandCopy(b.commands, native_command, 0x0E) :
      CommandSubmitResult::unavailable;
  // Native command owns its copied context. Clone/queue synchronously consumes
  // a separate game-owned copy; only these two caller-owned contexts are torn down.
  if (constructed || Load<void *>(native_command, 0x20) != nullptr)
    b.destroy(static_cast<std::byte *>(native_command) + 0x20);
  b.destroy(context);
  return result == CommandSubmitResult::submitted ? game::ArrangeMarriageResult::submitted :
      game::ArrangeMarriageResult::unavailable;
}

} // namespace xar::ck3_12002
