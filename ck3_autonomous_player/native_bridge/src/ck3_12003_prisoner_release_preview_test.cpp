#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"
#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_family_subject_abi.hpp"

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
#include <vector>

// A single FIRST fixture compound: the actual .2 collection reader (admitted
// by the .3 ABI reuse manifest), the new .3 release reader, and the actual
// whole collection serializer. It never invokes an old ransom reader/action.
// The four identities and lineage shape derive from archived source 721;
// the definition ordinal/hash, native callbacks, and costs are synthetic.
namespace {
namespace old = xar::ck3_12002;
namespace leaf = xar::ck3_12003;
namespace bridge = xar::bridge;

constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uintptr_t kCharacterStore = 0x200000000ULL;
constexpr std::uintptr_t kCharacterSlots = 0x210000000ULL;
constexpr std::uintptr_t kPlayer = 0x220000000ULL;
constexpr std::uintptr_t kPrisonerBase = 0x220001000ULL;
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
constexpr std::array<std::uint32_t, 4> kPrisonerIds{54235, 56063, 61540, 70766};
constexpr std::array<std::int64_t, 10> kCosts{
    100001, 200002, 300003, 400004, 500005,
    600006, 700007, 800008, 900009, 1000010};
constexpr std::int32_t kDefinitionHash = 0x51520123;
constexpr std::int32_t kDefinitionOrdinal = 186;
constexpr std::uint32_t kSelectedOrdinal = 2;

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

enum class Case { gate_true, gate_false, old11, selected_change_prison,
                  puppet_role_mismatch };

struct Fixture {
  explicit Fixture(Case value) : kind(value) {}
  Case kind;
  std::map<std::uintptr_t, std::byte> memory;
  std::array<std::byte, 0x2800> definition{};
  std::array<std::byte, 13 * 0x730> option_rows{};
  std::array<std::uint8_t, 13> selected{};
  std::vector<std::pair<std::uintptr_t, std::size_t>> readable_ranges;
  void *context = nullptr;
  std::uint8_t trigger_token = 1;
  unsigned constructed = 0, destroyed = 0, flags = 0;
  unsigned refreshed = 0, finalized = 0, gates = 0, costs = 0, auto_accepts = 0;
  bridge::PlayerPrisonerFrameV1 frame{
      1014, 1014, 1926335, 53286360, true, true,
      static_cast<std::int32_t>(kPlayerId), true, true};

