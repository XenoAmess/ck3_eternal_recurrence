#include "xar_bridge/steward_develop_county_candidates_v1_mailbox.hpp"
#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

xar::game::Snapshot g_snapshot{};
bool g_reader_available = true;
std::uint32_t g_reader_calls = 0;
std::uint32_t g_snapshot_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 &query,
    std::uint64_t sequence) {
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &xar::ck3_11906::
      ExecuteStewardDevelopCountyCandidatesMailboxQueryV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.request.expected_snapshot_revision = 77;
  query.expected_snapshot = g_snapshot;
}

xar::ck3_11906::MainThreadExecutionStampV1 Stamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 9;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = g_snapshot.date_raw;
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = 0x4000;
  return stamp;
}

bool TestParsing() {
  using namespace xar::ck3_11906;
  std::uint64_t revision = 0;
  return ParseStewardDevelopCountyCandidatesV1Step(
             "query-steward-develop-county-candidates-v1") &&
         !ParseStewardDevelopCountyCandidatesV1Step(
             "query-steward-develop-county-candidates-v1-1") &&
         ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":77})", revision) &&
         revision == 77 &&
         ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"step":"query-steward-develop-county-candidates-v1", "expected_revision": 77, "x":1})",
             revision) &&
         revision == 77 &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":0})", revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":077})", revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":77,"expected_revision":78})",
             revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1("{}",
                                                                 revision);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto stamp = Stamp();
  return !xar::ck3_11906::
              ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(
                  &query, stamp) &&
         query.completion ==
             xar::ck3_11906::
                 StewardDevelopCountyCandidatesMailboxCompletionV1::
                     infrastructure_rejected &&
         g_reader_calls == 0;
}

bool TestTypedCompletion(bool available) {
  g_reader_available = available;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  if (!xar::ck3_11906::
           ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(&query,
                                                                stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::
              StewardDevelopCountyCandidatesMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      (available && query.result.observed_date_raw != g_snapshot.date_raw) ||
      (!available && query.result.observed_date_raw.has_value()) ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadStewardDevelopCountyCandidatesResultV1::
                   available &&
           query.result.status ==
               xar::game::StewardDevelopCountyCandidatesStatusV1::available &&
           query.result.player_character_id == 0x02000001 &&
           query.result.steward_character_id == 0x02000002 &&
           query.result.same_frame_stable && query.result.readiness.ready &&
           query.result.unavailable_reason ==
               xar::game::StewardDevelopCountyFailureReasonV1::none;
  }
  return query.read_result ==
             xar::game::ReadStewardDevelopCountyCandidatesResultV1::
                 unavailable &&
         query.result.status ==
             xar::game::StewardDevelopCountyCandidatesStatusV1::unavailable &&
         !query.result.same_frame_stable && !query.result.readiness.ready &&
         query.result.unavailable_reason ==
             xar::game::StewardDevelopCountyFailureReasonV1::
                 native_reader_not_frozen;
}

bool TestCurrentMaterialUnsupportedCompletion() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, 12);
  query.material_profile = true;
  // Intentionally unadmitted build: invoke the real current reader, without
  // overriding its entry or routing through the legacy fixture source.
  const auto stamp = Stamp();
  const auto reader_calls_before = g_reader_calls;
  const auto snapshot_calls_before = g_snapshot_calls;
  return xar::ck3_11906::
             ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(&query, stamp) &&
         g_reader_calls == reader_calls_before &&
         g_snapshot_calls == snapshot_calls_before &&
         query.executor_invocations == 1 && query.execution_stamp == stamp &&
         query.completion == xar::ck3_11906::
                                 StewardDevelopCountyCandidatesMailboxCompletionV1::
                                     completed &&
         query.read_result ==
             xar::game::ReadStewardDevelopCountyCandidatesResultV1::unavailable &&
         query.result.status ==
             xar::game::StewardDevelopCountyCandidatesStatusV1::unavailable &&
         query.result.snapshot_revision == 77 &&
         query.result.material.has_value() && !query.result.readiness.ready &&
         query.result.unavailable_reason ==
             xar::game::StewardDevelopCountyFailureReasonV1::
                  exact_build_not_admitted;
}

