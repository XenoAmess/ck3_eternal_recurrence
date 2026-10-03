#include "xar_bridge/ck3_12003_activity_phase_dates.hpp"

#include <cstring>
#include <sstream>

namespace xar::ck3_12003::religion::activity_phase_dates {
namespace {
std::int32_t LoadDateRaw(const void *native_date) noexcept {
  std::int32_t raw{};
  std::memcpy(&raw, native_date, sizeof(raw));
  return raw;
}
std::string Quote(std::string_view value) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
} // namespace

Bindings BindActivityPhaseDatesImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  // Reflection registrar4CBF10: GetActiveStartDate ->24007A0.
  // Reflection registrar4CC010: GetProgressPhaseDate ->24007F0.
  b.active_start_date = reinterpret_cast<NativeDateGetter>(base + 0x24007A0);
  b.progress_phase_date = reinterpret_cast<NativeDateGetter>(base + 0x24007F0);
  return b;
}

bool ReadActivityPhaseDates12003(const Bindings &b, const void *activity,
    std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.date_raw = date; out.capture_epoch = epoch;
  if (!b.enabled || !b.active_start_date || !b.progress_phase_date) return false;
  if (!activity) { out.unavailable_reason = "resolved_activity_absent"; return false; }
  const auto *active = b.active_start_date(activity);
  const auto *progress = b.progress_phase_date(activity);
  if (!active || !progress) { out.unavailable_reason = "native_date_getter_unavailable"; return false; }
  out.active_start_date_raw = LoadDateRaw(active);
  out.progress_phase_date_raw = LoadDateRaw(progress);
  out.available = true; out.unavailable_reason.clear();
  return true;
}

std::string SerializeActivityPhaseDates12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema)
      << ",\"read_only\":true,\"schedule_source\":\"existing_native_activity\""
      << ",\"available\":" << t.available << ",\"unavailable_reason\":"
      << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"date_raw\":" << t.date_raw << ",\"capture_epoch\":" << t.capture_epoch
      << ",\"active_start_date_raw\":";
  if (t.active_start_date_raw) out << *t.active_start_date_raw; else out << "null";
  out << ",\"progress_phase_date_raw\":";
  if (t.progress_phase_date_raw) out << *t.progress_phase_date_raw; else out << "null";
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::activity_phase_dates
