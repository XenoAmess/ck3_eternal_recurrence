#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"

#include <algorithm>
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

// Actual2BA95C0 [95C0,95D0): five whole instructions. The saved R11 is
// the original RSP, and these instructions contain no relative operand.
constexpr std::array<std::uint8_t, kPersonSixStagePatchBytes12004>
    kCountPrologue{0x4C, 0x8B, 0xDC, 0x53, 0x48, 0x83, 0xEC, 0x50,
                   0x49, 0x89, 0x73, 0x18, 0x49, 0x89, 0x7B, 0x20};
// Actual2438830 [8830,883F): six whole instructions. The CMP flags pass
// unchanged through the absolute trampoline jump to its later native JE.
constexpr std::array<std::uint8_t, kPersonSixStageAppendPatchBytes12004>
    kAppendPrologue{0x40, 0x53, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x30,
                    0x83, 0x7A, 0x0C, 0x00, 0x49, 0x8B, 0xD8};
using OwnerKey = std::pair<std::uintptr_t, std::uint32_t>;
using Record = std::shared_ptr<const PersonSixStageCapture12004DTO>;
std::map<OwnerKey, Record> g_records;
std::mutex g_records_mutex;
std::uint64_t g_latest_sequence = 0;
PersonSixStageCaptureBindings12004 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<PersonSixStageOriginal12004> g_original{nullptr};
std::atomic<PersonSixStageAppendOriginal12004> g_append_original{nullptr};
std::atomic<PersonSixStageCaptureDetourState12004 *> g_active_state{nullptr};

struct PendingStage {
  bool valid = false;
  OwnerKey owner{};
  std::uintptr_t context = 0;
  std::uint64_t sequence = 0;
  std::uint32_t index = 0;
};
// Both physical call sites belong to the same natural synchronous loop. This
// joins actual append arguments to its immediately preceding raw-count call.
thread_local PendingStage g_pending;

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
bool BindingReady(const PersonSixStageCaptureBindings12004 &bindings) noexcept {
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
PersonFollowing2922680Pc CopyPc(std::uintptr_t address,
                               std::int64_t weight) noexcept {
  PersonFollowing2922680Pc pc;
  pc.identity = address;
  pc.admitted = true;
  pc.weight_q100000 = weight;
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
    if (keys) pc.properties->keys_u16 = CopyArray<std::uint16_t>(*keys, count);
    if (values) pc.properties->values_q64 = CopyArray<std::int64_t>(*values, count);
    if (!pc.properties->keys_u16 && !pc.properties->values_q64)
      pc.reason = "pc_keys_and_values_unread";
    else if (!pc.properties->keys_u16) pc.reason = "pc_keys_unread";
    else if (!pc.properties->values_q64) pc.reason = "pc_values_unread";
    else pc.ready = true;
  } catch (...) {
    pc.ready = false;
    pc.reason = "pc_copy_failed";
  }
  return pc;
}

PersonPreparationModel12004 CopyPreparationModel(std::uintptr_t context) noexcept {
  PersonPreparationModel12004 result;
  result.observed = true;
  result.model_identity = context - 0x10;
  result.owner_character_identity = Copy<std::uintptr_t>(*result.model_identity + 8);
  if (!result.owner_character_identity) {
    result.reason = "preparation_model_owner_unread";
    return result;
  }
  if (*result.owner_character_identity == 0) {
    result.reason = "preparation_model_owner_null";
    return result;
  }
  result.owner_character_id = Copy<std::uint32_t>(
      *result.owner_character_identity + kCharacterFullIdOffset);
  if (!result.owner_character_id) {
    result.reason = "preparation_model_owner_id_unread";
    return result;
  }
  result.ready = true;
  return result;
}

PersonSixStagePietyCategory12004 CopyPietyCategory(
    std::uintptr_t character, std::uint32_t index) noexcept {
  PersonSixStagePietyCategory12004 result;
  result.observed = true;
  try {
    const auto image = g_bindings.memory.module_base;
    // Actual2BA94A8 selects this U16 for the 28BE0B0 category.
    result.property_key_u16 = Copy<std::uint16_t>(image + 0x4807608 + 8 * index);
    result.extension_identity = Copy<std::uintptr_t>(character + 0x1B0);
    if (!result.extension_identity) {
      result.reason = "piety_extension_unread";
      return result;
    }
    if (*result.extension_identity == 0) {
      result.category_i32 = 0;
    } else {
      // Complete cached actual28BE0B0: compare signed score against each
      // loaded threshold until the first greater value, then apply cap>=0.
      result.score_q64 = Copy<std::int64_t>(*result.extension_identity + 0x118);
      result.cap_i32 = Copy<std::int32_t>(*result.extension_identity + 0x120);
      if (!result.score_q64 || !result.cap_i32) {
        result.reason = "piety_category_source_unread";
        return result;
      }
      result.threshold_count_i32 = Copy<std::int32_t>(image + 0x54582E4);
      if (!result.threshold_count_i32) {
        result.reason = "piety_threshold_count_unread";
        return result;
      }
      std::int32_t rank = 0;
      if (*result.threshold_count_i32 > 0) {
        const auto thresholds = Copy<std::uintptr_t>(image + 0x54582D8);
        if (!thresholds || *thresholds == 0) {
          result.reason = "piety_threshold_pointer_unread";
          return result;
        }
        while (rank < *result.threshold_count_i32) {
          const auto threshold = Copy<std::int64_t>(
              *thresholds + sizeof(std::int64_t) * static_cast<std::size_t>(rank));
          if (!threshold) {
            result.reason = "piety_threshold_value_unread";
            return result;
          }
          result.thresholds_used_q64.push_back(*threshold);
          if (*result.score_q64 < *threshold) break;
          ++rank;
        }
      }
      result.category_i32 = *result.cap_i32 < 0
          ? rank : (std::min)(rank, *result.cap_i32);
    }
    result.ready = result.property_key_u16.has_value();
    result.reason = result.ready ? "" : "piety_property_key_unread";
  } catch (...) {
    result.ready = false;
    result.reason = "piety_category_copy_failed";
  }
  return result;
}

