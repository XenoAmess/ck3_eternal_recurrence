// Private navigation namespace only. Startup wrapper/linkage is owned by parent.
// Actual 1.20.0.4 only; fixed four CALL sites, no caller-supplied RVA or policy.
// Include after Windows/array/cstdint/cstring/initializer_list/limits/string_view.
// Owner-thread receipt validation and native coordinate derivation stay in parent.
bool PresentationTooltipPositionOverride12004(void *gui, std::uint64_t &packed) noexcept;

static_assert(sizeof(void *) == 8, "Exact4 tooltip position relay requires x64");
constexpr std::string_view kPtpExeSha12004 =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
constexpr std::uintptr_t kPtpDispatcherRva12004 = 0x3AB26B0;
constexpr std::array<std::uintptr_t, 4> kPtpCalls12004{
    0x3AB2799, 0x3AB27A8, 0x3AB27B7, 0x3AB27C6};
constexpr std::array<std::uintptr_t, 4> kPtpCallees12004{
    0x3BFD8F0, 0x3BFDE80, 0x3BFE440, 0x3BFE990};
constexpr std::array<std::array<std::uint8_t, 5>, 4> kPtpOriginalCalls12004{{
    {{0xE8, 0x52, 0xB1, 0x14, 0x00}}, {{0xE8, 0xD3, 0xB6, 0x14, 0x00}},
    {{0xE8, 0x84, 0xBC, 0x14, 0x00}}, {{0xE8, 0xC5, 0xC1, 0x14, 0x00}}}};
// Original complete 392-byte dispatcher, including six-entry native jump table.
// Body SHA256 1ac0643b9d18a185dffa2ff62a513533823ececa29049f851c3fa559dd06aba7.
constexpr char kPtpDispatcherHex12004[] = "40534883ec2066ff815c040000488bd9488b89c8030000e814e9f1fc440fb7835c040000488b93d0000000488b8bc8030000e899100100440fb7835c040000488b93d8000000488b8bc8030000e87e10010080bb2c040000000f85be00000080bb2d040000000f85b1000000488b8bf8020000488d542438488b01ff5068660f6e442438660f6e4c243c488b8b700300000f5bc00f5bc9f30f11442430f30f114c2434e8c8584a00486383780300000f28c80f57dbf20f5c8b88030000f20f118388030000f20f5ad983f805775e488d157bd854fc8b8c822028ab034803caffe14c8b442430488bd3e852b11400eb3c4c8b442430488bd3e8d3b61400eb2d4c8b442430488bd3e884bc1400eb1e4c8b442430488bd3e8c5c11400eb0f488bcbc6832c04000000e8445effff83bb9c01000000742348638b9c010000488b839001000048c1e1054883c0e04803c87408488b09e8a86f0800488b8bc80300004883c1204883c4205be9c3e7f1fc0f1f00be27ab039127ab03af27ab03a027ab03af27ab03a027ab03";
constexpr char kPtpCalleePrefixHex12004[] =
    "488bc448895810488970204c894018488948085557415441564157488d68b84881ec200100000f2970c80f28f3498bd8488bfa";
constexpr std::size_t kPtpStubSize12004 = 256;
constexpr std::size_t kPtpBackingSize12004 = 4096;
using PtpStub12004 = std::array<std::uint8_t, kPtpStubSize12004>;
struct PtpSlot12004 {
  std::uintptr_t call = 0, native = 0, continuation = 0, stub = 0;
  std::array<std::uint8_t, 5> patch{};
};
struct PtpState12004 {
  // 0 untouched, 1 preparing, 2 all four installed, 3 failed; no hot retry.
  volatile LONG phase = 0;
  std::uintptr_t base = 0;
  void *backing = nullptr;
  std::array<PtpSlot12004, 4> slots{};
};
PtpState12004 ptp_state12004{};

