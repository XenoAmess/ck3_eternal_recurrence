#include "xar_bridge/army_strength_result_write_diagnostic_v1.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/scripted_widget_control12004.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <array>
#include <cstdlib>
#include <limits>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <thread>
#include <utility>
#include <vector>

extern "C" BOOL (WINAPI *__imp_WriteFile)(HANDLE, LPCVOID, DWORD, LPDWORD, LPOVERLAPPED);

namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;

#define CHECK(expression) do { if (!(expression)) { \
  std::fprintf(stderr, "semantic fixture line %d: %s\n", __LINE__, #expression); \
  return false; } } while (false)

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset, Value value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct MemoryFixture {
  void *iat = nullptr;
  DWORD page_protect = PAGE_READONLY;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> state{};
  std::array<std::byte, 0x28> tls{};
  std::uintptr_t jomini_slot = 0;
  std::uintptr_t state_slot = 0;
  std::uintptr_t null_rng_slot = 0;
  std::uint8_t tls_initialized = 1;
};
MemoryFixture *g_memory = nullptr;

BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
void *__fastcall FakeTls() noexcept { return g_memory->tls.data(); }
bool FakeQuery(void *opaque, const void *address,
               MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (address != &memory.iat) return false;
  output = {};
  output.BaseAddress = reinterpret_cast<void *>(
      reinterpret_cast<std::uintptr_t>(address) & ~4095ULL);
  output.AllocationBase = output.BaseAddress;
  output.RegionSize = 4096;
  output.State = MEM_COMMIT;
  output.Type = MEM_IMAGE;
  output.Protect = memory.page_protect;
  return true;
}
bool FakeProtect(void *opaque, void *, std::size_t size, DWORD desired,
                 DWORD &previous) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (size != 4096) return false;
  previous = memory.page_protect;
  memory.page_protect = desired;
  return true;
}

class FixtureAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> raw_reads{0};
  mutable std::atomic<std::uint32_t> semantic_calls{0};
  mutable std::atomic<std::uint32_t> wrong_owner{0};
  mutable std::atomic<DWORD> queue_thread{0};
  mutable std::atomic<std::int32_t> last_event_option{-1};
  mutable std::atomic<std::int32_t> last_army{-1};
  mutable std::atomic<std::int32_t> last_province{-1};
  mutable std::atomic<std::int32_t> last_family_subject{-1};
  bool reader_available = true;
  bool declarations_available = true;
  bool family_available = true;
  bool patch3 = false;
  bool patch4 = false;

  FixtureAdapter() {
    frame.date_raw = 123456;
    frame.speed = 3;
    frame.player_id = 7;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_id = 0x12000015;
    frame.played_character_alive = true;
    frame.has_active_event = true;
    frame.active_event_instance_id = 91;
    frame.active_event_option_count = 3;
    game::ArmySnapshot army{};
    army.army_id = 0x23000031;
    army.owner_character_id = frame.played_character_id;
    army.controllable = true;
    army.has_current_province = true;
    army.current_province_id = 900;
    frame.player_armies.push_back(army);
  }

  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 2> capabilities{
      "game.state.snapshot", "game.query.fresh-full-state.v1"};
    static const game::AdapterDescriptor value{
      xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion,
      xar::ck3_12004::kExecutableSha256, "offline-fresh-fixture",
      std::span<const std::string_view>{capabilities}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  void RecordSemantic() const noexcept {
    ++semantic_calls;
    if (GetCurrentThreadId() != owner) ++wrong_owner;
  }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++raw_reads;
    if (GetCurrentThreadId() != owner) {
      ++wrong_owner;
      output = {};
      return false;
    }
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::ResumeSubmitResult::submitted;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    queue_thread = GetCurrentThreadId();
    return speed == 4;
  }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return {game::SaveCheckpointStatus::submitted, 123456};
  }
  game::SelectEventOptionResult submit_select_event_option(
      std::int32_t option) const noexcept override {
    RecordSemantic();
    last_event_option = option;
    return option < 0 || option >= frame.active_event_option_count
      ? game::SelectEventOptionResult::option_out_of_range
      : game::SelectEventOptionResult::submitted;
  }
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return false;
    output.push_back({0x14000042, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return true;
  }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_id,
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return game::ReadDeclarableWarsResult::unavailable;
    if (target_id != 0x14000042) return game::ReadDeclarableWarsResult::target_not_found;
    output.push_back({target_id, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return game::ReadDeclarableWarsResult::available;
  }
  game::MoveArmyResult submit_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    RecordSemantic();
    last_army = army;
    last_province = province;
    return army == frame.player_armies.front().army_id && province == 901
      ? game::MoveArmyResult::submitted : game::MoveArmyResult::validation_failed;
  }
  game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<game::ArmyStrengthSnapshot> &output) const noexcept override {
    RecordSemantic();
    game::ArmyStrengthSnapshot row{};
    row.available = true;
    row.army_id = frame.player_armies.front().army_id;
    row.regiment_count = 2;
    row.current_soldiers = 734;
    row.maximum_soldiers = 1000;
    row.ai_base_power_raw = 123456789;
    output = {row};
    return game::ReadArmyStrengthsResult::available;
  }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    output = {{frame.played_character_id, 0x15000011}};
    diagnostics = {};
    diagnostics.storage_capacity = 17;
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageChoicesResult::available;
  }
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept override {
    RecordSemantic();
    output = {};
    if (frame.active_wars.empty() || frame.active_wars.front().war_id != war_id)
      return game::ReadWarTerminationOptionsResult::war_not_found;
    output.war_id = war_id;
    output.player_relative_war_score = frame.active_wars.front().player_relative_war_score;
    return game::ReadWarTerminationOptionsResult::available;
  }
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    last_family_subject = subject_id;
    output.clear();
    diagnostics = {};
    if (subject_id != 0x13000016)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::subject_not_found;
    diagnostics.storage_capacity = 17;
    diagnostics.slots_scanned = 2;
    if (!family_available)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = frame.played_character_id;
    row.subject_character_id = subject_id;
    row.candidate_character_id = 0x15000011;
    row.recipient_matchmaker_character_id = 0x14000042;
    row.recipient_ai_accept_raw = 2'500'000;
    row.recipient_answer_status_raw = 1;
    row.complete_can_send = true;
    row.recipient_answer_allows_send = true;
    row.heir_adult_measure_raw = std::int16_t{17};
    row.candidate_adult_measure_raw = std::int16_t{19};
    row.played_dynasty_id = 71;
    row.heir_dynasty_id = 71;
    row.candidate_dynasty_id = 72;
    row.realm_backed_actor_recipient = true;
    output.push_back(row);
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageFamilyCandidatesResultV1::available;
  }

