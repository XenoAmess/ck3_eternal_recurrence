#include "xar_bridge/character_interaction_proposal_payload_source_extension_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;
using Failure = game::CharacterInteractionProposalPayloadSourceFailureV1;
using Result = game::ReadCharacterInteractionProposalPayloadSourceResultV1;

constexpr std::int32_t kActor = 0x01000002;
constexpr std::int32_t kRecipient = 0x02000003;
constexpr std::int32_t kGuardian = 0x03000004;
constexpr std::int32_t kWard = 0x04000005;
constexpr std::int32_t kVassal = 0x05000006;
constexpr std::int32_t kPrisoner = 0x06000007;
constexpr std::int32_t kTitleOne = 0x07000008;
constexpr std::int32_t kTitleTwo = 0x08000009;
constexpr std::uintptr_t kFixtureModule = 0x10000000;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "proposal payload source fixture failed at line " +
        std::to_string(location.line()));
  }
}

template <std::size_t N, typename T>
void Store(std::array<std::byte, N> &memory, std::size_t offset,
           const T &value) {
  Require(offset <= memory.size() && sizeof(value) <= memory.size() - offset);
  std::memcpy(memory.data() + offset, &value, sizeof(value));
}

void AssignSnapshot(
    std::array<char, game::kCharacterInteractionPreviewSnapshotIdCapacityV1>
        &output,
    std::string_view value) {
  Require(value.size() < output.size());
  std::copy(value.begin(), value.end(), output.begin());
}

struct Fixture {
  std::array<std::byte, 0x338> interaction_context{};
  std::array<std::byte, 0x2A58> definition{};
  std::array<std::byte, 0x20> grant_titles_offer{};
  std::array<std::uint8_t, 32> selected_options{};
  std::array<std::int32_t, 4> selected_titles{};

  std::array<std::byte, 0x30> character_storage{};
  std::array<std::array<std::byte, 0x10>, 16> character_slots{};
  std::array<std::array<std::byte, 0x20>, 6> characters{};
  void *character_storage_pointer = character_storage.data();

  std::array<std::byte, 0x30> title_storage{};
  std::array<std::array<std::byte, 0x10>, 16> title_slots{};
  std::array<std::array<std::byte, 0x18>, 2> titles{};
  void *title_storage_pointer = title_storage.data();

  game::CharacterInteractionPreviewV1 preview{};
  ck3::CharacterInteractionProposalPayloadCollectorMemoryV1 collector{};
  std::int32_t capture_calls = 0;
  bool capture_succeeds = true;

  Fixture() {
    void *character_slots_pointer = character_slots.data();
    Store(character_storage, 0x20, character_slots_pointer);
    Store(character_storage, 0x2C, std::int32_t{16});
    void *title_slots_pointer = title_slots.data();
    Store(title_storage, 0x20, title_slots_pointer);
    Store(title_storage, 0x2C, std::int32_t{16});

    AddCharacter(0, kActor);
    AddCharacter(1, kRecipient);
    AddCharacter(2, kGuardian);
    AddCharacter(3, kWard);
    AddCharacter(4, kVassal);
    AddCharacter(5, kPrisoner);
    AddTitle(0, kTitleOne);
    AddTitle(1, kTitleTwo);

    preview.status = game::CharacterInteractionPreviewStatusV1::available;
    preview.unavailable_reason = game::CharacterInteractionPreviewFailureV1::none;
    AssignSnapshot(preview.snapshot_id, "diplomatic-payload-frame-44");
    preview.public_revision = 44;
    preview.native_revision = 144;
    preview.proof_epoch = 244;
    preview.date_raw = 53'211'600;
    preview.roles.actor_character_id = kActor;
    preview.roles.recipient_character_id = kRecipient;
    preview.readiness = {true, true, true, true, true, true, true, true};

    collector.interaction_context = interaction_context.data();
    collector.frame.snapshot_id = preview.snapshot_id;
    collector.frame.public_revision = preview.public_revision;
    collector.frame.native_revision = preview.native_revision;
    collector.frame.proof_epoch = preview.proof_epoch;
    collector.frame.date_raw = preview.date_raw;
    collector.frame.paused = true;
    collector.frame.map_ready = true;
    collector.frame.has_played_character = true;
    collector.frame.played_character_alive = true;
    collector.frame.played_character_id = kActor;

    void *definition_pointer = definition.data();
    Store(interaction_context, 0x00, definition_pointer);
    Store(interaction_context, 0x2D8, kActor);
    Store(interaction_context, 0x2DC, kRecipient);
    Store(interaction_context, 0x2E0, std::int32_t{-1});
    Store(interaction_context, 0x2E4, std::int32_t{-1});
    Store(interaction_context, 0x2E8, std::int32_t{-1});
    void *option_data = selected_options.data();
    Store(interaction_context, 0x300, option_data);
    Store(interaction_context, 0x308, std::int32_t{32});
    Store(interaction_context, 0x30C, std::int32_t{0});
  }

