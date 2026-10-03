#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002::family_obligations_alliance {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}
template <typename T>
void Store(void *object, std::size_t offset, const T &value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
bool Fail(std::string_view *reason, std::string_view text) noexcept {
  if (reason != nullptr) *reason = text;
  return false;
}
bool Ready(const Bindings &b) noexcept {
  const auto &c = b.context;
  return b.enabled && b.core.enabled && c.enabled && b.is_allied && b.key_hash &&
      b.lookup_definition && b.construct_context && b.can_pick_war_target &&
      b.was_called && b.final_answer && b.contains_participant && b.war_storage_slot &&
      b.war_fallback_slot && b.interaction_missing_slot &&
      c.interaction_database_slot && c.refresh && c.finalize && c.validate &&
      c.destroy && c.recipient_answer_score && c.evaluate_cost && c.evaluate_trigger;
}
void *Definition(const Bindings &b) noexcept {
  void *const database = *b.context.interaction_database_slot;
  if (database == nullptr) return nullptr;
  const auto hash = b.key_hash(database, kInteractionKey.data(),
                              static_cast<std::uint32_t>(kInteractionKey.size()));
  void *const definition = b.lookup_definition(database, static_cast<std::int32_t>(hash));
  if (definition == nullptr || definition == *b.interaction_missing_slot ||
      Load<std::uint32_t>(definition, 0x14) != hash ||
      Load<std::uint32_t>(definition, 0x38) != 0x4744624FU) return nullptr;
  const auto length = Load<std::uint64_t>(definition, 0x28);
  const auto capacity = Load<std::uint64_t>(definition, 0x30);
  if (length != kInteractionKey.size() || capacity < length) return nullptr;
  const auto key = capacity < 16 ? static_cast<const char *>(definition) + 0x18
                                : Load<const char *>(definition, 0x18);
  return key != nullptr && std::memcmp(key, kInteractionKey.data(), length) == 0
      ? definition : nullptr;
}
void *ResolveWar(const Bindings &b, std::int32_t id) noexcept {
  if (id == -1 || *b.war_storage_slot == nullptr) return nullptr;
  const auto storage = *b.war_storage_slot;
  const auto slots = Load<void *>(storage, 0x20);
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (capacity < 0 || capacity > 1'048'576 || slots == nullptr ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *const war = Load<void *>(slots, index * 0x10ULL + 8);
  return war != nullptr && war != *b.war_fallback_slot &&
      Load<std::int32_t>(war, 8) == id && Load<std::uint8_t>(war, 0x358) == 0
      ? war : nullptr;
}
bool Participants(const Bindings &b, const void *side,
                  std::vector<std::int32_t> &output) noexcept {
  output.clear();
  const auto records = Load<void *>(side, 8);
  const auto capacity = Load<std::int32_t>(side, 0x10);
  const auto count = Load<std::int32_t>(side, 0x14);
  if (count < 0 || capacity < count || capacity > 65'536 ||
      (count != 0 && records == nullptr)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto record = Load<void *>(records, static_cast<std::size_t>(index) * 8);
    if (record == nullptr) return false;
    const auto id = Load<std::int32_t>(record, 8);
    if (ResolveCoreCharacter(b.core, id) == nullptr) return false;
    if (std::find(output.begin(), output.end(), id) == output.end()) output.push_back(id);
  }
  return true;
}
Side ReadSide(const Bindings &b, const void *war, std::int32_t id) noexcept {
  const auto base = static_cast<const std::byte *>(war);
  const bool attacker = b.contains_participant(base + 0x20, id);
  const bool defender = b.contains_participant(base + 0x80, id);
  return attacker ? Side::attacker : defender ? Side::defender : Side::absent;
}
bool Terms(const Bindings &b, void *definition, WarExposure &row,
           std::string_view *reason) noexcept {
  struct alignas(8) Context { std::array<std::byte, 0x338> bytes{}; } storage;
  void *const context = storage.bytes.data();
  if (b.construct_context(context, definition, row.caller_character_id,
                          row.recipient_character_id, nullptr, true) != context)
    return Fail(reason, "call_ally_context_construction_unavailable");
  struct Cleanup {
    const ContextBindings &bindings;
    void *context;
    ~Cleanup() { bindings.destroy(context); }
  } cleanup{b.context, context};
  WarTarget target{};
  target.full_war_id = static_cast<std::uint32_t>(row.war_id);
  if (Load<std::int32_t>(context, kContextActorOffset) != row.caller_character_id ||
      Load<std::int32_t>(context, kContextRecipientOffset) != row.recipient_character_id)
    return Fail(reason, "call_ally_constructed_roles_identity_unavailable");
  // The native UI checks the requested candidate in a copied scope before
  // writing its selected WarTarget. An unpickable war has no selected terms.
  row.native_target_can_be_picked = b.can_pick_war_target(context, &target, nullptr);
  row.native_selected_target_context_available = false;
  row.native_target_row_selectable = row.native_target_can_be_picked &&
      row.recipient_side == Side::absent && !row.recipient_was_called;
  if (!row.native_target_can_be_picked) return true;
  Store(context, kContextTargetOffset, target);
  b.context.refresh(context, true);
  b.context.finalize(context);
  if (Load<std::int32_t>(context, kContextActorOffset) != row.caller_character_id)
    return Fail(reason, "call_ally_finalized_actor_identity_unavailable");
  if (Load<std::int32_t>(context, kContextRecipientOffset) != row.recipient_character_id)
    return Fail(reason, "call_ally_finalized_recipient_identity_unavailable");
  if (Load<std::uint16_t>(context, kContextTargetOffset) != kWarTargetType)
    return Fail(reason, "call_ally_finalized_target_type_unavailable");
  if (Load<std::uint64_t>(context, kContextTargetTokenOffset) != target.full_war_id)
    return Fail(reason, "call_ally_finalized_target_token_unavailable");
  if (Load<void *>(context, kContextSpecialInstanceOffset) == nullptr)
    return Fail(reason, "call_ally_finalized_special_instance_unavailable");
  row.native_selected_target_context_available = true;
  row.native_complete_can_send = b.context.validate(context, nullptr);
  b.context.evaluate_cost(static_cast<const std::byte *>(definition) + 0x40,
      static_cast<const std::byte *>(context) + 8, row.send_cost_raw.data());
  if (b.context.recipient_answer_score(context, &row.recipient_acceptance_raw) !=
      &row.recipient_acceptance_raw)
    return Fail(reason, "call_ally_native_acceptance_unavailable");
  row.recipient_answer_status_raw = b.final_answer(context, 1, 1, nullptr, nullptr);
  if (row.recipient_answer_status_raw > 2)
    return Fail(reason, "call_ally_native_final_answer_unavailable");
  void *const trigger = Load<void *>(definition, 0x2290);
  if (trigger != nullptr) {
    row.native_auto_accept = b.context.evaluate_trigger(
        trigger, static_cast<const std::byte *>(context) + 8);
  } else {
    const auto scalar = Load<std::uint8_t>(definition, 0x2718);
    if (scalar > 1) return Fail(reason, "call_ally_native_auto_accept_unavailable");
    row.native_auto_accept = scalar != 0;
  }
  return true;
}
bool Wars(const Bindings &b, void *definition, void *caller, std::int32_t caller_id,
          std::int32_t recipient_id, std::vector<WarExposure> &output,
          std::string_view *reason) noexcept {
  const auto realm = Load<void *>(caller, kCharacterRealmOffset);
  if (realm == nullptr) return true; // Native UI selects its empty fallback vector.
  const auto vector = static_cast<const std::byte *>(realm) + kRealmWarIdsOffset;
  const auto ids = Load<const std::int32_t *>(vector, 0);
  const auto capacity = Load<std::int32_t>(vector, 8);
  const auto count = Load<std::int32_t>(vector, 0xC);
  if (count < 0 || capacity < count || capacity > 65'536 || (count && ids == nullptr))
    return Fail(reason, "character_active_war_vector_unavailable");
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = ids[index];
    if (std::any_of(output.begin(), output.end(), [id](const auto &r) { return r.war_id == id; }))
      continue;
    void *const war = ResolveWar(b, id);
    if (war == nullptr) return Fail(reason, "active_war_full_id_unavailable");
    WarExposure row{};
    row.war_id = id; row.caller_character_id = caller_id; row.recipient_character_id = recipient_id;
    row.primary_attacker_character_id = Load<std::int32_t>(war, 0x288);
    row.primary_defender_character_id = Load<std::int32_t>(war, 0x28C);
    if (!Participants(b, static_cast<const std::byte *>(war) + 0x20, row.attacker_character_ids) ||
        !Participants(b, static_cast<const std::byte *>(war) + 0x80, row.defender_character_ids))
      return Fail(reason, "active_war_participant_graph_unavailable");
    row.caller_side = ReadSide(b, war, caller_id);
    row.recipient_side = ReadSide(b, war, recipient_id);
    if (row.caller_side == Side::absent)
      return Fail(reason, "caller_missing_from_active_war");
    row.caller_is_primary_war_leader = (row.caller_side == Side::attacker ?
        row.primary_attacker_character_id : row.primary_defender_character_id) == caller_id;
    row.recipient_was_called = b.was_called(war, recipient_id);
    if (!Terms(b, definition, row, reason)) return false;
    output.push_back(std::move(row));
  }
  return true;
}
bool SourceIds(const void *container, std::size_t stride,
               std::vector<std::int32_t> &ids) noexcept {
  const auto data = Load<const std::byte *>(container, 0);
  const auto capacity = Load<std::int32_t>(container, 8);
  const auto count = Load<std::int32_t>(container, 0xC);
  if (count < 0 || capacity < count || capacity > 65'536 || (count && data == nullptr))
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = Load<std::int32_t>(data, static_cast<std::size_t>(index) * stride);
    if (id != -1) ids.push_back(id);
  }
  return true;
}
} // namespace

bool ReadCurrentAllies(const Bindings &b, const CoreSnapshotPrefix &frame,
                       CurrentAlliesSnapshot &output, std::string_view *reason) noexcept {
  output = {};
  if (reason != nullptr) *reason = {};
  if (!b.enabled || !b.core.enabled || !b.is_allied)
    return Fail(reason, "current_allies_binding_unavailable");
  if (!frame.clock.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive)
    return Fail(reason, "paused_played_character_frame_required");
  void *const player = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (player == nullptr || Load<void *>(player, kCharacterDeathDataOffset) != nullptr)
    return Fail(reason, "current_allies_player_full_id_unavailable");
  CurrentAlliesSnapshot value{};
  value.played_character_id = frame.played_character_id;
  const auto family = Load<const std::byte *>(player, kCharacterFamilyOffset);
  if (family != nullptr) {
    if (!SourceIds(family + kFamilySpousesOffset, 4, value.source_character_ids))
      return Fail(reason, "current_allies_spouse_id_container_unavailable");
    const auto betrothed = Load<std::int32_t>(family, kFamilyBetrothedOffset);
    if (betrothed != -1) value.source_character_ids.push_back(betrothed);
  }
  const auto relations = Load<const std::byte *>(player, kCharacterRelationsOffset);
  if (relations != nullptr &&
      !SourceIds(relations + kRelationsRowsOffset, 16, value.source_character_ids))
    return Fail(reason, "current_allies_relation_id_container_unavailable");
  auto &ids = value.source_character_ids;
  std::sort(ids.begin(), ids.end());
  ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
  for (const auto id : ids) {
    if (id == frame.played_character_id) continue;
    void *const candidate = ResolveCoreCharacter(b.core, id);
    if (candidate == nullptr) {
      value.unresolved_source_character_ids.push_back(id);
      continue;
    }
    if (Load<void *>(candidate, kCharacterDeathDataOffset) != nullptr) {
      value.dead_source_character_ids.push_back(id);
      continue;
    }
    const bool forward = b.is_allied(player, candidate);
    const bool reverse = b.is_allied(candidate, player);
    if (forward && reverse)
      value.allies.push_back({id, forward, reverse,
                             Load<void *>(candidate, kCharacterRealmOffset) != nullptr});
  }
  output = std::move(value);
  return true;
}

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.context = BindContextImage(base, sha);
  b.construct_context = reinterpret_cast<ConstructInteractionContext>(base + kConstructInteractionContextRva);
  b.war_storage_slot = reinterpret_cast<void **>(base + kWarStorageSlotRva);
  b.war_fallback_slot = reinterpret_cast<void **>(base + kWarFallbackSlotRva);
  b.interaction_missing_slot = reinterpret_cast<void **>(base + kInteractionMissingSlotRva);
  b.is_allied = reinterpret_cast<IsAllied>(base + kIsAlliedRva);
  b.key_hash = reinterpret_cast<DefinitionKeyHash>(base + kDefinitionKeyHashRva);
  b.lookup_definition = reinterpret_cast<DefinitionLookup>(base + kDefinitionLookupRva);
  b.can_pick_war_target = reinterpret_cast<CanPickWarTarget>(base + kCanPickWarTargetRva);
  b.was_called = reinterpret_cast<WasCalled>(base + kWasCalledRva);
  b.final_answer = reinterpret_cast<FinalAnswer>(base + family_query_abi::kEvaluateAnswerRva);
  b.contains_participant = reinterpret_cast<ContainsParticipant>(base + kContainsParticipantRva);
  return b;
}

