#include "xar_bridge/ck3_12004_person_title_tail_capture.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"

#include <cstring>
#include <map>
#include <memory>
#include <mutex>
#include <sstream>
#include <utility>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Held actual291B3B0 [B3B0,B3BF): three whole stack MOV instructions.
// No RIP-relative operand or relative control transfer requires relocation.
constexpr std::array<std::uint8_t, kPersonTitleTailPatchBytes12004>
    kWrapperPrologue{0x48, 0x89, 0x5C, 0x24, 0x10,
                     0x48, 0x89, 0x6C, 0x24, 0x18,
                     0x48, 0x89, 0x74, 0x24, 0x20};
using OwnerKey = std::pair<std::uintptr_t, std::uint32_t>;
using Record = std::shared_ptr<const PersonTitleTailCapture12004DTO>;
std::map<OwnerKey, Record> g_records;
std::mutex g_records_mutex;
std::uint64_t g_latest_sequence = 0;
PersonTitleTailCaptureBindings12004 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<PersonTitleTailOriginal12004> g_original{nullptr};
std::atomic<PersonTitleTailCaptureDetourState12004 *> g_active_state{nullptr};

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}

bool CopyNativeSource(void *, const void *source, void *destination,
                      std::size_t bytes) noexcept {
  return ck3_12002::current_stored_context_12003::CopyBytes(
      destination, source, bytes);
}

bool BindingReady(const PersonTitleTailCaptureBindings12004 &bindings) noexcept {
  const auto &memory = bindings.memory;
  return memory.enabled && memory.module_base != 0 &&
      memory.read_memory != nullptr &&
      memory.current_context_getter_identity ==
          memory.module_base + kPersonCarrierContextGetterRva12004;
}

bool ReadMemory(std::uintptr_t address, void *output,
                std::size_t bytes) noexcept {
  if (address == 0 || g_bindings.memory.read_memory == nullptr) return false;
  return FaultBoundary([&]() noexcept {
    return g_bindings.memory.read_memory(
        g_bindings.memory.read_context,
        reinterpret_cast<const void *>(address), output, bytes);
  });
}

template <typename T> std::optional<T> Copy(std::uintptr_t address) noexcept {
  T value{};
  if (!ReadMemory(address, &value, sizeof(value))) return std::nullopt;
  return value;
}

template <typename T>
std::optional<std::vector<T>> CopyArray(std::uintptr_t address,
                                        std::int32_t count) {
  if (address == 0) return std::nullopt;
  std::vector<T> values(static_cast<std::size_t>(count));
  if (!ReadMemory(address, values.data(), values.size() * sizeof(T)))
    return std::nullopt;
  return values;
}

PersonFollowing2922680Pc CopyPc(std::uintptr_t address) noexcept {
  PersonFollowing2922680Pc pc;
  pc.identity = address;
  pc.admitted = true;
  try {
    if (address == 0) {
      pc.reason = "pc_identity_null";
      return pc;
    }
    pc.count_i32 = Copy<std::int32_t>(address + 0xC);
    if (!pc.count_i32) {
      pc.reason = "pc_count_unread";
      return pc;
    }
    const auto count = *pc.count_i32;
    if (count < 0) {
      pc.reason = "pc_count_negative";
      return pc;
    }
    pc.properties.emplace();
    if (count == 0) {
      pc.properties->keys_u16.emplace();
      pc.properties->values_q64.emplace();
      pc.ready = true;
      return pc;
    }
    const auto keys = Copy<std::uintptr_t>(address);
    const auto values = Copy<std::uintptr_t>(address + 0x68);
    if (keys)
      pc.properties->keys_u16 = CopyArray<std::uint16_t>(*keys, count);
    if (values)
      pc.properties->values_q64 = CopyArray<std::int64_t>(*values, count);
    if (!pc.properties->keys_u16 && !pc.properties->values_q64)
      pc.reason = "pc_keys_and_values_unread";
    else if (!pc.properties->keys_u16)
      pc.reason = "pc_keys_unread";
    else if (!pc.properties->values_q64)
      pc.reason = "pc_values_unread";
    else pc.ready = true;
  } catch (...) {
    pc.ready = false;
    pc.reason = "pc_copy_failed";
  }
  return pc;
}

PersonTitleTailCapture12004DTO EmptyResult(std::uint32_t full_character_id) {
  PersonTitleTailCapture12004DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  dto.character_id = full_character_id;
  dto.prepared_pc.reason = "pc_unobserved";
  dto.model_aggregate_pc.reason = "pc_unobserved";
  return dto;
}

