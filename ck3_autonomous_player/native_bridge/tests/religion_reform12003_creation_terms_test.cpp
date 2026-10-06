// Reuse the established fake-memory/owner-mailbox backing, never its old main.
// This target executes only the six new creation-terms cases below.
#define main XarRetainedReformMailboxFixtureMain
#include "../src/religion_reform12002_query_mailbox_test.cpp"
#undef main

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_reform12003_creation_terms.hpp"

namespace terms = f::creation_terms12003;
namespace {
struct TermsFixture final : Fixture {
  Bytes<0x30> rite_storage{}, faith_storage{};
  Bytes<0x80> rite_slots{}, faith_slots{};
  Bytes<0x8B8> alternate_rite{}, alternate_main{};
  Bytes<0x320> alternate_faith{};
  void *rite_storage_ptr = rite_storage.data();
  void *faith_storage_ptr = faith_storage.data();
  std::int64_t draft_divergence = 0;
  std::int64_t creation_threshold = 13'700'000;
  bool native_faith_branch = false;
  unsigned divergence_calls = 0, native_branch_calls = 0;
  bool terms_arguments_correct = true;
  static constexpr std::uint32_t alternate_rite_id = 0xCA000007U;
  static constexpr std::uint32_t alternate_faith_id = 0xC9000005U;
  static constexpr std::uint32_t alternate_main_id = 0xCB000006U;

  TermsFixture() {
    Put(rite_storage, 0x20, rite_slots.data());
    Put(rite_storage, 0x2C, std::int32_t{8});
    Put(faith_storage, 0x20, faith_slots.data());
    Put(faith_storage, 0x2C, std::int32_t{8});
    Put(rite_slots, 0 * 0x10 + 8, current_rite.data());
    Put(rite_slots, 2 * 0x10 + 8, main_rite.data());
    Put(faith_slots, 3 * 0x10 + 8, faith.data());
    Put(alternate_rite, 8, alternate_rite_id);
    Put(alternate_rite, r::kRiteFaithIdOffset, alternate_faith_id);
    Put(alternate_faith, 8, alternate_faith_id);
    Put(alternate_faith, r::kFaithMainRiteIdOffset, alternate_main_id);
    Put(alternate_main, 8, alternate_main_id);
    Put(alternate_main, r::kRiteFaithIdOffset, alternate_faith_id);
    Put(rite_slots, 7 * 0x10 + 8, alternate_rite.data());
    Put(rite_slots, 6 * 0x10 + 8, alternate_main.data());
    Put(faith_slots, 5 * 0x10 + 8, alternate_faith.data());
    main_rite[f::kRiteUnreformedOffset] = std::byte{0};
  }
};
TermsFixture *terms_fixture = nullptr;

std::int64_t *DraftDivergence(std::int64_t *out, const void *window) {
  ++terms_fixture->divergence_calls;
  terms_fixture->terms_arguments_correct &= window == terms_fixture->window.data();
  *out = terms_fixture->draft_divergence;
  return out;
}
bool NativeCreationBranch(const void *actor_faith, const void *draft) {
  ++terms_fixture->native_branch_calls;
  terms_fixture->terms_arguments_correct &= actor_faith == terms_fixture->faith.data() &&
      draft == terms_fixture->window.data() + f::kRiteCreationPriceDraftOffset;
  // Explicit synthetic callback verdict. No cost, divergence or native rule
  // formula is replicated in the fixture producer.
  return terms_fixture->native_faith_branch;
}
q::Bindings BindTerms(TermsFixture &fixture) {
  terms_fixture = &fixture;
  auto bindings = Bind(fixture);
  bindings.creation_terms = {true, &fixture.rite_storage_ptr,
      &fixture.faith_storage_ptr, &DraftDivergence, &fixture.creation_threshold,
      &NativeCreationBranch};
  return bindings;
}

bool QueryTerms(TermsFixture &fixture, FrameAdapter &adapter,
                const std::filesystem::path &directory,
                const char *filename, q::Observation &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionReformMailboxContext12002 query{};
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = BindTerms(fixture);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool succeeded = false, drained = false;
  std::string wire, failure;
  std::thread worker([&] {
    succeeded = c::RunPlayerReligionReformMailbox12002(
        query, "first-creation-terms-whole-wire", wire, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) &&
         std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) ==
        api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "new terms actual owner executor drained");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "new terms complete ticket reclaimed");
  Check(succeeded && query.completed && query.envelope.frame_stable &&
        failure.empty() && !wire.empty(), "new terms whole command_result exists");
  observed = query.observation;
  Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
        observed.capture_epoch != 701, "terms epoch is actual owner epoch, not revision");
  // This is the existing production .3 build renderer, not a native-row edit.
  wire = game::RenderCrozierBuildIdentity(std::move(wire), adapter.descriptor());
  std::ofstream(directory / filename, std::ios::binary) << wire << '\n';
  return succeeded;
}

