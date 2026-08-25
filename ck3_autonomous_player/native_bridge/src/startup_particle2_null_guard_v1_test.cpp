#include "xar_bridge/startup_particle2_null_guard_v1.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <initializer_list>
#include <iterator>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace {

const char *g_failure_stage = "not_started";

constexpr std::array<std::uint8_t, 29> kPrologue{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10,
    0x48, 0x89, 0x74, 0x24, 0x18, 0x48, 0x89, 0x7C, 0x24, 0x20,
    0x41, 0x56, 0x48, 0x81, 0xEC, 0x80, 0x08, 0x00, 0x00};
constexpr std::array<std::uint8_t, 21> kPatchAnchor{
    0x0F, 0xB6, 0xEA, 0x48, 0x8B, 0xD9, 0x48,
    0x8B, 0x05, 0x8E, 0x3B, 0x96, 0x03, 0x4C,
    0x8B, 0xB4, 0xE8, 0xA8, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 30> kEpilogue{
    0x4C, 0x8D, 0x9C, 0x24, 0x80, 0x08, 0x00, 0x00,
    0x49, 0x8B, 0x5B, 0x10, 0x49, 0x8B, 0x6B, 0x18,
    0x49, 0x8B, 0x73, 0x20, 0x49, 0x8B, 0x7B, 0x28,
    0x49, 0x8B, 0xE3, 0x41, 0x5E, 0xC3};

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

bool StrictUtf8WithoutReplacement(std::string_view input) {
  if (input.empty() ||
      input.size() > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
    return false;
  }
  const auto input_size = static_cast<int>(input.size());
  const int required = MultiByteToWideChar(
      CP_UTF8, MB_ERR_INVALID_CHARS, input.data(), input_size, nullptr, 0);
  if (required <= 0) {
    return false;
  }
  std::vector<wchar_t> decoded(static_cast<std::size_t>(required));
  if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, input.data(),
                          input_size, decoded.data(), required) != required) {
    return false;
  }
  return std::none_of(decoded.begin(), decoded.end(),
                      [](wchar_t value) { return value == 0xFFFDU; });
}

template <typename Value>
bool ReadInteger(std::string_view image, std::size_t offset, Value &output) {
  if (offset > image.size() || sizeof(output) > image.size() - offset) {
    return false;
  }
  std::memcpy(&output, image.data() + offset, sizeof(output));
  return true;
}

std::optional<std::size_t> RvaToOffset(std::string_view image,
                                       std::uint32_t rva) {
  std::uint32_t pe_offset = 0;
  if (image.size() < 0x40 || image.substr(0, 2) != "MZ" ||
      !ReadInteger(image, 0x3C, pe_offset) ||
      pe_offset > image.size() - 24 ||
      image.substr(pe_offset, 4) != std::string_view{"PE\0\0", 4}) {
    return std::nullopt;
  }
  std::uint16_t section_count = 0;
  std::uint16_t optional_header_size = 0;
  if (!ReadInteger(image, pe_offset + 6, section_count) ||
      !ReadInteger(image, pe_offset + 20, optional_header_size) ||
      section_count == 0 || section_count > 128) {
    return std::nullopt;
  }
  const auto section_table =
      static_cast<std::size_t>(pe_offset) + 24 + optional_header_size;
  if (section_table > image.size() ||
      static_cast<std::size_t>(section_count) >
          (image.size() - section_table) / 40) {
    return std::nullopt;
  }
  for (std::uint16_t index = 0; index < section_count; ++index) {
    const auto row = section_table + static_cast<std::size_t>(index) * 40;
    std::uint32_t virtual_size = 0;
    std::uint32_t virtual_address = 0;
    std::uint32_t raw_size = 0;
    std::uint32_t raw_offset = 0;
    if (!ReadInteger(image, row + 8, virtual_size) ||
        !ReadInteger(image, row + 12, virtual_address) ||
        !ReadInteger(image, row + 16, raw_size) ||
        !ReadInteger(image, row + 20, raw_offset)) {
      return std::nullopt;
    }
    const auto mapped_size = std::max(virtual_size, raw_size);
    if (rva < virtual_address || rva - virtual_address >= mapped_size) {
      continue;
    }
    const auto delta = static_cast<std::size_t>(rva - virtual_address);
    if (delta >= raw_size || raw_offset > image.size() ||
        delta > image.size() - raw_offset) {
      return std::nullopt;
    }
    return static_cast<std::size_t>(raw_offset) + delta;
  }
  return std::nullopt;
}

