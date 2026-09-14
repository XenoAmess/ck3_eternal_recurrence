#include "xar_bridge/culture_innovation_source_adapter_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

struct Region {
  std::uintptr_t address = 0;
  std::vector<std::byte> bytes;
};

struct Fixture {
  static constexpr std::uintptr_t kModule = 0x10000000;
  static constexpr std::uintptr_t kCharacterStore = 0x20000000;
  static constexpr std::uintptr_t kCharacterSlots = 0x21000000;
  static constexpr std::uintptr_t kCultureStore = 0x22000000;
  static constexpr std::uintptr_t kCultureSlots = 0x23000000;
  static constexpr std::uintptr_t kCharacterFallback = 0x24000000;
  static constexpr std::uintptr_t kCultureFallback = 0x25000000;
  static constexpr std::uintptr_t kInnovationFallback = 0x26000000;
  static constexpr std::uintptr_t kPlayedCharacter = 0x30000000;
  static constexpr std::uintptr_t kHeadCharacter = 0x30001000;
  static constexpr std::uintptr_t kCulture = 0x40000000;
  static constexpr std::uintptr_t kEraStates = 0x50000000;
  static constexpr std::uintptr_t kEraDefinition0 = 0x51000000;
  static constexpr std::uintptr_t kEraDefinition1 = 0x51001000;
  static constexpr std::uintptr_t kInnovationStates = 0x60000000;
  static constexpr std::uintptr_t kInnovationDefinition0 = 0x61000000;
  static constexpr std::uintptr_t kInnovationDefinition1 = 0x61001000;
  static constexpr std::uintptr_t kInnovationDefinition2 = 0x61002000;
  static constexpr std::uintptr_t kActiveDefinitions = 0x62000000;
  static constexpr std::uintptr_t kCandidateDefinitions = 0x62001000;

  std::vector<Region> regions;
  std::uintptr_t next_string = 0x70000000;
  bool predicates_available = true;
  std::int32_t player_id = 7;
  std::int32_t culture_id = 3;
  std::int32_t head_id = 7;

