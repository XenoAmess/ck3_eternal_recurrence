#include "xar_bridge/ck3_12002_thread_runtime.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace {
namespace mailbox_api = xar::ck3_11906;
namespace build = xar::ck3_12002;

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset, Value value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  void *iat = nullptr;
  DWORD page_protect = PAGE_READONLY;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> game{};
  std::array<std::byte, 0x28> tls{};
  std::uintptr_t jomini_slot = 0;
  std::uintptr_t game_slot = 0;
  std::uintptr_t null_rng_slot = 0;
  std::uint8_t tls_initialized = 1;
};
Fixture *g_fixture = nullptr;

BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
int __cdecl FakeSdlPoll(void *) { return 0; }
void *__fastcall FakeTls() noexcept { return g_fixture->tls.data(); }
bool FakeQuery(void *opaque, const void *address,
               MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (address != &fixture.iat) { return false; }
  output = {};
  const auto page = reinterpret_cast<std::uintptr_t>(address) & ~4095ULL;
  output.BaseAddress = reinterpret_cast<void *>(page);
  output.AllocationBase = output.BaseAddress;
  output.RegionSize = 4096;
  output.State = MEM_COMMIT;
  output.Type = MEM_IMAGE;
  output.Protect = fixture.page_protect;
  return true;
}
bool FakeProtect(void *opaque, void *, std::size_t size, DWORD desired,
                 DWORD &previous) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (size != 4096) { return false; }
  previous = fixture.page_protect;
  fixture.page_protect = desired;
  return true;
}

struct Execution {
  std::uint32_t calls = 0;
  mailbox_api::MainThreadExecutionStampV1 stamp{};
};
bool Execute(void *opaque,
             const mailbox_api::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &execution = *static_cast<Execution *>(opaque);
  ++execution.calls;
  execution.stamp = stamp;
  return true;
}

bool ExecuteSemantic(void *opaque,
                     const mailbox_api::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

struct SnapshotCacheFixture {
  std::uint32_t samples = 0;
  bool reader_available = true;
  bool valid = false;
  mailbox_api::MainThreadExecutionStampV1 last_stamp{};
};
bool ObserveSnapshot(void *opaque,
                     const mailbox_api::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &cache = *static_cast<SnapshotCacheFixture *>(opaque);
  cache.valid = false;
  ++cache.samples;
  if (!cache.reader_available) { return false; }
  cache.last_stamp = stamp;
  cache.valid = true;
  return true;
}

bool TestMappedImage(const char *path) {
  std::ifstream input(path, std::ios::binary);
  const std::string file{std::istreambuf_iterator<char>(input), {}};
  if (file.size() < sizeof(IMAGE_DOS_HEADER)) { return false; }
  const auto *dos = reinterpret_cast<const IMAGE_DOS_HEADER *>(file.data());
  if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew < 0 ||
      static_cast<std::size_t>(dos->e_lfanew) >
          file.size() - sizeof(IMAGE_NT_HEADERS64)) { return false; }
  const auto *nt = reinterpret_cast<const IMAGE_NT_HEADERS64 *>(
      file.data() + dos->e_lfanew);
  if (nt->Signature != IMAGE_NT_SIGNATURE ||
      nt->OptionalHeader.SizeOfImage != 0x61C5000) { return false; }
  std::vector<std::byte> image(nt->OptionalHeader.SizeOfImage);
  std::memcpy(image.data(), file.data(), nt->OptionalHeader.SizeOfHeaders);
  const auto *section = IMAGE_FIRST_SECTION(nt);
  for (WORD i = 0; i < nt->FileHeader.NumberOfSections; ++i) {
    const auto &entry = section[i];
    if (entry.SizeOfRawData == 0) { continue; }
    if (entry.PointerToRawData > file.size() ||
        entry.SizeOfRawData > file.size() - entry.PointerToRawData ||
        entry.VirtualAddress > image.size() ||
        entry.SizeOfRawData > image.size() - entry.VirtualAddress) {
      return false;
    }
    std::memcpy(image.data() + entry.VirtualAddress,
                file.data() + entry.PointerToRawData, entry.SizeOfRawData);
  }
  const auto base = reinterpret_cast<std::uintptr_t>(image.data());
  if (!build::VerifyThreadRuntimeImage(base)) { return false; }
  image[build::kMainThreadTlsStartupStoreRva] ^= std::byte{1};
  return !build::VerifyThreadRuntimeImage(base);
}

