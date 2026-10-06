#include "xar_bridge/ck3_12004_prisoner.hpp"
#include "xar_bridge/ck3_12004_prisoner_mailbox.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom_action.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

// Fixture-owned native objects/callbacks exercise the new actual4 provider.
// The software2 ownership scaffold is reused; no historical image binder or
// native callback is invoked. This executable does not run application-main
// mailbox routing or prove a real custody/payment effect.
namespace {
namespace native = xar::ck3_12004;
namespace bridge = xar::bridge;
namespace ownership = xar::ck3_12002;
constexpr std::int32_t kJailer = 29829, kPrisoner = 61540, kPayer = 73000;
constexpr std::int32_t kDate = 53286360, kHash = 0x12345678;
constexpr std::uint64_t kNativeRevision = 1014, kProofEpoch = 1926335;
constexpr std::int64_t kQuotedGold = 12000000, kPreGold = 5000000;
constexpr std::int64_t kNamedGold = 9000000;
constexpr std::string_view kNamedCostKey = "normal_ransom_cost_value";
constexpr std::uint32_t kNamedCostHash = 0x51520125;
constexpr std::array<std::string_view, 9> kFlags{
    "extortionate_gold", "extortionate_current_gold", "gold",
    "current_gold", "favor", "influence_send_option", "herd_send_option",
    "current_herd", "invalid"};
using Options = std::array<std::uint8_t, 9>;
using Command = std::array<std::byte, 0x368>;
using SubmitResult = native::PlayerPrisonerRansomSubmitV1;
unsigned checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) { std::cerr << "FIRST actual4 action RED " << message << '\n'; std::exit(1); }
}
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset, sizeof(result));
  return result;
}
struct Fixture;
Fixture *fixture = nullptr;
void *LocalPlayer(void *);
void *Database();
std::int32_t StableHash(void *, const char *, std::uint32_t);
void *Lookup(void *, std::int32_t);
void Redirect(void *, std::int32_t *, std::int32_t *, std::int32_t *,
              std::int32_t *, std::int32_t *, std::int32_t *);
void *Construct(void *, void *, std::int32_t, std::int32_t, std::int32_t,
                std::int32_t, std::int32_t, void *);
void Clear(void *);
void Select(void *, std::int32_t);
bool Validate(void *, void *);
std::int64_t *Score(void *, std::int64_t *);
std::uint8_t Answer(void *, std::uint8_t, std::uint8_t, void *, void *);
void DestroyContext(void *);
void *IdentifierTable();
std::int32_t *Identifier(void *, std::int32_t *, const void *);
void *Send(void *, const void *);
void **Clone(const void *, void **);
void *Delete(void *, std::uint32_t);
bool Queue(void *, void **, std::uint32_t);
bool Capture(void *, bridge::PlayerPrisonerFrameV1 &) noexcept;
bool ReadMemory(void *, std::uintptr_t, void *, std::size_t) noexcept;
void *PrimaryTitle(void *);
const void *LookupNamed(void *, std::uint32_t);
void *CloneNamedScope(void *, const void *);
void *Support118(void *);
void *Support2a8(void *);
const void *InternNamed(void *, const void *);
std::int64_t *EvaluateNamed(const void *, std::int64_t *, void *, void *, const void *);
void DestroyNamedTail(void *);
void EmptyNamedRows(void *);

struct Fixture {
  std::vector<std::byte> image = std::vector<std::byte>(0x5D1E000);
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local_player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::vector<std::byte> slots = std::vector<std::byte>(100000 * 0x10);
  std::array<std::array<std::byte, 0x1D8>, 3> characters{};
  std::array<std::byte, 0x110> player_extension{}, payer_extension{};
  std::array<std::byte, 0x290> prisoner_extension{};
  std::array<std::byte, 8> prison_relation{};
  std::array<std::byte, 0x358> player_land{};
  std::array<std::uint32_t, 1> prisoner_ids{static_cast<std::uint32_t>(kPrisoner)};
  std::array<std::byte, 0x30> house_store{}, dynasty_store{};
  std::array<std::byte, 64 * 0x10> house_slots{}, dynasty_slots{};
  std::array<std::array<std::byte, 0x30>, 2> houses{};
  std::array<std::array<std::byte, 0x18>, 2> dynasties{};
  std::array<std::byte, 0x2268> definition{};
  std::array<std::byte, 9 * 0x730> option_rows{};
  std::array<std::byte, 0xA0> named_definition{};
  native::PrisonerRansomActionBindings12004 bindings{};
  std::unordered_map<void *, Options *> contexts;
  std::vector<std::pair<std::uintptr_t, std::size_t>> readable;
  std::vector<std::string_view> verified_flags;
  std::uint64_t revision = kNativeRevision;
  bool queue_accepts = true;
  bool selected_gold = false;
  unsigned constructs = 0, destroys = 0, send_copies = 0, clones = 0;
  unsigned queues = 0, deletes = 0, gates = 0, frame_captures = 0;
  unsigned named_clones = 0, named_evaluations = 0, named_destroyed = 0;
  std::uint8_t evaluation_flag = 1;
  void *named_scope = nullptr, *named_owner = nullptr;
  void *queued = nullptr;

