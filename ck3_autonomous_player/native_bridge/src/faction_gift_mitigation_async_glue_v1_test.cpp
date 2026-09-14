#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

constexpr std::int32_t kGiftHash = 0x12345678;
constexpr std::uintptr_t kPrimaryVtable = 0x11111111;
constexpr std::uintptr_t kSecondaryVtable = 0x22222222;
alignas(16) std::array<std::byte, 0x2B00> g_definition{};
std::array<std::byte, 32> g_database{};
std::array<char, 17> g_key_storage{
    'g', 'i', 'f', 't', '_', 'i', 'n', 't', 'e',
    'r', 'a', 'c', 't', 'i', 'o', 'n', '\0'};
int g_destroy_count = 0;
int g_submit_count = 0;
int g_hash_count = 0;
int g_lookup_count = 0;
int g_construct_count = 0;
xar::game::Snapshot g_snapshot{};
alignas(16) std::array<std::byte, 0x200> g_character{};
std::array<std::byte, 0x40> g_character_storage{};
std::array<std::byte, 203 * 0x10> g_character_slots{};
void *g_character_storage_pointer = g_character_storage.data();
std::array<std::byte, 0xB0> g_game_state{};
std::array<std::byte, 0x300> g_game_data{};
std::array<std::byte, 0xE0> g_player_entry{};
std::array<void *, 1> g_player_entries{g_player_entry.data()};
void *g_game_state_pointer = g_game_state.data();

template <typename T>
void Store(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value,
              sizeof(value));
}

void *GetDatabase() { return g_database.data(); }

std::int32_t Hash(void *database, const char *data, std::uint32_t size) {
  ++g_hash_count;
  return database == g_database.data() &&
                 std::string_view(data, size) == "gift_interaction"
             ? kGiftHash
             : 0;
}

void *Lookup(void *database, std::int32_t hash) {
  ++g_lookup_count;
  return database == g_database.data() && hash == kGiftHash
             ? g_definition.data()
             : nullptr;
}

void *Construct(void *context, void *definition, std::int32_t actor,
                std::int32_t recipient, void *, bool) {
  ++g_construct_count;
  if (definition != g_definition.data() || actor != 101 || recipient != 202)
    return nullptr;
  return context;
}

void Refresh(void *, bool) {}
void Finalize(void *) {}
bool Validate(void *, void *) { return true; }
bool Trigger(void *, const void *) { return true; }
void Costs(const void *block, const void *, std::int64_t *output) {
  if (block == g_definition.data() + 0x38) output[0] = 2'500'000;
}
void Destroy(void *) { ++g_destroy_count; }

void *ConstructCommand(void *command, const void *) {
  Store(command, 0x00, kPrimaryVtable);
  Store(command, 0x18, kSecondaryVtable);
  return command;
}

bool Submit(void *, void *, std::uint32_t flags) {
  if (flags != 0x0E) return false;
  ++g_submit_count;
  return true;
}

xar::ck3_11906::Bindings MakeBindings() {
  xar::ck3_11906::Bindings bindings{};
  bindings.enabled = true;
  bindings.command_manager = g_database.data();
  bindings.submit_command = &Submit;
  bindings.get_character_interaction_database = &GetDatabase;
  bindings.hash_stable_key = &Hash;
  bindings.lookup_character_interaction = &Lookup;
  bindings.evaluate_character_interaction_cost = &Costs;
  bindings.construct_character_interaction_context = &Construct;
  bindings.refresh_character_interaction_context = &Refresh;
  bindings.finalize_character_interaction_context = &Finalize;
  bindings.validate_character_interaction_context = &Validate;
  bindings.evaluate_character_interaction_trigger = &Trigger;
  bindings.construct_send_character_interaction_command = &ConstructCommand;
  bindings.destroy_character_interaction_context = &Destroy;
  bindings.send_character_interaction_primary_vtable = kPrimaryVtable;
  bindings.send_character_interaction_secondary_vtable = kSecondaryVtable;
  bindings.character_storage_slot = &g_character_storage_pointer;
  bindings.game_state_slot = &g_game_state_pointer;
  bindings.player_character_manager_offset = 0x100;
  return bindings;
}

bool Check(bool value, const char *message) {
  if (!value) std::cerr << message << '\n';
  return value;
}

} // namespace

namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}
} // namespace xar::ck3_11906

