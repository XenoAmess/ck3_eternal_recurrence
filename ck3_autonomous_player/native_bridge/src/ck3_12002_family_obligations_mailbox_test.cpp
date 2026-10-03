#include "xar_bridge/ck3_12002_family_obligations_mailbox.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>

// Synthetic owner-side native objects/callbacks; actual lineage reader,
// optional-lane readers, owner envelope, mailbox executor and serializer are
// compiled unchanged. This is an offline fixture, not a CK3 observation.
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
ContextBindings BindContextImage(std::uintptr_t, std::string_view) noexcept { return {}; }
}
namespace {
using namespace xar::ck3_12002;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value)); return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
constexpr std::int32_t actor_id = 0x01000001, subject_id = 0x01000002,
    candidate_id = 0x01000003, subject_house = 0x01000001, candidate_house = 0x01000002,
    subject_dynasty = 0x01000001, candidate_dynasty = 0x01000002;
std::array<std::byte, 0x200> actor{}, subject{}, candidate{};
bool selected = false, native_legal = true, wrong_parent = false, drift = false;
int contexts = 0, destroys = 0, previews = 0;
bool ReadOption(const void *, std::uint32_t option) { Check(option == 9, "option ID"); return selected; }
void Refresh(void *, bool value) { Check(value, "refresh bool follows existing native pair"); }
void Finalize(void *) {}
void *NativeParent(const void *offer) {
  ++previews;
  Check(Get<std::uintptr_t>(offer, 0) == 0x12002, "exact offer vtable");
  Check(Get<void *>(offer, 8) == nullptr, "detached native cached-option branch");
  Check(Get<std::int32_t>(offer, 0x28) == subject_id &&
        Get<std::int32_t>(offer, 0x2C) == candidate_id, "full secondary IDs");
  Check(Get<bool>(offer, 0x80) == selected, "actual native selected option");
  if (wrong_parent) return actor.data();
  return selected == Get<bool>(subject.data(), family_value::kCharacterSexSelectorOffset)
      ? subject.data() : candidate.data();
}
struct Components {
  std::array<std::byte, 0x30> house_store{}, dynasty_store{};
  std::array<std::byte, 0x30> house_slots{}, dynasty_slots{};
  std::array<std::byte, 0x40> house_a{}, house_b{}, dynasty_a{}, dynasty_b{};
  void *houses = house_store.data(), *dynasties = dynasty_store.data();
  void *house_fallback = nullptr, *dynasty_fallback = nullptr;
  Components() {
    Put(house_store.data(), 0x20, house_slots.data()); Put(house_store.data(), 0x2C, std::int32_t{3});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data()); Put(dynasty_store.data(), 0x2C, std::int32_t{3});
    Put(house_slots.data(), 0x18, house_a.data()); Put(house_slots.data(), 0x28, house_b.data());
    Put(dynasty_slots.data(), 0x18, dynasty_a.data()); Put(dynasty_slots.data(), 0x28, dynasty_b.data());
    Put(house_a.data(), 0x10, subject_house); Put(house_b.data(), 0x10, candidate_house);
    Put(house_a.data(), 0x2C, subject_dynasty); Put(house_b.data(), 0x2C, candidate_dynasty);
    Put(dynasty_a.data(), 0x10, subject_dynasty); Put(dynasty_b.data(), 0x10, candidate_dynasty);
  }
};
} // namespace

namespace xar::ck3_12002 {
CoreBindings BindCoreImage(std::uintptr_t, std::string_view) noexcept { return {}; }
FamilyBindings BindFamilyImage(std::uintptr_t, std::string_view) noexcept { return {}; }
FamilyProjectionBindings BindFamilyProjectionImage(std::uintptr_t, std::string_view) noexcept { return {}; }
bool ReadCoreSnapshot(const CoreBindings &, CoreSnapshotPrefix &out) noexcept {
  out = {}; out.clock.paused = true; out.clock.date_raw = drift && previews ? 53220001 : 53220000;
  out.map_ready = true; out.has_played_character = true; out.played_character_alive = true;
  out.played_character_id = actor_id; return true;
}
void *ResolveCoreCharacter(const CoreBindings &, std::int32_t id) noexcept {
  return id == actor_id ? actor.data() : id == subject_id ? subject.data() :
      id == candidate_id ? candidate.data() : nullptr;
}
bool PrepareFamilyPairContextV1(const FamilyBindings &, std::int32_t actor_value,
    std::int32_t subject_value, std::int32_t candidate_value, FamilyPairContextV1 &out) noexcept {
  if (actor_value != actor_id || subject_value != subject_id || candidate_value != candidate_id) return false;
  out.initialized = true; ++contexts; return true;
}
void DestroyFamilyPairContextV1(const FamilyBindings &, FamilyPairContextV1 &out) noexcept {
  if (out.initialized) ++destroys;
  out = {};
}
bool ReadFamilyPairTermsV1(const FamilyBindings &, std::int32_t, std::int32_t,
    const FamilyPairContextV1 &, FamilyPairTermsV1 &out) noexcept {
  out = {}; out.complete_can_send = native_legal;
  // Deliberately differs from selected UI option to catch aliasing the two.
  out.effective_matrilineal_if_accepted = !selected; return true;
}
bool SelectFamilyMatrilinealOptionV1(const FamilyProjectionBindings &, void *) noexcept {
  selected = true; return true;
}
} // namespace xar::ck3_12002