bool BytesAt(std::string_view image, std::uint32_t rva,
             std::initializer_list<std::uint8_t> expected) {
  const auto offset = RvaToOffset(image, rva);
  return offset && *offset <= image.size() &&
         expected.size() <= image.size() - *offset &&
         std::equal(expected.begin(), expected.end(),
                    reinterpret_cast<const std::uint8_t *>(image.data()) +
                        *offset);
}

bool Sha256Upper(std::string_view input, std::string &output) {
  output.clear();
  if (input.size() > std::numeric_limits<ULONG>::max()) {
    return false;
  }
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool succeeded = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0 || copied != sizeof(object_size)) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0 ||
        BCryptHashData(
            hash,
            reinterpret_cast<PUCHAR>(const_cast<char *>(input.data())),
            static_cast<ULONG>(input.size()), 0) < 0 ||
        BCryptFinishHash(hash, digest.data(),
                         static_cast<ULONG>(digest.size()), 0) < 0) {
      break;
    }
    succeeded = true;
  } while (false);
  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  if (!succeeded) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  output.resize(digest.size() * 2);
  for (std::size_t index = 0; index < digest.size(); ++index) {
    output[index * 2] = digits[digest[index] >> 4U];
    output[index * 2 + 1] = digits[digest[index] & 0x0FU];
  }
  return true;
}

void WriteU64(std::uint8_t *destination, std::uintptr_t value) {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(destination, &encoded, sizeof(encoded));
}

std::uint64_t ReadU64(const std::uint8_t *source) {
  std::uint64_t value = 0;
  std::memcpy(&value, source, sizeof(value));
  return value;
}

std::int32_t ReadI32(const std::uint8_t *source) {
  std::int32_t value = 0;
  std::memcpy(&value, source, sizeof(value));
  return value;
}

struct SyntheticRegistrationFunction {
  static constexpr std::size_t kAllocationBytes = 4096;
  static constexpr std::size_t kPatchOffset = 29;
  static constexpr std::size_t kContinueOffset = 50;
  static constexpr std::size_t kEpilogueOffset = 256;

  std::uint8_t *code = nullptr;
  alignas(8) std::atomic<std::uint64_t> continuation_marker{0};
  alignas(8) std::array<std::uint8_t, 0x100> root{};
  std::uintptr_t root_slot = 0;

