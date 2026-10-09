#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {
struct EventWindowBindings;
}

namespace xar::ck3_11906 {

struct ZhongguoScoreboardNativeEnvironmentV1;

struct CurrentFirstHeirTypedWindowSpecV1 {
  std::int32_t slot_index;
  std::int32_t handler_member_offset;
  std::int32_t type_identifier;
};

inline constexpr std::array<CurrentFirstHeirTypedWindowSpecV1, 7>
    kCurrentFirstHeirTypedWindowSpecsV1{{
        {0, 0x98, 13092},
        {1, 0xA0, 11010},
        {2, 0xA8, 11399},
        {3, 0xB0, 14350},
        {4, 0xB8, 14351},
        {5, 0xC0, 15450},
        {6, 0xC8, 10602},
    }};

struct CurrentFirstHeirTypedWindowRowV1 {
  std::int32_t slot_index = 0;
  std::int32_t handler_member_offset = 0;
  std::int32_t type_identifier = 0;
  bool registered_name_available = false;
  std::optional<std::string> registered_name;
  std::string_view registered_name_unavailable_reason;
  std::string_view window_presence = "unavailable";
  std::string_view object_type_status = "unavailable";
  std::optional<std::uint64_t> object_vtable_rva;
  std::optional<std::uint64_t> object_col_rva;
  std::optional<std::uint64_t> object_type_descriptor_rva;
  std::optional<std::string> object_type_decorated_name;
  std::string_view object_type_unavailable_reason;
};

struct CurrentFirstHeirTypedWindowsReadV1 {
  bool window_handler_available = false;
  std::string_view window_handler_unavailable_reason;
  std::vector<CurrentFirstHeirTypedWindowRowV1> rows;
};

// Shared rows reader: borrowed registry strings are copied in the same call;
// null handler/slots retain independent registry-name observations.
CurrentFirstHeirTypedWindowsReadV1 ReadCurrentFirstHeirTypedWindowRows12004V1(
    std::uintptr_t base, std::uintptr_t image_size,
    const ck3_12002::EventWindowBindings &bindings,
    const void *handler) noexcept;

// Production admission and handler resolution use the existing actual4 UI
// environment. This observes window types only; it never navigates or clicks.
CurrentFirstHeirTypedWindowsReadV1 ReadCurrentFirstHeirTypedWindows12004V1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ck3_12002::EventWindowBindings &bindings) noexcept;

} // namespace xar::ck3_11906