PersonSixStageClassifiedPietyRow12004 CopyClassifiedPietyRow(
    std::uintptr_t row_address, std::uint32_t native_index,
    const std::optional<std::uint16_t> &property_key) noexcept {
  PersonSixStageClassifiedPietyRow12004 row;
  row.native_index = native_index;
  try {
    row.pc_identity = Copy<std::uintptr_t>(row_address);
    row.scale_q64 = Copy<std::int64_t>(row_address + 8);
    const auto lookup = [&]() {
      if (!property_key) {
        row.reason = "classified_property_key_unread";
        return;
      }
      // Actual23036E0 tests FFFF before reading anything through the PC.
      if (*property_key == std::uint16_t{0xFFFF}) {
        row.lookup_selection = "sentinel";
        row.raw_value_q64 = std::int64_t{0};
        row.ready = true;
        return;
      }
      if (!row.pc_identity || *row.pc_identity == 0) {
        row.reason = "classified_row_pc_unread";
        return;
      }
      row.pc_count_i32 = Copy<std::int32_t>(*row.pc_identity + 0xC);
      if (!row.pc_count_i32) {
        row.reason = "classified_pc_count_unread";
        return;
      }
      if (*row.pc_count_i32 < 0) {
        row.reason = "classified_pc_count_negative";
        return;
      }
      if (*row.pc_count_i32 == 0) {
        row.lookup_selection = "empty";
        row.raw_value_q64 = std::int64_t{0};
        row.ready = true;
        return;
      }
      const auto keys = Copy<std::uintptr_t>(*row.pc_identity);
      if (!keys || *keys == 0) {
        row.reason = "classified_pc_keys_unread";
        return;
      }
      const auto count = static_cast<std::uintptr_t>(*row.pc_count_i32);
      std::uintptr_t candidate = 0;
      auto remaining = count;
      // Literal2303721..2303740: advance by remaining-half, then retain
      // half regardless of the comparison. Preserve the residual check too.
      while (remaining != 0) {
        const auto half = remaining >> 1;
        const auto probed = Copy<std::uint16_t>(
            *keys + (candidate + half) * sizeof(std::uint16_t));
        if (!probed) {
          row.reason = "classified_pc_key_unread";
          return;
        }
        if (*probed < *property_key) candidate += remaining - half;
        remaining = half;
      }
      const auto absent = [&]() {
        row.lookup_selection = "absent";
        row.raw_value_q64 = std::int64_t{0};
        row.ready = true;
      };
      if (candidate == count) {
        absent();
        return;
      }
      const auto residual = Copy<std::uint16_t>(
          *keys + candidate * sizeof(std::uint16_t));
      if (!residual) {
        row.reason = "classified_pc_key_unread";
        return;
      }
      if (*property_key < *residual) {
        absent();
        return;
      }
      const auto low_index = static_cast<std::uint32_t>(candidate);
      std::int32_t signed_index{};
      std::memcpy(&signed_index, &low_index, sizeof(signed_index));
      if (signed_index < 0) {
        absent();
        return;
      }
      row.lookup_selection = "mapped";
      row.selected_index_u32 = low_index;
      const auto values = Copy<std::uintptr_t>(*row.pc_identity + 0x68);
      if (!values || *values == 0) {
        row.reason = "classified_pc_values_unread";
        return;
      }
      row.raw_value_q64 = Copy<std::int64_t>(
          *values + static_cast<std::uintptr_t>(signed_index) * sizeof(std::int64_t));
      if (!row.raw_value_q64) {
        row.reason = "classified_pc_value_unread";
        return;
      }
      row.ready = true;
    };
    lookup();
    if (!row.scale_q64) {
      row.ready = false;
      if (row.reason.empty()) row.reason = "classified_row_scale_unread";
    }
  } catch (...) {
    row.ready = false;
    row.reason = "classified_piety_copy_failed";
  }
  return row;
}

PersonSixStageClassifiedPietyStage12004 CopyClassifiedPietyStage(
    std::uintptr_t context, std::uint32_t index,
    const std::optional<std::uint16_t> &property_key) noexcept {
  PersonSixStageClassifiedPietyStage12004 result;
  result.index = index;
  result.observed = true;
  result.property_key_u16 = property_key;
  try {
    result.row_count_i32 = Copy<std::int32_t>(context + 0xC);
    if (!result.row_count_i32) {
      result.reason = "classified_row_count_unread";
      return result;
    }
    if (*result.row_count_i32 < 0) {
      result.reason = "classified_row_count_negative";
      return result;
    }
    // Actual2438980's zero-count branch has no row-pointer or key demand.
    if (*result.row_count_i32 == 0) {
      result.ready = true;
      result.reason.clear();
      return result;
    }
    result.row_array_identity = Copy<std::uintptr_t>(context);
    if (!result.row_array_identity || *result.row_array_identity == 0) {
      result.reason = "classified_row_array_unread";
      return result;
    }
    const auto count = static_cast<std::uint32_t>(*result.row_count_i32);
    result.rows.reserve(count);
    for (std::uint32_t native_index = 0; native_index < count; ++native_index)
      result.rows.push_back(CopyClassifiedPietyRow(
          *result.row_array_identity + static_cast<std::uintptr_t>(native_index) * 16,
          native_index, property_key));
    result.ready = std::all_of(result.rows.begin(), result.rows.end(),
        [](const auto &row) { return row.ready; });
    result.reason = result.ready ? "" : "classified_piety_rows_partial";
  } catch (...) {
    result.ready = false;
    result.reason = "classified_piety_copy_failed";
  }
  return result;
}