  void AddCharacter(std::size_t object_index, std::int32_t id) {
    Store(characters[object_index], 0x18, id);
    void *object = characters[object_index].data();
    const auto slot = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(character_slots[slot], 0x08, object);
  }

  void AddTitle(std::size_t object_index, std::int32_t id) {
    Store(titles[object_index], 0x10, id);
    void *object = titles[object_index].data();
    const auto slot = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(title_slots[slot], 0x08, object);
  }

  void Configure(std::string_view key) {
    preview.definition.canonical_key.assign(key);
    preview.definition.deterministic_key_hash = 0xD15EA5EDU;
    preview.definition.runtime_ordinal = 91;
    selected_options.fill(0);
    Store(interaction_context, 0x2E0, std::int32_t{-1});
    Store(interaction_context, 0x2E4, std::int32_t{-1});
    Store(interaction_context, 0x2E8, std::int32_t{-1});
    Store(interaction_context, 0x330, static_cast<void *>(nullptr));

    std::int32_t option_count = 0;
    if (key == "educate_child_interaction") {
      Store(interaction_context, 0x2E0, kGuardian);
      Store(interaction_context, 0x2E4, kWard);
      option_count = 4;
    } else if (key == "offer_ward_interaction") {
      Store(interaction_context, 0x2E0, kWard);
      Store(interaction_context, 0x2E4, kGuardian);
      option_count = 4;
    } else if (key == "offer_guardianship_interaction") {
      Store(interaction_context, 0x2E0, kGuardian);
      Store(interaction_context, 0x2E4, kWard);
      option_count = 4;
    } else if (key == "grant_titles_interaction") {
      void *offer = grant_titles_offer.data();
      void *vtable = reinterpret_cast<void *>(
          kFixtureModule +
          ck3::kCharacterInteractionProposalPayloadGrantTitlesOfferVtableRvaV1);
      void *ids = selected_titles.data();
      selected_titles = {kTitleOne, kTitleTwo, -1, -1};
      Store(grant_titles_offer, 0x00, vtable);
      Store(grant_titles_offer, 0x08, ids);
      Store(grant_titles_offer, 0x10, std::int32_t{4});
      Store(grant_titles_offer, 0x14, std::int32_t{2});
      Store(interaction_context, 0x330, offer);
    } else if (key == "grant_vassal_interaction") {
      Store(interaction_context, 0x2E0, kVassal);
    } else if (key == "ransom_interaction") {
      Store(interaction_context, 0x2E4, kPrisoner);
      selected_options[2] = 1; // exact authored `gold` row
      option_count = 7;
    }
    Store(interaction_context, 0x30C, option_count);
    Store(definition, 0x2554, option_count);
  }
};

bool Capture(
    void *context, std::string_view key, std::int32_t actor,
    std::int32_t recipient,
    ck3::CharacterInteractionProposalPayloadCollectorMemoryV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.capture_calls;
  if (!fixture.capture_succeeds || key != fixture.preview.definition.canonical_key ||
      actor != kActor || recipient != kRecipient) {
    return false;
  }
  output = fixture.collector;
  return true;
}

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  std::memcpy(output, address, size);
  return true;
}

bool LookupDefinition(void *context, std::string_view key,
                      void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (key != fixture.preview.definition.canonical_key) return false;
  output = fixture.definition.data();
  return true;
}

ck3::CharacterInteractionProposalPayloadSourceEnvironmentV1 Environment(
    Fixture &fixture) {
  return {true,
          true,
          ck3::kCharacterInteractionProposalPayloadSourceExecutableSha256V1,
          true,
          kFixtureModule,
          &fixture.character_storage_pointer,
          &fixture.title_storage_pointer};
}

ck3::CharacterInteractionProposalPayloadSourceAccessV1 Access(
    Fixture &fixture) {
  return {&fixture, &Capture, &ReadMemory, &LookupDefinition};
}

game::CharacterInteractionProposalPayloadSourceV1 ReadAvailable(
    Fixture &fixture) {
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::available);
  Require(output.available && output.failure == Failure::none);
  Require(output.public_revision == 44 && output.native_revision == 144 &&
          output.proof_epoch == 244 && output.date_raw == 53'211'600);
  Require(output.payload.complete &&
          !output.payload.religious_option_selected);
  Require(output.payload.fingerprint.find("cipps:v1:") == 0);
  return output;
}