bool InitializeRuntime(const PersonTitleTailCaptureBindings12004 &bindings,
                       PersonTitleTailOriginal12004 original) noexcept {
  if (!BindingReady(bindings) || original == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_records_mutex);
    g_bindings = bindings;
    g_records.clear();
    g_latest_sequence = 0;
  }
  g_original.store(original, std::memory_order_release);
  g_available.store(true, std::memory_order_release);
  return true;
}

void WriteAbsoluteJump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
void *DefaultAlloc(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
void Fail(PersonTitleTailCaptureDetourState12004 &state,
          ActualLossWriterJournalInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

std::array<std::uint8_t, kPersonTitleTailPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kPersonTitleTailPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(),
      reinterpret_cast<std::uintptr_t>(&XarPersonTitleTailHook12004V1));
  return patch;
}

bool WritePatch(
    PersonTitleTailCaptureDetourState12004 &state,
    const std::array<std::uint8_t, kPersonTitleTailPatchBytes12004> &expected,
    const std::array<std::uint8_t, kPersonTitleTailPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.wrapper_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_loss_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_loss_install_protection : actual_loss_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_loss_install_rollback);
  return false;
}

void String(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
    else out << static_cast<char>(c);
  }
  out << '"';
}
void Reason(std::ostream &out, std::string_view value) {
  if (value.empty()) out << "null";
  else String(out, value);
}
template <typename T>
void Number(std::ostream &out, const std::optional<T> &value) {
  if (value) out << +*value;
  else out << "null";
}
void Pointer(std::ostream &out, const std::optional<std::uintptr_t> &value) {
  if (!value) { out << "null"; return; }
  out << "\"0x" << std::hex << *value << std::dec << '"';
}
void Boolean(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}
template <typename T>
void Array(std::ostream &out, const std::optional<std::vector<T>> &values,
           bool decimal_strings) {
  if (!values) { out << "null"; return; }
  out << '[';
  bool first = true;
  for (const auto value : *values) {
    if (!first) out << ',';
    first = false;
    if (decimal_strings) out << '"';
    out << +value;
    if (decimal_strings) out << '"';
  }
  out << ']';
}
void Pc(std::ostream &out, const PersonFollowing2922680Pc &pc) {
  out << "{\"ready\":" << (pc.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, pc.reason);
  out << ",\"admitted\":"; Boolean(out, pc.admitted);
  out << ",\"identity\":"; Pointer(out, pc.identity);
  out << ",\"count_i32\":"; Number(out, pc.count_i32);
  out << ",\"properties\":";
  if (!pc.properties) out << "null";
  else {
    out << "{\"keys_u16\":"; Array(out, pc.properties->keys_u16, false);
    out << ",\"values_q64\":"; Array(out, pc.properties->values_q64, true);
    out << '}';
  }
  out << ",\"weight_q100000\":" << pc.weight_q100000 << '}';
}

} // namespace

PersonTitleTailCaptureBindings12004 BindPersonTitleTailCaptureImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  PersonTitleTailCaptureBindings12004 bindings;
  bindings.memory = BindPersonCarrierDirect12004(
      image_base, kGameVersion, executable_sha256, &CopyNativeSource);
  if (bindings.memory.enabled)
    bindings.game_state_slot = reinterpret_cast<void **>(
        image_base + kGameStateSlotRva);
  return bindings;
}

bool InitializePersonTitleTailCaptureFixture12004(
    const PersonTitleTailCaptureBindings12004 &bindings,
    PersonTitleTailOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original);
}

void ObservePersonTitleTailCapture12004(
    std::uintptr_t model, std::uintptr_t source_pc,
    std::uintptr_t caller_return_address) noexcept {
  if (!g_available.load(std::memory_order_acquire) ||
      caller_return_address !=
          g_bindings.memory.module_base + kPersonTitleTailReturnRva12004)
    return;
  try {
    // Source attribution is the actual Model+8 receiver. No final Model lookup
    // or ownership getter is used by the observer or by the query reader.
    const auto character = model == 0 ? std::nullopt
        : Copy<std::uintptr_t>(model + 0x08);
    if (!character || *character == 0) return;
    const auto full_id = Copy<std::uint32_t>(*character + kCharacterFullIdOffset);
    if (!full_id) return;

    auto dto = EmptyResult(*full_id);
    dto.configured = true;
    dto.capture_observed = true;
    dto.character_identity = *character;
    dto.model_identity = model;
    dto.source_return_rva = kPersonTitleTailReturnRva12004;
    dto.inline_destination_identity = model + 0x10;
    const auto game_state = Copy<std::uintptr_t>(
        reinterpret_cast<std::uintptr_t>(g_bindings.game_state_slot));
    if (game_state && *game_state != 0)
      dto.capture_date_raw = Copy<std::int32_t>(
          *game_state + kGameStateDateOffset);
    dto.prepared_pc = CopyPc(source_pc);
    dto.model_aggregate_pc = CopyPc(model + 0x78);
    dto.ready = dto.prepared_pc.ready;
    if (!dto.ready) dto.reason = "prepared_pc_partial";

    const std::lock_guard lock(g_records_mutex);
    dto.capture_sequence = ++g_latest_sequence;
    auto record = std::make_shared<const PersonTitleTailCapture12004DTO>(
        std::move(dto));
    g_records.insert_or_assign(OwnerKey{*character, *full_id}, std::move(record));
  } catch (...) {
    // Capture failure must not prevent the natural native invocation.
  }
}

