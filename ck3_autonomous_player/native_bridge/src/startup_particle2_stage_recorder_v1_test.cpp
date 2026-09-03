#include "xar_bridge/startup_particle2_stage_recorder_v1.hpp"

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

constexpr std::array<std::uint8_t,
                     xar::bridge::kStartupParticle2SourcePatchBytesV1>
    kSourcePatchAnchor{
        0x48, 0x8B, 0x4D, 0x77, 0x48, 0x85, 0xC9, 0x75, 0x08,
        0x4C, 0x89, 0x37, 0xE9, 0x92, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t,
                     xar::bridge::kStartupParticle2VariantPatchBytesV1>
    kVariantPatchAnchor{
        0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
        0x00, 0x00, 0x00, 0xE9, 0x1D, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t,
                     xar::bridge::kStartupParticle2BackendPatchBytesV1>
    kBackendPatchAnchor{
        0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
        0x00, 0x00, 0x00, 0x48, 0x8D, 0x4D, 0xB7};

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

void WriteI32(std::uint8_t *destination, std::int32_t value) {
  std::memcpy(destination, &value, sizeof(value));
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

bool IsExecuteRead(const void *address) {
  MEMORY_BASIC_INFORMATION information{};
  return address != nullptr &&
      VirtualQuery(address, &information, sizeof(information)) ==
          sizeof(information) &&
      information.State == MEM_COMMIT &&
      information.Protect == PAGE_EXECUTE_READ;
}

void Emit(std::uint8_t *code, std::size_t &cursor,
          std::initializer_list<std::uint8_t> bytes) {
  for (const auto byte : bytes) {
    code[cursor++] = byte;
  }
}

void EmitMarker(std::uint8_t *code, std::size_t &cursor,
                std::uint32_t value) {
  Emit(code, cursor, {0x41, 0xC7, 0x00}); // mov dword ptr [r8], imm32
  WriteI32(code + cursor, static_cast<std::int32_t>(value));
  cursor += sizeof(std::int32_t);
}

void EmitJump(std::uint8_t *code, std::size_t &cursor,
              std::size_t target) {
  code[cursor++] = 0xE9;
  const auto displacement = static_cast<std::int64_t>(target) -
      static_cast<std::int64_t>(cursor + sizeof(std::int32_t));
  WriteI32(code + cursor, static_cast<std::int32_t>(displacement));
  cursor += sizeof(std::int32_t);
}

void EmitFramedPrologue(std::uint8_t *code, std::size_t &cursor,
                        std::uint8_t local_slot) {
  Emit(code, cursor, {0x55});                         // push rbp
  Emit(code, cursor, {0x57});                         // push rdi
  Emit(code, cursor, {0x41, 0x56});                   // push r14
  Emit(code, cursor, {0x48, 0x81, 0xEC, 0xA0, 0, 0, 0}); // sub rsp,a0
  Emit(code, cursor, {0x48, 0x8B, 0xEC});             // mov rbp,rsp
  Emit(code, cursor, {0x48, 0x8B, 0xF9});             // mov rdi,rcx
  Emit(code, cursor, {0x45, 0x33, 0xF6});             // xor r14d,r14d
  Emit(code, cursor, {0x48, 0x89, 0x55, local_slot}); // mov [rbp+slot],rdx
}

void EmitFramedEpilogue(std::uint8_t *code, std::size_t &cursor) {
  Emit(code, cursor, {0x48, 0x81, 0xC4, 0xA0, 0, 0, 0}); // add rsp,a0
  Emit(code, cursor, {0x41, 0x5E});                       // pop r14
  Emit(code, cursor, {0x5F});                             // pop rdi
  Emit(code, cursor, {0x5D});                             // pop rbp
  Emit(code, cursor, {0xC3});                             // ret
}

struct SyntheticFactoryStages {
  static constexpr std::size_t kAllocationBytes = 4096;

  static constexpr std::size_t kSourceBase = 0x000;
  static constexpr std::size_t kSourcePatchOffset = kSourceBase + 0x18;
  static constexpr std::size_t kSourceHealthyOffset =
      kSourcePatchOffset + kSourcePatchAnchor.size();
  static constexpr std::size_t kSourceNullOffset =
      kSourcePatchOffset + 0x1A3;
  static constexpr std::size_t kSourceEpilogueOffset =
      kSourceNullOffset + 7;

  static constexpr std::size_t kVariantBase = 0x300;
  static constexpr std::size_t kVariantPatchOffset = kVariantBase + 0x15;
  static constexpr std::size_t kVariantHealthyOffset =
      kVariantPatchOffset + kVariantPatchAnchor.size();
  static constexpr std::size_t kVariantNullOffset =
      kVariantPatchOffset + 0x12D;
  static constexpr std::size_t kVariantEpilogueOffset =
      kVariantNullOffset + 7;

  static constexpr std::size_t kBackendBase = 0x600;
  static constexpr std::size_t kBackendPatchOffset = kBackendBase + 0x1F;
  static constexpr std::size_t kBackendNullOffset =
      kBackendPatchOffset + kBackendPatchAnchor.size();
  static constexpr std::size_t kBackendHealthyOffset =
      kBackendPatchOffset + 0x1A;
  static constexpr std::size_t kBackendEpilogueOffset =
      kBackendHealthyOffset + 7;

  std::uint8_t *code = nullptr;

  SyntheticFactoryStages() {
    code = static_cast<std::uint8_t *>(
        VirtualAlloc(nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT,
                     PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0x90, kAllocationBytes);
    if (!BuildSource() || !BuildVariant() || !BuildBackend()) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
      code = nullptr;
      return;
    }
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

  ~SyntheticFactoryStages() {
    if (code != nullptr) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
    }
  }

  SyntheticFactoryStages(const SyntheticFactoryStages &) = delete;
  SyntheticFactoryStages &operator=(const SyntheticFactoryStages &) = delete;

  bool valid() const noexcept { return code != nullptr; }

  bool BuildSource() noexcept {
    std::size_t cursor = kSourceBase;
    EmitFramedPrologue(code, cursor, 0x77);
    if (cursor != kSourcePatchOffset) {
      return false;
    }
    std::memcpy(code + cursor, kSourcePatchAnchor.data(),
                kSourcePatchAnchor.size());
    cursor += kSourcePatchAnchor.size();
    if (cursor != kSourceHealthyOffset) {
      return false;
    }
    EmitMarker(code, cursor, 1);
    EmitJump(code, cursor, kSourceEpilogueOffset);
    cursor = kSourceNullOffset;
    EmitMarker(code, cursor, 2);
    if (cursor != kSourceEpilogueOffset) {
      return false;
    }
    EmitFramedEpilogue(code, cursor);
    return cursor < kVariantBase;
  }

  bool BuildVariant() noexcept {
    std::size_t cursor = kVariantBase;
    Emit(code, cursor, {0x57});                         // push rdi
    Emit(code, cursor, {0x41, 0x56});                   // push r14
    Emit(code, cursor, {0x48, 0x83, 0xEC, 0x40});       // sub rsp,40
    Emit(code, cursor, {0x48, 0x8B, 0xF9});             // mov rdi,rcx
    Emit(code, cursor, {0x45, 0x33, 0xF6});             // xor r14d,r14d
    Emit(code, cursor, {0x48, 0x8B, 0xC2});             // mov rax,rdx
    Emit(code, cursor, {0x48, 0x85, 0xC0, 0x75, 0x10}); // native predicate
    if (cursor != kVariantPatchOffset) {
      return false;
    }
    std::memcpy(code + cursor, kVariantPatchAnchor.data(),
                kVariantPatchAnchor.size());
    cursor += kVariantPatchAnchor.size();
    if (cursor != kVariantHealthyOffset) {
      return false;
    }
    EmitMarker(code, cursor, 1);
    EmitJump(code, cursor, kVariantEpilogueOffset);
    cursor = kVariantNullOffset;
    EmitMarker(code, cursor, 2);
    if (cursor != kVariantEpilogueOffset) {
      return false;
    }
    Emit(code, cursor, {0x48, 0x83, 0xC4, 0x40}); // add rsp,40
    Emit(code, cursor, {0x41, 0x5E});             // pop r14
    Emit(code, cursor, {0x5F, 0xC3});             // pop rdi; ret
    return cursor < kBackendBase;
  }

  bool BuildBackend() noexcept {
    std::size_t cursor = kBackendBase;
    EmitFramedPrologue(code, cursor, 0x7F);
    Emit(code, cursor,
         {0x48, 0x83, 0x7D, 0x7F, 0x00, 0x75, 0x1A}); // native predicate
    if (cursor != kBackendPatchOffset) {
      return false;
    }
    std::memcpy(code + cursor, kBackendPatchAnchor.data(),
                kBackendPatchAnchor.size());
    cursor += kBackendPatchAnchor.size();
    if (cursor != kBackendNullOffset) {
      return false;
    }
    EmitMarker(code, cursor, 2);
    Emit(code, cursor, {0xEB, 0x09}); // jump backend epilogue
    cursor = kBackendHealthyOffset;
    EmitMarker(code, cursor, 1);
    if (cursor != kBackendEpilogueOffset) {
      return false;
    }
    EmitFramedEpilogue(code, cursor);
    return cursor < kAllocationBytes;
  }

  xar::bridge::StartupParticle2StageRecorderV1Environment Environment() {
    xar::bridge::StartupParticle2StageRecorderV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x140000000ULL;
    environment.source_patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kSourcePatchOffset);
    environment.source_healthy_target_override =
        reinterpret_cast<std::uintptr_t>(code + kSourceHealthyOffset);
    environment.source_null_target_override =
        reinterpret_cast<std::uintptr_t>(code + kSourceNullOffset);
    environment.variant_patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kVariantPatchOffset);
    environment.variant_null_target_override =
        reinterpret_cast<std::uintptr_t>(code + kVariantNullOffset);
    environment.backend_patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kBackendPatchOffset);
    environment.backend_null_target_override =
        reinterpret_cast<std::uintptr_t>(code + kBackendNullOffset);
    return environment;
  }

  bool SetPatchByte(std::size_t patch_offset, std::size_t relative_offset,
                    std::uint8_t value) noexcept {
    if (code == nullptr || patch_offset >= kAllocationBytes ||
        relative_offset >= kAllocationBytes - patch_offset) {
      return false;
    }
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READWRITE,
                       &previous) == FALSE ||
        previous != PAGE_EXECUTE_READ) {
      return false;
    }
    code[patch_offset + relative_offset] = value;
    const bool flushed = FlushInstructionCache(
        GetCurrentProcess(), code + patch_offset + relative_offset, 1) != FALSE;
    DWORD ignored = 0;
    const bool restored =
        VirtualProtect(code, kAllocationBytes, previous, &ignored) != FALSE;
    return flushed && restored;
  }

  void Invoke(std::size_t offset, std::uint64_t &output,
              std::uint64_t lookup, std::uint32_t &marker) const {
    using Function = void(__fastcall *)(std::uint64_t *, std::uint64_t,
                                        std::uint32_t *) noexcept;
    const auto function = reinterpret_cast<Function>(code + offset);
    function(&output, lookup, &marker);
  }

  void InvokeSource(std::uint64_t &output, std::uint64_t lookup,
                    std::uint32_t &marker) const {
    Invoke(kSourceBase, output, lookup, marker);
  }

  void InvokeVariant(std::uint64_t &output, std::uint64_t lookup,
                     std::uint32_t &marker) const {
    Invoke(kVariantBase, output, lookup, marker);
  }

  void InvokeBackend(std::uint64_t &output, std::uint64_t lookup,
                     std::uint32_t &marker) const {
    Invoke(kBackendBase, output, lookup, marker);
  }
};

