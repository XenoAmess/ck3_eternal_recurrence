#pragma once

#include "xar_bridge/battle_context_locale_inputs_v1.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <string_view>

namespace xar::ck3_12002 {

using ContextLocaleReadMemoryV1 = bool (*)(void *context, const void *address,
                                         void *output, std::size_t bytes) noexcept;
struct ContextSourceLocaleBindingsV1 {
  bool enabled = false;
  const void *crt_index_slot = nullptr;
  const void *value_api_cache_slot = nullptr;
  const void *decode_cookie_slot = nullptr;
  const void *tls_get_value_iat = nullptr;
  const void *get_last_error_iat = nullptr;
  const void *set_last_error_iat = nullptr;
  const void *global_locale_slot = nullptr;
  const void *locale_flags_mask_slot = nullptr;
  ContextLocaleReadMemoryV1 read_memory = nullptr;
  void *read_context = nullptr;
};

inline ContextSourceLocaleBindingsV1 BindContextSourceLocale12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  ContextSourceLocaleBindingsV1 b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.crt_index_slot = reinterpret_cast<const void *>(base + 0x542F328);
  b.value_api_cache_slot = reinterpret_cast<const void *>(base + 0x5C5D7B8);
  b.decode_cookie_slot = reinterpret_cast<const void *>(base + 0x542F0B8);
  b.tls_get_value_iat = reinterpret_cast<const void *>(base + 0x43DA460);
  b.get_last_error_iat = reinterpret_cast<const void *>(base + 0x43DA738);
  b.set_last_error_iat = reinterpret_cast<const void *>(base + 0x43DA420);
  b.global_locale_slot = reinterpret_cast<const void *>(base + 0x5C5DCD8);
  b.locale_flags_mask_slot = reinterpret_cast<const void *>(base + 0x542FCB0);
  return b;
}

namespace context_locale_detail {
template <typename T>
std::optional<T> Read(const ContextSourceLocaleBindingsV1 &b, const void *p,
                      std::size_t offset = 0) noexcept {
  if (!p) return std::nullopt;
  const auto *address = static_cast<const std::byte *>(p) + offset;
  T result{};
  if (b.read_memory) {
    if (!b.read_memory(b.read_context, address, &result, sizeof(result)))
      return std::nullopt;
  } else std::memcpy(&result, address, sizeof(result));
  return result;
}
} // namespace context_locale_detail