bool Read(const Bindings &b, const CoreSnapshotPrefix &frame, std::int32_t first,
          std::int32_t second, Snapshot &output, std::string_view *reason) noexcept {
  output = {};
  if (reason != nullptr) *reason = {};
  if (!Ready(b)) return Fail(reason, "alliance_war_binding_unavailable");
  if (!frame.clock.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive)
    return Fail(reason, "paused_played_character_frame_required");
  if (first == second) return Fail(reason, "distinct_alliance_pair_required");
  void *const first_character = ResolveCoreCharacter(b.core, first);
  void *const second_character = ResolveCoreCharacter(b.core, second);
  if (first_character == nullptr || second_character == nullptr ||
      Load<void *>(first_character, kCharacterDeathDataOffset) != nullptr ||
      Load<void *>(second_character, kCharacterDeathDataOffset) != nullptr)
    return Fail(reason, "alliance_pair_full_id_or_liveness_unavailable");
  void *const definition = Definition(b);
  if (definition == nullptr) return Fail(reason, "call_ally_definition_identity_unavailable");
  Snapshot value{};
  value.date_raw = frame.clock.date_raw; value.played_character_id = frame.played_character_id;
  value.first_character_id = first; value.second_character_id = second;
  value.first_has_second = b.is_allied(first_character, second_character);
  value.second_has_first = b.is_allied(second_character, first_character);
  if (!Wars(b, definition, first_character, first, second, value.first_wars, reason) ||
      !Wars(b, definition, second_character, second, first, value.second_wars, reason)) return false;
  output = std::move(value);
  return true;
}