bool IsOriginal(const SyntheticFactoryStages &fixture) {
  return std::memcmp(fixture.code + fixture.kSourcePatchOffset,
                     kSourcePatchAnchor.data(), kSourcePatchAnchor.size()) == 0 &&
      std::memcmp(fixture.code + fixture.kVariantPatchOffset,
                  kVariantPatchAnchor.data(), kVariantPatchAnchor.size()) == 0 &&
      std::memcmp(fixture.code + fixture.kBackendPatchOffset,
                  kBackendPatchAnchor.data(), kBackendPatchAnchor.size()) == 0;
}

bool InvokeAndExpect(const SyntheticFactoryStages &fixture,
                     std::size_t stage, bool present) {
  std::uint64_t output = 0x1122334455667788ULL;
  std::uint32_t marker = 0;
  const auto lookup = present ? 0x8877665544332211ULL : 0ULL;
  if (stage == 0) {
    fixture.InvokeSource(output, lookup, marker);
  } else if (stage == 1) {
    fixture.InvokeVariant(output, lookup, marker);
  } else {
    fixture.InvokeBackend(output, lookup, marker);
  }
  return marker == (present ? 1U : 2U) &&
      output == (present ? 0x1122334455667788ULL : 0ULL);
}

struct FaultInjectingMemory {
  std::uint32_t alloc_calls = 0;
  std::uint32_t free_calls = 0;
  std::uint32_t protect_calls = 0;
  std::uint32_t flush_calls = 0;
  std::uint32_t fail_protect_call_first = 0;
  std::uint32_t fail_protect_call_second = 0;
  std::uint32_t fail_flush_call_first = 0;
  std::uint32_t fail_flush_call_second = 0;
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
  if (memory.protect_calls == memory.fail_protect_call_first ||
      memory.protect_calls == memory.fail_protect_call_second) {
    old_protection = 0;
    return false;
  }
  return VirtualProtect(address, size, new_protection, &old_protection) !=
      FALSE;
}

