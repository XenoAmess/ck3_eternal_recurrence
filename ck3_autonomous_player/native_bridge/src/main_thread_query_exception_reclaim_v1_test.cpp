#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace {

using namespace xar::ck3_11906;

BOOL WINAPI FakePeekMessage(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
int __cdecl FakeSdlPollEvent(void *) { return 0; }
void *g_tls_context = nullptr;
void *__fastcall FakeTlsContextGetter() noexcept { return g_tls_context; }

struct MemoryProtection {
  void *slot = nullptr;
  DWORD protection = PAGE_READONLY;
};

bool MemoryQuery(void *opaque, const void *address,
                 MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &memory = *static_cast<MemoryProtection *>(opaque);
  if (address != memory.slot) return false;
  constexpr std::uintptr_t page_size = 4096;
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  information = {};
  information.BaseAddress = reinterpret_cast<void *>((value / page_size) * page_size);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = page_size;
  information.State = MEM_COMMIT;
  information.Protect = memory.protection;
  information.Type = MEM_IMAGE;
  return true;
}

bool MemoryProtect(void *opaque, void *, std::size_t size, DWORD protection,
                   DWORD &previous) noexcept {
  auto &memory = *static_cast<MemoryProtection *>(opaque);
  if (size != 4096) return false;
  previous = memory.protection;
  memory.protection = protection;
  return true;
}

struct Runtime {
  std::array<std::byte, 0x18> rng{};
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_slot = 0;
  std::array<std::byte, 0x28> jomini{};
  std::uintptr_t jomini_slot = 0;
  std::array<std::byte, 0x18> game{};
  std::uintptr_t game_slot = 0;
  std::uint8_t initialized = 1;
  std::array<std::byte, 0x28> tls{};
  MemoryProtection memory{};
  void *iat = reinterpret_cast<void *>(&FakePeekMessage);
  void *sdl_slot = reinterpret_cast<void *>(&FakeSdlPollEvent);
  MainThreadQueryMailboxV1 mailbox{};
  void *fault_page = nullptr;
  bool installed = false;

  explicit Runtime(std::uint32_t owner) {
    std::memcpy(rng.data() + 0x10, &owner, sizeof(owner));
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    const std::uint8_t paused = 1;
    std::memcpy(jomini.data() + 0x20, &paused, sizeof(paused));
    jomini_slot = reinterpret_cast<std::uintptr_t>(jomini.data());
    const std::int32_t date_raw = 53'288'232;
    std::memcpy(game.data() + 0x08, &date_raw, sizeof(date_raw));
    game_slot = reinterpret_cast<std::uintptr_t>(game.data());
    const std::uint8_t marker = 1;
    std::memcpy(tls.data() + 0x20, &marker, sizeof(marker));
    g_tls_context = tls.data();
    memory.slot = &iat;
    fault_page = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_NOACCESS);
  }

  ~Runtime() {
    if (installed) (void)UninstallMainThreadQueryMailboxV1(mailbox, 250);
    if (fault_page != nullptr) (void)VirtualFree(fault_page, 0, MEM_RELEASE);
    g_tls_context = nullptr;
  }

  MainThreadQueryInstallEnvironmentV1 Environment() {
    auto environment = MainThreadQueryInstallEnvironmentV1{
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        true, true, &iat, &FakePeekMessage,
        reinterpret_cast<std::uintptr_t>(&rng_slot),
        reinterpret_cast<std::uintptr_t>(&jomini_slot),
        reinterpret_cast<std::uintptr_t>(&game_slot),
        reinterpret_cast<std::uintptr_t>(&initialized),
        &FakeTlsContextGetter, &memory, &MemoryQuery, &MemoryProtect,
        4096, true,
    };
    environment.sdl_poll_event_slot_override = &sdl_slot;
    environment.resolved_sdl_poll_event_override = &FakeSdlPollEvent;
    return environment;
  }
};

struct Context {
  volatile unsigned char *fault_address = nullptr;
  std::uint32_t calls = 0;
};

bool Execute(void *opaque, const MainThreadExecutionStampV1 &) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  ++context.calls;
  if (context.fault_address != nullptr) *context.fault_address = 1;
  return true;
}

bool Check(bool result, const char *stage) {
  if (!result) std::fprintf(stderr, "FAIL: %s\n", stage);
  return result;
}

