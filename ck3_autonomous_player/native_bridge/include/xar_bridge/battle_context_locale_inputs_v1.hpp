#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

// Exact current alternate-locale prefix operands/result; no locale update.
struct ContextSourceLocaleClassificationV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> first_signed_byte;
  std::optional<std::uint32_t> crt_index;
  std::string cached_value_api_status;
  std::string thread_state_source;
  std::string locale_source;
  std::optional<bool> thread_state_present;
  std::optional<bool> current_locale_present;
  std::optional<bool> global_locale_present;
  std::optional<bool> selected_locale_present;
  std::optional<std::uint32_t> thread_locale_flags;
  std::optional<std::uint32_t> flags_mask;
  std::optional<std::int32_t> locale_max_multibyte;
  std::optional<std::uint16_t> table_element_u16;
  std::optional<std::int32_t> result_i32;
  std::string reason;
  friend bool operator==(const ContextSourceLocaleClassificationV1 &,
                         const ContextSourceLocaleClassificationV1 &) = default;
};

} // namespace xar::game