  template <typename T> void Put(std::uintptr_t address, const T &value) {
    std::array<std::byte, sizeof(T)> bytes{};
    std::memcpy(bytes.data(), &value, bytes.size());
    for (std::size_t i = 0; i < bytes.size(); ++i) memory[address + i] = bytes[i];
  }
  template <typename T> void BufferPut(void *buffer, std::size_t offset,
                                      const T &value) {
    std::memcpy(static_cast<std::byte *>(buffer) + offset, &value, sizeof(value));
  }
  void Range(const void *address, std::size_t size) {
    readable_ranges.emplace_back(reinterpret_cast<std::uintptr_t>(address), size);
  }
  void Storage(std::uintptr_t slot_rva, std::uintptr_t fallback_rva,
               std::uintptr_t storage, std::uintptr_t slots) {
    Put(kModule + slot_rva, storage);
    Put(kModule + fallback_rva, std::uintptr_t{0});
    Put(storage + 0x20, slots);
    Put(storage + 0x2C, std::int32_t{100000});
  }
  void Lineage(std::int32_t house, std::int32_t dynasty, std::uintptr_t house_object,
               std::uintptr_t dynasty_object) {
    Put(kHouseSlots + static_cast<std::uintptr_t>(house) * 0x10 + 8, house_object);
    Put(house_object + 0x10, house);
    Put(house_object + 0x2C, dynasty);
    Put(kDynastySlots + static_cast<std::uintptr_t>(dynasty) * 0x10 + 8, dynasty_object);
    Put(dynasty_object + 0x10, dynasty);
  }
  void Prepare() {
    Storage(old::kCharacterStorageSlotRva, 0x5C67570, kCharacterStore, kCharacterSlots);
    Storage(old::kFamilySubjectHouseStorageSlotRva,
            old::kFamilySubjectHouseFallbackSlotRva, kHouseStore, kHouseSlots);
    Storage(old::kFamilySubjectDynastyStorageSlotRva,
            old::kFamilySubjectDynastyFallbackSlotRva, kDynastyStore, kDynastySlots);
    Storage(old::kCampaignRootLandedTitleStorageSlotRva,
            old::kCampaignRootLandedTitleFallbackSlotRva, kTitleStore, kTitleSlots);
    Lineage(174, 174, 0x282000000ULL, 0x292000000ULL);
    Lineage(2237, 2237, 0x282001000ULL, 0x292001000ULL);
    Lineage(12690, 12077, 0x282002000ULL, 0x292002000ULL);
    Put(kCharacterSlots + kPlayerId * 0x10ULL + 8, kPlayer);
    Put(kPlayer + 0x18, kPlayerId);
    Put(kPlayer + 0x158, std::int32_t{174});
    Put(kPlayer + 0x1C0, kLand);
    Put(kLand + 0xD8, kPrisonerList);
    Put(kLand + 0xE4, std::int32_t{4});
    Put(kLand + 0x350, std::int64_t{1680000});
    for (std::size_t i = 0; i < kPrisonerIds.size(); ++i) {
      const auto character = kPrisonerBase + i * 0x1000;
      const auto extension = kExtensionBase + i * 0x1000;
      const auto relation = kRelationBase + i * 0x1000;
      Put(kCharacterSlots + kPrisonerIds[i] * 0x10ULL + 8, character);
      Put(kPrisonerList + i * sizeof(std::uint32_t), kPrisonerIds[i]);
      Put(character + 0x18, kPrisonerIds[i]);
      Put(character + 0x158, std::int32_t{i < 2 ? -1 : (i == 2 ? 2237 : 12690)});
      Put(character + 0x1A8, std::uintptr_t{0});
      Put(character + 0x1B0, extension);
      Put(extension + 0x288, relation);
      Put(relation, kPlayerId);
    }
    constexpr std::int32_t title_id = 2115;
    Put(kTitleSlots + title_id * 0x10ULL + 8, kTitle);
    Put(kTitle + 0x10, title_id);
    Put(kTitle + 0x48, kTitleTemplate);
    Put(kTitleTemplate + 0x64, std::int32_t{3});

    BufferPut(definition.data(), 0x10, kDefinitionOrdinal);
    BufferPut(definition.data(), 0x14, kDefinitionHash);
    BufferPut(definition.data(), 0x18, leaf::kPrisonerReleaseDefinitionKey12003.data());
    BufferPut(definition.data(), 0x28,
        static_cast<std::uint64_t>(leaf::kPrisonerReleaseDefinitionKey12003.size()));
    BufferPut(definition.data(), 0x30, std::uint64_t{64});
    BufferPut(definition.data(), 0x2258, option_rows.data());
    BufferPut(definition.data(), 0x2264, std::int32_t{kind == Case::old11 ? 11 : 13});
    BufferPut(definition.data(), 0x2290, &trigger_token);
    BufferPut(definition.data(), 0x2718, std::uint8_t{1});
    for (std::size_t i = 0; i < leaf::kPrisonerReleaseOptionKeys12003.size(); ++i)
      BufferPut(option_rows.data(), i * 0x730 + 0x368,
          static_cast<std::int32_t>(1000 + i));
    Range(definition.data(), definition.size());
    Range(option_rows.data(), option_rows.size());
    Range(selected.data(), selected.size());
    Range(leaf::kPrisonerReleaseDefinitionKey12003.data(),
          leaf::kPrisonerReleaseDefinitionKey12003.size());
  }
};
Fixture *active = nullptr;

bool ReadMemory(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto copy_range = [&](std::uintptr_t start, std::size_t length) {
    if (address < start || address - start > length || size > length - (address - start))
      return false;
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  };
  if (fixture.context != nullptr && copy_range(
      reinterpret_cast<std::uintptr_t>(fixture.context), old::kFactionGiftContextSizeV1))
    return true;
  for (const auto &[start, length] : fixture.readable_ranges)
    if (copy_range(start, length)) return true;
  auto *bytes = static_cast<std::byte *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto found = fixture.memory.find(address + i);
    if (found == fixture.memory.end()) return false;
    bytes[i] = found->second;
  }
  return true;
}
bool CaptureFrame(void *opaque, bridge::PlayerPrisonerFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}
void *PrimaryTitle(void *character) {
  return reinterpret_cast<std::uintptr_t>(character) == kPrisonerBase + 3 * 0x1000
      ? reinterpret_cast<void *>(kTitle) : nullptr;
}
void *Database() { return active; }
std::int32_t StableHash(void *database, const char *key, std::uint32_t size) {
  Require(database == active, "database identity");
  Require(std::string_view(key, size) == leaf::kPrisonerReleaseDefinitionKey12003,
          "definition key lookup");
  return kDefinitionHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Require(database == active && hash == kDefinitionHash, "definition lookup");
  return active->definition.data();
}
std::int32_t *Flag(void *table, std::int32_t *output, const void *view) {
  Require(table == active, "script identifier table");
  const char *data = nullptr;
  std::int32_t size = 0;
  std::memcpy(&data, view, sizeof(data));
  std::memcpy(&size, static_cast<const std::byte *>(view) + 8, sizeof(size));
  Require(size >= 0, "script identifier size");
  const auto key = std::string_view(data, static_cast<std::size_t>(size));
  for (std::size_t i = 0; i < leaf::kPrisonerReleaseOptionKeys12003.size(); ++i) {
    if (leaf::kPrisonerReleaseOptionKeys12003[i] == key) {
      *output = static_cast<std::int32_t>(1000 + i);
      ++active->flags;
      return output;
    }
  }
  Require(false, "unknown option key");
  return nullptr;
}
void *Construct(void *context, void *definition, std::int32_t actor,
                std::int32_t recipient, void *extras, bool redirect) {
  Require(definition == active->definition.data() && extras == nullptr && redirect,
          "two role constructor inputs");
  Require(actor == static_cast<std::int32_t>(kPlayerId) &&
          recipient == static_cast<std::int32_t>(kPrisonerIds[kSelectedOrdinal]),
          "two role identities");
  Require(active->context == nullptr, "owning context lifetime");
  active->context = context;
  ++active->constructed;
  auto &f = *active;
  f.BufferPut(context, 0, definition);
  f.BufferPut(context, 0x2D8, actor);
  f.BufferPut(context, 0x2DC, recipient);
  f.BufferPut(context, 0x2E0, std::int32_t{-1});
  f.BufferPut(context, 0x2E4, std::int32_t{-1});
  f.BufferPut(context, 0x2E8, std::int32_t{-1});
  f.BufferPut(context, 0x2EC,
      std::int32_t{actor + (f.kind == Case::puppet_role_mismatch ? 1 : 0)});
  f.BufferPut(context, 0x300, f.selected.data());
  f.BufferPut(context, 0x308, std::int32_t{13});
  f.BufferPut(context, 0x30C, std::int32_t{13});
  return context;
}
void Clear(void *context) {
  Require(context == active->context, "clear owns context");
  active->selected.fill(0);
}
void Refresh(void *context, bool recompute) {
  Require(context == active->context && recompute, "refresh finalized options");
  ++active->refreshed;
}
void Finalize(void *context) {
  Require(context == active->context, "finalize owns context");
  ++active->finalized;
  if (active->kind == Case::selected_change_prison) active->selected[5] = 1;
}
bool Gate(void *context, void *failure) {
  Require(context == active->context && failure == nullptr, "final gate context");
  ++active->gates;
  return active->kind != Case::gate_false;
}
void Cost(const void *definition_cost, const void *scope, std::int64_t *output) {
  Require(definition_cost == active->definition.data() + 0x40 &&
          scope == static_cast<std::byte *>(active->context) + 8,
          "cost definition and finalized scope");
  std::memcpy(output, kCosts.data(), sizeof(kCosts));
  ++active->costs;
}
bool AutoAccept(void *trigger, const void *scope) {
  Require(trigger == &active->trigger_token &&
          scope == static_cast<std::byte *>(active->context) + 8,
          "native auto accept trigger and scope");
  ++active->auto_accepts;
  return true;
}
void Destroy(void *context) {
  Require(context == active->context, "destroy owns context");
  ++active->destroyed;
  active->context = nullptr;
}