  explicit Fixture(std::int32_t requested_player_id = 7,
                   std::int32_t requested_culture_id = 3,
                   std::int32_t requested_head_id = 7)
      : player_id(requested_player_id), culture_id(requested_culture_id),
        head_id(requested_head_id) {
    Add(kModule + 0x570C000, 0x1000);
    Add(kModule + 0x57C0400, 0x100);
    Add(kCharacterStore, 0x40);
    Add(kCharacterSlots, 64 * 0x10);
    Add(kCultureStore, 0x40);
    Add(kCultureSlots, 64 * 0x10);
    Add(kPlayedCharacter, 0x200);
    if (head_id != player_id) Add(kHeadCharacter, 0x200);
    Add(kCulture, 0x920);
    Add(kEraStates, 2 * ck3::kCultureEraStateStrideV1);
    Add(kEraDefinition0, 0x40);
    Add(kEraDefinition1, 0x40);
    Add(kInnovationStates, 3 * ck3::kCultureInnovationStateStrideV1);
    Add(kInnovationDefinition0, 0x220);
    Add(kInnovationDefinition1, 0x220);
    Add(kInnovationDefinition2, 0x220);
    Add(kActiveDefinitions, 3 * sizeof(std::uintptr_t));
    Add(kCandidateDefinitions, 3 * sizeof(std::uintptr_t));

    Write(kModule + ck3::kCultureSourceCharacterStoreSlotV1,
          kCharacterStore);
    Write(kModule + ck3::kCultureSourceCharacterFallbackSlotV1,
          kCharacterFallback);
    Write(kModule + ck3::kCultureSourceCultureStoreSlotV1, kCultureStore);
    Write(kModule + ck3::kCultureSourceCultureFallbackSlotV1,
          kCultureFallback);
    Write(kModule + ck3::kCultureSourceInnovationFallbackSlotV1,
          kInnovationFallback);
    Write(kCharacterStore + 0x20, kCharacterSlots);
    Write<std::int32_t>(kCharacterStore + 0x2C, 64);
    Write(kCultureStore + 0x20, kCultureSlots);
    Write<std::int32_t>(kCultureStore + 0x2C, 64);
    Write(kCharacterSlots +
              static_cast<std::uintptr_t>(player_id) * 0x10 + 0x08,
          kPlayedCharacter);
    Write<std::int32_t>(
        kPlayedCharacter + ck3::kCultureSourceCharacterIdentityOffsetV1,
        player_id);
    Write<std::int32_t>(
        kPlayedCharacter + ck3::kCultureSourceCharacterCultureIdOffsetV1,
        culture_id);
    if (head_id != player_id) {
      Write(kCharacterSlots +
                static_cast<std::uintptr_t>(head_id) * 0x10 + 0x08,
            kHeadCharacter);
      Write<std::int32_t>(
          kHeadCharacter + ck3::kCultureSourceCharacterIdentityOffsetV1,
          head_id);
    }
    Write(kCultureSlots +
              static_cast<std::uintptr_t>(culture_id) * 0x10 + 0x08,
          kCulture);
    Write<std::int32_t>(
        kCulture + ck3::kCultureSourceCultureIdentityOffsetV1, culture_id);
    Write<std::int32_t>(kCulture + ck3::kCultureHeadHandleOffsetV1,
                        head_id);

    Write(kCulture + ck3::kCultureEraStateVectorOffsetV1, kEraStates);
    Write<std::int32_t>(kCulture + ck3::kCultureEraStateCountOffsetV1, 2);
    ConfigureEra(0, kEraDefinition0, "culture_era_tribal", 10'000'000);
    ConfigureEra(1, kEraDefinition1, "culture_era_early_medieval",
                 2'500'000);

    Write(kCulture + ck3::kCultureInnovationStateVectorOffsetV1,
          kInnovationStates);
    Write<std::int32_t>(
        kCulture + ck3::kCultureInnovationStateCountOffsetV1, 3);
    ConfigureInnovation(0, kInnovationDefinition0, "innovation_motte",
                        kEraDefinition0, 10'000'000);
    ConfigureInnovation(1, kInnovationDefinition1,
                        "innovation_city_planning", kEraDefinition0,
                        1'250'000);
    ConfigureInnovation(2, kInnovationDefinition2, "innovation_catapult",
                        kEraDefinition1, 0);

    Write(kActiveDefinitions, kInnovationDefinition0);
    Write(kCulture + ck3::kCultureSourceActiveInnovationVectorOffsetV1,
          kActiveDefinitions);
    Write<std::int32_t>(
        kCulture + ck3::kCultureSourceActiveInnovationCountOffsetV1, 1);
    Write(kCandidateDefinitions + 0 * sizeof(std::uintptr_t),
          kInnovationDefinition0);
    Write(kCandidateDefinitions + 1 * sizeof(std::uintptr_t),
          kInnovationDefinition1);
    Write(kCandidateDefinitions + 2 * sizeof(std::uintptr_t),
          kInnovationDefinition2);
    Write(kCulture + ck3::kCultureInnovationDefinitionVectorOffsetV1,
          kCandidateDefinitions);
    Write<std::int32_t>(
        kCulture + ck3::kCultureInnovationDefinitionCountOffsetV1, 3);
    Write(kCulture + ck3::kCultureFascinationMarkerOffsetV1,
          kInnovationDefinition1);
    Write(kCulture + ck3::kCultureSpreadMarkerOffsetV1,
          kInnovationDefinition2);
  }

  void Add(std::uintptr_t address, std::size_t size) {
    regions.push_back({address, std::vector<std::byte>(size)});
  }

  Region *Find(std::uintptr_t address, std::size_t size) noexcept {
    const auto iterator = std::find_if(
        regions.begin(), regions.end(), [address, size](const Region &region) {
          return address >= region.address &&
              address - region.address <= region.bytes.size() &&
              size <= region.bytes.size() - (address - region.address);
        });
    return iterator == regions.end() ? nullptr : &*iterator;
  }

  template <typename T>
  void Write(std::uintptr_t address, T value) {
    Region *const region = Find(address, sizeof(value));
    assert(region != nullptr);
    std::memcpy(region->bytes.data() + (address - region->address), &value,
                sizeof(value));
  }