PersonSixStageCapture12004DTO EmptyResult(std::uint32_t full_character_id) {
  PersonSixStageCapture12004DTO dto;
  dto.build_version = kGameVersion;
  dto.executable_sha256 = kExecutableSha256;
  dto.character_id = full_character_id;
  dto.preparation_model.reason = "preparation_model_unobserved";
  dto.pre_six_aggregate.pc.reason = "pre_six_aggregate_unobserved";
  dto.post_six_aggregate.pc.reason = "post_six_aggregate_unobserved";
  for (std::uint32_t i = 0; i < dto.stages.size(); ++i) {
    auto &stage = dto.stages[i];
    stage.index = i;
    dto.classified_piety_inputs[i].index = i;
    stage.first_pc.reason = "native_append_unobserved";
    stage.second_pc.reason = "native_append_unobserved";
    stage.first_pc.weight_q100000 = 0;
    stage.second_pc.weight_q100000 = 0;
  }
  return dto;
}
void UpdateReadiness(PersonSixStageCapture12004DTO &dto) {
  dto.raw_counts_ready = std::all_of(dto.stages.begin(), dto.stages.end(),
      [](const auto &stage) { return stage.observed && stage.raw_count_i32; });
  auto &base = dto.base_point_inputs;
  const bool base_observed = std::all_of(base.observed.begin(), base.observed.end(),
      [](bool observed) { return observed; });
  const bool base_readable = std::all_of(base.values_i32.begin(), base.values_i32.end(),
      [](const auto &value) { return value.has_value(); });
  base.ready = dto.raw_counts_ready && base_observed && base_readable;
  if (base.ready) base.reason.clear();
  else base.reason = base_observed && dto.raw_counts_ready
      ? "base_point_unread" : "base_point_unobserved";
  dto.ready = dto.capture_complete && dto.raw_counts_ready &&
      std::all_of(dto.stages.begin(), dto.stages.end(), [](const auto &stage) {
        return stage.first_pc.ready && stage.second_pc.ready;
      });
  dto.aggregate_postimage_inputs_ready = dto.ready &&
      dto.pre_six_aggregate.observed && dto.pre_six_aggregate.pc.ready;
  dto.aggregate_postimage_comparison_ready = dto.aggregate_postimage_inputs_ready &&
      dto.post_six_aggregate.observed && dto.post_six_aggregate.pc.ready;
  if (dto.ready) dto.reason.clear();
  else if (!dto.capture_complete) dto.reason = "native_six_stage_capture_open";
  else if (!dto.raw_counts_ready) dto.reason = "native_six_stage_counts_partial";
  else dto.reason = "native_six_stage_pc_partial";
}
bool InitializeRuntime(const PersonSixStageCaptureBindings12004 &bindings,
                       PersonSixStageOriginal12004 original,
                       PersonSixStageAppendOriginal12004 append_original) noexcept {
  if (!BindingReady(bindings) || original == nullptr || append_original == nullptr)
    return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_records_mutex);
    g_bindings = bindings;
    g_records.clear();
    g_latest_sequence = 0;
  }
  g_pending = {};
  g_original.store(original, std::memory_order_release);
  g_append_original.store(append_original, std::memory_order_release);
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
void Fail(PersonSixStageCaptureDetourState12004 &state,
          ActualLossWriterJournalInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}