// Called only for a needed nondefault-locale classifier row on the current
// query owning thread. Existing OS value getter only; preserve LastError.
// No CRT thread allocation, import resolution, locale sync or refcount calls.
inline game::ContextSourceLocaleClassificationV1
ReadContextSourceLocaleClassification12003(const ContextSourceLocaleBindingsV1 &b,
                                          std::int32_t first_signed_byte) noexcept {
  using context_locale_detail::Read;
  game::ContextSourceLocaleClassificationV1 out{};
  out.first_signed_byte = first_signed_byte;
  if (!b.enabled) {
    out.reason = "alternate_locale_reader_unbound";
    return out;
  }
  out.status = "partial";
  out.crt_index = Read<std::uint32_t>(b, b.crt_index_slot);
  const auto encoded = Read<std::uint64_t>(b, b.value_api_cache_slot);
  const auto cookie = Read<std::uint64_t>(b, b.decode_cookie_slot);
  if (!out.crt_index || !encoded || !cookie) {
    out.reason = "crt_existing_value_inputs_unavailable";
    return out;
  }
  if (*out.crt_index == 0xFFFFFFFFU) {
    out.reason = "crt_value_index_uninitialized";
    return out;
  }
  const auto decoded = std::rotr(*encoded ^ *cookie,
      static_cast<int>(*cookie & 63U));
  std::uintptr_t value_getter = static_cast<std::uintptr_t>(decoded);
  if (decoded == 0) {
    out.cached_value_api_status = "would_resolve";
    out.reason = "crt_value_api_would_resolve";
    return out;
  }
  if (decoded == (std::numeric_limits<std::uint64_t>::max)()) {
    out.cached_value_api_status = "tls_fallback";
    const auto getter = Read<std::uintptr_t>(b, b.tls_get_value_iat);
    if (!getter || !*getter) {
      out.reason = "crt_tls_value_import_unavailable";
      return out;
    }
    value_getter = *getter;
    out.thread_state_source = "existing_tls_value";
  } else {
    out.cached_value_api_status = "existing_fls";
    out.thread_state_source = "existing_fls_value";
  }
  const auto get_error = Read<std::uintptr_t>(b, b.get_last_error_iat);
  const auto set_error = Read<std::uintptr_t>(b, b.set_last_error_iat);
  if (!get_error || !*get_error || !set_error || !*set_error) {
    out.reason = "crt_last_error_imports_unavailable";
    return out;
  }
  using GetValue = void *(*)(std::uint32_t);
  using GetError = std::uint32_t (*)();
  using SetError = void (*)(std::uint32_t);
  const auto saved_error = reinterpret_cast<GetError>(*get_error)();
  const void *state = reinterpret_cast<GetValue>(value_getter)(*out.crt_index);
  reinterpret_cast<SetError>(*set_error)(saved_error);
  out.thread_state_present = state != nullptr &&
      reinterpret_cast<std::uintptr_t>(state) !=
      (std::numeric_limits<std::uintptr_t>::max)();
  if (!*out.thread_state_present) {
    out.reason = state ? "crt_thread_state_reserved" : "crt_thread_state_would_allocate";
    return out;
  }
  const auto current = Read<const void *>(b, state, 0x90);
  const auto global = Read<const void *>(b, b.global_locale_slot);
  if (current) out.current_locale_present = *current != nullptr;
  if (global) out.global_locale_present = *global != nullptr;
  if (!current || !global) {
    out.reason = "locale_pointer_reads_unavailable";
    return out;
  }
  const void *selected = nullptr;
  if (*current == *global) {
    selected = *current;
    out.locale_source = "thread_locale_equal_global";
  } else {
    out.thread_locale_flags = Read<std::uint32_t>(b, state, 0x3A8);
    out.flags_mask = Read<std::uint32_t>(b, b.locale_flags_mask_slot);
    if (!out.thread_locale_flags || !out.flags_mask) {
      out.reason = "locale_selection_flags_unavailable";
      return out;
    }
    if ((*out.thread_locale_flags & *out.flags_mask) != 0) {
      selected = *current;
      out.locale_source = "thread_locale_retained_by_flags";
    } else {
      selected = *global;
      out.locale_source = "global_locale_selected_without_sync";
    }
  }
  out.selected_locale_present = selected != nullptr;
  if (!selected) {
    out.reason = "locale_selected_pointer_null";
    return out;
  }
  if (static_cast<std::uint32_t>(first_signed_byte + 1) > 0x100U) {
    out.locale_max_multibyte = Read<std::int32_t>(b, selected, 8);
    if (!out.locale_max_multibyte) {
      out.reason = "locale_multibyte_count_unavailable";
      return out;
    }
    if (*out.locale_max_multibyte > 1) {
      out.reason = "classifier_unavailable_locale_multibyte_path";
      return out;
    }
    out.result_i32 = 0;
  } else {
    const auto table = Read<const void *>(b, selected);
    const void *element = table && *table
        ? static_cast<const std::byte *>(*table) + first_signed_byte * 2 : nullptr;
    out.table_element_u16 = Read<std::uint16_t>(b, element);
    if (!out.table_element_u16) {
      out.reason = "alternate_locale_table_element_unavailable";
      return out;
    }
    out.result_i32 = static_cast<std::int32_t>(*out.table_element_u16 & 4U);
  }
  out.ready = true;
  out.status = "available";
  return out;
}

} // namespace xar::ck3_12002
