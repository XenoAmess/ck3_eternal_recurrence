#pragma once

#include "xar_bridge/prewar_force_coalition12004.hpp"
#include <array>
#include <charconv>
#include <limits>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {
namespace prewar_request12004 {

// The typed SDK emits this closed ASCII control schema. Reject ambiguous keys,
// escaped strings, noninteger IDs and trailing data before any native query.
class Cursor {
 public:
  explicit Cursor(std::string_view input) : input_(input) {}
  bool Take(char value) {
    Space();
    if (at_ == input_.size() || input_[at_] != value) return false;
    ++at_; return true;
  }
  bool Text(std::string_view &value) {
    if (!Take('"')) return false;
    const auto start = at_;
    while (at_ < input_.size()) {
      const auto c = static_cast<unsigned char>(input_[at_++]);
      if (c == '"') {
        value = input_.substr(start, at_ - start - 1);
        return value.size() <= 128;
      }
      if (c < 0x20 || c >= 0x7f || c == '\\' || at_ - start > 128) return false;
    }
    return false;
  }
  bool Unsigned(std::uint64_t &value) {
    Space(); const auto start = at_;
    while (at_ < input_.size() && input_[at_] >= '0' && input_[at_] <= '9') ++at_;
    if (start == at_ || (at_ - start > 1 && input_[start] == '0')) return false;
    const auto parsed = std::from_chars(input_.data() + start, input_.data() + at_, value);
    return parsed.ec == std::errc{} && parsed.ptr == input_.data() + at_;
  }
  bool Id(std::int32_t &value, std::int32_t minimum) {
    Space(); const bool negative = Take('-');
    if (negative && (at_ == input_.size() || input_[at_] < '0' || input_[at_] > '9')) return false;
    std::uint64_t magnitude = 0;
    if (!Unsigned(magnitude) || magnitude > static_cast<std::uint64_t>(INT32_MAX)) return false;
    const auto number = negative ? -static_cast<std::int64_t>(magnitude) : static_cast<std::int64_t>(magnitude);
    if (number < minimum) return false;
    value = static_cast<std::int32_t>(number); return true;
  }
  bool Titles(std::vector<std::int32_t> &values) {
    if (!Take('[')) return false;
    if (Take(']')) return true;
    for (;;) {
      std::int32_t id = -1;
      if (values.size() >= 4096 || !Id(id, 0)) return false;
      values.push_back(id); // Native title ordering, repeats and TitleID zero matter.
      if (Take(']')) return true;
      if (!Take(',')) return false;
    }
  }
  bool End() { Space(); return at_ == input_.size(); }
 private:
  void Space() {
    while (at_ < input_.size() && (input_[at_] == ' ' || input_[at_] == '\t' ||
           input_[at_] == '\r' || input_[at_] == '\n')) ++at_;
  }
  std::string_view input_;
  std::size_t at_ = 0;
};

template<std::size_t N>
std::size_t Index(std::string_view key, const std::array<std::string_view, N> &keys) {
  for (std::size_t i = 0; i < N; ++i) if (key == keys[i]) return i;
  return N;
}

inline bool Selected(Cursor &cursor, game::DeclarableWarSnapshot &out) {
  constexpr std::array<std::string_view, 6> keys{
      "target_character_id", "casus_belli_index", "casus_belli_key",
      "configuration_index", "claimant_character_id", "target_title_ids"};
  if (!cursor.Take('{')) return false;
  unsigned seen = 0;
  for (unsigned ordinal = 0; !cursor.Take('}'); ++ordinal) {
    if (ordinal && !cursor.Take(',')) return false;
    std::string_view key;
    if (!cursor.Text(key) || !cursor.Take(':')) return false;
    const auto i = Index(key, keys);
    if (i == keys.size() || (seen & (1U << i))) return false;
    seen |= 1U << i;
    if (i == 0 && !cursor.Id(out.target_character_id, 1)) return false;
    if (i == 1 && !cursor.Id(out.casus_belli_index, 0)) return false;
    if (i == 2) {
      std::string_view text;
      if (!cursor.Text(text) || text.empty()) return false;
      for (char c : text)
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_')) return false;
      out.casus_belli_key.assign(text);
    }
    if (i == 3 && !cursor.Id(out.configuration_index, -1)) return false;
    if (i == 4 && !cursor.Id(out.claimant_character_id, -1)) return false;
    if (i == 5 && !cursor.Titles(out.target_title_ids)) return false;
  }
  return seen == 63;
}
} // namespace prewar_request12004

inline bool ParsePrewarForceCoalitionRequest12004(
    std::string_view payload, std::string_view expected_step,
    std::string_view expected_request_id, PrewarForceCoalitionRequest12004 &output) noexcept {
  try {
    if (payload.size() > 1024 * 1024 || expected_request_id.empty()) return false;
    prewar_request12004::Cursor cursor(payload);
    constexpr std::array<std::string_view, 8> keys{
        "type", "protocol_version", "request_id", "step", "expected_revision",
        "expected_public_revision", "declaration_id", "selected_declaration"};
    PrewarForceCoalitionRequest12004 parsed;
    if (!cursor.Take('{')) return false;
    unsigned seen = 0;
    for (unsigned ordinal = 0; !cursor.Take('}'); ++ordinal) {
      if (ordinal && !cursor.Take(',')) return false;
      std::string_view key;
      if (!cursor.Text(key) || !cursor.Take(':')) return false;
      const auto i = prewar_request12004::Index(key, keys);
      if (i == keys.size() || (seen & (1U << i))) return false;
      seen |= 1U << i;
      if (i == 0 || i == 2 || i == 3 || i == 6) {
        std::string_view value;
        if (!cursor.Text(value) || value.empty()) return false;
        if (i == 0 && value != "execute_step") return false;
        if (i == 2 && value != expected_request_id) return false;
        if (i == 3 && value != expected_step) return false;
        if (i == 6) parsed.declaration_id.assign(value);
      } else if (i == 1) {
        std::uint64_t version = 0;
        if (!cursor.Unsigned(version) || version != 1) return false;
      } else if (i == 4) {
        if (!cursor.Unsigned(parsed.expected_native_revision) || !parsed.expected_native_revision) return false;
      } else if (i == 5) {
        if (!cursor.Unsigned(parsed.expected_public_revision) || !parsed.expected_public_revision) return false;
      } else if (!prewar_request12004::Selected(cursor, parsed.selected)) return false;
    }
    if (seen != 255 || !cursor.End()) return false;
    const auto canonical = std::to_string(parsed.selected.target_character_id) + '-' +
        std::to_string(parsed.selected.casus_belli_index) + '-' +
        std::to_string(parsed.selected.configuration_index);
    if (parsed.declaration_id != canonical) return false;
    output = std::move(parsed); return true;
  } catch (...) { return false; }
}
} // namespace xar::ck3_12004
