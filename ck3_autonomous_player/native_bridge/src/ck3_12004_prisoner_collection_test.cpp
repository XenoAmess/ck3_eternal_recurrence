#include "xar_bridge/ck3_12004_prisoner.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// New actual .4 FIRST producer. It binds the real .4 providers, checks their
// admitted module-relative entries, then replaces native calls with callbacks
// over fixture-owned memory. Production .4 collection, ordinary ransom, named
// fixed-value, release readers and whole serializer perform the observation.
// Source721 IDs/frame/lineage and the five release scenes are software inputs;
// they are not a new paused CK3 sample. Mapped release/serialization software
// algorithms and copied DTOs may be shared; no historical binder or historical
// executable address is invoked.
namespace {
namespace native = xar::ck3_12004;
namespace contract = xar::ck3_12003; // Copied release DTO constants, no native call.
namespace bridge = xar::bridge;

constexpr std::uintptr_t kBindingProbeModule = 0x140000000ULL;
constexpr std::string_view kHistoricalSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::size_t kFixtureImageSize = 0x5C6A600;
constexpr std::int32_t kCharacterCapacity = 100000;
constexpr std::uintptr_t kLand = 0x230000000ULL;
constexpr std::uintptr_t kPrisonerList = 0x240000000ULL;
constexpr std::uintptr_t kExtensionBase = 0x260000000ULL;
constexpr std::uintptr_t kRelationBase = 0x270000000ULL;
constexpr std::uintptr_t kHouseStore = 0x280000000ULL;
constexpr std::uintptr_t kHouseSlots = 0x281000000ULL;
constexpr std::uintptr_t kDynastyStore = 0x290000000ULL;
constexpr std::uintptr_t kDynastySlots = 0x291000000ULL;
constexpr std::uintptr_t kTitleStore = 0x2A0000000ULL;
constexpr std::uintptr_t kTitleSlots = 0x2A1000000ULL;
constexpr std::uintptr_t kTitle = 0x2A2000000ULL;
constexpr std::uintptr_t kTitleTemplate = 0x2A3000000ULL;
constexpr std::uint32_t kPlayerId = 29829;
constexpr std::uint32_t kPayerId = 73000;
constexpr std::array<std::uint32_t, 4> kPrisonerIds{54235, 56063, 61540, 70766};
constexpr std::uint32_t kSelectedOrdinal = 2;
constexpr std::array<std::int64_t, 10> kCosts{
    100001, 200002, 300003, 400004, 500005,
    600006, 700007, 800008, 900009, 1000010};
constexpr std::int32_t kReleaseHash = 0x51520123;
constexpr std::int32_t kReleaseOrdinal = 186;
constexpr std::int32_t kRansomHash = 0x51540124;
constexpr std::uint32_t kNamedCostHash = 0x2BB40123U;
constexpr std::string_view kRansomKey = "ransom_interaction";
constexpr std::string_view kNamedCostKey = "normal_ransom_cost_value";
constexpr std::array<std::string_view, 9> kRansomFlags{
    "extortionate_gold", "extortionate_current_gold", "gold", "current_gold",
    "favor", "influence_send_option", "herd_send_option", "current_herd", "invalid"};
constexpr std::int64_t kNamedCostRaw = 9000000;
constexpr std::int64_t kPayerGoldRaw = 12000000;
constexpr std::int64_t kAnswerScoreRaw = 3300000;
unsigned checks = 0;

void Require(bool condition, std::string_view message) {
  ++checks;
  if (!condition) throw std::runtime_error(std::string(message));
}
template <typename T> void Put(void *base, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T output{};
  std::memcpy(&output, static_cast<const std::byte *>(base) + offset, sizeof(output));
  return output;
}
template <typename T>
void RequireEntry(T pointer, std::uintptr_t rva, std::string_view message) {
  Require(reinterpret_cast<std::uintptr_t>(pointer) == kBindingProbeModule + rva,
          message);
}

void CheckActual4Binders() {
  const auto shared = native::BindInteractionContext12004(
      kBindingProbeModule, native::kExecutableSha256);
  const auto release = native::BindPrisonerReleasePreview12004(
      kBindingProbeModule, native::kExecutableSha256);
  const auto ransom = native::BindPrisonerRansomImage12004(
      kBindingProbeModule, native::kExecutableSha256);
  Require(shared.enabled && release.enabled && ransom.enabled,
          "actual4 native admission must be closed before FIRST");
  Require(!native::BindInteractionContext12004(kBindingProbeModule, kHistoricalSha).enabled &&
          !native::BindPrisonerReleasePreview12004(kBindingProbeModule, kHistoricalSha).enabled &&
          !native::BindPrisonerRansomImage12004(kBindingProbeModule, kHistoricalSha).enabled,
          "historical SHA is not actual4 admission");
  Require(!native::BindPrisonerReleasePreview12004(0, native::kExecutableSha256).enabled &&
          !native::BindPrisonerRansomImage12004(0, native::kExecutableSha256).enabled,
          "null module has no native binding");
  RequireEntry(shared.get_database, native::kInteractionDatabaseGetterRva12004, "4 database entry");
  RequireEntry(shared.stable_hash, native::kInteractionStableHashRva12004, "4 stable hash entry");
  RequireEntry(shared.lookup_definition, native::kInteractionDefinitionLookupRva12004, "4 definition lookup entry");
  RequireEntry(shared.construct_two_role, native::kInteractionConstructTwoRoleRva12004, "4 two-role entry");
  RequireEntry(shared.context.construct_all_roles, native::kInteractionConstructAllRolesRva12004, "4 all-role entry");
  RequireEntry(shared.context.redirect_roles, native::kInteractionRedirectRolesRva12004, "4 role redirect entry");
  RequireEntry(shared.context.refresh, native::kInteractionRefreshRva12004, "4 refresh entry");
  RequireEntry(shared.context.finalize, native::kInteractionFinalizeRva12004, "4 finalizer entry");
  RequireEntry(shared.context.validate, native::kInteractionValidatorRva12004, "4 finalCanSend entry");
  RequireEntry(shared.context.evaluate_cost, native::kInteractionCostEvaluatorRva12004, "4 cost entry");
  RequireEntry(shared.context.evaluate_trigger, native::kInteractionTriggerEvaluatorRva12004, "4 trigger entry");
  RequireEntry(shared.context.destroy, native::kInteractionDestroyRva12004, "4 context destroy entry");
  RequireEntry(shared.clear_local_options, native::kInteractionClearOptionsRva12004, "4 clear entry");
  RequireEntry(shared.select_local_option, native::kInteractionSelectOptionRva12004, "4 select entry");
  RequireEntry(shared.evaluate_answer, native::kInteractionEvaluateAnswerRva12004, "4 answer entry");
  RequireEntry(shared.read_character_interaction_answer_score,
      native::kInteractionRecipientAnswerScoreRva12004, "4 score entry");
  RequireEntry(shared.get_script_identifier_table, native::kInteractionScriptIdTableRva12004, "4 flag table entry");
  RequireEntry(shared.lookup_script_identifier_id, native::kInteractionLookupScriptIdRva12004, "4 flag lookup entry");
  RequireEntry(shared.context.core.get_local_player, native::kGetLocalPlayerRva, "4 core local-player entry");
  RequireEntry(shared.context.core.character_storage_slot, native::kCharacterStorageSlotRva, "4 character slot");
  RequireEntry(release.gift.construct_two_role, native::kInteractionConstructTwoRoleRva12004, "4 release uses admitted constructor");
  RequireEntry(release.gift.interaction.validate, native::kInteractionValidatorRva12004, "4 release uses admitted gate");
  RequireEntry(ransom.interaction.context.construct_all_roles,
      native::kInteractionConstructAllRolesRva12004, "4 ransom uses admitted constructor");
  const auto &named = ransom.named;
  Require(named.enabled && named.module_base == kBindingProbeModule, "4 named provider admitted");
  RequireEntry(named.named_database, native::kPrisonerNamedDatabaseRva12004, "4 named database");
  RequireEntry(named.lookup_named, native::kPrisonerNamedLookupRva12004, "4 named lookup");
  RequireEntry(named.clone_scope, native::kPrisonerNamedCloneScopeRva12004, "4 named scope clone");
  RequireEntry(named.construct_support_118, native::kPrisonerNamedSupport118Rva12004, "4 named support118");
  RequireEntry(named.construct_support_2a8, native::kPrisonerNamedSupport2a8Rva12004, "4 named support2a8");
  RequireEntry(named.intern_database, native::kPrisonerNamedInternDatabaseRva12004, "4 named intern database");
  RequireEntry(named.intern_string, native::kPrisonerNamedInternStringRva12004, "4 named intern string");
  RequireEntry(named.evaluate_fixed, native::kPrisonerNamedFixedRva12004, "4 named fixed entry");
  RequireEntry(named.destroy_scope_tail, native::kPrisonerNamedDestroyTailRva12004, "4 named scope tail");
  RequireEntry(named.destroy_scope_rows, native::kPrisonerNamedDestroyScopeRowsRva12004, "4 named scope rows");
  RequireEntry(named.destroy_support_rows, native::kPrisonerNamedDestroySupportRowsRva12004, "4 named support rows");
  RequireEntry(named.evaluation_flag, native::kPrisonerNamedEvaluationFlagRva12004, "4 named flag slot");
  Require(named.named_primary_vtable == kBindingProbeModule + native::kPrisonerNamedPrimaryVtableRva12004 &&
          named.named_secondary_vtable == kBindingProbeModule + native::kPrisonerNamedSecondaryVtableRva12004,
          "4 named class identity entries");
}

enum class Case { gate_true, gate_false, old11, selected_change_prison,
                  puppet_role_mismatch };

struct Fixture {
  explicit Fixture(Case value) : kind(value) {}
  Case kind;
  // Only fixture-owned bytes: the slots need actual addresses because the .4
  // core and ransom readers dereference their admitted slots directly.
  std::vector<std::byte> image = std::vector<std::byte>(kFixtureImageSize);
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local_player{};
  std::vector<std::byte> state_data = std::vector<std::byte>(0x22350);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void *, 1> player_entries{player_entry.data()};
  std::array<std::byte, 0x30> character_store{};
  std::vector<std::byte> character_slots =
      std::vector<std::byte>(static_cast<std::size_t>(kCharacterCapacity) * 0x10);
  std::array<std::byte, 0x200> player{};
  std::array<std::array<std::byte, 0x200>, 4> prisoners{};
  std::array<std::byte, 0x200> payer{};
  std::array<std::byte, 0x110> payer_extension{};
  std::map<std::uintptr_t, std::byte> memory;
  std::array<std::byte, 0x2800> release_definition{}, ransom_definition{};
  std::array<std::byte, 13 * 0x730> release_rows{};
  std::array<std::byte, 9 * 0x730> ransom_rows{};
  std::array<std::byte, 0xA0> named_definition{};
  std::array<std::uint8_t, 13> release_selected{};
  std::array<std::uint8_t, 9> ransom_selected{};
  std::vector<std::pair<std::uintptr_t, std::size_t>> readable_ranges;
  void *context = nullptr;
  void *named_scope = nullptr;
  std::uint8_t trigger_token = 1, evaluation_flag = 1;
  unsigned constructed = 0, destroyed = 0, flags = 0;
  unsigned refreshed = 0, finalized = 0, gates = 0, costs = 0, auto_accepts = 0;
  unsigned ransom_constructed = 0, ransom_destroyed = 0, ransom_flags = 0;
  unsigned ransom_gates = 0, ransom_scores = 0, ransom_answers = 0;
  unsigned named_clones = 0, named_evaluations = 0, named_destroyed = 0;
  bridge::PlayerPrisonerFrameV1 frame{
      1014, 1014, 1926335, 53286360, true, true,
      static_cast<std::int32_t>(kPlayerId), true, true};