template <std::size_t N>
std::array<std::uint8_t, N> HookPatch(std::uintptr_t hook) noexcept {
  std::array<std::uint8_t, N> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), hook);
  return patch;
}
auto CountPatch() noexcept {
  return HookPatch<kPersonSixStagePatchBytes12004>(
      reinterpret_cast<std::uintptr_t>(&XarPersonSixStageHook12004V1));
}
auto AppendPatch() noexcept {
  return HookPatch<kPersonSixStageAppendPatchBytes12004>(
      reinterpret_cast<std::uintptr_t>(&XarPersonSixStageAppendHook12004V1));
}
template <std::size_t N>
bool WritePatch(PersonSixStageCaptureDetourState12004 &state,
    std::uintptr_t target_identity,
    const std::array<std::uint8_t, N> &expected,
    const std::array<std::uint8_t, N> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(target_identity);
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
template <std::size_t N>
void *MakeTrampoline(PersonSixStageCaptureDetourState12004 &state,
    ActualLossWriterVirtualAllocV1 allocate, std::uintptr_t target,
    const std::array<std::uint8_t, N> &prologue) noexcept {
  constexpr auto bytes_count = N + kActualLossWriterAbsoluteJumpBytes12004;
  auto *result = allocate(state.memory_context, bytes_count,
                           MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (result == nullptr) {
    Fail(state, actual_loss_install_allocation);
    return nullptr;
  }
  auto *bytes = static_cast<std::uint8_t *>(result);
  std::memcpy(bytes, prologue.data(), N);
  WriteAbsoluteJump(bytes + N, target + N);
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context, result,
      bytes_count, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, result, bytes_count);
  if (executable && flushed) return result;
  Fail(state, executable ? actual_loss_install_flush : actual_loss_install_protection);
  (void)state.virtual_free(state.memory_context, result, 0, MEM_RELEASE);
  return nullptr;
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
void Pc(std::ostream &out, const PersonFollowing2922680Pc &pc, bool observed) {
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
  out << ",\"weight_q100000\":";
  if (observed) out << pc.weight_q100000;
  else out << "null";
  out << '}';
}

} // namespace

PersonFollowing2922680Pc CopyPersonSixStageAggregatePc12004(
    std::uintptr_t actual_pc) noexcept {
  if (g_available.load(std::memory_order_acquire)) return CopyPc(actual_pc, 0);
  PersonFollowing2922680Pc result;
  result.identity = actual_pc;
  result.weight_q100000 = 0;
  result.reason = "preparation_pc_copier_not_configured";
  return result;
}

PersonSixStageCaptureBindings12004 BindPersonSixStageCaptureImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  PersonSixStageCaptureBindings12004 bindings;
  bindings.memory = BindPersonCarrierDirect12004(
      image_base, kGameVersion, executable_sha256, &CopyNativeSource);
  if (bindings.memory.enabled)
    bindings.game_state_slot = reinterpret_cast<void **>(
        image_base + kGameStateSlotRva);
  return bindings;
}
bool InitializePersonSixStageCaptureFixture12004(
    const PersonSixStageCaptureBindings12004 &bindings,
    PersonSixStageOriginal12004 original,
    PersonSixStageAppendOriginal12004 append_original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original, append_original);
}

static void ObserveSixStageWithBaseline12004(
    std::uintptr_t character, std::uintptr_t context, std::uint32_t index,
    std::uintptr_t raw_return_bits,
    std::uintptr_t caller_return_address,
    const PersonFollowing2922680Pc *pre_six_aggregate,
    const PersonPreparationModel12004 *preparation_model,
    const std::optional<std::int32_t> *pre_count_base_point,
    const PersonSixStagePietyCategory12004 *pre_count_piety_category,
    const PersonSixStageClassifiedPietyStage12004 *pre_count_classified_piety) noexcept {
  if (!g_available.load(std::memory_order_acquire) ||
      caller_return_address !=
          g_bindings.memory.module_base + kPersonSixStageReturnRva12004 ||
      character == 0 || context == 0 || index >= kPersonSixStageCount12004)
    return;
  try {
    const auto full_id = Copy<std::uint32_t>(character + kCharacterFullIdOffset);
    if (!full_id) return;
    const OwnerKey owner{character, *full_id};
    const auto low_bits = static_cast<std::uint32_t>(raw_return_bits);
    std::int32_t raw = 0;
    std::memcpy(&raw, &low_bits, sizeof(raw));
    const auto game_state = Copy<std::uintptr_t>(
        reinterpret_cast<std::uintptr_t>(g_bindings.game_state_slot));
    const auto date = game_state && *game_state != 0
        ? Copy<std::int32_t>(*game_state + kGameStateDateOffset) : std::nullopt;

    const std::lock_guard lock(g_records_mutex);
    const auto found = g_records.find(owner);
    const bool fresh = index == 0 || found == g_records.end() ||
        found->second->context_identity != context ||
        found->second->capture_complete;
    auto dto = fresh ? EmptyResult(*full_id) : *found->second;
    if (fresh) {
      dto.configured = true;
      dto.capture_observed = true;
      dto.capture_sequence = ++g_latest_sequence;
      dto.capture_date_raw = date;
      dto.capture_thread_id = GetCurrentThreadId();
      dto.character_identity = character;
      dto.context_identity = context;
      dto.source_return_rva = kPersonSixStageReturnRva12004;
      if (index == 0 && preparation_model != nullptr) {
        dto.preparation_model = *preparation_model;
        if (dto.preparation_model.ready)
          dto.preparation_model.owner_matches_capture =
              dto.preparation_model.owner_character_identity == character &&
              dto.preparation_model.owner_character_id == *full_id;
      }
      if (index == 0 && pre_six_aggregate != nullptr) {
        dto.pre_six_aggregate.observed = true;
        dto.pre_six_aggregate.pc = *pre_six_aggregate;
      }
    }
    auto &stage = dto.stages[index];
    stage.observed = true;
    stage.raw_count_i32 = raw;
    if (pre_count_base_point != nullptr) {
      dto.base_point_inputs.observed[index] = true;
      dto.base_point_inputs.values_i32[index] = *pre_count_base_point;
    }
    if (pre_count_piety_category != nullptr)
      dto.piety_category_inputs[index] = *pre_count_piety_category;
    if (pre_count_classified_piety != nullptr)
      dto.classified_piety_inputs[index] = *pre_count_classified_piety;
    UpdateReadiness(dto);
    const auto sequence = dto.capture_sequence;
    auto record = std::make_shared<const PersonSixStageCapture12004DTO>(std::move(dto));
    g_records.insert_or_assign(owner, std::move(record));
    g_pending = PendingStage{true, owner, context, sequence, index};
  } catch (...) {
    // Capture is auxiliary; it cannot replace or prevent the native callback.
  }
}

