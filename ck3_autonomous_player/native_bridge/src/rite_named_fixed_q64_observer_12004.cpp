#include "xar_bridge/rite_named_fixed_q64_observer_12004.hpp"
#include "xar_bridge/rite_dynamic_call_journal_12004.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>
#include <type_traits>

namespace xar::ck3_12004 {
namespace {

using State = RiteNamedFixedQ64Observer12004State;
using Relay = std::array<std::uint8_t, kRiteNamedFixedQ64RelayCapacity12004>;
std::atomic<State *> g_active{nullptr};
static_assert(sizeof(void *) == 8);
static_assert(std::is_standard_layout_v<RiteDynamicPrecallRegisters12004>);
static_assert(sizeof(RiteDynamicPrecallRegisters12004) == 64);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, helper_rbp) == 0);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, expression_receiver_rcx) == 8);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, vptr_rax) == 16);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, target_r10) == 24);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, definition_rsi) == 32);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, native_context_r12) == 40);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, native_r9_r15) == 48);
static_assert(offsetof(RiteDynamicPrecallRegisters12004, helper_out_rdi) == 56);
static_assert(std::is_same_v<RiteNamedFixedQ64PreCapture12004, RiteDynamicPrecallCapture12004>);
static_assert(std::is_same_v<RiteNamedFixedQ64PostCapture12004, RiteDynamicPostcallCapture12004>);

// Held complete393B source, ABI pin3803b0ef...bb06ce36. These are two ordinary
// MOV pairs. Neither the original CALL375438F nor its returnPC is relocated.
constexpr std::array<std::uint8_t, 9> kPre{
    0x48, 0x8B, 0x45, 0x7F, 0x48, 0x89, 0x44, 0x24, 0x20};
constexpr std::array<std::uint8_t, 13> kUntouchedCall{
    0x4D, 0x8B, 0xCF, 0x4D, 0x8B, 0xC4, 0x48, 0x8D, 0x55, 0x5F,
    0x41, 0xFF, 0xD2};
constexpr std::array<std::uint8_t, 7> kPost{
    0x48, 0x8B, 0x45, 0x5F, 0x48, 0x89, 0x07};
// Original JMP3754399 followed by separate literal entry375439B.
constexpr std::array<std::uint8_t, 6> kUntouchedLiteralBoundary{
    0xEB, 0x0D, 0x80, 0x7E, 0x7B, 0x00};

void Fail(State &state, RiteNamedFixedQ64ObserverFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(flag), std::memory_order_acq_rel);
}

bool Add(std::uintptr_t base, std::uintptr_t offset, std::uintptr_t &out) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  out = base + offset;
  return true;
}