  std::uintptr_t Module() const { return reinterpret_cast<std::uintptr_t>(image.data()); }
  template <typename T> void MemoryPut(std::uintptr_t address, const T &value) {
    std::array<std::byte, sizeof(T)> bytes{};
    std::memcpy(bytes.data(), &value, bytes.size());
    for (std::size_t i = 0; i < bytes.size(); ++i) memory[address + i] = bytes[i];
  }
  void Range(const void *address, std::size_t size) {
    readable_ranges.emplace_back(reinterpret_cast<std::uintptr_t>(address), size);
  }
  void Storage(std::uintptr_t slot_rva, std::uintptr_t fallback_rva,
               std::uintptr_t storage, std::uintptr_t slots) {
    MemoryPut(Module() + slot_rva, storage);
    MemoryPut(Module() + fallback_rva, std::uintptr_t{0});
    MemoryPut(storage + 0x20, slots);
    MemoryPut(storage + 0x2C, kCharacterCapacity);
  }
  void Lineage(std::int32_t house, std::int32_t dynasty,
               std::uintptr_t house_object, std::uintptr_t dynasty_object) {
    MemoryPut(kHouseSlots + static_cast<std::uintptr_t>(house) * 0x10 + 8, house_object);
    MemoryPut(house_object + 0x10, house);
    MemoryPut(house_object + 0x2C, dynasty);
    MemoryPut(kDynastySlots + static_cast<std::uintptr_t>(dynasty) * 0x10 + 8, dynasty_object);
    MemoryPut(dynasty_object + 0x10, dynasty);
  }
  void Prepare() {
    Put(image.data(), native::kCharacterStorageSlotRva, character_store.data());
    Put(image.data(), 0x5C67570, static_cast<void *>(nullptr));
    Put(character_store.data(), 0x20, character_slots.data());
    Put(character_store.data(), 0x2C, kCharacterCapacity);
    Put(character_slots.data(), kPlayerId * 0x10ULL + 8, player.data());
    Put(player.data(), 0x18, kPlayerId);
    Put(player.data(), 0x158, std::int32_t{174});
    Put(player.data(), 0x1C0, kLand);
    for (std::size_t i = 0; i < kPrisonerIds.size(); ++i) {
      const auto extension = kExtensionBase + i * 0x1000;
      const auto relation = kRelationBase + i * 0x1000;
      Put(character_slots.data(), kPrisonerIds[i] * 0x10ULL + 8, prisoners[i].data());
      Put(prisoners[i].data(), 0x18, kPrisonerIds[i]);
      Put(prisoners[i].data(), 0x158, std::int32_t{i < 2 ? -1 : (i == 2 ? 2237 : 12690)});
      Put(prisoners[i].data(), 0x1A8, std::uintptr_t{0});
      Put(prisoners[i].data(), 0x1B0, extension);
      MemoryPut(kPrisonerList + i * sizeof(std::uint32_t), kPrisonerIds[i]);
      MemoryPut(extension + 0x288, relation);
      MemoryPut(relation, kPlayerId);
      Range(prisoners[i].data(), prisoners[i].size());
    }
    Put(character_slots.data(), kPayerId * 0x10ULL + 8, payer.data());
    Put(payer.data(), 0x18, kPayerId);
    Put(payer.data(), 0x1B0, payer_extension.data());
    Put(payer_extension.data(), 0x100, kPayerGoldRaw);
    MemoryPut(kLand + 0xD8, kPrisonerList);
    MemoryPut(kLand + 0xE4, std::int32_t{4});
    MemoryPut(kLand + 0x350, std::int64_t{1680000});
    Storage(0x5D1DAF0, 0x5D1DAE8, kHouseStore, kHouseSlots);
    Storage(0x5D1DE78, 0x5D1DE28, kDynastyStore, kDynastySlots);
    Storage(native::kPrisonerTitleStorageSlotRva12004,
            native::kPrisonerTitleFallbackSlotRva12004, kTitleStore, kTitleSlots);
    Lineage(174, 174, 0x282000000ULL, 0x292000000ULL);
    Lineage(2237, 2237, 0x282001000ULL, 0x292001000ULL);
    Lineage(12690, 12077, 0x282002000ULL, 0x292002000ULL);
    constexpr std::int32_t title_id = 2115;
    MemoryPut(kTitleSlots + title_id * 0x10ULL + 8, kTitle);
    MemoryPut(kTitle + 0x10, title_id);
    MemoryPut(kTitle + 0x48, kTitleTemplate);
    MemoryPut(kTitleTemplate + 0x64, std::int32_t{3});

    Put(image.data(), native::kGameStateSlotRva, game_state.data());
    Put(image.data(), native::kJominiStateSlotRva, jomini.data());
    Put(game_state.data(), native::kGameStateDateOffset, frame.date_raw);
    Put(game_state.data(), native::kGameStateSpeedOffset, std::int32_t{2});
    Put(game_state.data(), native::kGameStateDataOffset, state_data.data());
    Put(jomini.data(), native::kJominiPlayersOffset, players.data());
    Put(jomini.data(), native::kJominiPausedOffset, std::uint8_t{1});
    Put(players.data(), native::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(local_player.data(), native::kPlayerIdOffset, std::int32_t{7});
    Put(state_data.data(), native::kPlayerCharacterManagerOffset + native::kPlayerManagerEntriesOffset, player_entries.data());
    Put(state_data.data(), native::kPlayerCharacterManagerOffset + native::kPlayerManagerCountOffset, std::int32_t{1});
    Put(player_entry.data(), native::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(player_entry.data(), native::kPlayerEntryCharacterIdOffset, kPlayerId);

    const auto release_key = contract::kPrisonerReleaseDefinitionKey12003;
    Put(release_definition.data(), 0x10, kReleaseOrdinal);
    Put(release_definition.data(), 0x14, kReleaseHash);
    Put(release_definition.data(), 0x18, release_key.data());
    Put(release_definition.data(), 0x28, static_cast<std::uint64_t>(release_key.size()));
    Put(release_definition.data(), 0x30, std::uint64_t{64});
    Put(release_definition.data(), 0x2258, release_rows.data());
    Put(release_definition.data(), 0x2264, std::int32_t{kind == Case::old11 ? 11 : 13});
    Put(release_definition.data(), 0x2290, &trigger_token);
    Put(release_definition.data(), 0x2718, std::uint8_t{1});
    for (std::size_t i = 0; i < contract::kPrisonerReleaseOptionKeys12003.size(); ++i)
      Put(release_rows.data(), i * 0x730 + 0x368, static_cast<std::int32_t>(1000 + i));
    Put(ransom_definition.data(), 0x14, kRansomHash);
    Put(ransom_definition.data(), 0x18, kRansomKey.data());
    Put(ransom_definition.data(), 0x28, static_cast<std::uint64_t>(kRansomKey.size()));
    Put(ransom_definition.data(), 0x30, std::uint64_t{64});
    Put(ransom_definition.data(), 0x2258, ransom_rows.data());
    Put(ransom_definition.data(), 0x2264, std::int32_t{9});
    for (std::size_t i = 0; i < kRansomFlags.size(); ++i)
      Put(ransom_rows.data(), i * 0x730 + 0x368, static_cast<std::int32_t>(100 + i));
    Put(named_definition.data(), 0, Module() + native::kPrisonerNamedPrimaryVtableRva12004);
    Put(named_definition.data(), 0x88, Module() + native::kPrisonerNamedSecondaryVtableRva12004);
    Put(named_definition.data(), 0x14, kNamedCostHash);
    Put(named_definition.data(), 0x18, kNamedCostKey.data());
    Put(named_definition.data(), 0x28, static_cast<std::uint64_t>(kNamedCostKey.size()));
    Put(named_definition.data(), 0x30, std::uint64_t{64});
    Put(named_definition.data(), 0x38, std::uint32_t{0x4744624F});
    Range(image.data(), image.size());
    Range(character_store.data(), character_store.size());
    Range(character_slots.data(), character_slots.size());
    Range(player.data(), player.size());
    Range(release_definition.data(), release_definition.size());
    Range(release_rows.data(), release_rows.size());
    Range(release_selected.data(), release_selected.size());
    Range(release_key.data(), release_key.size());
  }
};
Fixture *active = nullptr;

bool ReadMemory(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  // Virtual lineage slots lie beyond the fixture's real core image; map reads
  // are checked first so an overlapping real range cannot shadow them.
  const auto first = f.memory.find(address);
  if (first != f.memory.end()) {
    auto *bytes = static_cast<std::byte *>(output);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.memory.find(address + i);
      if (found == f.memory.end()) return false;
      bytes[i] = found->second;
    }
    return true;
  }
  const auto copy_range = [&](std::uintptr_t start, std::size_t length) {
    if (address < start || address - start > length || size > length - (address - start))
      return false;
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  };
  if (f.context != nullptr && copy_range(reinterpret_cast<std::uintptr_t>(f.context), 0x338))
    return true;
  for (const auto &[start, length] : f.readable_ranges)
    if (copy_range(start, length)) return true;
  return false;
}
bool CaptureFrame(void *opaque, bridge::PlayerPrisonerFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}
void *PrimaryTitle(void *character) {
  return character == active->prisoners[3].data() ? reinterpret_cast<void *>(kTitle) : nullptr;
}
void *LocalPlayer(void *jomini) {
  Require(jomini == active->jomini.data(), "actual4 core uses owned jomini slot");
  return active->local_player.data();
}
void *Database() { return active; }
std::int32_t StableHash(void *database, const char *data, std::uint32_t size) {
  const auto key = std::string_view(data, size);
  if (key == kNamedCostKey) {
    Require(database == nullptr, "named stable key without interaction database");
    return static_cast<std::int32_t>(kNamedCostHash);
  }
  Require(database == active, "interaction database identity");
  if (key == contract::kPrisonerReleaseDefinitionKey12003) return kReleaseHash;
  Require(key == kRansomKey, "canonical ransom key");
  return kRansomHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Require(database == active, "interaction lookup database");
  if (hash == kReleaseHash) return active->release_definition.data();
  Require(hash == kRansomHash, "canonical ransom definition hash");
  return active->ransom_definition.data();
}
std::int32_t *Flag(void *table, std::int32_t *output, const void *view) {
  Require(table == active && Get<std::uint8_t>(view, 0xC) == 0, "borrowed flag view/table");
  const auto size = Get<std::int32_t>(view, 8);
  Require(size >= 0, "flag view length");
  const auto key = std::string_view(Get<const char *>(view, 0), static_cast<std::size_t>(size));
  for (std::size_t i = 0; i < contract::kPrisonerReleaseOptionKeys12003.size(); ++i) {
    if (contract::kPrisonerReleaseOptionKeys12003[i] == key) {
      *output = static_cast<std::int32_t>(1000 + i);
      ++active->flags;
      return output;
    }
  }
  for (std::size_t i = 0; i < kRansomFlags.size(); ++i) {
    if (kRansomFlags[i] == key) {
      *output = static_cast<std::int32_t>(100 + i);
      ++active->ransom_flags;
      return output;
    }
  }
  Require(false, "flag belongs to current release13 or ransom9");
  return nullptr;
}
void *ConstructRelease(void *context, void *definition, std::int32_t actor,
                       std::int32_t recipient, void *extra, bool redirect) {
  Require(definition == active->release_definition.data() && extra == nullptr && redirect,
          "release two-role constructor inputs");
  Require(actor == static_cast<std::int32_t>(kPlayerId) &&
          recipient == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]),
          "release two-role IDs");
  Require(active->context == nullptr, "release context ownership");
  active->context = context;
  ++active->constructed;
  Put(context, 0, definition);
  Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, std::int32_t{-1}); Put(context, 0x2E4, std::int32_t{-1});
  Put(context, 0x2E8, std::int32_t{-1});
  Put(context, 0x2EC, std::int32_t{actor + (active->kind == Case::puppet_role_mismatch ? 1 : 0)});
  Put(context, 0x300, active->release_selected.data());
  Put(context, 0x308, std::int32_t{13}); Put(context, 0x30C, std::int32_t{13});
  return context;
}
void ClearRelease(void *context) {
  Require(context == active->context, "release clear owns context");
  active->release_selected.fill(0);
}
void Refresh(void *context, bool recompute) {
  Require(context == active->context && recompute, "release refresh");
  ++active->refreshed;
}
void Finalize(void *context) {
  Require(context == active->context, "release finalize");
  ++active->finalized;
  if (active->kind == Case::selected_change_prison) active->release_selected[5] = 1;
}
bool ReleaseGate(void *context, void *failure) {
  Require(context == active->context && failure == nullptr, "release final gate");
  ++active->gates;
  return active->kind != Case::gate_false;
}
void Cost(const void *definition_cost, const void *scope, std::int64_t *output) {
  Require(definition_cost == active->release_definition.data() + 0x40 &&
          scope == static_cast<std::byte *>(active->context) + 8, "release finalized cost scope");
  std::memcpy(output, kCosts.data(), sizeof(kCosts));
  ++active->costs;
}
bool AutoAccept(void *trigger, const void *scope) {
  Require(trigger == &active->trigger_token &&
          scope == static_cast<std::byte *>(active->context) + 8, "release native auto-accept scope");
  ++active->auto_accepts;
  return true;
}
void DestroyRelease(void *context) {
  Require(context == active->context, "release destroys once");
  ++active->destroyed;
  active->context = nullptr;
}
void RedirectRansom(void *definition, std::int32_t *actor, std::int32_t *recipient,
    std::int32_t *sa, std::int32_t *sr, std::int32_t *intermediary, std::int32_t *added) {
  Require(definition == active->ransom_definition.data() &&
          *actor == static_cast<std::int32_t>(kPlayerId) &&
          *recipient == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]) &&
          *sa == -1 && *sr == -1 && *intermediary == -1 && *added == -1,
          "actual4 ransom initial seven role arguments");
  *recipient = static_cast<std::int32_t>(kPayerId);
  *sr = static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]);
}
void *ConstructRansom(void *context, void *definition, std::int32_t actor,
    std::int32_t recipient, std::int32_t sa, std::int32_t sr,
    std::int32_t intermediary, void *extra) {
  Require(active->context == nullptr && definition == active->ransom_definition.data() &&
          actor == static_cast<std::int32_t>(kPlayerId) && recipient == static_cast<std::int32_t>(kPayerId) &&
          sa == -1 && sr == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]) &&
          intermediary == -1 && extra == nullptr, "actual4 redirected ransom roles");
  active->context = context;
  ++active->ransom_constructed;
  Put(context, 0, definition);
  Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, sa); Put(context, 0x2E4, sr); Put(context, 0x2E8, intermediary);
  Put(context, 0x300, active->ransom_selected.data());
  Put(context, 0x308, std::int32_t{9}); Put(context, 0x30C, std::int32_t{9});
  return context;
}
void ClearRansom(void *context) {
  Require(context == active->context, "ransom clear owns context");
  active->ransom_selected.fill(0);
}
void SelectRansom(void *context, std::int32_t option) {
  Require(context == active->context && (option == 2 || option == 3), "ordinary ransom option index");
  if ((active->kind == Case::old11 && option == 3) ||
      (active->kind != Case::old11 && option == 2))
    active->ransom_selected[static_cast<std::size_t>(option)] = 1;
}
bool RansomGate(void *context, void *failure) {
  Require(context == active->context && failure == nullptr, "ransom final gate");
  ++active->ransom_gates;
  return active->kind != Case::gate_false;
}
std::int64_t *RansomScore(void *context, std::int64_t *output) {
  Require(context == active->context, "ransom score context");
  *output = kAnswerScoreRaw;
  ++active->ransom_scores;
  return output;
}
std::uint8_t RansomAnswer(void *context, std::uint8_t mode, std::uint8_t flag,
                          void *first, void *second) {
  Require(context == active->context && mode == 1 && flag == 1 && first == nullptr && second == nullptr,
          "actual4 final native answer ABI");
  ++active->ransom_answers;
  return active->kind == Case::old11 ? std::uint8_t{0} :
      active->kind == Case::selected_change_prison ? std::uint8_t{2} : std::uint8_t{1};
}
void DestroyRansom(void *context) {
  Require(context == active->context && active->named_scope == nullptr, "ransom destroys owning context after named scratch");
  active->context = nullptr;
  ++active->ransom_destroyed;
}
const void *LookupNamed(void *database, std::uint32_t hash) {
  Require(database == active && hash == kNamedCostHash, "canonical named cost lookup");
  return active->named_definition.data();
}
void *CloneNamedScope(void *destination, const void *source) {
  Require(active->named_scope == nullptr && active->context != nullptr &&
          source == static_cast<std::byte *>(active->context) + 8 &&
          Get<void *>(active->context, 0) == active->ransom_definition.data() &&
          active->ransom_selected[2] == 1, "gold named read borrows finalized ransom scope");
  std::memcpy(destination, source, 0x168);
  active->named_scope = destination;
  ++active->named_clones;
  return destination;
}
void *Support118(void *support) { std::memset(support, 0, 0x128); return support; }
void *Support2a8(void *support) { std::memset(support, 0, 0x2A8); return support; }
const void *Intern(void *database, const void *view) {
  Require(database == active &&
          std::string_view(Get<const char *>(view, 0), Get<std::uint32_t>(view, 8)) == kNamedCostKey,
          "normal_ransom_cost_value interned source");
  return kNamedCostKey.data();
}
std::int64_t *EvaluateNamed(const void *definition, std::int64_t *output,
                            void *internal, void *secondary, const void *source) {
  Require(definition == active->named_definition.data() && secondary == nullptr &&
          Get<void *>(internal, 0) == active->named_scope &&
          Get<void *>(internal, 8) == active->named_scope &&
          Get<void *>(internal, 0x10) == active->named_scope &&
          Get<std::uint8_t>(internal, 0x20) == active->evaluation_flag &&
          Get<std::uint16_t>(active->named_scope, 0) == 4 &&
          Get<std::uint64_t>(active->named_scope, 8) == kPrisonerIds[kSelectedOrdinal] &&
          Get<const void *>(source, 0) == kNamedCostKey.data() &&
          Get<std::uint8_t>(source, 0x14) == 1 && Get<std::int32_t>(source, 0x18) == -1,
          "actual4 named fixed root/internal/source ABI");
  Require(Get<std::int32_t>(active->context, 0x2D8) == static_cast<std::int32_t>(kPlayerId) &&
          Get<std::int32_t>(active->context, 0x2DC) == static_cast<std::int32_t>(kPayerId) &&
          Get<std::int32_t>(active->context, 0x2E4) == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]),
          "named quote retains jailer/redirected payer/prisoner");
  *output = kNamedCostRaw;
  ++active->named_evaluations;
  return output;
}
void DestroyNamedTail(void *tail) {
  Require(active->named_scope != nullptr &&
          tail == static_cast<std::byte *>(active->named_scope) + 0x118, "actual4 named tail ownership");
  active->named_scope = nullptr;
  ++active->named_destroyed;
}
void EmptyNamedRows(void *) { Require(false, "fixture named vectors remain empty"); }

