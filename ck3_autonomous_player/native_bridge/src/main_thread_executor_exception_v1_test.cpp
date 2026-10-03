#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <stdexcept>
#include <string>

namespace {

int __cdecl FakeSdlPollEvent(void *event);

struct FakeMemoryProtection {
  void *slot = nullptr;
  DWORD current_protect = PAGE_READONLY;
  std::uint32_t query_calls = 0;
  std::uint32_t protect_calls = 0;
  bool fail_next_readonly_restore = false;
};

bool FakeMemoryQuery(void *opaque, const void *address,
                     MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &protection = *static_cast<FakeMemoryProtection *>(opaque);
  ++protection.query_calls;
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
  ++protection.protect_calls;
  old_protect = protection.current_protect;
  if (page_size != 4096) {
    return false;
  }
  if (new_protect == PAGE_READONLY &&
      protection.fail_next_readonly_restore) {
    protection.fail_next_readonly_restore = false;
    return false;
  }
  protection.current_protect = new_protect;
  return true;
}

void *g_fake_tls_context = nullptr;

void *__fastcall FakeTlsContextGetter() noexcept {
  return g_fake_tls_context;
}

struct FakeRuntime {
  std::array<std::byte, 0x18> rng_state{};
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_wrapper_slot = 0;
  std::array<std::byte, 0x28> jomini_state{};
  std::array<std::byte, 0x28> alternate_jomini_state{};
  std::uintptr_t jomini_state_slot = 0;
  std::array<std::byte, 0x18> game_state{};
  std::array<std::byte, 0x18> alternate_game_state{};
  std::uintptr_t game_state_slot = 0;
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls_context{};
  std::array<std::byte, 0x28> alternate_tls_context{};
  FakeMemoryProtection protection{};
  void *sdl_poll_event_slot =
      reinterpret_cast<void *>(&FakeSdlPollEvent);

  explicit FakeRuntime(std::uint32_t owner_thread_id,
                       std::int32_t date_raw) {
    std::memcpy(rng_state.data() + 0x10, &owner_thread_id,
                sizeof(owner_thread_id));
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng_state.data());
    rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    const std::uint8_t paused = 1;
    std::memcpy(jomini_state.data() + 0x20, &paused, sizeof(paused));
    std::memcpy(alternate_jomini_state.data() + 0x20, &paused,
                sizeof(paused));
    jomini_state_slot =
        reinterpret_cast<std::uintptr_t>(jomini_state.data());
    std::memcpy(game_state.data() + 0x08, &date_raw, sizeof(date_raw));
    std::memcpy(alternate_game_state.data() + 0x08, &date_raw,
                sizeof(date_raw));
    game_state_slot = reinterpret_cast<std::uintptr_t>(game_state.data());
    const std::uint8_t tls_main_thread_marker = 1;
    std::memcpy(tls_context.data() + 0x20, &tls_main_thread_marker,
                sizeof(tls_main_thread_marker));
    std::memcpy(alternate_tls_context.data() + 0x20,
                &tls_main_thread_marker,
                sizeof(tls_main_thread_marker));
    g_fake_tls_context = tls_context.data();
  }

  xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 Environment(
      std::uintptr_t module_base, void **iat_slot,
      xar::ck3_11906::PeekMessageWFunctionV1 original) {
    protection.slot = iat_slot;
    auto environment = xar::ck3_11906::MainThreadQueryInstallEnvironmentV1{
        module_base,
        true,
        true,
        iat_slot,
        original,
        reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot),
        reinterpret_cast<std::uintptr_t>(&jomini_state_slot),
        reinterpret_cast<std::uintptr_t>(&game_state_slot),
        reinterpret_cast<std::uintptr_t>(&tls_initialized),
        &FakeTlsContextGetter,
        &protection,
        &FakeMemoryQuery,
        &FakeMemoryProtect,
        4096,
        true,
    };
    environment.sdl_poll_event_slot_override = &sdl_poll_event_slot;
    environment.resolved_sdl_poll_event_override = &FakeSdlPollEvent;
    return environment;
  }

  void SetDate(std::int32_t date_raw) {
    std::memcpy(game_state.data() + 0x08, &date_raw, sizeof(date_raw));
  }

  void SetPaused(std::uint8_t paused) {
    std::memcpy(jomini_state.data() + 0x20, &paused, sizeof(paused));
  }

  void SetTlsMarker(std::uint8_t marker) {
    std::memcpy(tls_context.data() + 0x20, &marker, sizeof(marker));
  }

  void SetOwner(std::uint32_t owner_thread_id) {
    std::memcpy(rng_state.data() + 0x10, &owner_thread_id,
                sizeof(owner_thread_id));
  }

  void UseAlternateIdentityObjects(bool use_alternate) {
    jomini_state_slot = reinterpret_cast<std::uintptr_t>(
        use_alternate ? alternate_jomini_state.data() : jomini_state.data());
    game_state_slot = reinterpret_cast<std::uintptr_t>(
        use_alternate ? alternate_game_state.data() : game_state.data());
    g_fake_tls_context = use_alternate ? alternate_tls_context.data()
                                       : tls_context.data();
  }
};