#define UNAVAILABLE_RESULT(Result, Name, Parameters) \
  game::Result Name Parameters const noexcept override { \
    RecordSemantic(); return game::Result::unavailable; }
  UNAVAILABLE_RESULT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
                     (game::PendingInteractionReply))
  UNAVAILABLE_RESULT(AcknowledgePendingInteractionResult, submit_acknowledge_pending_interaction,
                     (std::int32_t))
  UNAVAILABLE_RESULT(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE_RESULT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE_RESULT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE_RESULT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE_RESULT(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE_RESULT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE_RESULT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE_RESULT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE_RESULT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE_RESULT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE_RESULT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationTermsResult, read_war_termination_terms,
                     (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
                     (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef UNAVAILABLE_RESULT
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override {
    RecordSemantic();
    return {};
  }
};

// Test-only local seam; not a production API or runtime platform.

#include "fresh_bridge_snapshot_support.inc"
#include "fresh_bridge_worker_state.inc"
struct WarEntryApplicationMainMailboxWorkerLifetime {
  void MaybeInstall(const game::Snapshot &) noexcept { std::terminate(); }
};
#include "fresh_bridge_publish.inc"
#include "fresh_bridge_command_result.inc"
#include "fresh_bridge_handler.inc"
bool ReadFreshSuccessPair(HANDLE reader, std::string_view request_id, std::uint64_t expected_revision) {
  if (expected_revision == 0) return false;
  auto r1 = xar::bridge::TryReadFrame(reader);
  if (r1.status != xar::bridge::ReadStatus::frame) return false;
  std::string type;
  if (!xar::bridge::JsonStringField(r1.payload, "type", type, 128) || type != "state_snapshot") return false;
  std::uint64_t pv;
  if (!xar::bridge::JsonUnsignedField(r1.payload, "protocol_version", pv) || pv != 1) return false;
  std::string rid;
  if (!xar::bridge::JsonStringField(r1.payload, "read_request_id", rid, 128) || rid != request_id) return false;
  std::string sid;
  if (!xar::bridge::JsonStringField(r1.payload, "snapshot_id", sid, 128)) return false;
  std::uint64_t rev;
  if (!xar::bridge::JsonUnsignedField(r1.payload, "revision", rev) || rev != expected_revision) return false;
  if (sid != "native:" + std::to_string(expected_revision)) return false;
  auto r2 = xar::bridge::TryReadFrame(reader);
  if (r2.status != xar::bridge::ReadStatus::frame) return false;
  std::string expected_ack = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(expected_ack, request_id);
  expected_ack += ",\"ok\":true,\"result\":{\"schema\":";
  AppendJsonString(expected_ack, "xar.native.fresh-full-state-read/v1");
  expected_ack += ",\"request_id\":";
  AppendJsonString(expected_ack, request_id);
  expected_ack += ",\"snapshot_id\":";
  AppendJsonString(expected_ack, "native:" + std::to_string(expected_revision));
  expected_ack += ",\"revision\":";
  expected_ack += std::to_string(expected_revision);
  expected_ack += "}}";
  if (r2.payload != expected_ack) return false;
  auto r3 = xar::bridge::TryReadFrame(reader);
  return r3.status == xar::bridge::ReadStatus::none;
}
bool ReadFreshFailureOnly(HANDLE reader, std::string_view request_id, std::string_view expected_error) {
  auto r1 = xar::bridge::TryReadFrame(reader);
  if (r1.status != xar::bridge::ReadStatus::frame) return false;
  std::string expected_err = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(expected_err, request_id);
  expected_err += ",\"ok\":false,\"error\":";
  AppendJsonString(expected_err, expected_error);
  expected_err += "}";
  if (r1.payload != expected_err) return false;
  auto r2 = xar::bridge::TryReadFrame(reader);
  return r2.status == xar::bridge::ReadStatus::none;
}
struct FreshAckWorkerProbe {
  std::atomic<build::WorkerAdapter *> proxy{nullptr};
  std::atomic<std::uint32_t> requested{0};
  std::atomic<std::uint32_t> completed{0};
  std::atomic<bool> stop{false};
  std::atomic<bool> failed{false};
  HANDLE write_handle = INVALID_HANDLE_VALUE;
  std::string request_id;
  std::string payload;
  bool call_result = false;
  std::uint64_t state_revision = 0;
  std::uint64_t published_checkpoint_sequence = 0;
  std::optional<game::Snapshot> previous_snapshot;
};
void FreshAckProbeWorker(FreshAckWorkerProbe &, const game::GameAdapter &,
    api::MainThreadQueryMailboxV1 &) noexcept;

void FreshAckProbeWorker(FreshAckWorkerProbe &probe, const game::GameAdapter &native, api::MainThreadQueryMailboxV1 &mailbox) noexcept {
  try {
    build::WorkerAdapter adapter(native, mailbox, build::ConsoleFixtureBindings{});
    WorkerState state{};
    probe.proxy.store(&adapter, std::memory_order_release);
    while (!probe.stop.load(std::memory_order_acquire)) {
      const auto req = probe.requested.load(std::memory_order_acquire);
      if (probe.completed.load(std::memory_order_acquire) != req) {
        const auto *proxy = probe.proxy.load(std::memory_order_acquire);
        if (proxy == nullptr) break;
        const bool result = RunFreshFullStateQuery12004(
            probe.write_handle, *proxy, state, probe.request_id, probe.payload);
        probe.call_result = result;
        probe.state_revision = state.state_revision;
        probe.published_checkpoint_sequence = state.published_checkpoint_sequence;
        probe.previous_snapshot = state.previous_snapshot;
        probe.completed.store(req, std::memory_order_release);
      } else {
        Sleep(1);
      }
    }
    probe.proxy.store(nullptr, std::memory_order_release);
  } catch (...) {
    probe.proxy.store(nullptr, std::memory_order_release);
    probe.failed.store(true, std::memory_order_release);
  }
}
using AckWriteFileFn = BOOL (WINAPI *)(HANDLE, LPCVOID, DWORD, LPDWORD, LPOVERLAPPED);
struct AckHeaderWriteFailProbe {
  HANDLE target_handle = INVALID_HANDLE_VALUE;
  HANDLE read_handle = INVALID_HANDLE_VALUE;
  std::atomic<DWORD> target_thread{0};
  std::atomic<std::uint32_t> target_calls{0};
  std::atomic<std::uint32_t> delegated_calls{0};
  std::atomic<std::uint32_t> failed_calls{0};
  std::atomic<std::uint32_t> snapshot_payload_bytes{0};
  std::atomic<bool> write_shape_ok{true};
  std::atomic<bool> snapshot_visible_at_failure{false};
  std::atomic<bool> installed{false};
  void **iat_slot = nullptr;
  AckWriteFileFn original = nullptr;
  DWORD original_protection = 0;
};
std::atomic<AckHeaderWriteFailProbe *> g_ack_write_fail{nullptr};
std::atomic<AckWriteFileFn> g_ack_write_delegate{nullptr};
BOOL WINAPI FreshAckWriteFileHook(HANDLE, LPCVOID, DWORD, LPDWORD, LPOVERLAPPED) noexcept;
bool InstallFreshAckWriteFailHook(AckHeaderWriteFailProbe &) noexcept;
bool RestoreFreshAckWriteFailHook(AckHeaderWriteFailProbe &) noexcept;

BOOL WINAPI FreshAckWriteFileHook(HANDLE handle, LPCVOID buffer, DWORD size, LPDWORD written, LPOVERLAPPED overlapped) noexcept {
  const auto delegate = g_ack_write_delegate.load(std::memory_order_acquire);
  if (delegate == nullptr) {
    SetLastError(ERROR_INVALID_FUNCTION);
    return FALSE;
  }
  auto *probe = g_ack_write_fail.load(std::memory_order_acquire);
  if (probe == nullptr || handle != probe->target_handle ||
      GetCurrentThreadId() != probe->target_thread.load(std::memory_order_acquire)) {
    return delegate(handle, buffer, size, written, overlapped);
  }
  const auto call = probe->target_calls.fetch_add(1, std::memory_order_relaxed) + 1;
  if (overlapped != nullptr) {
    probe->write_shape_ok.store(false, std::memory_order_relaxed);
    return delegate(handle, buffer, size, written, overlapped);
  }
  if (call == 1) {
    if (size != 4 || buffer == nullptr || written == nullptr) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
      return delegate(handle, buffer, size, written, overlapped);
    }
    const auto result = delegate(handle, buffer, size, written, overlapped);
    ++probe->delegated_calls;
    if (!result || *written != size) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
      return result;
    }
    const auto *bytes = static_cast<const std::byte *>(buffer);
    const auto payload_len = static_cast<std::uint32_t>(bytes[0]) |
                             (static_cast<std::uint32_t>(bytes[1]) << 8U) |
                             (static_cast<std::uint32_t>(bytes[2]) << 16U) |
                             (static_cast<std::uint32_t>(bytes[3]) << 24U);
    if (payload_len == 0) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
    } else {
      probe->snapshot_payload_bytes.store(payload_len, std::memory_order_relaxed);
    }
    return result;
  }
  if (call == 2) {
    if (buffer == nullptr || written == nullptr) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
      return delegate(handle, buffer, size, written, overlapped);
    }
    const auto expected = probe->snapshot_payload_bytes.load(std::memory_order_relaxed);
    if (expected == 0 || size != expected) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
      return delegate(handle, buffer, size, written, overlapped);
    }
    const auto result = delegate(handle, buffer, size, written, overlapped);
    ++probe->delegated_calls;
    if (!result || *written != size) {
      probe->write_shape_ok.store(false, std::memory_order_relaxed);
    }
    return result;
  }
  if (call == 3) {
    if (probe->write_shape_ok.load(std::memory_order_relaxed) &&
        probe->delegated_calls.load(std::memory_order_relaxed) == 2 &&
        probe->failed_calls.load(std::memory_order_relaxed) == 0 &&
        size == 4 && buffer != nullptr && written != nullptr) {
      const auto payload = probe->snapshot_payload_bytes.load(std::memory_order_relaxed);
      const auto expected_total = static_cast<std::uint64_t>(4) + payload;
      if (expected_total > (std::numeric_limits<DWORD>::max)()) {
        probe->write_shape_ok.store(false, std::memory_order_relaxed);
        return delegate(handle, buffer, size, written, overlapped);
      }
      std::array<std::byte, 4> peek_header{};
      DWORD peeked = 0;
      DWORD available = 0;
      if (!PeekNamedPipe(probe->read_handle, peek_header.data(), 4, &peeked, &available, nullptr) ||
          peeked != 4 || available != static_cast<DWORD>(expected_total)) {
        probe->write_shape_ok.store(false, std::memory_order_relaxed);
        return delegate(handle, buffer, size, written, overlapped);
      }
      const auto *bytes = static_cast<const std::byte *>(peek_header.data());
      const auto decoded = static_cast<std::uint32_t>(bytes[0]) |
                           (static_cast<std::uint32_t>(bytes[1]) << 8U) |
                           (static_cast<std::uint32_t>(bytes[2]) << 16U) |
                           (static_cast<std::uint32_t>(bytes[3]) << 24U);
      if (decoded != payload) {
        probe->write_shape_ok.store(false, std::memory_order_relaxed);
        return delegate(handle, buffer, size, written, overlapped);
      }
      probe->snapshot_visible_at_failure.store(true, std::memory_order_relaxed);
      probe->failed_calls.store(1, std::memory_order_relaxed);
      *written = 0;
      SetLastError(ERROR_WRITE_FAULT);
      return FALSE;
    }
    probe->write_shape_ok.store(false, std::memory_order_relaxed);
    return delegate(handle, buffer, size, written, overlapped);
  }
  probe->write_shape_ok.store(false, std::memory_order_relaxed);
  return delegate(handle, buffer, size, written, overlapped);
}
bool RestoreFreshAckWriteFailHook(AckHeaderWriteFailProbe &probe) noexcept {
  if (probe.iat_slot == nullptr || probe.original == nullptr) return true;
  const auto original = reinterpret_cast<void *>(probe.original);
  const auto hook = reinterpret_cast<void *>(&FreshAckWriteFileHook);
  if (*probe.iat_slot != original && *probe.iat_slot != hook) return false;
  DWORD writable_previous = 0;
  if (!VirtualProtect(probe.iat_slot, sizeof(void *), PAGE_READWRITE,
                      &writable_previous)) return false;
  const auto before = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(probe.iat_slot), original, hook);
  const bool unpatched = before == hook || before == original;
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(probe.iat_slot, sizeof(void *),
      probe.original_protection, &ignored) != FALSE;
  if (unpatched) {
    probe.installed.store(false, std::memory_order_release);
    auto *expected = &probe;
    (void)g_ack_write_fail.compare_exchange_strong(expected, nullptr,
        std::memory_order_acq_rel);
  }
  return unpatched && protected_again;
}