void TestAllSixTypedPayloads() {
  Fixture fixture{};
  fixture.Configure("educate_child_interaction");
  auto row = ReadAvailable(fixture);
  Require(row.payload.semantic_subject_character_id == kWard &&
          row.payload.semantic_object_character_id == kGuardian);

  fixture.Configure("offer_ward_interaction");
  row = ReadAvailable(fixture);
  Require(row.payload.semantic_subject_character_id == kWard &&
          row.payload.semantic_object_character_id == kGuardian);

  fixture.Configure("offer_guardianship_interaction");
  row = ReadAvailable(fixture);
  Require(row.payload.semantic_subject_character_id == kWard &&
          row.payload.semantic_object_character_id == kGuardian);

  fixture.Configure("grant_titles_interaction");
  row = ReadAvailable(fixture);
  Require(row.selected_title_ids ==
          std::vector<std::int32_t>({kTitleOne, kTitleTwo}));
  Require(row.payload.selected_title_count == 2 &&
          row.payload.semantic_subject_character_id == kRecipient &&
          row.payload.semantic_object_character_id == kActor);

  fixture.Configure("grant_vassal_interaction");
  row = ReadAvailable(fixture);
  Require(row.payload.semantic_subject_character_id == kVassal &&
          row.payload.semantic_object_character_id == kRecipient);

  fixture.Configure("ransom_interaction");
  row = ReadAvailable(fixture);
  Require(row.selected_option_mask == 4 &&
          row.payload.semantic_subject_character_id == kPrisoner &&
          row.payload.semantic_object_character_id == kActor);
  Require(fixture.capture_calls == 6);
}

void TestGenerationBearingIdentityIsMandatory() {
  Fixture fixture{};
  fixture.Configure("grant_vassal_interaction");
  Store(fixture.characters[4], 0x18, std::int32_t{0x06000006});
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::role_identity_unavailable);

  Fixture intermediary_fixture{};
  intermediary_fixture.Configure("ransom_interaction");
  Store(intermediary_fixture.interaction_context, 0x2E8, kVassal);
  Store(intermediary_fixture.characters[4], 0x18,
        std::int32_t{0x06000006});
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(intermediary_fixture), Access(intermediary_fixture),
              intermediary_fixture.preview, output) == Result::unavailable);
  Require(output.failure == Failure::role_identity_unavailable);
}

void TestProofAndDateCannotDrift() {
  Fixture fixture{};
  fixture.Configure("offer_ward_interaction");
  ++fixture.collector.frame.proof_epoch;
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::collector_frame_mismatch);
  --fixture.collector.frame.proof_epoch;
  ++fixture.collector.frame.date_raw;
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::collector_frame_mismatch);
}

void TestReligiousEducationOptionRemainsDeferred() {
  Fixture fixture{};
  fixture.Configure("educate_child_interaction");
  fixture.selected_options[1] = 1;
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::religious_option_deferred);
}

void TestGrantTitleCollectorAndGenerationGates() {
  Fixture fixture{};
  fixture.Configure("grant_titles_interaction");
  Store(fixture.grant_titles_offer, 0x00, static_cast<void *>(nullptr));
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::title_offer_identity_mismatch);

  fixture.Configure("grant_titles_interaction");
  Store(fixture.titles[1], 0x10, std::int32_t{0x09000009});
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::selected_title_identity_unavailable);
}

void TestMalformedOptionsAndExactBuildStayRed() {
  Fixture fixture{};
  fixture.Configure("ransom_interaction");
  fixture.selected_options[2] = 2;
  game::CharacterInteractionProposalPayloadSourceV1 output{};
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              Environment(fixture), Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::selected_options_malformed);

  fixture.Configure("ransom_interaction");
  auto environment = Environment(fixture);
  environment.admitted_executable_sha256 = "wrong";
  Require(ck3::ReadCharacterInteractionProposalPayloadSourceV1(
              environment, Access(fixture), fixture.preview, output) ==
          Result::unavailable);
  Require(output.failure == Failure::exact_build_not_admitted);
}

} // namespace

int main() {
  try {
    TestAllSixTypedPayloads();
    TestGenerationBearingIdentityIsMandatory();
    TestProofAndDateCannotDrift();
    TestReligiousEducationOptionRemainsDeferred();
    TestGrantTitleCollectorAndGenerationGates();
    TestMalformedOptionsAndExactBuildStayRed();
    for (std::uint32_t value = 0;
         value <= static_cast<std::uint32_t>(
                      Failure::selected_title_identity_unavailable);
         ++value) {
      Require(!ck3::CharacterInteractionProposalPayloadSourceFailureKeyV1(
                   static_cast<Failure>(value))
                   .empty());
    }
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  std::cout << "character interaction proposal payload source fixture: GREEN\n";
  return 0;
}
