#include "xar_bridge/startup_localize_current_root_guard_v1.hpp"

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

constexpr std::array<std::uint8_t, 13> kPatchAnchor{
    0x48, 0x8B, 0x05, 0x4B, 0x55, 0xD7, 0x01,
    0x48, 0x8B, 0x18, 0x0F, 0x10, 0x0A};

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
  const auto size = static_cast<int>(input.size());
  const int required = MultiByteToWideChar(
      CP_UTF8, MB_ERR_INVALID_CHARS, input.data(), size, nullptr, 0);
  if (required <= 0) {
    return false;
  }
  std::vector<wchar_t> decoded(static_cast<std::size_t>(required));
  return MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, input.data(),
                             size, decoded.data(), required) == required &&
      std::none_of(decoded.begin(), decoded.end(),
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

struct PeSection {
  std::uint32_t virtual_size = 0;
  std::uint32_t virtual_address = 0;
  std::uint32_t raw_size = 0;
  std::uint32_t raw_offset = 0;
  std::uint32_t characteristics = 0;
};

bool ParsePe(std::string_view image, std::size_t &optional_header,
             std::vector<PeSection> &sections) {
  std::uint32_t pe_offset = 0;
  if (image.size() < 0x40 || image.substr(0, 2) != "MZ" ||
      !ReadInteger(image, 0x3C, pe_offset) || pe_offset > image.size() - 24 ||
      image.substr(pe_offset, 4) != std::string_view{"PE\0\0", 4}) {
    return false;
  }
  std::uint16_t section_count = 0;
  std::uint16_t optional_size = 0;
  if (!ReadInteger(image, pe_offset + 6, section_count) ||
      !ReadInteger(image, pe_offset + 20, optional_size) ||
      section_count == 0 || section_count > 128) {
    return false;
  }
  optional_header = static_cast<std::size_t>(pe_offset) + 24;
  std::uint16_t magic = 0;
  if (!ReadInteger(image, optional_header, magic) || magic != 0x20B) {
    return false;
  }
  const auto table = optional_header + optional_size;
  if (table > image.size() ||
      static_cast<std::size_t>(section_count) >
          (image.size() - table) / 40) {
    return false;
  }
  sections.clear();
  for (std::uint16_t index = 0; index < section_count; ++index) {
    const auto row = table + static_cast<std::size_t>(index) * 40;
    PeSection section{};
    if (!ReadInteger(image, row + 8, section.virtual_size) ||
        !ReadInteger(image, row + 12, section.virtual_address) ||
        !ReadInteger(image, row + 16, section.raw_size) ||
        !ReadInteger(image, row + 20, section.raw_offset) ||
        !ReadInteger(image, row + 36, section.characteristics)) {
      return false;
    }
    sections.push_back(section);
  }
  return true;
}

std::optional<std::size_t> RvaToOffset(
    std::string_view image, const std::vector<PeSection> &sections,
    std::uint32_t rva) {
  for (const auto &section : sections) {
    const auto mapped_size = std::max(section.virtual_size, section.raw_size);
    if (rva < section.virtual_address ||
        rva - section.virtual_address >= mapped_size) {
      continue;
    }
    const auto delta = static_cast<std::size_t>(rva - section.virtual_address);
    if (delta >= section.raw_size || section.raw_offset > image.size() ||
        delta > image.size() - section.raw_offset) {
      return std::nullopt;
    }
    return static_cast<std::size_t>(section.raw_offset) + delta;
  }
  return std::nullopt;
}

bool BytesAt(std::string_view image, const std::vector<PeSection> &sections,
             std::uint32_t rva,
             std::initializer_list<std::uint8_t> expected) {
  const auto offset = RvaToOffset(image, sections, rva);
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
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size,
                         nullptr, 0, 0) < 0 ||
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

struct SyntheticLocalizeFunction {
  static constexpr std::size_t kAllocationBytes = 4096;
  static constexpr std::size_t kPatchOffset = 1;
  static constexpr std::size_t kContinueOffset =
      kPatchOffset + kPatchAnchor.size();

  std::uint8_t *code = nullptr;
  std::size_t native_miss_offset = 0;
  std::size_t raw_fallback_offset = 0;

  alignas(8) std::atomic<std::uint64_t> continuation_marker{0};
  alignas(8) std::atomic<std::uint64_t> native_miss_marker{0};
  alignas(8) std::atomic<std::uint64_t> raw_fallback_marker{0};
  alignas(8) std::uintptr_t observed_rcx = 0;
  alignas(8) std::uintptr_t observed_rdx = 0;
  alignas(8) std::uintptr_t observed_rbx = 0;
  alignas(8) std::array<std::uint8_t, 16> observed_xmm1{};
  alignas(8) std::uintptr_t current_root = 0;
  alignas(8) std::uintptr_t global_container_slot = 0;
  alignas(8) std::uint64_t root_object = 0xF00DFACE12345678ULL;

  static void EmitMovR11Imm(std::uint8_t *code, std::size_t &cursor,
                            std::uintptr_t value) {
    code[cursor++] = 0x49;
    code[cursor++] = 0xBB;
    WriteU64(code + cursor, value);
    cursor += sizeof(std::uint64_t);
  }

  static void EmitAtomicIncrement(std::uint8_t *code, std::size_t &cursor,
                                  std::atomic<std::uint64_t> &value) {
    EmitMovR11Imm(code, cursor, reinterpret_cast<std::uintptr_t>(&value));
    const std::array<std::uint8_t, 4> increment{
        0xF0, 0x49, 0xFF, 0x03}; // lock inc qword [r11]
    std::memcpy(code + cursor, increment.data(), increment.size());
    cursor += increment.size();
  }

  SyntheticLocalizeFunction() {
    global_container_slot = reinterpret_cast<std::uintptr_t>(&current_root);
    code = static_cast<std::uint8_t *>(
        VirtualAlloc(nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT,
                     PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0xCC, kAllocationBytes);
    code[0] = 0x53; // push rbx; the patch is inside an already-framed owner
    std::memcpy(code + kPatchOffset, kPatchAnchor.data(),
                kPatchAnchor.size());

    std::size_t cursor = kContinueOffset;
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rcx));
    const std::array<std::uint8_t, 3> store_rcx{0x49, 0x89, 0x0B};
    std::memcpy(code + cursor, store_rcx.data(), store_rcx.size());
    cursor += store_rcx.size();
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rdx));
    const std::array<std::uint8_t, 3> store_rdx{0x49, 0x89, 0x13};
    std::memcpy(code + cursor, store_rdx.data(), store_rdx.size());
    cursor += store_rdx.size();
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rbx));
    const std::array<std::uint8_t, 3> store_rbx{0x49, 0x89, 0x1B};
    std::memcpy(code + cursor, store_rbx.data(), store_rbx.size());
    cursor += store_rbx.size();
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(observed_xmm1.data()));
    const std::array<std::uint8_t, 4> store_xmm1{0x41, 0x0F, 0x11, 0x0B};
    std::memcpy(code + cursor, store_xmm1.data(), store_xmm1.size());
    cursor += store_xmm1.size();
    EmitAtomicIncrement(code, cursor, continuation_marker);
    code[cursor++] = 0x5B; // pop rbx
    code[cursor++] = 0xC3;

    native_miss_offset = cursor;
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rcx));
    std::memcpy(code + cursor, store_rcx.data(), store_rcx.size());
    cursor += store_rcx.size();
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rdx));
    std::memcpy(code + cursor, store_rdx.data(), store_rdx.size());
    cursor += store_rdx.size();
    EmitMovR11Imm(code, cursor,
                  reinterpret_cast<std::uintptr_t>(&observed_rbx));
    std::memcpy(code + cursor, store_rbx.data(), store_rbx.size());
    cursor += store_rbx.size();
    EmitAtomicIncrement(code, cursor, native_miss_marker);
    code[cursor++] = 0x49;
    code[cursor++] = 0xBB;
    const auto raw_target_immediate = cursor;
    cursor += sizeof(std::uint64_t);
    const std::array<std::uint8_t, 3> jump_r11{0x41, 0xFF, 0xE3};
    std::memcpy(code + cursor, jump_r11.data(), jump_r11.size());
    cursor += jump_r11.size();

    raw_fallback_offset = cursor;
    EmitAtomicIncrement(code, cursor, raw_fallback_marker);
    code[cursor++] = 0x5B; // pop rbx
    code[cursor++] = 0xC3;
    WriteU64(code + raw_target_immediate,
             reinterpret_cast<std::uintptr_t>(code + raw_fallback_offset));

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

  ~SyntheticLocalizeFunction() {
    if (code != nullptr) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
    }
  }

  SyntheticLocalizeFunction(const SyntheticLocalizeFunction &) = delete;
  SyntheticLocalizeFunction &operator=(const SyntheticLocalizeFunction &) =
      delete;

  bool valid() const noexcept { return code != nullptr; }

  xar::bridge::StartupLocalizeCurrentRootGuardV1Environment Environment() {
    xar::bridge::StartupLocalizeCurrentRootGuardV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x140000000ULL;
    environment.patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kPatchOffset);
    environment.global_container_slot_address_override =
        reinterpret_cast<std::uintptr_t>(&global_container_slot);
    environment.continue_target_override =
        reinterpret_cast<std::uintptr_t>(code + kContinueOffset);
    environment.native_miss_target_override =
        reinterpret_cast<std::uintptr_t>(code + native_miss_offset);
    return environment;
  }

  bool SetPatchByte(std::size_t offset, std::uint8_t value) noexcept {
    if (code == nullptr || offset >= kPatchAnchor.size()) {
      return false;
    }
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READWRITE,
                       &previous) == FALSE ||
        previous != PAGE_EXECUTE_READ) {
      return false;
    }
    code[kPatchOffset + offset] = value;
    const bool flushed = FlushInstructionCache(
        GetCurrentProcess(), code + kPatchOffset + offset, 1) != FALSE;
    DWORD ignored = 0;
    return VirtualProtect(code, kAllocationBytes, previous, &ignored) !=
               FALSE &&
        flushed;
  }

  void SetCurrentRoot(bool present) noexcept {
    current_root = present ? reinterpret_cast<std::uintptr_t>(&root_object) : 0;
  }

  void Invoke(void *context, const void *source) {
    using Function = void (*)(void *, const void *) noexcept;
    reinterpret_cast<Function>(code)(context, source);
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

bool FaultVirtualFlush(void *opaque, const void *address,
                       std::size_t size) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.flush_calls;
  if (memory.fail_flush_call != 0 &&
      memory.flush_calls == memory.fail_flush_call) {
    return false;
  }
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

void AddFaultCallbacks(
    xar::bridge::StartupLocalizeCurrentRootGuardV1Environment &environment,
    FaultInjectingMemory &memory) {
  environment.memory_context = &memory;
  environment.virtual_alloc_override = &FaultVirtualAlloc;
  environment.virtual_free_override = &FaultVirtualFree;
  environment.virtual_protect_override = &FaultVirtualProtect;
  environment.flush_instruction_cache_override = &FaultVirtualFlush;
}

bool IsOriginal(const SyntheticLocalizeFunction &fixture) {
  return std::memcmp(fixture.code + SyntheticLocalizeFunction::kPatchOffset,
                     kPatchAnchor.data(), kPatchAnchor.size()) == 0;
}

bool TestAdmissionAndAnchorRejection() {
  using namespace xar::bridge;
  g_failure_stage = "admission_exact_build";
  StartupLocalizeCurrentRootGuardV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;
  StartupLocalizeCurrentRootGuardV1State exact_state{};
  if (InstallStartupLocalizeCurrentRootGuardV1(exact_state, environment) ||
      (exact_state.failure_flags.load() &
       startup_localize_current_root_guard_failure_exact_build) == 0) {
    return false;
  }

  g_failure_stage = "admission_suspended";
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  StartupLocalizeCurrentRootGuardV1State suspended_state{};
  if (InstallStartupLocalizeCurrentRootGuardV1(suspended_state,
                                                environment) ||
      (suspended_state.failure_flags.load() &
       startup_localize_current_root_guard_failure_primary_thread_suspended) ==
          0) {
    return false;
  }

  g_failure_stage = "admission_override";
  environment.primary_thread_suspended_proven = true;
  environment.patch_target_override = 1;
  StartupLocalizeCurrentRootGuardV1State override_state{};
  if (InstallStartupLocalizeCurrentRootGuardV1(override_state, environment) ||
      (override_state.failure_flags.load() &
       startup_localize_current_root_guard_failure_unsupported_override) ==
          0) {
    return false;
  }

  g_failure_stage = "anchor_drift";
  SyntheticLocalizeFunction fixture;
  if (!fixture.valid() || !fixture.SetPatchByte(6, 0x02)) {
    return false;
  }
  const auto fixture_environment = fixture.Environment();
  StartupLocalizeCurrentRootGuardV1State drift_state{};
  return !InstallStartupLocalizeCurrentRootGuardV1(drift_state,
                                                    fixture_environment) &&
      (drift_state.failure_flags.load() &
       startup_localize_current_root_guard_failure_anchor) != 0 &&
      drift_state.stub == nullptr && !IsOriginal(fixture);
}

bool TestExecutableGuard() {
  using namespace xar::bridge;
  g_failure_stage = "executable_install";
  SyntheticLocalizeFunction fixture;
  if (!fixture.valid()) {
    return false;
  }
  StartupLocalizeCurrentRootGuardV1State state{};
  const auto environment = fixture.Environment();
  if (!InstallStartupLocalizeCurrentRootGuardV1(state, environment)) {
    return false;
  }
  const auto *patch = fixture.code + SyntheticLocalizeFunction::kPatchOffset;
  if (state.original_patch_bytes != kPatchAnchor ||
      state.installed_patch_bytes[0] != 0x49 ||
      state.installed_patch_bytes[1] != 0xBB ||
      state.installed_patch_bytes[10] != 0x41 ||
      state.installed_patch_bytes[11] != 0xFF ||
      state.installed_patch_bytes[12] != 0xE3 ||
      std::memcmp(patch, state.installed_patch_bytes.data(),
                  state.installed_patch_bytes.size()) != 0) {
    return false;
  }
  std::uint64_t embedded_stub = 0;
  std::memcpy(&embedded_stub, patch + 2, sizeof(embedded_stub));
  MEMORY_BASIC_INFORMATION stub_memory{};
  MEMORY_BASIC_INFORMATION target_memory{};
  if (embedded_stub != reinterpret_cast<std::uintptr_t>(state.stub) ||
      VirtualQuery(state.stub, &stub_memory, sizeof(stub_memory)) == 0 ||
      stub_memory.Protect != PAGE_EXECUTE_READ ||
      VirtualQuery(patch, &target_memory, sizeof(target_memory)) == 0 ||
      target_memory.Protect != PAGE_EXECUTE_READ) {
    return false;
  }

  g_failure_stage = "executable_healthy_replay_and_registers";
  fixture.SetCurrentRoot(true);
  const std::array<std::uint8_t, 16> source{
      0x10, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE,
      0xEF, 0xCD, 0xAB, 0x89, 0x67, 0x45, 0x23, 0x01};
  void *const context = &fixture.root_object;
  fixture.Invoke(context, source.data());
  auto diagnostics =
      ReadStartupLocalizeCurrentRootGuardV1Diagnostics(state);
  if (fixture.continuation_marker.load() != 1 ||
      fixture.native_miss_marker.load() != 0 ||
      fixture.raw_fallback_marker.load() != 0 ||
      diagnostics.native_miss_count != 0 ||
      fixture.observed_rcx != reinterpret_cast<std::uintptr_t>(context) ||
      fixture.observed_rdx !=
          reinterpret_cast<std::uintptr_t>(source.data()) ||
      fixture.observed_rbx != fixture.current_root ||
      fixture.observed_xmm1 != source) {
    return false;
  }

  g_failure_stage = "executable_null_root_native_raw_fallback";
  fixture.SetCurrentRoot(false);
  const auto container_before = fixture.global_container_slot;
  fixture.observed_rcx = 0;
  fixture.observed_rdx = 1;
  fixture.observed_rbx = 1;
  fixture.Invoke(context, nullptr);
  diagnostics = ReadStartupLocalizeCurrentRootGuardV1Diagnostics(state);
  if (fixture.continuation_marker.load() != 1 ||
      fixture.native_miss_marker.load() != 1 ||
      fixture.raw_fallback_marker.load() != 1 ||
      diagnostics.native_miss_count != 1 ||
      fixture.observed_rcx != reinterpret_cast<std::uintptr_t>(context) ||
      fixture.observed_rdx != 0 || fixture.observed_rbx != 0 ||
      fixture.global_container_slot != container_before ||
      fixture.current_root != 0 || fixture.observed_xmm1 != source) {
    return false;
  }

  g_failure_stage = "executable_uninstall";
  return UninstallStartupLocalizeCurrentRootGuardV1(state) &&
      state.stub == nullptr && state.installed.load() == 0 &&
      IsOriginal(fixture);
}

bool TestTransactionalRollback() {
  using namespace xar::bridge;
  g_failure_stage = "rollback_allocation";
  {
    SyntheticLocalizeFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_allocation = true;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupLocalizeCurrentRootGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupLocalizeCurrentRootGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_allocation) == 0) {
      return false;
    }
  }

  g_failure_stage = "rollback_stub_protect";
  {
    SyntheticLocalizeFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_protect_call = 1;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupLocalizeCurrentRootGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupLocalizeCurrentRootGuardV1(state, environment) ||
        state.stub != nullptr || memory.free_calls != 1 ||
        !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_stub_protection) == 0) {
      return false;
    }
  }

  g_failure_stage = "rollback_target_protect";
  {
    SyntheticLocalizeFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_protect_call = 2;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupLocalizeCurrentRootGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupLocalizeCurrentRootGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_target_protection) == 0) {
      return false;
    }
  }

  g_failure_stage = "rollback_flush_restores_original";
  {
    SyntheticLocalizeFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_flush_call = 2;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupLocalizeCurrentRootGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupLocalizeCurrentRootGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        memory.free_calls != 1 ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_flush) == 0 ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_rollback) != 0) {
      return false;
    }
  }

  // Keep last: rollback is deliberately unprovable. The target still reaches
  // the RX stub, so the component must retain installed ownership until exit.
  g_failure_stage = "rollback_failure_retains_reachable_stub";
  {
    SyntheticLocalizeFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_flush_call = 2;
    memory.fail_protect_call = 3;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupLocalizeCurrentRootGuardV1State state{};
    const auto *patch =
        fixture.code + SyntheticLocalizeFunction::kPatchOffset;
    if (!fixture.valid() ||
        InstallStartupLocalizeCurrentRootGuardV1(state, environment) ||
        state.installed.load() == 0 || state.stub == nullptr ||
        std::memcmp(patch, state.installed_patch_bytes.data(),
                    state.installed_patch_bytes.size()) != 0 ||
        (state.failure_flags.load() &
         startup_localize_current_root_guard_failure_rollback) == 0 ||
        memory.free_calls != 0) {
      return false;
    }
  }
  return true;
}