bool OtherRegistryIdentityFixture(
    void *, const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept {
  return false;
}

BOOL WINAPI PeekFixture(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }

struct Protection {
  void **slot = nullptr;
  DWORD protection = PAGE_READONLY;
};

bool QueryFixture(void *opaque, const void *address,
                  MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &protection = *static_cast<Protection *>(opaque);
  if (address != protection.slot) { return false; }
  const auto page =
      reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  information = {};
  information.BaseAddress = reinterpret_cast<void *>(page);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096;
  information.State = MEM_COMMIT;
  information.Protect = protection.protection;
  information.Type = MEM_IMAGE;
  return true;
}

bool ProtectFixture(void *opaque, void *, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  if (size != 4096) { return false; }
  auto &memory = *static_cast<Protection *>(opaque);
  old = memory.protection;
  memory.protection = protection;
  return true;
}

std::array<std::byte, 0x28> g_tls{};
void *__fastcall TlsFixture() noexcept { return g_tls.data(); }

bool TestCurrentMaterialRegisteredMailboxLifecycle() {
  using namespace xar::ck3_11906;
  constexpr auto executor =
      &ExecuteStewardDevelopCountyCandidatesMailboxQueryV1;
  // Another permitted identity reproduces the production whitelist rejection.
  // It is never submitted; the positive path invokes the real Develop executor.
  const std::array<MainThreadQueryExecutorV1, 1> typed{
      &OtherRegistryIdentityFixture};
  auto environment = xar::ck3_12002::BindThreadRuntimeImage(
      0x100000, xar::ck3_12002::kExecutableSha256, typed);
  if (environment.build_profile == nullptr ||
      environment.build_profile !=
          &xar::ck3_12002::ThreadRuntimeBuildProfile()) {
    return false;
  }
  MainThreadQueryMailboxV1 unregistered{};
  unregistered.permitted_executor = environment.permitted_executor;
  StewardDevelopCountyCandidatesMailboxContextV1 rejected_query{};
  MainThreadQueryTicketV1 rejected_ticket{99};
  const auto reader_calls_before = g_reader_calls;
  const auto snapshot_calls_before = g_snapshot_calls;
  if (TrySubmitMainThreadQueryV1(unregistered, executor, &rejected_query,
                                rejected_ticket) !=
          MainThreadQuerySubmitResultV1::invalid_request ||
      rejected_ticket.sequence != 0 ||
      rejected_query.executor_invocations != 0 ||
      g_reader_calls != reader_calls_before ||
      g_snapshot_calls != snapshot_calls_before) {
    return false;
  }

  xar::ck3_12002::NonwarMailboxExecutorsV1 callbacks{};
  callbacks.steward_develop_county = executor;
  xar::ck3_12002::RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  if (environment.permitted_executor_quattuordenary != executor) {
    return false;
  }

  const auto thread = GetCurrentThreadId();
  std::array<std::byte, 0x18> rng{};
  std::memcpy(rng.data() + 0x10, &thread, sizeof(thread));
  auto rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
  auto rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_pointer);
  std::array<std::byte, 0x28> jomini{};
  jomini[0x20] = std::byte{1};
  auto jomini_pointer = reinterpret_cast<std::uintptr_t>(jomini.data());
  std::array<std::byte, 0x18> game{};
  const auto date = g_snapshot.date_raw;
  std::memcpy(game.data() + 0x08, &date, sizeof(date));
  auto game_pointer = reinterpret_cast<std::uintptr_t>(game.data());
  std::uint8_t initialized = 1;
  g_tls[0x20] = std::byte{1};
  void *iat = reinterpret_cast<void *>(&PeekFixture);
  Protection protection{&iat};
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &iat;
  environment.resolved_peek_message_override = &PeekFixture;
  environment.global_rng_wrapper_slot_override =
      reinterpret_cast<std::uintptr_t>(&rng_wrapper);
  environment.jomini_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&jomini_pointer);
  environment.game_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&game_pointer);
  environment.tls_initialized_flag_override =
      reinterpret_cast<std::uintptr_t>(&initialized);
  environment.tls_context_getter_override = &TlsFixture;
  environment.memory_protection_context = &protection;
  environment.memory_query_override = &QueryFixture;
  environment.memory_protect_override = &ProtectFixture;
  environment.system_page_size_override = 4096;

  MainThreadQueryMailboxV1 mailbox{};
  if (!InstallMainThreadQueryMailboxV1(mailbox, environment)) { return false; }
  const bool passed = [&] {
    if (mailbox.permitted_executor_quattuordenary != executor ||
        iat != reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1)) {
      return false;
    }
    const auto return_rva = environment.build_profile->pump_exact_return_rva;
    for (std::size_t i = 0; i < 3; ++i) {
      if (ObserveMainThreadPumpAndDrainV1(mailbox, return_rva, thread)) {
        return false;
      }
    }
    if (!ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
      return false;
    }
    StewardDevelopCountyCandidatesMailboxContextV1 query{};
    query.mailbox = &mailbox;
    query.request.expected_snapshot_revision = 77;
    query.expected_snapshot = g_snapshot;
    // The actual .3 helper returns typed unavailable for this unadmitted build.
    query.material_profile = true;
    MainThreadQueryTicketV1 ticket{};
    if (TrySubmitMainThreadQueryV1(mailbox, executor, &query, ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      return false;
    }
    query.ticket = ticket;
    const bool drained =
        ObserveMainThreadPumpAndDrainV1(mailbox, return_rva, thread);
    const auto waited = WaitForMainThreadQueryV1(mailbox, ticket, 0);
    const bool completed =
        drained && ticket.sequence != 0 &&
        waited == MainThreadQueryWaitResultV1::completed &&
        query.executor_invocations == 1 &&
        query.completion ==
            StewardDevelopCountyCandidatesMailboxCompletionV1::completed &&
        query.execution_stamp.thread_id == thread &&
        query.execution_stamp.date_raw == date && query.execution_stamp.paused &&
        query.read_result ==
            xar::game::ReadStewardDevelopCountyCandidatesResultV1::unavailable &&
        query.result.status ==
            xar::game::StewardDevelopCountyCandidatesStatusV1::unavailable &&
        query.result.snapshot_revision == 77 &&
        query.result.material.has_value() && !query.result.readiness.ready &&
        query.result.unavailable_reason ==
            xar::game::StewardDevelopCountyFailureReasonV1::
                exact_build_not_admitted &&
        g_reader_calls == reader_calls_before &&
        g_snapshot_calls == snapshot_calls_before;
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, ticket);
    return completed &&
           reclaimed == MainThreadQueryReclaimResultV1::reclaimed;
  }();
  const auto uninstalled = UninstallMainThreadQueryMailboxV1(mailbox, 0);
  return passed &&
         uninstalled == MainThreadQueryUninstallResultV1::uninstalled &&
         iat == reinterpret_cast<void *>(&PeekFixture);
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  ++g_snapshot_calls;
  output = g_snapshot;
  return true;
}

