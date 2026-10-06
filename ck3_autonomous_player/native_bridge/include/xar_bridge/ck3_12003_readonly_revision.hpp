#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <string_view>

// Pure request parsing. No allocation, native binding, or process access.
namespace xar::ck3_12003::readonly_query {
namespace detail {

class RevisionParser final {
public:
  explicit RevisionParser(std::string_view text) noexcept : text_(text) {}

  bool Parse(std::uint64_t &revision) noexcept {
    revision = 0;
    Space();
    if (!Object(1, true)) return false;
    Space();
    if (at_ != text_.size() || (!canonical_seen_ && !alias_seen_) ||
        (canonical_seen_ && alias_seen_ && canonical_ != alias_)) return false;
    revision = canonical_seen_ ? canonical_ : alias_;
    return true;
  }

private:
  enum class Key { other, canonical, alias };
  static constexpr unsigned max_depth = 64;
  static constexpr std::string_view canonical_key = "expected_snapshot_revision";
  static constexpr std::string_view alias_key = "expected_revision";
  std::string_view text_;
  std::size_t at_ = 0;
  bool canonical_seen_ = false, alias_seen_ = false;
  std::uint64_t canonical_ = 0, alias_ = 0;

  static bool Digit(char ch) noexcept { return ch >= '0' && ch <= '9'; }
  void Space() noexcept {
    while (at_ < text_.size() && (text_[at_] == ' ' || text_[at_] == '\t' ||
           text_[at_] == '\r' || text_[at_] == '\n')) ++at_;
  }
  bool Take(char ch) noexcept {
    if (at_ == text_.size() || text_[at_] != ch) return false;
    ++at_;
    return true;
  }
  bool Literal(std::string_view value) noexcept {
    if (text_.substr(at_, value.size()) != value) return false;
    at_ += value.size();
    return true;
  }
  bool Hex4(std::uint32_t &value) noexcept {
    value = 0;
    for (unsigned i = 0; i != 4; ++i) {
      if (at_ == text_.size()) return false;
      const char ch = text_[at_++];
      const int digit = ch >= '0' && ch <= '9' ? ch - '0' :
          ch >= 'a' && ch <= 'f' ? ch - 'a' + 10 :
          ch >= 'A' && ch <= 'F' ? ch - 'A' + 10 : -1;
      if (digit < 0) return false;
      value = value * 16U + static_cast<std::uint32_t>(digit);
    }
    return true;
  }
  bool Utf8(std::uint32_t &value) noexcept {
    const auto first = static_cast<unsigned char>(text_[at_++]);
    unsigned remaining = 0;
    std::uint32_t minimum = 0;
    if (first >= 0xC2U && first <= 0xDFU) {
      remaining = 1; value = first & 0x1FU; minimum = 0x80U;
    } else if (first >= 0xE0U && first <= 0xEFU) {
      remaining = 2; value = first & 0x0FU; minimum = 0x800U;
    } else if (first >= 0xF0U && first <= 0xF4U) {
      remaining = 3; value = first & 0x07U; minimum = 0x10000U;
    } else return false;
    for (unsigned i = 0; i != remaining; ++i) {
      if (at_ == text_.size()) return false;
      const auto next = static_cast<unsigned char>(text_[at_++]);
      if ((next & 0xC0U) != 0x80U) return false;
      value = value * 64U + (next & 0x3FU);
    }
    return value >= minimum && value <= 0x10FFFFU &&
        (value < 0xD800U || value > 0xDFFFU);
  }
  bool String(Key *key = nullptr) noexcept {
    if (!Take('"')) return false;
    bool canonical_matches = true, alias_matches = true;
    std::size_t length = 0;
    while (at_ < text_.size()) {
      if (Take('"')) {
        if (key != nullptr) {
          *key = canonical_matches && length == canonical_key.size() ? Key::canonical :
              alias_matches && length == alias_key.size() ? Key::alias : Key::other;
        }
        return true;
      }
      std::uint32_t scalar = 0;
      const auto byte = static_cast<unsigned char>(text_[at_]);
      if (byte < 0x20U) return false;
      if (Take('\\')) {
        if (at_ == text_.size()) return false;
        switch (text_[at_++]) {
        case '"': scalar = '"'; break;
        case '\\': scalar = '\\'; break;
        case '/': scalar = '/'; break;
        case 'b': scalar = 8; break;
        case 'f': scalar = 12; break;
        case 'n': scalar = 10; break;
        case 'r': scalar = 13; break;
        case 't': scalar = 9; break;
        case 'u': {
          if (!Hex4(scalar)) return false;
          if (scalar >= 0xD800U && scalar <= 0xDBFFU) {
            std::uint32_t low = 0;
            if (!Take('\\') || !Take('u') || !Hex4(low) ||
                low < 0xDC00U || low > 0xDFFFU) return false;
            scalar = 0x10000U + (scalar - 0xD800U) * 0x400U + low - 0xDC00U;
          } else if (scalar >= 0xDC00U && scalar <= 0xDFFFU) return false;
          break;
        }
        default: return false;
        }
      } else if (byte < 0x80U) { scalar = byte; ++at_; }
      else if (!Utf8(scalar)) return false;
      canonical_matches = canonical_matches && length < canonical_key.size() &&
          scalar == static_cast<unsigned char>(canonical_key[length]);
      alias_matches = alias_matches && length < alias_key.size() &&
          scalar == static_cast<unsigned char>(alias_key[length]);
      ++length;
    }
    return false;
  }
  bool Number(std::uint64_t *revision = nullptr) noexcept {
    const bool negative = Take('-');
    if (at_ == text_.size() || !Digit(text_[at_])) return false;
    const bool zero = text_[at_] == '0';
    std::uint64_t integer = 0;
    bool fits = true;
    do {
      const auto digit = static_cast<std::uint64_t>(text_[at_++] - '0');
      if (revision != nullptr && fits) {
        const auto maximum = (std::numeric_limits<std::uint64_t>::max)();
        fits = integer <= (maximum - digit) / 10U;
        if (fits) integer = integer * 10U + digit;
      }
      if (zero && at_ < text_.size() && Digit(text_[at_])) return false;
    } while (at_ < text_.size() && Digit(text_[at_]));
    bool integral = true;
    if (Take('.')) {
      integral = false;
      if (at_ == text_.size() || !Digit(text_[at_])) return false;
      while (at_ < text_.size() && Digit(text_[at_])) ++at_;
    }
    if (Take('e') || Take('E')) {
      integral = false;
      if (!Take('+')) (void)Take('-');
      if (at_ == text_.size() || !Digit(text_[at_])) return false;
      while (at_ < text_.size() && Digit(text_[at_])) ++at_;
    }
    if (revision != nullptr) {
      if (negative || !integral || !fits || integer == 0) return false;
      *revision = integer;
    }
    return true;
  }
  bool Value(unsigned depth) noexcept {
    Space();
    if (at_ == text_.size()) return false;
    switch (text_[at_]) {
    case '{': return Object(depth + 1, false);
    case '[': return Array(depth + 1);
    case '"': return String();
    case 't': return Literal("true");
    case 'f': return Literal("false");
    case 'n': return Literal("null");
    default: return Number();
    }
  }
  bool Array(unsigned depth) noexcept {
    if (depth > max_depth || !Take('[')) return false;
    Space();
    if (Take(']')) return true;
    for (;;) {
      if (!Value(depth)) return false;
      Space();
      if (Take(']')) return true;
      if (!Take(',')) return false;
    }
  }
  bool Object(unsigned depth, bool root) noexcept {
    if (depth > max_depth || !Take('{')) return false;
    Space();
    if (Take('}')) return true;
    for (;;) {
      Space();
      Key key = Key::other;
      if (!String(root ? &key : nullptr)) return false;
      Space();
      if (!Take(':')) return false;
      Space();
      if (key == Key::canonical) {
        if (canonical_seen_ || !Number(&canonical_)) return false;
        canonical_seen_ = true;
      } else if (key == Key::alias) {
        if (alias_seen_ || !Number(&alias_)) return false;
        alias_seen_ = true;
      } else if (!Value(depth)) return false;
      Space();
      if (Take('}')) return true;
      if (!Take(',')) return false;
    }
  }
};

} // namespace detail

// The complete envelope must be a JSON object. Revisions are unique top-level
// decimal uint64 integers > 0; escaped equivalent keys have the same identity.
// Either name is required, and when both occur their values must agree.
// Other envelope values use strict UTF-8 JSON grammar with at most 64 nested
// containers, including the root object. Failure always clears the output.
inline bool ParseUniqueTopLevelRevision(std::string_view payload,
                                       std::uint64_t &revision) noexcept {
  return detail::RevisionParser(payload).Parse(revision);
}

} // namespace xar::ck3_12003::readonly_query