native::PrisonerReleasePreviewBindings12004 BindReleaseFixture(Fixture &f) {
  auto b = native::BindPrisonerReleasePreview12004(f.Module(), native::kExecutableSha256);
  Require(b.enabled && b.gift.enabled && b.gift.interaction.enabled, "actual4 release admitted before callback override");
  b.gift.get_database = Database; b.gift.stable_hash = StableHash;
  b.gift.lookup_definition = Lookup; b.gift.construct_two_role = ConstructRelease;
  b.gift.interaction.core.get_local_player = LocalPlayer;
  b.gift.interaction.refresh = Refresh; b.gift.interaction.finalize = Finalize;
  b.gift.interaction.validate = ReleaseGate; b.gift.interaction.evaluate_cost = Cost;
  b.gift.interaction.evaluate_trigger = AutoAccept; b.gift.interaction.destroy = DestroyRelease;
  b.get_script_identifier_table = Database; b.lookup_script_identifier_id = Flag;
  b.clear_local_options = ClearRelease;
  return b;
}
native::PrisonerRansomBindings12004 BindRansomFixture(Fixture &f) {
  auto b = native::BindPrisonerRansomImage12004(f.Module(), native::kExecutableSha256);
  Require(b.enabled && b.interaction.enabled && b.named.enabled, "actual4 ransom admitted before callback override");
  auto &interaction = b.interaction;
  interaction.context.core.get_local_player = LocalPlayer;
  interaction.context.redirect_roles = RedirectRansom;
  interaction.context.construct_all_roles = ConstructRansom;
  interaction.context.validate = RansomGate; interaction.context.destroy = DestroyRansom;
  interaction.get_database = Database; interaction.stable_hash = StableHash;
  interaction.lookup_definition = Lookup;
  interaction.get_script_identifier_table = Database; interaction.lookup_script_identifier_id = Flag;
  interaction.clear_local_options = ClearRansom; interaction.select_local_option = SelectRansom;
  interaction.read_character_interaction_answer_score = RansomScore; interaction.evaluate_answer = RansomAnswer;
  auto &named = b.named;
  named.core.get_local_player = LocalPlayer;
  named.named_database = Database; named.lookup_named = LookupNamed;
  named.clone_scope = CloneNamedScope;
  named.construct_support_118 = Support118; named.construct_support_2a8 = Support2a8;
  named.intern_database = Database; named.intern_string = Intern; named.evaluate_fixed = EvaluateNamed;
  named.destroy_scope_tail = DestroyNamedTail; named.destroy_scope_rows = EmptyNamedRows;
  named.destroy_support_rows = EmptyNamedRows; named.evaluation_flag = &f.evaluation_flag;
  return b;
}

