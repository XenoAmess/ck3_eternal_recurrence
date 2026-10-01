// Reuse the exact-layout fixture already qualified by the collection suite.
// Its eight collection cases are compiled but never executed by this target.
#define main RunUnusedCollectionFixtureCases
#include "ck3_12002_prisoner_collection_test.cpp"
#undef main

#include <filesystem>
#include <fstream>

namespace {
bool SaveWire(const std::filesystem::path &path,
              const PlayerPrisonerCollectionSnapshotV1 &snapshot,
              const std::array<PlayerPrisonerRansomQuoteV1, kPlayerPrisonerMaximumRowsV1> &quotes) {
  const auto wire = SerializePlayerPrisonerCollectionPrivateV1(snapshot, 11, quotes, true);
  if (wire.empty()) return false;
  std::ofstream output(path, std::ios::binary);
  output << wire << '\n';
  return static_cast<bool>(output);
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: prisoner-wire-fixture OUTPUT_DIRECTORY\n";
    return 2;
  }
  const std::filesystem::path into(argv[1]);
  std::filesystem::create_directories(into);
  int passed = 0;
  std::array<PlayerPrisonerRansomQuoteV1, kPlayerPrisonerMaximumRowsV1> quotes{};
  // The collection values come from the actual 1.20 provider. Quote values
  // are explicit synthetic DTO controls for the shared production serializer.
  auto &quote = quotes[0];
  quote.available = true;
  quote.failure = PlayerPrisonerRansomQuoteFailureV1::none;
  quote.jailer_character_id = static_cast<std::int32_t>(kPlayerId);
  quote.payer_character_id = static_cast<std::int32_t>(kSecondPrisonerId);
  quote.prisoner_character_id = static_cast<std::int32_t>(kPrisonerId);
  quote.selected_option = "gold";
  quote.quoted_gold_raw = 2'000'000;
  quote.recipient_acceptance_raw = 1'000'000;
  quote.recipient_answer_status_raw = 0;
  quote.would_accept_now = true;
  quotes[1].failure = PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  {
    Fixture fixture;
    PlayerPrisonerCollectionSnapshotV1 snapshot{};
    passed += Expect(ReadPlayerPrisonerCollectionV1(Access(fixture), snapshot) &&
        snapshot.returned_count == 2 && SaveWire(into / "two-prisoners.json", snapshot, quotes),
        "production getter and wire with two rows");
  }
  {
    Fixture fixture;
    fixture.Put(kPlayer + 0x1C0, std::uintptr_t{0});
    PlayerPrisonerCollectionSnapshotV1 snapshot{};
    passed += Expect(ReadPlayerPrisonerCollectionV1(Access(fixture), snapshot) &&
        snapshot.returned_count == 0 && SaveWire(into / "empty.json", snapshot, quotes),
        "production empty getter and wire");
  }
  {
    Fixture fixture;
    auto access = Access(fixture);
    access.admitted_executable_sha256 = kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
    PlayerPrisonerCollectionSnapshotV1 snapshot{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1(access, snapshot) &&
        snapshot.failure == PlayerPrisonerCollectionFailureV1::exact_build_mismatch &&
        SaveWire(into / "old-executable-unavailable.json", snapshot, quotes),
        "production old executable failure wire");
  }
  std::cout << "ck3_12002_prisoner_wire " << passed << "/3 GREEN\n";
  return passed == 3 ? 0 : 1;
}
