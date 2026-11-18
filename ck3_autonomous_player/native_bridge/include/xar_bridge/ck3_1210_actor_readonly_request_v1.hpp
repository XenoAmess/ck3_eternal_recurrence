#pragma once
#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
namespace xar::ck3_1210 {
struct ActorReadonlyRequestV1 { std::string request_id; std::uint64_t expected_revision = 0; };
enum class ActorReadonlyRevisionV1 { zero, positive };
// Closed standard NativeWire.execute envelope only. Callers pass a compiled
// readonly step and exact revision policy, then compare request_id to their
// outer correlation id. This parser grants no owner/capability/selector role.
// All five fields required once; no escapes/extra fields/coercions/trailing
// data. UTF-8 request ids retain NativeWire.control's original <=128-byte domain.
namespace actor_readonly_request_detail {
inline bool ValidUtf8(std::string_view text) noexcept {
  std::size_t i = 0;
  while (i < text.size()) {
    const auto first = static_cast<unsigned char>(text[i++]);
    if (first < 0x80) continue;
    unsigned remaining = 0; std::uint32_t code = 0, minimum = 0;
    if (first >= 0xC2 && first <= 0xDF) { remaining = 1; code = first & 31; minimum = 0x80; }
    else if (first >= 0xE0 && first <= 0xEF) { remaining = 2; code = first & 15; minimum = 0x800; }
    else if (first >= 0xF0 && first <= 0xF4) { remaining = 3; code = first & 7; minimum = 0x10000; }
    else return false;
    if (remaining > text.size() - i) return false;
    while (remaining-- != 0) {
      const auto next = static_cast<unsigned char>(text[i++]);
      if (next < 0x80 || next > 0xBF) return false;
      code = (code << 6) | (next & 63);
    }
    if (code < minimum || code > 0x10FFFF || (code >= 0xD800 && code <= 0xDFFF)) return false;
  }
  return true;
}
class Cursor {
  std::string_view text_; std::size_t at_ = 0;
public:
  explicit Cursor(std::string_view text) noexcept : text_(text) {}
  void White() noexcept {
    while (at_ < text_.size() && (text_[at_] == char(32) || text_[at_] == char(9) ||
      text_[at_] == char(10) || text_[at_] == char(13))) ++at_;
  }
  bool Take(char c) noexcept { White(); if (at_ == text_.size() || text_[at_] != c) return false; ++at_; return true; }
  bool Text(std::string_view &out) noexcept {
    if (!Take(char(34))) return false;
    const auto begin = at_;
    while (at_ < text_.size()) {
      const auto c = static_cast<unsigned char>(text_[at_++]);
      if (c == 34) { out = text_.substr(begin, at_ - begin - 1); return out.size() <= 128 && ValidUtf8(out); }
      if (c < 0x20 || c == 92 || at_ - begin > 128) return false;
    }
    return false;
  }
  bool Unsigned(std::uint64_t &out) noexcept {
    White(); const auto begin = at_;
    while (at_ < text_.size() && text_[at_] >= '0' && text_[at_] <= '9') ++at_;
    if (at_ == begin || at_ - begin > 20 || (text_[begin] == '0' && at_ - begin > 1)) return false;
    const auto r = std::from_chars(text_.data() + begin, text_.data() + at_, out);
    return r.ec == std::errc{} && r.ptr == text_.data() + at_;
  }
  bool Done() noexcept { White(); return at_ == text_.size(); }
};
} // namespace actor_readonly_request_detail
inline bool ParseActorReadonlyRequestV1(std::string_view json, std::string_view expected_step,
    ActorReadonlyRevisionV1 policy, ActorReadonlyRequestV1 &output) noexcept {
  using namespace actor_readonly_request_detail;
  if (json.empty() || json.size() > 1024 || expected_step.empty() || expected_step.size() > 128 ||
      (policy != ActorReadonlyRevisionV1::zero && policy != ActorReadonlyRevisionV1::positive)) return false;
  try {
    constexpr std::array<std::string_view, 5> keys{"type", "protocol_version", "request_id", "step", "expected_revision"};
    Cursor cursor(json); ActorReadonlyRequestV1 parsed{}; unsigned seen = 0;
    if (!cursor.Take('{')) return false;
    for (unsigned ordinal = 0; !cursor.Take('}'); ++ordinal) {
      if (ordinal && !cursor.Take(',')) return false;
      std::string_view key; if (!cursor.Text(key) || !cursor.Take(':')) return false;
      std::size_t index = 0; while (index < keys.size() && keys[index] != key) ++index;
      if (index == keys.size() || (seen & (1U << index))) return false;
      seen |= 1U << index;
      if (index == 1 || index == 4) {
        std::uint64_t value = 0; if (!cursor.Unsigned(value)) return false;
        if (index == 1 && value != 1) return false;
        if (index == 4) { if ((policy == ActorReadonlyRevisionV1::zero && value != 0) ||
            (policy == ActorReadonlyRevisionV1::positive && value == 0)) return false; parsed.expected_revision = value; }
      } else {
        std::string_view value; if (!cursor.Text(value)) return false;
        if (index == 0 && value != "execute_step") return false;
        if (index == 2) { if (value.empty()) return false; parsed.request_id = value; }
        if (index == 3 && value != expected_step) return false;
      }
    }
    if (seen != 0x1F || !cursor.Done()) return false;
    output = std::move(parsed); return true;
  } catch (...) { return false; }
}
} // namespace xar::ck3_1210
