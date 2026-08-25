#include "xar_bridge/war_entry_assessments_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <thread>

namespace {

struct FakeMemoryProtection {
  void *slot = nullptr;
  DWORD current_protect = PAGE_READONLY;
};

bool FakeMemoryQuery(void *opaque, const void *address,
                     MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &protection = *static_cast<FakeMemoryProtection *>(opaque);
  if (address != protection.slot) {
    return false;
  }
  constexpr std::uintptr_t page_size = 4096;
  const auto slot_address = reinterpret_cast<std::uintptr_t>(address);
  information = {};
  information.BaseAddress = reinterpret_cast<void *>(
      (slot_address / page_size) * page_size);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = page_size;
  information.State = MEM_COMMIT;
  information.Protect = protection.current_protect;
  information.Type = MEM_IMAGE;
  return true;
}

bool FakeMemoryProtect(void *opaque, void *, std::size_t page_size,
                       DWORD new_protect, DWORD &old_protect) noexcept {
  auto &protection = *static_cast<FakeMemoryProtection *>(opaque);
  if (page_size != 4096) {
    return false;
  }
  old_protect = protection.current_protect;
  protection.current_protect = new_protect;
  return true;
}

void *g_fake_tls_context = nullptr;

void *__fastcall FakeTlsContextGetter() noexcept {
  return g_fake_tls_context;
}

BOOL WINAPI FakePeekMessage(LPMSG message, HWND, UINT, UINT, UINT) {
  if (message != nullptr) {
    message->message = WM_NULL;
  }
  return TRUE;
}

struct FakeRuntime {
  std::array<std::byte, 0x18> rng_state{};
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_wrapper_slot = 0;
  std::array<std::byte, 0x28> jomini_state{};
  std::uintptr_t jomini_state_slot = 0;
  std::array<std::byte, 0x18> game_state{};
  std::uintptr_t game_state_slot = 0;
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls_context{};
  FakeMemoryProtection protection{};

  explicit FakeRuntime(std::int32_t date_raw) {
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng_state.data());
    rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    const std::uint8_t paused = 1;
    std::memcpy(jomini_state.data() + 0x20, &paused, sizeof(paused));
    jomini_state_slot = reinterpret_cast<std::uintptr_t>(jomini_state.data());
    std::memcpy(game_state.data() + 0x08, &date_raw, sizeof(date_raw));
    game_state_slot = reinterpret_cast<std::uintptr_t>(game_state.data());
    const std::uint8_t marker = 1;
    std::memcpy(tls_context.data() + 0x20, &marker, sizeof(marker));
    g_fake_tls_context = tls_context.data();
  }

  void SetOwner(std::uint32_t thread_id) {
    std::memcpy(rng_state.data() + 0x10, &thread_id, sizeof(thread_id));
  }

  xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 Environment(
      void **iat_slot) {
    protection.slot = iat_slot;
    xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = 0x140000000;
    environment.exact_build_admitted = true;
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = iat_slot;
    environment.resolved_peek_message_override = &FakePeekMessage;
    environment.global_rng_wrapper_slot_override =
        reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot);
    environment.jomini_state_slot_override =
        reinterpret_cast<std::uintptr_t>(&jomini_state_slot);
    environment.game_state_slot_override =
        reinterpret_cast<std::uintptr_t>(&game_state_slot);
    environment.tls_initialized_flag_override =
        reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &FakeTlsContextGetter;
    environment.memory_protection_context = &protection;
    environment.memory_query_override = &FakeMemoryQuery;
    environment.memory_protect_override = &FakeMemoryProtect;
    environment.system_page_size_override = 4096;
    environment.executor_submission_enabled = true;
    return environment;
  }
};

struct BlockingCaptureContext {
  HANDLE entered = nullptr;
  HANDLE release = nullptr;
  std::atomic<std::uint32_t> calls{0};
};

bool BlockingCapture(
    void *opaque, xar::game::WarEntryAssessmentFrameV1 &) noexcept {
  auto &context = *static_cast<BlockingCaptureContext *>(opaque);
  context.calls.fetch_add(1, std::memory_order_acq_rel);
  SetEvent(context.entered);
  (void)WaitForSingleObject(context.release, 5000);
  return false;
}

