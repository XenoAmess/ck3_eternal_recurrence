#include "xar_bridge/ck3_12002_epidemic_treatment_mailbox.hpp"

#include <array>
#include <atomic>
#include <bit>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <vector>

namespace c = xar::ck3_12002;
namespace api = xar::ck3_11906;
namespace game = xar::game;

#if defined(XAR_TREATMENT_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0x200> extension{};
  Bytes<0x48> rows{};
  Bytes<0x60> wanted{}, fallback{};
  std::string name = std::string(api::kPlayerEpidemicTreatmentModifierKeyV1);
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *fallback_ptr = fallback.data();
  bool fallback_lookup = false;
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::int32_t date = 53350560;
  static constexpr std::uint64_t revision = 123;
  static constexpr std::uint32_t hash = 0x22A483B2;
  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, c::kTreatmentCharacterExtensionOffset12002, extension.data());
    Put(extension, c::kTreatmentModifierRowsOffset12002, rows.data());
    Put(extension, c::kTreatmentModifierCountOffset12002, std::int32_t{1});
    Put(rows, 0, wanted.data());
    Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002, name.data());
    Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002 + 0x10, name.size());
    Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002 + 0x18, name.size());
  }
};
Fixture *fixture = nullptr;
void *Player(void *) { return fixture->player.data(); }
void *Database() { return fixture; }
std::uint32_t Hash(void *, const char *, std::uint32_t) { return Fixture::hash; }
void *Lookup(void *, std::int32_t) {
  return fixture->fallback_lookup ? fixture->fallback.data() : fixture->wanted.data();
}
c::TreatmentPresenceBindings12002 Bind(Fixture &value) {
  fixture = &value;
  c::TreatmentPresenceBindings12002 result{}; result.enabled = true;
  result.core = {true, &fixture->state_ptr, &fixture->jomini_ptr, &fixture->storage_ptr, &Player};
  result.get_modifier_database = &Database; result.hash_stable_key = &Hash;
  result.lookup_modifier = &Lookup; result.fallback_definition_slot = &fixture->fallback_ptr;
  return result;
}
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
      c::kExecutableSha256, "epidemic-treatment-fixture", {}};
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
  Pump(Fixture &value, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&value.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&value.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.offline_fixture = true;
    mailbox.permitted_executor_epidemic_treatment12002 = &c::ExecutePlayerEpidemicTreatmentMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &value, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, bool expect_available) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(value, mailbox);
  const auto bindings = Bind(value);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::HandlePlayerEpidemicTreatmentPrivate12002(adapter, mailbox, adapter.frame,
        Fixture::revision, c::kPlayerEpidemicTreatmentPrivateStep12002,
        "{\"expected_revision\":123}", "epidemic-treatment-\"mailbox-fixture",
        serialized, failure, &bindings);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual Handle queued callback drained on fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual Handle reclaimed mailbox");
  if (result) {
    Check(failure.empty() && !serialized.empty(), "actual Handle returned complete caller JSON");
    Check(adapter.reads == 2, "actual owning envelope captured before and after provider");
    Check(serialized.find(expect_available ? "\"status\":\"available\"" : "\"status\":\"unavailable\"") !=
          std::string::npos, "actual caller status matches provider result");
    std::ofstream output(directory / filename); output << serialized << '\n';
    Check(output.good(), "actual Handle packet saved");
  } else Check(serialized.empty() && !failure.empty(), "changed frame has no success packet");
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "own output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Fixture value; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id; adapter.frame.date_raw = Fixture::date;
    Check(Query(value, adapter, directory, "present.json", true), "present production Handle chain");
    Put(value.character, c::kTreatmentCharacterExtensionOffset12002, static_cast<void *>(nullptr));
    Check(Query(value, adapter, directory, "absent.json", true), "legal empty set through production Handle");
    value.fallback_lookup = true;
    Check(Query(value, adapter, directory, "definition-unavailable.json", false), "typed unavailable through production Handle");
    value.fallback_lookup = false; adapter.drift = true;
    Check(!Query(value, adapter, directory, "changed-frame.json", true), "owning frame changes suppress caller success");
    adapter.drift = false;
    api::MainThreadQueryMailboxV1 mailbox{};
    auto bindings = Bind(value);
    std::string wire, failure;
    const auto handle = [&](std::string_view payload) {
      return c::HandlePlayerEpidemicTreatmentPrivate12002(adapter, mailbox, adapter.frame,
          Fixture::revision, c::kPlayerEpidemicTreatmentPrivateStep12002, payload, "stale",
          wire, failure, &bindings);
    };
    mailbox.offline_fixture = true;
    Check(!handle("{\"expected_revision\":124}") && wire.empty() &&
          failure == "player_epidemic_treatment_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual Handle stale native revision rejected before submission");
    Check(!handle("{}") && failure == "player_epidemic_treatment_request_invalid" && mailbox.next_sequence == 0,
          "actual Handle requires native expected revision");
    Check(!handle("{\"expected_revision\":123}") &&
          failure == "player_epidemic_treatment_mailbox_submit_unavailable" && mailbox.next_sequence == 0,
          "actual Handle requires new named callback registration");
    mailbox.offline_fixture = false;
    Check(!handle("{\"expected_revision\":123}") &&
          failure == "player_epidemic_treatment_current_frame_unavailable" && mailbox.next_sequence == 0,
          "fixture seam is only admitted on offline mailbox");
    Check(c::IsPlayerEpidemicTreatmentPrivateStep12002(c::kPlayerEpidemicTreatmentPrivateStep12002) &&
          !c::IsPlayerEpidemicTreatmentPrivateStep12002("query-player-epidemic-treatment-presence-v2"),
          "unchanged exact selector");
    std::cout << "PASS checks=" << checks << " actual_handle=true actual_core=true actual_provider=true actual_mailbox=true actual_serializer=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