int main() {
  constexpr std::string_view key = "gift_interaction";
  Store(g_definition.data(), 0x18, g_key_storage.data());
  Store(g_definition.data(), 0x14, kGiftHash);
  Store(g_definition.data(), 0x28,
        static_cast<std::uint64_t>(key.size()));
  Store(g_definition.data(), 0x30, std::uint64_t{31});
  Store(g_definition.data(), 0x2580, static_cast<void *>(nullptr));
  Store(g_definition.data(), 0x2A48, std::uint8_t{1});
  Store(g_character.data(), 0x18, std::uint32_t{202});
  Store(g_character.data(), 0x1C8, static_cast<void *>(nullptr));
  Store(g_character_slots.data(), 202 * 0x10 + 0x08,
        static_cast<void *>(g_character.data()));
  Store(g_character_storage.data(), 0x20,
        static_cast<void *>(g_character_slots.data()));
  Store(g_character_storage.data(), 0x2C, std::int32_t{203});
  Store(g_game_state.data(), 0xA0, static_cast<void *>(g_game_data.data()));
  Store(g_game_data.data() + 0x100, 0x58,
        static_cast<void *>(g_player_entries.data()));
  Store(g_game_data.data() + 0x100, 0x64, std::int32_t{1});
  Store(g_player_entry.data(), 0xB0, std::uint32_t{101});

  const auto bindings = MakeBindings();
  xar::game::FactionGiftPreviewV1 preview{};
  if (!Check(xar::ck3_11906::
                 ReadFactionGiftPreviewThroughGenericInteractionV1(
                     bindings, 101, 202, preview),
             "preview failed")) {
    std::cerr << "hash=" << g_hash_count << " lookup=" << g_lookup_count
              << " construct=" << g_construct_count << '\n';
    return 1;
  }
  if (
      !Check(preview.available && preview.definition_key == key &&
                 preview.definition_stable_hash ==
                     static_cast<std::uint32_t>(kGiftHash) &&
                 preview.interaction_legal && preview.auto_accept &&
                 preview.gold_cost_raw == 2'500'000 &&
                 preview.gold_scale == 100000 &&
                 preview.opinion_delta == 0,
             "preview mismatch")) {
    return 1;
  }
  bool valid = false;
  std::string reason;
  if (!Check(xar::ck3_11906::
                 ValidateFactionGiftThroughGenericInteractionDirectV1(
                     bindings, 101, 202, key,
                     static_cast<std::uint32_t>(kGiftHash), valid, reason) &&
                 valid && reason.empty(),
             "validate failed") ||
      !Check(xar::ck3_11906::
                 SubmitFactionGiftThroughGenericInteractionDirectV1(
                     bindings, 101, 202, key,
                     static_cast<std::uint32_t>(kGiftHash)),
             "submit failed") ||
      !Check(g_submit_count == 1 && g_destroy_count == 4,
             "lifecycle mismatch")) {
    return 1;
  }

  g_snapshot.date_raw = 100;
  g_snapshot.speed = 1;
  g_snapshot.paused = true;
  g_snapshot.player_id = 1;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_id = 101;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_gold = {5'000'000, 100'000};
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::FactionGiftMitigationAsyncContextV1 query{};
  query.mailbox = &mailbox;
  query.bindings = bindings;
  query.module_base = 0x10000000;
  query.expected_snapshot = g_snapshot;
  query.targeting_rows.terminal =
      xar::bridge::FactionTargetingRowProbeTerminalV1::ready;
  query.targeting_rows.published_generation = 2;
  query.targeting_rows.required_binding = {true, 7, 11, 100, 101};
  query.targeting_rows.observed_binding =
      query.targeting_rows.required_binding;
  query.targeting_rows.faction_count = 1;
  query.targeting_rows.factions[0].faction_id = 303;
  query.targeting_rows.factions[0].target_character_id = 101;
  query.targeting_rows.factions[0].leader_present = true;
  query.targeting_rows.factions[0].leader_character_id = 202;
  query.targeting_rows.factions[0].leader_present_in_character_members = true;
  query.targeting_rows.factions[0].character_member_count = 1;
  query.targeting_rows.factions[0].character_member_ids[0] = 202;
  query.direct_landed_vassal_character_ids = {202};
  query.source_faction_id = 303;
  query.recipient_character_id = 202;
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.paused = true;
  stamp.pump_epoch = 12;
  stamp.date_raw = 100;
  if (!Check(xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1(
                 &query, stamp),
             "async executor failed") ||
      !Check(query.completion == xar::ck3_11906::
                                     FactionGiftMitigationAsyncCompletionV1::
                                         preview_ready &&
                 query.observation.available &&
                 query.observation.snapshot_revision == 11 &&
                 query.observation.native_snapshot_revision == 12 &&
                 query.observation.player_gold_raw == 5'000'000 &&
                 query.observation.recipient_alive &&
                 query.observation.recipient_is_ai &&
                 query.observation.recipient_is_direct_landed_vassal &&
                 !query.observation.source_faction_requery_complete &&
                 !query.observation.recipient_opinion_query_complete &&
                 query.observation.gift_preview.gold_cost_raw == 2'500'000 &&
                 query.failure_flags ==
                     (xar::ck3_11906::
                          faction_gift_async_failure_faction_war_receiver |
                      xar::ck3_11906::
                          faction_gift_async_failure_opinion_receiver) &&
                 !query.receipt_pending,
             "async stack mismatch")) {
    return 1;
  }

  xar::ck3_11906::FactionGiftMitigationAsyncContextV1 context{};
  context.completion = xar::ck3_11906::
      FactionGiftMitigationAsyncCompletionV1::preview_ready;
  context.failure_flags = xar::ck3_11906::
                              faction_gift_async_failure_faction_war_receiver |
                          xar::ck3_11906::
                              faction_gift_async_failure_opinion_receiver;
  context.source_faction_id = 303;
  context.recipient_character_id = 202;
  context.observation.available = true;
  context.observation.gift_preview = preview;
  const auto json = xar::ck3_11906::
      SerializeFactionGiftMitigationAsyncContextV1(context);
  if (!Check(json.find("\"completion\":\"preview_ready\"") !=
                 std::string::npos &&
                 json.find("\"gold_cost_raw\":2500000") !=
                     std::string::npos &&
                 json.find("gift_opinion_receiver_unclosed") !=
                     std::string::npos &&
                 json.find("\"receipt_pending\":false") !=
                     std::string::npos,
             "serializer mismatch")) {
    return 1;
  }
  return 0;
}