  std::uintptr_t Module() const { return reinterpret_cast<std::uintptr_t>(image.data()); }
  template <typename T> void Register(T &region) {
    readable.emplace_back(reinterpret_cast<std::uintptr_t>(region.data()), region.size());
  }
  void SetHeld(bool held) {
    Put(player_land.data(), 0xD8, prisoner_ids.data());
    Put(player_land.data(), 0xE4, std::int32_t{held ? 1 : 0});
  }
  void PayerGold(std::int64_t raw) { Put(payer_extension.data(), 0x100, raw); }
  void PlayerGold(std::int64_t raw) { Put(player_extension.data(), 0x100, raw); }
  void CopyContext(void *destination, const void *source) {
    const auto found = contexts.find(const_cast<void *>(source));
    Check(found != contexts.end(), "copy retains a live source context");
    std::memcpy(destination, source, 0x338);
    auto *options = new Options(*found->second);
    Check(contexts.emplace(destination, options).second, "deep copied option owner is unique");
    Put(destination, 0x300, options->data());
  }
  explicit Fixture(bool gold) : selected_gold(gold) {
    fixture = this;
    Put(state.data(), native::kGameStateDateOffset, kDate);
    Put(state.data(), native::kGameStateSpeedOffset, std::int32_t{2});
    Put(state.data(), native::kGameStateDataOffset, data.data());
    Put(jomini.data(), native::kJominiPlayersOffset, players.data());
    Put(jomini.data(), native::kJominiPausedOffset, std::uint8_t{1});
    Put(players.data(), native::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(local_player.data(), native::kPlayerIdOffset, std::int32_t{7});
    Put(data.data(), native::kPlayerCharacterManagerOffset + native::kPlayerManagerEntriesOffset, entries.data());
    Put(data.data(), native::kPlayerCharacterManagerOffset + native::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry.data(), native::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry.data(), native::kPlayerEntryCharacterIdOffset, kJailer);
    Put(store.data(), native::kCharacterStorageSlotsOffset, slots.data());
    Put(store.data(), native::kCharacterStorageCapacityOffset, std::int32_t{100000});
    const std::array ids{kJailer, kPrisoner, kPayer};
    for (std::size_t i = 0; i < ids.size(); ++i) {
      Put(characters[i].data(), native::kCharacterFullIdOffset, ids[i]);
      Put(slots.data(), static_cast<std::size_t>(ids[i]) * native::kCharacterStorageSlotStride +
          native::kCharacterStorageObjectOffset, characters[i].data());
      Register(characters[i]);
    }
    Put(image.data(), native::kGameStateSlotRva, state.data());
    Put(image.data(), native::kJominiStateSlotRva, jomini.data());
    Put(image.data(), native::kCharacterStorageSlotRva, store.data());
    Put(image.data(), native::kCharacterStorageSlotRva + 8, static_cast<void *>(nullptr));
    Put(characters[0].data(), 0x1B0, player_extension.data());
    Put(characters[0].data(), 0x1C0, player_land.data());
    Put(characters[1].data(), 0x1B0, prisoner_extension.data());
    Put(prisoner_extension.data(), 0x288, prison_relation.data());
    Put(prison_relation.data(), 0, kJailer);
    Put(characters[2].data(), 0x1B0, payer_extension.data());
    Put(characters[0].data(), 0x158, std::int32_t{11});
    Put(characters[1].data(), 0x158, std::int32_t{12});
    Put(characters[2].data(), 0x158, std::int32_t{-1});
    Put(player_land.data(), 0x350, std::int64_t{1680000});
    Put(image.data(), std::size_t{0x5D1DAF0}, house_store.data());
    Put(image.data(), std::size_t{0x5D1DAE8}, static_cast<void *>(nullptr));
    Put(image.data(), std::size_t{0x5D1DE78}, dynasty_store.data());
    Put(image.data(), std::size_t{0x5D1DE28}, static_cast<void *>(nullptr));
    Put(image.data(), native::kPrisonerTitleFallbackSlotRva12004, static_cast<void *>(nullptr));
    Put(house_store.data(), 0x20, house_slots.data()); Put(house_store.data(), 0x2C, std::int32_t{64});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data()); Put(dynasty_store.data(), 0x2C, std::int32_t{64});
    for (std::size_t i = 0; i < houses.size(); ++i) {
      const auto house = static_cast<std::int32_t>(11 + i);
      const auto dynasty = static_cast<std::int32_t>(22 + i);
      Put(houses[i].data(), 0x10, house); Put(houses[i].data(), 0x2C, dynasty);
      Put(dynasties[i].data(), 0x10, dynasty);
      Put(house_slots.data(), static_cast<std::size_t>(house) * 0x10 + 8, houses[i].data());
      Put(dynasty_slots.data(), static_cast<std::size_t>(dynasty) * 0x10 + 8, dynasties[i].data());
      Register(houses[i]); Register(dynasties[i]);
    }
    SetHeld(true); PayerGold(kQuotedGold); PlayerGold(kPreGold);
    constexpr std::string_view key = "ransom_interaction";
    Put(definition.data(), 0x14, kHash); Put(definition.data(), 0x18, key.data());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x2258, option_rows.data()); Put(definition.data(), 0x2264, std::int32_t{9});
    for (std::size_t i = 0; i < kFlags.size(); ++i)
      Put(option_rows.data(), i * 0x730 + 0x368, static_cast<std::int32_t>(100 + i));
    bindings = native::BindPrisonerRansomActionImage12004(Module(), native::kExecutableSha256);
    Check(bindings.enabled && bindings.quote.enabled && bindings.commands.enabled,
          "actual4 production action binder admits mapped native dependencies");
    Check(bindings.module_base == Module() && bindings.quote.module_base == Module() &&
          reinterpret_cast<std::uintptr_t>(bindings.construct_send_character_interaction_command) == Module() + native::kPrisonerRansomSendConstructorRva12004 &&
          bindings.send_character_interaction_primary_vtable == Module() + native::kPrisonerRansomSendPrimaryVtableRva12004 &&
          bindings.send_character_interaction_secondary_vtable == Module() + native::kPrisonerRansomSendSecondaryVtableRva12004,
          "actual4 mapped constructor and command vptr identities");
    Check(bindings.quote.named.enabled &&
          reinterpret_cast<std::uintptr_t>(bindings.quote.named.evaluate_fixed) == Module() + native::kPrisonerNamedFixedRva12004,
          "actual4 named fixed reader retains its admitted native entry");
    Put(named_definition.data(), 0, Module() + native::kPrisonerNamedPrimaryVtableRva12004);
    Put(named_definition.data(), 0x88, Module() + native::kPrisonerNamedSecondaryVtableRva12004);
    Put(named_definition.data(), 0x14, kNamedCostHash); Put(named_definition.data(), 0x18, kNamedCostKey.data());
    Put(named_definition.data(), 0x28, static_cast<std::uint64_t>(kNamedCostKey.size()));
    Put(named_definition.data(), 0x30, std::uint64_t{64}); Put(named_definition.data(), 0x38, std::uint32_t{0x4744624F});
    // Leave enabled and mapped vptr identities exactly as the actual4 binder
    // returned them. Only borrowed function pointers/managers are substituted.
    auto &interaction = bindings.quote.interaction;
    interaction.context.core.get_local_player = &LocalPlayer;
    interaction.get_database = &Database; interaction.stable_hash = &StableHash;
    interaction.lookup_definition = &Lookup; interaction.context.redirect_roles = &Redirect;
    interaction.context.construct_all_roles = &Construct; interaction.context.validate = &Validate;
    interaction.read_character_interaction_answer_score = &Score; interaction.evaluate_answer = &Answer;
    interaction.context.destroy = &DestroyContext; interaction.clear_local_options = &Clear;
    interaction.select_local_option = &Select; interaction.get_script_identifier_table = &IdentifierTable;
    interaction.lookup_script_identifier_id = &Identifier;
    auto &named = bindings.quote.named;
    named.core.get_local_player = &LocalPlayer; named.named_database = &Database; named.lookup_named = &LookupNamed;
    named.clone_scope = &CloneNamedScope; named.construct_support_118 = &Support118;
    named.construct_support_2a8 = &Support2a8; named.intern_database = &Database; named.intern_string = &InternNamed;
    named.evaluate_fixed = &EvaluateNamed; named.destroy_scope_tail = &DestroyNamedTail;
    named.destroy_scope_rows = &EmptyNamedRows; named.destroy_support_rows = &EmptyNamedRows;
    named.evaluation_flag = &evaluation_flag;
    bindings.commands.command_manager = this; bindings.commands.queue_owned_command = &Queue;
    bindings.construct_send_character_interaction_command = &Send;
    Put(image.data(), native::kPrisonerRansomSendPrimaryVtableRva12004, &Delete);
    Put(image.data(), native::kPrisonerRansomSendPrimaryVtableRva12004 + 0x40, &Clone);
    Register(image); Register(store); Register(slots); Register(player_extension); Register(payer_extension);
    Register(prisoner_extension); Register(prison_relation); Register(player_land);
    readable.emplace_back(reinterpret_cast<std::uintptr_t>(prisoner_ids.data()), sizeof(prisoner_ids));
    Register(house_store); Register(dynasty_store); Register(house_slots); Register(dynasty_slots);
  }
  bridge::PlayerPrisonerCollectionAccessV1 Access() {
    bridge::PlayerPrisonerCollectionAccessV1 access{};
    access.exact_build_admitted = bindings.enabled;
    access.admitted_executable_sha256 = native::kExecutableSha256;
    access.module_base = Module(); access.current_thread_id = 77; access.application_main_thread_id = 77;
    access.read_lineage = true; access.read_child_relation = true; access.read_title_tier = true; access.read_dread = true;
    access.context = this; access.capture_frame = &Capture; access.read_memory = &ReadMemory;
    access.get_primary_title = &PrimaryTitle;
    return access;
  }
  native::PlayerPrisonerRansomQuoteV1 Quote() {
    auto result = native::ReadPlayerPrisonerRansomQuotePrivateV1(bindings.quote, Module(), kJailer, kPrisoner);
    Check(contexts.empty() && named_scope == nullptr && named_owner == nullptr,
          "quote releases temporary gold/current_gold contexts and named scratch");
    Check(result.available && result.failure == native::PlayerPrisonerRansomQuoteFailureV1::none &&
          result.jailer_character_id == kJailer && result.payer_character_id == kPayer &&
          result.prisoner_character_id == kPrisoner && result.selected_option == (selected_gold ? "gold" : "current_gold") &&
          result.quoted_gold_raw == (selected_gold ? kNamedGold : kQuotedGold) &&
          result.amount_is_acceptance_time_quote == !selected_gold &&
          result.recipient_acceptance_raw == 3300000 && result.recipient_answer_status_raw == 1 && result.would_accept_now,
          "actual4 selected ordinary gold/current_gold role/amount/native score/answer input");
    return result;
  }
  void ReleaseQueued() {
    Check(queued != nullptr && contexts.size() == 1, "queue owns one independent clone");
    const auto context = static_cast<const std::byte *>(queued) + 0x20;
    Check(Get<void *>(context, 0) == definition.data() && Get<std::int32_t>(context, 0x2D8) == kJailer &&
          Get<std::int32_t>(context, 0x2DC) == kPayer && Get<std::int32_t>(context, 0x2E4) == kPrisoner &&
          Get<std::uint8_t>(Get<void *>(context, 0x300), selected_gold ? 2U : 3U) == 1,
          "queued clone retains final roles and ordinary mask after source destruction");
    Check(ownership::DestroyOwnedCommand(queued) && queued == nullptr, "shared production owner destroys retained actual4 command");
  }
};