namespace {
using namespace xar;
using namespace xar::ck3_12002;
namespace api = xar::ck3_11906;
class Adapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        "ck3-1.20.0.2-msvc-x64", "1.20.0.2", kExecutableSha256, "fixture", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    output = frame; ++reads;
    if (drift && reads > 1) ++output.date_raw;
    return true;
  }
  game::PauseSubmitResult submit_pause_map(game::Snapshot *) const noexcept override { return {}; }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot *) const noexcept override { return {}; }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SelectEventOptionResult submit_select_event_option(std::int32_t) const noexcept override { return {}; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply) const noexcept override { return {}; }
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override { return {}; }
  game::MoveArmyResult submit_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::DisbandArmyResult submit_disband_army(std::int32_t) const noexcept override { return {}; }
  game::SplitArmyHalfResult submit_split_army_half(std::int32_t) const noexcept override { return {}; }
  game::MergeArmiesResult submit_merge_armies(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::StartAssaultResult submit_start_assault(std::int32_t) const noexcept override { return {}; }
  game::StopAssaultResult submit_stop_assault(std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(std::int32_t, std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return {}; }
  game::DeclareWarResult submit_declare_war(const game::DeclarableWarSnapshot &) const noexcept override { return {}; }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &) const noexcept override { return {}; }
  game::ArrangeMarriageResult submit_arrange_marriage(const game::ArrangeMarriageChoice &) const noexcept override { return {}; }
  game::EnforceDemandsResult submit_enforce_demands(std::int32_t) const noexcept override { return {}; }
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationOptionsResult read_war_termination_options(std::int32_t, game::WarTerminationOptionsSnapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationTermsResult read_war_termination_terms(std::int32_t, game::WarTerminationTermsSnapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(std::int32_t, game::WarTerminationExitTermsSnapshot &) const noexcept override { return {}; }
  game::SurrenderWarResult submit_surrender_war(std::int32_t) const noexcept override { return {}; }
  game::OfferWhitePeaceResult submit_offer_white_peace(std::int32_t) const noexcept override { return {}; }
};

void Prepare(Adapter &adapter, api::MainThreadQueryMailboxV1 &mailbox,
             FamilyObligationsMailboxContext12002 &query,
             api::MainThreadExecutionStampV1 &stamp) {
  adapter.frame = {};
  adapter.reads = 0; adapter.drift = false;
  adapter.frame.paused = adapter.frame.map_ready = true;
  adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
  adapter.frame.played_character_id = actor_id;
  adapter.frame.date_raw = 53220000;
  query.envelope = {};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 53;
  query.envelope.ticket.sequence = 5;
  query.envelope.typed_context = &query;
  query.completed = false;
  mailbox.state = api::MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = 5; mailbox.owner_thread_id = adapter.owner;
  mailbox.executor = &ExecuteFamilyObligationsMailbox12002;
  mailbox.executor_context = &query.envelope;
  stamp = {};
  stamp.pump_epoch = 5; stamp.thread_id = adapter.owner;
  stamp.paused = true; stamp.date_raw = adapter.frame.date_raw;
  stamp.tls_initialized = stamp.tls_main_thread_marker = 1;
  stamp.tls_context = stamp.jomini_state = stamp.game_state = 1;
}
}
int main(int argc, char **argv) {
  try {
    Components components{};
    Put(subject.data(), family_value::kCharacterHouseOffset, subject_house);
    Put(candidate.data(), family_value::kCharacterHouseOffset, candidate_house);
    std::uint32_t option_id = 9;
    family_obligations_lineage::Bindings b{}; b.enabled = true; b.family.enabled = true; b.family.context.core.enabled = true;
    b.family.values.enabled = true; b.family.values.core.enabled = true;
    b.family.values.house_store = &components.houses; b.family.values.house_fallback = &components.house_fallback;
    b.family.values.dynasty_store = &components.dynasties; b.family.values.dynasty_fallback = &components.dynasty_fallback;
    b.family.read_boolean_option = ReadOption; b.family.matrilineal_option = &option_id;
    b.family.context.refresh = Refresh; b.family.context.finalize = Finalize;
    b.native_preview_parent = NativeParent; b.native_offer_vtable = 0x12002;

    Adapter adapter{}; api::MainThreadQueryMailboxV1 mailbox{};
    FamilyObligationsMailboxContext12002 query{};
    api::MainThreadExecutionStampV1 stamp{};
    query.lineage_bindings = b;
    query.observation.request = {subject_id, candidate_id, -1, -1, true, 53};
    selected = false;
    Put(subject.data(), family_value::kCharacterSexSelectorOffset, std::uint8_t{1});
    Prepare(adapter, mailbox, query, stamp);
    Check(ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp) &&
          query.completed && query.envelope.frame_stable && query.observation.lineage_available,
          "actual native lineage reader completes on owning mailbox thread");
    Check(query.observation.lineage.native_selected_parent_character_id == subject_id &&
          query.observation.lineage.native_preview_lineage.house_id == subject_house &&
          query.observation.lineage.selected_matrilineal_option &&
          !query.observation.lineage.effective_matrilineal_if_accepted,
          "real native preview and resolved full house IDs survive the mailbox");
    Check(FamilyObligationsQueryStatus12002(query.observation) == "available" &&
          contexts == destroys, "omitted unrelated lanes and native context lifetime");
    const auto actual_wire = SerializeFamilyObligationsResult12002("family-obligations-mailbox-fixture", query.observation);
    if (argc == 2) {
      std::ofstream output(argv[1], std::ios::binary); output << actual_wire << '\n';
      Check(static_cast<bool>(output), "actual provider mailbox wire output");
    }
    query.observation.request.ally_character_id = candidate_id;
    Prepare(adapter, mailbox, query, stamp);
    ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp);
    Check(query.completed && query.envelope.frame_stable && query.observation.lineage_available &&
          FamilyObligationsQueryStatus12002(query.observation) == "partial" &&
          !query.observation.alliance_available &&
          SerializeFamilyObligationsObservation12002(query.observation).find("alliance_war_binding_unavailable") != std::string::npos,
          "unbound requested war source stays unavailable and preserves actual child lineage");
    query.observation.request.ally_character_id = -1;
    query.observation.request.break_recipient_character_id = candidate_id;
    query.break_bindings.enabled = query.break_bindings.interaction.enabled = true;
    Prepare(adapter, mailbox, query, stamp);
    ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp);
    Check(query.completed && query.envelope.frame_stable &&
          query.observation.break_terms.status == FamilyObligationsBreakStatusV1::no_betrothal &&
          FamilyObligationsQueryStatus12002(query.observation) == "available",
          "actual break reader observes subject genuinely has no betrothal");
    Prepare(adapter, mailbox, query, stamp); adapter.drift = true;
    ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp);
    Check(query.completed && !query.envelope.frame_stable, "post-read full snapshot drift rejects current frame");
    Prepare(adapter, mailbox, query, stamp);
    std::thread worker([&] { ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp); }); worker.join();
    Check(!query.completed, "worker cannot call owning-thread native readers");
    FamilyObligationsRequest12002 request{};
    const std::string payload = "{\"subject_character_id\":16777218,\"candidate_character_id\":16777219,\"request_matrilineal_option\":true,\"expected_snapshot_revision\":53}";
    Check(ParseFamilyObligationsPrivateRequest12002(payload, request) &&
          request.subject_character_id == subject_id && request.request_matrilineal_option &&
          request.ally_character_id == -1, "concrete fixed request grammar");
    for (const auto invalid : {"{}", "{\"subject_character_id\":1,\"candidate_character_id\":1}",
         "{\"subject_character_id\":1,\"candidate_character_id\":2147483648}",
         "{\"subject_character_id\":1,\"candidate_character_id\":2,\"ally_character_id\":0}",
         "{\"subject_character_id\":1,\"candidate_character_id\":2,\"request_matrilineal_option\":1}"})
      Check(!ParseFamilyObligationsPrivateRequest12002(invalid, request), "invalid native query identity rejected");
    Check(IsFamilyObligationsPrivateStep12002(kFamilyObligationsPrivateStep12002) &&
          !IsFamilyObligationsPrivateStep12002("read-family-obligations"), "single private selector");
    std::string wire, failure; const auto reads = adapter.reads;
    Check(!HandleFamilyObligationsPrivate12002(adapter, mailbox, adapter.frame, 54,
          kFamilyObligationsPrivateStep12002, payload, "stale", wire, failure) &&
          failure == "family_obligations_current_frame_unavailable" && reads == adapter.reads,
          "worker stale request cannot reach native read");
    const std::string deferred_self_payload = "{\"subject_character_id\":16777218,\"candidate_character_id\":16777219,\"ally_character_id\":16777217,\"expected_snapshot_revision\":53}";
    Check(!HandleFamilyObligationsPrivate12002(adapter, mailbox, adapter.frame, 53,
          kFamilyObligationsPrivateStep12002, deferred_self_payload, "deferred-self", wire, failure) &&
          failure == "family_obligations_mailbox_submit_unavailable",
          "deferred ally argument cannot reject unrelated nonwar current frame");
    std::cout << "PASS actual lineage provider -> owner mailbox -> native wire; deferred ally lane, genuine no-betrothal, thread/frame semantics\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
