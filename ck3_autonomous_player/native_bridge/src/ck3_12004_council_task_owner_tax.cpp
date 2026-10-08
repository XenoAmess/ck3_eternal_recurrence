#include "xar_bridge/ck3_12004_council_task_owner_tax.hpp"
#include "xar_bridge/ck3_12004_council_candidates.hpp"
#include "xar_bridge/ck3_12004_county_conversion_abi.hpp"

#include <array>
#include <cstring>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
namespace task_abi = religion::county_conversion::abi;
using Failure = game::CouncilCurrentTaskDomainTaxFailureV1;

template <typename T>
bool Read(const CouncilCandidatesAccessV1 &access, const void *base,
          std::size_t offset, T &value) noexcept {
  return base && ReadCouncilMemory12004(access,
      static_cast<const std::byte *>(base) + offset, &value, sizeof(value));
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

// Same native CString layout used by actual4 campaign/county conversion.
// The returned keyword object is borrowed; this copies and never destroys it.
template <std::size_t Size>
bool CopyString(const CouncilCandidatesAccessV1 &access, const void *object,
                std::array<char, Size> &out) noexcept {
  std::uint64_t size = 0, capacity = 0;
  if (!Read(access, object, 0x10, size) || !Read(access, object, 0x18, capacity) ||
      size == 0 || size >= Size || size > capacity) return false;
  const void *text = object;
  if (capacity > 15 && (!Read(access, object, 0, text) || !text)) return false;
  return ReadCouncilMemory12004(access, text, out.data(), static_cast<std::size_t>(size));
}
} // namespace

CouncilTaskOwnerTaxBindings12004 BindCouncilTaskOwnerTax12004(
    std::uintptr_t base, std::string_view sha,
    CouncilTaskTaxDescriptor12004 descriptor) noexcept {
  CouncilTaskOwnerTaxBindings12004 bindings;
  if (!base || sha != kExecutableSha256) return bindings;
  bindings.descriptor = descriptor;
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

game::CouncilCurrentTaskDomainTaxV1 ReadCouncilTaskOwnerTax12004(
    const CouncilTaskOwnerTaxBindings12004 &bindings,
    const CouncilCandidatesAccessV1 &access, const void *task,
    std::int32_t active_task_id, std::int32_t owner_id, std::int32_t incumbent_id) {
  game::CouncilCurrentTaskDomainTaxV1 out;
  out.active_task_id = active_task_id;
  out.owner_character_id = owner_id;
  out.incumbent_character_id = incumbent_id;
  out.modifier_id = bindings.descriptor.modifier_id;
  out.keyword_id = bindings.descriptor.keyword_id;
  const void *type = nullptr;
  std::uint8_t frozen = 0;
  alignas(8) std::array<std::byte, 32> original_scopes{};
  if (!task || incumbent_id <= 0 ||
      !Read(access, task, task_abi::kTaskTypeOffset, type) || !type ||
      !Read(access, task, task_abi::kTaskFrozenOffset, frozen) ||
      !ReadCouncilMemory12004(access,
          static_cast<const std::byte *>(task) + task_abi::kTaskScopesOffset,
          original_scopes.data(), original_scopes.size()) ||
      !CopyString(access, static_cast<const std::byte *>(type) +
          task_abi::kDefinitionKeyOffset, out.task_key)) {
    out.unavailable_reason = Failure::context_unavailable;
    return out;
  }
  out.frozen = frozen != 0;
  if (!bindings.build || !bindings.value || !bindings.destroy || !bindings.keyword_name) {
    out.unavailable_reason = Failure::native_bindings_unavailable;
    return out;
  }
  const std::string *keyword = nullptr;
  if (!Invoke(bindings.keyword_name, keyword,
      static_cast<std::int32_t>(bindings.descriptor.keyword_id)) ||
      !CopyString(access, keyword, out.observed_keyword_key)) {
    out.unavailable_reason = Failure::keyword_unavailable;
    return out;
  }
  if (std::string_view(out.observed_keyword_key.data()) != "domain_tax_mult") {
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
  // Standalone evaluated output is the receiver; values are internal at+68.
  const bool read = returned == storage.data() &&
      Invoke(bindings.value, value_result, storage.data(), &raw,
          bindings.descriptor.modifier_id) && value_result == &raw;
  if (!Destroy(bindings.destroy, storage.data())) {
    out.unavailable_reason = Failure::cleanup_unavailable;
  } else if (!read) {
    out.unavailable_reason = Failure::numeric_unavailable;
  } else {
    out.raw = raw; // A native absent-ID zero remains an available value.
  }
  return out;
}

} // namespace xar::ck3_12004