  void WriteBytes(std::uintptr_t address, const void *value,
                  std::size_t size) {
    Region *const region = Find(address, size);
    assert(region != nullptr);
    std::memcpy(region->bytes.data() + (address - region->address), value,
                size);
  }

  void WriteMsvcString(std::uintptr_t storage, std::string_view value) {
    assert(!value.empty());
    if (value.size() < 16) {
      WriteBytes(storage, value.data(), value.size());
      Write<std::size_t>(storage + 0x10, value.size());
      Write<std::size_t>(storage + 0x18, 15);
      return;
    }
    const auto allocation = next_string;
    next_string += 0x100;
    Add(allocation, value.size());
    WriteBytes(allocation, value.data(), value.size());
    Write(storage, allocation);
    Write<std::size_t>(storage + 0x10, value.size());
    Write<std::size_t>(storage + 0x18, value.size());
  }

  void ConfigureEra(std::int32_t index, std::uintptr_t definition,
                    std::string_view key, std::int64_t progress) {
    const auto state = kEraStates +
        static_cast<std::uintptr_t>(index) * ck3::kCultureEraStateStrideV1;
    Write(state + ck3::kCultureSourceEraDefinitionOffsetV1, definition);
    Write(state + ck3::kCultureSourceEraCultureOffsetV1, kCulture);
    Write(state + ck3::kCultureSourceEraProgressOffsetV1, progress);
    Write<std::int32_t>(
        definition + ck3::kCultureSourceDefinitionIndexOffsetV1, index);
    WriteMsvcString(
        definition + ck3::kCultureSourceDefinitionStableKeyOffsetV1, key);
  }

  void ConfigureInnovation(std::int32_t index, std::uintptr_t definition,
                           std::string_view key,
                           std::uintptr_t era_definition,
                           std::int64_t progress) {
    const auto state = kInnovationStates + static_cast<std::uintptr_t>(index) *
        ck3::kCultureInnovationStateStrideV1;
    Write(state + ck3::kInnovationCultureOffsetV1, kCulture);
    Write(state + ck3::kInnovationDefinitionOffsetV1, definition);
    Write(state + ck3::kInnovationProgressOffsetV1, progress);
    Write<std::int32_t>(
        definition + ck3::kCultureSourceDefinitionIndexOffsetV1, index);
    WriteMsvcString(
        definition + ck3::kCultureSourceDefinitionStableKeyOffsetV1, key);
    Write(definition + ck3::kCultureSourceInnovationEraDefinitionOffsetV1,
          era_definition);
  }

  static bool ReadMemory(void *context, std::uintptr_t address, void *output,
                         std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    Region *const region = fixture.Find(address, size);
    if (region == nullptr || output == nullptr) return false;
    std::memcpy(output,
                region->bytes.data() + (address - region->address), size);
    return true;
  }

  static bool CanGainProgress(void *context, std::uintptr_t,
                              std::uintptr_t state, bool &output) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    if (!fixture.predicates_available) return false;
    output = state != kInnovationStates;
    return true;
  }

  static bool CanBeFascination(void *context, std::uintptr_t,
                               std::uintptr_t definition, std::uintptr_t,
                               bool &output) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    if (!fixture.predicates_available) return false;
    output = definition != kInnovationDefinition0;
    return true;
  }

  ck3::CultureInnovationSourceAdapterContextV1 Context() noexcept {
    ck3::CultureInnovationSourceAdapterContextV1 result{};
    result.module_base = kModule;
    result.native.context = this;
    result.native.read_memory = ReadMemory;
    result.native.can_gain_progress = CanGainProgress;
    result.native.can_be_fascination = CanBeFascination;
    return result;
  }
};

std::string_view Key(const game::CultureInnovationStableKeyV1 &key) {
  return ck3::CultureInnovationStableKeyViewV1(key);
}

