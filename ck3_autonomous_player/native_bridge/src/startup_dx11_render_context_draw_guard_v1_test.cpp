#include "xar_bridge/startup_dx11_render_context_draw_guard_v1.hpp"

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

constexpr std::array<std::uint8_t, 15> kPatchAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08,
    0x48, 0x89, 0x74, 0x24, 0x10,
    0x57, 0x48, 0x83, 0xEC, 0x20};
constexpr std::array<std::uint8_t, 46> kProductionAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
    0x57, 0x48, 0x83, 0xEC, 0x20, 0x41, 0x8B, 0xF8, 0x8B, 0xF2,
    0x48, 0x8B, 0xD9, 0xE8, 0x14, 0xFD, 0xFF, 0xFF, 0x48, 0x8B,
    0x8B, 0x30, 0x19, 0x00, 0x00, 0x44, 0x8B, 0xC7, 0x8B, 0xD6,
    0x48, 0x8B, 0x01, 0xFF, 0x50, 0x68};

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

bool TextAt(std::string_view image, const std::vector<PeSection> &sections,
            std::uint32_t rva, std::string_view expected) {
  const auto offset = RvaToOffset(image, sections, rva);
  return offset && *offset <= image.size() &&
      expected.size() <= image.size() - *offset &&
      image.substr(*offset, expected.size()) == expected;
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

struct SyntheticDrawContext {
  alignas(8) std::array<std::uint8_t, 0x1948> bytes{};

  void SetDirty(std::uint8_t value) noexcept {
    bytes[xar::bridge::kStartupDx11RenderContextDrawDirtyOffsetV1] = value;
  }

  std::uint8_t Dirty() const noexcept {
    return bytes[xar::bridge::kStartupDx11RenderContextDrawDirtyOffsetV1];
  }

  void SetShaderState(std::uintptr_t value) noexcept {
    std::memcpy(
        bytes.data() +
            xar::bridge::kStartupDx11RenderContextDrawShaderStateOffsetV1,
        &value, sizeof(value));
  }
};

struct SyntheticDrawFunction {
  static constexpr std::size_t kAllocationBytes = 4096;
  static constexpr std::size_t kContinueOffset = 15;

  std::uint8_t *code = nullptr;
  alignas(8) std::atomic<std::uint64_t> continuation_marker{0};

  SyntheticDrawFunction() {
    code = static_cast<std::uint8_t *>(
        VirtualAlloc(nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT,
                     PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0xCC, kAllocationBytes);
    std::memcpy(code, kPatchAnchor.data(), kPatchAnchor.size());
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
    const std::array<std::uint8_t, 15> epilogue{
        0x48, 0x83, 0xC4, 0x20,       // add rsp, 20
        0x5F,                         // pop rdi
        0x48, 0x8B, 0x5C, 0x24, 0x08, // mov rbx, [rsp+08]
        0x48, 0x8B, 0x74, 0x24, 0x10  // mov rsi, [rsp+10]
    };
    std::memcpy(code + cursor, epilogue.data(), epilogue.size());
    cursor += epilogue.size();
    code[cursor++] = 0xC3;
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

  ~SyntheticDrawFunction() {
    if (code != nullptr) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
    }
  }

  SyntheticDrawFunction(const SyntheticDrawFunction &) = delete;
  SyntheticDrawFunction &operator=(const SyntheticDrawFunction &) = delete;

  bool valid() const noexcept { return code != nullptr; }

  xar::bridge::StartupDx11RenderContextDrawGuardV1Environment Environment() {
    xar::bridge::StartupDx11RenderContextDrawGuardV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x140000000ULL;
    environment.patch_target_override =
        reinterpret_cast<std::uintptr_t>(code);
    environment.continue_target_override =
        reinterpret_cast<std::uintptr_t>(code + kContinueOffset);
    return environment;
  }

  bool SetEntryByte(std::size_t offset, std::uint8_t value) noexcept {
    if (code == nullptr || offset >= kPatchAnchor.size()) {
      return false;
    }
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READWRITE,
                       &previous) == FALSE ||
        previous != PAGE_EXECUTE_READ) {
      return false;
    }
    code[offset] = value;
    const bool flushed =
        FlushInstructionCache(GetCurrentProcess(), code + offset, 1) != FALSE;
    DWORD ignored = 0;
    return VirtualProtect(code, kAllocationBytes, previous, &ignored) !=
               FALSE &&
        flushed;
  }

  void Invoke(SyntheticDrawContext &context) {
    using Function = void (*)(void *, std::uint32_t, std::uint32_t) noexcept;
    reinterpret_cast<Function>(code)(context.bytes.data(), 7, 11);
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
    xar::bridge::StartupDx11RenderContextDrawGuardV1Environment &environment,
    FaultInjectingMemory &memory) {
  environment.memory_context = &memory;
  environment.virtual_alloc_override = &FaultVirtualAlloc;
  environment.virtual_free_override = &FaultVirtualFree;
  environment.virtual_protect_override = &FaultVirtualProtect;
  environment.flush_instruction_cache_override = &FaultVirtualFlush;
}

bool IsOriginal(const SyntheticDrawFunction &fixture) {
  return std::memcmp(fixture.code, kPatchAnchor.data(), kPatchAnchor.size()) ==
         0;
}

bool TestAdmissionAndAnchorRejection() {
  using namespace xar::bridge;
  g_failure_stage = "admission_exact_build";
  StartupDx11RenderContextDrawGuardV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;
  StartupDx11RenderContextDrawGuardV1State exact_state{};
  if (InstallStartupDx11RenderContextDrawGuardV1(exact_state, environment) ||
      (exact_state.failure_flags.load() &
       startup_dx11_render_context_draw_guard_failure_exact_build) == 0) {
    return false;
  }

  g_failure_stage = "admission_suspended";
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  StartupDx11RenderContextDrawGuardV1State suspended_state{};
  if (InstallStartupDx11RenderContextDrawGuardV1(suspended_state,
                                                  environment) ||
      (suspended_state.failure_flags.load() &
       startup_dx11_render_context_draw_guard_failure_primary_thread_suspended) ==
          0) {
    return false;
  }

  g_failure_stage = "admission_override";
  environment.primary_thread_suspended_proven = true;
  environment.patch_target_override = 1;
  StartupDx11RenderContextDrawGuardV1State override_state{};
  if (InstallStartupDx11RenderContextDrawGuardV1(override_state, environment) ||
      (override_state.failure_flags.load() &
       startup_dx11_render_context_draw_guard_failure_unsupported_override) ==
          0) {
    return false;
  }

  g_failure_stage = "anchor_drift";
  SyntheticDrawFunction fixture;
  if (!fixture.valid() || !fixture.SetEntryByte(11, 0x49)) {
    return false;
  }
  auto fixture_environment = fixture.Environment();
  StartupDx11RenderContextDrawGuardV1State drift_state{};
  return !InstallStartupDx11RenderContextDrawGuardV1(drift_state,
                                                      fixture_environment) &&
      (drift_state.failure_flags.load() &
       startup_dx11_render_context_draw_guard_failure_anchor) != 0 &&
      drift_state.stub == nullptr && !IsOriginal(fixture);
}

bool TestExecutableGuard() {
  using namespace xar::bridge;
  g_failure_stage = "executable_install";
  SyntheticDrawFunction fixture;
  SyntheticDrawContext context{};
  if (!fixture.valid()) {
    return false;
  }
  StartupDx11RenderContextDrawGuardV1State state{};
  const auto environment = fixture.Environment();
  if (!InstallStartupDx11RenderContextDrawGuardV1(state, environment)) {
    return false;
  }
  if (state.original_patch_bytes != kPatchAnchor ||
      state.installed_patch_bytes[0] != 0x49 ||
      state.installed_patch_bytes[1] != 0xBB ||
      state.installed_patch_bytes[10] != 0x41 ||
      state.installed_patch_bytes[11] != 0xFF ||
      state.installed_patch_bytes[12] != 0xE3 ||
      state.installed_patch_bytes[13] != 0x90 ||
      state.installed_patch_bytes[14] != 0x90 ||
      std::memcmp(fixture.code, state.installed_patch_bytes.data(),
                  state.installed_patch_bytes.size()) != 0) {
    return false;
  }
  std::uint64_t embedded_stub = 0;
  std::memcpy(&embedded_stub, fixture.code + 2, sizeof(embedded_stub));
  MEMORY_BASIC_INFORMATION stub_memory{};
  MEMORY_BASIC_INFORMATION target_memory{};
  if (embedded_stub != reinterpret_cast<std::uintptr_t>(state.stub) ||
      VirtualQuery(state.stub, &stub_memory, sizeof(stub_memory)) == 0 ||
      stub_memory.Protect != PAGE_EXECUTE_READ ||
      VirtualQuery(fixture.code, &target_memory, sizeof(target_memory)) == 0 ||
      target_memory.Protect != PAGE_EXECUTE_READ) {
    return false;
  }

  g_failure_stage = "executable_dirty_state_nonnull";
  context.SetDirty(1);
  context.SetShaderState(1);
  fixture.Invoke(context);
  auto diagnostics =
      ReadStartupDx11RenderContextDrawGuardV1Diagnostics(state);
  if (fixture.continuation_marker.load() != 1 ||
      diagnostics.suppressed_count != 0 || context.Dirty() != 1) {
    return false;
  }

  g_failure_stage = "executable_dirty_state_null_preserves_dirty";
  context.SetDirty(1);
  context.SetShaderState(0);
  fixture.Invoke(context);
  diagnostics = ReadStartupDx11RenderContextDrawGuardV1Diagnostics(state);
  if (fixture.continuation_marker.load() != 1 ||
      diagnostics.suppressed_count != 1 || context.Dirty() != 1) {
    return false;
  }

  g_failure_stage = "executable_clean_state_null";
  context.SetDirty(0);
  context.SetShaderState(0);
  fixture.Invoke(context);
  diagnostics = ReadStartupDx11RenderContextDrawGuardV1Diagnostics(state);
  if (fixture.continuation_marker.load() != 2 ||
      diagnostics.suppressed_count != 1 || context.Dirty() != 0) {
    return false;
  }

  g_failure_stage = "executable_uninstall";
  if (!UninstallStartupDx11RenderContextDrawGuardV1(state) ||
      state.stub != nullptr || state.installed.load() != 0 ||
      !IsOriginal(fixture)) {
    return false;
  }
  context.SetDirty(1);
  fixture.Invoke(context);
  return fixture.continuation_marker.load() == 3 && context.Dirty() == 1;
}

bool TestTransactionalRollback() {
  using namespace xar::bridge;
  g_failure_stage = "rollback_allocation";
  {
    SyntheticDrawFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_allocation = true;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupDx11RenderContextDrawGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupDx11RenderContextDrawGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_allocation) == 0) {
      return false;
    }
  }

  g_failure_stage = "rollback_stub_protect";
  {
    SyntheticDrawFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_protect_call = 1;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupDx11RenderContextDrawGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupDx11RenderContextDrawGuardV1(state, environment) ||
        state.stub != nullptr || memory.free_calls != 1 ||
        !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_stub_protection) ==
            0) {
      return false;
    }
  }

  g_failure_stage = "rollback_target_protect";
  {
    SyntheticDrawFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_protect_call = 2;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupDx11RenderContextDrawGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupDx11RenderContextDrawGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_target_protection) ==
            0) {
      return false;
    }
  }

  g_failure_stage = "rollback_flush_restores_original";
  {
    SyntheticDrawFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_flush_call = 2;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupDx11RenderContextDrawGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupDx11RenderContextDrawGuardV1(state, environment) ||
        state.stub != nullptr || !IsOriginal(fixture) ||
        memory.free_calls != 1 ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_flush) == 0 ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_rollback) != 0) {
      return false;
    }
  }

  // Keep this last: rollback itself is deliberately made unprovable. The
  // global owner and executable stub must remain alive while the jump can reach
  // it. The process exits without invoking that deliberately retained patch.
  g_failure_stage = "rollback_failure_retains_reachable_stub";
  {
    SyntheticDrawFunction fixture;
    FaultInjectingMemory memory{};
    memory.fail_flush_call = 2;
    memory.fail_protect_call = 3;
    auto environment = fixture.Environment();
    AddFaultCallbacks(environment, memory);
    StartupDx11RenderContextDrawGuardV1State state{};
    if (!fixture.valid() ||
        InstallStartupDx11RenderContextDrawGuardV1(state, environment) ||
        state.installed.load() == 0 || state.stub == nullptr ||
        std::memcmp(fixture.code, state.installed_patch_bytes.data(),
                    state.installed_patch_bytes.size()) != 0 ||
        (state.failure_flags.load() &
         startup_dx11_render_context_draw_guard_failure_rollback) == 0 ||
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
    if (begin == 0x3B0B0F0 && end == 0x3B0B14F &&
        unwind == 0x4C395F0) {
      ++matches;
    }
  }
  return matches == 1;
}

