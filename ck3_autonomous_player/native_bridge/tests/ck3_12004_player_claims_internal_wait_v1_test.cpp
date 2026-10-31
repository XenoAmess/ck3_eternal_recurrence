// Owned-memory regression for the real WorkerAdapter internal 30s Wait retry.
// The included fixture entry and its old8/45 scenes are never invoked.
// This isolated EXE observes only its own GetTickCount64 import references;
// the real timer value is forwarded unchanged and production budgets are kept.
#define main PlayerClaimsPriorLifecycleEntryNotExecuted
#include "ck3_12004_player_claims_semantic_mailbox_v1_test.cpp"
#undef main
#include <intrin.h>
#include <limits>

namespace observation {
using TickFunction = ULONGLONG (WINAPI *)();
std::atomic<TickFunction> real_tick{nullptr};
std::atomic<bool> armed{false};
std::atomic<DWORD> worker_id{0};
std::atomic<std::uintptr_t> wait_begin{0}, wait_end{0}, first_site{0};
std::atomic<std::uint64_t> entry_count{0}, first_tick{0}, second_tick{0};
struct Sample { std::atomic<std::uintptr_t> site{0}; std::atomic<DWORD> thread{0}; std::atomic<std::uint64_t> tick{0}; std::atomic<bool> ready{false}; }; constexpr std::size_t MAX_SAMPLES = 8; std::array<Sample, MAX_SAMPLES> armed_samples; std::array<Sample, MAX_SAMPLES> worker_samples; std::atomic<std::size_t> armed_count{0}; std::atomic<std::size_t> worker_count{0}; std::atomic<std::size_t> total_hook_calls{0};
std::atomic<DWORD> expected_worker_id{0};

// Forward declaration of the independently implemented normalization helper.
bool NormalizeRuntimeFunction(
    DWORD64 image_base,
    std::size_t image_size,
    const RUNTIME_FUNCTION &entry,
    RUNTIME_FUNCTION &primary) noexcept;

// Immutable canonical identity for the actual Wait function entry.
struct WaitIdentity {
  DWORD64 image_base = 0;
  std::size_t image_size = 0;
  RUNTIME_FUNCTION primary{};
  bool valid = false;
};
WaitIdentity wait_identity;

// Predicate: checks if a return PC belongs to the canonical Wait function.
bool IsInWaitFunction(std::uintptr_t site) noexcept {
  if (!wait_identity.valid) return false;
  const auto addr = static_cast<DWORD64>(site);
  // Reject if address is outside the known owned image extent.
  if (addr < wait_identity.image_base || addr - wait_identity.image_base >= wait_identity.image_size) return false;

  // Perform actual lookup for this specific return PC.
  DWORD64 local_image_base = 0;
  const auto *function = RtlLookupFunctionEntry(addr, &local_image_base, nullptr);
  if (function == nullptr || local_image_base != wait_identity.image_base) return false;

  // Normalize the found entry to its canonical primary triple.
  RUNTIME_FUNCTION normalized{};
  if (!NormalizeRuntimeFunction(local_image_base, wait_identity.image_size, *function, normalized)) return false;

  // Compare canonical primary triple against the stored Wait primary.
  // RUNTIME_FUNCTION has BeginAddress, EndAddress, UnwindData (no RelativeCodeAddress).
  return normalized.BeginAddress == wait_identity.primary.BeginAddress &&
         normalized.EndAddress == wait_identity.primary.EndAddress &&
         normalized.UnwindData == wait_identity.primary.UnwindData;
}
// Model08 supplied the header decoding/aligned chain traversal. Owner corrected
// image arithmetic, all-entry bounds, alignment and flag/span rejection.
static bool InImageRva(std::size_t image_size, std::size_t offset,
                       std::size_t length) noexcept {
  return offset <= image_size && length <= image_size - offset;
}

static DWORD ReadDword(std::uintptr_t address) noexcept {
  DWORD value;
  std::memcpy(&value, reinterpret_cast<const void *>(address), sizeof(value));
  return value;
}

bool NormalizeRuntimeFunction(DWORD64 image_base, std::size_t image_size,
                              const RUNTIME_FUNCTION &entry,
                              RUNTIME_FUNCTION &primary) noexcept {
  const auto img_base = static_cast<std::uintptr_t>(image_base);
  if (image_base == 0 || image_size == 0 ||
      image_size > std::numeric_limits<std::uintptr_t>::max() - img_base) {
    return false;
  }
  RUNTIME_FUNCTION current = entry;
  constexpr int MAX_CHAIN_DEPTH = 16;
  for (int depth = 0; depth < MAX_CHAIN_DEPTH; ++depth) {
    if (current.BeginAddress >= current.EndAddress ||
        current.EndAddress > image_size || current.UnwindData == 0 ||
        (current.UnwindData & 3U) != 0 ||
        !InImageRva(image_size, current.UnwindData, 4)) {
      return false;
    }
    const std::uintptr_t unwind_addr = img_base + current.UnwindData;
    const auto *header = reinterpret_cast<const BYTE *>(unwind_addr);
    const BYTE byte0 = header[0];
    const BYTE version = byte0 & 0x07;
    const BYTE flags = (byte0 >> 3) & 0x1F;
    const BYTE count_of_codes = header[2];
    if ((version != 1 && version != 2) || (flags & ~7U) != 0) {
      return false;
    }
    const std::size_t padded_slots =
        (static_cast<std::size_t>(count_of_codes) + 1) & ~std::size_t{1};
    const std::size_t chain_offset = 4 + 2 * padded_slots;
    if (!InImageRva(image_size, current.UnwindData, chain_offset)) {
      return false;
    }
    const bool has_chain = (flags & 0x04) != 0;
    if (!has_chain) {
      if ((flags & 0x03) != 0 &&
          !InImageRva(image_size, current.UnwindData, chain_offset + sizeof(DWORD))) {
        return false;
      }
      primary = current;
      return true;
    }
    if ((flags & 0x03) != 0 ||
        !InImageRva(image_size, current.UnwindData,
                    chain_offset + sizeof(RUNTIME_FUNCTION))) {
      return false;
    }
    const std::uintptr_t chain_addr = unwind_addr + chain_offset;
    current.BeginAddress = ReadDword(chain_addr);
    current.EndAddress = ReadDword(chain_addr + 4);
    current.UnwindData = ReadDword(chain_addr + 8);
  }
  // Cyclic or excessively deep chains never gain function ownership.
  return false;
}

void RecordSample(std::array<Sample, MAX_SAMPLES> &samples, std::size_t index,
                  std::uintptr_t site, DWORD thread, std::uint64_t tick) noexcept {
  if (index >= MAX_SAMPLES) return;
  auto &sample = samples[index];
  sample.site.store(site, std::memory_order_relaxed);
  sample.thread.store(thread, std::memory_order_relaxed);
  sample.tick.store(tick, std::memory_order_relaxed);
  sample.ready.store(true, std::memory_order_release);
}

TickFunction ResolveRealTick() noexcept {
  auto function = real_tick.load(std::memory_order_acquire);
  if (function == nullptr) {
    const auto address = GetProcAddress(GetModuleHandleW(L"kernel32.dll"), "GetTickCount64");
    static_assert(sizeof(function) == sizeof(address));
    std::memcpy(&function, &address, sizeof(function));
    if (function == nullptr) std::abort();
    real_tick.store(function, std::memory_order_release);
  }
  return function;
}
__declspec(noinline) ULONGLONG WINAPI ObservedTick() noexcept {
  // Call the real WinAPI exactly once and forward its value without adjustment.
  const auto value = ResolveRealTick()();
  const auto site = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  total_hook_calls.fetch_add(1, std::memory_order_relaxed);
  if (armed.load(std::memory_order_acquire)) {
    const auto sample_thread = GetCurrentThreadId();
    RecordSample(armed_samples, armed_count.fetch_add(1, std::memory_order_relaxed), site, sample_thread, value);
    if (sample_thread == expected_worker_id.load(std::memory_order_acquire))
      RecordSample(worker_samples, worker_count.fetch_add(1, std::memory_order_relaxed), site, sample_thread, value);
  }
  if (armed.load(std::memory_order_acquire) && IsInWaitFunction(site)) {
    const auto thread = GetCurrentThreadId();
    DWORD empty = 0;
    (void)worker_id.compare_exchange_strong(empty, thread);
    if (worker_id.load() == thread) {
      if (first_site.load() == 0) first_site.store(site);
      if (first_site.load() == site) {
        const auto previous = entry_count.load();
        if (previous == 0) first_tick.store(value);
        if (previous == 1) second_tick.store(value);
        entry_count.store(previous + 1, std::memory_order_release);
      }
    }
  }
  return value;
}
void DumpDiagnostics(DWORD64 wait_addr, DWORD64 begin, DWORD64 end, DWORD expected_id) { std::cout << "DIAG wait_addr=" << wait_addr << " begin=" << begin << " end=" << end << " expected_worker=" << expected_id << " observed_worker=" << worker_id.load() << " total_hooks=" << total_hook_calls.load() << " armed_samples=" << armed_count.load() << " worker_samples=" << worker_count.load() << " qualified=" << entry_count.load() << "\n"; for (std::size_t i=0; i<MAX_SAMPLES; ++i) { if (armed_samples[i].ready.load()) std::cout << "A" << i << " t=" << armed_samples[i].thread.load() << " s=" << armed_samples[i].site.load() << " v=" << armed_samples[i].tick.load() << " "; } std::cout << "\n"; for (std::size_t i=0; i<MAX_SAMPLES; ++i) { if (worker_samples[i].ready.load()) std::cout << "W" << i << " t=" << worker_samples[i].thread.load() << " s=" << worker_samples[i].site.load() << " v=" << worker_samples[i].tick.load() << " "; } std::cout << "\n" << std::flush; }
} // namespace observation

