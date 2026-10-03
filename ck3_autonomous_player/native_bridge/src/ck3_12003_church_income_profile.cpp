#include "xar_bridge/ck3_12003_church_income_profile.hpp"

#include <cstring>
#include <sstream>

namespace xar::ck3_12003::religion::church_income {
namespace {
std::int32_t CharacterId(const void *character) noexcept {
  std::int32_t id{};
  std::memcpy(&id, static_cast<const std::byte *>(character) + 0x18, sizeof(id));
  return id;
}
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
} // namespace

Bindings BindPlayerChurchIncomeProfileImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  if (base == 0 || sha != kExecutableSha256) return {};
  return {true, reinterpret_cast<MonthlyIncome>(base + kMonthlyIncomeRva)};
}

bool ReadPlayerChurchIncomeProfile12003(const Bindings &b, void *character,
    std::int32_t id, std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = id;
  if (!b.enabled || !b.monthly_income) return false;
  if (!character || id <= 0 || CharacterId(character) != id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  try {
    std::int64_t current = 0, maximum = 0;
    if (b.monthly_income(&current, character, false, false, nullptr) != &current) {
      out.unavailable_reason = "current_monthly_income_unavailable"; return false;
    }
    if (b.monthly_income(&maximum, character, false, true, nullptr) != &maximum) {
      out.unavailable_reason = "maximum_monthly_income_unavailable"; return false;
    }
    out.current_monthly_income_raw = current;
    out.maximum_monthly_income_raw = maximum;
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) {
    out.unavailable_reason = "church_income_native_copy_exception"; return false;
  }
}

std::string SerializePlayerChurchIncomeProfile12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema) << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id << ",\"current_monthly_income_raw\":";
  if (t.current_monthly_income_raw) out << *t.current_monthly_income_raw; else out << "null";
  out << ",\"maximum_monthly_income_raw\":";
  if (t.maximum_monthly_income_raw) out << *t.maximum_monthly_income_raw; else out << "null";
  out << ",\"raw_scale\":100000}";
  return out.str();
}

} // namespace xar::ck3_12003::religion::church_income