void CheckVisibleTerms(const TermsFixture &fixture, const q::Observation &out,
                       std::uint32_t source_rite, std::uint32_t source_faith,
                       std::uint32_t source_main, bool ui, bool native) {
  const auto &value = out.draft_creation_terms;
  Check(out.publish_creation_terms && value.available &&
        value.source_rite_id == source_rite && value.source_faith_id == source_faith &&
        value.source_main_rite_id == source_main && value.actor_faith_id == Fixture::faith_id,
        "terms keeps full source and actor Faith identities");
  Check(value.capture_epoch == out.capture_epoch && value.date_raw == Fixture::date &&
        value.played_character_id == static_cast<std::uint32_t>(Fixture::actor_id),
        "terms preserves its composed owner frame");
  Check(value.draft_divergence_raw == fixture.draft_divergence &&
        value.faith_creation_threshold_raw == fixture.creation_threshold &&
        value.divergence_results_in_faith_creation == ui &&
        value.native_create_faith_or_reform == native,
        "terms publishes signed raw values and independent booleans");
  Check(fixture.divergence_calls == 1 && fixture.native_branch_calls == 1 &&
        fixture.terms_arguments_correct && fixture.arguments_correct,
        "new getter and native branch use real callback inputs once");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "terms wire-directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    const auto run_visible = [&](const char *name, std::int64_t divergence,
                                 std::int64_t threshold, bool native,
                                 bool unreformed, bool different_source,
                                 bool final_create) {
      auto fixture = std::make_unique<TermsFixture>();
      fixture->draft_divergence = divergence;
      fixture->creation_threshold = threshold;
      fixture->native_faith_branch = native;
      fixture->create = final_create;
      fixture->main_rite[f::kRiteUnreformedOffset] =
          unreformed ? std::byte{1} : std::byte{0};
      if (different_source)
        Put(fixture->window, f::kDraftWindowRiteIdOffset,
            TermsFixture::alternate_rite_id);
      FrameAdapter adapter;
      adapter.identity = game::AdapterDescriptor{xar::ck3_12003::kAdapterId,
          xar::ck3_12003::kGameVersion, xar::ck3_12003::kExecutableSha256,
          "synthetic-creation-terms-first-whole-wire", {}};
      adapter.frame.paused = adapter.frame.map_ready = true;
      adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
      adapter.frame.played_character_id = Fixture::actor_id;
      adapter.frame.date_raw = Fixture::date;
      q::Observation out{};
      Check(QueryTerms(*fixture, adapter, directory, name, out) && out.available,
            "visible actual composed terms query completed");
      CheckVisibleTerms(*fixture, out,
          different_source ? TermsFixture::alternate_rite_id : Fixture::rite_id,
          different_source ? TermsFixture::alternate_faith_id : Fixture::faith_id,
          different_source ? TermsFixture::alternate_main_id : Fixture::main_id,
          divergence >= threshold, native);
      Check(out.draft_eligibility.can_create_rite == final_create &&
            out.draft_costs.piety_missing_signed_raw == -2'500'000 &&
            out.draft_costs.has_enough_piety == true,
            "native branch, final legality and current quote remain independent");
    };
    run_visible("visible-zero-below-threshold.json", 0, 13'700'000,
                false, false, false, true);
    run_visible("visible-exact-threshold.json", 9'300'000, 9'300'000,
                true, false, false, true);
    run_visible("visible-above-threshold.json", 0, -500'000,
                true, false, false, false);
    run_visible("unreformed-native-branch.json", 0, 13'700'000,
                true, true, false, false);
    run_visible("different-source-and-actor-faith.json", 14'000'000, 13'700'000,
                false, false, true, true);

    auto fixture = std::make_unique<TermsFixture>();
    fixture->visible = false;
    FrameAdapter adapter;
    adapter.identity = game::AdapterDescriptor{xar::ck3_12003::kAdapterId,
        xar::ck3_12003::kGameVersion, xar::ck3_12003::kExecutableSha256,
        "synthetic-creation-terms-first-whole-wire", {}};
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    q::Observation out{};
    Check(QueryTerms(*fixture, adapter, directory, "hidden-existing-window.json", out),
          "hidden current window composed query completed");
    const auto &value = out.draft_creation_terms;
    Check(out.available && out.context.available && out.publish_creation_terms &&
          !value.available && !value.failure.empty() &&
          !value.source_rite_id && !value.source_faith_id && !value.source_main_rite_id &&
          !value.actor_faith_id && !value.draft_divergence_raw &&
          !value.faith_creation_threshold_raw && !value.divergence_results_in_faith_creation &&
          !value.native_create_faith_or_reform,
          "hidden draft absence does not fill terms or erase current context");
    Check(value.capture_epoch == out.capture_epoch && value.date_raw == Fixture::date &&
          value.played_character_id == static_cast<std::uint32_t>(Fixture::actor_id) &&
          fixture->divergence_calls == 0 && fixture->native_branch_calls == 0,
          "hidden terms preserves frame metadata without native draft calls");
    std::ofstream(directory / "PROVENANCE.json", std::ios::binary)
        << "{\"schema\":\"creation_terms_first_six_whole_wire_provenance_v1\","
           "\"synthetic_native_backing\":true,\"native_callback_values\":\"synthetic\","
           "\"actual_production_composed_reader\":true,\"actual_mailbox\":true,"
           "\"actual_command_result_serializer\":true,\"actual_12003_renderer\":true,"
           "\"native_rows_rewritten\":false,\"cases\":6,\"live\":false}\n";
    std::cout << "PASS new_creation_terms_cases=6 checks=" << checks
              << " whole_native_command_results=true synthetic_native_backing=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