bool InstallFreshAckWriteFailHook(AckHeaderWriteFailProbe &probe) noexcept {
  if (g_ack_write_fail.load(std::memory_order_acquire) != nullptr ||
      probe.target_handle == nullptr || probe.target_handle == INVALID_HANDLE_VALUE ||
      probe.read_handle == nullptr || probe.read_handle == INVALID_HANDLE_VALUE ||
      probe.target_thread.load(std::memory_order_acquire) == 0) return false;
  auto **slot = reinterpret_cast<void **>(&::__imp_WriteFile);
  const auto original = reinterpret_cast<AckWriteFileFn>(*slot);
  if (original == nullptr || original == &FreshAckWriteFileHook) return false;
  DWORD protection = 0;
  if (!VirtualProtect(slot, sizeof(void *), PAGE_READWRITE, &protection)) return false;
  probe.iat_slot = slot;
  probe.original = original;
  probe.original_protection = protection;
  g_ack_write_delegate.store(original, std::memory_order_release);
  g_ack_write_fail.store(&probe, std::memory_order_release);
  const auto before = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(slot),
      reinterpret_cast<void *>(&FreshAckWriteFileHook),
      reinterpret_cast<void *>(original));
  if (before != reinterpret_cast<void *>(original)) {
    DWORD ignored = 0;
    (void)VirtualProtect(slot, sizeof(void *), protection, &ignored);
    g_ack_write_fail.store(nullptr, std::memory_order_release);
    return false;
  }
  probe.installed.store(true, std::memory_order_release);
  DWORD ignored = 0;
  if (!VirtualProtect(slot, sizeof(void *), protection, &ignored)) {
    (void)RestoreFreshAckWriteFailHook(probe);
    return false;
  }
  return true;
}