void DummyAssessment(
    void *, const xar::ck3_11906::NativeWarEntryActorStateV1 *, void *,
    xar::ck3_11906::NativeWarEntryAssessmentOutputV1 *,
    const std::int64_t *, std::int32_t) {}

void DummyActorStateBuilder(
    void *, xar::ck3_11906::NativeWarEntryActorStateV1 *) {}

void DummyNetwork(
    void *, xar::ck3_11906::NativeWarEntryNetworkConfigurationV1 *) {}

void *DummyEffectiveTarget(void *, void *target, std::uint32_t, bool) {
  return target;
}

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

bool WaitForFlag(const std::atomic<bool> &flag) {
  for (std::uint32_t attempt = 0; attempt < 5000; ++attempt) {
    if (flag.load(std::memory_order_acquire)) {
      return true;
    }
    Sleep(1);
  }
  return false;
}

bool DirectInvocationIsRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::WarEntryAssessmentMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 3;
  stamp.thread_id = GetCurrentThreadId();
  stamp.rng_wrapper = 1;
  stamp.rng_state = 2;
  stamp.rng_owner_thread_id = stamp.thread_id;
  stamp.tls_initialized_flag_address = 3;
  stamp.tls_initialized = 1;
  stamp.tls_context = 4;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 5;
  stamp.game_state = 6;
  stamp.date_raw = 53175816;
  stamp.paused = true;
  const auto executed =
      xar::ck3_11906::ExecuteWarEntryAssessmentMailboxQueryV1(&query, stamp);
  const auto ok =
      !executed &&
      query.completion == xar::ck3_11906::
                              WarEntryAssessmentMailboxCompletionV1::
                                  infrastructure_rejected &&
      query.executor_invocations == 0;
  if (!ok) {
    std::cerr << "direct invocation mismatch: executed=" << executed
              << " completion=" << static_cast<std::uint32_t>(query.completion)
              << " invocations=" << query.executor_invocations << '\n';
  }
  return ok;
}