BOOL WINAPI FakePeekMessage(LPMSG, HWND, UINT, UINT, UINT) {
  return TRUE;
}

int __cdecl FakeSdlPollEvent(void *) {
  return 1;
}

void Require(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

struct FaultContext {
  std::uint32_t calls = 0;
  std::uint32_t observed_thread_id = 0;
  std::int32_t observed_date_raw = 0;
};

// Volatile runtime address forces a genuine Windows access violation. The
// production drain's SEH filter receives GetExceptionInformation itself.
volatile std::uintptr_t g_fault_address = 0;

__declspec(noinline) bool ExecuteAccessViolation(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &context = *static_cast<FaultContext *>(opaque);
  ++context.calls;
  context.observed_thread_id = stamp.thread_id;
  context.observed_date_raw = stamp.date_raw;
  *reinterpret_cast<volatile std::uint32_t *>(g_fault_address) = 0x517U;
  return false;
}

void TestActualExecutorExceptionAndPersistentRejection() {
  using namespace xar::ck3_11906;
  constexpr std::int32_t date_raw = 53'236'632;
  const auto owner_thread = GetCurrentThreadId();
  FakeRuntime runtime(owner_thread, date_raw);
  MainThreadQueryMailboxV1 mailbox{};
  void *iat = reinterpret_cast<void *>(&FakePeekMessage);
  auto environment = runtime.Environment(0x140000000ULL, &iat,
                                         &FakePeekMessage);
  environment.permitted_executor = &ExecuteAccessViolation;
  Require(InstallMainThreadQueryMailboxV1(mailbox, environment),
          "offline fixture installation failed");
  Require(!ObserveMainThreadPumpAndDrainV1(
              mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread),
          "first idle pump unexpectedly executed");
  Require(!ObserveMainThreadPumpAndDrainV1(
              mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread),
          "second idle pump unexpectedly executed");
  const auto ready = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  Require(ready.ready && ready.failure_flags == 0 &&
              ready.last_executor_exception_code == 0 &&
              ready.last_executor_exception_image ==
                  MainThreadExecutorExceptionImageV1::none &&
              ready.last_executor_exception_rva == 0,
          "initial ready exception metadata not empty");
  Require(SerializeMainThreadExecutorExceptionDiagnosticV1(ready) ==
              "{\"code\":0,\"image\":\"none\",\"rva\":null}",
          "empty native exception diagnostic wire mismatch");

  FaultContext context{};
  MainThreadQueryTicketV1 ticket{};
  Require(TrySubmitMainThreadQueryV1(mailbox, &ExecuteAccessViolation,
                                    &context, ticket) ==
              MainThreadQuerySubmitResultV1::submitted && ticket.sequence == 1,
          "fault executor not submitted through production gate");
  Require(ObserveMainThreadPumpAndDrainV1(
              mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread),
          "fault executor did not run in production drain");
  const auto fault = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  Require(context.calls == 1 && context.observed_thread_id == owner_thread &&
              context.observed_date_raw == date_raw,
          "fault callback stamp not actual paused owner");
  Require(fault.state == MainThreadQueryMailboxStateV1::executor_failed &&
              fault.failure_flags == 512 && !fault.ready &&
              fault.executor_started_requests == 1 &&
              fault.executed_requests == 1 &&
              fault.executor_started_sequence == ticket.sequence &&
              fault.completed_sequence == ticket.sequence &&
              fault.published_sequence == ticket.sequence,
          "real SEH did not preserve exact 512 and completion counters");
  Require(fault.last_executor_exception_code == EXCEPTION_ACCESS_VIOLATION &&
              fault.last_executor_exception_image ==
                  MainThreadExecutorExceptionImageV1::game,
          "real EXE access violation code/image not recorded");
  const auto image_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto callback_address = reinterpret_cast<std::uintptr_t>(&ExecuteAccessViolation);
  Require(image_base != 0 && callback_address >= image_base &&
              fault.last_executor_exception_rva >= callback_address - image_base &&
              fault.last_executor_exception_rva < callback_address - image_base + 256,
          "module-relative fault RVA outside actual fault callback");
  const auto wire = SerializeMainThreadExecutorExceptionDiagnosticV1(fault);
  Require(wire.find("\"code\":3221225477") != std::string::npos &&
              wire.find("\"image\":\"game\"") != std::string::npos &&
              wire.find("\"rva\":" + std::to_string(fault.last_executor_exception_rva)) !=
                  std::string::npos,
          "real SEH native diagnostic serializer missing metadata");
  Require(WaitForMainThreadQueryV1(mailbox, ticket, 0) ==
              MainThreadQueryWaitResultV1::executor_failed,
          "SEH completion not observable by production wait");

  MainThreadQueryTicketV1 rejected_before{};
  Require(TrySubmitMainThreadQueryV1(mailbox, &ExecuteAccessViolation,
                                    &context, rejected_before) ==
              MainThreadQuerySubmitResultV1::infrastructure_failed &&
              rejected_before.sequence == 0,
          "submission before reclaim incorrectly cleared fault");
  Require(ReclaimMainThreadQueryV1(mailbox, ticket) ==
              MainThreadQueryReclaimResultV1::reclaimed,
          "failed terminal ticket not reclaimed");
  MainThreadQueryTicketV1 rejected_after{};
  Require(TrySubmitMainThreadQueryV1(mailbox, &ExecuteAccessViolation,
                                    &context, rejected_after) ==
              MainThreadQuerySubmitResultV1::infrastructure_failed &&
              rejected_after.sequence == 0,
          "submission after reclaim automatically rearmed fault");
  Require(!ObserveMainThreadPumpAndDrainV1(
              mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread),
          "faulted idle mailbox unexpectedly reran executor");
  const auto reclaimed = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  Require(reclaimed.state == MainThreadQueryMailboxStateV1::idle &&
              reclaimed.failure_flags == 512 && !reclaimed.ready &&
              reclaimed.executor_started_requests == 1 &&
              reclaimed.executed_requests == 1 && context.calls == 1 &&
              reclaimed.completed_sequence == ticket.sequence &&
              reclaimed.published_sequence == ticket.sequence &&
              reclaimed.last_executor_exception_code ==
                  fault.last_executor_exception_code &&
              reclaimed.last_executor_exception_image ==
                  fault.last_executor_exception_image &&
              reclaimed.last_executor_exception_rva ==
                  fault.last_executor_exception_rva &&
              SerializeMainThreadExecutorExceptionDiagnosticV1(reclaimed) == wire,
          "reclaim changed fault metadata, counters or persistent 512 gate");
  Require(UninstallMainThreadQueryMailboxV1(mailbox, 0) ==
              MainThreadQueryUninstallResultV1::uninstalled &&
              iat == reinterpret_cast<void *>(&FakePeekMessage),
          "fixture hooks were not reclaimed");
  std::printf("{\"case\":\"actual_executor_seh_persistent_rejection\","
              "\"status\":\"GREEN\",\"failure_flags\":512,"
              "\"executor_started_requests\":1,\"executed_requests\":1,"
              "\"continued_submissions_rejected\":2,\"reclaim\":\"reclaimed\","
              "\"exception\":%s}\n", wire.c_str());
}

} // namespace

int main() {
  try {
    TestActualExecutorExceptionAndPersistentRejection();
    return 0;
  } catch (const std::exception &error) {
    std::fprintf(stderr, "actual executor SEH focused fixture RED: %s\n", error.what());
    return 1;
  }
}