void ObservePersonSixStageCapture12004(
    std::uintptr_t character, std::uintptr_t context, std::uint32_t index,
    std::uintptr_t raw_return_bits,
    std::uintptr_t caller_return_address) noexcept {
  ObserveSixStageWithBaseline12004(character, context, index, raw_return_bits,
      caller_return_address, nullptr, nullptr, nullptr, nullptr, nullptr);
}

std::uintptr_t InvokePersonSixStageCapture12004(
    void *character, void *context, std::uint32_t index,
    std::uintptr_t caller_return_address) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
  std::optional<PersonFollowing2922680Pc> pre_six_aggregate;
  std::optional<PersonPreparationModel12004> preparation_model;
  std::optional<std::int32_t> pre_count_base_point;
  std::optional<PersonSixStagePietyCategory12004> pre_count_piety_category;
  std::optional<PersonSixStageClassifiedPietyStage12004> pre_count_classified_piety;
  const bool capture_this_call = g_available.load(std::memory_order_acquire) &&
      index < kPersonSixStageCount12004 &&
      character != nullptr && context != nullptr &&
      caller_return_address ==
          g_bindings.memory.module_base + kPersonSixStageReturnRva12004;
  if (capture_this_call) {
    // Actual2BA960E consumes this signed DWORD for this exact stage. Own
    // each input before its original call, without substituting a later value.
    pre_count_base_point = Copy<std::int32_t>(
        reinterpret_cast<std::uintptr_t>(character) + 0xC0 + 4 * index);
    pre_count_piety_category = CopyPietyCategory(
        reinterpret_cast<std::uintptr_t>(character), index);
    pre_count_classified_piety = CopyClassifiedPietyStage(
        reinterpret_cast<std::uintptr_t>(context), index,
        pre_count_piety_category->property_key_u16);
  }
  if (capture_this_call && index == 0) {
    // Native2438964 passes this inline PC to2303100. Own it before the
    // first count callback can observe or modify the aggregate.
    preparation_model = CopyPreparationModel(reinterpret_cast<std::uintptr_t>(context));
    pre_six_aggregate = CopyPc(reinterpret_cast<std::uintptr_t>(context) + 0x68, 0);
  }
  const auto result = original(character, context, index);
  ObserveSixStageWithBaseline12004(reinterpret_cast<std::uintptr_t>(character),
      reinterpret_cast<std::uintptr_t>(context), index, result,
      caller_return_address, pre_six_aggregate ? &*pre_six_aggregate : nullptr,
      preparation_model ? &*preparation_model : nullptr,
      capture_this_call ? &pre_count_base_point : nullptr,
      pre_count_piety_category ? &*pre_count_piety_category : nullptr,
      pre_count_classified_piety ? &*pre_count_classified_piety : nullptr);
  return result;
}

void ObservePersonSixStageAppend12004(
    std::uintptr_t context, std::uintptr_t source_pc,
    std::int64_t weight_q100000,
    std::uintptr_t caller_return_address) noexcept {
  if (!g_available.load(std::memory_order_acquire) || !g_pending.valid ||
      context != g_pending.context) return;
  const auto base = g_bindings.memory.module_base;
  const bool first = caller_return_address ==
      base + kPersonSixStageFirstAppendReturnRva12004;
  const bool second = caller_return_address ==
      base + kPersonSixStageSecondAppendReturnRva12004;
  if (!first && !second) return;
  try {
    auto pc = CopyPc(source_pc, weight_q100000);
    const std::lock_guard lock(g_records_mutex);
    const auto found = g_records.find(g_pending.owner);
    if (found == g_records.end() ||
        found->second->capture_sequence != g_pending.sequence ||
        found->second->context_identity != context ||
        found->second->capture_complete) return;
    auto dto = *found->second;
    auto &stage = dto.stages[g_pending.index];
    if (first) {
      stage.first_append_observed = true;
      stage.first_pc = std::move(pc);
    } else {
      stage.second_append_observed = true;
      stage.second_pc = std::move(pc);
    }
    UpdateReadiness(dto);
    g_records.insert_or_assign(g_pending.owner,
        std::make_shared<const PersonSixStageCapture12004DTO>(std::move(dto)));
  } catch (...) {
    // The original append still runs exactly once with its untouched arguments.
  }
}

void CompletePersonSixStageCapture12004(
    std::uintptr_t actual_character, std::uint32_t full_character_id,
    std::uintptr_t actual_context) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return;
  try {
    const OwnerKey owner{actual_character, full_character_id};
    const auto query_thread = GetCurrentThreadId();
    const std::lock_guard lock(g_records_mutex);
    const auto found = g_records.find(owner);
    if (found == g_records.end() ||
        found->second->capture_thread_id != query_thread ||
        !found->second->raw_counts_ready || found->second->capture_complete ||
        (actual_context != 0 &&
         found->second->context_identity != actual_context)) return;
    auto dto = *found->second;
    dto.capture_complete = true;
    dto.query_thread_id = query_thread;
    // This is the actual same-thread completion observation, not a relabelled
    // current final Model or a reconstructed immediate-last-append snapshot.
    dto.post_six_aggregate.observed = true;
    dto.post_six_aggregate.pc = CopyPc(*dto.context_identity + 0x68, 0);
    for (auto &stage : dto.stages) {
      if (!stage.observed) continue;
      // Only the paused query after this thread's finished natural native loop
      // turns an absent physical append into a known native gate skip.
      if (!stage.first_append_observed) {
        stage.first_pc.ready = true;
        stage.first_pc.admitted = false;
        stage.first_pc.reason.clear();
      }
      if (!stage.second_append_observed) {
        stage.second_pc.ready = true;
        stage.second_pc.admitted = false;
        stage.second_pc.reason.clear();
      }
    }
    UpdateReadiness(dto);
    g_records.insert_or_assign(owner,
        std::make_shared<const PersonSixStageCapture12004DTO>(std::move(dto)));
    if (g_pending.valid && g_pending.owner == owner) g_pending = {};
  } catch (...) {
    // A failed owned copy leaves the prior capture open and explicitly partial.
  }
}