bool Equal(std::uintptr_t address, const std::uint8_t *bytes, std::size_t size) noexcept {
  if (address == 0 || bytes == nullptr || size == 0 ||
      size - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), bytes, size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool CopyTo(std::uintptr_t address, const std::uint8_t *bytes, std::size_t size) noexcept {
  if (address == 0 || bytes == nullptr || size == 0 ||
      size - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), bytes, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Executable(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ || protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}

bool Flush(const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool Relative32(std::uintptr_t target, std::uintptr_t next_pc, std::int32_t &relative) noexcept {
  if (target >= next_pc) {
    const auto distance = target - next_pc;
    if (distance > 0x7FFFFFFFu) return false;
    relative = static_cast<std::int32_t>(distance);
  } else {
    const auto distance = next_pc - target;
    if (distance > 0x80000000u) return false;
    relative = distance == 0x80000000u ? (std::numeric_limits<std::int32_t>::min)()
                                    : -static_cast<std::int32_t>(distance);
  }
  return true;
}

bool ReachBoth(std::uintptr_t backing, std::uintptr_t pre_next, std::uintptr_t post_next) noexcept {
  std::uintptr_t post_relay = 0;
  std::int32_t relative = 0;
  return Add(backing, kRiteNamedFixedQ64RelayCapacity12004, post_relay) &&
      Relative32(backing, pre_next, relative) && Relative32(post_relay, post_next, relative);
}

// Existing fixed-near plumbing, limited to the pre E9's signed-rel32 window.
// Both entry displacements are checked; the two relays share one owned block.
void *AllocateNearRelays(std::uintptr_t pre_next, std::uintptr_t post_next) noexcept {
  SYSTEM_INFO info{};
  GetSystemInfo(&info);
  const auto granularity = static_cast<std::uintptr_t>(info.dwAllocationGranularity);
  if (granularity == 0) return nullptr;
  const auto minimum = reinterpret_cast<std::uintptr_t>(info.lpMinimumApplicationAddress);
  const auto maximum = reinterpret_cast<std::uintptr_t>(info.lpMaximumApplicationAddress);
  auto low = pre_next > 0x80000000u ? pre_next - 0x80000000u : minimum;
  auto high = pre_next <= (std::numeric_limits<std::uintptr_t>::max)() - 0x7FFFFFFFu
      ? pre_next + 0x7FFFFFFFu : maximum;
  if (low < minimum) low = minimum;
  if (high > maximum) high = maximum;
  for (auto cursor = low; cursor <= high;) {
    MEMORY_BASIC_INFORMATION region{};
    if (VirtualQuery(reinterpret_cast<const void *>(cursor), &region, sizeof(region)) == 0) break;
    const auto begin = reinterpret_cast<std::uintptr_t>(region.BaseAddress);
    if (region.RegionSize == 0 ||
        region.RegionSize > (std::numeric_limits<std::uintptr_t>::max)() - begin) break;
    const auto end = begin + region.RegionSize;
    if (end <= cursor) break;
    if (region.State == MEM_FREE) {
      auto candidate = cursor > begin ? cursor : begin;
      const auto remainder = candidate % granularity;
      if (remainder != 0) {
        const auto adjustment = granularity - remainder;
        if (candidate > (std::numeric_limits<std::uintptr_t>::max)() - adjustment) break;
        candidate += adjustment;
      }
      if (candidate <= high && candidate < end &&
          kRiteNamedFixedQ64BackingBytes12004 <= end - candidate &&
          ReachBoth(candidate, pre_next, post_next)) {
        auto *allocated = VirtualAlloc(reinterpret_cast<void *>(candidate),
            kRiteNamedFixedQ64BackingBytes12004, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (allocated != nullptr) {
          if (ReachBoth(reinterpret_cast<std::uintptr_t>(allocated), pre_next, post_next))
            return allocated;
          (void)VirtualFree(allocated, 0, MEM_RELEASE);
        }
      }
    }
    cursor = end;
  }
  return nullptr;
}

struct Emitter {
  Relay code{};
  std::size_t cursor = 0;
  bool valid = true;
  Emitter() noexcept { code.fill(0x90); }
  void Bytes(const std::uint8_t *bytes, std::size_t size) noexcept {
    if (!valid || size > code.size() - cursor) { valid = false; return; }
    std::memcpy(code.data() + cursor, bytes, size);
    cursor += size;
  }
  void Emit(std::initializer_list<std::uint8_t> bytes) noexcept { Bytes(bytes.begin(), bytes.size()); }
  void U32(std::uint32_t value) noexcept {
    Bytes(reinterpret_cast<const std::uint8_t *>(&value), sizeof(value));
  }
  void U64(std::uintptr_t value) noexcept {
    const auto bits = static_cast<std::uint64_t>(value);
    Bytes(reinterpret_cast<const std::uint8_t *>(&bits), sizeof(bits));
  }
};

// Original native RSP is16-aligned at both cuts. Sixteen pushes save all15
// GPRs plus RFLAGS (=128B). The368B frame keeps16 alignment, with32B shadow,
// XMM0..15 at20..11F, eight copied register words at120..15F, and MXCSR160.
// Saved register offsets below include that frame. RSP returns exactly to its
// original native address before either displaced MOV pair is replayed.
constexpr std::uint32_t kSavedR15 = 0x170;
constexpr std::uint32_t kSavedR12 = 0x188;
constexpr std::uint32_t kSavedR10 = 0x198;
constexpr std::uint32_t kSavedRdi = 0x1B0;
constexpr std::uint32_t kSavedRsi = 0x1B8;
constexpr std::uint32_t kSavedRbp = 0x1C0;
constexpr std::uint32_t kSavedRcx = 0x1D8;
constexpr std::uint32_t kSavedRax = 0x1E0;

void Xmm(Emitter &out, bool restore, std::uint8_t reg) noexcept {
  out.Emit({0xF3});
  if (reg >= 8) out.Emit({0x44}); // REX.R selects XMM8..15.
  out.Emit({0x0F, static_cast<std::uint8_t>(restore ? 0x6F : 0x7F),
            static_cast<std::uint8_t>(0x84 + 8 * (reg & 7)), 0x24});
  out.U32(0x20u + 0x10u * reg); // disp32 prevents sign extension above7F.
}

void Preserve(Emitter &out) noexcept {
  out.Emit({0x9C, 0x50, 0x51, 0x52, 0x53, 0x55, 0x56, 0x57,
            0x41, 0x50, 0x41, 0x51, 0x41, 0x52, 0x41, 0x53,
            0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57});
  out.Emit({0x48, 0x81, 0xEC}); out.U32(0x170);
  for (std::uint8_t reg = 0; reg != 16; ++reg) Xmm(out, false, reg);
  out.Emit({0x0F, 0xAE, 0x9C, 0x24}); out.U32(0x160); // STMXCSR.
  out.Emit({0xFC}); // ABI DF=0 for callback; original flags are restored.
}

void Restore(Emitter &out) noexcept {
  out.Emit({0x0F, 0xAE, 0x94, 0x24}); out.U32(0x160); // LDMXCSR.
  for (std::uint8_t reg = 0; reg != 16; ++reg) Xmm(out, true, reg);
  out.Emit({0x48, 0x81, 0xC4}); out.U32(0x170);
  out.Emit({0x41, 0x5F, 0x41, 0x5E, 0x41, 0x5D, 0x41, 0x5C,
            0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59, 0x41, 0x58,
            0x5F, 0x5E, 0x5D, 0x5B, 0x5A, 0x59, 0x58, 0x9D});
}

void CopySavedWord(Emitter &out, std::uint32_t saved_offset, std::uint32_t field_offset) noexcept {
  out.Emit({0x48, 0x8B, 0x84, 0x24}); out.U32(saved_offset);
  out.Emit({0x48, 0x89, 0x84, 0x24}); out.U32(0x120 + field_offset);
}

extern "C" void RiteNamedFixedQ64PreThunk12004(
    void *context, const RiteDynamicPrecallRegisters12004 *registers) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr && registers != nullptr && state->environment.pre_capture != nullptr)
    state->environment.pre_capture(context, *registers);
}

extern "C" void RiteNamedFixedQ64PostThunk12004(
    void *context, std::uintptr_t helper_rbp, std::uint64_t raw_returned_rax) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr && state->environment.post_capture != nullptr)
    state->environment.post_capture(context, helper_rbp, raw_returned_rax);
}