bool Run() {
  const auto owner = GetCurrentThreadId();
  Runtime runtime(owner);
  if (!Check(runtime.fault_page != nullptr, "allocate actual no-access AV page")) return false;
  auto environment = runtime.Environment();
  environment.permitted_executor = &Execute;
  runtime.installed = InstallMainThreadQueryMailboxV1(runtime.mailbox, environment);
  if (!Check(runtime.installed, "install synthetic runtime with production mailbox")) return false;
  auto &mailbox = runtime.mailbox;
  (void)ObserveMainThreadPumpAndDrainV1(mailbox, kHandlePdxEventsSdlPollEventReturnRva, owner);
  (void)ObserveMainThreadPumpAndDrainV1(mailbox, kHandlePdxEventsSdlPollEventReturnRva, owner);
  if (!Check(ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready, "paused owner proof")) return false;

  Context fault{static_cast<volatile unsigned char *>(runtime.fault_page)};
  MainThreadQueryTicketV1 fault_ticket{};
  if (!Check(TrySubmitMainThreadQueryV1(mailbox, &Execute, &fault, fault_ticket) ==
                 MainThreadQuerySubmitResultV1::submitted, "submit actual AV request") ||
      !Check(ObserveMainThreadPumpAndDrainV1(mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner), "drain AV request") ||
      !Check(WaitForMainThreadQueryV1(mailbox, fault_ticket, 0) ==
                 MainThreadQueryWaitResultV1::executor_failed, "wait executor_failed")) return false;
  const auto before = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  const auto diagnostic = SerializeMainThreadExecutorExceptionDiagnosticV1(before);
  if (!Check(before.failure_flags == main_thread_query_failure_executor_exception &&
                 before.last_executor_exception_code == EXCEPTION_ACCESS_VIOLATION &&
                 before.last_executor_exception_image != MainThreadExecutorExceptionImageV1::none &&
                 before.last_executor_exception_rva != 0 && fault.calls == 1,
             "actual SEH exception code/image/RVA and single invocation") ||
      !Check(ReclaimMainThreadQueryV1(mailbox, fault_ticket) ==
                 MainThreadQueryReclaimResultV1::reclaimed, "reclaim original terminal request")) return false;
  const auto after = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  if (!Check(after.failure_flags == 0 && after.ready &&
                 mailbox.state.load() == MainThreadQueryMailboxStateV1::idle &&
                 mailbox.executor == nullptr && mailbox.executor_context == nullptr &&
                 SerializeMainThreadExecutorExceptionDiagnosticV1(after) == diagnostic,
             "clear only request exception while preserving failed receipt diagnostic")) return false;

  Context normal{};
  MainThreadQueryTicketV1 normal_ticket{};
  if (!Check(TrySubmitMainThreadQueryV1(mailbox, &Execute, &normal, normal_ticket) ==
                 MainThreadQuerySubmitResultV1::submitted, "following normal request admitted") ||
      !Check(normal_ticket.sequence != fault_ticket.sequence, "distinct following request") ||
      !Check(ObserveMainThreadPumpAndDrainV1(mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner), "drain normal request") ||
      !Check(WaitForMainThreadQueryV1(mailbox, normal_ticket, 0) ==
                 MainThreadQueryWaitResultV1::completed && normal.calls == 1 && fault.calls == 1,
             "normal request completes without fault retry") ||
      !Check(ReclaimMainThreadQueryV1(mailbox, normal_ticket) ==
                 MainThreadQueryReclaimResultV1::reclaimed, "reclaim following normal request")) return false;

  MainThreadQueryTicketV1 other_ticket{};
  if (!Check(TrySubmitMainThreadQueryV1(mailbox, &Execute, &fault, other_ticket) ==
                 MainThreadQuerySubmitResultV1::submitted, "submit second independent AV request") ||
      !Check(ObserveMainThreadPumpAndDrainV1(mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner), "drain second AV request") ||
      !Check(WaitForMainThreadQueryV1(mailbox, other_ticket, 0) ==
                 MainThreadQueryWaitResultV1::executor_failed, "second AV reaches terminal")) return false;
  const auto second_diagnostic = SerializeMainThreadExecutorExceptionDiagnosticV1(
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox));
  mailbox.failure_flags.fetch_or(main_thread_query_failure_thread_identity);
  if (!Check(ReclaimMainThreadQueryV1(mailbox, other_ticket) ==
                 MainThreadQueryReclaimResultV1::reclaimed, "reclaim with unrelated infrastructure flag")) return false;
  const auto preserved = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  MainThreadQueryTicketV1 blocked_ticket{};
  return Check(preserved.failure_flags == main_thread_query_failure_thread_identity &&
                   SerializeMainThreadExecutorExceptionDiagnosticV1(preserved) == second_diagnostic &&
                   TrySubmitMainThreadQueryV1(mailbox, &Execute, &normal, blocked_ticket) ==
                       MainThreadQuerySubmitResultV1::infrastructure_failed &&
                   normal.calls == 1 && fault.calls == 2,
               "other failure bit and admission behavior remain unchanged");
}

} // namespace

int main() {
  if (!Run()) return 1;
  std::puts("PASS: actual SEH AV reclaimed; diagnostic preserved; next normal request completes; other infrastructure flag retained");
  return 0;
}
