#include "ck3_12002_activity_feast_router.hpp"
#include "ck3_12004_player_pilgrimage_activities_private_v1.hpp"
#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include <array>
#include <cstdio>
#include <cstring>

namespace {
namespace api = xar::ck3_11906;
namespace native = xar::ck3_12002;
namespace actual = xar::ck3_12004;
#define REQUIRE(condition) do { if (!(condition)) { \
  std::fprintf(stderr, "pilgrimage gate line %d: %s\n", __LINE__, #condition); \
  return false; } } while (false)
constexpr std::int32_t fixture_date = 53220000;
struct Probe {
  api::MainThreadQueryMailboxV1 *mailbox = nullptr;
  api::MainThreadQueryTicketV1 ticket{};
  unsigned calls = 0, kind = 0;
  bool ownership_verified = false;
  api::MainThreadExecutionStampV1 stamp{};
};
bool Record(void *opaque, const api::MainThreadExecutionStampV1 &stamp,
            unsigned kind, api::MainThreadQueryExecutorV1 executor) noexcept {
  auto &probe = *static_cast<Probe *>(opaque);
  auto &owner = *probe.mailbox;
  ++probe.calls; probe.kind = kind; probe.stamp = stamp;
  probe.ownership_verified =
      owner.state.load() == api::MainThreadQueryMailboxStateV1::executing &&
      owner.executor.load() == executor && owner.executor_context == &probe &&
      owner.published_sequence.load() == probe.ticket.sequence &&
      owner.owner_thread_id.load() == GetCurrentThreadId() &&
      stamp.thread_id == GetCurrentThreadId() && stamp.pump_epoch != 0 &&
      stamp.date_raw == fixture_date && stamp.paused &&
      stamp.tls_initialized == 1 && stamp.tls_main_thread_marker == 1 &&
      stamp.tls_context != 0 && stamp.jomini_state != 0 && stamp.game_state != 0;
  return probe.ownership_verified;
}
bool ReadonlyProbe(void *opaque, const api::MainThreadExecutionStampV1 &stamp) noexcept {
  return Record(opaque, stamp, 1, &ReadonlyProbe);
}
bool LegacyStart(void *opaque, const api::MainThreadExecutionStampV1 &stamp) noexcept {
  return Record(opaque, stamp, 2, &LegacyStart);
}
bool Unlisted(void *, const api::MainThreadExecutionStampV1 &) noexcept { return false; }
BOOL WINAPI PeekFixture(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Memory {
  void *iat = reinterpret_cast<void *>(&PeekFixture);
  DWORD protection = PAGE_READONLY;
  std::array<std::byte, 0x18> rng{}, game{};
  std::array<std::byte, 0x28> jomini{}, tls{};
  std::uintptr_t rng_pointer = 0, rng_wrapper = 0, jomini_pointer = 0, game_pointer = 0;
  std::uint8_t initialized = 1;
  void Reset() {
    iat = reinterpret_cast<void *>(&PeekFixture); protection = PAGE_READONLY;
    rng = {}; game = {}; jomini = {}; tls = {}; initialized = 1;
    const auto thread = GetCurrentThreadId();
    std::memcpy(rng.data() + 0x10, &thread, sizeof(thread));
    std::memcpy(game.data() + 0x08, &fixture_date, sizeof(fixture_date));
    jomini[0x20] = std::byte{1}; tls[0x20] = std::byte{1};
    rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_pointer);
    jomini_pointer = reinterpret_cast<std::uintptr_t>(jomini.data());
    game_pointer = reinterpret_cast<std::uintptr_t>(game.data());
  }
};
// Pinned mailbox and all callback data remain alive until process exit.
Memory memory;
api::MainThreadQueryMailboxV1 mailbox;
void *__fastcall TlsFixture() noexcept { return memory.tls.data(); }
bool QueryFixture(void *opaque, const void *address,
                  MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &source = *static_cast<Memory *>(opaque);
  if (address != &source.iat) return false;
  output = {};
  output.BaseAddress = reinterpret_cast<void *>(reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095});
  output.AllocationBase = output.BaseAddress; output.AllocationProtect = PAGE_READONLY;
  output.RegionSize = 4096; output.State = MEM_COMMIT;
  output.Protect = source.protection; output.Type = MEM_IMAGE;
  return true;
}
bool ProtectFixture(void *opaque, void *, std::size_t size,
                    DWORD desired, DWORD &previous) noexcept {
  if (size != 4096) return false;
  auto &source = *static_cast<Memory *>(opaque);
  previous = source.protection; source.protection = desired;
  return true;
}
bool CheckProfile(bool read_on, bool start_on) {
  native::NonwarMailboxExecutorsV1 actual4{};
  native::PopulateNonwarRouterExecutors12004(actual4);
  REQUIRE(actual4.pilgrimage_identities ==
      (read_on ? &native::ExecutePlayerPilgrimageActivitiesPrivate12004V1 : nullptr));
  REQUIRE((actual4.feast_start != nullptr) == start_on);
  if (read_on && start_on) REQUIRE(actual4.pilgrimage_identities != actual4.feast_start);
  for (const auto step : {"query-activity-feast-stage5-start-inputs-v1-private",
                         "query-activity-feast-hosted-post-v1-private"})
    REQUIRE(native::IsActivityFeastPrivateStep12002(step) == start_on);
  api::MainThreadQueryInstallEnvironmentV1 environment{};
  environment.permitted_executor_quattuorsexagintary = &LegacyStart;
  environment.permitted_executor_secondary = &Unlisted;
  native::NonwarMailboxExecutorsV1 callbacks{};
  callbacks.pilgrimage_identities = &ReadonlyProbe;
  callbacks.feast_start = &LegacyStart;
  native::RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  native::RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  REQUIRE(environment.permitted_executor_quattuorsexagintary == &LegacyStart);
  REQUIRE(environment.permitted_executor_secondary == &Unlisted);
  REQUIRE(environment.permitted_executor_player_pilgrimage_identities12004 ==
      (read_on ? &ReadonlyProbe : nullptr));
  return true;
}
bool Exercise(api::MainThreadQueryExecutorV1 executor, unsigned kind) {
  Probe probe{&mailbox};
  REQUIRE(api::TrySubmitMainThreadQueryV1(mailbox, executor, &probe, probe.ticket) ==
          api::MainThreadQuerySubmitResultV1::submitted);
  REQUIRE(probe.ticket.sequence != 0);
  const api::MainThreadQueryTicketV1 wrong{probe.ticket.sequence + 1};
  REQUIRE(api::WaitForMainThreadQueryV1(mailbox, wrong, 0) == api::MainThreadQueryWaitResultV1::ticket_mismatch);
  REQUIRE(api::ReclaimMainThreadQueryV1(mailbox, wrong) == api::MainThreadQueryReclaimResultV1::ticket_mismatch);
  REQUIRE(probe.calls == 0 && mailbox.state == api::MainThreadQueryMailboxStateV1::queued);
  REQUIRE(api::ObserveMainThreadPumpAndDrainV1(mailbox,
      actual::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId()));
  REQUIRE(api::WaitForMainThreadQueryV1(mailbox, probe.ticket, 0) == api::MainThreadQueryWaitResultV1::completed);
  REQUIRE(probe.calls == 1 && probe.kind == kind && probe.ownership_verified);
  REQUIRE(probe.stamp.tls_context == reinterpret_cast<std::uintptr_t>(memory.tls.data()));
  REQUIRE(probe.stamp.jomini_state == memory.jomini_pointer && probe.stamp.game_state == memory.game_pointer);
  REQUIRE(api::ReclaimMainThreadQueryV1(mailbox, probe.ticket) == api::MainThreadQueryReclaimResultV1::reclaimed);
  REQUIRE(mailbox.executor.load() == nullptr && mailbox.executor_context == nullptr);
  REQUIRE(mailbox.state == api::MainThreadQueryMailboxStateV1::idle && mailbox.failure_flags == 0);
  return true;
}
bool CheckLifecycle(bool coexist_with_start) {
  memory.Reset();
  // Actual .4 software profile, with ONLY owned offline TLS/RNG/state/IAT data.
  auto environment = actual::BindThreadRuntimeImage(0x140000000ULL, actual::kExecutableSha256);
  REQUIRE(environment.build_profile == &actual::ThreadRuntimeBuildProfile());
  environment.executor_submission_enabled = true;
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &PeekFixture;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.rng_wrapper);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_pointer);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.game_pointer);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.initialized);
  environment.tls_context_getter_override = &TlsFixture;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &QueryFixture;
  environment.memory_protect_override = &ProtectFixture;
  environment.system_page_size_override = 4096;
  native::NonwarMailboxExecutorsV1 callbacks{};
  callbacks.pilgrimage_identities = &ReadonlyProbe;
  callbacks.feast_start = coexist_with_start ? &LegacyStart : nullptr;
  native::RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  const auto old_start = coexist_with_start ? &LegacyStart : nullptr;
  REQUIRE(environment.permitted_executor == nullptr && environment.permitted_executor_secondary == nullptr);
  REQUIRE(environment.permitted_executor_player_pilgrimage_identities12004 == &ReadonlyProbe);
  REQUIRE(environment.permitted_executor_quattuorsexagintary == old_start);
  REQUIRE(api::InstallMainThreadQueryMailboxV1(mailbox, environment));
  REQUIRE(mailbox.permitted_executor_player_pilgrimage_identities12004 == &ReadonlyProbe);
  REQUIRE(mailbox.permitted_executor_quattuorsexagintary == old_start);
  // Pointer values are copied, not aliases into the caller's environment.
  environment.permitted_executor_player_pilgrimage_identities12004 = &Unlisted;
  environment.permitted_executor_quattuorsexagintary = &Unlisted;
  REQUIRE(mailbox.permitted_executor_player_pilgrimage_identities12004 == &ReadonlyProbe);
  REQUIRE(mailbox.permitted_executor_quattuorsexagintary == old_start);
  REQUIRE(memory.iat == reinterpret_cast<void *>(&api::XarMainThreadPeekMessageWHookV1));
  for (unsigned i = 0; i < 3; ++i)
    REQUIRE(!api::ObserveMainThreadPumpAndDrainV1(mailbox,
        actual::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId()));
  REQUIRE(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready);
  Probe rejected{&mailbox};
  REQUIRE(api::TrySubmitMainThreadQueryV1(mailbox, &Unlisted, &rejected, rejected.ticket) ==
          api::MainThreadQuerySubmitResultV1::invalid_request);
  REQUIRE(rejected.ticket.sequence == 0 && mailbox.state == api::MainThreadQueryMailboxStateV1::idle);
  if (!coexist_with_start)
    REQUIRE(api::TrySubmitMainThreadQueryV1(mailbox, &LegacyStart, &rejected, rejected.ticket) ==
            api::MainThreadQuerySubmitResultV1::invalid_request);
  REQUIRE(Exercise(&ReadonlyProbe, 1));
  if (coexist_with_start) REQUIRE(Exercise(&LegacyStart, 2));
  REQUIRE(mailbox.permitted_executor_player_pilgrimage_identities12004 == &ReadonlyProbe);
  REQUIRE(mailbox.permitted_executor_quattuorsexagintary == old_start);
  REQUIRE(api::UninstallMainThreadQueryMailboxV1(mailbox, 0) == api::MainThreadQueryUninstallResultV1::uninstalled);
  REQUIRE(memory.iat == reinterpret_cast<void *>(&PeekFixture));
  REQUIRE(mailbox.state == api::MainThreadQueryMailboxStateV1::detached);
  REQUIRE(mailbox.permitted_executor_player_pilgrimage_identities12004 == nullptr);
  // The old Start slot retains its existing uninstall behavior.
  REQUIRE(mailbox.permitted_executor_quattuorsexagintary == old_start);
  REQUIRE(api::TrySubmitMainThreadQueryV1(mailbox, &ReadonlyProbe, &rejected, rejected.ticket) !=
          api::MainThreadQuerySubmitResultV1::submitted);
  REQUIRE(rejected.calls == 0);
  return true;
}
}
int main() {
  using namespace xar::ck3_12002;
  using namespace xar::ck3_11906;
#if defined(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_ACTIVITIES_PRIVATE_QUERY_V1)
  constexpr bool read_on = true;
#else
  constexpr bool read_on = false;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  constexpr bool start_on = true;
#else
  constexpr bool start_on = false;
#endif
  MainThreadQueryInstallEnvironmentV1 environment{};
  NonwarMailboxExecutorsV1 executors{};
  executors.pilgrimage_identities = &ExecutePlayerPilgrimageActivitiesPrivate12004V1;
  executors.feast_start = &LegacyStart;
  RegisterNonwarMailboxExecutorsV1(environment, executors);
  if (IsActivityFeastPrivateStep12002(kPlayerPilgrimageActivitiesPrivate12004StepV1) != read_on ||
      IsActivityFeastPrivateStep12002("start-activity-feast-stage5-v1-private") != start_on ||
      (environment.permitted_executor_player_pilgrimage_identities12004 != nullptr) != read_on ||
      (environment.permitted_executor_quattuorsexagintary != nullptr) != start_on)
    return 1;
  if (read_on && environment.permitted_executor_player_pilgrimage_identities12004 !=
                     &ExecutePlayerPilgrimageActivitiesPrivate12004V1) return 2;
  if (start_on && environment.permitted_executor_quattuorsexagintary != &LegacyStart) return 3;
  if (!CheckProfile(read_on, start_on)) return 4;
  if (read_on && !CheckLifecycle(false)) return 5;
  if (read_on && start_on && !CheckLifecycle(true)) return 6;
  std::printf("PASS: real production READ=%u Start=%u profile/classifier/registration; "
      "READ=1 exercises only-new permission copy/allow/owner/reclaim/uninstall; "
      "owned .4-profile fixture only, no gameplay or live qualification\n", unsigned(read_on), unsigned(start_on));
  return 0;
}