void TestReadsLiveContainerSemantics() {
  Fixture fixture;
  auto context = fixture.Context();
  ck3::CultureInnovationSourceSampleV1 output{};
  assert(ck3::ReadExactBuildCultureInnovationSourceV1(
             context, Fixture::kPlayedCharacter, output) ==
         ck3::CultureInnovationSourceAdapterFailureV1::none);
  assert(context.last_failure ==
         ck3::CultureInnovationSourceAdapterFailureV1::none);
  assert(output.player_character_id == 7);
  assert(output.player_identity_round_trip);
  assert(output.state.culture_id == 3);
  assert(output.state.culture_head_presence ==
         game::CultureInnovationPresenceV1::present);
  assert(output.state.culture_head_character_id == 7);
  assert(output.state.is_player_culture_head);
  assert(output.state.fascination_presence ==
         game::CultureInnovationPresenceV1::present);
  assert(Key(output.state.current_fascination_key) ==
         "innovation_city_planning");
  assert(output.state.era_count == 2);
  assert(Key(output.state.eras[0].key) == "culture_era_tribal");
  assert(output.state.eras[0].progress_raw == 10'000'000);
  assert(Key(output.state.eras[1].key) ==
         "culture_era_early_medieval");
  assert(output.state.eras[1].progress_raw == 2'500'000);
  assert(output.state.innovation_count == 3);

  const auto &motte = output.state.innovations[0];
  assert(Key(motte.key) == "innovation_motte");
  assert(Key(motte.era_key) == "culture_era_tribal");
  assert(Key(motte.group_key) == "culture_group_military");
  assert(Key(motte.skill_key) == "stewardship");
  assert(motte.progress_raw == 10'000'000);
  assert(motte.is_active);
  assert(!motte.can_gain_progress);
  assert(!motte.can_be_fascination);
  assert(!motte.is_fascination);
  assert(!motte.has_spread_marker);

  const auto &planning = output.state.innovations[1];
  assert(Key(planning.key) == "innovation_city_planning");
  assert(planning.progress_raw == 1'250'000);
  assert(!planning.is_active);
  assert(planning.can_gain_progress);
  assert(planning.can_be_fascination);
  assert(planning.is_fascination);
  assert(!planning.has_spread_marker);

  const auto &catapult = output.state.innovations[2];
  assert(Key(catapult.era_key) == "culture_era_early_medieval");
  assert(Key(catapult.skill_key) == "learning");
  assert(catapult.progress_raw == 0);
  assert(catapult.has_spread_marker);
}

void TestLegalZeroAndAbsentAreObserved() {
  Fixture fixture(0, 0, 0);
  fixture.Write<std::int64_t>(
      Fixture::kEraStates + ck3::kCultureSourceEraProgressOffsetV1, 0);
  fixture.Write<std::int64_t>(
      Fixture::kInnovationStates + ck3::kInnovationProgressOffsetV1, 0);
  auto context = fixture.Context();
  ck3::CultureInnovationSourceSampleV1 output{};
  assert(ck3::ReadExactBuildCultureInnovationSourceV1(
             context, Fixture::kPlayedCharacter, output) ==
         ck3::CultureInnovationSourceAdapterFailureV1::none);
  assert(output.player_character_id == 0);
  assert(output.state.culture_id == 0);
  assert(output.state.culture_head_character_id == 0);
  assert(output.state.is_player_culture_head);
  assert(output.state.eras[0].progress_raw == 0);
  assert(output.state.innovations[0].progress_raw == 0);

  fixture.Write<std::int32_t>(
      Fixture::kCulture + ck3::kCultureHeadHandleOffsetV1, -1);
  fixture.Write(Fixture::kCulture + ck3::kCultureFascinationMarkerOffsetV1,
                Fixture::kInnovationFallback);
  fixture.Write(Fixture::kCulture + ck3::kCultureSpreadMarkerOffsetV1,
                Fixture::kInnovationFallback);
  assert(ck3::ReadExactBuildCultureInnovationSourceV1(
             context, Fixture::kPlayedCharacter, output) ==
         ck3::CultureInnovationSourceAdapterFailureV1::none);
  assert(output.state.culture_head_presence ==
         game::CultureInnovationPresenceV1::absent);
  assert(output.state.culture_head_character_id == -1);
  assert(!output.state.is_player_culture_head);
  assert(output.state.fascination_presence ==
         game::CultureInnovationPresenceV1::absent);
  assert(Key(output.state.current_fascination_key).empty());
  assert(std::none_of(
      output.state.innovations.begin(),
      output.state.innovations.begin() + output.state.innovation_count,
      [](const auto &row) {
        return row.is_fascination || row.has_spread_marker;
      }));
}