bool FaultFlush(void *opaque, const void *address, std::size_t size) noexcept {
  auto &memory = *static_cast<FaultInjectingMemory *>(opaque);
  ++memory.flush_calls;
  if (memory.flush_calls == memory.fail_flush_call_first ||
      memory.flush_calls == memory.fail_flush_call_second) {
    return false;
  }
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

void AddFaultCallbacks(
    xar::bridge::StartupParticle2StageRecorderV1Environment &environment,
    FaultInjectingMemory &memory) {
  environment.memory_context = &memory;
  environment.virtual_alloc_override = &FaultVirtualAlloc;
  environment.virtual_free_override = &FaultVirtualFree;
  environment.virtual_protect_override = &FaultVirtualProtect;
  environment.flush_instruction_cache_override = &FaultFlush;
}

bool TestAdmissionAndAnchorRejection() {
  using namespace xar::bridge;
  g_failure_stage = "admission_exact_build";
  StartupParticle2StageRecorderV1State exact_rejected{};
  StartupParticle2StageRecorderV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;
  if (InstallStartupParticle2StageRecorderV1(exact_rejected, environment) ||
      (exact_rejected.failure_flags.load() &
       startup_particle2_stage_recorder_failure_exact_build) == 0) {
    return false;
  }

  g_failure_stage = "admission_suspended";
  StartupParticle2StageRecorderV1State suspension_rejected{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  if (InstallStartupParticle2StageRecorderV1(suspension_rejected,
                                              environment) ||
      (suspension_rejected.failure_flags.load() &
       startup_particle2_stage_recorder_failure_primary_thread_suspended) ==
          0) {
    return false;
  }

  g_failure_stage = "admission_override";
  StartupParticle2StageRecorderV1State override_rejected{};
  environment.primary_thread_suspended_proven = true;
  environment.source_patch_target_override = 1;
  if (InstallStartupParticle2StageRecorderV1(override_rejected, environment) ||
      (override_rejected.failure_flags.load() &
       startup_particle2_stage_recorder_failure_unsupported_override) == 0) {
    return false;
  }

  g_failure_stage = "anchor_drift";
  SyntheticFactoryStages fixture;
  if (!fixture.valid()) {
    return false;
  }
  const auto saved = fixture.code[fixture.kVariantPatchOffset + 4];
  if (!fixture.SetPatchByte(fixture.kVariantPatchOffset, 4,
                            static_cast<std::uint8_t>(saved ^ 0x80U))) {
    return false;
  }
  StartupParticle2StageRecorderV1State drift_rejected{};
  const bool installed = InstallStartupParticle2StageRecorderV1(
      drift_rejected, fixture.Environment());
  const bool restored = fixture.SetPatchByte(fixture.kVariantPatchOffset, 4,
                                              saved);
  return restored && !installed && drift_rejected.stub_allocation == nullptr &&
      drift_rejected.patch_mask.load() == 0 &&
      (drift_rejected.failure_flags.load() &
       startup_particle2_stage_recorder_failure_anchor) != 0;
}

bool TestExecutableRecorderAndNativeFlow() {
  using namespace xar::bridge;
  g_failure_stage = "native_flow_before_install";
  SyntheticFactoryStages fixture;
  if (!fixture.valid() || !IsOriginal(fixture)) {
    return false;
  }
  for (std::size_t stage = 0; stage < 3; ++stage) {
    if (!InvokeAndExpect(fixture, stage, true) ||
        !InvokeAndExpect(fixture, stage, false)) {
      return false;
    }
  }

  g_failure_stage = "recorder_install";
  StartupParticle2StageRecorderV1State state{};
  const auto environment = fixture.Environment();
  if (!InstallStartupParticle2StageRecorderV1(state, environment) ||
      state.installed.load() != 1 || state.stub_allocation == nullptr ||
      state.patch_mask.load() != kStartupParticle2AllPatchMaskV1 ||
      !IsExecuteRead(state.stub_allocation) ||
      !IsExecuteRead(fixture.code)) {
    return false;
  }

  const auto *source_patch = fixture.code + fixture.kSourcePatchOffset;
  const auto *variant_patch = fixture.code + fixture.kVariantPatchOffset;
  const auto *backend_patch = fixture.code + fixture.kBackendPatchOffset;
  const auto stub_base =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  if (source_patch[0] != 0x49 || source_patch[1] != 0xBB ||
      ReadU64(source_patch + 2) != stub_base ||
      variant_patch[0] != 0x49 || variant_patch[1] != 0xBB ||
      ReadU64(variant_patch + 2) !=
          stub_base + kStartupParticle2SourceStubBytesV1 ||
      backend_patch[0] != 0x49 || backend_patch[1] != 0xBB ||
      ReadU64(backend_patch + 2) !=
          stub_base + kStartupParticle2SourceStubBytesV1 +
              kStartupParticle2VariantStubBytesV1 ||
      !std::all_of(source_patch + 13,
                   source_patch + kStartupParticle2SourcePatchBytesV1,
                   [](std::uint8_t value) { return value == 0x90; }) ||
      !std::all_of(variant_patch + 13,
                   variant_patch + kStartupParticle2VariantPatchBytesV1,
                   [](std::uint8_t value) { return value == 0x90; }) ||
      !std::all_of(backend_patch + 13,
                   backend_patch + kStartupParticle2BackendPatchBytesV1,
                   [](std::uint8_t value) { return value == 0x90; })) {
    return false;
  }

  g_failure_stage = "generated_stub_identity";
  const auto *stub = static_cast<const std::uint8_t *>(state.stub_allocation);
  constexpr std::size_t variant_stub = kStartupParticle2SourceStubBytesV1;
  constexpr std::size_t backend_stub =
      kStartupParticle2SourceStubBytesV1 +
      kStartupParticle2VariantStubBytesV1;
  if (std::memcmp(stub, "\x48\x8B\x4D\x77\x48\x85\xC9\x0F\x85", 9) != 0 ||
      13 + ReadI32(stub + 9) != 43 ||
      ReadU64(stub + 15) !=
          reinterpret_cast<std::uintptr_t>(&state.source_lookup_null_count) ||
      ReadU64(stub + 32) != environment.source_null_target_override ||
      ReadU64(stub + 45) != environment.source_healthy_target_override ||
      ReadU64(stub + variant_stub + 2) !=
          reinterpret_cast<std::uintptr_t>(&state.variant_lookup_null_count) ||
      ReadU64(stub + variant_stub + 27) !=
          environment.variant_null_target_override ||
      ReadU64(stub + backend_stub + 2) !=
          reinterpret_cast<std::uintptr_t>(&state.backend_creation_null_count) ||
      ReadU64(stub + backend_stub + 31) !=
          environment.backend_null_target_override) {
    return false;
  }

  g_failure_stage = "native_flow_after_install";
  for (std::size_t stage = 0; stage < 3; ++stage) {
    if (!InvokeAndExpect(fixture, stage, true) ||
        !InvokeAndExpect(fixture, stage, false)) {
      return false;
    }
  }
  const auto diagnostics = ReadStartupParticle2StageRecorderV1Diagnostics(state);
  if (!diagnostics.installed ||
      diagnostics.patch_mask != kStartupParticle2AllPatchMaskV1 ||
      diagnostics.failure_flags !=
          startup_particle2_stage_recorder_failure_none ||
      diagnostics.source_lookup_null_count != 1 ||
      diagnostics.variant_lookup_null_count != 1 ||
      diagnostics.backend_creation_null_count != 1) {
    return false;
  }

  g_failure_stage = "recorder_uninstall";
  if (!UninstallStartupParticle2StageRecorderV1(state) ||
      state.installed.load() != 0 || state.patch_mask.load() != 0 ||
      state.stub_allocation != nullptr || !IsOriginal(fixture) ||
      !IsExecuteRead(fixture.code)) {
    return false;
  }
  for (std::size_t stage = 0; stage < 3; ++stage) {
    if (!InvokeAndExpect(fixture, stage, true) ||
        !InvokeAndExpect(fixture, stage, false)) {
      return false;
    }
  }
  return true;
}

bool TestAllocationAndRecoverableRollback() {
  using namespace xar::bridge;
  g_failure_stage = "allocation_failure";
  SyntheticFactoryStages allocation_fixture;
  if (!allocation_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory allocation_memory{};
  allocation_memory.fail_allocation = true;
  auto allocation_environment = allocation_fixture.Environment();
  AddFaultCallbacks(allocation_environment, allocation_memory);
  StartupParticle2StageRecorderV1State allocation_state{};
  if (InstallStartupParticle2StageRecorderV1(allocation_state,
                                              allocation_environment) ||
      !IsOriginal(allocation_fixture) || allocation_memory.alloc_calls != 1 ||
      allocation_memory.free_calls != 0 ||
      (allocation_state.failure_flags.load() &
       startup_particle2_stage_recorder_failure_allocation) == 0) {
    return false;
  }

  // Stub flush is call one and the source patch flush is call two. Failing the
  // variant patch flush (call three) exercises rollback of that transaction
  // followed by restoration of the already-installed source patch.
  g_failure_stage = "recoverable_variant_rollback";
  SyntheticFactoryStages recoverable_fixture;
  if (!recoverable_fixture.valid()) {
    return false;
  }
  FaultInjectingMemory recoverable_memory{};
  recoverable_memory.fail_flush_call_first = 3;
  auto recoverable_environment = recoverable_fixture.Environment();
  AddFaultCallbacks(recoverable_environment, recoverable_memory);
  StartupParticle2StageRecorderV1State recoverable_state{};
  if (InstallStartupParticle2StageRecorderV1(recoverable_state,
                                              recoverable_environment) ||
      recoverable_state.installed.load() != 0 ||
      recoverable_state.patch_mask.load() != 0 ||
      recoverable_state.stub_allocation != nullptr ||
      !IsOriginal(recoverable_fixture) || recoverable_memory.free_calls != 1 ||
      (recoverable_state.failure_flags.load() &
       startup_particle2_stage_recorder_failure_flush) == 0 ||
      (recoverable_state.failure_flags.load() &
       startup_particle2_stage_recorder_failure_rollback) != 0) {
    return false;
  }

  // A clean retry proves that the recoverable failure released global
  // ownership as well as the combined stub allocation.
  g_failure_stage = "post_rollback_reinstall";
  StartupParticle2StageRecorderV1State retry_state{};
  if (!InstallStartupParticle2StageRecorderV1(
          retry_state, recoverable_fixture.Environment()) ||
      !UninstallStartupParticle2StageRecorderV1(retry_state) ||
      !IsOriginal(recoverable_fixture)) {
    return false;
  }
  return true;
}

bool TestFrozenExecutableAndSourceContract(int argc, char **argv) {
  using namespace xar::bridge;
  g_failure_stage = "source_contract_arguments";
  if (argc != 8) {
    return false;
  }
  const auto header = ReadFile(argv[1]);
  const auto source = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto fixture = ReadFile(argv[4]);
  const auto executable = ReadFile(argv[5]);
  const auto cmake = ReadFile(argv[6]);
  const auto bridge = ReadFile(argv[7]);
  if (!StrictUtf8WithoutReplacement(header) ||
      !StrictUtf8WithoutReplacement(source) ||
      !StrictUtf8WithoutReplacement(abi) ||
      !StrictUtf8WithoutReplacement(fixture) || executable.empty() ||
      !StrictUtf8WithoutReplacement(cmake) ||
      !StrictUtf8WithoutReplacement(bridge)) {
    return false;
  }

  g_failure_stage = "source_contract_tokens";
  const std::array<std::string_view, 18> header_tokens{
      "kStartupParticle2FactoryFunctionRvaV1 =",
      "0x3A866D0",
      "kStartupParticle2SourcePatchRvaV1 =",
      "0x3A86769",
      "kStartupParticle2SourceNullRvaV1 =",
      "0x3A8690C",
      "kStartupParticle2VariantPatchRvaV1 =",
      "0x3A867B0",
      "kStartupParticle2VariantNullRvaV1 =",
      "0x3A868DD",
      "kStartupParticle2BackendPatchRvaV1 =",
      "0x3A867EC",
      "kStartupParticle2BackendNullRvaV1 =",
      "0x3A867FB",
      "kStartupParticle2StageRecorderInstalledByDefaultV1 =",
      "false",
      "primary_thread_suspended_proven",
      "backend_creation_null_count"};
  for (const auto token : header_tokens) {
    if (!Contains(header, token)) {
      return false;
    }
  }
  const std::array<std::string_view, 11> source_tokens{
      "BuildSourceStub",
      "BuildVariantStub",
      "BuildBackendStub",
      "EmitCounterIncrement",
      "WriteTargetTransaction",
      "ProveOriginalTarget",
      "RestoreAllPatches",
      "kStartupParticle2SourcePatchMaskV1",
      "startup_particle2_stage_recorder_failure_rollback",
      "MEM_RESERVE | MEM_COMMIT",
      "PAGE_EXECUTE_READ"};
  for (const auto token : source_tokens) {
    if (!Contains(source, token)) {
      return false;
    }
  }
  const std::array<std::string_view, 19> contract_tokens{
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "0x3A866D0",
      "0x3A86769",
      "0x3A8677A",
      "0x3A8690C",
      "0x3A867B0",
      "0x3A868DD",
      "0x3A867EC",
      "0x3A867FB",
      "installed_by_default",
      "no-suppression",
      "source_lookup_null_count",
      "variant_lookup_null_count",
      "backend_creation_null_count",
      "transactional_rollback",
      "unproven rollback",
      "quiescent uninstall retry",
      "startup_failure_containment_enabled",
      "containment_mutually_exclusive"};
  for (const auto token : contract_tokens) {
    if (!Contains(abi, token) || !Contains(fixture, token)) {
      return false;
    }
  }

  g_failure_stage = "cmake_bridge_wiring";
  const std::array<std::string_view, 4> cmake_tokens{
      "option(",
      "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1",
      "OFF",
      "src/startup_particle2_stage_recorder_v1.cpp"};
  for (const auto token : cmake_tokens) {
    if (!Contains(cmake, token)) {
      return false;
    }
  }
  const std::array<std::string_view, 13> bridge_tokens{
      "startup_particle2_stage_recorder_v1.hpp",
      "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1",
      "kStartupFailureContainmentEnabledV1 = true",
      "kStartupFailureContainmentEnabledV1 = false",
      "kStartupParticle2StageRecorderEnabledV1",
      "static_assert(!(kStartupFailureContainmentEnabledV1 &&",
      "g_startup_particle2_stage_recorder_v1",
      "ReadStartupParticle2StageRecorderV1Diagnostics",
      "startup_particle2_stage_recorder_enabled",
      "startup_particle2_stage_recorder_v1",
      "source_lookup_null_count",
      "backend_creation_null_count",
      "InstallStartupParticle2StageRecorderV1"};
  for (const auto token : bridge_tokens) {
    if (!Contains(bridge, token)) {
      return false;
    }
  }
  if (!Contains(cmake, "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1") ||
      !Contains(cmake,
                "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1")) {
    return false;
  }

  g_failure_stage = "frozen_executable_hash";
  std::string sha256;
  if (!Sha256Upper(executable, sha256) ||
      sha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86") {
    return false;
  }

  g_failure_stage = "frozen_executable_bytes";
  return BytesAt(executable, 0x3A866D0,
                 {0x48, 0x89, 0x4C, 0x24, 0x08, 0x55, 0x53, 0x56, 0x57,
                  0x41, 0x54, 0x41, 0x56, 0x41, 0x57, 0x48, 0x8D, 0x6C,
                  0x24, 0xD9, 0x48, 0x81, 0xEC, 0xF0, 0x00, 0x00, 0x00}) &&
      BytesAt(executable, 0x3A86769,
              {0x48, 0x8B, 0x4D, 0x77, 0x48, 0x85, 0xC9, 0x75, 0x08,
               0x4C, 0x89, 0x37, 0xE9, 0x92, 0x01, 0x00, 0x00}) &&
      BytesAt(executable, 0x3A8677A,
              {0x48, 0x8D, 0x46, 0x20, 0x8B, 0x50, 0x10}) &&
      BytesAt(executable, 0x3A8690C,
              {0x48, 0x8B, 0xC7, 0x48, 0x81, 0xC4, 0xF0, 0x00, 0x00, 0x00,
               0x41, 0x5F, 0x41, 0x5E, 0x41, 0x5C, 0x5F, 0x5E, 0x5B, 0x5D,
               0xC3}) &&
      BytesAt(executable, 0x3A867AB,
              {0x48, 0x85, 0xC0, 0x75, 0x10}) &&
      BytesAt(executable, 0x3A867B0,
              {0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
               0x00, 0x00, 0x00, 0xE9, 0x1D, 0x01, 0x00, 0x00}) &&
      BytesAt(executable, 0x3A868DD,
              {0x48, 0x8B, 0x75, 0x77, 0x48, 0x85, 0xF6, 0x74, 0x26}) &&
      BytesAt(executable, 0x3A867E5,
              {0x48, 0x83, 0x7D, 0x7F, 0x00, 0x75, 0x1A}) &&
      BytesAt(executable, 0x3A867EC,
              {0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
               0x00, 0x00, 0x00, 0x48, 0x8D, 0x4D, 0xB7}) &&
      BytesAt(executable, 0x3A867FB,
              {0xE8, 0x30, 0x01, 0x00, 0x00, 0x90,
               0xE9, 0xD7, 0x00, 0x00, 0x00});
}

bool TestUnprovenRollbackRetainsLifetime() {
  using namespace xar::bridge;
  // Keep this case last. The desired source-patch flush and its rollback flush
  // both fail. Even though the data bytes compare equal to the original, the
  // instruction-cache state is unproven, so executable storage, ownership, and
  // the stable counter state must remain alive until process termination.
  g_failure_stage = "unproven_rollback_retains_lifetime";
  static auto *fixture = new SyntheticFactoryStages();
  if (!fixture->valid()) {
    return false;
  }
  static FaultInjectingMemory memory{};
  memory.fail_flush_call_first = 2;
  memory.fail_flush_call_second = 3;
  auto environment = fixture->Environment();
  AddFaultCallbacks(environment, memory);
  static StartupParticle2StageRecorderV1State state{};
  if (InstallStartupParticle2StageRecorderV1(state, environment) ||
      state.installed.load() != 1 || state.stub_allocation == nullptr ||
      state.patch_mask.load() != kStartupParticle2SourcePatchMaskV1 ||
      memory.free_calls != 0 || !IsOriginal(*fixture) ||
      (state.failure_flags.load() &
       startup_particle2_stage_recorder_failure_flush) == 0 ||
      (state.failure_flags.load() &
       startup_particle2_stage_recorder_failure_rollback) == 0) {
    return false;
  }
  const auto diagnostics = ReadStartupParticle2StageRecorderV1Diagnostics(state);
  if (!diagnostics.installed ||
      diagnostics.patch_mask != kStartupParticle2SourcePatchMaskV1 ||
      diagnostics.source_lookup_null_count != 0 ||
      diagnostics.variant_lookup_null_count != 0 ||
      diagnostics.backend_creation_null_count != 0 ||
      !IsExecuteRead(state.stub_allocation)) {
    return false;
  }

  // Once quiescence is proven by the caller, a later uninstall must redo the
  // cache/protection proof before releasing the retained RX stub and owner.
  g_failure_stage = "unproven_rollback_quiescent_retry";
  return UninstallStartupParticle2StageRecorderV1(state) &&
      state.installed.load() == 0 && state.patch_mask.load() == 0 &&
      state.stub_allocation == nullptr && memory.free_calls == 1 &&
      memory.flush_calls == 4 && IsOriginal(*fixture) &&
      IsExecuteRead(fixture->code) &&
      !ReadStartupParticle2StageRecorderV1Diagnostics(state).installed;
}

} // namespace

int main(int argc, char **argv) {
  if (!TestAdmissionAndAnchorRejection() ||
      !TestExecutableRecorderAndNativeFlow() ||
      !TestAllocationAndRecoverableRollback() ||
      !TestFrozenExecutableAndSourceContract(argc, argv) ||
      !TestUnprovenRollbackRetainsLifetime()) {
    std::fprintf(stderr, "startup particle2 stage recorder failure: %s\n",
                 g_failure_stage);
    return 1;
  }
  return 0;
}