CommandSubmitResult SubmitCallAlly(const Bindings &b, const CoreSnapshotPrefix &frame,
    const CallAllySubmitRequest &request, CallAllySubmitReceipt &receipt,
    std::string_view *reason) noexcept {
  receipt = {};
  if (reason != nullptr) *reason = {};
  const auto reject = [reason](std::string_view why) {
    if (reason != nullptr) *reason = why;
    return CommandSubmitResult::rejected;
  };
  if (!Ready(b) || !b.context.construct_send_command || !b.context.commands.enabled ||
      !b.context.send_primary_vtable || !b.context.send_secondary_vtable) {
    if (reason != nullptr) *reason = "call_ally_send_binding_unavailable";
    return CommandSubmitResult::unavailable;
  }
  const auto same_frame = [&frame](const CoreSnapshotPrefix &now) {
    return now.clock.paused && now.map_ready && now.has_played_character &&
        now.played_character_alive && frame.clock.paused && frame.map_ready &&
        frame.has_played_character && frame.played_character_alive &&
        now.clock.date_raw == frame.clock.date_raw && now.clock.speed == frame.clock.speed &&
        now.local_player_id == frame.local_player_id &&
        now.played_character_id == frame.played_character_id;
  };
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(b.core, current) || !same_frame(current))
    return reject("call_ally_current_player_frame_mismatch");
  if (request.recipient_character_id == -1 || request.war_id == -1 ||
      request.recipient_character_id == frame.played_character_id)
    return reject("call_ally_concrete_recipient_and_war_required");
  void *const recipient = ResolveCoreCharacter(b.core, request.recipient_character_id);
  void *const war = ResolveWar(b, request.war_id);
  void *const definition = Definition(b);
  if (!recipient || Load<void *>(recipient, kCharacterDeathDataOffset) || !war || !definition)
    return reject("call_ally_current_identity_unavailable");
  const auto side = ReadSide(b, war, frame.played_character_id);
  const auto primary = side == Side::attacker ? Load<std::int32_t>(war, 0x288) :
      side == Side::defender ? Load<std::int32_t>(war, 0x28C) : -1;
  if (primary != frame.played_character_id || ReadSide(b, war, request.recipient_character_id) != Side::absent ||
      b.was_called(war, request.recipient_character_id))
    return reject("call_ally_selected_war_or_recipient_not_selectable");
  struct alignas(8) Storage { std::array<std::byte, 0x338> bytes{}; } source;
  void *const context = source.bytes.data();
  if (b.construct_context(context, definition, frame.played_character_id,
                          request.recipient_character_id, nullptr, true) != context) {
    if (reason != nullptr) *reason = "call_ally_context_construction_unavailable";
    return CommandSubmitResult::unavailable;
  }
  struct Cleanup {
    const ContextBindings &b; void *context;
    ~Cleanup() { b.destroy(context); }
  } cleanup{b.context, context};
  WarTarget target{}; target.full_war_id = static_cast<std::uint32_t>(request.war_id);
  if (Load<std::int32_t>(context, kContextActorOffset) != frame.played_character_id ||
      Load<std::int32_t>(context, kContextRecipientOffset) != request.recipient_character_id)
    return reject("call_ally_constructed_roles_identity_unavailable");
  if (!b.can_pick_war_target(context, &target, nullptr))
    return reject("call_ally_selected_war_target_not_pickable");
  Store(context, kContextTargetOffset, target);
  b.context.refresh(context, true); b.context.finalize(context);
  const auto same_context = [&](const void *copy) {
    return Load<void *>(copy, 0) == definition &&
        Load<std::int32_t>(copy, kContextActorOffset) == frame.played_character_id &&
        Load<std::int32_t>(copy, kContextRecipientOffset) == request.recipient_character_id &&
        Load<std::uint16_t>(copy, kContextTargetOffset) == kWarTargetType &&
        Load<std::uint64_t>(copy, kContextTargetTokenOffset) == target.full_war_id &&
        Load<void *>(copy, kContextSpecialInstanceOffset) != nullptr;
  };
  if (!same_context(context) || !b.context.validate(context, nullptr))
    return reject("call_ally_final_native_selected_target_rejected");
  receipt.selected_target_native_legal = true;
  b.context.evaluate_cost(static_cast<const std::byte *>(definition) + 0x40,
      static_cast<const std::byte *>(context) + 8, receipt.actual_send_cost_raw.data());
  receipt.send_cost_sampled = true;
  if (receipt.actual_send_cost_raw != request.expected_send_cost_raw)
    return reject("call_ally_observed_send_cost_changed");
  if (!ReadCoreSnapshot(b.core, current) || !same_frame(current))
    return reject("call_ally_current_player_frame_changed");
  struct alignas(8) Command { std::array<std::byte, 0x368> bytes{}; } command;
  void *const native_command = command.bytes.data();
  const bool constructed = b.context.construct_send_command(native_command, context) == native_command;
  const void *const copy = static_cast<const std::byte *>(native_command) + 0x20;
  bool identity = constructed && Load<std::uintptr_t>(native_command, 0) == b.context.send_primary_vtable &&
      Load<std::uintptr_t>(native_command, 0x18) == b.context.send_secondary_vtable && same_context(copy);
  for (const auto offset : {0x2E0U, 0x2E4U, 0x2E8U, 0x2ECU})
    identity = identity && Load<std::int32_t>(copy, offset) == Load<std::int32_t>(context, offset);
  receipt.copied_context_identity_verified = identity;
  const auto result = identity ? SubmitCommandCopy(b.context.commands, native_command, 0x0E) :
      CommandSubmitResult::unavailable;
  if (constructed || Load<void *>(native_command, 0x20) != nullptr)
    b.context.destroy(static_cast<std::byte *>(native_command) + 0x20);
  if (!identity && reason != nullptr) *reason = "call_ally_copied_context_identity_unavailable";
  return result;
}

} // namespace xar::ck3_12002::family_obligations_alliance