bool PinAddress(std::uintptr_t address) noexcept {
  HMODULE module = nullptr;
  return address != 0 && GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
      GET_MODULE_HANDLE_EX_FLAG_PIN, reinterpret_cast<LPCWSTR>(address), &module) != FALSE;
}

bool PinCallbacks(State &state) noexcept {
  // Linked runtime/thunks and journal are retained for the process lifetime.
  // Callback modules are pinned separately rather than assuming their image.
  const bool pinned = PinAddress(reinterpret_cast<std::uintptr_t>(&RiteNamedFixedQ64PreThunk12004)) &&
      PinAddress(reinterpret_cast<std::uintptr_t>(state.environment.pre_capture)) &&
      PinAddress(reinterpret_cast<std::uintptr_t>(state.environment.post_capture));
  state.callback_modules_pinned = pinned;
  if (!pinned) Fail(state, rite_q64_failure_module_pin);
  return pinned;
}

std::size_t BuildRelay(const State &state, bool post, Relay &code) noexcept {
  Emitter out{};
  Preserve(out);
  if (!post) {
    constexpr std::array<std::uint32_t, 8> offsets{
        kSavedRbp, kSavedRcx, kSavedRax, kSavedR10,
        kSavedRsi, kSavedR12, kSavedR15, kSavedRdi};
    for (std::size_t field = 0; field != offsets.size(); ++field)
      CopySavedWord(out, offsets[field], static_cast<std::uint32_t>(8 * field));
    out.Emit({0x48, 0x8D, 0x94, 0x24}); out.U32(0x120); // RDX=&copied registers.
  } else {
    out.Emit({0x48, 0x8B, 0x94, 0x24}); out.U32(kSavedRbp); // RDX=original RBP.
    out.Emit({0x4C, 0x8B, 0x84, 0x24}); out.U32(kSavedRax); // R8=raw returned RAX.
  }
  out.Emit({0x48, 0xB9}); out.U64(reinterpret_cast<std::uintptr_t>(state.environment.capture_context));
  out.Emit({0x48, 0xB8});
  out.U64(post ? reinterpret_cast<std::uintptr_t>(&RiteNamedFixedQ64PostThunk12004)
               : reinterpret_cast<std::uintptr_t>(&RiteNamedFixedQ64PreThunk12004));
  out.Emit({0xFF, 0xD0}); // Observer callback only, not the native virtual CALL.
  Restore(out);
  if (post) out.Bytes(kPost.data(), kPost.size());
  else out.Bytes(kPre.data(), kPre.size());
  out.Emit({0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  out.U64(post ? state.post_resume : state.pre_resume);
  if (!out.valid) return 0;
  code = out.code;
  return out.cursor;
}

template <std::size_t Size>
bool MakeNearPatch(std::uintptr_t target, std::uintptr_t relay,
                   std::array<std::uint8_t, Size> &patch) noexcept {
  static_assert(Size >= 5);
  std::uintptr_t next = 0;
  std::int32_t relative = 0;
  if (!Add(target, 5, next) || !Relative32(relay, next, relative)) return false;
  patch.fill(0x90);
  patch[0] = 0xE9;
  std::memcpy(patch.data() + 1, &relative, sizeof(relative));
  return true;
}

enum class WriteResult { success, expected_preserved, restore_unproven };

WriteResult WriteWindow(State &state, std::uintptr_t address, const std::uint8_t *expected,
    const std::uint8_t *desired, std::size_t size, std::uint32_t &original_protection) noexcept {
  if (!Equal(address, expected, size)) {
    Fail(state, rite_q64_failure_target_identity);
    return WriteResult::restore_unproven;
  }
  auto *target = reinterpret_cast<void *>(address);
  DWORD previous = 0;
  if (VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &previous) == FALSE) {
    Fail(state, rite_q64_failure_target_protection);
    return WriteResult::expected_preserved;
  }
  if (original_protection == 0) original_protection = previous;
  if (!Executable(previous) || !Executable(original_protection)) {
    DWORD ignored = 0;
    const bool restored = VirtualProtect(target, size, previous, &ignored) != FALSE;
    Fail(state, rite_q64_failure_target_protection);
    return restored ? WriteResult::expected_preserved : WriteResult::restore_unproven;
  }
  const bool wrote = CopyTo(address, desired, size);
  const bool identity = wrote && Equal(address, desired, size);
  const bool flushed = identity && Flush(target, size);
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(target, size, original_protection, &ignored) != FALSE;
  if (identity && flushed && protected_again) return WriteResult::success;
  if (!flushed) Fail(state, rite_q64_failure_flush);
  if (!protected_again) Fail(state, rite_q64_failure_target_protection);
  DWORD rollback_previous = 0;
  const bool writable = VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &rollback_previous) != FALSE;
  const bool restored = writable && CopyTo(address, expected, size) && Equal(address, expected, size);
  const bool restore_flushed = restored && Flush(target, size);
  const bool restore_protected = writable &&
      VirtualProtect(target, size, original_protection, &ignored) != FALSE;
  if (restored && restore_flushed && restore_protected) return WriteResult::expected_preserved;
  Fail(state, rite_q64_failure_restore);
  return WriteResult::restore_unproven;
}