bool MailboxExecutionPreservesContextThroughExecutingTimeout() {
  using namespace xar::ck3_11906;
  // Uninstall restores the IAT but deliberately process-pins the hook owner so
  // a thread that fetched the old target before restore cannot observe freed
  // storage. This test executable therefore owns exactly one static mailbox.
  static MainThreadQueryMailboxV1 mailbox{};
  void *iat_slot = reinterpret_cast<void *>(&FakePeekMessage);
  FakeRuntime runtime(53175816);
  auto install_environment = runtime.Environment(&iat_slot);
  if (!InstallMainThreadQueryMailboxV1(mailbox, install_environment)) {
    return false;
  }

  BlockingCaptureContext capture{};
  capture.entered = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  capture.release = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  if (capture.entered == nullptr || capture.release == nullptr) {
    if (capture.entered != nullptr) {
      CloseHandle(capture.entered);
    }
    if (capture.release != nullptr) {
      CloseHandle(capture.release);
    }
    (void)UninstallMainThreadQueryMailboxV1(mailbox, 1000);
    return false;
  }

  void *dummy_game_state = &runtime;
  void *dummy_storage = &runtime;
  void *dummy_fallback = &runtime;
  void *dummy_builder_dependency = &runtime;
  WarEntryAssessmentMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.environment.game_state_slot = &dummy_game_state;
  query.environment.character_storage_slot = &dummy_storage;
  query.environment.character_fallback_slot = &dummy_fallback;
  query.environment.actor_state_dependency_slot =
      &dummy_builder_dependency;
  query.environment.actor_state_builder = &DummyActorStateBuilder;
  query.environment.assessment = &DummyAssessment;
  query.environment.network_collector = &DummyNetwork;
  query.environment.effective_target_resolver = &DummyEffectiveTarget;
  query.environment.offline_fixture_function_overrides = true;
  query.access.context = &capture;
  query.access.capture_frame = &BlockingCapture;
  query.request.expected_snapshot_revision = 74;
  query.request.target_character_ids = {12345};

  std::atomic<bool> primed{false};
  std::atomic<bool> submitted{false};
  bool drained = false;
  std::thread pump([&]() {
    const auto thread_id = GetCurrentThreadId();
    runtime.SetOwner(thread_id);
    for (std::uint64_t epoch = 0;
         epoch < kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
         ++epoch) {
      (void)ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, thread_id);
    }
    primed.store(true, std::memory_order_release);
    while (!submitted.load(std::memory_order_acquire)) {
      Sleep(1);
    }
    drained = ObserveMainThreadPumpAndDrainV1(
        mailbox, kSdlWindowsPumpFirstPeekReturnRva, thread_id);
  });

  bool ok = WaitForFlag(primed);
  if (ok) {
    ok = TrySubmitMainThreadQueryV1(
             mailbox, &ExecuteWarEntryAssessmentMailboxQueryV1, &query,
             query.ticket) == MainThreadQuerySubmitResultV1::submitted;
  }
  submitted.store(true, std::memory_order_release);
  if (ok) {
    ok = WaitForSingleObject(capture.entered, 5000) == WAIT_OBJECT_0;
  }
  if (ok) {
    ok = WaitForMainThreadQueryV1(mailbox, query.ticket, 0) ==
             MainThreadQueryWaitResultV1::timeout_executor_already_running &&
         query.executor_invocations == 1 &&
         query.completion ==
             WarEntryAssessmentMailboxCompletionV1::not_executed;
  }

  // The caller-owned query remains alive after the executing timeout. It is
  // released only after the main thread exits the callback and reclaim wins.
  SetEvent(capture.release);
  pump.join();
  if (ok) {
    ok = drained &&
         WaitForMainThreadQueryV1(mailbox, query.ticket, 1000) ==
             MainThreadQueryWaitResultV1::completed &&
         query.executor_invocations == 1 &&
         query.completion ==
             WarEntryAssessmentMailboxCompletionV1::query_unavailable &&
         query.read_result ==
             xar::game::ReadWarEntryAssessmentsV1Result::unavailable &&
         query.result.unavailable_stage == "frame_before" &&
         !query.result.available && capture.calls.load() == 1;
  }
  if (ok) {
    ok = ReclaimMainThreadQueryV1(mailbox, query.ticket) ==
         MainThreadQueryReclaimResultV1::reclaimed;
  }
  const auto uninstall = UninstallMainThreadQueryMailboxV1(mailbox, 1000);
  ok = ok && uninstall == MainThreadQueryUninstallResultV1::uninstalled &&
       iat_slot == reinterpret_cast<void *>(&FakePeekMessage);
  CloseHandle(capture.release);
  CloseHandle(capture.entered);
  return ok;
}

bool SourceContract(int argc, char **argv) {
  if (argc != 5 ||
      !xar::ck3_11906::
          kWarEntryAssessmentsV1MailboxAdapterProductionWired) {
    return false;
  }
  const auto header = ReadFile(argv[1]);
  const auto source = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto documentation = ReadFile(argv[4]);
  return !header.empty() && !source.empty() && !abi.empty() &&
         !documentation.empty() &&
         Contains(header, "timeout_executor_already_running") &&
         Contains(header, "ReclaimMainThreadQueryV1 succeeds") &&
         Contains(header, "query-specific unavailable result returns true") &&
         Contains(source, "MainThreadQueryMailboxStateV1::executing") &&
         Contains(source, "mailbox.executor_context") &&
         Contains(source, "GetCurrentThreadId() != stamp.thread_id") &&
         Contains(source, "MarkQueryUnavailable") &&
         Contains(source, "return true") &&
         Contains(abi, "\"production_wiring\": true") &&
         Contains(abi, "\"live_boundary_observation\": true") &&
         Contains(abi, "\"live_executor_observation\": false") &&
         Contains(abi, "RNG owner is provenance only") &&
         Contains(abi, "\"first_live_target_limit\": 1") &&
         Contains(abi, "\"process_pin_static_mailbox_fixture\": true") &&
         Contains(abi, "timeout_executor_already_running") &&
         Contains(abi, "query_specific_unavailable") &&
         Contains(documentation, "MainThreadQueryExecutorV1") &&
         Contains(documentation, "terminal + reclaim");
}

} // namespace

int main(int argc, char **argv) {
  if (!DirectInvocationIsRejected()) {
    return 1;
  }
  if (!MailboxExecutionPreservesContextThroughExecutingTimeout()) {
    return 2;
  }
  if (!SourceContract(argc, argv)) {
    return 3;
  }
  return 0;
}