bool TestFreshHandlerAck(bool ack_write_failure_only = false) {
  struct PipeGuard {
    HANDLE read = INVALID_HANDLE_VALUE;
    HANDLE write = INVALID_HANDLE_VALUE;
    ~PipeGuard() {
      if (read != INVALID_HANDLE_VALUE) CloseHandle(read);
      if (write != INVALID_HANDLE_VALUE) CloseHandle(write);
    }
  };

  FixtureAdapter native;
  native.patch4 = true;
  native.frame.paused = true;
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, native.frame.date_raw);

  PipeGuard pipes;
  if (!CreatePipe(&pipes.read, &pipes.write, nullptr, 65536)) return false;

  api::MainThreadQueryMailboxV1 mailbox;
  std::array<api::MainThreadQueryExecutorV1, 14> executors{};
  executors[13] = &build::ExecuteSemanticAdapter12002;
  auto environment = xar::ck3_12004::BindThreadRuntimeImage(
      0x140000000ULL, native.descriptor().executable_sha256, executors);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;

  if (!api::InstallMainThreadQueryMailboxV1(mailbox, environment)) return false;
  bool installed = true;

  FreshAckWorkerProbe probe;
  AckHeaderWriteFailProbe write_failure;
  bool hook_restored = false;
  probe.write_handle = pipes.write;

  std::thread worker;
  try {
    worker = std::thread([&] {
      FreshAckProbeWorker(probe, native, mailbox);
    });
  } catch (...) {
    if (installed) {
      (void)api::UninstallMainThreadQueryMailboxV1(mailbox, 0);
      installed = false;
    }
    return false;
  }

  const auto pump = [&] {
    (void)api::ObserveMainThreadPumpAndDrainV1(mailbox,
        xar::ck3_12004::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId());
  };

  const auto cleanup = [&] {
    if (ack_write_failure_only) {
      const bool restored = RestoreFreshAckWriteFailHook(write_failure);
      hook_restored = restored && !write_failure.installed.load();
      if (!restored) std::abort();
    }
    if (installed) {
      (void)api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
      installed = false;
    }
    probe.stop.store(true, std::memory_order_release);
    worker.join();
  };

  const auto until = [&](auto predicate) {
    const auto end = GetTickCount64() + 3000;
    while (!predicate() && GetTickCount64() < end) {
      if (probe.failed.load(std::memory_order_acquire)) return false;
      pump();
      Sleep(1);
    }
    return predicate();
  };

  const auto request = [&](std::uint32_t sequence, std::string_view rid, std::string_view payload) {
    probe.request_id = std::string(rid);
    probe.payload = std::string(payload);
    probe.requested.store(sequence, std::memory_order_release);
    return until([&] {
      return probe.completed.load(std::memory_order_acquire) == sequence;
    });
  };

  bool ok = false;
  try {
    ok = until([&] {
    return probe.proxy.load(std::memory_order_acquire) != nullptr;
  });
  if (ok) ok = until([&] {
    return api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready;
  });

  if (ack_write_failure_only) {
  // Case 8: ACK header write failure after successful snapshot publication
  if (ok) {
    native.frame.played_character_gold.raw = 444;
    write_failure.target_handle = pipes.write;
    write_failure.read_handle = pipes.read;
    write_failure.target_thread = GetThreadId(worker.native_handle());
    write_failure.iat_slot = nullptr;
    write_failure.installed = false;
    write_failure.target_calls = 0;
    write_failure.delegated_calls = 0;
    write_failure.failed_calls = 0;
    write_failure.write_shape_ok = true;
    write_failure.snapshot_visible_at_failure = false;

    if (!InstallFreshAckWriteFailHook(write_failure)) {
      ok = false;
    } else {
      // First request: expect snapshot written, ACK header fails
      ok = request(8, "req8", R"({"expected_revision":0})");
      if (ok) {
        ok = probe.call_result == false;
        ok = ok && write_failure.target_calls.load() == 3;
        ok = ok && write_failure.delegated_calls.load() == 2;
        ok = ok && write_failure.failed_calls.load() == 1;
        ok = ok && write_failure.write_shape_ok.load();
        ok = ok && write_failure.snapshot_visible_at_failure.load();

        // Consume the one actual state_snapshot frame
        auto r1 = xar::bridge::TryReadFrame(pipes.read);
        ok = ok && r1.status == xar::bridge::ReadStatus::frame;
        if (ok) {
          // Verify it matches the expected StateSnapshotFrame
          std::string expected_snapshot = StateSnapshotFrame(native.frame, 1, CheckpointSubmission{}, {}, "req8");
          ok = ok && r1.payload == expected_snapshot;
        }
        // Verify no ACK bytes remain
        auto r2 = xar::bridge::TryReadFrame(pipes.read);
        ok = ok && r2.status == xar::bridge::ReadStatus::none;

        // Verify state committed despite ACK failure
        ok = ok && native.raw_reads.load() == 1;
        ok = ok && native.wrong_owner.load() == 0;
        ok = ok && probe.state_revision == 1;
        ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot == native.frame;
        ok = ok && probe.published_checkpoint_sequence == 0;
      }

      // Restore hook before recovery
      hook_restored = RestoreFreshAckWriteFailHook(write_failure);
      ok = ok && hook_restored && !write_failure.installed.load();

      // Recovery: unchanged frame, new request ID, expect success pair at revision 1
      if (ok) {
        ok = request(9, "req9", R"({"expected_revision":0})");
        if (ok) {
          ok = probe.call_result == true;
          ok = ok && ReadFreshSuccessPair(pipes.read, "req9", 1);
          ok = ok && native.raw_reads.load() == 2;
          ok = ok && probe.state_revision == 1;
          ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot == native.frame;
          ok = ok && probe.published_checkpoint_sequence == 0;
          ok = ok && native.wrong_owner.load() == 0;
        }
      }
    }
  }
  } else {
  // Case 1: expected_revision 7 -> error fresh_read_requires_revision_zero
  if (ok) {
    ok = request(1, "req1", "{\"expected_revision\":7}");
    if (ok) {
      ok = probe.call_result == true; // Handler returns true after writing negative ACK
      ok = ok && ReadFreshFailureOnly(pipes.read, "req1", "fresh_read_requires_revision_zero");
      ok = ok && native.raw_reads.load() == 0;
      ok = ok && probe.state_revision == 0;
      ok = ok && !probe.previous_snapshot.has_value();
    }
  }

  // Case 2: gold.raw 111, expected 0, new id -> success pair revision 1
  if (ok) {
    native.frame.played_character_gold.raw = 111;
    ok = request(2, "req2", "{\"expected_revision\":0}");
    if (ok) {
      ok = probe.call_result == true;
      ok = ok && ReadFreshSuccessPair(pipes.read, "req2", 1);
      ok = ok && native.raw_reads.load() == 1;
      ok = ok && probe.state_revision == 1;
      ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot->played_character_gold.raw == 111;
    }
  }

  // Case 3: unchanged gold 111, expected 0, different new id -> success pair revision 1 (correlated resend)
  if (ok) {
    ok = request(3, "req3", "{\"expected_revision\":0}");
    if (ok) {
      ok = probe.call_result == true;
      ok = ok && ReadFreshSuccessPair(pipes.read, "req3", 1);
      ok = ok && native.raw_reads.load() == 2;
      ok = ok && probe.state_revision == 1;
      ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot->played_character_gold.raw == 111;
    }
  }

  // Case 4: reader_available=false, expected 0 -> error fresh_full_state_read_failed, raw 3, state remains 1
  if (ok) {
    native.reader_available = false;
    ok = request(4, "req4", "{\"expected_revision\":0}");
    if (ok) {
      ok = probe.call_result == true; // Handler returns true after writing negative ACK
      ok = ok && ReadFreshFailureOnly(pipes.read, "req4", "fresh_full_state_read_failed");
      ok = ok && native.raw_reads.load() == 3;
      ok = ok && probe.state_revision == 1;
      ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot->played_character_gold.raw == 111;
    }
  }

  // Case 5: reader_available=true, gold 222, expected 0 -> success pair revision 2
  if (ok) {
    native.reader_available = true;
    native.frame.played_character_gold.raw = 222;
    ok = request(5, "req5", "{\"expected_revision\":0}");
    if (ok) {
      ok = probe.call_result == true;
      ok = ok && ReadFreshSuccessPair(pipes.read, "req5", 2);
      ok = ok && native.raw_reads.load() == 4;
      ok = ok && probe.state_revision == 2;
      ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot->played_character_gold.raw == 222;
    }
  }

  // Case 6: gold 333, INVALID_HANDLE_VALUE write, expected 0 -> handler returns false, raw 5, state remains 2
  if (ok) {
    native.frame.played_character_gold.raw = 333;
    probe.write_handle = INVALID_HANDLE_VALUE;
    ok = request(6, "req6", "{\"expected_revision\":0}");
    if (ok) {
      ok = probe.call_result == false; // WriteFrame fails on invalid handle
      ok = ok && native.raw_reads.load() == 5;
      ok = ok && probe.state_revision == 2;
      ok = ok && probe.previous_snapshot.has_value() && probe.previous_snapshot->played_character_gold.raw == 222;
      ok = ok && probe.published_checkpoint_sequence == 0;
      // Verify original valid pipe has no new frames
      auto r = xar::bridge::TryReadFrame(pipes.read);
      ok = ok && r.status == xar::bridge::ReadStatus::none;
    }
  }

  // Case 7: Uninstall mailbox, then valid pipe new request expected 0 -> error fresh_full_state_read_failed, no new raw, state 2
  if (ok) {
    const auto terminal = api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
    installed = false;
    ok = terminal == api::MainThreadQueryUninstallResultV1::uninstalled;
    if (ok) {
      probe.write_handle = pipes.write; // restore valid handle
      ok = request(7, "req7", "{\"expected_revision\":0}");
      if (ok) {
        ok = probe.call_result == true; // Handler returns true after writing negative ACK
        ok = ok && ReadFreshFailureOnly(pipes.read, "req7", "fresh_full_state_read_failed");
        ok = ok && native.raw_reads.load() == 5;
        ok = ok && probe.state_revision == 2;
      }
    }
  }

  }

  } catch (...) {
    ok = false;
  }
  cleanup();
  if (ack_write_failure_only) {
  MEMORY_BASIC_INFORMATION iat_memory{};
  const bool iat_restored = write_failure.iat_slot != nullptr &&
      *write_failure.iat_slot == reinterpret_cast<void *>(write_failure.original) &&
      VirtualQuery(write_failure.iat_slot, &iat_memory, sizeof(iat_memory)) == sizeof(iat_memory) &&
      iat_memory.Protect == write_failure.original_protection;
  ok = ok && hook_restored && iat_restored;
  ok = ok && native.wrong_owner.load() == 0 && native.raw_reads.load() == 2;
  ok = ok && memory.iat == reinterpret_cast<void *>(&FakePeek);
  ok = ok && memory.page_protect == PAGE_READONLY;
  std::printf("fresh-ack-writefail: ok=%d calls=%u delegated=%u failures=%u visible=%d rev=%llu raw=%u wrong=%u restored=%d\n",
      ok ? 1 : 0, write_failure.target_calls.load(), write_failure.delegated_calls.load(),
      write_failure.failed_calls.load(), write_failure.snapshot_visible_at_failure.load() ? 1 : 0,
      static_cast<unsigned long long>(probe.state_revision), native.raw_reads.load(),
      native.wrong_owner.load(), hook_restored && iat_restored ? 1 : 0);
  return ok;
  }

  ok = ok && native.wrong_owner.load() == 0;
  ok = ok && native.raw_reads.load() == 5;
  ok = ok && memory.iat == reinterpret_cast<void *>(&FakePeek);
  ok = ok && memory.page_protect == PAGE_READONLY;

  std::printf("fresh-ack: ok=%d raw=%u wrong=%u\n",
      ok ? 1 : 0, native.raw_reads.load(), native.wrong_owner.load());
  return ok;
}
bool TestFreshAckWriteFailureOnly() {
  return TestFreshHandlerAck(true);
}
} // namespace
int main(int argc, char **argv) {
  if (argc == 1) return TestFreshHandlerAck() ? 0 : 1;
  if (argc == 2 && std::strcmp(argv[1], "--ack-write-failure-only") == 0)
    return TestFreshAckWriteFailureOnly() ? 0 : 1;
  return 2;
}