void TestTypedFailuresAndCallback() {
  {
    Fixture fixture;
    fixture.Write<std::int32_t>(
        Fixture::kCulture + ck3::kCultureSourceCultureIdentityOffsetV1, 99);
    auto context = fixture.Context();
    ck3::CultureInnovationSourceSampleV1 output{};
    assert(ck3::ReadExactBuildCultureInnovationSourceV1(
               context, Fixture::kPlayedCharacter, output) ==
           ck3::CultureInnovationSourceAdapterFailureV1::culture_store_invalid);
    assert(!output.player_identity_round_trip);
  }
  {
    Fixture fixture;
    fixture.Write<std::int64_t>(
        Fixture::kEraStates + ck3::kCultureSourceEraProgressOffsetV1,
        10'000'001);
    auto context = fixture.Context();
    ck3::CultureInnovationSourceSampleV1 output{};
    assert(ck3::ReadExactBuildCultureInnovationSourceV1(
               context, Fixture::kPlayedCharacter, output) ==
           ck3::CultureInnovationSourceAdapterFailureV1::era_progress_invalid);
  }
  {
    Fixture fixture;
    fixture.WriteMsvcString(
        Fixture::kInnovationDefinition0 +
            ck3::kCultureSourceDefinitionStableKeyOffsetV1,
        "modded_innovation");
    auto context = fixture.Context();
    ck3::CultureInnovationSourceSampleV1 output{};
    assert(!ck3::ReadExactBuildCultureInnovationNativeSourceV1(
        &context, Fixture::kPlayedCharacter, output));
    assert(context.last_failure ==
           ck3::CultureInnovationSourceAdapterFailureV1::
               innovation_metadata_unavailable);
    assert(ck3::CultureInnovationSourceAdapterFailureKeyV1(
               context.last_failure) == "innovation_metadata_unavailable");
  }
  {
    Fixture fixture;
    fixture.predicates_available = false;
    auto context = fixture.Context();
    ck3::CultureInnovationSourceSampleV1 output{};
    assert(ck3::ReadExactBuildCultureInnovationSourceV1(
               context, Fixture::kPlayedCharacter, output) ==
           ck3::CultureInnovationSourceAdapterFailureV1::
               native_predicate_unavailable);
  }
  {
    ck3::CultureInnovationSourceSampleV1 output{};
    assert(!ck3::ReadExactBuildCultureInnovationNativeSourceV1(
        nullptr, Fixture::kPlayedCharacter, output));
  }
}

void TestDirectBindingsAreConcrete() {
  const auto direct = ck3::DirectCultureInnovationSourceNativeAccessV1();
  assert(direct.read_memory != nullptr);
  assert(direct.can_gain_progress != nullptr);
  assert(direct.can_be_fascination != nullptr);
}

void TestResolvesPlayedCharacterThroughFrozenStore() {
  Fixture fixture(0, 0, 0);
  auto context = fixture.Context();
  std::uintptr_t played_character = 0;
  assert(ck3::ResolveExactBuildCultureInnovationPlayedCharacterV1(
      context, 0, played_character));
  assert(played_character == Fixture::kPlayedCharacter);
  assert(context.last_failure ==
         ck3::CultureInnovationSourceAdapterFailureV1::none);

  played_character = Fixture::kPlayedCharacter;
  assert(!ck3::ResolveExactBuildCultureInnovationPlayedCharacterV1(
      context, 1, played_character));
  assert(played_character == 0);
  assert(context.last_failure ==
         ck3::CultureInnovationSourceAdapterFailureV1::
             player_identity_round_trip_failed);
}

} // namespace

int main() {
  TestReadsLiveContainerSemantics();
  TestLegalZeroAndAbsentAreObserved();
  TestTypedFailuresAndCallback();
  TestDirectBindingsAreConcrete();
  TestResolvesPlayedCharacterThroughFrozenStore();
  std::cout << "culture_innovation_source_adapter_v1_test: 5/5 GREEN\n";
  return 0;
}
