#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/crown_authority_cooldown_observer_12004.hpp"
#include "xar_bridge/crown_authority_cooldown_turn_tick_12004.hpp"
#include "xar_bridge/realm_law_12004_native.hpp"

#include <windows.h>

#include <array>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>

using namespace xar::ck3_12002;
namespace {
namespace game = xar::game;
namespace mailbox_api = xar::ck3_11906;
constexpr std::uintptr_t base = 0x10000000, image = 0x140000000;
constexpr std::uintptr_t actor = base + 0x100, context = base + 0x400,
    active_slots = base + 0x800, database = base + 0x1000,
    crown = base + 0x1400, succession = base + 0x1800,
    groups = base + 0x1C00, crown_slots = base + 0x2000,
    succession_slots = base + 0x2100;
constexpr std::array<std::uintptr_t, 4> laws{base + 0x3000, base + 0x4000,
    base + 0x5000, base + 0x6000};
struct Memory {
  std::array<std::byte, 0x10000> bytes{};
  struct NativeSpan {
    std::uintptr_t address = 0;
    std::size_t size = 0;
  };
  std::array<NativeSpan, 16> native_spans{};
  std::size_t native_span_count = 0;
  std::uintptr_t extra_slot_address = 0, extra_slot_value = 0;
  std::uintptr_t denied_address = 0;
  std::size_t denied_size = 0, denied_reads = 0;
  template <class T> void Map(const T &value) {
    assert(native_span_count < native_spans.size());
    native_spans[native_span_count++] = {
        reinterpret_cast<std::uintptr_t>(&value), sizeof(value)};
  }
  template <class T> void Store(std::uintptr_t address, const T &value) {
    std::memcpy(bytes.data() + address - base, &value, sizeof(value));
  }
  void Key(std::uintptr_t address, std::string_view text, std::uintptr_t heap) {
    Store(address + 0x18, heap);
    Store(address + 0x28, static_cast<std::uint64_t>(text.size()));
    Store(address + 0x30, std::uint64_t{63});
    std::memcpy(bytes.data() + heap - base, text.data(), text.size());
  }
  static bool Read(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(opaque);
    if (memory.denied_address != 0 && size != 0 &&
        ((address >= memory.denied_address &&
          address - memory.denied_address < memory.denied_size) ||
         (address < memory.denied_address &&
          memory.denied_address - address < size))) {
      ++memory.denied_reads;
      return false;
    }
    if (memory.extra_slot_address != 0 && address == memory.extra_slot_address &&
        size == sizeof(memory.extra_slot_value)) {
      std::memcpy(out, &memory.extra_slot_value, size);
      return true;
    }
    if (address == image + private_law::kLawGroupDatabaseSingletonRva12002 ||
        address == image + xar::ck3_12004::private_law::kLawGroupDatabaseSingletonRva12004) {
      std::memcpy(out, &database, size); return true;
    }
    if (address >= base && size <= memory.bytes.size() &&
        address - base <= memory.bytes.size() - size) {
      std::memcpy(out, memory.bytes.data() + address - base, size);
      return true;
    }
    for (std::size_t i = 0; i < memory.native_span_count; ++i) {
      const auto &span = memory.native_spans[i];
      if (address >= span.address && size <= span.size &&
          address - span.address <= span.size - size) {
        std::memcpy(out, reinterpret_cast<const void *>(address), size);
        return true;
      }
    }
    return false;
  }
};
std::size_t LawIndex(const void *law) {
  const auto address = reinterpret_cast<std::uintptr_t>(law);
  for (std::size_t i = 0; i < laws.size(); ++i) if (address == laws[i]) return i;
  assert(false); return 0;
}
bool Kind(const void *) { return true; }
bool Active(const void *who, const void *law) {
  assert(reinterpret_cast<std::uintptr_t>(who) == actor);
  return LawIndex(law) % 2 == 0;
}
bool Final(const void *law, const void *, void *) { return LawIndex(law) == 1; }
std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t who) {
  assert(who == 29829);
  const auto index = LawIndex(reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(block) - private_law::kRealmLawCompiledCostOffset));
  for (std::size_t i = 0; i < 10; ++i) out[i] = index == 1 ? static_cast<std::int64_t>(i) * 300003 : 0;
  return out;
}
bool Reason(const void *law, const void *, void *out) {
  static constexpr char blocked[] = "Fixture native reason: council \"no\"\n";
  const auto index = LawIndex(law);
  const char *text = index == 1 ? "" : blocked;
  const std::uint64_t size = std::strlen(text), capacity = size > 15 ? size : 15;
  auto *sink = static_cast<std::byte *>(out);
  if (size > 15) std::memcpy(sink, &text, sizeof(text));
  std::memcpy(sink + 0x10, &size, 8); std::memcpy(sink + 0x18, &capacity, 8);
  return index == 1;
}
void Destroy(void *) {}
void InitializeLawMemory(Memory &memory) {
  memory.Store(actor + 0x1C0, context);
  memory.Store(context + 0x200, active_slots);
  memory.Store(context + 0x20C, std::int32_t{2});
  memory.Store(active_slots, laws[0]); memory.Store(active_slots + 8, laws[2]);
  memory.Store(database + 0x50, groups); memory.Store(database + 0x5C, std::int32_t{2});
  memory.Store(groups, crown); memory.Store(groups + 8, succession);
  memory.Key(crown, "crown_authority", base + 0x7000);
  memory.Key(succession, "succession_order_laws", base + 0x7100);
  memory.Store(crown + 0x58, crown_slots); memory.Store(crown + 0x64, std::int32_t{2});
  memory.Store(succession + 0x58, succession_slots); memory.Store(succession + 0x64, std::int32_t{2});
  constexpr std::array<std::string_view, 4> keys{"crown_authority_0", "crown_authority_1",
      "confederate_partition_succession_law", "high_partition_succession_law"};
  for (std::size_t i = 0; i < laws.size(); ++i) {
    memory.Store((i < 2 ? crown_slots : succession_slots) + (i % 2) * 8, laws[i]);
    memory.Store(laws[i] + 0x40, i < 2 ? crown : succession);
    memory.Key(laws[i], keys[i], base + 0x7200 + i * 0x100);
  }
}

