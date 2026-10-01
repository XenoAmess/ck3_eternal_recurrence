#include "xar_bridge/religion_doctrine12002_catalogue_mailbox.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace c = xar::ck3_12002;
namespace d = c::religion::doctrine12002;
namespace {
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class B, class T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template<class B> void Key(B &b, std::string_view key) {
  const auto at = d::kDoctrineStableKeyOffset;
  if (key.size() < 16) std::memcpy(b.data() + at, key.data(), key.size());
  else Put(b, at, key.data());
  Put(b, at + 0x10, static_cast<std::uint64_t>(key.size()));
  Put(b, at + 0x18, key.size() < 16 ? std::uint64_t{15} : static_cast<std::uint64_t>(key.size()));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; Bytes<0x22350> data{}; Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()}; Bytes<0x30> storage{};
  Bytes<0x80> slots{}; Bytes<0x1D8> actor{}; Bytes<0x80> database{};
  Bytes<0xB10> one{}, two{}, three{}; Bytes<0x150> group{};
  std::array<const void *, 3> rows{one.data(), two.data(), three.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *database_ptr = database.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::string_view mod_key = "mod_custom_doctrine\"信";
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(database, d::kDoctrineDatabaseArrayOffset, rows.data());
    Put(database, 0x58, std::int32_t{3}); Put(database, d::kDoctrineDatabaseCountOffset, std::int32_t{3});
    Key(one, "doctrine_a"); Key(two, "doctrine_b"); Key(three, mod_key); Key(group, "group_a");
    Put(one, d::kDoctrineGroupPointerOffset, group.data());
    Put(two, d::kDoctrineGroupPointerOffset, group.data());
    Put(three, d::kDoctrineGroupPointerOffset, group.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
d::CatalogueBindings Bind(Fixture &q) {
  f = &q; d::CatalogueBindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.database_slot = &f->database_ptr; return b;
}
} // namespace

#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>

#if defined(XAR_CATALOGUE_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "religion-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // Existing offline primary permit; central owns the new named slot and
    // validates its thin production branch independently after this package.
    mailbox.permitted_executor = &c::ExecutePlayerReligionDoctrineCatalogueMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};


bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, d::DoctrineCatalogue &observed) {
  api::MainThreadQueryMailboxV1 mailbox{}; Pump pump(fixture, mailbox);
  c::PlayerReligionDoctrineCatalogueMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture); adapter.reads = 0;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionDoctrineCatalogueMailbox12002(query,
        "catalogue\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "real queued executor drained on fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  observed = query.observation;
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(),
          "actual complete serialized response");
    Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          observed.capture_epoch != query.envelope.expected_snapshot_revision, "pump epoch separate from revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Check(serialized.empty() && !failure.empty(), "unstable owner has no success packet");
  return result;
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]); Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = 53175816; d::DoctrineCatalogue observed{};
    Check(Query(fixture, adapter, directory, "loaded-catalogue.json", observed) && observed.available &&
          observed.catalogue_complete && observed.rows.size() == 3 &&
          observed.rows[2].doctrine_key == Fixture::mod_key, "full actual loaded registry through mailbox");
    Put(fixture.database, d::kDoctrineDatabaseCountOffset, std::int32_t{0});
    Check(Query(fixture, adapter, directory, "known-empty.json", observed) && observed.available &&
          observed.catalogue_complete && observed.rows.empty(), "empty registry remains observed complete");
    fixture.database_ptr = nullptr;
    Check(Query(fixture, adapter, directory, "database-unavailable.json", observed) && !observed.available &&
          !observed.catalogue_complete && observed.unavailable_reason == "doctrine_database_unavailable" &&
          observed.played_character_id == Fixture::actor_id && observed.date_raw == 53175816,
          "typed unavailable complete false with actual owner provenance");
    fixture.database_ptr = fixture.database.data(); adapter.drift = true;
    Check(!Query(fixture, adapter, directory, "owner-frame-drift.json", observed),
          "actual owner snapshot changed after native capture"); adapter.drift = false;
    std::uint64_t revision = 0;
    Check(c::ParsePlayerReligionDoctrineCatalogueRevision12002("{\"expected_revision\":701}", revision) &&
          revision == 701, "actual revision alias parser");
    api::MainThreadQueryMailboxV1 mailbox{}; std::string wire, failure;
    Check(!c::HandlePlayerReligionDoctrineCataloguePrivate12002(adapter, mailbox, adapter.frame, 701,
          c::kPlayerReligionDoctrineCataloguePrivateStep12002, "{\"expected_revision\":702}", "stale", wire, failure) &&
          wire.empty() && mailbox.next_sequence == 0 &&
          failure == "player_religion_doctrine_catalogue_current_frame_unavailable",
          "actual caller rejects stale revision before mailbox submit");
    Check(c::IsPlayerReligionDoctrineCataloguePrivateStep12002(c::kPlayerReligionDoctrineCataloguePrivateStep12002),
          "actual catalogue exact private selector");
    std::cout << "PASS checks=" << checks << " actual_core=true actual_provider=true actual_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
