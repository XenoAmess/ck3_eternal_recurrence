#include "xar_bridge/ck3_12004_council_task_owner_monthly_piety.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstring>

#if defined(_MSC_VER)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
using Failure = CouncilTaskOwnerMonthlyPietyFailure12004;

bool Read(CouncilTaskMonthlyPietyReadMemory12004 read, void *context,
          const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output || !size) return false;
  if (read) return read(context, address, output, size);
#if defined(_MSC_VER)
  __try { std::memcpy(output, address, size); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(output, address, size);
#endif
  return true;
}

template <typename Function, typename Return, typename... Args>
bool Invoke(Function function, Return &out, Args... args) noexcept {
  if (!function) return false;
#if defined(_MSC_VER)
  __try { out = function(args...); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  out = function(args...);
#endif
  return true;
}

bool Destroy(NativeCouncilTaskModifierDestroy12004 destroy, void *storage) noexcept {
  if (!destroy) return false;
#if defined(_MSC_VER)
  __try { destroy(storage); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  destroy(storage);
#endif
  return true;
}

// The native keyword CString is borrowed. Copy it without std::string ABI
// operations and never destroy it. This is the existing actual4 CString layout.
bool CopyKeyword(CouncilTaskMonthlyPietyReadMemory12004 read, void *context,
                 const void *object, std::array<char, 64> &out,
                 std::size_t &copied_size) noexcept {
  if (!object) return false;
  const auto *bytes = static_cast<const std::byte *>(object);
  std::uint64_t size = 0, capacity = 0;
  if (!Read(read, context, bytes + 0x10, &size, sizeof(size)) ||
      !Read(read, context, bytes + 0x18, &capacity, sizeof(capacity)) ||
      size == 0 || size >= out.size() || size > capacity) return false;
  const void *text = object;
  if (capacity > 15 && (!Read(read, context, object, &text, sizeof(text)) || !text))
    return false;
  copied_size = static_cast<std::size_t>(size);
  return Read(read, context, text, out.data(), copied_size);
}
} // namespace

CouncilTaskOwnerMonthlyPietyBindings12004 BindCouncilTaskOwnerMonthlyPiety12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  CouncilTaskOwnerMonthlyPietyBindings12004 bindings;
  if (!base || sha != kExecutableSha256) return bindings;
  bindings.build = reinterpret_cast<NativeCouncilTaskOwnerModifier12004>(
      base + kCouncilTaskOwnerModifierRva12004);
  bindings.value = reinterpret_cast<NativeCouncilTaskModifierValue12004>(
      base + kCouncilTaskModifierValueRva12004);
  bindings.destroy = reinterpret_cast<NativeCouncilTaskModifierDestroy12004>(
      base + kCouncilTaskModifierDestroyRva12004);
  bindings.keyword_name = reinterpret_cast<NativeCouncilTaskKeywordName12004>(
      base + kCouncilTaskKeywordNameRva12004);
  return bindings;
}

CouncilTaskOwnerMonthlyPietyObservation12004 ReadCouncilTaskOwnerMonthlyPiety12004(
    const CouncilTaskOwnerMonthlyPietyBindings12004 &bindings,
    const void *type, const void *scopes,
    CouncilTaskMonthlyPietyReadMemory12004 read_memory, void *read_context) noexcept {
  CouncilTaskOwnerMonthlyPietyObservation12004 out;
  alignas(8) std::array<std::byte, 32> original_scopes{};
  if (!type || !Read(read_memory, read_context, scopes, original_scopes.data(),
                     original_scopes.size())) {
    out.unavailable_reason = Failure::context_unavailable;
    return out;
  }
  std::memcpy(&out.incumbent_character_id, original_scopes.data(), sizeof(std::int32_t));
  std::memcpy(&out.owner_character_id, original_scopes.data() + 4, sizeof(std::int32_t));
  if (out.incumbent_character_id <= 0 || out.owner_character_id <= 0) {
    out.unavailable_reason = Failure::context_unavailable;
    return out;
  }
  if (!bindings.build || !bindings.value || !bindings.destroy || !bindings.keyword_name) {
    out.unavailable_reason = Failure::native_bindings_unavailable;
    return out;
  }
  const std::string *keyword = nullptr;
  std::size_t keyword_size = 0;
  if (!Invoke(bindings.keyword_name, keyword,
              static_cast<std::int32_t>(kCouncilMonthlyPietyDescriptor12004.keyword_id)) ||
      !CopyKeyword(read_memory, read_context, keyword, out.observed_keyword_key,
                   keyword_size)) {
    out.unavailable_reason = Failure::keyword_unavailable;
    return out;
  }
  if (std::string_view(out.observed_keyword_key.data(), keyword_size) != "monthly_piety") {
    out.unavailable_reason = Failure::keyword_mismatch;
    return out;
  }
  alignas(8) std::array<std::byte, kCouncilTaskModifierSize12004> storage{};
  void *returned = nullptr;
  if (!Invoke(bindings.build, returned, type, storage.data(), original_scopes.data())) {
    out.unavailable_reason = Failure::builder_unavailable;
    return out;
  }
  std::int64_t raw = 0;
  std::int64_t *value_result = nullptr;
  // Pass the whole standalone modifier: +68 is its internal value buffer.
  const bool available = returned == storage.data() &&
      Invoke(bindings.value, value_result, storage.data(), &raw,
             kCouncilMonthlyPietyDescriptor12004.modifier_id) && value_result == &raw;
  if (!Destroy(bindings.destroy, storage.data())) {
    out.unavailable_reason = Failure::cleanup_unavailable;
  } else if (!available) {
    out.unavailable_reason = Failure::numeric_unavailable;
  } else {
    out.raw = raw; // Native absent-ID zero is an available signed value.
  }
  return out;
}

bool ReadCampaignRootTaskOwnerMonthlyPiety12004(
    std::uintptr_t base, void *type, const void *scopes, std::int64_t &raw) noexcept {
  const auto observation = ReadCouncilTaskOwnerMonthlyPiety12004(
      BindCouncilTaskOwnerMonthlyPiety12004(base, kExecutableSha256), type, scopes);
  if (!observation.raw) return false;
  raw = *observation.raw;
  return true;
}
} // namespace xar::ck3_12004