game::ReadStewardDevelopCountyCandidatesResultV1
ReadStewardDevelopCountyCandidatesV1(
    const StewardDevelopCountyCandidatesNativeEnvironmentV1 &,
    const StewardDevelopCountyCandidatesAccessV1 &access,
    const StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept {
  ++g_reader_calls;
  game::StewardDevelopCountyCandidatesFrameV1 frame{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame)) {
    return game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  if (!g_reader_available) {
    output.status = game::StewardDevelopCountyCandidatesStatusV1::unavailable;
    output.unavailable_reason =
        game::StewardDevelopCountyFailureReasonV1::native_reader_not_frozen;
    return game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  }
  output.status = game::StewardDevelopCountyCandidatesStatusV1::available;
  output.observed_date_raw = frame.date_raw;
  output.player_character_id = 0x02000001;
  output.steward_character_id = 0x02000002;
  output.shown = true;
  output.valid = true;
  output.steward_increase_development_value_raw = 5'000'000;
  output.current_gold_raw = 8'000'000;
  output.no_ai_increase_development = false;
  output.has_active_improve_development_directive = true;
  output.same_frame_stable = true;
  output.readiness.ready = true;
  return game::ReadStewardDevelopCountyCandidatesResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 0x02000001;
  if (!TestParsing()) {
    std::cerr << "steward develop-county mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "steward develop-county direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(true) || !TestTypedCompletion(false)) {
    std::cerr << "steward develop-county typed completion fixture failed\n";
    return 1;
  }
  if (!TestCurrentMaterialUnsupportedCompletion()) {
    std::cerr << "steward develop-county current material mailbox fixture failed\n";
    return 1;
  }
  if (!TestCurrentMaterialRegisteredMailboxLifecycle()) {
    std::cerr << "steward develop-county registered mailbox lifecycle fixture failed\n";
    return 1;
  }
  std::cout << "steward-develop-county-candidates-v1 mailbox fixture passed\n";
  return 0;
}