template <std::size_t Size>
bool RestoreWindow(State &state, std::uint8_t bit, std::uintptr_t target,
    const std::array<std::uint8_t, Size> &original,
    const std::array<std::uint8_t, Size> &installed, std::uint32_t &protection) noexcept {
  const bool owned = (state.owned_patch_mask.load(std::memory_order_acquire) & bit) != 0;
  if (!owned) return Equal(target, original.data(), Size);
  bool restored = false;
  if (Equal(target, original.data(), Size)) {
    DWORD ignored = 0;
    restored = Flush(reinterpret_cast<const void *>(target), Size) &&
        (protection == 0 || VirtualProtect(reinterpret_cast<void *>(target), Size,
                                          protection, &ignored) != FALSE);
  } else if (Equal(target, installed.data(), Size)) {
    restored = WriteWindow(state, target, installed.data(), original.data(), Size, protection)
        == WriteResult::success;
  }
  if (restored) {
    state.owned_patch_mask.fetch_and(static_cast<std::uint8_t>(~bit), std::memory_order_acq_rel);
    return true;
  }
  Fail(state, rite_q64_failure_restore);
  return false;
}

bool ReleaseBacking(State &state) noexcept {
  if (state.owned_patch_mask.load(std::memory_order_acquire) != 0) return false;
  if (state.backing != nullptr && VirtualFree(state.backing, 0, MEM_RELEASE) == FALSE) {
    Fail(state, rite_q64_failure_restore);
    return false;
  }
  state.backing = nullptr;
  state.backing_bytes = 0;
  state.pre_relay_bytes = 0;
  state.post_relay_bytes = 0;
  state.pre_target = state.pre_resume = state.post_target = state.post_resume = 0;
  state.pre_original_protection = state.post_original_protection = 0;
  state.environment = {};
  state.installed.store(false, std::memory_order_release);
  State *expected = &state;
  (void)g_active.compare_exchange_strong(expected, nullptr, std::memory_order_acq_rel);
  return true;
}