leaf::PrisonerReleasePreviewBindings12003 BindFixture(Fixture &fixture) {
  active = &fixture;
  leaf::PrisonerReleasePreviewBindings12003 b{};
  b.enabled = true;
  b.module_base = kModule;
  b.gift.enabled = true;
  b.gift.module_base = kModule;
  b.gift.get_database = Database;
  b.gift.stable_hash = StableHash;
  b.gift.lookup_definition = Lookup;
  b.gift.construct_two_role = Construct;
  b.gift.interaction.enabled = true;
  b.gift.interaction.refresh = Refresh;
  b.gift.interaction.finalize = Finalize;
  b.gift.interaction.validate = Gate;
  b.gift.interaction.evaluate_cost = Cost;
  b.gift.interaction.evaluate_trigger = AutoAccept;
  b.gift.interaction.destroy = Destroy;
  b.get_script_identifier_table = Database;
  b.lookup_script_identifier_id = Flag;
  b.clear_local_options = Clear;
  return b;
}

void RunCase(Case kind, std::string_view name, const std::filesystem::path &directory) {
  Fixture fixture(kind);
  fixture.Prepare();
  bridge::PlayerPrisonerCollectionAccessV1 collection_access{};
  collection_access.exact_build_admitted = true;
  collection_access.admitted_executable_sha256 = old::kExecutableSha256;
  collection_access.module_base = kModule;
  collection_access.current_thread_id = 8;
  collection_access.application_main_thread_id = 8;
  collection_access.read_lineage = true;
  collection_access.read_child_relation = true;
  collection_access.read_title_tier = true;
  collection_access.read_dread = true;
  collection_access.context = &fixture;
  collection_access.capture_frame = CaptureFrame;
  collection_access.read_memory = ReadMemory;
  collection_access.get_primary_title = PrimaryTitle;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(old::ReadPlayerPrisonerCollectionV1(collection_access, collection),
          "actual whole collection reader");
  Require(collection.available && collection.collection_complete &&
          collection.total_count == 4 && collection.returned_count == 4 &&
          collection.played_house_id == 174 && collection.played_dynasty_id == 174 &&
          collection.played_dread_raw == 1680000, "source 721 complete shape");
  for (std::size_t i = 0; i < kPrisonerIds.size(); ++i)
    Require(collection.rows[i].full_character_id == kPrisonerIds[i] &&
            collection.rows[i].jailer_character_id == kPlayerId &&
            collection.rows[i].source_ordinal == i &&
            !collection.rows[i].child_of_played_character,
            "source collection order and reverse custody");
  Require(collection.rows[2].house_id == 2237 && collection.rows[2].dynasty_id == 2237 &&
          collection.rows[3].house_id == 12690 && collection.rows[3].dynasty_id == 12077 &&
          collection.rows[3].primary_title_tier_raw == 3,
          "source collection lineage and title");

  const auto bindings = BindFixture(fixture);
  const leaf::PrisonerReleasePreviewAccess12003 access{
      8, 8, &fixture, CaptureFrame, ReadMemory};
  std::array<leaf::PrisonerReleasePreview12003,
      bridge::kPlayerPrisonerMaximumRowsV1> previews{};
  const bool complete = leaf::ReadPrisonerReleasePreview12003(bindings, access,
      kPlayerId, kPrisonerIds[kSelectedOrdinal], previews[kSelectedOrdinal]);
  const auto &preview = previews[kSelectedOrdinal];
  const bool expected_complete = kind == Case::gate_true || kind == Case::gate_false;
  Require(complete == expected_complete && preview.available == expected_complete,
          "release observation completeness");
  if (expected_complete) {
    Require(preview.can_send == (kind == Case::gate_true) && preview.auto_accept &&
            preview.send_costs_raw == kCosts && preview.raw_scale == 100000 &&
            preview.frame == fixture.frame && preview.unavailable_reason.empty(),
            "native true/false and all ten costs preserved");
    Require(preview.definition_key == leaf::kPrisonerReleaseDefinitionKey12003 &&
            preview.definition_stable_hash == static_cast<std::uint32_t>(kDefinitionHash) &&
            preview.definition_ordinal == kDefinitionOrdinal &&
            preview.actor_character_id == kPlayerId &&
            preview.recipient_character_id == kPrisonerIds[kSelectedOrdinal] &&
            preview.puppet_or_actor_character_id == kPlayerId &&
            preview.observed_definition_option_count == 13 &&
            preview.observed_context_option_count == 13 &&
            preview.selected_option_mask_bits == 0, "all 13 off and actual custody root");
    Require(fixture.constructed == 2 && fixture.destroyed == 2 && fixture.flags == 26 &&
            fixture.refreshed == 2 && fixture.finalized == 2 && fixture.gates == 2 &&
            fixture.costs == 2 && fixture.auto_accepts == 2,
            "two actual native source samples");
  } else {
    const std::string_view reason = kind == Case::old11 ? "option_definition_count_unexpected" :
        kind == Case::selected_change_prison ? "option_mask_unexpected" :
        "option_context_roles_unverified";
    Require(preview.unavailable_reason == reason && fixture.gates == 0 &&
            fixture.costs == 0 && fixture.auto_accepts == 0,
            "ordinary selection unavailable before final evaluation");
    const unsigned contexts = kind == Case::old11 ? 0U : 1U;
    Require(fixture.constructed == contexts && fixture.destroyed == contexts &&
            fixture.refreshed == contexts && fixture.finalized == contexts,
            "unavailable owning context is destroyed");
  }
  Require(fixture.context == nullptr, "all owning context lifetimes ended");

  // Synthetic legacy quote control: selected ordinal has an evaluated
  // unavailable result so the existing collection transport can bind it.
  // No native ransom reader is called or covered by this new compound.
  std::array<old::PlayerPrisonerRansomQuoteV1,
      bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  for (auto &quote : quotes) quote.failure = old::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  quotes[kSelectedOrdinal].failure = old::PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
  const auto value = old::SerializePlayerPrisonerCollectionPrivateV1(
      collection, fixture.frame.native_revision, quotes, true, &previews);
  Require(value.find("\"unconditional_release_preview\"") != std::string::npos &&
          value.find("release_preview_not_enabled_for_12002_ransom") == std::string::npos,
          "actual collection serializer consumes the new preview array");
  // The mailbox's command-result envelope contains this whole collection
  // value. Fixture metadata supplies only its read-only outer result fields;
  // every collection and preview field comes from the production readers.
  const auto wire = std::string{
      "{\"step\":\"query-player-prisoner-collection-private-v1-ransom-ordinal-2\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":"} +
      std::to_string(static_cast<unsigned>(kind) + 1U) +
      ",\"observation_revision\":" + std::to_string(fixture.frame.proof_epoch) +
      ",\"snapshot_revision\":" + std::to_string(fixture.frame.native_revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\"}";
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Require(stream.is_open(), "open whole wire fixture");
  stream << wire << '\n';
  Require(stream.good(), "write whole wire fixture");
  std::cout << "FIRST " << name << " whole_collection=4 release_available="
            << (preview.available ? "true" : "false") << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12003_prisoner_release_preview_test OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunCase(Case::gate_true, "gate_true", directory);
    RunCase(Case::gate_false, "gate_false", directory);
    RunCase(Case::old11, "old11", directory);
    RunCase(Case::selected_change_prison, "selected_change_prison", directory);
    RunCase(Case::puppet_role_mismatch, "puppet_role_mismatch", directory);
    std::cout << "FIRST groups=3 cases=5 complete\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST RED " << error.what() << '\n';
    return 1;
  }
}