std::vector<std::uint32_t> FindDirectXrefs(
    std::string_view image, const std::vector<PeSection> &sections,
    std::uint32_t target) {
  std::vector<std::uint32_t> output;
  for (const auto &section : sections) {
    if ((section.characteristics & 0x20000000U) == 0 ||
        section.raw_offset > image.size() ||
        section.raw_size > image.size() - section.raw_offset) {
      continue;
    }
    for (std::uint32_t index = 0; index + 5 <= section.raw_size; ++index) {
      const auto opcode = static_cast<std::uint8_t>(
          image[static_cast<std::size_t>(section.raw_offset) + index]);
      if (opcode != 0xE8 && opcode != 0xE9) {
        continue;
      }
      std::int32_t displacement = 0;
      if (!ReadInteger(image,
                       static_cast<std::size_t>(section.raw_offset) + index + 1,
                       displacement)) {
        continue;
      }
      const auto source = static_cast<std::int64_t>(section.virtual_address) +
                          index;
      if (source + 5 + displacement == target) {
        output.push_back(static_cast<std::uint32_t>(source));
      }
    }
  }
  std::sort(output.begin(), output.end());
  return output;
}

bool TestFrozenExecutableAndContracts(int argc, char **argv) {
  using namespace xar::bridge;
  if (argc != 7) {
    g_failure_stage = "contract_arguments";
    return false;
  }
  const auto header = ReadFile(argv[1]);
  const auto source = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto fixture = ReadFile(argv[4]);
  const auto executable = ReadFile(argv[5]);
  const auto bridge = ReadFile(argv[6]);
  g_failure_stage = "contract_utf8";
  if (!StrictUtf8WithoutReplacement(header) ||
      !StrictUtf8WithoutReplacement(source) ||
      !StrictUtf8WithoutReplacement(abi) ||
      !StrictUtf8WithoutReplacement(fixture) ||
      !StrictUtf8WithoutReplacement(bridge)) {
    return false;
  }
  const std::array<std::string_view, 16> tokens{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x3B0B0F0", "0x3B0B0FF", "0x3B0B107", "0x3B0AE20",
      "0x3465FE8", "0x130", "0x1938", "0x1940", "0x4C395F0",
      "SizeOfProlog", "0x0F", "15", "62", "transactional_rollback",
      "installed_by_default"};
  for (const auto token : tokens) {
    if (!Contains(abi, token) || !Contains(fixture, token)) {
      g_failure_stage = "contract_tokens";
      return false;
    }
  }
  if (!Contains(source, "PAGE_EXECUTE_READ") ||
      !Contains(source, "rollback_unproven") ||
      !Contains(source, "kStartupDx11RenderContextDrawDirtyOffsetV1 ==") ||
      !Contains(source,
                "kStartupDx11RenderContextDrawShaderStateOffsetV1 ==") ||
      !Contains(fixture, "preserves dirty exactly") ||
      !Contains(fixture, "dirty=0 and shader-state=null")) {
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
  if (!Contains(bridge,
                "xar_bridge/startup_dx11_render_context_draw_guard_v1.hpp") ||
      !Contains(bridge,
                "ReadStartupDx11RenderContextDrawGuardV1Diagnostics") ||
      !Contains(bridge, "startup_dx11_render_context_draw_guard_v1") ||
      !Contains(bridge,
                "UninstallStartupParticle2ConsumerGuardV1") ||
      !Contains(bridge, "UninstallStartupParticle2NullGuardV1") ||
      producer_install == std::string::npos ||
      consumer_install == std::string::npos ||
      draw_install == std::string::npos ||
      !(producer_install < consumer_install && consumer_install < draw_install)) {
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

  g_failure_stage = "frozen_entry_pdata";
  const auto entry_offset = RvaToOffset(executable, sections, 0x3B0B0F0);
  if (!entry_offset ||
      !std::equal(kProductionAnchor.begin(), kProductionAnchor.end(),
                  reinterpret_cast<const std::uint8_t *>(executable.data()) +
                      *entry_offset) ||
      !HasExactPdataRow(executable, optional_header, sections) ||
      !BytesAt(executable, sections, 0x4C395F0,
               {0x01, 0x0F, 0x06, 0x00}) ||
      kStartupDx11RenderContextDrawPatchBytesV1 != 0x0F) {
    return false;
  }

  g_failure_stage = "frozen_helper_predicate";
  if (!BytesAt(executable, sections, 0x3B0B107,
               {0xE8, 0x14, 0xFD, 0xFF, 0xFF}) ||
      !BytesAt(executable, sections, 0x3B0AE4B,
               {0xF6, 0x81, 0x38, 0x19, 0x00, 0x00, 0x01,
                0x0F, 0x84, 0x65, 0x02, 0x00, 0x00,
                0x4C, 0x8B, 0xB1, 0x40, 0x19, 0x00, 0x00}) ||
      !BytesAt(executable, sections, 0x3465FE8,
               {0xFF, 0x90, 0x30, 0x01, 0x00, 0x00})) {
    return false;
  }

  g_failure_stage = "frozen_rtti";
  constexpr std::string_view type_name{".?AVCGfxDX11RenderContext@@\0", 29};
  if (!TextAt(executable, sections, 0x56E9E08, type_name) ||
      !BytesAt(executable, sections, 0x4BF0948,
               {0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0xF8, 0x9D, 0x6E, 0x05,
                0xC8, 0x0B, 0xBF, 0x04, 0x48, 0x09, 0xBF, 0x04}) ||
      !BytesAt(executable, sections, 0x4BF0998,
               {0x01, 0x00, 0x00, 0x00, 0x98, 0x14, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0xF8, 0x9D, 0x6E, 0x05,
                0xC8, 0x0B, 0xBF, 0x04, 0x98, 0x09, 0xBF, 0x04})) {
    return false;
  }

  g_failure_stage = "frozen_virtual_only_xrefs";
  return FindDirectXrefs(
             executable, sections,
             static_cast<std::uint32_t>(
                 kStartupDx11RenderContextDrawFunctionRvaV1))
      .empty();
}

} // namespace

int main(int argc, char **argv) {
  if (!TestAdmissionAndAnchorRejection() || !TestExecutableGuard() ||
      !TestFrozenExecutableAndContracts(argc, argv) ||
      !TestTransactionalRollback()) {
    std::fprintf(stderr, "startup DX11 draw guard failure: %s\n",
                 g_failure_stage);
    return 1;
  }
  return 0;
}