// Resolve only this isolated software EXE's dllimport data references. The
// production object files and Kernel32 exports are not edited.
extern "C" {
observation::TickFunction __imp_GetTickCount64 = &observation::ObservedTick;
}

namespace {
struct Barrier {
  std::atomic<bool> entered{false}, release{false}, hard_expired{false};
  std::atomic<std::uint64_t> entered_tick{0};
  std::atomic<unsigned> calls{0};
  static inline Barrier *active = nullptr;
  static void *Read(void *output, void *actor, void *title) {
    auto &barrier = *active;
    if (barrier.calls.fetch_add(1) == 0) {
      const auto began = observation::ResolveRealTick()();
      barrier.entered_tick.store(began);
      barrier.entered.store(true, std::memory_order_release);
      while (!barrier.release.load(std::memory_order_acquire)) {
        if (observation::ResolveRealTick()() - began >= 40'000) {
          barrier.hard_expired.store(true);
          break;
        }
        Sleep(1);
      }
    }
    return Fixture::ReadClaim(output, actor, title);
  }
};
struct ControlObservation {
  bool entered = false;
  bool repeated_entry = false;
  bool executing_context_retained = false;
  std::uint64_t release_tick = 0;
  std::uint64_t entries_before_release = 0;
  std::uint64_t completed_while_held = 0;
  std::uint64_t started_while_held = 0;
  std::uint64_t executed_while_held = 0;
};
}

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[2]) == "--internal-wait-only",
        "usage: internal-wait-test OUTPUT_ROOT --internal-wait-only");
    const auto directory = std::filesystem::path(argv[1]) / ("run-" + std::to_string(GetCurrentProcessId()) + "-" + std::to_string(GetTickCount64()));
    Check(!std::filesystem::exists(directory) && std::filesystem::create_directories(directory), "new executing output required");
    const auto real_tick = observation::ResolveRealTick();
    DWORD64 image_base = 0;
    const auto wait_address = reinterpret_cast<DWORD64>(&api::WaitForMainThreadQueryV1);
    const auto *function = RtlLookupFunctionEntry(wait_address, &image_base, nullptr);
    Check(function != nullptr, "actual Wait x64 runtime function entry unavailable; no branch credit");
    const auto begin = image_base + function->BeginAddress;
    const auto end = image_base + function->EndAddress;
    Check(begin <= wait_address && wait_address < end, "Wait symbol not in runtime function entry");
    observation::wait_begin.store(begin);
    observation::wait_end.store(end);

    // Read only this already loaded owned image's small headers for its extent.
    const auto *dos_header = reinterpret_cast<const IMAGE_DOS_HEADER *>(image_base);
    Check(dos_header->e_magic == IMAGE_DOS_SIGNATURE && dos_header->e_lfanew > 0,
        "owned image DOS header unavailable");
    const auto *nt_headers = reinterpret_cast<const IMAGE_NT_HEADERS64 *>(
        image_base + static_cast<DWORD>(dos_header->e_lfanew));
    Check(nt_headers->Signature == IMAGE_NT_SIGNATURE &&
        nt_headers->OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR64_MAGIC,
        "owned image NT headers unavailable");
    const auto image_size = static_cast<std::size_t>(nt_headers->OptionalHeader.SizeOfImage);
    RUNTIME_FUNCTION normalized_primary{};
    Check(observation::NormalizeRuntimeFunction(image_base, image_size, *function, normalized_primary),
        "Wait runtime function normalization failed");
    observation::wait_identity.image_base = image_base;
    observation::wait_identity.image_size = image_size;
    observation::wait_identity.primary = normalized_primary;
    observation::wait_identity.valid = true;

    Check(__imp_GetTickCount64 == &observation::ObservedTick && real_tick != &observation::ObservedTick,
        "isolated import observer did not preserve real timer delegate");

    Lifecycle life;
    Barrier barrier;
    Barrier::active = &barrier;
    life.fixture.bindings.read_character_claim = &Barrier::Read;
    observation::armed.store(true, std::memory_order_release);
    PendingRead first(life, kStrongExplicit);
    const auto real_worker_id = GetThreadId(first.worker.native_handle());
    observation::expected_worker_id.store(real_worker_id, std::memory_order_release);
    const auto context = first.queued_envelope;
    Check(first.ticket.sequence == 1, "first request sequence changed");
    ControlObservation control;
    std::thread controller([&] {
      const auto start = real_tick();
      while (!barrier.entered.load(std::memory_order_acquire) && real_tick() - start < 2'000) Sleep(1);
      control.entered = barrier.entered.load(std::memory_order_acquire);
      if (control.entered) {
        std::cout << "BARRIER entered: real WorkerAdapter claims getter; waiting for repeated Wait start site, hold>=32s\n" << std::flush;
        const auto deadline = barrier.entered_tick.load() + 38'000;
        std::uint64_t last_progress = real_tick();
        while (real_tick() < deadline) {
          const auto entries = observation::entry_count.load(std::memory_order_acquire);
          const auto initial = observation::first_tick.load();
          if (entries >= 2 && initial != 0 && real_tick() - initial >= 32'000) {
            const auto diag = api::ReadMainThreadQueryMailboxDiagnosticsV1(life.mailbox);
            control.entries_before_release = entries;
            control.repeated_entry = true;
            control.completed_while_held = diag.completed_sequence;
            control.started_while_held = diag.executor_started_requests;
            control.executed_while_held = diag.executed_requests;
            control.executing_context_retained = diag.state == api::MainThreadQueryMailboxStateV1::executing &&
                diag.published_sequence == first.ticket.sequence && diag.completed_sequence == 0 &&
                diag.executor_started_requests == 1 && diag.executed_requests == 0 && diag.failure_flags == 0 &&
                life.mailbox.executor_context == reinterpret_cast<void *>(context) &&
                life.mailbox.executor.load() == &build::ExecuteSemanticAdapter12002;
            break;
          }
          if (real_tick() - last_progress >= 10'000) {
            std::cout << "BARRIER progress elapsed_ms=" << real_tick() - barrier.entered_tick.load()
                      << " observed_Wait_entries=" << entries << '\n' << std::flush;
            last_progress = real_tick();
          }
          Sleep(5);
        }
      }
      control.release_tick = real_tick();
      barrier.release.store(true, std::memory_order_release);
    });
    Pump(life.mailbox);
    controller.join();
    first.Join();
    observation::armed.store(false, std::memory_order_release);
    observation::DumpDiagnostics(wait_address, begin, end, real_worker_id);
    Check(control.entered && control.repeated_entry && control.executing_context_retained && !barrier.hard_expired.load(),
        "no repeated real Wait start site with retained executing context; no internal timeout branch credit");
    const auto first_tick = observation::first_tick.load();
    const auto second_tick = observation::second_tick.load();
    Check(observation::worker_id.load() == real_worker_id && second_tick >= first_tick + 30'000 &&
        control.release_tick >= first_tick + 32'000, "worker thread or real30s entry timing not proven");
    Check(first.result == Result::available && first.output.available && first.output.title_ids == first.ids &&
        life.native.claim_calls == 1 && life.fixture.getter_calls == 2 && barrier.calls.load() == 2,
        "held original request did not complete through actual claims reader");
    CheckIdle(life, 1, 1);
    SaveBody(first, api::ReadMainThreadQueryMailboxDiagnosticsV1(life.mailbox), directory, "executing-timeout-completed");
    life.fixture.bindings.read_character_claim = &Fixture::ReadClaim;
    PendingRead fresh(life, kWeakImplicit);
    Check(fresh.ticket.sequence == 2 && fresh.ids != first.ids, "fresh query identity");
    Pump(life.mailbox);
    fresh.Join();
    Check(fresh.result == Result::available && fresh.output.available && fresh.output.title_ids == fresh.ids &&
        life.native.claim_calls == 2 && life.fixture.getter_calls == 4 && life.fixture.destructor_calls == 4,
        "same-adapter fresh query after executing timeout failed");
    CheckIdle(life, 2, 2);
    SaveBody(fresh, api::ReadMainThreadQueryMailboxDiagnosticsV1(life.mailbox), directory, "executing-timeout-fresh");
    life.Close();
    std::cout << "{\"case\":\"actual_internal_executing_timeout\",\"pass\":true,\"real_worker_thread_id\":" << real_worker_id
        << ",\"observed_worker_thread_id\":" << observation::worker_id.load() << ",\"wait_symbol\":\"" << wait_address
        << "\",\"wait_runtime_begin\":\"" << begin << "\",\"wait_runtime_end\":\"" << end
        << "\",\"observed_start_return_site\":\"" << observation::first_site.load()
        << "\",\"same_start_site_entries_before_release\":" << control.entries_before_release
        << ",\"first_entry_tick\":" << first_tick << ",\"second_entry_tick\":" << second_tick
        << ",\"entry_delta_ms\":" << second_tick - first_tick << ",\"hold_from_first_entry_ms\":" << control.release_tick - first_tick
        << ",\"completed_while_held\":" << control.completed_while_held << ",\"started_while_held\":" << control.started_while_held
        << ",\"executed_while_held\":" << control.executed_while_held
        << ",\"context_retained_while_executing\":true,\"same_owner_adapter_fresh_sequence\":2,\"final_idle_context_null\":true"
        << ",\"timer_values_forwarded_unmodified\":true,\"external_wait_or_cancel_calls\":0,\"checks\":" << checks << "}\n";
    std::cout << "PASS one new actual internal30s executing-timeout scenario; no old8/45 runs, no Game/full Bridge; observed repeated real Wait start site\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL: " << error.what() << '\n'; return 1; }
}