void *LocalPlayer(void *jomini) {
  Check(jomini == fixture->jomini.data(), "actual4 core reads fixture-owned jomini");
  return fixture->local_player.data();
}
void *Database() { return fixture; }
std::int32_t StableHash(void *database, const char *key, std::uint32_t size) {
  if (std::string_view(key, size) == kNamedCostKey) {
    Check(database == nullptr, "normal ransom named key uses its native stable hash scope");
    return static_cast<std::int32_t>(kNamedCostHash);
  }
  Check(database == fixture && std::string_view(key, size) == "ransom_interaction", "canonical stock action definition hash");
  return kHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Check(database == fixture && hash == kHash, "canonical stock action definition lookup");
  return fixture->definition.data();
}
void Redirect(void *definition, std::int32_t *actor, std::int32_t *recipient,
              std::int32_t *sa, std::int32_t *sr, std::int32_t *intermediary, std::int32_t *added) {
  Check(definition == fixture->definition.data() && *actor == kJailer && *recipient == kPrisoner &&
        *sa == -1 && *sr == -1 && *intermediary == -1 && *added == -1, "all actual4 redirect role arguments");
  *recipient = kPayer; *sr = kPrisoner;
}
void *Construct(void *context, void *definition, std::int32_t actor, std::int32_t recipient,
                std::int32_t sa, std::int32_t sr, std::int32_t intermediary, void *extra) {
  Check(definition == fixture->definition.data() && actor == kJailer && recipient == kPayer &&
        sa == -1 && sr == kPrisoner && intermediary == -1 && extra == nullptr, "actual4 finalized ransom roles");
  auto *options = new Options{};
  Check(fixture->contexts.emplace(context, options).second, "fresh options ownership");
  Put(context, 0, definition); Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, sa); Put(context, 0x2E4, sr); Put(context, 0x2E8, intermediary);
  Put(context, 0x300, options->data()); Put(context, 0x308, std::int32_t{9}); Put(context, 0x30C, std::int32_t{9});
  ++fixture->constructs; return context;
}
void Clear(void *context) { fixture->contexts.at(context)->fill(0); }
void Select(void *context, std::int32_t index) {
  Check(index == 2 || index == 3, "only ordinary gold/current_gold is requested");
  const auto selected = fixture->selected_gold ? 2 : 3;
  if (index == selected) (*fixture->contexts.at(context))[static_cast<std::size_t>(selected)] = 1;
}
bool Validate(void *context, void *error) {
  Check(error == nullptr && fixture->contexts.count(context) == 1, "native final CanSend owns its context");
  const auto &mask = *fixture->contexts.at(context);
  const std::size_t selected = fixture->selected_gold ? 2U : 3U;
  for (std::size_t i = 0; i < mask.size(); ++i)
    Check(mask[i] == (i == selected ? 1 : 0), "final context has exactly the retained ordinary gold/current_gold option");
  ++fixture->gates; return true;
}
std::int64_t *Score(void *context, std::int64_t *output) {
  Check(fixture->contexts.count(context) == 1, "native acceptance score context");
  *output = 3300000; return output;
}
std::uint8_t Answer(void *context, std::uint8_t mode, std::uint8_t flag, void *first, void *second) {
  Check(fixture->contexts.count(context) == 1 && mode == 1 && flag == 1 &&
        first == nullptr && second == nullptr, "actual4 native answer ABI");
  return 1;
}
void DestroyContext(void *context) {
  Check(fixture->named_scope == nullptr && fixture->named_owner == nullptr,
        "owning interaction outlives its named scratch evaluation");
  const auto found = fixture->contexts.find(context);
  Check(found != fixture->contexts.end(), "each owned context is destroyed exactly once");
  delete found->second; fixture->contexts.erase(found);
  Put(context, 0, static_cast<void *>(nullptr)); Put(context, 0x300, static_cast<void *>(nullptr));
  ++fixture->destroys;
}
void *IdentifierTable() { return fixture; }
std::int32_t *Identifier(void *table, std::int32_t *output, const void *view) {
  Check(table == fixture && Get<std::uint8_t>(view, 0xC) == 0, "borrowed loaded script-ID table view");
  const auto size = Get<std::int32_t>(view, 8);
  Check(size >= 0, "loaded option flag length");
  const auto key = std::string_view(Get<const char *>(view, 0), static_cast<std::size_t>(size));
  for (std::size_t i = 0; i < kFlags.size(); ++i) if (key == kFlags[i]) {
    fixture->verified_flags.push_back(kFlags[i]); *output = static_cast<std::int32_t>(100 + i); return output;
  }
  Check(false, "all nine loaded stock option identities are present"); return nullptr;
}
void *Send(void *command, const void *context) {
  Put(command, 0, fixture->bindings.send_character_interaction_primary_vtable);
  Put(command, 0x18, fixture->bindings.send_character_interaction_secondary_vtable);
  fixture->CopyContext(static_cast<std::byte *>(command) + 0x20, context);
  ++fixture->send_copies; return command;
}
void **Clone(const void *source, void **output) {
  auto *copy = new Command{}; std::memcpy(copy->data(), source, copy->size());
  fixture->CopyContext(copy->data() + 0x20, static_cast<const std::byte *>(source) + 0x20);
  ++fixture->clones; *output = copy; return output;
}
void *Delete(void *command, std::uint32_t flags) {
  Check(flags == 1, "native scalar deleting destructor ownership flag");
  DestroyContext(static_cast<std::byte *>(command) + 0x20); delete static_cast<Command *>(command);
  ++fixture->deletes; return nullptr;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Check(manager == fixture && flags == 0x0E && owned != nullptr && *owned != nullptr,
        "actual4 queue channel and unique owned command");
  Check(fixture->queued == nullptr, "only one queued native command");
  auto *command = *owned; *owned = nullptr; ++fixture->queues;
  if (fixture->queue_accepts) fixture->queued = command;
  else Delete(command, 1); // Native queue consumes ownership also on rejection.
  return fixture->queue_accepts;
}
bool Capture(void *opaque, bridge::PlayerPrisonerFrameV1 &output) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  native::CoreSnapshotPrefix core{};
  if (!native::ReadCoreSnapshot(f.bindings.quote.interaction.context.core, core)) return false;
  const bool round_trip = core.has_played_character &&
      native::ResolveCoreCharacter(f.bindings.quote.interaction.context.core, core.played_character_id) == f.characters[0].data();
  output = {f.revision, f.revision, kProofEpoch + f.revision - kNativeRevision,
            core.clock.date_raw, core.clock.paused, core.map_ready,
            core.played_character_id, core.played_character_alive, round_trip};
  ++f.frame_captures; return true;
}
bool ReadMemory(void *opaque, std::uintptr_t address, void *output, std::size_t size) noexcept {
  const auto &f = *static_cast<Fixture *>(opaque);
  for (const auto &[start, length] : f.readable) {
    if (address >= start && address - start <= length && size <= length - (address - start)) {
      std::memcpy(output, reinterpret_cast<const void *>(address), size); return true;
    }
  }
  return false;
}
void *PrimaryTitle(void *character) {
  Check(character == fixture->characters[1].data(), "collection title callback receives its current prisoner");
  return nullptr;
}
const void *LookupNamed(void *database, std::uint32_t hash) {
  Check(database == fixture && hash == kNamedCostHash, "canonical ordinary named-cost lookup");
  return fixture->named_definition.data();
}
void *CloneNamedScope(void *destination, const void *source) {
  auto *owner = const_cast<std::byte *>(static_cast<const std::byte *>(source) - 8);
  Check(fixture->named_scope == nullptr && fixture->contexts.count(owner) == 1 &&
        Get<void *>(owner, 0) == fixture->definition.data() && (*fixture->contexts.at(owner))[2] == 1,
        "actual4 gold named read borrows the finalized selected interaction scope");
  std::memcpy(destination, source, 0x168); fixture->named_scope = destination; fixture->named_owner = owner;
  ++fixture->named_clones; return destination;
}
void *Support118(void *support) { std::memset(support, 0, 0x128); return support; }
void *Support2a8(void *support) { std::memset(support, 0, 0x2A8); return support; }
const void *InternNamed(void *database, const void *view) {
  Check(database == fixture &&
        std::string_view(Get<const char *>(view, 0), Get<std::uint32_t>(view, 8)) == kNamedCostKey,
        "actual4 normal_ransom_cost_value InternString source");
  return kNamedCostKey.data();
}
std::int64_t *EvaluateNamed(const void *definition, std::int64_t *output,
                          void *internal, void *secondary, const void *source) {
  Check(definition == fixture->named_definition.data() && secondary == nullptr &&
        Get<void *>(internal, 0) == fixture->named_scope && Get<void *>(internal, 8) == fixture->named_scope &&
        Get<void *>(internal, 0x10) == fixture->named_scope &&
        Get<std::uint8_t>(internal, 0x20) == fixture->evaluation_flag &&
        Get<std::uint16_t>(fixture->named_scope, 0) == 4 &&
        Get<std::uint64_t>(fixture->named_scope, 8) == static_cast<std::uint64_t>(kPrisoner) &&
        Get<const void *>(source, 0) == kNamedCostKey.data() && Get<std::uint8_t>(source, 0x14) == 1 &&
        Get<std::int32_t>(source, 0x18) == -1, "actual4 named fixed prisoner root/internal/source ABI");
  Check(Get<std::int32_t>(fixture->named_owner, 0x2D8) == kJailer &&
        Get<std::int32_t>(fixture->named_owner, 0x2DC) == kPayer &&
        Get<std::int32_t>(fixture->named_owner, 0x2E4) == kPrisoner,
        "gold fixed evaluation retains actual redirected payer and prisoner");
  *output = kNamedGold; ++fixture->named_evaluations; return output;
}
void DestroyNamedTail(void *tail) {
  Check(fixture->named_scope != nullptr && tail == static_cast<std::byte *>(fixture->named_scope) + 0x118,
        "actual4 named scratch tail ownership");
  fixture->named_scope = nullptr; fixture->named_owner = nullptr; ++fixture->named_destroyed;
}
void EmptyNamedRows(void *) { Check(false, "fixture named scratch vectors remain empty"); }
std::string SnapshotWire(Fixture &f) {
  native::CoreSnapshotPrefix core{};
  Check(native::ReadCoreSnapshot(f.bindings.quote.interaction.context.core, core) &&
        core.clock.paused && core.map_ready && core.has_played_character && core.played_character_alive &&
        core.played_character_id == kJailer &&
        native::ResolveCoreCharacter(f.bindings.quote.interaction.context.core, kJailer) == f.characters[0].data(),
        "snapshot packet core fields come from actual4 decoder");
  const auto gold = Get<std::int64_t>(f.player_extension.data(), 0x100);
  return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:" +
      std::to_string(f.revision) + "\",\"revision\":" + std::to_string(f.revision) +
      ",\"state\":{\"phase\":\"map_hud\",\"date\":\"synthetic:ransom-action12004\",\"date_raw\":" +
      std::to_string(core.clock.date_raw) + ",\"speed\":1,\"paused\":true,\"map_ready\":true,"
      "\"history\":[],\"active_event\":null,\"pending_character_interaction\":null,"
      "\"played_character\":{\"character_id\":29829,\"alive\":true},\"played_character_gold\":{\"raw\":" +
      std::to_string(gold) + ",\"scale\":100000},\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[]}}";
}
std::string CollectionWire(Fixture &f, const native::PlayerPrisonerRansomQuoteV1 *quote,
                           std::uint64_t sequence, bool held) {
  bridge::PlayerPrisonerCollectionSnapshotV1 snapshot{};
  Check(native::ReadPlayerPrisonerCollectionV1(f.Access(), snapshot) && snapshot.available &&
        snapshot.collection_complete && snapshot.returned_count == (held ? 1U : 0U) &&
        snapshot.total_count == snapshot.returned_count && snapshot.played_house_id == 11 &&
        snapshot.played_dynasty_id == 22 && snapshot.played_dread_raw == 1680000,
        "actual4 complete independently sampled prisoner collection");
  if (held) Check(snapshot.rows[0].full_character_id == static_cast<std::uint32_t>(kPrisoner) &&
        snapshot.rows[0].jailer_character_id == static_cast<std::uint32_t>(kJailer) &&
        snapshot.rows[0].house_id == 12 && snapshot.rows[0].dynasty_id == 23 &&
        !snapshot.rows[0].child_of_played_character && snapshot.rows[0].primary_title_tier_raw == -1,
        "collection input retains current custody and independent lineage");
  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  if (quote != nullptr) quotes[0] = *quote;
  const auto value = native::SerializePlayerPrisonerCollectionPrivateV1(snapshot, f.revision, quotes, true);
  Check(!value.empty() && value.find("\"schema_version\":6") != std::string::npos,
        "current collection uses production base schema6 serializer");
  return "{\"step\":\"query-player-prisoner-collection-private-v1\",\"accepted\":true,\"status\":\"available\","
      "\"query_sequence\":" + std::to_string(sequence) + ",\"observation_revision\":" +
      std::to_string(snapshot.frame.proof_epoch) + ",\"snapshot_revision\":" + std::to_string(f.revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\"}";
}
void CheckBinders() {
  constexpr std::uintptr_t probe = 0x10000000;
  constexpr std::string_view old_sha = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
  const auto admitted = native::BindPrisonerRansomActionImage12004(probe, native::kExecutableSha256);
  Check(admitted.enabled && admitted.quote.enabled && admitted.commands.enabled &&
        admitted.commands.command_manager != nullptr && admitted.commands.queue_owned_command != nullptr,
        "actual4 action binding requires admitted quote and command providers");
  Check(!native::BindPrisonerRansomActionImage12004(probe, old_sha).enabled &&
        !native::BindPrisonerRansomActionImage12004(0, native::kExecutableSha256).enabled,
        "historical SHA and null module do not admit actual4 action");
}
enum class Case { queued_pending, queued_applied, queued_ambiguous, quote_changed, queue_failure };
void RunCase(Case kind, std::string_view name, const std::filesystem::path &directory) {
  Fixture f(kind == Case::queued_pending);
  const unsigned before_checks = checks;
  const auto quote = f.Quote();
  const auto before_snapshot = SnapshotWire(f);
  const auto before_collection = CollectionWire(f, &quote, 1, true);
  if (kind == Case::quote_changed) f.PayerGold(kQuotedGold - 100000);
  if (kind == Case::queue_failure) f.queue_accepts = false;
  const auto result = native::SubmitPlayerPrisonerRansomPrivateV1(
      f.bindings, f.Module(), quote, kNativeRevision, kDate);
  const bool accepted = kind != Case::quote_changed && kind != Case::queue_failure;
  const auto expected = kind == Case::quote_changed ? SubmitResult::quote_changed :
      kind == Case::queue_failure ? SubmitResult::command_unavailable : SubmitResult::submitted_verification_pending;
  Check(result == expected, "actual4 submit produces its expected queue-only result");
  const auto ack = native::SerializePlayerPrisonerRansomCommandResult12004(
      "fixture-ransom-action-" + std::string(name), result);
  if (accepted) {
    Check(f.send_copies == 1 && f.clones == 1 && f.queues == 1 && f.deletes == 0 &&
          f.contexts.size() == 1 && f.gates >= 3 &&
          ack.find("\"status\":\"submitted_verification_pending\"") != std::string::npos &&
          ack.find("material_result") == std::string::npos,
          "one queue owns a deep clone; production ACK contains no material claim");
    f.ReleaseQueued();
  } else if (kind == Case::quote_changed) {
    Check(f.send_copies == 0 && f.clones == 0 && f.queues == 0 && f.deletes == 0,
          "changed fresh current_gold offer does not construct or queue");
  } else {
    Check(f.send_copies == 1 && f.clones == 1 && f.queues == 1 && f.deletes == 1,
          "rejected queue consumes and destroys its unique deep clone");
  }
  Check(f.contexts.empty() && f.destroys == f.constructs + 2 * f.send_copies,
        "all quote/context/send-copy/queue-copy owners are destroyed once");
  Check(f.named_scope == nullptr && f.named_owner == nullptr &&
        f.named_clones == (f.selected_gold ? 2U : 0U) &&
        f.named_evaluations == (f.selected_gold ? 4U : 0U) &&
        f.named_destroyed == f.named_clones,
        "observed and fresh gold quotes each use actual4 named reader with two matching samples and scratch teardown");
  Check(f.verified_flags.size() >= 18 && f.verified_flags.size() % kFlags.size() == 0,
        "observed and fresh quote retain all nine authored option identities");
  for (std::size_t i = 0; i < f.verified_flags.size(); ++i)
    Check(f.verified_flags[i] == kFlags[i % kFlags.size()], "every loaded nine-flag pass preserves stock order");
  const bool held = kind != Case::queued_applied && kind != Case::queued_ambiguous;
  const std::int64_t gain = kind == Case::queued_applied ? 7000000 : 0;
  f.revision = kNativeRevision + 1; Put(f.state.data(), native::kGameStateDateOffset, kDate + 1);
  f.SetHeld(held); f.PlayerGold(kPreGold + gain);
  const auto post_snapshot = SnapshotWire(f);
  const auto post_collection = CollectionWire(f, nullptr, 2, held);
  Check(f.frame_captures == 4, "before/post collection each captures the actual4 frame twice");
  const std::string_view receipt = kind == Case::queued_applied ? "applied" :
      kind == Case::queued_ambiguous ? "ambiguous" : accepted ? "pending" : "not_read_after_native_red";
  const std::string_view result_name = kind == Case::quote_changed ? "quote_changed" :
      kind == Case::queue_failure ? "command_unavailable" : "submitted_verification_pending";
  const auto packet = "{\"scenario\":\"" + std::string(name) + "\",\"before_snapshot\":" + before_snapshot +
      ",\"before_collection\":" + before_collection + ",\"command_result\":" + ack +
      ",\"post_snapshot\":" + post_snapshot + ",\"post_collection\":" + post_collection +
      ",\"native_expectations\":{\"submit_result\":\"" + std::string(result_name) +
      "\",\"receipt_expected_status\":\"" + std::string(receipt) + "\",\"selected_option\":\"" +
      std::string(quote.selected_option) + "\",\"quoted_gold_raw\":" + std::to_string(quote.quoted_gold_raw) +
      ",\"amount_is_acceptance_time_quote\":" + (quote.amount_is_acceptance_time_quote ? "true" : "false") +
      ",\"named_fixed_evaluations\":" + std::to_string(f.named_evaluations) +
      ",\"post_prisoner_held\":" + (held ? "true" : "false") +
      ",\"observed_player_gold_gain_raw\":" + std::to_string(gain) + ",\"queue_calls\":" + std::to_string(f.queues) +
      ",\"clone_calls\":" + std::to_string(f.clones) + ",\"deletes\":" + std::to_string(f.deletes) +
      ",\"case_checks\":" + std::to_string(checks - before_checks) +
      ",\"mailbox_route_fixture_covered\":false,\"synthetic_native_callbacks\":true}}";
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Check(stream.is_open(), "open fresh actual4 action packet"); stream << packet << '\n';
  Check(stream.good(), "write complete actual4 action packet");
  std::cout << "FIRST actual4 action " << name << " queue=" << f.queues << " submit=" << result_name << '\n';
  fixture = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  Check(argc == 2, "usage: ck3_12004_prisoner_ransom_action_test OUTPUT_DIRECTORY");
  CheckBinders();
  const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
  RunCase(Case::queued_pending, "queued_pending", directory);
  RunCase(Case::queued_applied, "queued_applied", directory);
  RunCase(Case::queued_ambiguous, "queued_ambiguous", directory);
  RunCase(Case::quote_changed, "quote_changed", directory);
  RunCase(Case::queue_failure, "queue_failure", directory);
  std::cout << "FIRST actual4 action cases=5 checks=" << checks << " complete\n";
  return 0;
}
