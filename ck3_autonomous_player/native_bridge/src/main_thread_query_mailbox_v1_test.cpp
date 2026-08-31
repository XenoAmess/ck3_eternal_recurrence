#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace {

const char *g_failure_stage = "not_started";

struct FakeMemoryProtection {
  void *slot = nullptr;
  DWORD current_protect = PAGE_READONLY;
  std::uint32_t query_calls = 0;
  std::uint32_t protect_calls = 0;
  bool fail_next_readonly_restore = false;
};

bool FakeMemoryQuery(void *opaque, const void *address,
                     MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &protection = *static_cast<FakeMemoryProtection *>(opaque);
  ++protection.query_calls;
  if (address != protection.slot) {
    return false;
  }
  constexpr std::uintptr_t page_size = 4096;
  const auto slot_address = reinterpret_cast<std::uintptr_t>(address);
  information = {};
  information.BaseAddress = reinterpret_cast<void *>(
      (slot_address / page_size) * page_size);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = page_size;
  information.State = MEM_COMMIT;
  information.Protect = protection.current_protect;
  information.Type = MEM_IMAGE;
  return true;
}

bool FakeMemoryProtect(void *opaque, void *, std::size_t page_size,
                       DWORD new_protect, DWORD &old_protect) noexcept {
  auto &protection = *static_cast<FakeMemoryProtection *>(opaque);
  ++protection.protect_calls;
  old_protect = protection.current_protect;
  if (page_size != 4096) {
    return false;
  }
  if (new_protect == PAGE_READONLY &&
      protection.fail_next_readonly_restore) {
    protection.fail_next_readonly_restore = false;
    return false;
  }
  protection.current_protect = new_protect;
  return true;
}

void *g_fake_tls_context = nullptr;

void *__fastcall FakeTlsContextGetter() noexcept {
  return g_fake_tls_context;
}

struct FakeRuntime {
  std::array<std::byte, 0x18> rng_state{};
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_wrapper_slot = 0;
  std::array<std::byte, 0x28> jomini_state{};
  std::array<std::byte, 0x28> alternate_jomini_state{};
  std::uintptr_t jomini_state_slot = 0;
  std::array<std::byte, 0x18> game_state{};
  std::array<std::byte, 0x18> alternate_game_state{};
  std::uintptr_t game_state_slot = 0;
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls_context{};
  std::array<std::byte, 0x28> alternate_tls_context{};
  FakeMemoryProtection protection{};

  explicit FakeRuntime(std::uint32_t owner_thread_id,
                       std::int32_t date_raw) {
    std::memcpy(rng_state.data() + 0x10, &owner_thread_id,
                sizeof(owner_thread_id));
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng_state.data());
    rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    const std::uint8_t paused = 1;
    std::memcpy(jomini_state.data() + 0x20, &paused, sizeof(paused));
    std::memcpy(alternate_jomini_state.data() + 0x20, &paused,
                sizeof(paused));
    jomini_state_slot =
        reinterpret_cast<std::uintptr_t>(jomini_state.data());
    std::memcpy(game_state.data() + 0x08, &date_raw, sizeof(date_raw));
    std::memcpy(alternate_game_state.data() + 0x08, &date_raw,
                sizeof(date_raw));
    game_state_slot = reinterpret_cast<std::uintptr_t>(game_state.data());
    const std::uint8_t tls_main_thread_marker = 1;
    std::memcpy(tls_context.data() + 0x20, &tls_main_thread_marker,
                sizeof(tls_main_thread_marker));
    std::memcpy(alternate_tls_context.data() + 0x20,
                &tls_main_thread_marker,
                sizeof(tls_main_thread_marker));
    g_fake_tls_context = tls_context.data();
  }

  xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 Environment(
      std::uintptr_t module_base, void **iat_slot,
      xar::ck3_11906::PeekMessageWFunctionV1 original) {
    protection.slot = iat_slot;
    return {
        module_base,
        true,
        true,
        iat_slot,
        original,
        reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot),
        reinterpret_cast<std::uintptr_t>(&jomini_state_slot),
        reinterpret_cast<std::uintptr_t>(&game_state_slot),
        reinterpret_cast<std::uintptr_t>(&tls_initialized),
        &FakeTlsContextGetter,
        &protection,
        &FakeMemoryQuery,
        &FakeMemoryProtect,
        4096,
        true,
    };
  }

  void SetDate(std::int32_t date_raw) {
    std::memcpy(game_state.data() + 0x08, &date_raw, sizeof(date_raw));
  }

  void SetPaused(std::uint8_t paused) {
    std::memcpy(jomini_state.data() + 0x20, &paused, sizeof(paused));
  }

  void SetTlsMarker(std::uint8_t marker) {
    std::memcpy(tls_context.data() + 0x20, &marker, sizeof(marker));
  }

  void SetOwner(std::uint32_t owner_thread_id) {
    std::memcpy(rng_state.data() + 0x10, &owner_thread_id,
                sizeof(owner_thread_id));
  }

  void UseAlternateIdentityObjects(bool use_alternate) {
    jomini_state_slot = reinterpret_cast<std::uintptr_t>(
        use_alternate ? alternate_jomini_state.data() : jomini_state.data());
    game_state_slot = reinterpret_cast<std::uintptr_t>(
        use_alternate ? alternate_game_state.data() : game_state.data());
    g_fake_tls_context = use_alternate ? alternate_tls_context.data()
                                       : tls_context.data();
  }
};

struct ExecutorContext {
  std::uint32_t calls = 0;
  bool return_value = true;
  bool mutate_date = false;
  FakeRuntime *runtime = nullptr;
  xar::ck3_11906::MainThreadExecutionStampV1 observed{};
};

bool Execute(void *opaque,
             const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &context = *static_cast<ExecutorContext *>(opaque);
  ++context.calls;
  context.observed = stamp;
  if (context.mutate_date && context.runtime != nullptr) {
    context.runtime->SetDate(stamp.date_raw + 1);
  }
  return context.return_value;
}

bool ExecuteSecondary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteTertiary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteQuaternary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteQuinary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteSenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteSeptenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteOctonary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteNonary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteDenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteUndenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteDuodenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteThirdenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteQuattuordenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteQuindenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteSexdenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteSeptendenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteOctodenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteNovemdenary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

bool ExecuteVigintary(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return Execute(opaque, stamp);
}

struct BlockingExecutorContext {
  HANDLE entered = nullptr;
  HANDLE release = nullptr;
  std::uint32_t calls = 0;
};