bool TestMailboxProfile() {
  constexpr std::uintptr_t fake_base = 0x140000000ULL;
  constexpr std::uint32_t owner = 0x1234;
  std::array<mailbox_api::MainThreadQueryExecutorV1, 14> callbacks{};
  callbacks[0] = &Execute;
  callbacks[13] = &ExecuteSemantic;
  auto environment = build::BindThreadRuntimeImage(
      fake_base, build::kExecutableSha256, callbacks);
  if (!environment.exact_build_admitted || environment.offline_fixture ||
      !environment.executor_submission_enabled ||
      environment.permitted_executor != &Execute ||
      environment.permitted_executor_semantic12002 != &ExecuteSemantic ||
      environment.permitted_executor_quattuordenary != nullptr ||
      environment.build_profile == nullptr ||
      environment.build_profile->pump_exact_return_rva != 0x40D9432 ||
      environment.build_profile->peek_message_iat_slot_rva != 0x43DAE38 ||
      environment.build_profile->tls_initialized_flag_rva != 0x5CBE6BF ||
      environment.build_profile->jomini_state_slot_rva != 0x5C6A520 ||
      build::BindThreadRuntimeImage(fake_base, "wrong").exact_build_admitted ||
      build::BindThreadRuntimeImage(0, build::kExecutableSha256)
          .exact_build_admitted) { return false; }
  const auto observation = build::BindThreadRuntimeImage(
      fake_base, build::kExecutableSha256);
  if (observation.executor_submission_enabled) { return false; }
  std::array<mailbox_api::MainThreadQueryExecutorV1, 15> too_many{};
  if (build::BindThreadRuntimeImage(fake_base, build::kExecutableSha256,
                                   too_many).exact_build_admitted) {
    return false;
  }
  Fixture fixture;
  g_fixture = &fixture;
  fixture.iat = reinterpret_cast<void *>(&FakePeek);
  fixture.jomini_slot = reinterpret_cast<std::uintptr_t>(fixture.jomini.data());
  fixture.game_slot = reinterpret_cast<std::uintptr_t>(fixture.game.data());
  Store(fixture.jomini, 0x20, std::uint8_t{0});
  Store(fixture.game, 0x08, std::int32_t{123456});
  Store(fixture.tls, 0x20, std::uint8_t{1});
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &fixture.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override =
      reinterpret_cast<std::uintptr_t>(&fixture.null_rng_slot);
  environment.jomini_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&fixture.jomini_slot);
  environment.game_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&fixture.game_slot);
  environment.tls_initialized_flag_override =
      reinterpret_cast<std::uintptr_t>(&fixture.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &fixture;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  void *sdl_slot = reinterpret_cast<void *>(&FakeSdlPoll);
  environment.sdl_poll_event_slot_override = &sdl_slot;
  environment.resolved_sdl_poll_event_override = &FakeSdlPoll;
  SnapshotCacheFixture cache;
  environment.snapshot_observer_callback = &ObserveSnapshot;
  environment.snapshot_observer_context = &cache;
  mailbox_api::MainThreadQueryMailboxV1 mailbox;
  if (!mailbox_api::InstallMainThreadQueryMailboxV1(mailbox, environment) ||
      mailbox.pump_exact_return_rva != 0x40D9432 ||
      mailbox.sdl_poll_event_exact_return_rva != 0 ||
      mailbox.sdl_poll_event_slot != nullptr ||
      mailbox.original_sdl_poll_event != nullptr ||
      sdl_slot != reinterpret_cast<void *>(&FakeSdlPoll) ||
      fixture.page_protect != PAGE_READONLY) { return false; }
  Execution execution;
  mailbox_api::MainThreadQueryTicketV1 ticket;
  if (mailbox_api::TrySubmitMainThreadQueryV1(mailbox, &Execute, &execution,
                                             ticket) !=
      mailbox_api::MainThreadQuerySubmitResultV1::paused_main_thread_not_observed) {
    return false;
  }
  if (mailbox_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox_api::kSdlWindowsPumpFirstPeekReturnRva, owner) ||
      mailbox_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, mailbox_api::kHandlePdxEventsSdlPollEventReturnRva, owner) ||
      mailbox.pump_epochs.load() != 0) { return false; }
  mailbox_api::ObserveMainThreadPumpAndDrainV1(
      mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner);
  if (!cache.valid || cache.samples != 1 || cache.last_stamp.paused ||
      cache.last_stamp.thread_id != owner ||
      mailbox_api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  // Fixture delivery of the worker's cloned pause command; no native call.
  const auto pause_command = build::MakePauseCommand(fake_base, 7, true);
  Store(fixture.jomini, 0x20, pause_command.paused);
  for (int i = 0; i < 2; ++i) {
    if (mailbox_api::ObserveMainThreadPumpAndDrainV1(
            mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner)) {
      return false;
    }
  }
  if (!mailbox_api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready ||
      mailbox_api::TrySubmitMainThreadQueryV1(mailbox, &ExecuteSemantic, &execution,
                                             ticket) !=
          mailbox_api::MainThreadQuerySubmitResultV1::submitted ||
      !mailbox_api::ObserveMainThreadPumpAndDrainV1(
          mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner) ||
      execution.calls != 1 || execution.stamp.thread_id != owner ||
      execution.stamp.date_raw != 123456 || !execution.stamp.paused ||
      execution.stamp.tls_main_thread_marker != 1 ||
      !cache.valid || !cache.last_stamp.paused || cache.samples != 4 ||
      mailbox_api::WaitForMainThreadQueryV1(mailbox, ticket, 0) !=
          mailbox_api::MainThreadQueryWaitResultV1::completed ||
      mailbox_api::ReclaimMainThreadQueryV1(mailbox, ticket) !=
          mailbox_api::MainThreadQueryReclaimResultV1::reclaimed) {
    return false;
  }
  // Snapshot-reader failure invalidates the cache without poisoning queries.
  cache.reader_available = false;
  mailbox_api::ObserveMainThreadPumpAndDrainV1(
      mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner);
  if (cache.valid || mailbox.failure_flags.load() != 0 ||
      !mailbox_api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  cache.reader_available = true;
  if (mailbox_api::TrySubmitMainThreadQueryV1(mailbox, &ExecuteSemantic, &execution,
                                             ticket) !=
          mailbox_api::MainThreadQuerySubmitResultV1::submitted ||
      mailbox_api::CancelMainThreadQueryV1(mailbox, ticket) !=
          mailbox_api::MainThreadQueryCancelResultV1::cancelled ||
      mailbox_api::ReclaimMainThreadQueryV1(mailbox, ticket) !=
          mailbox_api::MainThreadQueryReclaimResultV1::reclaimed ||
      execution.calls != 1) { return false; }
  const auto resume_command = build::MakePauseCommand(fake_base, 7, false);
  Store(fixture.jomini, 0x20, resume_command.paused);
  Store(fixture.game, 0x08, std::int32_t{123457});
  mailbox_api::ObserveMainThreadPumpAndDrainV1(
      mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner);
  if (mailbox_api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready ||
      !cache.valid || cache.last_stamp.paused ||
      cache.last_stamp.date_raw != 123457 || cache.samples != 6) {
    return false;
  }
  if (mailbox_api::UninstallMainThreadQueryMailboxV1(mailbox, 0) !=
          mailbox_api::MainThreadQueryUninstallResultV1::uninstalled ||
      fixture.iat != reinterpret_cast<void *>(&FakePeek) ||
      fixture.page_protect != PAGE_READONLY ||
      mailbox.snapshot_observer_callback != nullptr ||
      mailbox.snapshot_observer_context != nullptr) { return false; }
  mailbox_api::ObserveMainThreadPumpAndDrainV1(
      mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, owner);
  if (cache.samples != 6) { return false; }
  return true;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2 || !TestMappedImage(argv[1])) {
    std::fprintf(stderr, "12002 mapped-image thread anchor fixture failed\n");
    return 1;
  }
  if (!TestMailboxProfile()) {
    std::fprintf(stderr, "12002 mailbox profile fixture failed\n");
    return 2;
  }
  std::puts("PASS: 12002 mapped anchors, legacy SDL exclusion, unpaused snapshot, pause command, named semantic executor, observer failure isolation, resume snapshot, cancellation and IAT restore; no live CK3 access");
  return 0;
}