bool HasExactPdataRow(std::string_view image, std::size_t optional_header,
                      const std::vector<PeSection> &sections) {
  std::uint32_t exception_rva = 0;
  std::uint32_t exception_size = 0;
  if (!ReadInteger(image, optional_header + 112 + 3 * 8, exception_rva) ||
      !ReadInteger(image, optional_header + 112 + 3 * 8 + 4,
                   exception_size)) {
    return false;
  }
  const auto offset = RvaToOffset(image, sections, exception_rva);
  if (!offset || exception_size % 12 != 0 ||
      exception_size > image.size() - *offset) {
    return false;
  }
  std::uint32_t matches = 0;
  for (std::size_t cursor = *offset;
       cursor < *offset + exception_size; cursor += 12) {
    std::uint32_t begin = 0;
    std::uint32_t end = 0;
    std::uint32_t unwind = 0;
    if (!ReadInteger(image, cursor, begin) ||
        !ReadInteger(image, cursor + 4, end) ||
        !ReadInteger(image, cursor + 8, unwind)) {
      return false;
    }
    if (begin == 0x3A6A410 && end == 0x3A6A6D5 &&
        unwind == 0x4EF30D8) {
      ++matches;
    }
  }
  return matches == 1;
}

bool RipRelativeTarget(std::string_view image,
                       const std::vector<PeSection> &sections,
                       std::uint32_t instruction_rva,
                       std::size_t displacement_offset,
                       std::size_t instruction_size,
                       std::uint32_t &target) {
  const auto offset = RvaToOffset(image, sections, instruction_rva);
  std::int32_t displacement = 0;
  if (!offset ||
      !ReadInteger(image, *offset + displacement_offset, displacement)) {
    return false;
  }
  const auto resolved = static_cast<std::int64_t>(instruction_rva) +
      static_cast<std::int64_t>(instruction_size) + displacement;
  if (resolved < 0 ||
      resolved > std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  target = static_cast<std::uint32_t>(resolved);
  return true;
}

bool TestFrozenExecutableAndContracts(int argc, char **argv) {
  using namespace xar::bridge;
  if (argc != 8) {
    g_failure_stage = "contract_arguments";
    return false;
  }
  const auto header = ReadFile(argv[1]);
  const auto source = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto fixture = ReadFile(argv[4]);
  const auto executable = ReadFile(argv[5]);
  const auto cmake = ReadFile(argv[6]);
  const auto bridge = ReadFile(argv[7]);
  g_failure_stage = "contract_utf8";
  if (!StrictUtf8WithoutReplacement(header) ||
      !StrictUtf8WithoutReplacement(source) ||
      !StrictUtf8WithoutReplacement(abi) ||
      !StrictUtf8WithoutReplacement(fixture) ||
      !StrictUtf8WithoutReplacement(cmake) ||
      !StrictUtf8WithoutReplacement(bridge)) {
    return false;
  }
  const std::array<std::string_view, 22> tokens{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x3A6A410", "0x3A6A4D6", "0x3A6A4E3", "0x57DFA28",
      "0x3A6A51A", "0x3A6A67F", "0x3A70610", "0x3A6B250",
      "0x3A6B3DA", "0x3A6C070", "0x3A6C350", "0x5AACC04",
      "0x4EF30D8", "SizeOfProlog", "0x2B", "13", "64",
      "RCX", "RDX", "transactional_rollback", "installed_by_default"};
  for (const auto token : tokens) {
    if (!Contains(abi, token) || !Contains(fixture, token)) {
      g_failure_stage = "contract_tokens";
      return false;
    }
  }
  if (!Contains(source, "PAGE_EXECUTE_READ") ||
      !Contains(source, "rollback_unproven") ||
      !Contains(source, "without touching RCX") ||
      !Contains(source, "movups xmm1, [rdx]") ||
      !Contains(fixture, "null current root skips movups") ||
      !Contains(fixture, "generic lookup is never patched") ||
      !Contains(cmake, "src/startup_localize_current_root_guard_v1.cpp") ||
      !Contains(cmake,
                "xar_ck3_startup_localize_current_root_guard_v1_test")) {
    g_failure_stage = "source_tokens";
    return false;
  }

  g_failure_stage = "bridge_wiring";
  const auto producer_install =
      bridge.find("InstallStartupParticle2NullGuardV1");
  const auto consumer_install =
      bridge.find("InstallStartupParticle2ConsumerGuardV1");
  const auto draw_install =
      bridge.find("InstallStartupDx11RenderContextDrawGuardV1");
  const auto localize_install =
      bridge.find("InstallStartupLocalizeCurrentRootGuardV1");
  if (!Contains(bridge,
                "xar_bridge/startup_localize_current_root_guard_v1.hpp") ||
      !Contains(bridge, "ReadStartupLocalizeCurrentRootGuardV1Diagnostics") ||
      !Contains(bridge, "startup_localize_current_root_guard_v1") ||
      !Contains(bridge, "native_miss_count") ||
      !Contains(bridge,
                "constexpr bool kStartupFailureContainmentEnabledV1 = false") ||
      !Contains(bridge, "startup_failure_containment_enabled") ||
      !Contains(bridge, "if (!kStartupFailureContainmentEnabledV1)") ||
      !Contains(bridge, "UninstallStartupDx11RenderContextDrawGuardV1") ||
      !Contains(bridge,
                "UninstallStartupParticle2ConsumerGuardV1") ||
      !Contains(bridge, "UninstallStartupParticle2NullGuardV1") ||
      producer_install == std::string::npos ||
      consumer_install == std::string::npos ||
      draw_install == std::string::npos ||
      localize_install == std::string::npos ||
      !(producer_install < consumer_install && consumer_install < draw_install &&
        draw_install < localize_install)) {
    return false;
  }

  g_failure_stage = "frozen_hash";
  std::string sha256;
  if (!Sha256Upper(executable, sha256) ||
      sha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86") {
    return false;
  }
  std::size_t optional_header = 0;
  std::vector<PeSection> sections;
  if (!ParsePe(executable, optional_header, sections)) {
    return false;
  }

  g_failure_stage = "frozen_entry_pdata_unwind";
  const auto patch_offset = RvaToOffset(executable, sections, 0x3A6A4D6);
  if (!patch_offset ||
      !std::equal(kPatchAnchor.begin(), kPatchAnchor.end(),
                  reinterpret_cast<const std::uint8_t *>(executable.data()) +
                      *patch_offset) ||
      !HasExactPdataRow(executable, optional_header, sections) ||
      !BytesAt(executable, sections, 0x5AACC04,
               {0x10, 0xA4, 0xA6, 0x03, 0xD5, 0xA6, 0xA6, 0x03,
                0xD8, 0x30, 0xEF, 0x04}) ||
      !BytesAt(executable, sections, 0x4EF30D8,
               {0x11, 0x2B, 0x0F, 0x00}) ||
      kStartupLocalizeCurrentRootPatchRvaV1 -
              kStartupLocalizeCurrentRootOwnerRvaV1 <=
          0x2B ||
      kStartupLocalizeCurrentRootContinueRvaV1 !=
          kStartupLocalizeCurrentRootPatchRvaV1 +
              kStartupLocalizeCurrentRootPatchBytesV1) {
    return false;
  }

  g_failure_stage = "frozen_global_and_owner_callgraph";
  std::uint32_t target = 0;
  if (!RipRelativeTarget(executable, sections, 0x3A6A4D6, 3, 7, target) ||
      target != 0x57DFA28 ||
      !BytesAt(executable, sections, 0x3A6A506,
               {0xE8, 0x05, 0x61, 0x00, 0x00}) ||
      !RipRelativeTarget(executable, sections, 0x3A6A506, 1, 5, target) ||
      target != 0x3A70610 ||
      !BytesAt(executable, sections, 0x3A70610,
               {0x4C, 0x8B, 0x59, 0x08, 0x4C, 0x8B, 0xC9,
                0x0F, 0xB6, 0x02, 0x4C, 0x63, 0x51, 0x14})) {
    return false;
  }

  g_failure_stage = "frozen_native_miss_to_raw_fallback";
  if (!BytesAt(executable, sections, 0x3A6A50B,
               {0x48, 0x85, 0xC0, 0x74, 0x0A}) ||
      !BytesAt(executable, sections, 0x3A6A51A,
               {0x4C, 0x89, 0x6D, 0x9F, 0x44, 0x89, 0x6D, 0xA7,
                0xC6, 0x45, 0xAB, 0x01}) ||
      !BytesAt(executable, sections, 0x3A6A531,
               {0x66, 0x48, 0x0F, 0x7E, 0xC0, 0x48, 0x85, 0xC0,
                0x0F, 0x84, 0x40, 0x01, 0x00, 0x00}) ||
      !BytesAt(executable, sections, 0x3A6A67F,
               {0x4C, 0x63, 0x46, 0x08, 0x48, 0x8B, 0x16,
                0x4C, 0x89, 0x2F, 0x4C, 0x89, 0x6F, 0x10})) {
    return false;
  }

  g_failure_stage = "frozen_producers";
  if (!BytesAt(executable, sections, 0x3A6B250,
               {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10}) ||
      !BytesAt(executable, sections, 0x3A6B398,
               {0x4C, 0x89, 0x38, 0x4C, 0x89, 0x78, 0x08,
                0x4C, 0x89, 0x78, 0x10}) ||
      !BytesAt(executable, sections, 0x3A6B3DA,
               {0x48, 0x89, 0x1D, 0x47, 0x46, 0xD7, 0x01}) ||
      !RipRelativeTarget(executable, sections, 0x3A6B3DA, 3, 7, target) ||
      target != 0x57DFA28 ||
      !BytesAt(executable, sections, 0x3A6C070,
               {0x48, 0x89, 0x5C, 0x24, 0x10,
                0x48, 0x89, 0x74, 0x24, 0x18}) ||
      !BytesAt(executable, sections, 0x3A6C338,
               {0x48, 0x8B, 0x1D, 0xE9, 0x36, 0xD7, 0x01}) ||
      !RipRelativeTarget(executable, sections, 0x3A6C338, 3, 7, target) ||
      target != 0x57DFA28 ||
      !BytesAt(executable, sections, 0x3A6C344,
               {0x48, 0x8D, 0x55, 0xF7, 0x48, 0x8B, 0xCB,
                0xE8, 0xA0, 0x28, 0x00, 0x00, 0x48, 0x89, 0x03}) ||
      kStartupLocalizeCurrentRootNativeMissRvaV1 != 0x3A6A51A ||
      kStartupLocalizeCurrentRootRawKeyFallbackRvaV1 != 0x3A6A67F) {
    return false;
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (!TestAdmissionAndAnchorRejection() || !TestExecutableGuard() ||
      !TestFrozenExecutableAndContracts(argc, argv) ||
      !TestTransactionalRollback()) {
    std::fprintf(stderr, "startup localization root guard failure: %s\n",
                 g_failure_stage);
    return 1;
  }
  return 0;
}