enum class TurnTickScene {
  late_exact_context_match,
  complete_known_not_member,
  legitimate_empty_manager,
  member_zero_scalars,
  member_untimed_tail,
  bucket_read_unavailable,
};
constexpr std::array<std::pair<std::string_view, TurnTickScene>, 6>
    turn_tick_scenes{{
        {"late-exact-context-match", TurnTickScene::late_exact_context_match},
        {"complete-known-not-member", TurnTickScene::complete_known_not_member},
        {"legitimate-empty-manager", TurnTickScene::legitimate_empty_manager},
        {"member-zero-scalars", TurnTickScene::member_zero_scalars},
        {"member-untimed-tail", TurnTickScene::member_untimed_tail},
        {"bucket-read-unavailable", TurnTickScene::bucket_read_unavailable},
    }};
template <std::size_t N, class T>
void StoreNative(std::array<std::byte, N> &object, std::size_t offset,
                 const T &value) {
  assert(offset <= N && sizeof(value) <= N - offset);
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

struct TurnTickMemoryFixture {
  Memory memory{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0xA8> game_data{};
  std::array<std::byte, 0x30> full_context{}, other_context_a{}, other_context_b{};
  std::array<std::byte, 0x40> scalar_rows{};
  std::array<std::array<std::byte, 0x10>, 3> buckets{};
  std::array<std::uintptr_t, 3> outer_entries{};
  std::array<std::uintptr_t, 2> early_entries{}, late_entries{};
  explicit TurnTickMemoryFixture(TurnTickScene scene) {
    InitializeLawMemory(memory);
    const auto current = reinterpret_cast<std::uintptr_t>(full_context.data());
    const auto other_a = reinterpret_cast<std::uintptr_t>(other_context_a.data());
    const auto other_b = reinterpret_cast<std::uintptr_t>(other_context_b.data());
    StoreNative(game_state, 0xA0,
                reinterpret_cast<std::uintptr_t>(game_data.data()));
    StoreNative(full_context, 0x10,
                reinterpret_cast<std::uintptr_t>(scalar_rows.data()));
    StoreNative(full_context, 0x1C, std::int32_t{2});
    StoreNative(full_context, 0x28, std::int32_t{7});
    StoreNative(scalar_rows, 0x08, std::int32_t{0x01000006});
    StoreNative(scalar_rows, 0x0C, std::int32_t{27});
    StoreNative(scalar_rows, 0x28, std::int32_t{0x01000007});
    StoreNative(scalar_rows, 0x2C, std::int32_t{37});
    early_entries = {other_a, other_b};
    late_entries = {current, current};
    if (scene == TurnTickScene::complete_known_not_member)
      late_entries = {other_b, other_a};
    StoreNative(buckets[0], 0,
                reinterpret_cast<std::uintptr_t>(early_entries.data()));
    StoreNative(buckets[0], 0x0C, std::int32_t{2});
    StoreNative(buckets[2], 0,
                reinterpret_cast<std::uintptr_t>(late_entries.data()));
    StoreNative(buckets[2], 0x0C, std::int32_t{2});
    // The middle bucket is valid and empty; the exact match is later.
    outer_entries = {reinterpret_cast<std::uintptr_t>(buckets[0].data()),
                     reinterpret_cast<std::uintptr_t>(buckets[1].data()),
                     reinterpret_cast<std::uintptr_t>(buckets[2].data())};
    StoreNative(game_data, 0x98,
                reinterpret_cast<std::uintptr_t>(outer_entries.data()));
    StoreNative(game_data, 0xA4, std::int32_t{3});
    if (scene == TurnTickScene::legitimate_empty_manager) {
      StoreNative(game_data, 0x98, std::uintptr_t{0});
      StoreNative(game_data, 0xA4, std::int32_t{0});
    }
    if (scene == TurnTickScene::legitimate_empty_manager ||
        scene == TurnTickScene::member_zero_scalars) {
      StoreNative(full_context, 0x10, std::uintptr_t{0});
      StoreNative(full_context, 0x1C, std::int32_t{0});
    }
    if (scene == TurnTickScene::member_zero_scalars ||
        scene == TurnTickScene::member_untimed_tail) {
      early_entries[0] = current;
      StoreNative(buckets[0], 0x0C, std::int32_t{1});
      StoreNative(game_data, 0xA4, std::int32_t{1});
    }
    if (scene == TurnTickScene::member_untimed_tail) {
      StoreNative(full_context, 0x1C, std::int32_t{1});
      StoreNative(scalar_rows, 0x0C, std::int32_t{-1});
    }
    if (scene == TurnTickScene::bucket_read_unavailable) {
      memory.denied_address = reinterpret_cast<std::uintptr_t>(&late_entries[1]);
      memory.denied_size = sizeof(late_entries[1]);
    }
    memory.Map(game_state);
    memory.Map(game_data);
    memory.Map(full_context);
    memory.Map(other_context_a);
    memory.Map(other_context_b);
    memory.Map(scalar_rows);
    memory.Map(buckets);
    memory.Map(outer_entries);
    memory.Map(early_entries);
    memory.Map(late_entries);
  }
};

TurnTickMemoryFixture *active_turn_tick_fixture = nullptr;
std::size_t turn_tick_context_resolves = 0;
int variable_table_cookie = 0;
const std::string cooldown_key = "crown_authority_cooldown";
void *CooldownVariableTable() { return &variable_table_cookie; }
std::int32_t *CooldownVariableLookup(
    void *table, std::int32_t *out, const PhaseStringView32 *view) {
  assert(table == &variable_table_cookie && out && view && view->pad == 0);
  assert(std::string_view(view->data, view->size) == cooldown_key);
  *out = 0x01000006;
  return out;
}
const std::string *CooldownVariableName(void *table, std::int32_t id) {
  assert(table == &variable_table_cookie);
  return id == 0x01000006 ? &cooldown_key : nullptr;
}
void *CooldownVariableContext(const PhaseVariableTarget *target) {
  assert(active_turn_tick_fixture && target && target->kind == 4 &&
         target->payload == 29829);
  ++turn_tick_context_resolves;
  return active_turn_tick_fixture->full_context.data();
}
xar::ck3_12004::crown_cooldown::Bindings FixtureCooldownBindings() {
  xar::ck3_12004::crown_cooldown::Bindings binding{};
  binding.identifiers.enabled = true;
  binding.identifiers.variable_table = &CooldownVariableTable;
  binding.identifiers.lookup_variable_identifier = &CooldownVariableLookup;
  binding.identifiers.variable_identifier_name = &CooldownVariableName;
  binding.identifiers.variable_context = &CooldownVariableContext;
  return binding;
}
constexpr RealmLawReadbackFrame12002 turn_tick_frame{9, 53169072, 29829};
std::string TurnTickRequestId(std::string_view name) {
  std::size_t ordinal = 0;
  for (std::size_t i = 0; i < turn_tick_scenes.size(); ++i)
    if (name == turn_tick_scenes[i].first) ordinal = i + 1;
  if (name == "legacy-leaf-absent") ordinal = turn_tick_scenes.size() + 1;
  assert(ordinal != 0);
  std::ostringstream out;
  out << "realm-law-read-" << std::hex << std::setw(32) << std::setfill('0')
      << ordinal;
  return out.str();
}
void WriteTurnTickWholeWire(const std::filesystem::path &directory,
                           std::string_view name,
                           std::string_view native_readback) {
  const auto wire = SerializeRealmLawReadbackCommandResult12002(
      TurnTickRequestId(name), native_readback, turn_tick_frame.snapshot_revision);
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << wire << '\n';
  assert(out.good());
}
void WriteTurnTickReceipt(const std::filesystem::path &directory) {
  std::ofstream out(directory / "fixture-receipt.json", std::ios::binary);
  out << "{\"schema\":\"xar.ck3.crown-authority-cooldown-turn-tick-context-native-whole-fixture12004/v1\","
         "\"status\":\"GREEN\",\"live\":false,\"old_cases_executed\":0,"
         "\"law_action_calls\":0,\"cases\":6,\"whole_wire_files\":[";
  for (const auto &scene : turn_tick_scenes)
    out << '\"' << scene.first << ".json\",";
  out << "\"legacy-leaf-absent.json\"],\"frame\":{"
         "\"public_revision\":2,\"native_revision\":"
      << turn_tick_frame.snapshot_revision << ",\"date_raw\":"
      << turn_tick_frame.date_raw << ",\"actor_character_id\":"
      << turn_tick_frame.actor_character_id
      << ",\"paused\":true,\"map_ready\":true},\"case_frames\":[";
  for (std::size_t i = 0; i <= turn_tick_scenes.size(); ++i) {
    const std::string_view name = i == turn_tick_scenes.size()
        ? "legacy-leaf-absent" : turn_tick_scenes[i].first;
    if (i != 0) out << ',';
    out << "{\"file\":\"" << name << ".json\",\"request_id\":\""
        << TurnTickRequestId(name) << "\",\"native_revision\":"
        << turn_tick_frame.snapshot_revision << ",\"date_raw\":"
        << turn_tick_frame.date_raw << ",\"actor_character_id\":"
        << turn_tick_frame.actor_character_id << '}';
  }
  out << "]}\n";
  assert(out.good());
}
class TurnTickFrameAdapter final : public game::GameAdapter {
 public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0, commands = 0;
  game::AdapterDescriptor identity{xar::ck3_12004::kAdapterId,
      xar::ck3_12004::kGameVersion, xar::ck3_12004::kExecutableSha256,
      "turn-tick-context-whole-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    ++reads;
    out = frame;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { ++commands; return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { ++commands; return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) \
  game::Result Name Params const noexcept override { ++commands; return game::Result::unavailable; }
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
void AssertTurnTickScene(
    TurnTickScene scene,
    const xar::ck3_12004::crown_cooldown::turn_tick::Observation &observed) {
  if (scene == TurnTickScene::bucket_read_unavailable) {
    assert(!observed.read_available && !observed.manager_match_count &&
           !observed.manager_contains_context && !observed.scalar_tail_allows_tick &&
           !observed.context_tick_eligible && !observed.unavailable_reason.empty());
    return;
  }
  assert(observed.read_available && observed.unavailable_reason.empty());
  const bool member = scene != TurnTickScene::complete_known_not_member &&
                      scene != TurnTickScene::legitimate_empty_manager;
  const bool tail = scene == TurnTickScene::late_exact_context_match ||
                    scene == TurnTickScene::complete_known_not_member;
  const std::uint64_t count = scene == TurnTickScene::late_exact_context_match
      ? 2 : member ? 1 : 0;
  assert(observed.manager_match_count == count);
  assert(observed.manager_contains_context == member);
  assert(observed.scalar_tail_allows_tick == tail);
  assert(observed.context_tick_eligible == (member && tail));
}
int RunTurnTickContextWholeFixture(const std::filesystem::path &directory) {
  std::filesystem::create_directories(directory);
  for (const auto &scene : turn_tick_scenes) {
    TurnTickMemoryFixture fixture(scene.second);
    active_turn_tick_fixture = &fixture;
    turn_tick_context_resolves = 0;
    fixture.memory.extra_slot_address = image + xar::ck3_12004::kGameStateSlotRva;
    fixture.memory.extra_slot_value =
        reinterpret_cast<std::uintptr_t>(fixture.game_state.data());
    const private_law::RealmLawActiveCollectionAccess access{
        xar::ck3_12004::kExecutableSha256, actor, &fixture.memory, &Memory::Read};
    const private_law::RealmLawFinalTerms12002Operations operations{
        {&Kind, &Active, &Final, &Cost}, &Reason, &Destroy};
    const auto cooldown = FixtureCooldownBindings();
    TurnTickFrameAdapter adapter;
    adapter.frame.date_raw = turn_tick_frame.date_raw;
    adapter.frame.speed = 0;
    adapter.frame.paused = true;
    adapter.frame.player_id = 1;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = turn_tick_frame.actor_character_id;
    adapter.frame.played_character_alive = true;
    mailbox_api::MainThreadQueryMailboxV1 mailbox{};
    RealmLawTurnTickQuery12004 owner{};
    auto &query = owner.query;
    auto &envelope = query.envelope;
    envelope.game = &adapter;
    envelope.mailbox = &mailbox;
    envelope.ticket.sequence = 1;
    envelope.expected_snapshot = adapter.frame;
    envelope.expected_snapshot_revision = turn_tick_frame.snapshot_revision;
    envelope.typed_context = &owner;
    query.module_base = image;
    query.actual_executable_sha256 = xar::ck3_12004::kExecutableSha256;
    query.collection_access_override = &access;
    query.final_operations_override = &operations;
    query.cooldown_bindings_override = &cooldown;
    const auto thread_id = GetCurrentThreadId();
    mailbox.state = mailbox_api::MainThreadQueryMailboxStateV1::executing;
    mailbox.published_sequence = envelope.ticket.sequence;
    mailbox.owner_thread_id = thread_id;
    mailbox.executor = &ExecuteRealmLawPausedPrivateQueryWithTurnTick12004;
    mailbox.executor_context = &envelope;
    mailbox_api::MainThreadExecutionStampV1 stamp{};
    stamp.thread_id = thread_id;
    stamp.pump_epoch = 3;
    stamp.paused = true;
    stamp.date_raw = turn_tick_frame.date_raw;
    stamp.tls_initialized = 1;
    stamp.tls_main_thread_marker = 1;
    stamp.tls_context = reinterpret_cast<std::uintptr_t>(&variable_table_cookie);
    stamp.jomini_state = reinterpret_cast<std::uintptr_t>(&fixture);
    stamp.game_state = reinterpret_cast<std::uintptr_t>(fixture.game_state.data());
    assert(ExecuteRealmLawPausedPrivateQueryWithTurnTick12004(&envelope, stamp));
    assert(envelope.entered && envelope.frame_stable && adapter.reads == 2 &&
           adapter.commands == 0 && turn_tick_context_resolves == 1);
    assert(query.readback.available && query.readback.crown_authority_cooldown_observed &&
           query.readback.crown_authority_cooldown.read_available);
    assert(query.readback.final[0][1].terms.status ==
           private_law::RealmLawFinalTerms12002Status::can_enact);
    assert(query.readback.final[1][1].terms.status ==
           private_law::RealmLawFinalTerms12002Status::engine_blocked);
    AssertTurnTickScene(scene.second, owner.turn_tick);
    assert(fixture.memory.denied_reads ==
           (scene.second == TurnTickScene::bucket_read_unavailable ? 1U : 0U));
    const auto serialized = SerializeRealmLawReadbackWithTurnTick12004(
        query.readback, owner.turn_tick);
    WriteTurnTickWholeWire(directory, scene.first, serialized);
    if (scene.second == TurnTickScene::late_exact_context_match) {
      // Same successful capture, original serializer: no old case is executed.
      WriteTurnTickWholeWire(directory, "legacy-leaf-absent",
                            SerializeRealmLawReadback12002(query.readback));
    }
    active_turn_tick_fixture = nullptr;
  }
  WriteTurnTickReceipt(directory);
  std::cout << "PASS: six real-memory same-query TurnTick scenes -> seven whole law wires\n";
  return 0;
}
}
int main(int argc, char **argv) {
  if (argc == 3 && std::string_view(argv[1]) == "--turn-tick-context-wire-dir")
    return RunTurnTickContextWholeFixture(argv[2]);
  Memory memory{};
  InitializeLawMemory(memory);
  const private_law::RealmLawActiveCollectionAccess access{
      private_law::kRealmLawActiveCollectionExeSha25612002, actor, &memory, &Memory::Read};
  const private_law::RealmLawFinalTerms12002Operations operations{
      {&Kind, &Active, &Final, &Cost}, &Reason, &Destroy};
  RealmLawReadback12002 readback{};
  assert(CaptureRealmLawReadback12002(access, image, {74, 53169072, 29829}, operations, readback));
  assert(readback.collection.groups[0].candidate_count == 2 && readback.collection.groups[1].candidate_count == 2);
  assert(readback.final[0][1].terms.status == private_law::RealmLawFinalTerms12002Status::can_enact);
  assert(readback.final[1][1].terms.status == private_law::RealmLawFinalTerms12002Status::engine_blocked);
  const auto serialized = SerializeRealmLawReadback12002(readback);
  assert(serialized.find("council \\\"no\\\"\\u000a") != std::string::npos);
  if (argc == 2) { std::ofstream out(argv[1], std::ios::binary); out << serialized << '\n'; assert(out.good()); }
  std::cout << "PASS: actual 1.20 native-layout collections -> final terms -> existing JSON DTO wire\n";
}
