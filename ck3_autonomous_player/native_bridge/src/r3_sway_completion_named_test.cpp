// Reuse only fixture-owned core/storage/adapter setup, not its test entry.
#define main SwayCompletionPreviousFixtureMain
#include "ck3_12002_sway_completion_test.cpp"
#undef main

namespace {
namespace api = xar::ck3_11906;
void *queue_tls_context = nullptr;
void *__fastcall QueueTls() noexcept { return queue_tls_context; }
BOOL WINAPI QueuePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Protection {
  void **slot = nullptr;
  DWORD current = PAGE_READONLY;
};
bool MemoryQuery(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &info) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (address != memory.slot) return false;
  const auto start = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  info = {};
  info.BaseAddress = reinterpret_cast<void *>(start);
  info.AllocationBase = info.BaseAddress;
  info.AllocationProtect = PAGE_READONLY;
  info.RegionSize = 4096; info.State = MEM_COMMIT;
  info.Protect = memory.current; info.Type = MEM_IMAGE;
  return true;
}
bool MemoryProtect(void *opaque, void *, std::size_t size,
    DWORD protection, DWORD &previous) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (size != 4096) return false;
  previous = memory.current; memory.current = protection; return true;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "named queue output directory");
    const std::filesystem::path output{argv[1]};
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.date_raw = date_raw; adapter.frame.paused = true; adapter.frame.speed = 1;
    adapter.frame.player_id = 0; adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true; adapter.frame.played_character_id = actor_id;
    adapter.frame.played_character_alive = true;
    std::array<std::byte, 0x28> tls{};
    tls[0x20] = std::byte{1}; queue_tls_context = tls.data();
    std::uint8_t tls_initialized = 1;
    std::uintptr_t unused_rng = 0;
    void *peek_slot = reinterpret_cast<void *>(&QueuePeek);
    Protection protection{&peek_slot};
    // The version-independent production install receives caller-owned fixture
    // overrides. This synthetic boundary is not an executable ABI/live claim.
    api::MainThreadQueryBuildProfileV1 fixture_profile{};
    fixture_profile.pump_exact_return_rva = 0x12002;
    api::MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = image_base;
    environment.exact_build_admitted = true; environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &QueuePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&unused_rng);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.jomini_pointer);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.state_pointer);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &QueueTls;
    environment.memory_protection_context = &protection;
    environment.memory_query_override = &MemoryQuery;
    environment.memory_protect_override = &MemoryProtect;
    environment.system_page_size_override = 4096;
    environment.executor_submission_enabled = true;
    environment.build_profile = &fixture_profile;
    environment.permitted_executor_sway_completion12002 = &ExecuteSwayCompletionMailboxV1;
    api::MainThreadQueryMailboxV1 mailbox;
    Check(api::InstallMainThreadQueryMailboxV1(mailbox, environment),
        "production Install admits the new named completion slot");
    Check(mailbox.permitted_executor_sway_completion12002 == &ExecuteSwayCompletionMailboxV1 &&
        mailbox.permitted_executor == nullptr,
        "actual install copies named executor, without a generic permit");
    for (int pump = 0; pump < 2; ++pump)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox,
          fixture_profile.pump_exact_return_rva, GetCurrentThreadId());
    Check(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready,
        "actual paused owner pump observations qualify queue submission");
    SwayCompletionMailboxContextV1 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = revision; query.envelope.typed_context = &query;
    query.request = fixture.request; query.bindings = fixture.bindings;
    continue_result = false;
    Check(api::TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayCompletionMailboxV1,
        &query.envelope, query.envelope.ticket) == api::MainThreadQuerySubmitResultV1::submitted,
        "real TrySubmit admits the named callback");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::queued,
        "actual queued state precedes executor");
    Check(api::ObserveMainThreadPumpAndDrainV1(mailbox,
        fixture_profile.pump_exact_return_rva, GetCurrentThreadId()),
        "actual owner pump drains named callback");
    Check(api::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100) ==
        api::MainThreadQueryWaitResultV1::completed,
        "actual Wait reports completed callback");
    Check(query.completed && query.envelope.frame_stable && query.failure.empty() &&
        query.result.available && query.result.exact_instance_join_ready &&
        query.result.native_can_continue_observed && !query.result.native_can_continue &&
        !query.result.native_terminal_state_observed && continue_calls == 2,
        "actual named queue reaches production reader and preserves native false");
    Check(api::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket) ==
        api::MainThreadQueryReclaimResultV1::reclaimed &&
        mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "actual completed ticket reclaimed to idle");
    Save(output, "named-queue-false-wire.json", query.result);
    Check(api::UninstallMainThreadQueryMailboxV1(mailbox, 100) ==
        api::MainThreadQueryUninstallResultV1::uninstalled,
        "fixture install released through production uninstall");
    queue_tls_context = nullptr;
    std::cout << "PASS actual named sway-completion install/env permit, TrySubmit, two paused owner pumps, "
                 "drain, production reader, Wait/Reclaim and false full-command wire\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