bool BlockingExecute(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept {
  auto &context = *static_cast<BlockingExecutorContext *>(opaque);
  ++context.calls;
  SetEvent(context.entered);
  return WaitForSingleObject(context.release, 5'000) == WAIT_OBJECT_0;
}

struct DrainThreadContext {
  xar::ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  std::uint32_t owner_thread_id = 0;
  bool executor_ran = false;
};

DWORD WINAPI DrainOnFixtureThread(void *opaque) {
  auto &context = *static_cast<DrainThreadContext *>(opaque);
  context.executor_ran = xar::ck3_11906::ObserveMainThreadPumpAndDrainV1(
      *context.mailbox,
      xar::ck3_11906::kSdlWindowsPumpFirstPeekReturnRva,
      context.owner_thread_id);
  return 0;
}

struct DelayedDrainThreadContext {
  DrainThreadContext drain{};
  std::uint32_t delay_milliseconds = 0;
};

DWORD WINAPI DelayedDrainOnFixtureThread(void *opaque) {
  auto &context = *static_cast<DelayedDrainThreadContext *>(opaque);
  Sleep(context.delay_milliseconds);
  return DrainOnFixtureThread(&context.drain);
}

std::uint32_t g_original_peek_calls = 0;

BOOL WINAPI FakePeekMessage(LPMSG message, HWND, UINT, UINT, UINT) {
  ++g_original_peek_calls;
  if (message != nullptr) {
    message->message = WM_NULL;
  }
  SetLastError(0x5A17U);
  return TRUE;
}

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

std::size_t CountOccurrences(std::string_view haystack,
                             std::string_view needle) {
  if (needle.empty()) {
    return 0;
  }
  std::size_t count = 0;
  std::size_t offset = 0;
  while ((offset = haystack.find(needle, offset)) != std::string_view::npos) {
    ++count;
    offset += needle.size();
  }
  return count;
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

bool RvaIsReadOnlyDataSection(std::string_view image, std::uint32_t rva,
                              std::string_view expected_name) {
  std::uint32_t pe_offset = 0;
  std::uint16_t section_count = 0;
  std::uint16_t optional_header_size = 0;
  if (image.size() < 0x40 || image.substr(0, 2) != "MZ" ||
      !ReadInteger(image, 0x3C, pe_offset) ||
      pe_offset > image.size() - 24 ||
      image.substr(pe_offset, 4) != std::string_view{"PE\0\0", 4} ||
      !ReadInteger(image, pe_offset + 6, section_count) ||
      !ReadInteger(image, pe_offset + 20, optional_header_size)) {
    return false;
  }
  const auto section_table =
      static_cast<std::size_t>(pe_offset) + 24 + optional_header_size;
  if (section_count == 0 || section_count > 128 ||
      section_table > image.size() ||
      static_cast<std::size_t>(section_count) >
          (image.size() - section_table) / 40) {
    return false;
  }
  for (std::uint16_t index = 0; index < section_count; ++index) {
    const auto row = section_table + static_cast<std::size_t>(index) * 40;
    std::uint32_t virtual_size = 0;
    std::uint32_t virtual_address = 0;
    std::uint32_t raw_size = 0;
    std::uint32_t characteristics = 0;
    if (!ReadInteger(image, row + 8, virtual_size) ||
        !ReadInteger(image, row + 12, virtual_address) ||
        !ReadInteger(image, row + 16, raw_size) ||
        !ReadInteger(image, row + 36, characteristics)) {
      return false;
    }
    const auto mapped_size = std::max(virtual_size, raw_size);
    if (rva < virtual_address || rva - virtual_address >= mapped_size) {
      continue;
    }
    const auto raw_name = image.substr(row, 8);
    const auto name_end = raw_name.find('\0');
    const auto name = raw_name.substr(
        0, name_end == std::string_view::npos ? raw_name.size() : name_end);
    return name == expected_name &&
           (characteristics & IMAGE_SCN_CNT_INITIALIZED_DATA) != 0 &&
           (characteristics & IMAGE_SCN_MEM_READ) != 0 &&
           (characteristics & IMAGE_SCN_MEM_WRITE) == 0 &&
           (characteristics & IMAGE_SCN_MEM_EXECUTE) == 0;
  }
  return false;
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

bool ImportNameAtIat(std::string_view image, std::uint32_t iat_rva,
                     std::string_view expected) {
  const auto iat_offset = RvaToOffset(image, iat_rva);
  std::uint64_t name_rva = 0;
  if (!iat_offset || !ReadInteger(image, *iat_offset, name_rva) ||
      name_rva > std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  const auto name_offset =
      RvaToOffset(image, static_cast<std::uint32_t>(name_rva));
  return name_offset && *name_offset + 2 + expected.size() < image.size() &&
         image.substr(*name_offset + 2, expected.size()) == expected &&
         image[*name_offset + 2 + expected.size()] == '\0';
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

bool TestMailboxStateMachine() {
  using namespace xar::ck3_11906;
  g_failure_stage = "initial_install";
  constexpr std::uint32_t owner_thread = 0x42U;
  constexpr std::uintptr_t fake_module_base = 0x140000000ULL;
  FakeRuntime runtime(owner_thread, 53'175'816);

  void *bad_iat = reinterpret_cast<void *>(0x1234U);
  MainThreadQueryMailboxV1 rejected{};
  if (InstallMainThreadQueryMailboxV1(
          rejected,
          runtime.Environment(fake_module_base, &bad_iat,
                              &FakePeekMessage)) ||
      (rejected.failure_flags.load() &
       main_thread_query_failure_iat_identity) == 0) {
    return false;
  }

  void *iat = reinterpret_cast<void *>(&FakePeekMessage);
  static MainThreadQueryMailboxV1 mailbox{};
  if (!InstallMainThreadQueryMailboxV1(
          mailbox,
          runtime.Environment(fake_module_base, &iat, &FakePeekMessage)) ||
      iat != reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1) ||
      runtime.protection.current_protect != PAGE_READONLY ||
      runtime.protection.query_calls != 1 ||
      runtime.protection.protect_calls != 2) {
    return false;
  }

  ExecutorContext context{};
  MainThreadQueryTicketV1 ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &context, ticket) !=
      MainThreadQuerySubmitResultV1::paused_main_thread_not_observed) {
    return false;
  }
  if (ObserveMainThreadPumpAndDrainV1(mailbox, 0xDEADBEEFU,
                                     owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread)) {
    return false;
  }
  auto diagnostics = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  g_failure_stage = "consecutive_proof_drift";
  if (!diagnostics.ready || diagnostics.owner_thread_id != owner_thread ||
      diagnostics.pump_epochs != 2 ||
      diagnostics.paused_owner_verified_pump_epochs != 2 ||
      diagnostics.observed_current_thread_id != owner_thread ||
      diagnostics.observed_rng_owner_thread_id != owner_thread ||
      diagnostics.observed_tls_initialized != 1 ||
      diagnostics.observed_tls_main_thread_marker != 1 ||
      !diagnostics.observed_paused ||
      !diagnostics.observed_stamp_read_success) {
    return false;
  }

  // 0x356B600 owns this wrapper for arbitrary scoped consumers. A different
  // owner is raw provenance, not an application-main admission failure.
  runtime.SetOwner(owner_thread + 1);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .observed_current_thread_id != owner_thread ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .observed_rng_owner_thread_id != owner_thread + 1 ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).failure_flags != 0) {
    return false;
  }
  runtime.SetOwner(owner_thread);

  runtime.SetDate(53'175'817);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  runtime.SetDate(53'175'816);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }

  runtime.UseAlternateIdentityObjects(true);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  runtime.UseAlternateIdentityObjects(false);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }

  constexpr std::uint32_t alternate_owner_thread = 0x43U;
  runtime.SetOwner(alternate_owner_thread);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva,
          alternate_owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva,
          alternate_owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  runtime.SetOwner(owner_thread);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }

  runtime.SetPaused(0);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 0 ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }
  runtime.SetPaused(1);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }

  const auto saved_game_state_slot = runtime.game_state_slot;
  runtime.game_state_slot = 0;
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 0) {
    return false;
  }
  runtime.game_state_slot = saved_game_state_slot;
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox)
              .paused_owner_verified_pump_epochs != 1 ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    return false;
  }

  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &context, ticket) !=
          MainThreadQuerySubmitResultV1::submitted ||
      ticket.sequence != 1 ||
      !ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      context.calls != 1 || context.observed.thread_id != owner_thread ||
      context.observed.rng_owner_thread_id != owner_thread ||
      context.observed.tls_initialized != 1 ||
      context.observed.tls_main_thread_marker != 1 ||
      context.observed.tls_context !=
          reinterpret_cast<std::uintptr_t>(runtime.tls_context.data()) ||
      context.observed.date_raw != 53'175'816 || !context.observed.paused ||
      WaitForMainThreadQueryV1(mailbox, ticket, 0) !=
          MainThreadQueryWaitResultV1::completed ||
      ReclaimMainThreadQueryV1(mailbox, ticket) !=
          MainThreadQueryReclaimResultV1::reclaimed) {
    return false;
  }

  g_failure_stage = "basic_queue_states";

  ExecutorContext cancelled_context{};
  MainThreadQueryTicketV1 cancelled_ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &cancelled_context,
                                cancelled_ticket) !=
          MainThreadQuerySubmitResultV1::submitted ||
      WaitForMainThreadQueryV1(mailbox, cancelled_ticket, 0) !=
          MainThreadQueryWaitResultV1::timeout_cancelled_before_execution ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      cancelled_context.calls != 0 ||
      ReclaimMainThreadQueryV1(mailbox, cancelled_ticket) !=
          MainThreadQueryReclaimResultV1::reclaimed) {
    return false;
  }

  // The old route worker cancelled a still-queued ticket after two seconds.
  // A verified paused pump arriving just beyond that interval must instead
  // execute the original ticket, join the pump thread, and reclaim cleanly.
  g_failure_stage = "queued_wait_crosses_delayed_paused_pump";
  constexpr std::uint32_t delayed_pump_milliseconds = 2'200;
  static_assert(kRouteContactHorizonV1QueuedWaitBudgetMilliseconds >
                delayed_pump_milliseconds);
  static_assert(kRouteContactHorizonV1QueuedWaitBudgetMilliseconds < 10'000);
  ExecutorContext delayed_context{};
  MainThreadQueryTicketV1 delayed_ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &delayed_context,
                                delayed_ticket) !=
      MainThreadQuerySubmitResultV1::submitted) {
    return false;
  }
  DelayedDrainThreadContext delayed_drain{
      {&mailbox, owner_thread, false}, delayed_pump_milliseconds};
  HANDLE delayed_thread =
      CreateThread(nullptr, 0, &DelayedDrainOnFixtureThread, &delayed_drain,
                   0, nullptr);
  if (delayed_thread == nullptr) {
    (void)WaitForMainThreadQueryV1(mailbox, delayed_ticket, 0);
    (void)ReclaimMainThreadQueryV1(mailbox, delayed_ticket);
    return false;
  }
  const auto delayed_wait = WaitForMainThreadQueryV1(
      mailbox, delayed_ticket,
      kRouteContactHorizonV1QueuedWaitBudgetMilliseconds);
  const auto delayed_thread_wait =
      WaitForSingleObject(delayed_thread, 1'000);
  CloseHandle(delayed_thread);
  const auto delayed_reclaim =
      ReclaimMainThreadQueryV1(mailbox, delayed_ticket);
  if (delayed_wait != MainThreadQueryWaitResultV1::completed ||
      delayed_thread_wait != WAIT_OBJECT_0 || !delayed_drain.drain.executor_ran ||
      delayed_context.calls != 1 ||
      delayed_reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
      mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::idle) {
    return false;
  }

  ExecutorContext failed_context{};
  failed_context.return_value = false;
  MainThreadQueryTicketV1 failed_ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &failed_context,
                                failed_ticket) !=
          MainThreadQuerySubmitResultV1::submitted ||
      !ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      WaitForMainThreadQueryV1(mailbox, failed_ticket, 0) !=
          MainThreadQueryWaitResultV1::executor_failed ||
      ReclaimMainThreadQueryV1(mailbox, failed_ticket) !=
          MainThreadQueryReclaimResultV1::reclaimed) {
    return false;
  }

  MSG message{};
  SetLastError(0);
  g_original_peek_calls = 0;
  if (!XarMainThreadPeekMessageWHookV1(&message, nullptr, 0, 0, 1) ||
      g_original_peek_calls != 1 || GetLastError() != 0x5A17U ||
      message.message != WM_NULL) {
    return false;
  }

  ExecutorContext drift_context{};
  g_failure_stage = "post_executor_drift";
  drift_context.mutate_date = true;
  drift_context.runtime = &runtime;
  MainThreadQueryTicketV1 drift_ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &drift_context,
                                drift_ticket) !=
          MainThreadQuerySubmitResultV1::submitted ||
      !ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      WaitForMainThreadQueryV1(mailbox, drift_ticket, 0) !=
          MainThreadQueryWaitResultV1::infrastructure_failed ||
      (mailbox.failure_flags.load() &
       main_thread_query_failure_post_execution_drift) == 0) {
    return false;
  }

  mailbox.active_hook_calls.store(1, std::memory_order_release);
  g_failure_stage = "uninstall_and_reinstall";
  if (UninstallMainThreadQueryMailboxV1(mailbox, 0) !=
          MainThreadQueryUninstallResultV1::active_hook_calls_pending ||
      iat != reinterpret_cast<void *>(&FakePeekMessage) ||
      mailbox.iat_hook_installed.load(std::memory_order_acquire) ||
      runtime.protection.current_protect != PAGE_READONLY) {
    return false;
  }
  mailbox.active_hook_calls.store(0, std::memory_order_release);
  if (UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled ||
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).iat_installed ||
      iat != reinterpret_cast<void *>(&FakePeekMessage)) {
    return false;
  }

  // A delayed hook entry remains safe after IAT restoration because v1 pins
  // the mailbox and original function pointer until process exit.
  const auto pump_epochs_after_uninstall =
      mailbox.pump_epochs.load(std::memory_order_acquire);
  SetLastError(0);
  if (!XarMainThreadPeekMessageWHookV1(&message, nullptr, 0, 0, 1) ||
      GetLastError() != 0x5A17U ||
      mailbox.active_hook_calls.load(std::memory_order_acquire) != 0 ||
      mailbox.pump_epochs.load(std::memory_order_acquire) !=
          pump_epochs_after_uninstall) {
    return false;
  }

  runtime.SetDate(53'175'816);
  if (!InstallMainThreadQueryMailboxV1(
          mailbox,
          runtime.Environment(fake_module_base, &iat, &FakePeekMessage)) ||
      iat != reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1)) {
    return false;
  }
  runtime.SetTlsMarker(0);
  g_failure_stage = "tls_gate";
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      (mailbox.failure_flags.load(std::memory_order_acquire) &
       main_thread_query_failure_tls_identity) == 0) {
    return false;
  }
  runtime.SetTlsMarker(1);
  if (UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled ||
      iat != reinterpret_cast<void *>(&FakePeekMessage)) {
    return false;
  }

  if (!InstallMainThreadQueryMailboxV1(
          mailbox,
          runtime.Environment(fake_module_base, &iat, &FakePeekMessage)) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread)) {
    return false;
  }
  ExecutorContext reentry_context{};
  MainThreadQueryTicketV1 reentry_ticket{};
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &reentry_context,
                                reentry_ticket) !=
      MainThreadQuerySubmitResultV1::submitted) {
    return false;
  }
  mailbox.proof_reset_requested.store(true, std::memory_order_release);
  mailbox.failure_flags.fetch_or(main_thread_query_failure_reentry,
                                 std::memory_order_acq_rel);
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      reentry_context.calls != 0 ||
      WaitForMainThreadQueryV1(mailbox, reentry_ticket, 0) !=
          MainThreadQueryWaitResultV1::infrastructure_failed ||
      ReclaimMainThreadQueryV1(mailbox, reentry_ticket) !=
          MainThreadQueryReclaimResultV1::reclaimed ||
      UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled) {
    return false;
  }

  // An executing timeout never destroys its context, and shutdown refuses to
  // restore/reset the lifecycle until that synchronous callback returns.
  if (!InstallMainThreadQueryMailboxV1(
          mailbox,
          runtime.Environment(fake_module_base, &iat, &FakePeekMessage))) {
    g_failure_stage = "blocking_reinstall";
    return false;
  }
  if (ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      !ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready) {
    g_failure_stage = "blocking_epoch_admission";
    return false;
  }
  g_failure_stage = "executing_timeout_context_lifetime";
  BlockingExecutorContext blocking_context{
      CreateEventW(nullptr, TRUE, FALSE, nullptr),
      CreateEventW(nullptr, TRUE, FALSE, nullptr), 0};
  if (blocking_context.entered == nullptr || blocking_context.release == nullptr) {
    if (blocking_context.entered != nullptr) {
      CloseHandle(blocking_context.entered);
    }
    if (blocking_context.release != nullptr) {
      CloseHandle(blocking_context.release);
    }
    return false;
  }
  MainThreadQueryTicketV1 blocking_ticket{};
  DrainThreadContext drain_context{&mailbox, owner_thread, false};
  HANDLE drain_thread = nullptr;
  const auto blocking_submit = TrySubmitMainThreadQueryV1(
      mailbox, &BlockingExecute, &blocking_context, blocking_ticket);
  if (blocking_submit == MainThreadQuerySubmitResultV1::submitted) {
    drain_thread = CreateThread(nullptr, 0, &DrainOnFixtureThread,
                                &drain_context, 0, nullptr);
  }
  const auto entered_wait =
      drain_thread == nullptr
          ? WAIT_FAILED
          : WaitForSingleObject(blocking_context.entered, 5'000);
  const auto executing_wait =
      entered_wait == WAIT_OBJECT_0
          ? WaitForMainThreadQueryV1(mailbox, blocking_ticket, 0)
          : MainThreadQueryWaitResultV1::ticket_mismatch;
  const auto early_reclaim =
      entered_wait == WAIT_OBJECT_0
          ? ReclaimMainThreadQueryV1(mailbox, blocking_ticket)
          : MainThreadQueryReclaimResultV1::ticket_mismatch;
  const auto active_uninstall =
      entered_wait == WAIT_OBJECT_0
          ? UninstallMainThreadQueryMailboxV1(mailbox, 0)
          : MainThreadQueryUninstallResultV1::wrong_mailbox;
  if (blocking_submit != MainThreadQuerySubmitResultV1::submitted ||
      drain_thread == nullptr || entered_wait != WAIT_OBJECT_0 ||
      executing_wait !=
          MainThreadQueryWaitResultV1::timeout_executor_already_running ||
      early_reclaim != MainThreadQueryReclaimResultV1::not_terminal ||
      active_uninstall != MainThreadQueryUninstallResultV1::request_active) {
    g_failure_stage =
        blocking_submit != MainThreadQuerySubmitResultV1::submitted
            ? "blocking_submit"
            : drain_thread == nullptr
                  ? "blocking_create_thread"
                  : entered_wait != WAIT_OBJECT_0
                        ? "blocking_enter_wait"
                        : executing_wait != MainThreadQueryWaitResultV1::
                                                timeout_executor_already_running
                              ? "blocking_timeout_result"
                              : early_reclaim !=
                                        MainThreadQueryReclaimResultV1::
                                            not_terminal
                                    ? "blocking_early_reclaim"
                                    : "blocking_active_uninstall";
    if (drain_thread != nullptr) {
      SetEvent(blocking_context.release);
      WaitForSingleObject(drain_thread, 5'000);
      CloseHandle(drain_thread);
    }
    CloseHandle(blocking_context.entered);
    CloseHandle(blocking_context.release);
    return false;
  }
  SetEvent(blocking_context.release);
  const bool blocking_completed =
      WaitForSingleObject(drain_thread, 5'000) == WAIT_OBJECT_0;
  CloseHandle(drain_thread);
  if (!blocking_completed || !drain_context.executor_ran ||
      blocking_context.calls != 1 ||
      WaitForMainThreadQueryV1(mailbox, blocking_ticket, 0) !=
          MainThreadQueryWaitResultV1::completed ||
      ReclaimMainThreadQueryV1(mailbox, blocking_ticket) !=
          MainThreadQueryReclaimResultV1::reclaimed ||
      UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled) {
    CloseHandle(blocking_context.entered);
    CloseHandle(blocking_context.release);
    return false;
  }
  CloseHandle(blocking_context.entered);
  CloseHandle(blocking_context.release);

  // The prior counter-only boundary acceptance and this regression mode expose
  // heartbeat counters while making executor submission impossible.
  auto counter_only_environment =
      runtime.Environment(fake_module_base, &iat, &FakePeekMessage);
  counter_only_environment.executor_submission_enabled = false;
  g_failure_stage = "counter_only_mode";
  if (!InstallMainThreadQueryMailboxV1(mailbox, counter_only_environment) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread)) {
    return false;
  }
  ExecutorContext forbidden_context{};
  MainThreadQueryTicketV1 forbidden_ticket{};
  const auto counter_diagnostics =
      ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  if (TrySubmitMainThreadQueryV1(mailbox, &Execute, &forbidden_context,
                                forbidden_ticket) !=
          MainThreadQuerySubmitResultV1::executor_submission_disabled ||
      !counter_diagnostics.ready ||
      counter_diagnostics.executor_submission_enabled ||
      counter_diagnostics.executed_requests != 0 ||
      counter_diagnostics.paused_owner_verified_pump_epochs != 2 ||
      UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled) {
    return false;
  }

  // Production exposes twenty exact typed identities, never a generic
  // callback slot. Every admitted identity executes normally; a twenty-first
  // callback is rejected before it can enter the queue.
  auto typed_environment =
      runtime.Environment(fake_module_base, &iat, &FakePeekMessage);
  typed_environment.permitted_executor = &Execute;
  typed_environment.permitted_executor_secondary = &ExecuteSecondary;
  typed_environment.permitted_executor_tertiary = &ExecuteTertiary;
  typed_environment.permitted_executor_quaternary = &ExecuteQuaternary;
  typed_environment.permitted_executor_quinary = &ExecuteQuinary;
  typed_environment.permitted_executor_senary = &ExecuteSenary;
  typed_environment.permitted_executor_septenary = &ExecuteSeptenary;
  typed_environment.permitted_executor_octonary = &ExecuteOctonary;
  typed_environment.permitted_executor_nonary = &ExecuteNonary;
  typed_environment.permitted_executor_denary = &ExecuteDenary;
  typed_environment.permitted_executor_undenary = &ExecuteUndenary;
  typed_environment.permitted_executor_duodenary = &ExecuteDuodenary;
  typed_environment.permitted_executor_thirdenary = &ExecuteThirdenary;
  typed_environment.permitted_executor_quattuordenary =
      &ExecuteQuattuordenary;
  typed_environment.permitted_executor_quindenary = &ExecuteQuindenary;
  typed_environment.permitted_executor_sexdenary = &ExecuteSexdenary;
  typed_environment.permitted_executor_septendenary = &ExecuteSeptendenary;
  typed_environment.permitted_executor_octodenary = &ExecuteOctodenary;
  typed_environment.permitted_executor_novemdenary = &ExecuteNovemdenary;
  typed_environment.permitted_executor_vigintary = &ExecuteVigintary;
  g_failure_stage = "typed_executor_registry";
  if (!InstallMainThreadQueryMailboxV1(mailbox, typed_environment) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
      ObserveMainThreadPumpAndDrainV1(
          mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread)) {
    return false;
  }
  ExecutorContext typed_context{};
  BlockingExecutorContext rejected_typed_context{};
  MainThreadQueryTicketV1 rejected_typed_ticket{};
  if (TrySubmitMainThreadQueryV1(
          mailbox, &BlockingExecute, &rejected_typed_context,
          rejected_typed_ticket) !=
          MainThreadQuerySubmitResultV1::invalid_request) {
    return false;
  }
  constexpr std::array<MainThreadQueryExecutorV1, 20> typed_executors{
      &Execute, &ExecuteSecondary, &ExecuteTertiary, &ExecuteQuaternary,
      &ExecuteQuinary, &ExecuteSenary, &ExecuteSeptenary, &ExecuteOctonary,
      &ExecuteNonary, &ExecuteDenary, &ExecuteUndenary,
      &ExecuteDuodenary, &ExecuteThirdenary, &ExecuteQuattuordenary,
      &ExecuteQuindenary, &ExecuteSexdenary, &ExecuteSeptendenary,
      &ExecuteOctodenary, &ExecuteNovemdenary, &ExecuteVigintary};
  for (const auto executor : typed_executors) {
    MainThreadQueryTicketV1 typed_ticket{};
    if (TrySubmitMainThreadQueryV1(mailbox, executor, &typed_context,
                                  typed_ticket) !=
            MainThreadQuerySubmitResultV1::submitted ||
        !ObserveMainThreadPumpAndDrainV1(
            mailbox, kSdlWindowsPumpFirstPeekReturnRva, owner_thread) ||
        WaitForMainThreadQueryV1(mailbox, typed_ticket, 0) !=
            MainThreadQueryWaitResultV1::completed ||
        ReclaimMainThreadQueryV1(mailbox, typed_ticket) !=
            MainThreadQueryReclaimResultV1::reclaimed) {
      return false;
    }
  }
  if (typed_context.calls != typed_executors.size() ||
      UninstallMainThreadQueryMailboxV1(mailbox, 10) !=
          MainThreadQueryUninstallResultV1::uninstalled) {
    return false;
  }

  runtime.protection.fail_next_readonly_restore = true;
  g_failure_stage = "iat_protection_rollback";
  if (InstallMainThreadQueryMailboxV1(
          mailbox,
          runtime.Environment(fake_module_base, &iat, &FakePeekMessage)) ||
      iat != reinterpret_cast<void *>(&FakePeekMessage) ||
      runtime.protection.current_protect != PAGE_READONLY ||
      (mailbox.failure_flags.load(std::memory_order_acquire) &
       main_thread_query_failure_iat_page_protect) == 0) {
    return false;
  }
  return true;
}

bool TestSourceContract(int argc, char **argv) {
  if (argc != 7) {
    return false;
  }
  const auto source = ReadFile(argv[1]);
  const auto abi = ReadFile(argv[2]);
  const auto fixture = ReadFile(argv[3]);
  const auto documentation = ReadFile(argv[4]);
  const auto executable = ReadFile(argv[5]);
  const auto bridge = ReadFile(argv[6]);
  if (source.empty() || abi.empty() || fixture.empty() ||
      documentation.empty() || executable.empty() || bridge.empty()) {
    return false;
  }
  using namespace xar::ck3_11906;
  if (kMainThreadQueryMailboxV1CapabilityAdvertised ||
      kMainThreadQueryMailboxV1AdapterId != "ck3-1.19.0.6-msvc-x64" ||
      kPeekMessageWIatSlotRva != 0x3FD2EE8 ||
      kSdlWindowsPumpFirstPeekReturnRva != 0x3CE4222 ||
      kGlobalRngWrapperSlotRva != 0x4FEB1C8 ||
      kMainThreadQueryMaximumDrainPerPump != 1 ||
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs != 2) {
    return false;
  }
  constexpr std::array<std::string_view, 60> source_tokens{
      "InterlockedCompareExchangePointer",
      "kPeekMessageWIatSlotRva",
      "kSdlWindowsPumpFirstPeekReturnRva",
      "ReadExecutionStamp",
      "kGlobalRngOwnerThreadIdOffset",
      "Diagnostic only",
      "PublishObservedStamp",
      "SameExecutionBoundary(before, after)",
      "kJominiPausedOffset",
      "kGameStateDateRawOffset",
      "kMainThreadQueryMaximumDrainPerPump",
      "compare_exchange_strong",
      "MainThreadQueryMailboxStateV1::executing",
      "timeout_cancelled_before_execution",
      "main_thread_query_failure_reentry",
      "original_last_error",
      "SetLastError(original_last_error)",
      "GetCurrentThreadId()",
      "executor(context, before)",
      "DefaultMemoryQuery",
      "VirtualQuery",
      "DefaultMemoryProtect",
      "VirtualProtect",
      "PAGE_READONLY",
      "PAGE_READWRITE",
      "AtomicSwapReadOnlyIat",
      "UninstallMainThreadQueryMailboxV1",
      "active_hook_calls",
      "stop_requested",
      "SwitchToThread",
      "SignalMainThreadQueryMailboxProcessDetachV1",
      "kMainThreadTlsInitializedFlagRva",
      "tls_context_getter",
      "tls_main_thread_marker",
      "main_thread_query_failure_tls_identity",
      "ResetConsecutivePausedPumpProof",
      "SameVerifiedPumpIdentity",
      "executor_submission_disabled",
      "mailbox.permitted_executor",
      "mailbox.permitted_executor_secondary",
      "mailbox.permitted_executor_tertiary",
      "mailbox.permitted_executor_quaternary",
      "mailbox.permitted_executor_quinary",
      "mailbox.permitted_executor_senary",
      "mailbox.permitted_executor_septenary",
      "mailbox.permitted_executor_octonary",
      "mailbox.permitted_executor_nonary",
      "mailbox.permitted_executor_denary",
      "mailbox.permitted_executor_undenary",
      "mailbox.permitted_executor_duodenary",
      "mailbox.permitted_executor_thirdenary",
      "mailbox.permitted_executor_quattuordenary",
      "mailbox.permitted_executor_quindenary",
      "mailbox.permitted_executor_sexdenary",
      "mailbox.permitted_executor_septendenary",
      "mailbox.permitted_executor_octodenary",
      "mailbox.permitted_executor_novemdenary",
      "mailbox.permitted_executor_vigintary",
      "Process-lifetime pin",
      "mailbox.failure_flags.load(std::memory_order_acquire) != 0",
  };
  for (const auto token : source_tokens) {
    if (!Contains(source, token)) {
      return false;
    }
  }
  constexpr std::array<std::string_view, 68> contract_tokens{
      "0x3FD2EE8", "USER32!PeekMessageW", "0x3CE41E0",
      "0x3CE421C", "0x3CE4222", "0x3CFE7AB", "0x3CD3600",
      "0x3CD366C", "0x3CD3763", "0x3CD3D84", "0x3CD40D6",
      "0x3CD4727", "0x4FEB1C8", "0x356A0A0", "0x3D00000",
      "0x3FD2570", "GetCurrentThreadId", "single_slot",
      "timeout_cancel", "LastError", "advertised\": false",
      ".rdata", "VirtualQuery", "VirtualProtect", "PAGE_READONLY",
      "PAGE_READWRITE", "uninstall", "active_hook_calls",
      "PROCESS_DETACH", "WorkerMain",
      "0x57727ED", "0x7E7CDE", "0x7E7CE5", "0x3B86430",
      "0x3A2EC30", "0x3A2EC4D", "0x3A2EC58", "0x351F0D0",
      "0x3555820", "0x3555190", "0x3A2EE60", "0x4FE0A68",
      "TLS", "marker",
      "process_lifetime_pinned", "consecutive", "heartbeat",
      "executor_submission_enabled", "executed_requests",
      "application_main_thread_war_entry_v1", "rng_owner_tid",
      "tls_global", "tls_context", "tls_marker", "stamp_read_success",
      "fixed_executor_slots", "ExecuteCampaignRootContextMailboxQueryV1",
      "ExecuteLoadedFeatureManifestMailboxQueryV1",
      "ExecutePendingCharacterInteractionContextMailboxQueryV1",
      "ExecuteEventWindowContextMailboxQueryV1",
      "ExecuteTitleMapNavigationMailboxV1",
      "ExecuteZhongguoCaseSnapshotMailboxQueryV1",
      "ExecuteZhongguoResultCaseSnapshotMailboxQueryV1",
      "ExecuteZhongguoB2PipSnapshotMailboxQueryV1",
      "ExecuteZhongguoIncidentSnapshotMailboxQueryV1",
      "ExecuteZhongguoScoreboardStateMailboxQueryV1",
      "ExecuteZhongguoWorkforceCollectiveSnapshotMailboxQueryV1",
      "ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1",
  };
  for (const auto token : contract_tokens) {
    if (!Contains(abi, token) && !Contains(fixture, token) &&
        !Contains(documentation, token)) {
      return false;
    }
  }
  if (!StrictUtf8WithoutReplacement(documentation) ||
      CountOccurrences(documentation, "```mermaid") != 3 ||
      CountOccurrences(documentation, "```") != 6 ||
      !Contains(documentation, "paused_owner_verified_pump_epochs") ||
      !Contains(documentation, "live-confirmed") ||
      !Contains(abi, "\"live_observation\": true") ||
      !Contains(abi, "\"production_wiring\": true") ||
      !Contains(fixture, "\"live_paused_pump_observed\": true") ||
      Contains(abi, "\"permit_dll_unload\"") ||
      Contains(fixture, "\"unload_gate\"") ||
      Contains(source, "0x2909D30") || Contains(source, "war_entry")) {
    return false;
  }

  constexpr std::array<std::string_view, 83> bridge_tokens{
      "HeartbeatFrame",
      "main_thread_query_mailbox_v1",
      "installed",
      "stop_requested",
      "failure_flags",
      "pump_epochs",
      "consecutive_verified",
      "owner_thread_id",
      "executed_requests",
      "ready",
      "executor_submission_enabled = true",
      "WarEntryApplicationMainMailboxWorkerLifetime",
      "InstallMainThreadQueryMailboxV1",
      "UninstallMainThreadQueryMailboxV1",
      "worker_wait != WAIT_OBJECT_0",
      "g_lifecycle.store(2)",
      "SignalMainThreadQueryMailboxProcessDetachV1",
      "process-lifetime pinned",
      "\\\"stop\\\"",
      "\\\"failure\\\"",
      "\\\"owner_tid\\\"",
      "compare_exchange_strong(expected_lifecycle, 1)",
      "expected_lifecycle == 1 ? TRUE : FALSE",
      "kMainThreadQueryMailboxV1AdapterId",
      "kMainThreadQueryMailboxV1CandidateId",
      "typed_war_entry_route_actual_contact_combat_v3_battle_control_battle_transition_reinforcement_assignment_campaign_root_context_loaded_feature_manifest_pending_character_interaction_context_current_event_window_title_map_navigation",
      "ExecuteWarEntryAssessmentMailboxQueryV1",
      "ExecuteRouteContactHorizonMailboxQueryV1",
      "ExecuteActualContactScopeMailboxQueryV1",
      "ExecuteCombatSimulationInputsV3MailboxQuery",
      "ExecuteBattleControlSnapshotMailboxQueryV1",
      "ExecuteBattleTransitionMailboxQueryV1",
      "ExecuteBattleReinforcementAssignmentMailboxQueryV1",
      "ExecuteBattleTerminalTransitionMailboxQueryV1",
      "ExecuteCampaignRootContextMailboxQueryV1",
      "ExecuteLoadedFeatureManifestMailboxQueryV1",
      "ExecutePendingCharacterInteractionContextMailboxQueryV1",
      "ExecuteEventWindowContextMailboxQueryV1",
      "ExecuteTitleMapNavigationMailboxV1",
      "ExecuteZhongguoCaseSnapshotMailboxQueryV1",
      "ExecuteZhongguoResultCaseSnapshotMailboxQueryV1",
      "ExecuteZhongguoScoreboardStateMailboxQueryV1",
      "ExecuteZhongguoWorkforceCollectiveSnapshotMailboxQueryV1",
      "ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1",
      "kTitleMapNavigationV1Step",
      "ParseTitleMapNavigationRequestV1",
      "request.expected_snapshot_revision != state_revision",
      "BindTitleMapNavigationNativeEnvironmentV1",
      "BindTitleMapNavigationCameraEnvironmentV1",
      "RunTitleMapNavigationMailboxV1",
      "SerializeTitleMapNavigationResultV1",
      "query.dispatch_ticket_sequence",
      "TitleMapNavigationResultFrame",
      "TrySubmitMainThreadQueryV1",
      "permitted_executor",
      "permitted_executor_secondary",
      "permitted_executor_tertiary",
      "permitted_executor_quaternary",
      "permitted_executor_quinary",
      "permitted_executor_senary",
      "permitted_executor_septenary",
      "permitted_executor_octonary",
      "permitted_executor_nonary",
      "permitted_executor_denary",
      "permitted_executor_undenary",
      "permitted_executor_duodenary",
      "permitted_executor_thirdenary",
      "permitted_executor_quattuordenary",
      "permitted_executor_quindenary",
      "permitted_executor_sexdenary",
      "permitted_executor_septendenary",
      "permitted_executor_octodenary",
      "permitted_executor_novemdenary",
      "permitted_executor_vigintary",
      "kWarEntryAssessmentsV1FirstLiveMaximumTargets",
      "CaptureWarEntryBridgeFrame",
      "ReadSnapshot(*context->game",
      "void MaybeInstall(const xar::game::Snapshot &snapshot)",
      "!snapshot.paused",
      "!snapshot.map_ready",
      "!snapshot.has_played_character",
      "!snapshot.played_character_alive",
      "&mailbox_lifetime",
  };
  for (const auto token : bridge_tokens) {
    if (!Contains(bridge, token)) {
      return false;
    }
  }
  if (Contains(bridge, "g_lifecycle.exchange(1)") ||
      Contains(bridge, "game.command.main-thread-query-mailbox") ||
      Contains(bridge, "game.command.query-main-thread")) {
    return false;
  }
  // The stale-revision branch must precede every route snapshot/native call,
  // and a second worker snapshot must bind the main-thread result back to the
  // same published revision before serialization.
  const auto route_handler =
      bridge.find("kRouteContactHorizonV1StepPrefix");
  const auto route_revision_parse = bridge.find(
      "ParseRouteContactExpectedRevisionV1", route_handler);
  const auto route_revision_gate = bridge.find(
      "expected_revision != state_revision", route_revision_parse);
  const auto route_preflight_snapshot = bridge.find(
      "xar::game::Snapshot current_snapshot{}", route_revision_gate);
  const auto route_scope_gate = bridge.find(
      "RouteHostileScopeMatchesSnapshot", route_preflight_snapshot);
  const auto route_bind = bridge.find(
      "BindCurrentProcess(true)", route_scope_gate);
  const auto route_submit = bridge.find(
      "TrySubmitMainThreadQueryV1", route_bind);
  const auto route_queued_wait_budget = bridge.find(
      "kRouteContactHorizonV1QueuedWaitBudgetMilliseconds", route_submit);
  const auto route_executing_wait_slice = bridge.find(
      "kRouteContactHorizonV1ExecutingWaitSliceMilliseconds",
      route_queued_wait_budget);
  const auto route_completion_snapshot = bridge.find(
      "xar::game::Snapshot completion_snapshot{}",
      route_executing_wait_slice);
  const auto route_completion_read = bridge.find(
      "ReadSnapshot(game, completion_snapshot)",
      route_completion_snapshot);
  const auto route_revision_publish = bridge.find(
      "query.result.snapshot_revision = state_revision",
      route_completion_read);
  if (route_handler == std::string::npos ||
      route_revision_parse == std::string::npos ||
      route_revision_gate == std::string::npos ||
      route_preflight_snapshot == std::string::npos ||
      route_scope_gate == std::string::npos ||
      route_bind == std::string::npos || route_submit == std::string::npos ||
      route_queued_wait_budget == std::string::npos ||
      route_executing_wait_slice == std::string::npos ||
      route_completion_snapshot == std::string::npos ||
      route_completion_read == std::string::npos ||
      route_revision_publish == std::string::npos ||
      !(route_handler < route_revision_parse &&
        route_revision_parse < route_revision_gate &&
        route_revision_gate < route_preflight_snapshot &&
        route_preflight_snapshot < route_scope_gate &&
        route_scope_gate < route_bind && route_bind < route_submit &&
        route_submit < route_queued_wait_budget &&
        route_queued_wait_budget < route_executing_wait_slice &&
        route_executing_wait_slice < route_completion_snapshot &&
        route_completion_snapshot < route_completion_read &&
        route_completion_read < route_revision_publish)) {
    return false;
  }
  const auto lifetime_constructor = bridge.find(
      "explicit WarEntryApplicationMainMailboxWorkerLifetime(");
  const auto maybe_install = bridge.find(
      "void MaybeInstall(const xar::game::Snapshot &snapshot)");
  const auto iat_install = bridge.find(
      "installed_ = xar::ck3_11906::InstallMainThreadQueryMailboxV1(");
  const auto connected_session = bridge.find("void RunConnectedSession(");
  const auto hello_publish = bridge.find(
      "WriteFrame(pipe, HelloFrame(game))", connected_session);
  const auto readiness_observer = bridge.find(
      "&mailbox_lifetime", hello_publish);
  if (lifetime_constructor == std::string::npos ||
      maybe_install == std::string::npos || iat_install == std::string::npos ||
      connected_session == std::string::npos ||
      hello_publish == std::string::npos ||
      readiness_observer == std::string::npos ||
      !(lifetime_constructor < maybe_install && maybe_install < iat_install) ||
      !(connected_session < hello_publish &&
        hello_publish < readiness_observer)) {
    return false;
  }

  std::string digest;
  if (!Sha256Upper(executable, digest) ||
      digest != kMainThreadQueryMailboxV1ExecutableSha256 ||
      !ImportNameAtIat(executable, 0x3FD2EE8, "PeekMessageW") ||
      !ImportNameAtIat(executable, 0x3FD2570, "GetCurrentThreadId") ||
      !RvaIsReadOnlyDataSection(executable, 0x3FD2EE8, ".rdata")) {
    return false;
  }
  return BytesAt(executable, 0x3CFE7AB,
                 {0x48, 0x8D, 0x05, 0x2E, 0x5A, 0xFE, 0xFF}) &&
         BytesAt(executable, 0x3CFE7B2,
                 {0x48, 0x89, 0x85, 0x38, 0x02, 0x00, 0x00}) &&
         BytesAt(executable, 0x3CD3600,
                 {0x48, 0x8B, 0xC4, 0x48, 0x83, 0xEC, 0x68}) &&
         BytesAt(executable, 0x3CD3669,
                 {0x48, 0x8B, 0xCE, 0xFF, 0x96, 0x38, 0x02, 0x00, 0x00}) &&
         BytesAt(executable, 0x3CD3763,
                 {0xE8, 0x98, 0xFE, 0xFF, 0xFF}) &&
         BytesAt(executable, 0x3CD3D84,
                 {0xE8, 0x77, 0xF8, 0xFF, 0xFF}) &&
         BytesAt(executable, 0x3CD40D6,
                 {0xE8, 0x25, 0xF5, 0xFF, 0xFF}) &&
         BytesAt(executable, 0x3CD4727,
                 {0xE8, 0xD4, 0xEE, 0xFF, 0xFF}) &&
         BytesAt(executable, 0x3CE41E0,
                 {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
                  0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x60}) &&
         BytesAt(executable, 0x3CE421C,
                 {0xFF, 0x15, 0xC6, 0xEC, 0x2E, 0x00}) &&
         BytesAt(executable, 0x3CE4207,
                 {0x45, 0x33, 0xC9, 0xC7, 0x44, 0x24, 0x20, 0x01,
                  0x00, 0x00, 0x00, 0x45, 0x33, 0xC0, 0x48, 0x8D,
                  0x4C, 0x24, 0x30, 0x33, 0xD2, 0xFF, 0x15, 0xC6,
                  0xEC, 0x2E, 0x00, 0x85, 0xC0}) &&
         BytesAt(executable, 0x356A0AA,
                 {0x48, 0x8B, 0x1D, 0x17, 0x11, 0xA8, 0x01}) &&
         BytesAt(executable, 0x356A0BA,
                 {0xE8, 0x41, 0x5F, 0x79, 0x00}) &&
         BytesAt(executable, 0x356A0BF,
                 {0x48, 0x8B, 0x0B, 0x44, 0x8B, 0x41, 0x10,
                  0x44, 0x3B, 0xC0, 0x74, 0x20}) &&
         BytesAt(executable, 0x3D00000,
                 {0x48, 0xFF, 0x25, 0x69, 0x25, 0x2D, 0x00}) &&
         BytesAt(executable, 0x7E7CDE,
                 {0xC6, 0x05, 0x08, 0xAB, 0xF8, 0x04, 0x01, 0xE8,
                  0x46, 0xE7, 0x39, 0x03, 0xC6, 0x40, 0x20, 0x01}) &&
         BytesAt(executable, 0x3B86430,
                 {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x65, 0x48,
                  0x8B, 0x04, 0x25, 0x58, 0x00, 0x00, 0x00, 0x48,
                  0x8B, 0x08, 0xBA, 0x98, 0x32, 0x00, 0x00, 0x8B,
                  0x04, 0x0A, 0x41, 0xB8, 0xA0, 0x32, 0x00, 0x00}) &&
         BytesAt(executable, 0x3B864AF,
                 {0x49, 0x8D, 0x04, 0x08, 0x48, 0x83, 0xC4, 0x20,
                  0x5B, 0xC3}) &&
         BytesAt(executable, 0x3A2EC4D,
                 {0x0F, 0xB6, 0x05, 0x99, 0x3B, 0xD4, 0x01, 0x84,
                  0xC0, 0x74, 0x28, 0xE8, 0xD3, 0x77, 0x15, 0x00,
                  0x80, 0x78, 0x20, 0x00, 0x74, 0x1D}) &&
         BytesAt(executable, 0x351F0D9,
                 {0x48, 0x8B, 0x49, 0x08, 0x48, 0x8B, 0x01, 0xFF,
                  0x50, 0x18}) &&
         BytesAt(executable, 0x3555826,
                 {0x80, 0xB9, 0x60, 0x01, 0x00, 0x00, 0x00, 0x48,
                  0x8B, 0xD9, 0x75, 0x5B, 0x80, 0xB9, 0x89, 0x00,
                  0x00, 0x00, 0x00}) &&
         BytesAt(executable, 0x355587B,
                 {0x48, 0x8B, 0xCB, 0xE8, 0x0D, 0xF9, 0xFF,
                  0xFF}) &&
         BytesAt(executable, 0x35551F9,
                 {0x48, 0x8B, 0x35, 0x18, 0xA7, 0x1B, 0x02}) &&
         BytesAt(executable, 0x355523B,
                 {0x48, 0x8B, 0x06, 0x4C, 0x8B, 0x50, 0x08, 0x48,
                  0x8B, 0x47, 0x28, 0x48, 0x89, 0x54, 0x24, 0x28,
                  0x48, 0x89, 0x44, 0x24, 0x20, 0x4C, 0x8B, 0x4F,
                  0x20, 0x4C, 0x8B, 0x47, 0x18, 0x48, 0x8B, 0xCE,
                  0x41, 0xFF, 0xD2}) &&
         BytesAt(executable, 0x3A2EE9E,
                 {0x48, 0x8D, 0x4C, 0x24, 0x48, 0xFF, 0x15, 0xBF,
                  0x1B, 0x5B, 0x01}) &&
         BytesAt(executable, 0x3CD3760,
                 {0x8D, 0x48, 0x01, 0xE8, 0x98, 0xFE, 0xFF,
                  0xFF});
}

} // namespace

int main(int argc, char **argv) {
  if (!TestMailboxStateMachine()) {
    std::fprintf(stderr, "mailbox fixture failed at %s\n", g_failure_stage);
    return 1;
  }
  if (!TestSourceContract(argc, argv)) {
    return 2;
  }
  return 0;
}
