#pragma once
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 { struct AppointmentWindowAccessV1; }

namespace xar::ck3_12004 {
// Source-only primitive. Call only inside the existing exact4 paused owner
// mailbox after validating the current appointment window/rule/title lease.
// Type0 has an actual getter/floor chain; its string name is not yet proved.
struct AppointmentCharacterLevel12004 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::uint32_t character_id = 0, title_id = 0;
  std::uint8_t native_level_source_ordinal = 0;
  bool native_level_source_ordinal_available = false;
  bool resource_extension_present = false;
  std::int64_t accumulated_raw = 0;
  std::int32_t level_cap_raw = -1, native_level = 0;
  std::int32_t title_tier = 0, required_native_level = 0;
  bool meets_native_level_floor = false;
};

bool ReadAppointmentCharacterLevel12004(
    const ck3_11906::AppointmentWindowAccessV1 &access,
    std::string_view admitted_exe_sha256,
    std::uintptr_t admitted_rule, std::uintptr_t admitted_title,
    std::uint32_t title_id, std::uint32_t character_id,
    AppointmentCharacterLevel12004 &out) noexcept;
}
