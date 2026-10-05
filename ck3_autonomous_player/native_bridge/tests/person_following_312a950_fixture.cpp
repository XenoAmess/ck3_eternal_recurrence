#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t address; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &entry : denied) count += entry.attempts;
    return count;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &entry : memory.denied) {
      if (begin < entry.address + entry.size && entry.address < begin + size) {
        ++entry.attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;
constexpr std::uint32_t kGovernmentBit29 = 0x20000000U;
constexpr std::uint32_t kLandA = 0xAA000001U;
constexpr std::uint32_t kLandB = 0xBB000002U;
constexpr std::uint32_t kRelatedRequested = 0xBA000001U;

// All observed bytes are fixed before the two whole queries. Government and
// first-Land sources deliberately keep their different death/live priorities.
// The minimum has no fabricated PC or native evaluator/getter/initializer.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *state = memory.Allocate(0x580);
  void *living = memory.Allocate(0x400);
  void *death = memory.Allocate(0x90);
  void *living_ids = memory.Allocate(2 * 4);
  void *death_ids = memory.Allocate(4);
  void *living_government = memory.Allocate(0x44);
  void *death_government = memory.Allocate(0x44);
  void *global_government = memory.Allocate(0x44);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *character_store = memory.Allocate(0x30);
  void *character_table = memory.Allocate(2 * 16);
  void *wrong_generation_character = memory.Allocate(0x1D8);
  void *related_character = memory.Allocate(0x1D8);
  void *related_living = memory.Allocate(0x400);
  void *related_carrier = memory.Allocate(0xD0);
  void *government_fallback_slot = memory.Allocate(8);
  void *land_storage_slot = memory.Allocate(8);
  void *land_fallback_slot = memory.Allocate(8);
  void *land_store = memory.Allocate(0x30);
  void *land_table = memory.Allocate(3 * 16);
  void *land_a = memory.Allocate(0x320);
  void *land_fallback = memory.Allocate(0x320);
  void *provider_slot = memory.Allocate(8);
  void *provider = memory.Allocate(0x16A0);

  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.following_312a950;
    b.enabled = true;
    b.character_storage_slot = character_storage_slot;
    b.character_fallback_slot = character_fallback_slot;
    b.government_fallback_slot = government_fallback_slot;
    b.land_storage_slot = land_storage_slot;
    b.land_fallback_slot = land_fallback_slot;
    b.provider_slot = provider_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1B0, state);
    memory.Put(character, 0x1C0, living);
    memory.Put(living, 0x3F8, living_government);
    memory.Put(death, 0x88, death_government);
    memory.Put(living_government, 0x40, kGovernmentBit29);
    memory.Put(death_government, 0x40, kGovernmentBit29);
    memory.Put(global_government, 0x40, kGovernmentBit29);
    memory.Put(government_fallback_slot, 0, global_government);
    memory.Put(character_storage_slot, 0, character_store);
    memory.Put(character_fallback_slot, 0, character);
    memory.Put(character_store, 0x20, character_table);
    memory.Put(character_store, 0x2C, std::uint32_t{2});
    memory.Put(character_table, 16 + 8, wrong_generation_character);
    memory.Put(wrong_generation_character, 0x18, std::uint32_t{0xCA000001U});
    memory.Put(wrong_generation_character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(related_character, 0x18, std::uint32_t{0xDA000007U});
    memory.Put(related_character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(related_character, 0x1C0, related_living);
    memory.Put(related_living, 0x3F8, living_government);
    memory.Put(related_carrier, 0xC8, kRelatedRequested);
    memory.Put(living, 0x1E0, living_ids);
    memory.Put(living, 0x1EC, std::int32_t{1});
    memory.Put(living_ids, 0, kLandA);
    memory.Put(living_ids, 4, kLandB);
    memory.Put(death, 0x68, death_ids);
    memory.Put(death, 0x74, std::int32_t{1});
    memory.Put(death_ids, 0, kLandB);
    memory.Put(land_storage_slot, 0, land_store);
    memory.Put(land_fallback_slot, 0, land_fallback);
    memory.Put(land_store, 0x20, land_table);
    memory.Put(land_store, 0x2C, std::uint32_t{3});
    memory.Put(land_table, 16 + 8, land_a);
    memory.Put(land_a, 0x10, kLandA);
    memory.Put(land_a, 0x14, std::uint32_t{0x4C616E64U});
    memory.Put(land_a, 0x318, std::int64_t{0});
    memory.Put(land_fallback, 0x10, std::int32_t{-1});
    memory.Put(land_fallback, 0x14, std::uint32_t{0});
    memory.Put(provider_slot, 0, provider);

    // Actual empty headers for the existing always-collected source leaves.
    void *first = memory.Allocate(0x220);
    void *second = memory.Allocate(0x150);
    bindings.first_storage_slot = memory.Allocate(8);
    bindings.first_fallback_slot = memory.Allocate(8);
    bindings.second_storage_slot = memory.Allocate(8);
    bindings.second_fallback_slot = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.first_fallback_slot), 0, first);
    memory.Put(const_cast<void *>(bindings.second_fallback_slot), 0, second);
    bindings.lifestyle_fallback_header = memory.Allocate(0x10);
    bindings.house_extra_fallback_header = memory.Allocate(0x10);
    bindings.source_fallback_header = memory.Allocate(0x10);
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.following_312a950.enabled,
            "following312a950 source binding disabled");
    Require(!bindings.gated_temporary_tail.enabled && !bindings.after_gated_tail.enabled &&
                !bindings.provider192_and2920850.enabled && !bindings.following_2920b50.enabled &&
                !bindings.following_2bca620.enabled &&
                !bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled &&
                !bindings.trait_stage.enabled && !bindings.middle_helpers.enabled &&
                !bindings.tail_prefix_enabled && !bindings.helper_2922070_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "following312a950 fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "following312a950 whole snapshots differ in fixed frame");
    Require(first.following_government_land_312a950.has_value(), "following312a950 source leaf absent");
    Require(memory.Attempts() == 0, "following312a950 unused numeric operands were demanded");
    return first;
  }
};
void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("following312a950-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("following312a950 wire write failed");
}
void EarlyKnownZero(const auto &leaf, const char *selection) {
  Require(leaf.ready && leaf.government_source.ready && leaf.stage_selection == selection &&
              !leaf.first_land_source && !leaf.land_resolution &&
              !leaf.mode3_classifier && !leaf.provider_selection,
          "following312a950 early known zero must leave all later groups unobserved");
}
void LaterKnownZero(const auto &leaf, const char *selection) {
  Require(leaf.ready && leaf.government_source.ready && leaf.character_state_present == true &&
              leaf.stage_selection == selection && leaf.first_land_source &&
              leaf.first_land_source->ready && leaf.land_resolution &&
              leaf.land_resolution->ready && !leaf.mode3_classifier && !leaf.provider_selection,
          "following312a950 observed Land skip must not demand mode3/provider groups");
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &b = bindings.following_312a950;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && b.enabled && b.character_storage_slot == address(0x5C67568) &&
              b.character_fallback_slot == address(0x5C67570) &&
              b.government_fallback_slot == address(0x5D1E2A8) &&
              b.land_storage_slot == address(0x5D1DAF8) && b.land_fallback_slot == address(0x5D1DAE0) &&
              b.provider_slot == address(0x5C670F8),
          "following312a950 exact-build bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").following_312a950.enabled,
          "following312a950 exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Put(f.living_government, 0x40, std::uint32_t{0});
    f.memory.Deny(f.living, 0x1E0, 8);
    f.memory.Deny(f.living, 0x1EC, 4);
    f.memory.Deny(f.land_storage_slot, 0, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    Require(snapshot.ready && leaf.government_source.flags_raw_u32 == 0U &&
                leaf.government_source.selection == "living_1c0_3f8" &&
                leaf.government_source.selection_native_index == 0 &&
                !leaf.character_state_present,
            "following312a950 false bit29 must precede character-state and first Land demand");
    EarlyKnownZero(leaf, "government_bit29_false");
    Save(directory, "government-bit29-false", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.memory.Deny(f.living, 0x1E0, 8);
    f.memory.Deny(f.living, 0x1EC, 4);
    f.memory.Deny(f.land_storage_slot, 0, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    Require(snapshot.ready && leaf.character_state_present == false &&
                leaf.government_source.flags_raw_u32 == kGovernmentBit29,
            "following312a950 bit29 true must observe absent current state before first Land");
    EarlyKnownZero(leaf, "character_1b0_absent");
    Save(directory, "character-state-absent", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.memory.Put(f.character, 0x1B8, f.related_carrier);
    f.memory.Put(f.character_fallback_slot, 0, f.related_character);
    f.memory.Put(f.land_storage_slot, 0, static_cast<void *>(nullptr));
    f.memory.Deny(f.related_living, 0x1E0, 8);
    f.memory.Deny(f.related_living, 0x1EC, 4);
    f.memory.Deny(f.land_fallback, 0x10, 4);
    f.memory.Deny(f.land_fallback, 0x318, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    LaterKnownZero(leaf, "first_land_invalid");
    Require(snapshot.ready && leaf.government_source.selection_native_index == 1 &&
                leaf.government_source.selection == "living_1c0_3f8" &&
                leaf.government_source.selected_character_identity &&
                leaf.first_land_source->selection == "none" &&
                leaf.first_land_source->living_present == false &&
                leaf.first_land_source->death_present == false &&
                leaf.first_land_source->full_id_raw == -1 &&
                leaf.land_resolution->selection == "native_fallback" &&
                !leaf.land_resolution->requested_full_id_raw &&
                !leaf.land_resolution->selected_full_id_raw &&
                leaf.land_resolution->magic_u32 == 0U &&
                leaf.land_resolution->admitted == false && !leaf.land_resolution->full_id_raw &&
                !leaf.land_resolution->balance_raw_q64,
            "following312a950 generation miss must select actual related fallback; null Land store skips ID");
    Save(directory, "related-generation-fallback-land-bad-magic", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.land_storage_slot, 0, static_cast<void *>(nullptr));
    f.memory.Put(f.land_fallback, 0x14, std::uint32_t{0x4C616E64U});
    f.memory.Deny(f.land_fallback, 0x318, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    LaterKnownZero(leaf, "first_land_invalid");
    Require(snapshot.ready && leaf.land_resolution->selection == "native_fallback" &&
                leaf.land_resolution->magic_u32 == 0x4C616E64U &&
                leaf.land_resolution->full_id_raw == -1 &&
                leaf.land_resolution->admitted == false && !leaf.land_resolution->balance_raw_q64,
            "following312a950 Land full-ID minus-one must skip balance after magic");
    Save(directory, "land-id-minus-one", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.land_a, 0x318, std::numeric_limits<std::int64_t>::max());
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    LaterKnownZero(leaf, "first_land_nonnegative");
    Require(snapshot.ready && leaf.land_resolution->selection == "registry_full_id_10" &&
                leaf.land_resolution->requested_full_id_raw == static_cast<std::int32_t>(kLandA) &&
                leaf.land_resolution->selected_full_id_raw == static_cast<std::int32_t>(kLandA) &&
                leaf.land_resolution->admitted == true &&
                leaf.land_resolution->balance_raw_q64 == std::numeric_limits<std::int64_t>::max(),
            "following312a950 nonnegative signed Land balance must give known zero");
    Save(directory, "land-nonnegative", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.land_a, 0x318, std::int64_t{-1});
    f.memory.Deny(f.provider, 0x12D4, 4);
    f.memory.Deny(f.provider, 0x12C8, 8);
    f.memory.Deny(f.provider, 0x1690, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    Require(!snapshot.ready && !leaf.ready &&
                leaf.stage_selection == "negative_land_mode3_income_unobserved" &&
                leaf.land_resolution && leaf.land_resolution->ready &&
                leaf.land_resolution->balance_raw_q64 == -1 &&
                leaf.mode3_classifier && !leaf.mode3_classifier->ready &&
                !leaf.mode3_classifier->income_q64 && !leaf.mode3_classifier->index_raw_i32 &&
                leaf.mode3_classifier->reason == "mode3_income_2bca580" &&
                leaf.provider_selection && leaf.provider_selection->provider_loaded == true &&
                !leaf.provider_selection->ready && !leaf.provider_selection->count_raw &&
                !leaf.provider_selection->selection && !leaf.provider_selection->definition_identity &&
                !leaf.provider_selection->definition_magic_u32 && !leaf.provider_selection->admitted &&
                !leaf.provider_selection->pc.property_identity && !leaf.provider_selection->pc.property_block,
            "following312a950 negative Land must expose exact mode3 income gap without downstream provider fields");
    Save(directory, "negative-land-mode3-gap", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1D0, f.death);
    f.memory.Put(f.living_government, 0x40, std::uint32_t{0});
    f.memory.Put(f.living, 0x1EC, std::int32_t{-2});
    f.memory.Deny(f.living, 0x3F8, 8);
    f.memory.Deny(f.living_ids, 4, 4);
    f.memory.Deny(f.death, 0x68, 8);
    f.memory.Deny(f.death, 0x74, 4);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    LaterKnownZero(leaf, "first_land_nonnegative");
    Require(snapshot.ready && leaf.government_source.selection == "death_1d0_88" &&
                leaf.government_source.selection_native_index == 0 &&
                leaf.government_source.flags_raw_u32 == kGovernmentBit29 &&
                leaf.first_land_source->selection == "living_1c0" &&
                leaf.first_land_source->count_raw == -2 &&
                leaf.first_land_source->array_present == true &&
                leaf.first_land_source->full_id_raw == static_cast<std::int32_t>(kLandA) &&
                !leaf.first_land_source->death_present && leaf.land_resolution->balance_raw_q64 == 0,
            "following312a950 government death-first and first-Land live-first must stay distinct");
    Save(directory, "death-government-live-land", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1D0, f.death);
    f.memory.Put(f.living, 0x1EC, std::int32_t{0});
    f.memory.Deny(f.living, 0x1E0, 8);
    f.memory.Deny(f.death, 0x68, 8);
    f.memory.Deny(f.death, 0x74, 4);
    f.memory.Deny(f.land_store, 0x20, 8);
    f.memory.Deny(f.land_fallback, 0x10, 4);
    f.memory.Deny(f.land_fallback, 0x318, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_government_land_312a950;
    LaterKnownZero(leaf, "first_land_invalid");
    Require(snapshot.ready && leaf.first_land_source->selection == "living_1c0" &&
                leaf.first_land_source->count_raw == 0 && !leaf.first_land_source->array_present &&
                leaf.first_land_source->full_id_raw == -1 && !leaf.first_land_source->death_present &&
                leaf.land_resolution->selection == "native_fallback" &&
                leaf.land_resolution->requested_full_id_raw == -1 &&
                leaf.land_resolution->magic_u32 == 0U && leaf.land_resolution->admitted == false,
            "following312a950 live count zero must skip death but still resolve minus-one through actual fallback");
    Save(directory, "live-zero-count-no-death", snapshot);
  }
}
} // namespace

void RunFollowing312a950Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