bool RestoreBothAndRelease(State &state) noexcept {
  // Evaluate both restoration attempts independently. On partial failure keep
  // the allocation, state and pinned callback code; no possibly live relay is
  // freed. Retry accepts an already restored window without rewriting it.
  const bool pre = RestoreWindow(state, 1, state.pre_target,
      state.original_pre, state.installed_pre, state.pre_original_protection);
  const bool post = RestoreWindow(state, 2, state.post_target,
      state.original_post, state.installed_post, state.post_original_protection);
  const auto mask = state.owned_patch_mask.load(std::memory_order_acquire);
  state.installed.store(mask != 0, std::memory_order_release);
  if (!pre || !post || mask != 0) return false;
  return ReleaseBacking(state);
}

bool PrepareRelays(State &state) noexcept {
  std::uintptr_t pre_next = 0, post_next = 0, post_relay = 0;
  if (!Add(state.pre_target, 5, pre_next) || !Add(state.post_target, 5, post_next)) return false;
  state.backing = AllocateNearRelays(pre_next, post_next);
  if (state.backing == nullptr) { Fail(state, rite_q64_failure_near_allocation); return false; }
  state.backing_bytes = kRiteNamedFixedQ64BackingBytes12004;
  const auto backing = reinterpret_cast<std::uintptr_t>(state.backing);
  if (!Add(backing, kRiteNamedFixedQ64RelayCapacity12004, post_relay)) return false;
  Relay pre{}, post{};
  state.pre_relay_bytes = BuildRelay(state, false, pre);
  state.post_relay_bytes = BuildRelay(state, true, post);
  if (state.pre_relay_bytes == 0 || state.post_relay_bytes == 0 ||
      !CopyTo(backing, pre.data(), pre.size()) ||
      !CopyTo(post_relay, post.data(), post.size()) ||
      !Equal(backing, pre.data(), pre.size()) || !Equal(post_relay, post.data(), post.size())) {
    Fail(state, rite_q64_failure_relay);
    return false;
  }
  DWORD previous = 0;
  if (VirtualProtect(state.backing, state.backing_bytes, PAGE_EXECUTE_READ, &previous) == FALSE ||
      previous != PAGE_READWRITE || !Flush(state.backing, state.backing_bytes)) {
    Fail(state, rite_q64_failure_relay);
    return false;
  }
  if (!MakeNearPatch(state.pre_target, backing, state.installed_pre) ||
      !MakeNearPatch(state.post_target, post_relay, state.installed_post)) {
    Fail(state, rite_q64_failure_near_allocation);
    return false;
  }
  return true;
}

} // namespace

