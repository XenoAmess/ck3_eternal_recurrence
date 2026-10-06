#include "xar_bridge/ck3_12003_prisoner_native_kinship.hpp"
// Reuse only the fixture-owned collection memory substrate. The existing
// release FIRST entry and RunCase are compiled but never called or rerun.
#define main PrisonerReleaseFixtureNotExecuted12003
#include "ck3_12003_prisoner_release_preview_test.cpp"
#undef main

namespace {
enum class KinshipCase { nonchild_close_family, unrelated, sample_drift,
                         wrong_generation, wrong_jailer, not_paused };
KinshipCase kinship_case{};
unsigned close_calls = 0, extended_calls = 0;
bool NativeClose(void *subject, void *target) {
  Require(reinterpret_cast<std::uintptr_t>(subject) == kPrisonerBase + 2 * 0x1000 &&
          reinterpret_cast<std::uintptr_t>(target) == kPlayer,
          "exact native subject/target full-ID objects");
  ++close_calls;
  return kinship_case == KinshipCase::nonchild_close_family ||
      (kinship_case == KinshipCase::sample_drift && close_calls == 1);
}
bool NativeExtended(void *subject, void *target) {
  Require(reinterpret_cast<std::uintptr_t>(subject) == kPrisonerBase + 2 * 0x1000 &&
          reinterpret_cast<std::uintptr_t>(target) == kPlayer,
          "exact extended-family subject/target objects");
  ++extended_calls;
  return kinship_case == KinshipCase::nonchild_close_family;
}
void KinshipRun(KinshipCase kind, std::string_view name, const std::filesystem::path &directory) {
  kinship_case = kind;
  close_calls = extended_calls = 0;
  Fixture fixture(Case::gate_true);
  fixture.Prepare();
  bridge::PlayerPrisonerCollectionAccessV1 ca{};
  ca.exact_build_admitted = true;
  ca.admitted_executable_sha256 = old::kExecutableSha256;
  ca.module_base = kModule;
  ca.current_thread_id = ca.application_main_thread_id = 8;
  ca.read_lineage = ca.read_child_relation = ca.read_title_tier = ca.read_dread = true;
  ca.context = &fixture;
  ca.capture_frame = CaptureFrame;
  ca.read_memory = ReadMemory;
  ca.get_primary_title = PrimaryTitle;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(old::ReadPlayerPrisonerCollectionV1(ca, collection),
          "actual complete collection source");
  Require(collection.collection_complete && collection.returned_count == 4 &&
          !collection.rows[2].child_of_played_character &&
          collection.rows[2].dynasty_id != collection.played_dynasty_id,
          "non-child non-dynasty metadata differs from native close family");

  if (kind == KinshipCase::wrong_generation)
    fixture.Put(kPrisonerBase + 2 * 0x1000 + 0x18,
                kPrisonerIds[2] + std::uint32_t{0x01000000});
  if (kind == KinshipCase::wrong_jailer)
    fixture.Put(kRelationBase + 2 * 0x1000, kPlayerId + std::uint32_t{1});
  if (kind == KinshipCase::not_paused) fixture.frame.paused = false;
  leaf::PrisonerNativeKinshipBindings12003 bindings{};
  bindings.enabled = true;
  bindings.module_base = kModule;
  bindings.close_family = NativeClose;
  bindings.close_or_extended_family = NativeExtended;
  const leaf::PrisonerNativeKinshipAccess12003 access{8, 8, &fixture, CaptureFrame, ReadMemory};
  std::array<leaf::PrisonerNativeKinship12003, bridge::kPlayerPrisonerMaximumRowsV1> results{};
  const bool ok = leaf::ReadPrisonerNativeKinship12003(bindings, access,
      kPlayerId, kPrisonerIds[2], 2, results[2]);
  const bool available = kind == KinshipCase::nonchild_close_family ||
                         kind == KinshipCase::unrelated;
  Require(ok == available && results[2].available == available,
          "observed false versus typed unavailable");
  if (available) {
    const bool related = kind == KinshipCase::nonchild_close_family;
    Require(results[2].is_close_family_of_played_character == related &&
            results[2].is_close_or_extended_family_of_played_character == related &&
            results[2].frame == collection.frame && results[2].source_ordinal == 2 &&
            results[2].jailer_character_id == kPlayerId &&
            results[2].prisoner_character_id == kPrisonerIds[2] &&
            close_calls == 2 && extended_calls == 2,
            "two complete native relation samples bind exact frame and ordinal");
  } else {
    const std::string_view expected = kind == KinshipCase::sample_drift ?
        "native_sample_drift" : kind == KinshipCase::not_paused ?
        "not_paused" : "custody_relation_unverified";
    Require(results[2].unavailable_reason == expected, "typed native failure retained");
    const unsigned calls = kind == KinshipCase::sample_drift ? 2U : 0U;
    Require(close_calls == calls && extended_calls == calls,
            "identity/custody/frame failures do not evaluate native kinship");
  }
  std::array<old::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  for (auto &quote : quotes) quote.failure = old::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  quotes[2].failure = old::PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
  std::array<leaf::PrisonerReleasePreview12003, bridge::kPlayerPrisonerMaximumRowsV1> releases{};
  const auto value = old::SerializePlayerPrisonerCollectionPrivateV1(
      collection, collection.frame.native_revision, quotes, true, &releases, &results);
  Require(value.find("\"schema_version\":7") != std::string::npos &&
          value.find("\"native_kinship\"") != std::string::npos,
          "actual whole collection serializer publishes selected native kinship");
  const auto wire = std::string{
      "{\"step\":\"query-player-prisoner-collection-private-v1-ransom-ordinal-2\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":"} +
      std::to_string(static_cast<unsigned>(kind) + 1U) +
      ",\"observation_revision\":" + std::to_string(collection.frame.proof_epoch) +
      ",\"snapshot_revision\":" + std::to_string(collection.frame.native_revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\"}";
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Require(stream.is_open(), "open new whole kinship wire");
  stream << wire << '\n';
  Require(stream.good(), "write new whole kinship wire");
  std::cout << "FIRST kinship " << name << " whole_collection=4 available="
            << (available ? "true" : "false") << '\n';
}
} // namespace
int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12003_prisoner_native_kinship_test OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    KinshipRun(KinshipCase::nonchild_close_family, "nonchild_close_family", directory);
    KinshipRun(KinshipCase::unrelated, "unrelated", directory);
    KinshipRun(KinshipCase::sample_drift, "sample_drift", directory);
    KinshipRun(KinshipCase::wrong_generation, "wrong_generation", directory);
    KinshipRun(KinshipCase::wrong_jailer, "wrong_jailer", directory);
    KinshipRun(KinshipCase::not_paused, "not_paused", directory);
    std::cout << "FIRST kinship groups=3 cases=6 complete\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST kinship RED " << error.what() << '\n';
    return 1;
  }
}
