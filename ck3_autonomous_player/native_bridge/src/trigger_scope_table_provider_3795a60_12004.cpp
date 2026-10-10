#include "xar_bridge/trigger_scope_table_provider_3795a60_12004.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
std::optional<std::uintptr_t> Address(std::uintptr_t base, std::size_t offset,
                                    std::size_t bytes = 1) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base ||
      bytes > (std::numeric_limits<std::uintptr_t>::max)() - (base + offset)) return {};
  return base + offset;
}
struct ScalarCopy {
  std::uintptr_t address = 0;
  std::size_t bytes = 0;
  std::array<std::byte, 8> value{};
};
struct Copier {
  const SourceLeafReadOnlyAccess12004 &access;
  TriggerScopeTableProviderRaw3795A6012004 &out;
  std::array<ScalarCopy, 5> copies{};
  std::size_t copied = 0;

  template <typename T>
  std::optional<T> Read(std::uintptr_t receiver, std::size_t offset, const char *field) {
    static_assert(sizeof(T) <= 8);
    out.any_native_field_read_attempted = true;
    const auto address = Address(receiver, offset, sizeof(T));
    T value{};
    if (!address || copied == copies.size() ||
        !access.read_memory(access.context, reinterpret_cast<const void *>(*address),
                            &value, sizeof(T))) {
      out.missing_fields.emplace_back(field);
      return {};
    }
    auto &copy = copies[copied++];
    copy.address = *address;
    copy.bytes = sizeof(T);
    std::memcpy(copy.value.data(), &value, sizeof(T));
    out.source_scalar_reads = copied;
    return value;
  }
  bool Unchanged() const noexcept {
    for (std::size_t index = 0; index < copied; ++index) {
      const auto &copy = copies[index];
      std::array<std::byte, 8> current{};
      if (!access.read_memory(access.context, reinterpret_cast<const void *>(copy.address),
                              current.data(), copy.bytes) ||
          std::memcmp(current.data(), copy.value.data(), copy.bytes) != 0) return false;
    }
    return true;
  }
};
} // namespace

TriggerScopeTableProviderRaw3795A6012004 ReadTriggerScopeTableProvider3795A6012004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceReadFrame12004 &frame,
    std::optional<std::uint16_t> kind) {
  TriggerScopeTableProviderRaw3795A6012004 out{};
  out.frame = frame;
  out.caller_copied_root_kind_raw_u16 = kind;
  out.query_frame_ready = SourceReadFrameReady12004(frame);
  if (!out.query_frame_ready) {
    out.unavailable_reason = "original_source_read_frame_unavailable";
    return out;
  }
  out.source_provider_entry_identity = Address(frame.module_base,
                                               kTriggerScopeTableProviderRva3795A6012004);
  out.source_return_table_identity = Address(frame.module_base,
                                             kTriggerScopeTableInlineRva3795A6012004, 0x10);
  out.return_pointer_on_returning_native_paths_source_closed =
      out.source_provider_entry_identity.has_value() && out.source_return_table_identity.has_value();
  if (!out.return_pointer_on_returning_native_paths_source_closed) {
    out.unavailable_reason = "source_static_table_address_unavailable";
    return out;
  }
  if (kind) out.caller_root_zero_bypasses_descriptor = *kind == 0;
  if (kind && *kind == 0) {
    out.unavailable_reason = "caller_root_kind_zero_bypasses_provider_and_descriptor";
    return out;
  }
  if (!access.read_memory) {
    out.unavailable_reason = "guarded_source_read_callback_unavailable";
    return out;
  }
  Copier copier{access, out};
  out.initialization_guard_raw_i32 = copier.Read<std::int32_t>(frame.module_base,
      kTriggerScopeTableGuardRva3795A6012004, "table.initialization_guard");
  const auto table = *out.source_return_table_identity;
  out.table_data_identity = copier.Read<std::uintptr_t>(table, 0, "table.data0");
  out.capacity_raw_i32 = copier.Read<std::int32_t>(table, 8, "table.capacity8");
  out.count_raw_i32 = copier.Read<std::int32_t>(table, 0xC, "table.countC");
  out.table_header_copy_complete = out.table_data_identity.has_value() &&
      out.capacity_raw_i32.has_value() && out.count_raw_i32.has_value();
  if (kind && out.count_raw_i32) {
    const bool use_table = *out.count_raw_i32 > static_cast<std::int32_t>(*kind);
    out.selected_source_fallback = !use_table;
    if (use_table) {
      if (out.table_data_identity && *out.table_data_identity != 0) {
        out.selected_descriptor_identity = Address(*out.table_data_identity,
            static_cast<std::size_t>(*kind) * kTriggerScopeDescriptorStride3795A6012004, 0x18);
      }
      if (!out.selected_descriptor_identity)
        out.missing_fields.emplace_back("descriptor.selected_table_pointer");
    } else {
      out.selected_descriptor_identity = Address(frame.module_base,
          kTriggerScopeFallbackRva3795A6012004, 0x18);
      if (!out.selected_descriptor_identity)
        out.missing_fields.emplace_back("descriptor.source_fallback_pointer");
    }
    out.descriptor_selection_inputs_copied = out.selected_descriptor_identity.has_value();
    if (out.selected_descriptor_identity) {
      out.descriptor_validator_pointer10 = copier.Read<std::uintptr_t>(
          *out.selected_descriptor_identity, 0x10, "descriptor.validator10");
      out.descriptor_validator_pointer_copied = out.descriptor_validator_pointer10.has_value();
    }
  }
  out.all_attempted_native_reads_complete = out.any_native_field_read_attempted && out.missing_fields.empty();
  if (copier.copied != 0) out.copied_fields_unchanged = copier.Unchanged();
  if (out.copied_fields_unchanged && !*out.copied_fields_unchanged)
    out.unavailable_reason = "copied_source_fields_changed";
  else if (!out.missing_fields.empty()) out.unavailable_reason = "scope_table_raw_copy_partial";
  else if (!kind) out.unavailable_reason = "caller_copied_root_kind_unavailable";
  else out.unavailable_reason = "raw_descriptor_pointer_only_validator_result_unavailable";
  // Do not manufacture a calling-thread TLS epoch, initializer completion,
  // native RAX observation or a validator result from these copied fields.
  return out;
}
} // namespace xar::ck3_12004