bool PtpShaMatches12004(std::string_view sha) noexcept {
  if (sha.size() != kPtpExeSha12004.size()) return false;
  for (std::size_t i = 0; i != sha.size(); ++i) {
    auto c = sha[i];
    if (c >= 'A' && c <= 'F') c = static_cast<char>(c + ('a' - 'A'));
    if (c != kPtpExeSha12004[i]) return false;
  }
  return true;
}
bool PtpAdd12004(std::uintptr_t base, std::uintptr_t rva, std::uintptr_t &out) noexcept {
  if (!base || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  out = base + rva;
  return true;
}
bool PtpCopyFrom12004(std::uintptr_t from, void *to, std::size_t size) noexcept {
  if (!from || !to || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(to, reinterpret_cast<const void *>(from), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool PtpCopyTo12004(std::uintptr_t to, const void *from, std::size_t size) noexcept {
  if (!from || !to || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(to), from, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool PtpEqual12004(std::uintptr_t address, const std::uint8_t *bytes, std::size_t size) noexcept {
  if (!address || !bytes || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), bytes, size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool PtpHexMatches12004(std::uintptr_t address, std::string_view hex) noexcept {
  if (!address || hex.size() % 2 || hex.size() > 784) return false;
  std::array<std::uint8_t, 392> actual{};
  if (!PtpCopyFrom12004(address, actual.data(), hex.size() / 2)) return false;
  constexpr char digits[] = "0123456789abcdef";
  for (std::size_t i = 0; i != hex.size() / 2; ++i)
    if (hex[i * 2] != digits[actual[i] >> 4] || hex[i * 2 + 1] != digits[actual[i] & 15]) return false;
  return true;
}
bool PtpExecutable12004(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ || protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}
bool PtpRelative12004(std::uintptr_t target, std::uintptr_t next, std::int32_t &out) noexcept {
  if (target >= next) {
    const auto distance = target - next;
    if (distance > 0x7FFFFFFFu) return false;
    out = static_cast<std::int32_t>(distance);
  } else {
    const auto distance = next - target;
    if (distance > 0x80000000u) return false;
    out = distance == 0x80000000u ? (std::numeric_limits<std::int32_t>::min)()
                                : -static_cast<std::int32_t>(distance);
  }
  return true;
}
bool PtpAllReachable12004(std::uintptr_t backing, const PtpState12004 &state) noexcept {
  for (std::size_t i = 0; i != state.slots.size(); ++i) {
    std::uintptr_t stub = 0;
    std::int32_t relative = 0;
    if (!PtpAdd12004(backing, i * kPtpStubSize12004, stub) ||
        !PtpRelative12004(stub, state.slots[i].continuation, relative)) return false;
  }
  return true;
}
void *PtpAllocateNear12004(const PtpState12004 &state) noexcept {
  SYSTEM_INFO info{};
  GetSystemInfo(&info);
  const auto granularity = static_cast<std::uintptr_t>(info.dwAllocationGranularity);
  if (!granularity) return nullptr;
  const auto next = state.slots.front().continuation;
  const auto minimum = reinterpret_cast<std::uintptr_t>(info.lpMinimumApplicationAddress);
  const auto maximum = reinterpret_cast<std::uintptr_t>(info.lpMaximumApplicationAddress);
  auto low = next > 0x80000000u ? next - 0x80000000u : minimum;
  auto high = next <= (std::numeric_limits<std::uintptr_t>::max)() - 0x7FFFFFFFu
      ? next + 0x7FFFFFFFu : maximum;
  if (low < minimum) low = minimum;
  if (high > maximum) high = maximum;
  for (auto cursor = low; cursor <= high;) {
    MEMORY_BASIC_INFORMATION region{};
    if (!VirtualQuery(reinterpret_cast<void *>(cursor), &region, sizeof(region))) break;
    const auto begin = reinterpret_cast<std::uintptr_t>(region.BaseAddress);
    if (!region.RegionSize || region.RegionSize > (std::numeric_limits<std::uintptr_t>::max)() - begin) break;
    const auto end = begin + region.RegionSize;
    if (end <= cursor) break;
    if (region.State == MEM_FREE) {
      auto candidate = cursor > begin ? cursor : begin;
      const auto remainder = candidate % granularity;
      const auto adjustment = remainder ? granularity - remainder : 0;
      if (candidate > (std::numeric_limits<std::uintptr_t>::max)() - adjustment) break;
      candidate += adjustment;
      if (candidate <= high && candidate < end && kPtpBackingSize12004 <= end - candidate &&
          PtpAllReachable12004(candidate, state)) {
        auto *allocated = VirtualAlloc(reinterpret_cast<void *>(candidate), kPtpBackingSize12004,
            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (allocated) {
          if (PtpAllReachable12004(reinterpret_cast<std::uintptr_t>(allocated), state)) return allocated;
          (void)VirtualFree(allocated, 0, MEM_RELEASE);
        }
      }
    }
    cursor = end;
  }
  return nullptr;
}

template<auto Override>
std::uint64_t PtpApplyWith12004(void *gui, std::uint64_t original, LONG phase) noexcept {
  if (!gui || phase != 2) return original;
  auto candidate = original;
  // Parent must re-bind the active finite receipt/current root/source/frame here.
  // No receipt, leave, stale binding, modal, different GUI or unknown geometry => false.
#if defined(_MSC_VER)
  __try {
#endif
    return Override(gui, candidate) ? candidate : original;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return original; }
#endif
}
std::uint64_t PtpApply12004(void *gui, std::uint64_t original) noexcept {
  // Production binds one compile-time callback. No runtime injection interface.
  return PtpApplyWith12004<&PresentationTooltipPositionOverride12004>(gui, original,
      InterlockedCompareExchange(&ptp_state12004.phase, 2, 2));
}
bool PtpEmit12004(PtpStub12004 &bytes, std::size_t &at,
    std::initializer_list<std::uint8_t> values) noexcept {
  if (values.size() > bytes.size() - at) return false;
  for (const auto value : values) bytes[at++] = value;
  return true;
}
bool PtpU6412004(PtpStub12004 &bytes, std::size_t &at, std::uintptr_t value) noexcept {
  if (sizeof(value) > bytes.size() - at) return false;
  std::memcpy(bytes.data() + at, &value, sizeof(value));
  at += sizeof(value);
  return true;
}
template<auto Apply = &PtpApply12004>
std::size_t PtpBuildStub12004(const PtpSlot12004 &slot, PtpStub12004 &bytes) noexcept {
  bytes.fill(0x90);
  std::size_t at = 0;
  // Original E8 CALL enters with its real normal/shadow return address, RSP=8 mod16.
  // Push64B then reserve136B: shadow32B + XMM0..5=96B + alignment8B.
  if (!PtpEmit12004(bytes, at, {0x9C,0x50,0x51,0x52,0x41,0x50,0x41,0x51,0x41,0x52,0x41,0x53}) ||
      !PtpEmit12004(bytes, at, {0x48,0x81,0xEC,0x88,0x00,0x00,0x00})) return 0;
  for (std::uint8_t reg = 0; reg != 6; ++reg)
    if (!PtpEmit12004(bytes, at, {0xF3,0x0F,0x7F,static_cast<std::uint8_t>(0x44 + 8 * reg),
        0x24,static_cast<std::uint8_t>(0x20 + 0x10 * reg)})) return 0;
  // callback RCX = original RDX (GUI), RDX = original packed R8 (XY).
  if (!PtpEmit12004(bytes, at, {0x48,0x8B,0x94,0x24,0xA0,0x00,0x00,0x00}) ||
      !PtpEmit12004(bytes, at, {0x48,0x8B,0x8C,0x24,0xA8,0x00,0x00,0x00}) ||
      !PtpEmit12004(bytes, at, {0x48,0xB8}) ||
      !PtpU6412004(bytes, at, reinterpret_cast<std::uintptr_t>(Apply)) ||
      !PtpEmit12004(bytes, at, {0xFF,0xD0}) ||
      !PtpEmit12004(bytes, at, {0x48,0x89,0x84,0x24,0xA0,0x00,0x00,0x00})) return 0;
  // Replace exactly saved R8. Restore original flags, opaque RCX, context RDX,
  // all other volatile GP and XMM0..5 (including native dt in XMM3).
  for (std::uint8_t reg = 0; reg != 6; ++reg)
    if (!PtpEmit12004(bytes, at, {0xF3,0x0F,0x6F,static_cast<std::uint8_t>(0x44 + 8 * reg),
        0x24,static_cast<std::uint8_t>(0x20 + 0x10 * reg)})) return 0;
  if (!PtpEmit12004(bytes, at, {0x48,0x81,0xC4,0x88,0x00,0x00,0x00}) ||
      !PtpEmit12004(bytes, at, {0x41,0x5B,0x41,0x5A,0x41,0x59,0x41,0x58,0x5A,0x59,0x58,0x9D}) ||
      // Tail-enter native once with original E8 return address still on both stacks.
      // Native RET/unwind goes directly to original dispatcher, never relay+152.
      !PtpEmit12004(bytes, at, {0xFF,0x25,0x00,0x00,0x00,0x00}) ||
      !PtpU6412004(bytes, at, slot.native)) return 0;
  return at;
}

bool PresentationTooltipPositionHooksReady12004() noexcept {
  if (InterlockedCompareExchange(&ptp_state12004.phase, 2, 2) != 2) return false;
  for (const auto &slot : ptp_state12004.slots)
    if (!PtpEqual12004(slot.call, slot.patch.data(), slot.patch.size())) return false;
  return true;
}
bool InstallPresentationTooltipPositionHooks12004(
    std::uintptr_t base, std::string_view sha, bool suspended) noexcept {
  if (!suspended || !base || !PtpShaMatches12004(sha) ||
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) != base) return false;
  if (InterlockedCompareExchange(&ptp_state12004.phase, 1, 0) != 0)
    return ptp_state12004.base == base && PresentationTooltipPositionHooksReady12004();
  auto &state = ptp_state12004;
  state.base = base;
  const auto fail = [&]() noexcept {
    InterlockedExchange(&state.phase, 3);
    return false;
  };
  std::uintptr_t dispatcher = 0;
  if (!PtpAdd12004(base, kPtpDispatcherRva12004, dispatcher) ||
      !PtpHexMatches12004(dispatcher, kPtpDispatcherHex12004)) return fail();
  for (std::size_t i = 0; i != state.slots.size(); ++i) {
    auto &slot = state.slots[i];
    if (!PtpAdd12004(base, kPtpCalls12004[i], slot.call) ||
        !PtpAdd12004(base, kPtpCallees12004[i], slot.native) ||
        !PtpAdd12004(slot.call, 5, slot.continuation) ||
        !PtpHexMatches12004(slot.native, kPtpCalleePrefixHex12004) ||
        !PtpEqual12004(slot.call, kPtpOriginalCalls12004[i].data(), 5)) return fail();
  }
  // Permanent CALL patches must never outlive their DLL callback.
  // PIN is process-lifetime and is not undone if a later install step fails.
  HMODULE pinned_bridge = nullptr;
  if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&PtpApply12004), &pinned_bridge) ||
      pinned_bridge == nullptr) return fail();
  state.backing = PtpAllocateNear12004(state);
  if (!state.backing) return fail();
  bool stub_ok = true;
  for (std::size_t i = 0; i != state.slots.size(); ++i) {
    auto &slot = state.slots[i];
    slot.stub = reinterpret_cast<std::uintptr_t>(state.backing) + i * kPtpStubSize12004;
    PtpStub12004 bytes{};
    std::int32_t relative = 0;
    if (!PtpBuildStub12004(slot, bytes) || !PtpCopyTo12004(slot.stub, bytes.data(), bytes.size()) ||
        !PtpEqual12004(slot.stub, bytes.data(), bytes.size()) ||
        !PtpRelative12004(slot.stub, slot.continuation, relative)) { stub_ok = false; break; }
    slot.patch[0] = 0xE8;
    std::memcpy(slot.patch.data() + 1, &relative, sizeof(relative));
  }
  DWORD stub_previous = 0;
  if (!stub_ok || !VirtualProtect(state.backing, kPtpBackingSize12004, PAGE_EXECUTE_READ, &stub_previous) ||
      stub_previous != PAGE_READWRITE ||
      !FlushInstructionCache(GetCurrentProcess(), state.backing, kPtpBackingSize12004)) {
    if (VirtualFree(state.backing, 0, MEM_RELEASE)) state.backing = nullptr;
    return fail();
  }
  // One page/protection transaction for the four fixed sites. Main is suspended.
  const auto span = state.slots.back().continuation - state.slots.front().call;
  auto *target = reinterpret_cast<void *>(state.slots.front().call);
  DWORD original_protection = 0;
  if (!VirtualProtect(target, span, PAGE_EXECUTE_READWRITE, &original_protection)) {
    if (VirtualFree(state.backing, 0, MEM_RELEASE)) state.backing = nullptr;
    return fail();
  }
  bool patched = PtpExecutable12004(original_protection);
  for (std::size_t i = 0; patched && i != state.slots.size(); ++i) {
    const auto &slot = state.slots[i];
    patched = PtpEqual12004(slot.call, kPtpOriginalCalls12004[i].data(), 5) &&
        PtpCopyTo12004(slot.call, slot.patch.data(), 5) && PtpEqual12004(slot.call, slot.patch.data(), 5);
  }
  const bool flushed = patched && FlushInstructionCache(GetCurrentProcess(), target, span);
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(target, span, original_protection, &ignored) != FALSE;
  if (flushed && protected_again) {
    InterlockedExchange(&state.phase, 2);
    if (PresentationTooltipPositionHooksReady12004()) return true;
    return fail(); // Keep backing; startup must not resume an unproven patch.
  }
  // Roll back every byte we may have written. Do not overwrite any third-party
  // patch. Unproven rollback retains executable backing and permanently fails.
  DWORD rollback_previous = 0;
  bool rollback = VirtualProtect(target, span, PAGE_EXECUTE_READWRITE, &rollback_previous) != FALSE;
  for (std::size_t i = 0; i != state.slots.size(); ++i) {
    const auto &slot = state.slots[i];
    if (PtpEqual12004(slot.call, kPtpOriginalCalls12004[i].data(), 5)) continue;
    if (!rollback || !PtpEqual12004(slot.call, slot.patch.data(), 5) ||
        !PtpCopyTo12004(slot.call, kPtpOriginalCalls12004[i].data(), 5) ||
        !PtpEqual12004(slot.call, kPtpOriginalCalls12004[i].data(), 5)) rollback = false;
  }
  rollback = FlushInstructionCache(GetCurrentProcess(), target, span) && rollback;
  DWORD rollback_ignored = 0;
  rollback = VirtualProtect(target, span, original_protection, &rollback_ignored) && rollback;
  if (rollback && VirtualFree(state.backing, 0, MEM_RELEASE)) state.backing = nullptr;
  return fail();
}