PersonSixStageCapture12004DTO ReadPersonSixStageCaptureForCharacter12004(
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
      dto.reason = "native_six_stage_unobserved";
      return dto;
    }
    return *found->second;
  } catch (...) {
    PersonSixStageCapture12004DTO dto;
    dto.configured = g_available.load(std::memory_order_acquire);
    dto.character_id = full_character_id;
    dto.reason = "owned_capture_copy_failed";
    return dto;
  }
}

bool InstallPersonSixStageCapture12004(
    PersonSixStageCaptureDetourState12004 &state,
    const PersonSixStageCaptureInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(actual_loss_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !BindingReady(environment.bindings)) {
    Fail(state, actual_loss_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  PersonSixStageCaptureDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_loss_install_already_installed);
    return false;
  }
  state.count_target = environment.count_target_override != 0
      ? environment.count_target_override
      : environment.bindings.memory.module_base + kPersonSixStageCountRva12004;
  state.append_target = environment.append_target_override != 0
      ? environment.append_target_override
      : environment.bindings.memory.module_base + kPersonSixStageAppendRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.count_target),
                   kCountPrologue.data(), kCountPrologue.size()) == 0 &&
            std::memcmp(reinterpret_cast<const void *>(state.append_target),
                   kAppendPrologue.data(), kAppendPrologue.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  state.count_trampoline = MakeTrampoline(state, allocate, state.count_target,
                                         kCountPrologue);
  state.append_trampoline = state.count_trampoline == nullptr ? nullptr
      : MakeTrampoline(state, allocate, state.append_target, kAppendPrologue);
  const bool initialized = state.count_trampoline != nullptr &&
      state.append_trampoline != nullptr && InitializeRuntime(environment.bindings,
          reinterpret_cast<PersonSixStageOriginal12004>(state.count_trampoline),
          reinterpret_cast<PersonSixStageAppendOriginal12004>(state.append_trampoline));
  const bool count_patched = initialized && WritePatch(state, state.count_target,
                                                       kCountPrologue, CountPatch());
  const bool append_patched = count_patched && WritePatch(state, state.append_target,
                                                       kAppendPrologue, AppendPatch());
  if (!append_patched) {
    if (count_patched)
      (void)WritePatch(state, state.count_target, CountPatch(), kCountPrologue);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    g_append_original.store(nullptr, std::memory_order_release);
    if (state.count_trampoline != nullptr)
      (void)state.virtual_free(state.memory_context, state.count_trampoline, 0, MEM_RELEASE);
    if (state.append_trampoline != nullptr)
      (void)state.virtual_free(state.memory_context, state.append_trampoline, 0, MEM_RELEASE);
    state.count_trampoline = nullptr;
    state.append_trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kCountPrologue;
  state.append_original = kAppendPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPersonSixStageCapture12004(
    PersonSixStageCaptureDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (!WritePatch(state, state.append_target, AppendPatch(), state.append_original))
    return false;
  if (!WritePatch(state, state.count_target, CountPatch(), state.original)) {
    (void)WritePatch(state, state.append_target, state.append_original, AppendPatch());
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_append_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool count_freed = state.virtual_free(state.memory_context,
      state.count_trampoline, 0, MEM_RELEASE);
  const bool append_freed = state.virtual_free(state.memory_context,
      state.append_trampoline, 0, MEM_RELEASE);
  if (count_freed) state.count_trampoline = nullptr;
  if (append_freed) state.append_trampoline = nullptr;
  if (!count_freed || !append_freed) Fail(state, actual_loss_install_allocation);
  return count_freed && append_freed;
}

std::string SerializePersonSixStageCapture12004(
    const PersonSixStageCapture12004DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonSixStageCaptureSchema12004);
  out << ",\"build_version\":"; String(out, dto.build_version);
  out << ",\"executable_sha256\":"; String(out, dto.executable_sha256);
  out << ",\"configured\":" << (dto.configured ? "true" : "false");
  out << ",\"capture_observed\":" << (dto.capture_observed ? "true" : "false");
  out << ",\"capture_complete\":" << (dto.capture_complete ? "true" : "false");
  out << ",\"ready\":" << (dto.ready ? "true" : "false");
  out << ",\"raw_counts_ready\":" << (dto.raw_counts_ready ? "true" : "false");
  out << ",\"reason\":"; Reason(out, dto.reason);
  out << ",\"capture_sequence\":" << dto.capture_sequence;
  out << ",\"capture_date_raw\":"; Number(out, dto.capture_date_raw);
  out << ",\"capture_thread_id\":"; Number(out, dto.capture_thread_id);
  out << ",\"query_thread_id\":"; Number(out, dto.query_thread_id);
  out << ",\"character_id\":"; Number(out, dto.character_id);
  out << ",\"character_identity\":"; Pointer(out, dto.character_identity);
  out << ",\"context_identity\":"; Pointer(out, dto.context_identity);
  out << ",\"source_return_rva\":"; Pointer(out, dto.source_return_rva);
  out << ",\"piety_category_inputs\":{\"source_stage\":\"before_each_original_count\""
      << ",\"getter_rva\":42721456,\"key_table_rva\":75527688,\"key_stride_bytes\":8"
      << ",\"character_extension_offset\":432,\"score_offset\":280,\"cap_offset\":288"
      << ",\"threshold_pointer_rva\":88441560,\"threshold_count_rva\":88441572,\"stages\":[";
  for (std::size_t i = 0; i < dto.piety_category_inputs.size(); ++i) {
    if (i != 0) out << ',';
    const auto &input = dto.piety_category_inputs[i];
    out << "{\"index\":" << i << ",\"observed\":" << (input.observed ? "true" : "false")
        << ",\"ready\":" << (input.ready ? "true" : "false") << ",\"reason\":";
    Reason(out, input.reason);
    out << ",\"property_key_u16\":"; Number(out, input.property_key_u16);
    out << ",\"extension_identity\":"; Pointer(out, input.extension_identity);
    out << ",\"score_q64\":";
    if (input.score_q64) out << '"' << *input.score_q64 << '"'; else out << "null";
    out << ",\"cap_i32\":"; Number(out, input.cap_i32);
    out << ",\"threshold_count_i32\":"; Number(out, input.threshold_count_i32);
    out << ",\"thresholds_used_q64\":[";
    for (std::size_t j = 0; j < input.thresholds_used_q64.size(); ++j) {
      if (j != 0) out << ',';
      out << '"' << input.thresholds_used_q64[j] << '"';
    }
    out << "],\"category_i32\":"; Number(out, input.category_i32);
    out << '}';
  }
  out << "]}";
  out << ",\"classified_piety_inputs\":{\"source_stage\":\"before_each_original_count\""
      << ",\"context_rows_offset\":0,\"context_count_offset\":12,\"row_stride_bytes\":16"
      << ",\"row_pc_offset\":0,\"row_scale_offset\":8,\"classified_reader_rva\":"
      << std::uintptr_t{0x2438980} << ",\"key_lookup_rva\":" << std::uintptr_t{0x23036E0}
      << ",\"stages\":[";
  for (std::size_t i = 0; i < dto.classified_piety_inputs.size(); ++i) {
    if (i != 0) out << ',';
    const auto &input = dto.classified_piety_inputs[i];
    out << "{\"index\":" << input.index << ",\"observed\":" << (input.observed ? "true" : "false")
        << ",\"ready\":" << (input.ready ? "true" : "false") << ",\"reason\":";
    Reason(out, input.reason);
    out << ",\"property_key_u16\":"; Number(out, input.property_key_u16);
    out << ",\"row_count_i32\":"; Number(out, input.row_count_i32);
    out << ",\"row_array_identity\":"; Pointer(out, input.row_array_identity);
    out << ",\"rows\":[";
    for (std::size_t j = 0; j < input.rows.size(); ++j) {
      if (j != 0) out << ',';
      const auto &row = input.rows[j];
      out << "{\"native_index\":" << row.native_index << ",\"ready\":"
          << (row.ready ? "true" : "false") << ",\"reason\":";
      Reason(out, row.reason);
      out << ",\"pc_identity\":"; Pointer(out, row.pc_identity);
      out << ",\"pc_count_i32\":"; Number(out, row.pc_count_i32);
      out << ",\"lookup_selection\":"; String(out, row.lookup_selection);
      out << ",\"selected_index_u32\":"; Number(out, row.selected_index_u32);
      out << ",\"raw_value_q64\":";
      if (row.raw_value_q64) out << '"' << *row.raw_value_q64 << '"'; else out << "null";
      out << ",\"scale_q64\":";
      if (row.scale_q64) out << '"' << *row.scale_q64 << '"'; else out << "null";
      out << '}';
    }
    out << "]}";
  }
  out << "]}";
  out << ",\"base_point_inputs\":{\"source_stage\":\"before_each_original_count\"";
  out << ",\"character_offset\":192,\"stride_bytes\":4,\"observed\":[";
  for (std::size_t i = 0; i < dto.base_point_inputs.observed.size(); ++i) {
    if (i != 0) out << ',';
    out << (dto.base_point_inputs.observed[i] ? "true" : "false");
  }
  out << "],\"values_i32\":[";
  for (std::size_t i = 0; i < dto.base_point_inputs.values_i32.size(); ++i) {
    if (i != 0) out << ',';
    Number(out, dto.base_point_inputs.values_i32[i]);
  }
  out << "],\"ready\":" << (dto.base_point_inputs.ready ? "true" : "false");
  out << ",\"reason\":"; Reason(out, dto.base_point_inputs.reason);
  out << '}';
  out << ",\"preparation_model\":{\"observed\":"
      << (dto.preparation_model.observed ? "true" : "false");
  out << ",\"ready\":" << (dto.preparation_model.ready ? "true" : "false");
  out << ",\"reason\":"; Reason(out, dto.preparation_model.reason);
  out << ",\"model_identity\":"; Pointer(out, dto.preparation_model.model_identity);
  out << ",\"owner_character_identity\":";
  Pointer(out, dto.preparation_model.owner_character_identity);
  out << ",\"owner_character_id\":"; Number(out, dto.preparation_model.owner_character_id);
  out << ",\"owner_matches_capture\":"; Boolean(out, dto.preparation_model.owner_matches_capture);
  out << ",\"context_offset\":16,\"owner_offset\":8";
  out << ",\"source_stage\":\"before_first_count_callback\"}";
  out << ",\"pre_six_aggregate\":{\"observed\":"
      << (dto.pre_six_aggregate.observed ? "true" : "false");
  out << ",\"source_stage\":\"before_first_count_callback\"";
  out << ",\"context_pc_offset\":104,\"pc\":";
  Pc(out, dto.pre_six_aggregate.pc, false);
  out << "},\"post_six_aggregate\":{\"observed\":"
      << (dto.post_six_aggregate.observed ? "true" : "false");
  out << ",\"source_stage\":\"same_thread_capture_completion\"";
  out << ",\"context_pc_offset\":104,\"pc\":";
  Pc(out, dto.post_six_aggregate.pc, false);
  out << "},\"aggregate_postimage_inputs_ready\":"
      << (dto.aggregate_postimage_inputs_ready ? "true" : "false");
  out << ",\"aggregate_postimage_comparison_ready\":"
      << (dto.aggregate_postimage_comparison_ready ? "true" : "false");
  out << ",\"stages\":[";
  bool first = true;
  for (const auto &stage : dto.stages) {
    if (!first) out << ',';
    first = false;
    out << "{\"index\":" << stage.index;
    out << ",\"observed\":" << (stage.observed ? "true" : "false");
    out << ",\"raw_count_i32\":"; Number(out, stage.raw_count_i32);
    out << ",\"first_append_observed\":"
        << (stage.first_append_observed ? "true" : "false");
    out << ",\"second_append_observed\":"
        << (stage.second_append_observed ? "true" : "false");
    out << ",\"first_pc\":"; Pc(out, stage.first_pc, stage.first_append_observed);
    out << ",\"second_pc\":"; Pc(out, stage.second_pc, stage.second_append_observed);
    out << '}';
  }
  out << "]";
  out << ",\"actual_model_write_performed\":"
      << (dto.actual_model_write_performed ? "true" : "false");
  out << ",\"full_helper_ready\":" << (dto.full_helper_ready ? "true" : "false");
  out << ",\"source_stage\":\"ordered_six_attribute_native_calls\"";
  out << ",\"historical_capture\":" << (dto.historical_capture ? "true" : "false") << '}';
  return out.str();
}

PersonSixStageQuery12004DTO CollectPersonSixStageQuery12004(
    void **character_storage_slot, std::span<const std::int32_t> requested_ids,
    std::uint64_t snapshot_revision, std::int64_t observed_date_raw) noexcept {
  PersonSixStageQuery12004DTO dto;
  dto.snapshot_revision = snapshot_revision;
  dto.observed_date_raw = observed_date_raw;
  try {
    dto.character_captures.reserve(requested_ids.size());
    const auto storage = Copy<std::uintptr_t>(
        reinterpret_cast<std::uintptr_t>(character_storage_slot));
    const auto rows = storage && *storage != 0
        ? Copy<std::uintptr_t>(*storage + 0x20) : std::nullopt;
    const auto capacity = storage && *storage != 0
        ? Copy<std::uint32_t>(*storage + 0x2C) : std::nullopt;
    for (const auto requested_id : requested_ids) {
      const auto full_id = static_cast<std::uint32_t>(requested_id);
      const auto index = full_id & 0x00FFFFFFU;
      std::optional<std::uintptr_t> character;
      if (rows && *rows != 0 && capacity && index < *capacity) {
        const auto candidate = Copy<std::uintptr_t>(
            *rows + static_cast<std::uintptr_t>(index) * 16 + 8);
        if (candidate && *candidate != 0) {
          const auto actual_id = Copy<std::uint32_t>(
              *candidate + kCharacterFullIdOffset);
          if (actual_id && *actual_id == full_id) character = *candidate;
        }
      }
      if (character) {
        CompletePersonSixStageCapture12004(*character, full_id, 0);
        dto.character_captures.push_back(
            ReadPersonSixStageCaptureForCharacter12004(*character, full_id));
      } else {
        auto empty = EmptyResult(full_id);
        empty.configured = g_available.load(std::memory_order_acquire);
        empty.reason = empty.configured ? "character_resolution_unavailable"
                                        : "capture_not_configured";
        dto.character_captures.push_back(std::move(empty));
      }
    }
  } catch (...) {
    // The owned query can remain partial without replaying native work or
    // borrowing another generation's capture to fill a failed resolution.
  }
  return dto;
}

std::string SerializePersonSixStageQuery12004(
    const PersonSixStageQuery12004DTO &dto) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kPersonSixStageQuerySchema12004);
  out << ",\"snapshot_revision\":" << dto.snapshot_revision;
  out << ",\"observed_date_raw\":" << dto.observed_date_raw;
  out << ",\"character_captures\":[";
  bool first = true;
  for (const auto &capture : dto.character_captures) {
    if (!first) out << ',';
    first = false;
    out << SerializePersonSixStageCapture12004(capture);
  }
  out << "]}";
  return out.str();
}

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonSixStageHook12004V1(void *character, void *context,
                            std::uint32_t index) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  // Native result is obtained exactly once. Its complete RAX representation is
  // returned untouched; only its low EAX bits are copied as the signed count.
  return InvokePersonSixStageCapture12004(character, context, index, caller);
}
extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonSixStageAppendHook12004V1(void *context, void *source_pc,
                                  std::int64_t weight_q100000) noexcept {
  const auto original = g_append_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  ObservePersonSixStageAppend12004(reinterpret_cast<std::uintptr_t>(context),
      reinterpret_cast<std::uintptr_t>(source_pc), weight_q100000, caller);
  return original(context, source_pc, weight_q100000);
}

} // namespace xar::ck3_12004