void RunCase(Case kind, std::string_view name, const std::filesystem::path &directory) {
  Fixture f(kind);
  active = &f;
  f.Prepare();
  bridge::PlayerPrisonerCollectionAccessV1 collection_access{};
  collection_access.exact_build_admitted = true;
  collection_access.admitted_executable_sha256 = native::kExecutableSha256;
  collection_access.module_base = f.Module();
  collection_access.current_thread_id = 8; collection_access.application_main_thread_id = 8;
  collection_access.read_lineage = true; collection_access.read_child_relation = true;
  collection_access.read_title_tier = true; collection_access.read_dread = true;
  collection_access.context = &f; collection_access.capture_frame = CaptureFrame;
  collection_access.read_memory = ReadMemory; collection_access.get_primary_title = PrimaryTitle;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  if (kind == Case::gate_true) {
    auto historical_access = collection_access;
    historical_access.admitted_executable_sha256 = kHistoricalSha;
    Require(!native::ReadPlayerPrisonerCollectionV1(historical_access, collection) &&
            collection.failure == bridge::PlayerPrisonerCollectionFailureV1::exact_build_mismatch,
            "actual4 collection rejects historical admission");
  }
  Require(native::ReadPlayerPrisonerCollectionV1(collection_access, collection), "actual4 complete collection reader");
  Require(collection.available && collection.collection_complete && collection.total_count == 4 &&
          collection.returned_count == 4 && collection.played_house_id == 174 &&
          collection.played_dynasty_id == 174 && collection.played_dread_raw == 1680000,
          "synthetic source721 full collection shape");
  for (std::size_t i = 0; i < kPrisonerIds.size(); ++i)
    Require(collection.rows[i].full_character_id == kPrisonerIds[i] &&
            collection.rows[i].jailer_character_id == kPlayerId && collection.rows[i].source_ordinal == i &&
            !collection.rows[i].child_of_played_character, "full ordered IDs and reverse custody");
  Require(collection.rows[2].house_id == 2237 && collection.rows[2].dynasty_id == 2237 &&
          collection.rows[3].house_id == 12690 && collection.rows[3].dynasty_id == 12077 &&
          collection.rows[3].primary_title_tier_raw == 3, "actual4 collection lineage/title read");

  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  for (auto &quote : quotes) quote.failure = native::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  quotes[kSelectedOrdinal] = native::ReadPlayerPrisonerRansomQuotePrivateV1(BindRansomFixture(f),
      f.Module(), static_cast<std::int32_t>(kPlayerId), static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]));
  const auto &quote = quotes[kSelectedOrdinal];
  if (kind == Case::gate_false) {
    Require(!quote.available && quote.failure == native::PlayerPrisonerRansomQuoteFailureV1::final_can_send_false &&
            f.ransom_gates == 1 && f.ransom_scores == 0 && f.ransom_answers == 0 && f.named_evaluations == 0,
            "actual4 negative ransom gate gives no made-up score/amount");
  } else {
    const bool current_gold = kind == Case::old11;
    const auto answer = current_gold ? std::uint8_t{0} :
        kind == Case::selected_change_prison ? std::uint8_t{2} : std::uint8_t{1};
    Require(quote.available && quote.failure == native::PlayerPrisonerRansomQuoteFailureV1::none &&
            quote.jailer_character_id == static_cast<std::int32_t>(kPlayerId) &&
            quote.payer_character_id == static_cast<std::int32_t>(kPayerId) &&
            quote.prisoner_character_id == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]) &&
            quote.selected_option == (current_gold ? "current_gold" : "gold") &&
            quote.quoted_gold_raw == (current_gold ? kPayerGoldRaw : kNamedCostRaw) &&
            quote.amount_is_acceptance_time_quote == current_gold &&
            quote.recipient_acceptance_raw == kAnswerScoreRaw && quote.recipient_answer_status_raw == answer &&
            quote.would_accept_now == (answer != 2) && f.ransom_gates == 1 && f.ransom_scores == 1 &&
            f.ransom_answers == 1, "actual4 ordinary final roles/current gold/named amount/native answer");
    Require(f.named_clones == (current_gold ? 0U : 1U) &&
            f.named_evaluations == (current_gold ? 0U : 2U) &&
            f.named_destroyed == f.named_clones, "actual4 native fixed repeated sample and scratch destruction");
  }
  Require(quote.observed_definition_option_count == 9 && quote.observed_context_option_count == 9 &&
          f.ransom_flags == 9 && f.ransom_constructed == f.ransom_destroyed &&
          f.ransom_constructed == (kind == Case::old11 || kind == Case::gate_false ? 2U : 1U) &&
          f.context == nullptr && f.named_scope == nullptr, "all9 authored flags and ransom ownership");

  const native::PrisonerReleasePreviewAccess12004 release_access{8, 8, &f, CaptureFrame, ReadMemory};
  std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> previews{};
  const bool complete = native::ReadPrisonerReleasePreview12004(BindReleaseFixture(f), release_access,
      kPlayerId, kPrisonerIds[kSelectedOrdinal], previews[kSelectedOrdinal]);
  const auto &preview = previews[kSelectedOrdinal];
  const bool expected_complete = kind == Case::gate_true || kind == Case::gate_false;
  Require(complete == expected_complete && preview.available == expected_complete, "actual4 release observation completeness");
  if (expected_complete) {
    Require(preview.can_send == (kind == Case::gate_true) && preview.auto_accept &&
            preview.send_costs_raw == kCosts && preview.raw_scale == 100000 && preview.frame == f.frame &&
            preview.unavailable_reason.empty(), "actual4 native true/false and ten costs");
    Require(preview.definition_key == contract::kPrisonerReleaseDefinitionKey12003 &&
            preview.definition_stable_hash == static_cast<std::uint32_t>(kReleaseHash) &&
            preview.definition_ordinal == kReleaseOrdinal && preview.actor_character_id == kPlayerId &&
            preview.recipient_character_id == kPrisonerIds[kSelectedOrdinal] && preview.puppet_or_actor_character_id == kPlayerId &&
            preview.observed_definition_option_count == 13 && preview.observed_context_option_count == 13 &&
            preview.selected_option_mask_bits == 0, "actual4 player/jailer and all13-off final roles");
    Require(f.constructed == 2 && f.destroyed == 2 && f.flags == 26 && f.refreshed == 2 &&
            f.finalized == 2 && f.gates == 2 && f.costs == 2 && f.auto_accepts == 2,
            "two independent actual4 release source samples");
  } else {
    const std::string_view reason = kind == Case::old11 ? "option_definition_count_unexpected" :
        kind == Case::selected_change_prison ? "option_mask_unexpected" : "option_context_roles_unverified";
    Require(preview.unavailable_reason == reason && f.gates == 0 && f.costs == 0 && f.auto_accepts == 0,
            "actual4 release unavailable before final evaluation");
    const unsigned contexts = kind == Case::old11 ? 0U : 1U;
    Require(f.constructed == contexts && f.destroyed == contexts && f.refreshed == contexts && f.finalized == contexts,
            "unavailable release context destroyed");
  }
  Require(f.context == nullptr, "all temporary context lifetimes ended");
  const auto value = native::SerializePlayerPrisonerCollectionPrivateV1(
      collection, f.frame.native_revision, quotes, true, &previews);
  Require(!value.empty() && value.find("\"schema_version\":6") != std::string::npos &&
          value.find("\"unconditional_release_preview\"") != std::string::npos &&
          value.find("\"native_kinship\"") == std::string::npos && value.find("\"negotiated_release_preview\"") == std::string::npos,
          "base-only production collection serializer keeps schema6");
  const auto wire = std::string{
      "{\"step\":\"query-player-prisoner-collection-private-v1-ransom-ordinal-2\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":"} +
      std::to_string(static_cast<unsigned>(kind) + 1U) +
      ",\"observation_revision\":" + std::to_string(f.frame.proof_epoch) +
      ",\"snapshot_revision\":" + std::to_string(f.frame.native_revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\"}";
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Require(stream.is_open(), "open new actual4 whole wire");
  stream << wire << '\n';
  Require(stream.good(), "write new actual4 whole wire");
  std::cout << "FIRST actual4 " << name << " whole_collection=4 ransom_available="
            << (quote.available ? "true" : "false") << " release_available="
            << (preview.available ? "true" : "false") << '\n';
  active = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12004_prisoner_collection_test OUTPUT_DIRECTORY");
    CheckActual4Binders();
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunCase(Case::gate_true, "gate_true", directory);
    RunCase(Case::gate_false, "gate_false", directory);
    RunCase(Case::old11, "old11", directory);
    RunCase(Case::selected_change_prison, "selected_change_prison", directory);
    RunCase(Case::puppet_role_mismatch, "puppet_role_mismatch", directory);
    std::cout << "FIRST actual4 groups=3 cases=5 checks=" << checks << " complete\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST actual4 RED " << error.what() << '\n';
    return 1;
  }
}