bool InstallRiteNamedFixedQ64Observer12004(
    State &state, const RiteNamedFixedQ64Observer12004Environment &environment) noexcept {
  if (state.installed.load(std::memory_order_acquire) ||
      state.owned_patch_mask.load(std::memory_order_acquire) != 0 || state.backing != nullptr) {
    Fail(state, rite_q64_failure_already_owned);
    return false;
  }
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (!environment.exact_12004_build_admitted || environment.module_base == 0) {
    Fail(state, rite_q64_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, rite_q64_failure_suspension);
    return false;
  }
  if (environment.pre_capture == nullptr || environment.post_capture == nullptr) {
    Fail(state, rite_q64_failure_callbacks);
    return false;
  }
  std::uintptr_t pre_target = 0, pre_resume = 0, post_target = 0, post_resume = 0;
  if (!Add(environment.module_base, kRiteNamedFixedQ64PrePatchRva12004, pre_target) ||
      !Add(environment.module_base, kRiteNamedFixedQ64PreResumeRva12004, pre_resume) ||
      !Add(environment.module_base, kRiteNamedFixedQ64PostPatchRva12004, post_target) ||
      !Add(environment.module_base, kRiteNamedFixedQ64PostResumeRva12004, post_resume) ||
      !Equal(pre_target, kPre.data(), kPre.size()) ||
      !Equal(pre_resume, kUntouchedCall.data(), kUntouchedCall.size()) ||
      !Equal(post_target, kPost.data(), kPost.size()) ||
      !Equal(post_resume, kUntouchedLiteralBoundary.data(), kUntouchedLiteralBoundary.size())) {
    Fail(state, rite_q64_failure_anchor);
    return false;
  }
  State *expected = nullptr;
  if (!g_active.compare_exchange_strong(expected, &state, std::memory_order_acq_rel)) {
    Fail(state, rite_q64_failure_already_owned);
    return false;
  }
  state.environment = environment;
  state.pre_target = pre_target; state.pre_resume = pre_resume;
  state.post_target = post_target; state.post_resume = post_resume;
  state.original_pre = kPre; state.original_post = kPost;
  if (!PinCallbacks(state) || !PrepareRelays(state)) {
    // No target write has occurred. Preserve failed free ownership if needed.
    (void)ReleaseBacking(state);
    return false;
  }
  const auto pre = WriteWindow(state, state.pre_target, state.original_pre.data(),
      state.installed_pre.data(), state.original_pre.size(), state.pre_original_protection);
  if (pre != WriteResult::expected_preserved)
    state.owned_patch_mask.fetch_or(1, std::memory_order_acq_rel);
  if (pre != WriteResult::success) {
    state.installed.store(state.owned_patch_mask.load(std::memory_order_acquire) != 0,
                          std::memory_order_release);
    (void)RestoreBothAndRelease(state);
    return false;
  }
  const auto post = WriteWindow(state, state.post_target, state.original_post.data(),
      state.installed_post.data(), state.original_post.size(), state.post_original_protection);
  if (post != WriteResult::expected_preserved)
    state.owned_patch_mask.fetch_or(2, std::memory_order_acq_rel);
  if (post != WriteResult::success) {
    state.installed.store(true, std::memory_order_release);
    (void)RestoreBothAndRelease(state);
    return false;
  }
  state.installed.store(true, std::memory_order_release);
  return true;
}

bool UninstallRiteNamedFixedQ64Observer12004(
    State &state, bool primary_thread_suspended_proven,
    bool observer_execution_quiescent_proven) noexcept {
  if (!primary_thread_suspended_proven) { Fail(state, rite_q64_failure_suspension); return false; }
  if (!observer_execution_quiescent_proven) { Fail(state, rite_q64_failure_quiescence); return false; }
  if (g_active.load(std::memory_order_acquire) != &state) {
    Fail(state, rite_q64_failure_already_owned);
    return false;
  }
  return RestoreBothAndRelease(state);
}

RiteNamedFixedQ64Observer12004Diagnostics ReadRiteNamedFixedQ64Observer12004Diagnostics(
    const State &state) noexcept {
  RiteNamedFixedQ64Observer12004Diagnostics out{};
  out.installed = state.installed.load(std::memory_order_acquire);
  out.owned_patch_mask = state.owned_patch_mask.load(std::memory_order_acquire);
  out.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  out.backing_retained = state.backing != nullptr;
  out.callback_modules_pinned = state.callback_modules_pinned;
  return out;
}

} // namespace xar::ck3_12004