  SyntheticRegistrationFunction() {
    code = static_cast<std::uint8_t *>(
        VirtualAlloc(nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT,
                     PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0xCC, kAllocationBytes);
    std::memcpy(code, kPrologue.data(), kPrologue.size());
    std::memcpy(code + kPatchOffset, kPatchAnchor.data(),
                kPatchAnchor.size());

    std::size_t cursor = kContinueOffset;
    code[cursor++] = 0x49;
    code[cursor++] = 0xBB; // mov r11, &continuation_marker
    WriteU64(code + cursor,
             reinterpret_cast<std::uintptr_t>(&continuation_marker));
    cursor += sizeof(std::uint64_t);
    const std::array<std::uint8_t, 4> increment{
        0xF0, 0x49, 0xFF, 0x03}; // lock inc qword [r11]
    std::memcpy(code + cursor, increment.data(), increment.size());
    cursor += increment.size();
    code[cursor++] = 0x49;
    code[cursor++] = 0xBB; // mov r11, epilogue
    WriteU64(code + cursor,
             reinterpret_cast<std::uintptr_t>(code + kEpilogueOffset));
    cursor += sizeof(std::uint64_t);
    const std::array<std::uint8_t, 3> jump{0x41, 0xFF, 0xE3};
    std::memcpy(code + cursor, jump.data(), jump.size());
    std::memcpy(code + kEpilogueOffset, kEpilogue.data(), kEpilogue.size());
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READ, &previous) ==
            FALSE ||
        previous != PAGE_READWRITE ||
        FlushInstructionCache(GetCurrentProcess(), code, kAllocationBytes) ==
            FALSE) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
      code = nullptr;
    }
  }

  ~SyntheticRegistrationFunction() {
    if (code != nullptr) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
    }
  }

  SyntheticRegistrationFunction(const SyntheticRegistrationFunction &) =
      delete;
  SyntheticRegistrationFunction &operator=(
      const SyntheticRegistrationFunction &) = delete;

  bool valid() const noexcept { return code != nullptr; }

  bool SetPatchByte(std::size_t relative_offset,
                    std::uint8_t value) noexcept {
    if (code == nullptr || relative_offset >= kPatchAnchor.size()) {
      return false;
    }
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READWRITE,
                       &previous) == FALSE ||
        previous != PAGE_EXECUTE_READ) {
      return false;
    }
    code[kPatchOffset + relative_offset] = value;
    const bool flushed = FlushInstructionCache(
        GetCurrentProcess(), code + kPatchOffset + relative_offset, 1) !=
        FALSE;
    DWORD ignored = 0;
    const bool restored =
        VirtualProtect(code, kAllocationBytes, previous, &ignored) != FALSE;
    return flushed && restored;
  }

  xar::bridge::StartupParticle2NullGuardV1Environment Environment() {
    xar::bridge::StartupParticle2NullGuardV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x140000000ULL;
    environment.patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kPatchOffset);
    environment.root_slot_address_override =
        reinterpret_cast<std::uintptr_t>(&root_slot);
    environment.continue_target_override =
        reinterpret_cast<std::uintptr_t>(code + kContinueOffset);
    environment.skip_target_override =
        reinterpret_cast<std::uintptr_t>(code + kEpilogueOffset);
    return environment;
  }

  void SetRoot(bool present) noexcept {
    root_slot = present ? reinterpret_cast<std::uintptr_t>(root.data()) : 0;
  }

  void SetSlot(std::uint32_t index, std::uintptr_t value) noexcept {
    const auto offset = xar::bridge::kStartupParticle2SlotBaseOffsetV1 +
                        index * xar::bridge::kStartupParticle2SlotStrideV1;
    std::memcpy(root.data() + offset, &value, sizeof(value));
  }

  void Invoke(std::uint8_t index) {
    using Function = void(__fastcall *)(void *, std::uint8_t) noexcept;
    const auto function = reinterpret_cast<Function>(code);
    function(reinterpret_cast<void *>(0x1234U), index);
  }
};

struct FaultInjectingMemory {
  std::uint32_t alloc_calls = 0;
  std::uint32_t free_calls = 0;
  std::uint32_t protect_calls = 0;
  std::uint32_t flush_calls = 0;
  std::uint32_t fail_protect_call = 0;
  std::uint32_t fail_flush_call = 0;
  bool fail_allocation = false;
};

void *FaultVirtualAlloc(void *opaque, std::size_t size,
                        DWORD allocation_type, DWORD protection) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.alloc_calls;
  if (memory.fail_allocation) {
    return nullptr;
  }
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool FaultVirtualFree(void *opaque, void *address, std::size_t size,
                      DWORD free_type) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.free_calls;
  return VirtualFree(address, size, free_type) != FALSE;
}

bool FaultVirtualProtect(void *opaque, void *address, std::size_t size,
                         DWORD new_protection,
                         DWORD &old_protection) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.protect_calls;
  if (memory.fail_protect_call != 0 &&
      memory.protect_calls == memory.fail_protect_call) {
    old_protection = 0;
    return false;
  }
  return VirtualProtect(address, size, new_protection, &old_protection) !=
         FALSE;
}

bool FaultFlush(void *opaque, const void *address, std::size_t size) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.flush_calls;
  if (memory.fail_flush_call != 0 &&
      memory.flush_calls == memory.fail_flush_call) {
    return false;
  }
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

void AddFaultCallbacks(
    xar::bridge::StartupParticle2NullGuardV1Environment &environment,
    FaultInjectingMemory &memory) {
  environment.memory_context = &memory;
  environment.virtual_alloc_override = &FaultVirtualAlloc;
  environment.virtual_free_override = &FaultVirtualFree;
  environment.virtual_protect_override = &FaultVirtualProtect;
  environment.flush_instruction_cache_override = &FaultFlush;
}