PersonTitleTailCapture12004DTO ReadPersonTitleTailCaptureForCharacter12004(
    std::uintptr_t actual_character, std::uint32_t full_character_id) noexcept {
  try {
    auto dto = EmptyResult(full_character_id);
    dto.configured = g_available.load(std::memory_order_acquire);
    if (!dto.configured) {
      dto.reason = "capture_not_configured";
      return dto;
    }
    const std::lock_guard lock(g_records_mutex);
    const auto found = g_records.find(OwnerKey{actual_character, full_character_id});
    if (found == g_records.end()) {
      dto.reason = "native_title_tail_unobserved";
      return dto;
    }
    return *found->second;
  } catch (...) {
    PersonTitleTailCapture12004DTO dto;
    dto.configured = g_available.load(std::memory_order_acquire);
    dto.character_id = full_character_id;
    dto.reason = "owned_capture_copy_failed";
    return dto;
  }
}

bool InstallPersonTitleTailCapture12004(
    PersonTitleTailCaptureDetourState12004 &state,
    const PersonTitleTailCaptureInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(actual_loss_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 ||
      !BindingReady(environment.bindings)) {
    Fail(state, actual_loss_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  PersonTitleTailCaptureDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_loss_install_already_installed);
    return false;
  }
  state.wrapper_target = environment.wrapper_target_override != 0
      ? environment.wrapper_target_override
      : environment.bindings.memory.module_base + kPersonTitleTailWrapperRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.wrapper_target),
                            kWrapperPrologue.data(), kWrapperPrologue.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kPersonTitleTailPatchBytes12004 +
      kActualLossWriterAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_loss_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kWrapperPrologue.data(), kWrapperPrologue.size());
  WriteAbsoluteJump(bytes + kWrapperPrologue.size(),
                    state.wrapper_target + kWrapperPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<PersonTitleTailOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kWrapperPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_loss_install_protection);
    else if (!flushed) Fail(state, actual_loss_install_flush);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kWrapperPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPersonTitleTailCapture12004(
    PersonTitleTailCaptureDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (!WritePatch(state, HookPatch(), state.original)) return false;
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline,
                                         0, MEM_RELEASE);
  if (freed) state.trampoline = nullptr;
  else Fail(state, actual_loss_install_allocation);
  return freed;
}

std::string SerializePersonTitleTailCapture12004(
    const PersonTitleTailCapture12004DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonTitleTailCaptureSchema12004);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"configured\":" << (dto.configured ? "true" : "false");
  out << ",\"capture_observed\":" << (dto.capture_observed ? "true" : "false");
  out << ",\"ready\":" << (dto.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, dto.reason);
  out << ",\"capture_sequence\":" << dto.capture_sequence;
  out << ",\"capture_date_raw\":"; Number(out, dto.capture_date_raw);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"model_identity\":"; Pointer(out, dto.model_identity);
  out << ",\"source_return_rva\":"; Pointer(out, dto.source_return_rva);
  out << ",\"inline_destination_identity\":";
  Pointer(out, dto.inline_destination_identity);
  out << ",\"prepared_pc\":"; Pc(out, dto.prepared_pc);
  out << ",\"model_aggregate_pc\":"; Pc(out, dto.model_aggregate_pc);
  out << ",\"weight_q100000\":" << dto.weight_q100000;
  out << ",\"actual_model_write_performed\":"
      << (dto.actual_model_write_performed ? "true" : "false");
  out << ",\"full_helper_ready\":" << (dto.full_helper_ready ? "true" : "false");
  out << ",\"source_stage\":\"post_composer_pre_final_outer_append\"";
  out << ",\"historical_capture\":true}";
  return out.str();
}

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonTitleTailHook12004V1(void *model, void *source_pc) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  ObservePersonTitleTailCapture12004(reinterpret_cast<std::uintptr_t>(model),
      reinterpret_cast<std::uintptr_t>(source_pc), caller);
  // Forward the natural native invocation exactly once with identical arguments.
  // Capturing calls no CK3 function; the query only copies owned records.
  return original(model, source_pc);
}

} // namespace xar::ck3_12004