bool IsOriginalPatch(const SyntheticRegistrationFunction &fixture) {
  return std::memcmp(fixture.code + fixture.kPatchOffset,
                     kPatchAnchor.data(),
                     xar::bridge::kStartupParticle2NullGuardPatchBytesV1) ==
         0;
}

bool TestAdmissionAndAnchorRejection() {
  using namespace xar::bridge;
  g_failure_stage = "admission";
  StartupParticle2NullGuardV1State exact_rejected{};
  StartupParticle2NullGuardV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;
  if (InstallStartupParticle2NullGuardV1(exact_rejected, environment) ||
      (exact_rejected.failure_flags.load() &
       startup_particle2_null_guard_failure_exact_build) == 0) {
    return false;
  }

  StartupParticle2NullGuardV1State suspension_rejected{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  if (InstallStartupParticle2NullGuardV1(suspension_rejected, environment) ||
      (suspension_rejected.failure_flags.load() &
       startup_particle2_null_guard_failure_primary_thread_suspended) == 0) {
    return false;
  }

  StartupParticle2NullGuardV1State override_rejected{};
  environment.primary_thread_suspended_proven = true;
  environment.patch_target_override = 1;
  if (InstallStartupParticle2NullGuardV1(override_rejected, environment) ||
      (override_rejected.failure_flags.load() &
       startup_particle2_null_guard_failure_unsupported_override) == 0) {
    return false;
  }

  SyntheticRegistrationFunction fixture;
  if (!fixture.valid()) {
    return false;
  }
  const auto saved = fixture.code[fixture.kPatchOffset + 4];
  if (!fixture.SetPatchByte(4, static_cast<std::uint8_t>(saved ^ 0x80U))) {
    return false;
  }
  StartupParticle2NullGuardV1State drift_rejected{};
  auto drift_environment = fixture.Environment();
  const bool drift_installed =
      InstallStartupParticle2NullGuardV1(drift_rejected, drift_environment);
  const bool restored = fixture.SetPatchByte(4, saved);
  return restored && !drift_installed && drift_rejected.stub == nullptr &&
      (drift_rejected.failure_flags.load() &
       startup_particle2_null_guard_failure_anchor) != 0;
}

bool TestExecutableGuard() {
  using namespace xar::bridge;
  g_failure_stage = "executable_guard_install";
  SyntheticRegistrationFunction fixture;
  if (!fixture.valid()) {
    return false;
  }
  StartupParticle2NullGuardV1State state{};
  const auto environment = fixture.Environment();
  if (!InstallStartupParticle2NullGuardV1(state, environment) ||
      state.installed.load() != 1 || state.stub == nullptr) {
    return false;
  }

  const auto *patch = fixture.code + fixture.kPatchOffset;
  if (patch[0] != 0x49 || patch[1] != 0xBB || patch[10] != 0x41 ||
      patch[11] != 0xFF || patch[12] != 0xE3 ||
      ReadU64(patch + 2) != reinterpret_cast<std::uintptr_t>(state.stub) ||
      fixture.kPatchOffset != kStartupParticle2RegistrationPrologueBytesV1) {
    return false;
  }

  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  if (std::memcmp(stub, "\x0F\xB6\xEA\x48\x8B\xD9\x83\xFD\x07", 9) != 0 ||
      stub[9] != 0x0F || stub[10] != 0x87 ||
      15 + ReadI32(stub + 11) != 90 ||
      ReadU64(stub + 17) != environment.root_slot_address_override ||
      stub[31] != 0x0F || stub[32] != 0x84 ||
      37 + ReadI32(stub + 33) != 67 ||
      stub[48] != 0x0F || stub[49] != 0x84 ||
      54 + ReadI32(stub + 50) != 67 ||
      ReadU64(stub + 56) != environment.continue_target_override ||
      ReadU64(stub + 78) !=
          reinterpret_cast<std::uintptr_t>(&state.suppressed_index_mask) ||
      ReadU64(stub + 92) !=
          reinterpret_cast<std::uintptr_t>(&state.suppressed_count) ||
      ReadU64(stub + 106) !=
          reinterpret_cast<std::uintptr_t>(&state.last_suppressed_index) ||
      ReadU64(stub + 119) != environment.skip_target_override) {
    return false;
  }

  g_failure_stage = "executable_guard_root_null";
  fixture.SetRoot(false);
  fixture.Invoke(2);
  auto diagnostics = ReadStartupParticle2NullGuardV1Diagnostics(state);
  if (diagnostics.suppressed_count != 1 ||
      diagnostics.suppressed_index_mask != (1U << 2) ||
      diagnostics.last_suppressed_index != 2 ||
      fixture.continuation_marker.load() != 0) {
    return false;
  }

  g_failure_stage = "executable_guard_slot_null";
  fixture.SetRoot(true);
  fixture.SetSlot(4, 0);
  fixture.Invoke(4);
  diagnostics = ReadStartupParticle2NullGuardV1Diagnostics(state);
  if (diagnostics.suppressed_count != 2 ||
      diagnostics.suppressed_index_mask != ((1U << 2) | (1U << 4)) ||
      diagnostics.last_suppressed_index != 4 ||
      fixture.continuation_marker.load() != 0) {
    return false;
  }

  g_failure_stage = "executable_guard_nonnull";
  fixture.SetSlot(4, reinterpret_cast<std::uintptr_t>(fixture.root.data()));
  fixture.Invoke(4);
  diagnostics = ReadStartupParticle2NullGuardV1Diagnostics(state);
  if (diagnostics.suppressed_count != 2 ||
      diagnostics.suppressed_index_mask != ((1U << 2) | (1U << 4)) ||
      diagnostics.last_suppressed_index != 4 ||
      fixture.continuation_marker.load() != 1) {
    return false;
  }

  g_failure_stage = "executable_guard_oob";
  // A fall-through would dereference root=1 while calculating slot[8] and
  // fault. Returning proves the unsigned index bound dominates both reads.
  fixture.root_slot = 1;
  fixture.Invoke(8);
  diagnostics = ReadStartupParticle2NullGuardV1Diagnostics(state);
  if (diagnostics.suppressed_count != 3 ||
      diagnostics.suppressed_index_mask != ((1U << 2) | (1U << 4)) ||
      diagnostics.last_suppressed_index != 8 ||
      fixture.continuation_marker.load() != 1) {
    return false;
  }

  g_failure_stage = "executable_guard_uninstall";
  if (!UninstallStartupParticle2NullGuardV1(state) ||
      state.installed.load() != 0 || state.stub != nullptr ||
      !IsOriginalPatch(fixture)) {
    return false;
  }
  return true;
}

bool TestAllocationAndTransactionalRollback() {
  using namespace xar::bridge;

  g_failure_stage = "allocation_failure";
  SyntheticRegistrationFunction allocation_fixture;
  if (!allocation_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory allocation_memory{};
  allocation_memory.fail_allocation = true;
  auto allocation_environment = allocation_fixture.Environment();
  AddFaultCallbacks(allocation_environment, allocation_memory);
  StartupParticle2NullGuardV1State allocation_state{};
  if (InstallStartupParticle2NullGuardV1(allocation_state,
                                         allocation_environment) ||
      !IsOriginalPatch(allocation_fixture) ||
      allocation_memory.alloc_calls != 1 || allocation_memory.free_calls != 0 ||
      (allocation_state.failure_flags.load() &
       startup_particle2_null_guard_failure_allocation) == 0) {
    return false;
  }

  g_failure_stage = "flush_rollback";
  SyntheticRegistrationFunction flush_fixture;
  if (!flush_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory flush_memory{};
  flush_memory.fail_flush_call = 2; // generated stub flush is call one
  auto flush_environment = flush_fixture.Environment();
  AddFaultCallbacks(flush_environment, flush_memory);
  StartupParticle2NullGuardV1State flush_state{};
  if (InstallStartupParticle2NullGuardV1(flush_state, flush_environment) ||
      flush_state.installed.load() != 0 || flush_state.stub != nullptr ||
      !IsOriginalPatch(flush_fixture) || flush_memory.free_calls != 1 ||
      flush_memory.flush_calls != 3 ||
      (flush_state.failure_flags.load() &
       startup_particle2_null_guard_failure_flush) == 0 ||
      (flush_state.failure_flags.load() &
       startup_particle2_null_guard_failure_rollback) != 0) {
    return false;
  }

  g_failure_stage = "protection_rollback";
  SyntheticRegistrationFunction protection_fixture;
  if (!protection_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory protection_memory{};
  // stub RX, target RWX, then fail the first target protection restore.
  protection_memory.fail_protect_call = 3;
  auto protection_environment = protection_fixture.Environment();
  AddFaultCallbacks(protection_environment, protection_memory);
  StartupParticle2NullGuardV1State protection_state{};
  if (InstallStartupParticle2NullGuardV1(protection_state,
                                         protection_environment) ||
      protection_state.installed.load() != 0 ||
      protection_state.stub != nullptr ||
      !IsOriginalPatch(protection_fixture) ||
      protection_memory.free_calls != 1 ||
      protection_memory.protect_calls != 5 ||
      (protection_state.failure_flags.load() &
       startup_particle2_null_guard_failure_target_protection) == 0 ||
      (protection_state.failure_flags.load() &
       startup_particle2_null_guard_failure_rollback) != 0) {
    return false;
  }

  // A successful install after both rollback cases proves global ownership was
  // released and no failed transaction left a live target jump behind.
  g_failure_stage = "post_rollback_reinstall";
  StartupParticle2NullGuardV1State retry_state{};
  const auto retry_environment = protection_fixture.Environment();
  if (!InstallStartupParticle2NullGuardV1(retry_state, retry_environment) ||
      !UninstallStartupParticle2NullGuardV1(retry_state) ||
      !IsOriginalPatch(protection_fixture)) {
    return false;
  }

  // Keep this case last: an unproven rollback intentionally retains global
  // ownership and executable storage for the remainder of the process.
  g_failure_stage = "failed_rollback_retains_stub";
  SyntheticRegistrationFunction unsafe_fixture;
  if (!unsafe_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory unsafe_memory{};
  unsafe_memory.fail_flush_call = 2;
  unsafe_memory.fail_protect_call = 3;
  auto unsafe_environment = unsafe_fixture.Environment();
  AddFaultCallbacks(unsafe_environment, unsafe_memory);
  static StartupParticle2NullGuardV1State unsafe_state{};
  if (InstallStartupParticle2NullGuardV1(unsafe_state, unsafe_environment) ||
      unsafe_state.installed.load() != 1 || unsafe_state.stub == nullptr ||
      unsafe_memory.free_calls != 0 ||
      unsafe_fixture.code[unsafe_fixture.kPatchOffset] != 0x49 ||
      unsafe_fixture.code[unsafe_fixture.kPatchOffset + 1] != 0xBB ||
      ReadU64(unsafe_fixture.code + unsafe_fixture.kPatchOffset + 2) !=
          reinterpret_cast<std::uintptr_t>(unsafe_state.stub) ||
      (unsafe_state.failure_flags.load() &
       startup_particle2_null_guard_failure_flush) == 0 ||
      (unsafe_state.failure_flags.load() &
       startup_particle2_null_guard_failure_rollback) == 0) {
    return false;
  }
  return true;
}

bool TestFrozenExecutableAndSourceContract(int argc, char **argv) {
  using namespace xar::bridge;
  g_failure_stage = "source_contract_arguments";
  if (argc != 6) {
    return false;
  }
  const auto header = ReadFile(argv[1]);
  const auto source = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto fixture = ReadFile(argv[4]);
  const auto executable = ReadFile(argv[5]);
  if (!StrictUtf8WithoutReplacement(header) ||
      !StrictUtf8WithoutReplacement(source) ||
      !StrictUtf8WithoutReplacement(abi) ||
      !StrictUtf8WithoutReplacement(fixture) || executable.empty()) {
    return false;
  }

  g_failure_stage = "source_contract_tokens";
  const std::array<std::string_view, 12> header_tokens{
      "kStartupParticle2NullGuardPatchRvaV1 =",
      "0x1DABD6D",
      "kStartupParticle2NullGuardContinueRvaV1 =",
      "0x1DABD82",
      "kStartupParticle2NullGuardSkipRvaV1 =",
      "0x1DABEA0",
      "kStartupParticle2RootSlotRvaV1 = 0x570F908",
      "kStartupParticle2NullGuardPatchBytesV1 = 13",
      "kStartupParticle2NullGuardInstalledByDefaultV1 = false",
      "primary_thread_suspended_proven",
      "suppressed_index_mask",
      "kStartupParticle2NoSuppressedIndexV1"};
  for (const auto token : header_tokens) {
    if (!Contains(header, token)) {
      return false;
    }
  }
  const std::array<std::string_view, 8> source_tokens{
      "mov r11, imm64; jmp r11",
      "mov r14, [r11 + rbp*8 + 0xa8]",
      "BuildStub",
      "ExactAnchorsMatch",
      "WriteTargetTransaction",
      "startup_particle2_null_guard_failure_rollback",
      "MEM_RESERVE | MEM_COMMIT",
      "PAGE_EXECUTE_READ"};
  for (const auto token : source_tokens) {
    if (!Contains(source, token)) {
      return false;
    }
  }
  const std::array<std::string_view, 12> contract_tokens{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x1DABD50",
      "0x1DABD6D",
      "0x1DABD82",
      "0x1DABEA0",
      "0x570F908",
      "0xA8 + index * 8",
      "13",
      "130",
      "0x1D",
      "installed_by_default",
      "transactional_rollback"};
  for (const auto token : contract_tokens) {
    if (!Contains(abi, token) || !Contains(fixture, token)) {
      return false;
    }
  }

  g_failure_stage = "frozen_executable_hash";
  std::string sha256;
  if (!Sha256Upper(executable, sha256) ||
      sha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86") {
    return false;
  }

  g_failure_stage = "frozen_executable_bytes";
  if (!BytesAt(executable, 0x1DABD50,
               {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
                0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x48,
                0x89, 0x7C, 0x24, 0x20, 0x41, 0x56, 0x48, 0x81,
                0xEC, 0x80, 0x08, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1DABD6D,
               {0x0F, 0xB6, 0xEA, 0x48, 0x8B, 0xD9, 0x48,
                0x8B, 0x05, 0x8E, 0x3B, 0x96, 0x03, 0x4C,
                0x8B, 0xB4, 0xE8, 0xA8, 0x00, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1DABEA0,
               {0x4C, 0x8D, 0x9C, 0x24, 0x80, 0x08, 0x00, 0x00,
                0x49, 0x8B, 0x5B, 0x10, 0x49, 0x8B, 0x6B, 0x18,
                0x49, 0x8B, 0x73, 0x20, 0x49, 0x8B, 0x7B, 0x28,
                0x49, 0x8B, 0xE3, 0x41, 0x5E, 0xC3})) {
    return false;
  }

  // Exact .pdata row and UNWIND_INFO header. The patch is therefore at
  // BeginAddress + SizeOfProlog, never inside the unwind-described prologue.
  g_failure_stage = "frozen_executable_unwind";
  return BytesAt(executable, 0x598B3B0,
                 {0x50, 0xBD, 0xDA, 0x01, 0xBE, 0xBE, 0xDA, 0x01,
                  0x84, 0xBE, 0xD2, 0x04}) &&
      BytesAt(executable, 0x4D2BE84, {0x11, 0x1D, 0x0B, 0x00}) &&
      kStartupParticle2NullGuardPatchRvaV1 ==
          kStartupParticle2RegistrationFunctionRvaV1 +
              kStartupParticle2RegistrationPrologueBytesV1;
}

} // namespace

int main(int argc, char **argv) {
  if (!TestAdmissionAndAnchorRejection() || !TestExecutableGuard() ||
      !TestAllocationAndTransactionalRollback() ||
      !TestFrozenExecutableAndSourceContract(argc, argv)) {
    std::fprintf(stderr, "startup particle2 null guard failure: %s\n",
                 g_failure_stage);
    return 1;
  }
  return 0;
}
